# Infant coverage review — 9 September 2026

The current HumanAnatomy workspace had no infant body model. A neighboring local
project, HumanAnatomyFemale, contained an 85-region dHCP neonatal brain atlas.
That existing reference is now imported into this app as **Infant · Brain**.
It is not a complete infant body, and its regions are not new segmentations.

## Included

[dHCP morphological atlas](https://gin.g-node.org/BioMedIA/dhcp-volumetric-atlas-groupwise),
revision `d699540b1820d8224a07db3c1d727d0c747218dc`, provides the 40-week
post-menstrual-age structural segmentation. It is a mixed-sex population atlas.
All 85 non-background labels from the existing conversion are retained. Geometry
is reoriented into the viewer axes and translated above the floor without scaling.
The source volume, label table, chunk hashes, and gzip payloads are checked during
import. No alignment with either adult model is claimed.

The missing body includes skull/face, skeleton, muscles, internal organs,
peripheral nerves and vessels, and skin. Additional brain atlases do not fill
those gaps.

## Whole-body source found

**Thalia** is a promising 10-month-old female model with 442 MRI-derived tissue
segments, described in a [July 2026 preprint](https://doi.org/10.64898/2026.07.09.737638).
However, the paper's Data Availability section says release will follow
publication through ABILAB/Martinos and IT'IS, including segmentations and STL
surfaces. The [IT'IS hosted-model list](https://itis.swiss/virtual-population/virtual-population/hosted-models/overview)
checked during this review lists MARTIN and ATHENA, but not Thalia. A downloadable
Thalia release and data reuse license were not verified. Nothing was imported.

The abstract's description of an open resource is not sufficient evidence that
the dataset is downloadable now. The preprint copyright notice is also separate
from the eventual model license. Once released, Thalia should remain a distinct
10-month reference; it should not be presented as a body belonging to the
40-week dHCP neonatal population brain.

MARTIN (29-month boy) and ATHENA (3.5-year girl), listed on that same provider
page, are older children and do not supply neonatal anatomy. The
[ICRP paediatric phantoms](https://doi.org/10.1177/0146645320915031) include
newborn reference bodies, but this review did not establish a freely
redistributable surface-mesh release for this app.

## Reproduction

`python3 scripts/import-infant.py /path/to/HumanAnatomyFemale`

`node scripts/validate-atlas.mjs atlas-infant.json` validates geometry, scale,
provenance, excluded background labels, and packed buffers. The app's interaction
checks include infant search, isolation selection, explosion packing and URL
switching. Credits and conversion details are in `public/ATTRIBUTION.md` and
`public/infant-sources/`.
