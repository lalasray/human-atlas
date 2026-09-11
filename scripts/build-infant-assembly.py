"""Combine the existing brain and chest meshes in one approximate infant display.

Run after the two source importers. Source manifests remain reproducible inputs;
only the brain's display positions change. This is not anatomical registration.
"""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / 'public/models'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def bounds(parts):
    return [[min(p['bounds'][0][axis] for p in parts) for axis in range(3)],
            [max(p['bounds'][1][axis] for p in parts) for axis in range(3)]]


def main():
    inputs = []
    for filename, count in [('atlas-infant.json', 85), ('atlas-infant-thorax.json', 9)]:
        raw = (MODELS / filename).read_bytes()
        atlas = json.loads(raw)
        assert len(atlas['parts']) == len(atlas['concepts']) == count
        assert atlas['license'] == 'CC-BY-4.0'
        for chunk in atlas['chunks']:
            data = (ROOT / 'public' / chunk['url'].lstrip('/')).read_bytes()
            assert len(data) == chunk['bytes'] and digest(data) == chunk['sha256']
        inputs.append((filename, digest(raw), atlas))
    brain, chest = [item[2] for item in inputs]
    brain_bounds, chest_bounds = bounds(brain['parts']), bounds(chest['parts'])
    brain_width = brain_bounds[1][0] - brain_bounds[0][0]
    chest_width = chest_bounds[1][0] - chest_bounds[0][0]
    chest_height = chest_bounds[1][1] - chest_bounds[0][1]
    # Display proportions chosen for a combined overview, not patient measurements.
    scale = .78 * chest_width / brain_width
    gap = .06 * chest_height
    translation = [(sum(chest_bounds[i][axis] for i in (0, 1)) -
                    scale * sum(brain_bounds[i][axis] for i in (0, 1))) / 2
                   for axis in range(3)]
    translation[1] = chest_bounds[1][1] + gap - scale * brain_bounds[0][1]
    matrices = {
        'dhcp-neonatal': [[scale if i == j else 0 for j in range(3)] + [translation[i]]
                         for i in range(3)] + [[0, 0, 0, 1]],
        'tyndall-newborn-thorax': [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
    }
    parts, concepts, chunks, transforms = [], [], [], []
    for filename, manifest_hash, source_atlas in inputs:
        source = source_atlas['parts'][0]['provenance']['source']
        transform_id = source + '-to-infant-display'
        matrix = matrices[source]
        is_brain = source == 'dhcp-neonatal'
        transform = {'id': transform_id, 'source': source, 'matrix': matrix,
            'scale': scale if is_brain else 1, 'source_manifest': '/models/' + filename,
            'source_manifest_sha256': manifest_hash,
            'from': source_atlas['parts'][0]['provenance']['display_space'],
            'to': 'infant assembly display stage, metres',
            'type': 'approximate display assembly', 'anatomical_registration': False,
            'review_status': 'approximate placement; unreviewed'}
        transforms.append(transform)
        for index, source_chunk in enumerate(source_atlas['chunks']):
            data = bytearray((ROOT / 'public' / source_chunk['url'].lstrip('/')).read_bytes())
            chunk_parts = deepcopy([p for p in source_atlas['parts'] if p['chunk'] == index])
            for part in chunk_parts:
                part['chunk'] = len(chunks)
                if is_brain:
                    low, high = [float('inf')] * 3, [float('-inf')] * 3
                    for vertex in range(part['vertexCount']):
                        offset = part['positions'] + vertex * 12
                        xyz = struct.unpack_from('<3f', data, offset)
                        struct.pack_into('<3f', data, offset, *(scale * xyz[a] + translation[a] for a in range(3)))
                        for axis, value in enumerate(struct.unpack_from('<3f', data, offset)):
                            low[axis], high[axis] = min(low[axis], value), max(high[axis], value)
                    part['bounds'] = [low, high]
                # Uniform positive scaling and translation preserve normal directions.
                provenance = part['provenance']
                provenance['source_display_registration'] = provenance['registration']
                provenance['source_conversion_notes'] = provenance['notes']
                provenance['assembly_input_chunk_sha256'] = source_chunk['sha256']
                provenance['display_space'] = transform['to']
                provenance['registration'] = {'type': transform['type'], 'display_transform_id': transform_id,
                    'transform_id': None, 'canonical_registration': False,
                    'review_status': transform['review_status']}
                provenance['display_transform'] = transform
                provenance['notes'] = ('Combined infant view using different source models. The brain is uniformly '
                    'resized and positioned above the chest for display; this is not a single scanned infant '
                    'or validated anatomical alignment. Original conversion details are retained separately.')
            chunk = deepcopy(source_chunk)
            if is_brain:
                name = f'infant-assembly-brain-{index}.bin'
                compressed = gzip.compress(data, mtime=0)
                (MODELS / name).write_bytes(data)
                (MODELS / (name + '.gz')).write_bytes(compressed)
                chunk = {'url': '/models/' + name, 'bytes': len(data), 'sha256': digest(data),
                         'gzip': '/models/' + name + '.gz', 'gzipBytes': len(compressed)}
            for part in chunk_parts:
                part['provenance']['derived_chunk_sha256'] = chunk['sha256']
            chunks.append(chunk)
            parts.extend(chunk_parts)
        concepts.extend(deepcopy(source_atlas['concepts']))
    atlas = {'version': 'Infant assembly 1.0', 'source': 'dHCP + Tyndall',
        'region': 'infant-assembly', 'developmental_stage': 'neonatal composite',
        'scope': 'Combined infant brain and chest display from different sources; approximate proportions '
                 'and placement, not a complete body or a single scanned infant.',
        'default_visible': ['nervous', 'cardiac', 'respiratory', 'arterial', 'skeletal', 'connective'],
        'license': 'CC-BY-4.0', 'parts': parts, 'concepts': concepts, 'chunks': chunks,
        'triangles': sum(p['indexCount'] // 3 for p in parts), 'display_transforms': transforms,
        'assembly': {'brain_to_chest_width_ratio': .78, 'brain_scale': scale,
            'brain_chest_gap_m': gap, 'anatomical_registration': False,
            'shared_donor': False, 'complete_body': False}}
    output = json.dumps(atlas, separators=(',', ':')).encode()
    (MODELS / 'atlas-infant-expanded.json').write_bytes(output)
    report = {'manifestSha256': digest(output), 'meshes': len(parts), 'concepts': len(concepts),
        'triangles': atlas['triangles'], 'displayTransforms': transforms, 'assembly': atlas['assembly'],
        'remainingGaps': ['Skull, face, neck, limbs and pelvis.', 'Abdominal and pelvic organs.',
                          'Complete peripheral nerves and vessels.']}
    (ROOT / 'public/infant-sources/assembly.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Built one infant view: {len(parts)} parts; brain display scale {scale:.4f}; neck gap {gap:.4f} m.')


if __name__ == '__main__':
    main()
