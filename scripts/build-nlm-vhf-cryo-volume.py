#!/usr/bin/env python3
"""Build bounded RGB NIfTI channels from downloaded NLM VHF cryosections.

Outputs three uint8 scalar volumes because this representation is directly usable by
common medical-imaging and segmentation tools. Raw source sections are not aligned;
the metadata therefore records ``unaligned-original`` and never claims canonical space.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data/raw/nlm-vhf/cryo-download-manifest.json"
DEFAULT_OUTPUT = ROOT / "data/derived/nlm-vhf/cryo"
EXPECTED_FORMAT = "RGB 24-bit non-interleaved, one complete section per .raw.Z file"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--validate-only", action="store_true")
    return parser


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_manifest(manifest: dict, root: Path = ROOT) -> list[dict]:
    if manifest.get("format") != EXPECTED_FORMAT:
        raise ValueError(f"unsupported cryosection format: {manifest.get('format')!r}")
    if manifest.get("alignment_status") != "unaligned-original":
        raise ValueError("this builder only accepts original, explicitly unaligned source sections")
    width, height = manifest.get("width"), manifest.get("height")
    if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
        raise ValueError("manifest width and height must be positive integers")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("manifest must contain at least one downloaded section")
    ordinals = [record.get("source_ordinal") for record in files]
    if any(not isinstance(value, int) for value in ordinals):
        raise ValueError("every section requires an integer source_ordinal")
    if ordinals != list(range(ordinals[0], ordinals[0] + len(ordinals))):
        raise ValueError("downloaded sections must be ordered and contiguous")
    names = [record.get("filename") for record in files]
    if len(set(names)) != len(names):
        raise ValueError("duplicate cryosection filenames")
    expected_raw = width * height * 3
    for record in files:
        local = root / record["local"]
        if not local.is_file():
            raise FileNotFoundError(local)
        if record.get("bytes") != local.stat().st_size:
            raise ValueError(f"compressed byte count mismatch: {record['filename']}")
        if record.get("sha256") != sha256(local):
            raise ValueError(f"SHA-256 mismatch: {record['filename']}")
        if record.get("expected_uncompressed_bytes") != expected_raw:
            raise ValueError(f"unexpected decoded size declaration: {record['filename']}")
    return files


def read_planar_rgb(path: Path, width: int, height: int) -> bytes:
    result = subprocess.run(["gzip", "-dc", str(path)], check=True, capture_output=True)
    expected = width * height * 3
    if len(result.stdout) != expected:
        raise ValueError(f"{path.name}: decoded {len(result.stdout)} bytes; expected {expected}")
    return result.stdout


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = json.loads(args.manifest.read_text())
    files = validate_manifest(manifest)
    summary = {"manifest": str(args.manifest), "sections": len(files), "width": manifest["width"],
               "height": manifest["height"], "alignment_status": manifest["alignment_status"]}
    if args.validate_only:
        print(json.dumps(summary, indent=2))
        return 0

    try:
        import nibabel as nib
        import numpy as np
    except ImportError as error:
        raise SystemExit("building NIfTI volumes requires .venv/bin/pip install -r requirements-pipeline.txt") from error

    width, height = manifest["width"], manifest["height"]
    spacing = manifest["spacing_mm"]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    channels = [np.empty((width, height, len(files)), dtype=np.uint8) for _ in range(3)]
    decoded_hashes: dict[str, str] = {}
    plane_bytes = width * height
    for index, record in enumerate(files):
        raw = read_planar_rgb(ROOT / record["local"], width, height)
        decoded_hashes[record["filename"]] = hashlib.sha256(raw).hexdigest()
        # NLM documents planar RGB: all red pixels, then green, then blue.
        for channel in range(3):
            plane = np.frombuffer(raw, dtype=np.uint8, count=plane_bytes, offset=channel * plane_bytes)
            channels[channel][:, :, index] = plane.reshape(height, width).T
        print(f"{index + 1}/{len(files)} decoded {record['filename']}", flush=True)

    # Raw images provide spacing but no coordinate offsets or alignment. This affine is
    # an index-space convenience only and is not the VHF-image-2022 canonical transform.
    affine = np.array([[spacing[0], 0, 0, 0], [0, spacing[1], 0, 0],
                       [0, 0, -spacing[2], 0], [0, 0, 0, 1]], dtype=float)
    outputs: dict[str, dict] = {}
    for name, data in zip(("red", "green", "blue"), channels):
        image = nib.Nifti1Image(data, affine)
        image.header.set_xyzt_units("mm")
        image.header["descrip"] = b"NLM VHF raw cryosections; unaligned original index space"
        target = args.output_dir / f"vhf-cryo-{name}.nii.gz"
        nib.save(image, target)
        outputs[name] = {"file": str(target.relative_to(ROOT)), "sha256": sha256(target)}

    metadata = {
        "source": manifest["source"], "terms_url": manifest["terms_url"], "format": manifest["format"],
        "shape": [width, height, len(files)], "dtype": "uint8", "spacing_mm": spacing,
        "channel_order": ["red", "green", "blue"], "source_sections": [record["filename"] for record in files],
        "source_ordinals": [record["source_ordinal"] for record in files], "source_sha256": {record["filename"]: record["sha256"] for record in files},
        "decoded_sha256": decoded_hashes, "outputs": outputs, "affine_index_space": affine.tolist(),
        "alignment_status": "unaligned-original",
        "canonical_space": None,
        "warning": "These raw sections are not registered to VHF-image-2022. Do not ingest labels or compose anatomy until alignment is measured and reviewed.",
        "attribution": "Courtesy of the U.S. National Library of Medicine",
    }
    metadata_path = args.output_dir / "vhf-cryo-metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    summary.update({"outputs": outputs, "metadata": str(metadata_path.relative_to(ROOT))})
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
