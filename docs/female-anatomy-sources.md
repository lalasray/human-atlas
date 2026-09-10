# Female anatomy expansion — updated 9 September 2026

## Integrated data

The HRA-only view omitted most limb musculature and the upper skeleton. The
expanded view imports the already aligned composition 0.4 from
[Female Open Human Atlas](https://github.com/rubdttcom/human-atlas/tree/f1c09ede05984702c98fc89198b1f1e2c60f073f).
That pinned repository supplies browser-ready buffers, source hashes,
per-mesh provenance, inclusion/exclusion decisions and alignment evidence.

| Source | Included | Evidence and limitations |
| --- | ---: | --- |
| [Denver Visible Human Female](https://digitalcommons.du.edu/visiblehuman/1/) | 128 meshes | Female donor; manually segmented bones, muscles, cartilage and ligaments from pelvis to feet; source smoothed and corrected overlaps. CC BY 4.0. |
| [NLM Visible Human Female CT](https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Female-Images/radiological/normalCT/) | 101 labels | Same donor as Denver; automatic TotalSegmentator labels converted upstream to surfaces. Includes skull, ribs, spine, shoulder/upper-arm bones, trunk organs. [NLM terms](https://www.nlm.nih.gov/databases/download/terms_and_conditions.html). |
| [HRA United Female v1.5](https://lod.humanatlas.io/ref-organ/united-female/v1.5) | 786 meshes | Reference organ detail, including female reproductive structures. Per-component donors unresolved. CC BY 4.0. |

There are 229 added donor-derived meshes and 102 excluded/replaced HRA meshes,
giving 1,015 meshes, a net increase of 127. This is not a completeness percentage.
Grouped CT labels, detailed substructures and compound concepts cannot be counted
as equivalent units. The standalone HRA original is no longer shipped; its retained detail remains in the expanded assembly.

The base import performed no new anatomical fitting or segmentation locally. The September 9 hand/forearm extension described below performs a new automatic segmentation. Upstream's
composition validator confirmed every transformed vertex against the source
matrix, unchanged indices and same-donor geometry identity. NLM pelvis fit p95
is 4.72 mm; HRA organ-proxy fit RMS is 7.42 mm. These are geometric checks on
specific proxies, not an anatomical review or a guarantee of accurate placement.

## Hand and forearm extension

On September 9, ten new automatic CT label meshes were added with
[MOOSE](https://github.com/ENHANCE-PET/MOOSE): left/right carpal, metacarpal and
finger bone groups, plus left/right radius and ulna references. The assembly now
has **1,025 meshes, 1,281 concepts and 3,530,527 triangles**. The addition is
2.94 MB compressed. All ten use the same VHF donor and existing CT-to-VHF matrix.

The original prepared CT checksum was verified. MOOSE 3.2.2 ran on its first
1,100 slices with the `clin_ct_peripheral_bones` model (CC BY 4.0 weights).
Marching cubes generated the surfaces without smoothing or simplification.
An 848-voxel finger fragment had the wrong side label and was reassigned using
source RAS coordinates; a two-voxel metacarpal fragment was removed. These edits,
input/model hashes, components and transforms are in
[hand-forearm-qa.json](../public/female-sources/hand-forearm-qa.json).

**Forearm references are partial**, because the scan cuts off parts of the arms;
the right ulna is fragmented. The hand meshes group bones, including some merged
boundaries. No anatomical review or completeness is claimed. The original 1,015
mesh buffers are unchanged. The NLM terms continue to apply to the source scan.

## Other sources investigated

- [TCIA Healthy Total Body CTs](https://www.cancerimagingarchive.net/collection/healthy-total-body-cts/): the linked repository has 36 published segmentation labels for female subject 003. A different donor, grouped bones and a different limb pose make it unsuitable as an automatic fill for this assembly. Its toes label has a documented outlier; it is excluded from composition 0.4.
- [Z-Anatomy](https://zenodo.org/records/4953712): detailed musculoskeletal geometry derived from BodyParts3D. It does not supply evidence of female donor geometry for filling these gaps. Not added to the female assembly.
- [NLM full Visible Human data](https://www.nlm.nih.gov/research/visible/visible_human.html): publicly available CT, MRI and cryosection images provide material for further segmentation, rather than a complete labelled mesh atlas.
- [Teem's Visible Female CT hands workflow](https://teem.sourceforge.net/nrrd/vfhand/index.html): documents extracting and masking hand volumes from the same donor. A useful next source for hand reconstruction, but it does not deliver separate, anatomically reviewed hand-bone meshes ready for this viewer.
- [Open Twin XR](https://github.com/Opening-Science/open-twin-xr): reviewed its source inventory. Its female whole-body addition uses TCIA; that does not resolve the same-donor labelled hand and muscle gaps here.
- [TotalSegmentator](https://github.com/wasserth/TotalSegmentator): its shoulder-muscle task covers additional muscles, but requires access to licensed weights. No access was obtained and no outputs were added.
- [OpenHands](https://github.com/abel-research/OpenHands): public statistical finger-bone models derive from a mixed male/female sample; they are not individual female donor anatomy. Not merged.
- [Visible Korean](https://sites.google.com/ajou.ac.kr/anatomy): a female whole-body 3D PDF is available, but the original release describes only 27 segmented structures. Later work describes a 459-structure female voxel phantom; current mesh access and redistribution terms were not established. The downloadable movable hand model traces to the male whole-body source and was not used as female anatomy.

## Remaining work

Hand bones now have grouped automatic CT references. Radius and ulna references
remain partial at clipped scan boundaries; the right ulna is fragmented. Most
upper-body, arm and hand musculature is absent. Peripheral nerves, vessels and connective tissues
have partial coverage; some foot meshes and CT labels group structures. There is
no whole-body skin in the expanded view because the original HRA pose differs.

A further same-donor expansion needs segmentation and labelling of hands,
forearms and upper-body muscles from the source images, followed by anatomical
review. CT boundaries, source ontology equivalences, head/cervical continuity
and all HRA placement also need review. The viewer labels the assembly as
experimental and exposes these limitations under Coverage & sources.

## Reproduction

Run `python3 scripts/import-female-expansion.py /path/to/human-atlas` with the
source clone at revision `f1c09ede05984702c98fc89198b1f1e2c60f073f`. The script
checks revision, buffer SHA-256, gzip equivalence, and donor-source counts before
copying. Base geometry is byte-identical to the upstream composition. Then run
the local extension with Python 3.12 and `moosez==3.2.2` (CPU torch/torchvision),
`nibabel`, `numpy`, `scipy`, `scikit-image` and `trimesh`:

```sh
python scripts/segment-female-bones.py /path/to/vhf-fresh-ct.nii.gz /path/to/output
python scripts/import-female-bones.py /path/to/output/clin_CT_peripheral_bones_segmentation_CT_vhf_upper.nii.gz
```

The prepared CT is available from the source repository's
[data release](https://github.com/rubdttcom/human-atlas/releases/tag/data-2026-09-05).
The importer pins the reviewed run's segmentation hash; a different result must
be inspected before updating that hash. Geometry checks are separate from
anatomical review.

Full credits and adaptations are in [ATTRIBUTION.md](../public/ATTRIBUTION.md).
The generated [coverage record](../public/female-sources/coverage.json) and
alignment/inclusion records under `public/female-sources/` are shipped with the app.
