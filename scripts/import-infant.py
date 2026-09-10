"""Import the existing dHCP neonatal brain, preserving scale and source evidence.

Usage: python3 scripts/import-infant.py /path/to/HumanAnatomyFemale
Only a rigid display rotation/translation is applied; no adult registration.
"""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'd699540b1820d8224a07db3c1d727d0c747218dc'
INPUT_HASH = '57592a9cfd85542a158ed5803a86530fc19ba72946d1c2e0a3c6f8c597cc85d0'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    source = Path(sys.argv[1]).resolve()
    manifest = source / 'public/atlases/dhcp-neonatal.json'
    atlas = json.loads(manifest.read_text())
    assert atlas['source_revision'] == REVISION and atlas['input_sha256'] == INPUT_HASH
    assert len(atlas['parts']) == len(atlas['concepts']) == 85
    assert atlas['license'] == 'CC-BY-4.0' and atlas['region'] == 'brain'
    raw = source / 'data/raw/dhcp-neonatal'
    assert digest((raw / 'structures.nii.gz').read_bytes()) == INPUT_HASH
    records = json.loads((raw / 'download-manifest.json').read_text())
    assert records['revision'] == REVISION and records['license'] == 'CC-BY-4.0'
    for record in records['files']:
        data = (raw / Path(record['local']).name).read_bytes()
        assert len(data) == record['bytes'] and digest(data) == record['sha256']
    blobs = []
    for i, chunk in enumerate(atlas['chunks']):
        assert chunk['url'].startswith('/models/dhcp-neonatal-')
        data = (source / 'public' / chunk['url'].lstrip('/')).read_bytes()
        compressed = (source / 'public' / chunk['gzip'].lstrip('/')).read_bytes()
        assert len(data) == chunk['bytes'] and len(compressed) == chunk['gzipBytes']
        assert gzip.decompress(compressed) == data
        for part in atlas['parts']:
            if part['chunk'] == i:
                assert part['provenance']['source_chunk_sha256'] == digest(data)
        blobs.append(bytearray(data))
    low = [min(p['bounds'][0][a] for p in atlas['parts']) for a in range(3)]
    high = [max(p['bounds'][1][a] for p in atlas['parts']) for a in range(3)]
    cx, cy = [(low[a] + high[a]) / 2 for a in (0, 1)]
    z0 = low[2] - .01
    matrix = [[-1, 0, 0, cx], [0, 0, 1, -z0], [0, 1, 0, -cy], [0, 0, 0, 1]]
    for part in atlas['parts']:
        data = blobs[part['chunk']]
        bounds = [[float('inf')] * 3, [float('-inf')] * 3]
        for i in range(part['vertexCount']):
            offset = part['positions'] + i * 12
            x, y, z = struct.unpack_from('<3f', data, offset)
            struct.pack_into('<3f', data, offset, -x + cx, z - z0, y - cy)
            for a, value in enumerate(struct.unpack_from('<3f', data, offset)):
                bounds[0][a] = min(bounds[0][a], value)
                bounds[1][a] = max(bounds[1][a], value)
            offset = part['normals'] + i * 6
            x, y, z = struct.unpack_from('<3h', data, offset)
            struct.pack_into('<3h', data, offset, max(-32767, min(32767, -x)), z, y)
        part['bounds'] = bounds
        part['provenance']['display_space'] = 'dHCP GA40 display stage, metres'
        part['provenance']['registration']['display_transform_id'] = 'dhcp-ras-metres-to-stage'
    output = ROOT / 'public/models'
    for i, data in enumerate(blobs):
        name = f'infant-brain-{i}.bin'
        compressed = gzip.compress(data, mtime=0)
        (output / name).write_bytes(data)
        (output / (name + '.gz')).write_bytes(compressed)
        atlas['chunks'][i] = {'url': '/models/' + name, 'bytes': len(data), 'sha256': digest(data),
                              'gzip': '/models/' + name + '.gz', 'gzipBytes': len(compressed)}
        for part in atlas['parts']:
            if part['chunk'] == i:
                part['provenance']['derived_chunk_sha256'] = digest(data)
    atlas['display_transform'] = {'id': 'dhcp-ras-metres-to-stage', 'matrix': matrix,
        'scale': 1, 'units': 'metres', 'registration_to_adult': False,
        'description': 'Rigid display reorientation: x left, y superior, z anterior; centered above floor.'}
    (output / 'atlas-infant.json').write_text(json.dumps(atlas, separators=(',', ':')))
    evidence = ROOT / 'public/infant-sources'
    evidence.mkdir(exist_ok=True)
    for name in ['LICENSE.md', 'README.md', 'download-manifest.json', 'structures.txt']:
        shutil.copyfile(source / 'data/raw/dhcp-neonatal' / name, evidence / name)
    report = {'source': atlas['source_url'], 'sourceRevision': REVISION, 'inputSha256': INPUT_HASH,
              'sourceManifestSha256': digest(manifest.read_bytes()),
              'manifestSha256': digest((output / 'atlas-infant.json').read_bytes()),
              'meshes': 85, 'concepts': 85, 'age': atlas['reference_age'], 'region': 'brain',
              'displayTransform': atlas['display_transform'], 'anatomicalReview': 'local conversion unreviewed',
              'remainingGaps': ['Skull, face, eyes and ears.', 'Skeleton and muscles of the body.',
                                'Chest, abdominal and pelvic organs.', 'Peripheral nerves, vessels and skin.']}
    (evidence / 'coverage.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Imported 85 neonatal brain regions. No whole-body infant anatomy is claimed.')


if __name__ == '__main__':
    main()
