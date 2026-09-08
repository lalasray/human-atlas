# Human Anatomy Atlas

Local fork of [ashemag/human-atlas](https://github.com/ashemag/human-atlas), combining
open anatomical sources with a source record for every mesh. The original
React/Three.js renderer, search, system layers, isolation and exploded views are
retained. New controls expose source/donor evidence, licences, transforms, geometry
checks and an interactive coverage table.

**Work in progress. The atlas is not anatomically validated or complete.**

| Public model | Included geometry | Interpretation |
| --- | --- | --- |
| Female | 1,015 meshes, 933 canonical concepts | Unified experimental adult female composition. Exact duplicates use Denver VHF, then same-donor NLM CT, then HRA reference detail. Anatomy remains unreviewed. |
| Male | 2,234 meshes, 3,432 concepts | BodyParts3D 4.0 adult male reference anatomy. |
| Infant | 85 brain regions | Brain-only dHCP aggregate neonatal reference at 40 weeks post-menstrual age, derived from 275 structurally normal neonatal MRI scans. Mixed-sex population; not a whole-body infant model. |

The 4,400 catalog entries are the imported source union, not a complete anatomical
ontology. Dataset-local labels and lateralized FMA identifiers resolve to UBERON/FMA
through a crosswalk with Ontology Lookup Service evidence (1,712 meshes; anatomist review
pending), so 248 entries now list several sources. Current reports separately identify 128
measured-female entries (Denver VHF), 231 entries natively in the canonical space (Denver
and NLM CT), 114 same-donor CT labels, 717 female-reference entries and 1,461 template-only
entries. Hierarchy-only entries without direct meshes must not be confused with missing
human anatomy.

## Run the viewer

Everything the viewer needs is committed: the optimized geometry (`public/models/`, about
340 MB), the enriched atlases (`public/atlases/`), the coverage matrix and the registration
report. No Python, no downloads and no segmentation are required to look at the atlas.

```bash
npm ci
npm run dev -- --port 3017
```

Open http://localhost:3017. The model selector offers Female, Male, and Infant.
The Infant choice is intentionally brain-only because no comparable openly redistributable
whole-body infant atlas was identified.

## Rebuild the data

Only if you want to regenerate or extend the geometry (new sources, new segmentation,
new registration). It downloads about 2 GB of source data (TCIA, Denver, NLM CT), needs two
Python environments and a CPU run of TotalSegmentator of about 35 minutes. The full order
of scripts and verification steps is in
[docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md); the GitHub release `data-2026-09-05` provides the prepared source and intermediate data (412 MB) so the download and segmentation steps can be skipped. Keep `data/` and `.venv-seg/` out of the
Vite root scan (they are in `.gitignore`), otherwise the dev server and the build stall.

## Data and checks

- [Implementation status and remaining work](docs/PROGRESS.md)
- [Full original plan](docs/plans/female-open-human-atlas-plan.md), [cryosection segmentation project plan](docs/plans/vhf-cryosection-segmentation-plan.md)
- [Reproducible download, conversion and verification](docs/REPRODUCIBILITY.md)
- [Dataset inventory](datasets.csv), [structure catalog](structures.csv), [coverage](coverage.csv)
- [Source records](registry/sources.json), [donors](registry/donors.json), [licences](registry/licences.json)
- [Registration evidence](generated/registration-report.md), [NLM CT registration and frame verification](generated/nlm-ct-registration.json), [geometry QA](generated/qa-report.md), [anatomy QA](generated/anatomy-qa.json)
- [Ontology crosswalk](registry/ontology-crosswalk-reviewed.json), [BMFToolkit comparison](generated/bmftoolkit-comparison.md), [review registries](registry/review-status.json)
- [Attribution](public/ATTRIBUTION.md), [original upstream README](docs/UPSTREAM-README.md)

The source binary buffers retain their original geometry identity. Every record
includes source asset, source revision or input hash, chunk SHA-256, donor evidence,
geometry type, applied display transform, licence and review status. Confidence is
unassessed unless evidence establishes it. The composite is expressed in canonical
space VHF-image-2022; the same-donor CT placement is a rigid surface fit and the HRA
placement an experimental proxy fit, not reviewed anatomical registrations. The neonatal
brain remains in its own dHCP atlas frame and is not merged with either adult model.

```bash
npx tsc --noEmit
python3 scripts/validate-provenance.py
.venv/bin/python scripts/validate-composition.py
.venv/bin/python scripts/validate-reviews.py
./atlas check-licenses --target open-clean
npm run build
```

Input volumes and external source repositories are excluded from Git. The VHF trunk,
upper limb and head come from automatic CT labels of the same donor; VHF hands, forearm
bones and CT appendicular bones, specialist datasets, anatomist review of landmarks,
labels and ontology equivalences remain unfinished. Denver assets need
`scripts/fetch-denver.py` (local Chrome) because the publisher's endpoint rejects plain
HTTP clients. BMFToolkit's 63 meshes are compared bone by bone with Denver but are not
part of the public build until the authors confirm the data licence.

Application code: MIT. Included data: CC BY 4.0 sources with separate attribution, plus NLM Visible Human images under the NLM Terms and Conditions ("Courtesy of the U.S. National Library of Medicine").
