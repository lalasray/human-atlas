"""Import the pinned, pre-aligned female assembly and its evidence from human-atlas.

Usage: python3 scripts/import-female-expansion.py /path/to/human-atlas
No segmentation or new registration is performed by this importer.
"""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from collections import Counter

REVISION = 'f1c09ede05984702c98fc89198b1f1e2c60f073f'
ROOT = Path(__file__).resolve().parents[1]


def main():
    source = Path(sys.argv[1]).resolve()
    revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != REVISION:
        raise ValueError(f'Expected upstream revision {REVISION}, got {revision}')
    manifest = source / 'public/atlases/composed.json'
    atlas = json.loads(manifest.read_text())
    original = json.loads((source / 'public/atlases/hra-female.json').read_text())
    sources = Counter(p['provenance']['source'] for p in atlas['parts'])
    assert sources == {'hra-female': 786, 'denver-vhf': 128, 'nlm-vhf-ct': 101}
    assert atlas['sex'] == 'female' and atlas['canonical_space'] == 'VHF-image-2022'
    # Validate everything before writing assets into the project.
    for chunk in atlas['chunks']:
        data = (source / 'public' / chunk['url'].lstrip('/')).read_bytes()
        compressed = (source / 'public' / chunk['gzip'].lstrip('/')).read_bytes()
        assert len(data) == chunk['bytes'] and len(compressed) == chunk['gzipBytes']
        assert hashlib.sha256(data).hexdigest() == chunk['sha256']
        assert gzip.decompress(compressed) == data
    for chunk in atlas['chunks']:
        for key in ('url', 'gzip'):
            shutil.copyfile(source / 'public' / chunk[key].lstrip('/'), ROOT / 'public' / chunk[key].lstrip('/'))
    shutil.copyfile(manifest, ROOT / 'public/models/atlas-female-expanded.json')
    evidence = ROOT / 'public/female-sources'
    for relative in (
        'registry/composition-recipe.json', 'registry/review-status.json',
        'transforms/canonical-space.json', 'transforms/hra-stage-to-vhf.json',
        'transforms/denver-stage-to-vhf.json', 'transforms/nlm-stage-to-vhf.json',
        'transforms/nlm-ct-to-vhf.json', 'generated/registration-report.json',
    ):
        target = evidence / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, target)
    report = {
        'sourceRepository': 'https://github.com/rubdttcom/human-atlas',
        'sourceRevision': REVISION,
        'manifestSha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
        'anatomicalReview': 'pending',
        'counts': {'originalMeshes': len(original['parts']), 'expandedMeshes': len(atlas['parts']),
                   'retainedHraMeshes': sources['hra-female'], 'addedVhfMeshes': 229,
                   'excludedHraMeshes': len(original['parts']) - sources['hra-female'],
                   'concepts': len(atlas['concepts'])},
        'meshesBySource': sources,
        'systems': [
            {'id': system,
             'original': sum(p['system'] == system for p in original['parts']),
             'expanded': sum(p['system'] == system for p in atlas['parts'])}
            for system in sorted({p['system'] for p in original['parts'] + atlas['parts']})
        ],
        'remainingGaps': [
            'Hands and forearm bones (radius and ulna) are absent.',
            'Most upper-body, arm and hand muscles are absent.',
            'Small peripheral nerves, vessels and connective tissues have partial coverage.',
            'Some CT labels and foot meshes group multiple structures.',
            'The expanded assembly has no whole-body skin surface.',
            'CT boundaries, HRA organ placement and anatomical equivalences remain unreviewed.',
        ],
    }
    (evidence / 'coverage.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f"Imported {len(atlas['parts'])} meshes: {dict(sources)}. Anatomy remains incomplete and unreviewed.")


if __name__ == '__main__':
    main()
