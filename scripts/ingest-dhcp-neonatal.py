#!/usr/bin/env python3
"""Convert the pinned dHCP 40-week PMA hard segmentation into web meshes.

This is a brain-only aggregate neonatal reference. Geometry remains in the source
atlas metric frame; no registration to either adult atlas is claimed.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import re
import struct
from pathlib import Path

import numpy as np
import trimesh
from skimage.measure import marching_cubes

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/dhcp-neonatal"
OUT = ROOT / "public/models"
REVISION = "d699540b1820d8224a07db3c1d727d0c747218dc"
EXCLUDED_LABELS = {84: "Extra-cranial background", 85: "Intra-cranial background"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_nifti_uint8(path: Path) -> tuple[np.ndarray, np.ndarray, dict]:
    raw = gzip.open(path, "rb").read()
    if len(raw) < 352 or struct.unpack_from("<I", raw, 0)[0] != 348 or raw[344:348] != b"n+1\0":
        raise ValueError("expected little-endian single-file NIfTI-1")
    dim = struct.unpack_from("<8h", raw, 40)
    datatype, bitpix = struct.unpack_from("<hh", raw, 70)
    pixdim = struct.unpack_from("<8f", raw, 76)
    offset = int(struct.unpack_from("<f", raw, 108)[0])
    qform_code = struct.unpack_from("<h", raw, 252)[0]
    if dim[0] != 3 or datatype != 2 or bitpix != 8 or qform_code <= 0 or offset < 352:
        raise ValueError("unsupported dHCP NIfTI header contract")
    shape = tuple(dim[1:4])
    count = int(np.prod(shape))
    if len(raw) < offset + count:
        raise ValueError("truncated dHCP NIfTI payload")
    volume = np.frombuffer(raw, dtype=np.uint8, count=count, offset=offset).reshape(shape, order="F")
    b, c, d = struct.unpack_from("<3f", raw, 256)
    x, y, z = struct.unpack_from("<3f", raw, 268)
    a = math.sqrt(max(0.0, 1.0 - b * b - c * c - d * d))
    rotation = np.array([
        [a*a+b*b-c*c-d*d, 2*b*c-2*a*d, 2*b*d+2*a*c],
        [2*b*c+2*a*d, a*a+c*c-b*b-d*d, 2*c*d-2*a*b],
        [2*b*d-2*a*c, 2*c*d+2*a*b, a*a+d*d-c*c-b*b],
    ])
    scales = np.array(pixdim[1:4], dtype=float)
    if pixdim[0] < 0:
        scales[2] *= -1
    affine = np.eye(4)
    affine[:3, :3] = rotation @ np.diag(scales)
    affine[:3, 3] = [x, y, z]
    return volume, affine, {"shape": list(shape), "datatype": datatype, "bitpix": bitpix,
                            "pixdim_mm": list(pixdim[1:4]), "qform_code": qform_code,
                            "quaternion_bcd": [b, c, d], "qoffset_xyz_mm": [x, y, z]}


def read_labels(path: Path) -> dict[int, str]:
    labels = {}
    lines = path.read_text().splitlines()
    if not lines or lines[0].strip() != "irtkSegmentTable: 87":
        raise ValueError("expected dHCP 87-structure table")
    for line in lines[1:]:
        match = re.match(r"\s*(\d+)\s+(?:\d+\s+){5}(.+?)\s*$", line)
        if match:
            labels[int(match.group(1))] = match.group(2)
    if set(labels) != set(range(1, 88)):
        raise ValueError("dHCP label table must define values 1 through 87")
    return labels


def laterality(name: str) -> str:
    lowered = name.lower()
    return "left" if lowered.endswith(" left") or " left " in lowered else "right" if lowered.endswith(" right") or " right " in lowered else "midline"


def main() -> int:
    manifest = json.loads((RAW / "download-manifest.json").read_text())
    if manifest["revision"] != REVISION or manifest["license"] != "CC-BY-4.0":
        raise ValueError("unexpected dHCP source revision or license")
    source = RAW / "structures.nii.gz"
    records = {Path(item["local"]).name: item for item in manifest["files"]}
    for name in ("structures.nii.gz", "structures.txt", "LICENSE.md"):
        path = RAW / name
        if records[name]["bytes"] != path.stat().st_size or records[name]["sha256"] != sha256(path):
            raise ValueError(f"source identity mismatch: {name}")
    volume, affine, header = read_nifti_uint8(source)
    labels = read_labels(RAW / "structures.txt")
    present = set(int(value) for value in np.unique(volume) if value)
    if present != set(labels):
        raise ValueError(f"segmentation labels differ from table: missing={set(labels)-present}, unknown={present-set(labels)}")

    parts, concepts, chunks, qa = [], [], [], []
    blob = bytearray()

    def append(values: np.ndarray) -> int:
        while len(blob) % 4:
            blob.append(0)
        offset = len(blob)
        blob.extend(values.tobytes())
        return offset

    def flush() -> None:
        if not blob:
            return
        name = f"dhcp-neonatal-source-{len(chunks)}.bin"
        target = OUT / name
        target.write_bytes(blob)
        chunks.append({"url": "/models/" + name, "bytes": len(blob)})
        blob.clear()

    voxel_to_metres = affine.copy()
    voxel_to_metres[:3] *= 0.001
    for value, name in labels.items():
        if value in EXCLUDED_LABELS:
            continue
        mask = volume == value
        crop = np.pad(mask.astype(np.uint8), 1)
        vertices, faces, _, _ = marching_cubes(crop, 0.5, allow_degenerate=False)
        vertices -= 1
        vertices = trimesh.transform_points(vertices, voxel_to_metres)
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
        if mesh.volume < 0:
            mesh.invert()
        positions = np.asarray(mesh.vertices, dtype="<f4")
        normals = np.asarray(np.clip(mesh.vertex_normals * 32767, -32767, 32767), dtype="<i2")
        indices = np.asarray(mesh.faces, dtype="<u4").ravel()
        if len(blob) > 5_000_000:
            flush()
        identity = f"DHCP:GA40:{value}"
        side = laterality(name)
        metadata = {
            "source_sex": "mixed-aggregate", "reference_sex": "mixed",
            "source_donor": "dhcp-ga40-aggregate", "geometry_type": "derived_group_atlas_segmentation",
            "developmental_stage": "term-equivalent neonatal", "reference_age": "40 weeks post-menstrual age",
            "region": "brain", "label_value": value, "source_label": name, "laterality": side,
            "input_sha256": records["structures.nii.gz"]["sha256"], "source_revision": REVISION,
            "ontology_mapping": "dHCP source label retained; ontology crosswalk not yet reviewed",
            "notes": "Derived from the dHCP aggregate 40-week PMA hard structural segmentation. Brain only; not a whole-body infant model. Source atlas construction used structurally normal neonatal MRI. Local mesh conversion is unreviewed. Global age-size DOF was not applied; source common atlas metric space is preserved.",
        }
        part = {"id": identity, "name": name, "conceptId": identity, "system": "nervous", "chunk": len(chunks),
                "positions": append(positions), "normals": append(normals), "indices": append(indices),
                "vertexCount": len(positions), "indexCount": len(indices),
                "bounds": [positions.min(axis=0).tolist(), positions.max(axis=0).tolist()], "source_metadata": metadata}
        parts.append(part)
        concepts.append({"id": identity, "name": name, "elements": [identity]})
        qa.append({"label_value": value, "name": name, "voxels": int(mask.sum()), "vertices": len(positions),
                   "triangles": len(indices) // 3, "watertight": bool(mesh.is_watertight),
                   "anatomical_review": "upstream atlas methodology; local conversion unreviewed"})
        print(f"{value}/87 {name}: {len(indices)//3} triangles", flush=True)
    flush()
    atlas = {
        "version": "dHCP neonatal brain atlas, 40 weeks PMA, pinned revision " + REVISION,
        "source": "dHCP neonatal brain atlas", "region": "brain", "developmental_stage": "neonatal",
        "reference_age": "40 weeks post-menstrual age", "population_sex": "mixed aggregate",
        "scope": "Brain-only aggregate term-equivalent neonatal reference at 40 weeks PMA; 85 anatomical regions from the dHCP 87-label Draw-EM segmentation of 275 structurally normal neonatal MRI scans (two background labels excluded). Not a whole-body infant atlas and not registered to either adult model.",
        "parts": parts, "concepts": concepts, "chunks": chunks,
        "triangles": sum(part["indexCount"] // 3 for part in parts), "source_affine_mm": affine.tolist(),
        "source_header": header, "source_revision": REVISION, "input_sha256": records["structures.nii.gz"]["sha256"],
        "license": "CC-BY-4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "source_url": "https://gin.g-node.org/BioMedIA/dhcp-volumetric-atlas-groupwise",
        "doi": "10.12751/g-node.d2b353", "citation_doi": "10.1101/251512",
        "source_label_count": 87, "excluded_labels": EXCLUDED_LABELS,
        "size_scaling": "Not applied; source common atlas metric coordinate system preserved. scale/ga_40.dof retained as evidence.",
    }
    target = OUT / "atlas-dhcp-neonatal.json"
    target.write_text(json.dumps(atlas, separators=(",", ":")))
    (ROOT / "generated/dhcp-neonatal-qa.json").write_text(json.dumps(qa, indent=2) + "\n")
    print(json.dumps({"parts": len(parts), "concepts": len(concepts), "triangles": atlas["triangles"],
                      "chunks": len(chunks), "input_sha256": atlas["input_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
