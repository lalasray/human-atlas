# Anatomy data attribution

BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International.

- License: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html (updated 2025-02-27)
- Dataset: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html
- License terms: https://creativecommons.org/licenses/by/4.0/
- Source geometry: `isa_BP3D_4.0_obj_99.zip`, BodyParts3D 4.0.
- English names and relationships: IS-A and PART-OF concept, element, and inclusion tables from the same archive.
- Publication: Mitsuhashi et al. (2009), BodyParts3D: 3D structure database for anatomical concepts. https://doi.org/10.1093/nar/gkn613

Adaptations: axes and units converted from millimeters/Z-up to meters/Y-up; translated to rest at the stage; geometry simplified using meshoptimizer with 0.2% relative error limit per structure; normals quantized to signed 16-bit; packed into binary chunks; curated display system groupings and colors. The source contains 2,234 individual OBJ meshes; all remain represented. The combined hierarchy contains 3,432 named FMA concepts, which may reference multiple meshes. Original source identity is preserved in the manifest.

Source OBJ comments mention an older CC BY-SA 2.1 Japan license. The official current database license linked above supersedes that legacy text and explicitly permits redistribution and adaptation under CC BY 4.0.

BodyParts3D represents an adult male reference anatomy based on TARO MRI and anatomical illustration refinements. It is not a complete model of every possible human anatomical structure or variation. This interface is educational and is not a clinical tool.

## Female reference anatomy

Female reference anatomy: Kristen Browne and Heidi Schlehlein, Human Reference Atlas / HuBMAP, *3D Reference Organ Set for Female v1.5* (2023). CC BY 4.0. Geometry adapted for this viewer.

- Source DOI: https://doi.org/10.48539/HBM352.BTSQ.586
- Dataset: https://lod.humanatlas.io/ref-organ/united-female/v1.5
- Original GLB: https://cdn.humanatlas.io/digital-objects/ref-organ/united-female/v1.5/assets/3d-vh-f-united.glb
- License: https://creativecommons.org/licenses/by/4.0/

Adaptations: translated native meter/Y-up coordinates onto the stage, coincident vertices welded and source normals averaged, geometry simplified with a 0.2% per-structure relative error bound, and normals quantized. Colors and display systems are curated for this interface. The upstream HRA source has 888 meshes and 1,073 source nodes. This release retains 786 HRA meshes within the expanded assembly; the standalone original HRA model is not shipped.

This is a reference assembly with whole-body surface and selected organs, including female reproductive anatomy. Its skeleton and muscle coverage is partial. It is not a complete model of every human structure or a single-person scan. Eight placenta/umbilical structures are classified under Pregnancy reference and hidden by default.

Imported HRA geometry and per-mesh provenance from https://github.com/rubdttcom/human-atlas at revision `f1c09ede05984702c98fc89198b1f1e2c60f073f`. Binary geometry is unchanged. Per-component donor identity is unresolved and anatomical review is pending.

## Expanded female assembly

The expanded option uses Female Open Human Atlas composition 0.4 from
[rubdttcom/human-atlas](https://github.com/rubdttcom/human-atlas), revision
`f1c09ede05984702c98fc89198b1f1e2c60f073f`. Its 1,015 meshes contain 786 HRA reference
meshes, 128 Denver lower-limb meshes and 101 NLM CT labels. The 229 Denver and CT
meshes describe the same Visible Human Female donor. HRA component donors remain
unresolved. This is an incomplete, experimentally aligned assembly; anatomical
review is pending. The standalone original HRA view is not included.

### University of Denver Visible Human Female, 2022

Andreassen, T. E., Hume, D. R., Hamilton, L. D., Walker, K. E., Higinbotham, S. E.
and Shelburne, K. B. *Three-dimensional lower extremity musculoskeletal geometry
of the Visible Human Female and Male.* Scientific Data.
https://doi.org/10.1038/s41597-022-01905-2.

Dataset: https://digitalcommons.du.edu/visiblehuman/1/
(DOI https://doi.org/10.56902/COB.vh.2022.1), University of Denver Center for
Orthopaedic Biomechanics. CC BY 4.0. Supported by NIH grant U01 AR072989.
Overclosure processing: https://doi.org/10.48550/arXiv.2209.06948.

Included: all 128 final meshes (28 bones, 76 muscles, 16 cartilages and 8
ligaments). The authors manually segmented the female cryosections, smoothed
surfaces and corrected overlaps. Upstream adaptations: STL vertices welded;
source axes and millimetres converted to viewer metres; normals derived;
meshoptimizer simplification with 0.2% relative error; binary packing and gzip.
Their native aligned image frame defines the assembly's coordinate system.

### NLM Visible Human Female CT-derived meshes

Courtesy of the U.S. National Library of Medicine.

Images: The Visible Human Project, Female data set (1995), fresh CT acquired
22 September 1993. Source:
https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Female-Images/radiological/normalCT/
Terms: https://www.nlm.nih.gov/databases/download/terms_and_conditions.html.
NLM does not endorse this application. Derived meshes are produced by the source
repository and do not reflect the most current or accurate NLM data.

Segmentation: Wasserthal et al. (2023), *TotalSegmentator: Robust Segmentation of
104 Anatomic Structures in CT Images*, https://doi.org/10.1148/ryai.230024.
Upstream used TotalSegmentator 2.18.0, task `total` (Apache-2.0), CPU inference.
These are automatic, unreviewed labels, sometimes grouping structures.

Upstream adaptations: CT slices assembled and resampled; marching cubes per
label; small islands removed; rigid same-donor pelvis registration into the
Denver frame; axis and unit conversion; meshoptimizer simplification; normal
quantization; binary packing and gzip. 101 of 114 source labels are included;
Denver replaces overlapping pelvis, femur and lower-limb muscle labels.

### Composition and local import

Upstream retains 786 HRA meshes after excluding its skeleton, whole-body skin,
lower-limb muscle overlaps and organs covered by CT labels. HRA organ detail is
placed using a six-organ proxy similarity fit (RMS 7.42 mm); head detail uses a
separate brain-envelope fit. NLM CT uses a rigid pelvis fit (p95 4.72 mm). These
measurements describe the fitted proxies; they do not establish anatomical
accuracy or validation of the assembled body.

The base import preserves all composed geometry buffers, source hashes, per-mesh
provenance, transforms and review status without performing new alignment or
segmentation. The import script checks the pinned source revision, SHA-256
hashes and gzip equivalence. Evidence and coverage counts are served under
`/female-sources/`. HRA exclusions are recorded in
`/female-sources/registry/composition-recipe.json`.

Ontology metadata carried by the source includes UBERON (CC BY 3.0) and FMA
(CC BY 3.0, Structural Informatics Group, University of Washington), retrieved
through the EBI Ontology Lookup Service: https://www.ebi.ac.uk/ols4/.

## Additional female hand and forearm CT references

Courtesy of the U.S. National Library of Medicine. Ten additional VHF CT label
surfaces were segmented locally using MOOSE 3.2.2 by ENHANCE-PET, then converted
with marching cubes and the existing CT-to-VHF display transform. The NLM terms
apply to the source CT; these derivatives do not reflect the most current or
accurate NLM data, and NLM does not endorse this application.

- MOOSE: https://github.com/ENHANCE-PET/MOOSE
- Model weights: `clin_ct_peripheral_bones_ras_07052025.zip`, release `moosez-v.3.1.3`.
- Weights license: CC BY 4.0, https://github.com/ENHANCE-PET/MOOSE/blob/main/MODEL_LICENSE
- Code license: Apache 2.0.
- Changes: 848 finger-label voxels reassigned from right to left using source
  RAS coordinates; a two-voxel metacarpal fragment removed; no surface smoothing
  or simplification. Hand bones are grouped, forearms partial, and local anatomy
  unreviewed. Input and model hashes: `/female-sources/hand-forearm-qa.json`.

## Neonatal brain reference

The Infant option contains 85 regions from the Developing Human Connectome
Project (dHCP) morphological atlas at 40 weeks post-menstrual age. This is a
mixed-sex population brain reference, not a whole-body infant or an individual
female donor. Two background labels are excluded.

- Source: https://gin.g-node.org/BioMedIA/dhcp-volumetric-atlas-groupwise
- Data DOI: https://doi.org/10.12751/g-node.d2b353
- Citation: Schuh et al., *Unbiased construction of a spatio-temporal atlas of
  the neonatal brain*, https://doi.org/10.1101/251512
- License: CC BY 4.0; the source license is retained in
  `/infant-sources/LICENSE.md`.
- Pinned source revision: `d699540b1820d8224a07db3c1d727d0c747218dc`.
- Adaptations: marching-cubes surface extraction and meshoptimizer simplification
  in the existing HumanAnatomyFemale project, followed here by a rigid display
  rotation and translation. Metric scale is preserved. No registration to an
  adult body is performed. Local conversion remains anatomically unreviewed.
- Input and output hashes and display matrix: `/infant-sources/coverage.json`.
