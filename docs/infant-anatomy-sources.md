# Infant anatomy coverage — 11 September 2026

The viewer offers exactly **Male, Female, and Infant**. Infant combines all
**85 brain regions and nine chest organ/tissue groups** in one scene. These
remain distinct source datasets with different ages and donors; the brain is
resized and placed above the chest for an approximate display assembly.

## Combined infant display

`scripts/build-infant-assembly.py` reads the unchanged source manifests
`atlas-infant.json` and `atlas-infant-thorax.json`, verifies their geometry hashes,
and builds `atlas-infant-expanded.json`. All 94 parts and concepts are retained.
The chest keeps its original size and organ placement. A uniform brain scale of
about **1.1426** sets brain width to **78% of chest width**, and a translation
places its lowest point about **6.3 mm** above the chest. These are display choices,
not measured anatomical proportions or a validated registration. No neck or
other missing tissue is synthesized. Normals and triangle indices are preserved.

The shared viewer supports search, layers, inspection, isolation and explosion
across both sources. Its opening view shows 91 parts; muscles, fat and skin can
be enabled using the layers. `/?model=infant`, old `/?model=infant-thorax` links
and the legacy source parameters all open the same combined model.

`public/infant-sources/assembly.json` records input manifest hashes and display
matrices. Per-part provenance retains the original source conversion record and
the additional assembly transformation. Rebuild after either source import:

```sh
python3 scripts/build-infant-assembly.py
node scripts/validate-atlas.mjs atlas-infant-expanded.json
```

## Newborn chest added

Andrea Pacheco, Baptiste Jayet and Stefan Andersson-Engels (Tyndall National
Institute) published [a discrete newborn thorax mesh](https://zenodo.org/records/4916863),
v1.0.0, DOI **10.5281/zenodo.4916863**, under **CC BY 4.0**. The actual record,
source README, file identities and conversion report are preserved in
`public/infant-sources/thorax/`. The related [neonatal thorax study](https://doi.org/10.1117/1.JBO.25.11.115001)
describes the CT-derived anatomy and optical phantom work.

The source describes an anonymized newborn CT from Cork University Hospital,
with approval recorded by the dataset authors. The infant was born at 36 weeks
gestation with a birth weight of 3.58 kg. The dataset does not report sex or the
age at the CT scan; gestational age at birth is not treated as imaging age.

| Source label(s) | Selectable chest region | Display system |
| --- | --- | --- |
| 1, 10, 11 | Lungs (group) | Respiratory |
| 2 | Chest bones (group) | Skeleton |
| 3 | Chest cartilage (group) | Connective tissue |
| 4 | Heart | Heart |
| 5 | Chest muscles (group) | Muscles |
| 6 | Artery (source region) | Arteries |
| 7 | Chest fat | CT tissue maps |
| 8 | Chest skin | Body surface |
| 9 | Trachea | Respiratory |

The three source lung subdivisions are experimental inner/middle/outer regions,
not anatomical lobes. They are combined into one lung mesh. Bones, muscles and
arteries remain grouped: no individual rib, muscle, artery or laterality labels
are invented.

### Conversion and limitations

The downloaded `mesh.mat` is a MATLAB 7.3/HDF5 nodal mesh with 229,363 nodes and
**1,356,069 tetrahedra**. The README has a different count in one format-description
line; the actual array shape is used. Published MD5 hashes and sizes were verified.
Input SHA-256: `7de29df4092f47f702b7a27d0c6c3e147f953dcc6db8d8bc3ddda7fd4d9e77a3`.

Each region is a binary indicator on the original mesh nodes. VTK clips its
linearly interpolated value at 0.5, then extracts the surface of the retained
cell pieces, including the scan's cut faces. Coincident vertices are welded and
normals computed. The conversion does not smooth or simplify the surfaces, add
labels, fill missing anatomy, or run a new segmentation. The resulting nine
meshes contain **952,150 triangles** and about **12.4 MB** of compressed geometry.

A shared display rotation/translation converts source millimetres to metres,
centres the chest, and places it above the viewer floor. Inter-organ distances
are preserved. The source has no anatomical orientation header; anatomical
laterality is unverified. The display matrix and software versions are recorded.

The source was made for optical simulation and treats regions as homogeneous.
Fine structures are absent, small disconnected pieces remain, and several
surfaces have nonmanifold edges. These are reported per region in
`public/infant-sources/thorax/coverage.json`; successful buffer checks do not
constitute anatomical or printability validation. Bones and cartilage can be
shown with the layer controls, while the opening view reveals the internal organs.

### Reproduction

Download the record metadata, `mesh.mat`, and `readme.md` from Zenodo record
4916863 to `data/raw/infant-thorax/` (which is ignored by Git). Install
`requirements-infant-thorax.txt` in a virtual environment, then run:

```sh
python scripts/import-infant-thorax.py
node scripts/validate-atlas.mjs atlas-infant-thorax.json
```

The script validates the pinned file hashes, source license and region labels
before writing the manifest, packed geometry, source evidence and coverage.
Run the assembly builder to update the shared Infant view. The chest-only manifest remains a pipeline input.

## Existing neonatal brain

The [dHCP morphological atlas](https://gin.g-node.org/BioMedIA/dhcp-volumetric-atlas-groupwise),
revision `d699540b1820d8224a07db3c1d727d0c747218dc`, provides the 40-week
post-menstrual-age structural segmentation. It is a mixed-sex population atlas.
All 85 non-background labels from the existing conversion are retained.
The brain is included in the combined `/?model=infant` view. See `public/infant-sources/coverage.json`
for its independent import evidence. Reproduction uses
`python3 scripts/import-infant.py /path/to/HumanAnatomyFemale`.

## Remaining gaps and other leads

The combined reference still lacks a full skull/head, limbs, pelvis, abdominal
or pelvic organs, or complete peripheral nerves and vessels. A whole-body infant
source with suitable download and redistribution terms is still needed.

- [NCI PHANTOM library](https://dceg.cancer.gov/tools/radiation-dosimetry-tools/phantoms-library):
  includes pediatric reference anatomy, but access requires a Software Transfer
  Agreement for noncommercial research. It was not downloaded or redistributed.
- [ICRP Publication 156](https://www.icrp.org/publication.asp?id=ICRP+Publication+156):
  describes newborn and one-year male/female mesh phantoms. A freely
  redistributable data release was not established in this review.
- **Thalia**, a 10-month female model with 442 segments, was described in a
  [July 2026 preprint](https://doi.org/10.64898/2026.07.09.737638). The prior review
  found release deferred until publication; no verified data release was added.
- The [IT'IS hosted-model listing](https://itis.swiss/virtual-population/virtual-population/hosted-models/overview)
  includes MARTIN (29 months) and ATHENA (3.5 years), which are older children.

No restricted model was imported and no access request was sent to a third party.
