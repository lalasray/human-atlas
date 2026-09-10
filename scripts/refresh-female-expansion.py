"""Combine the canonical female catalog with the existing MOOSE bone extension.

Run after rebuilding public/atlases/composed.json. This preserves the ten
segmented hand/forearm meshes and uses the composition's deduplicated concepts.
It does not rerun segmentation or change the extension's registration.
"""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'nlm-vhf-moose'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    base_path = ROOT / 'public/atlases/composed.json'
    target = ROOT / 'public/models/atlas-female-expanded.json'
    evidence = ROOT / 'public/female-sources'
    base = json.loads(base_path.read_text())
    previous = json.loads(target.read_text())
    assert base['canonical_space'] == previous['canonical_space'] == 'VHF-image-2022'
    for name in ['nlm-ct-to-vhf', 'canonical-space']:
        assert json.loads((ROOT / f'transforms/{name}.json').read_text()) == json.loads(
            (evidence / f'transforms/{name}.json').read_text()), 'Review changed registration before combining'
    added = [deepcopy(p) for p in previous['parts'] if p['provenance']['source'] == SOURCE]
    assert len(added) == 10 and len(base['parts']) == 1015
    assert not any(p['provenance']['source'] == SOURCE for p in base['parts'])
    chunk_ids = sorted({p['chunk'] for p in added})
    for part in added:
        chunk = previous['chunks'][part['chunk']]
        assert digest((ROOT / 'public' / chunk['url'].lstrip('/')).read_bytes()) == part['provenance']['derived_chunk_sha256']
        part['chunk'] = len(base['chunks']) + chunk_ids.index(part['chunk'])
    base['chunks'].extend(previous['chunks'][i] for i in chunk_ids)
    base['parts'].extend(added)
    base['concepts'].extend({'id': p['conceptId'], 'name': p['name'], 'elements': [p['id']]} for p in added)
    base['triangles'] = sum(p['indexCount'] // 3 for p in base['parts'])
    base['version'] += ' plus MOOSE hand/forearm references'
    base['source'] += ' + MOOSE hand/forearm labels'
    base['scope'] += ' Ten additional MOOSE hand/forearm labels remain partial or grouped, with anatomical review pending.'
    target.write_text(json.dumps(base, separators=(',', ':')))
    report_path = evidence / 'coverage.json'
    report = json.loads(report_path.read_text())
    report['manifestSha256'] = digest(target.read_bytes())
    report['baseManifestSha256'] = digest(base_path.read_bytes())
    report['compositionBase'] = '/atlases/composed.json'
    report['counts']['concepts'] = len(base['concepts'])
    report['counts']['expandedMeshes'] = len(base['parts'])
    report['meshesBySource'] = dict(Counter(p['provenance']['source'] for p in base['parts']))
    for row in report['systems']:
        row['expanded'] = sum(p['system'] == row['id'] for p in base['parts'])
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    for path in ['generated/registration-report.json', 'registry/composition-recipe.json', 'registry/review-status.json']:
        (evidence / path).write_bytes((ROOT / path).read_bytes())
    print(f'Expanded female: {len(base["parts"])} meshes, {len(base["concepts"])} distinct concepts; MOOSE extension retained.')


if __name__ == '__main__':
    main()
