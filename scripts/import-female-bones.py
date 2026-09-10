"""Add ten MOOSE hand/forearm label surfaces to the expanded female assembly.

Usage: python scripts/import-female-bones.py /path/to/segmentation.nii.gz
Dependencies: numpy, scipy, nibabel, scikit-image, trimesh.
These are automatic CT references, including incomplete forearm boundaries.
"""
import gzip
import hashlib
import json
from pathlib import Path
import sys

import nibabel as nib
import numpy as np
from scipy import ndimage
from skimage.measure import marching_cubes
import trimesh

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'nlm-vhf-moose'
LABEL_HASH = '9f3aed912c383bfa1017ae89448786af2958b71c5a682e6a8a7db462c50e3a01'
CT_HASH = '5284a87267a83911f0174a07fb3f755301376eb5658daf12d95455cc2ecad26f'
WEIGHT_HASH = 'd12373c2f13b94abf4ed1102be2eb494020f6d075d8aca93afd9fd405d86cd47'
LABELS = {1: 'carpal_left', 2: 'carpal_right', 9: 'fingers_left', 10: 'fingers_right',
          13: 'metacarpal_left', 14: 'metacarpal_right', 19: 'radius_left', 20: 'radius_right',
          30: 'ulna_left', 31: 'ulna_right'}
NAMES = {'carpal': 'carpal bones (group)', 'fingers': 'finger bones (group)',
         'metacarpal': 'metacarpal bones (group)', 'radius': 'radius', 'ulna': 'ulna'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    path = Path(sys.argv[1])
    assert digest(path.read_bytes()) == LABEL_HASH, 'Unexpected segmentation; review a new run before import'
    image = nib.load(path)
    assert image.shape == (512, 512, 1100)
    assert np.allclose(image.affine, [[-.9375, 0, 0, 239.53125], [0, -.9375, 0, 239.53125], [0, 0, -1, 0], [0, 0, 0, 1]])
    volume = np.array(image.dataobj)
    evidence = ROOT / 'public/female-sources'
    ct_transform = json.loads((evidence / 'transforms/nlm-ct-to-vhf.json').read_text())
    stage_transform = json.loads((evidence / 'transforms/canonical-space.json').read_text())['image_to_stage']
    transform = np.array(stage_transform['matrix_row_major']).reshape(4, 4) @ np.array(ct_transform['matrix_row_major']).reshape(4, 4)
    voxel_to_stage = transform @ image.affine
    # MOOSE assigned a left-hand fragment to the right fingers. Fix laterality
    # using the known source RAS midline; this does not invent new geometry.
    correction = (volume == 10) & (np.arange(512)[:, None, None] > 255)
    assert int(correction.sum()) == 848
    volume[correction] = 9
    manifest = ROOT / 'public/models/atlas-female-expanded.json'
    atlas = json.loads(manifest.read_text())
    # Re-running replaces only this import's records and final chunk.
    atlas['parts'] = [p for p in atlas['parts'] if p.get('provenance', {}).get('source') != SOURCE]
    atlas['concepts'] = [c for c in atlas['concepts'] if not c['id'].startswith(SOURCE + ':')]
    atlas['chunks'] = [c for c in atlas['chunks'] if not c['url'].startswith('/models/female-hand-forearm-')]
    assert len(atlas['parts']) == 1015 and len(atlas['chunks']) == 17
    blob = bytearray()
    rows, new_parts = [], []

    def append(values):
        blob.extend(b'\0' * (-len(blob) % 4))
        offset = len(blob)
        blob.extend(values.tobytes())
        return offset

    for value, label in LABELS.items():
        xyz = np.argwhere(volume == value)
        assert len(xyz) > 1000, f'Empty or tiny label: {label}'
        low, high = xyz.min(axis=0), xyz.max(axis=0)
        mask = volume[tuple(slice(l, h + 1) for l, h in zip(low, high))] == value
        components, count = ndimage.label(mask)
        sizes = np.bincount(components.ravel())
        tiny = np.flatnonzero((sizes < 10) & (np.arange(len(sizes)) > 0))
        removed = int(sizes[tiny].sum())
        mask[np.isin(components, tiny)] = False
        vertices, faces, _, _ = marching_cubes(np.pad(mask.astype(np.uint8), 1), .5, allow_degenerate=False)
        vertices += low - 1
        vertices = trimesh.transform_points(vertices, voxel_to_stage)
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
        if mesh.volume < 0:
            mesh.invert()
        positions = np.asarray(mesh.vertices, dtype='<f4')
        normals = np.asarray(np.clip(mesh.vertex_normals * 32767, -32767, 32767), dtype='<i2')
        indices = np.asarray(mesh.faces, dtype='<u4').ravel()
        kind, side = label.rsplit('_', 1)
        partial = kind in ('radius', 'ulna')
        name = side.title() + ' ' + NAMES[kind] + (' (partial CT reference)' if partial else '')
        identity = SOURCE + ':' + label
        bounds = [positions.min(0).tolist(), positions.max(0).tolist()]
        assert all(x > 0 for x in positions[:, 0]) if side == 'left' else all(x < 0 for x in positions[:, 0])
        assert .7 < bounds[0][1] < bounds[1][1] < 1.35, f'Unexpected upper limb location: {label}'
        record = {'source': SOURCE, 'source_asset': label, 'source_donor': 'VHF', 'source_sex': 'female',
            'source_url': 'https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Female-Images/radiological/normalCT/',
            'geometry_type': 'automatic_ct_segmentation', 'label_name': label, 'label_value': value,
            'input_sha256': CT_HASH, 'segmentation_sha256': LABEL_HASH, 'model_weights_sha256': WEIGHT_HASH,
            'model': 'MOOSE clin_ct_peripheral_bones', 'software_version': 'moosez 3.2.2',
            'license': 'NLM-Terms-and-Conditions', 'license_url': 'https://www.nlm.nih.gov/databases/download/terms_and_conditions.html',
            'model_license': 'CC-BY-4.0', 'model_license_url': 'https://github.com/ENHANCE-PET/MOOSE/blob/main/MODEL_LICENSE',
            'canonical_space': 'VHF-image-2022', 'laterality': side,
            'granularity': 'grouped' if kind in ('carpal', 'metacarpal', 'fingers') else 'individual',
            'registration': {'transform_id': 'nlm-ct-to-vhf', 'display_transform_id': 'canonical-image-to-stage',
                             'type': 'existing rigid same-donor CT registration', 'review_status': 'unreviewed'},
            'anatomical_review': 'pending', 'partial_scan_reference': partial,
            'notes': 'Automatic labels. Forearm coverage is incomplete where the source scan cuts off the arms; right ulna is fragmented. Hand labels group multiple bones. No anatomical completeness or accuracy claim.',
            'adaptations': {'method': 'marching cubes at source voxel resolution; no smoothing or simplification',
                            'removed_noise_voxels': removed,
                            'laterality_correction': '848 voxels moved from right to left finger label using source RAS coordinates' if kind == 'fingers' else None}}
        part = {'id': identity, 'name': name, 'conceptId': identity, 'system': 'skeletal', 'chunk': 17,
                'positions': append(positions), 'normals': append(normals), 'indices': append(indices),
                'vertexCount': len(positions), 'indexCount': len(indices), 'bounds': bounds, 'provenance': record}
        atlas['parts'].append(part)
        atlas['concepts'].append({'id': identity, 'name': name, 'elements': [identity]})
        new_parts.append(part)
        rows.append({'label': label, 'voxels': int(mask.sum()), 'removed_noise_voxels': removed,
                     'components': count - len(tiny), 'bounds': bounds, 'watertight': bool(mesh.is_watertight),
                     'triangles': len(indices) // 3, 'partial_scan_reference': partial})
        print(name, len(indices) // 3, 'triangles', flush=True)
    data_hash = digest(blob)
    for p in new_parts:
        p['provenance']['derived_chunk_sha256'] = data_hash
    name = 'female-hand-forearm-0.bin'
    compressed = gzip.compress(blob, mtime=0)
    (ROOT / 'public/models' / name).write_bytes(blob)
    (ROOT / 'public/models' / (name + '.gz')).write_bytes(compressed)
    atlas['chunks'].append({'url': '/models/' + name, 'bytes': len(blob), 'sha256': data_hash,
                            'gzip': '/models/' + name + '.gz', 'gzipBytes': len(compressed)})
    atlas['version'] = 'Female composition 0.4 plus MOOSE hand/forearm references, experimental'
    atlas['source'] = 'Denver VHF + NLM VHF CT + HRA + MOOSE hand/forearm labels'
    atlas['triangles'] = sum(p['indexCount'] // 3 for p in atlas['parts'])
    manifest.write_text(json.dumps(atlas, separators=(',', ':')))
    report = json.loads((evidence / 'coverage.json').read_text())
    report.setdefault('baseManifestSha256', report['manifestSha256'])
    report['manifestSha256'] = digest(manifest.read_bytes())
    report['counts'].update(expandedMeshes=1025, addedVhfMeshes=239, concepts=1281)
    report['meshesBySource'][SOURCE] = 10
    for row in report['systems']:
        row['expanded'] = sum(p['system'] == row['id'] for p in atlas['parts'])
    report['remainingGaps'][0] = 'Forearm bones remain partial at clipped scan boundaries; hand bones are grouped automatic labels, not individually reviewed bones.'
    report['extensions'] = [{'source': SOURCE, 'meshes': 10, 'evidence': '/female-sources/hand-forearm-qa.json'}]
    (evidence / 'coverage.json').write_text(json.dumps(report, indent=2) + '\n')
    qa = {'source': SOURCE, 'modelUrl': 'https://github.com/ENHANCE-PET/MOOSE',
          'modelWeightsUrl': 'https://github.com/ENHANCE-PET/MOOSE/releases/download/moosez-v.3.1.3/clin_ct_peripheral_bones_ras_07052025.zip',
          'modelWeightsSha256': WEIGHT_HASH, 'inputSha256': CT_HASH, 'labelsSha256': LABEL_HASH,
          'crop': [0, 1100], 'voxelToStage': voxel_to_stage.tolist(), 'lateralityCorrectedVoxels': 848,
          'labels': rows, 'anatomicalReview': 'pending'}
    (evidence / 'hand-forearm-qa.json').write_text(json.dumps(qa, indent=2) + '\n')
    print(f'Female assembly: {len(atlas["parts"])} meshes; {len(compressed):,} added compressed bytes. Still incomplete.')


if __name__ == '__main__':
    main()
