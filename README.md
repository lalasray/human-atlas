# Human Atlas

An interactive 3D anatomy explorer built with React, Three.js, and shadcn/ui. Explore the male reference (2,234 meshes), expanded female assembly (1,025 meshes), and neonatal brain (85 regions). This repository is maintained at [lalasray/human-atlas](https://github.com/lalasray/human-atlas).

## Explore

- Orbit, zoom, and select structures directly on the body.
- Toggle individual systems or use skeleton and organ presets.
- Move from assembled anatomy to a spaced inventory of every visible piece.
- Search anatomical names and source identifiers.
- Isolate a selected structure and read its details.
- Use compact controls and detail panels on mobile.

## Run locally

Requires Node.js 22.13 or newer. No API keys or accounts are needed.

```sh
npm ci
npm run dev
```

Open http://localhost:3016. To build the static site, run `npm run build`; the output is in `dist/`.

## Validate

```sh
npm run check
node scripts/validate-atlas.mjs
node scripts/validate-atlas.mjs atlas-female-expanded.json
node scripts/validate-atlas.mjs atlas-infant.json
python3 scripts/validate-composition.py
python3 scripts/validate-provenance.py
node --experimental-strip-types scripts/validate-interactions.mjs
npm run build
```

Validation covers mesh buffers, names and concept membership, nonoverlapping exploded layouts at desktop and mobile aspect ratios, search and inspection contracts, and tap-versus-drag handling. Browser interaction checks have exercised selection, system controls, search, isolation, rotation, and 390×844, 320×568, and 844×390 layouts. Phone controls stay clear of the exploded inventory, and isolated structures fit the space above or beside the detail panel. Physical-device performance and real multitouch hardware have not been tested.

## Anatomy data

The male reference uses **BodyParts3D 4.0**, licensed **CC BY 4.0**. The female and infant references and their separate source terms are described below. It does not represent every human structure or variation. Individual source meshes are distinct from named concepts, which may group multiple meshes. Descriptions distinguish general system context from individual organ explanations.

Geometry is simplified for browser performance while retaining every source mesh. The packaged model contains 2,288,268 triangles and downloads approximately 33 MB of compressed geometry. Full credits, source links, and adaptation details are in [ATTRIBUTION.md](public/ATTRIBUTION.md).

This is an educational explorer, not a diagnostic or surgical tool.

## How it works

Geometry is merged into batches. Per-structure GPU textures control translation, visibility, and selection, while component geometry supports accurate picking. Exploded layouts pack only the visible pieces. Rendering updates when the scene changes; orbit controls remain responsive without thousands of separate draw calls.

The optional WebMCP tools expose anatomy search and inspection in compatible browsers. The visible interface works without them.

## Rebuilding geometry

The repository includes browser-ready geometry. Rebuilding it is optional: obtain the official BodyParts3D OBJ archive and English metadata tables, prepare the joined concepts and display-system mappings, run `scripts/convert-anatomy.py`, then `node scripts/optimize-anatomy.mjs` and `node scripts/compress-models.mjs`. Simplification uses a 0.2% relative error limit per structure.

## Deploy

Import this repository into Vercel as a Vite project. The included `vercel.json` configures `npm ci`, `npm run build`, and the `dist` output directory. It can also be served by a static host.

## License

Original application code is released under the [MIT License](LICENSE). **Anatomy data has separate source terms**: CC BY 4.0 for BodyParts3D, HRA and Denver; NLM terms for the CT-derived data; CC BY 3.0 for inherited ontology metadata. Preserve the source attribution when redistributing it. Third-party dependencies retain their respective licenses.

Issues and pull requests are welcome. Please include reproduction steps and browser/device details for interaction problems.

## Female anatomy

The reference selector offers Male · BodyParts3D, Female · Expanded, and Infant · Brain. `/?sex=female` opens the expanded assembly. Older female links with `reference=hra` also open the expanded assembly. Search, layers, inspection, isolation and explosion use the selected model. Switching clears the prior model's selection and view state.

The expanded reference combines the repository’s [composition 0.5 catalog](public/atlases/composed.json) with the MOOSE extension: **1,025 meshes, 943 distinct named concepts and 3,530,527 triangles** (about 43 MB compressed geometry), including a local MOOSE extension. It combines:

- 128 University of Denver Visible Human Female lower-limb meshes: 28 bones, 76 muscles, 16 cartilages and 8 ligaments.
- 101 automatic NLM Visible Human Female CT labels: skull, ribs, spine, shoulder/upper-arm bones, trunk organs and other structures from the same donor.
- 786 HRA detail meshes, including the female reproductive structures.
- 10 new same-donor MOOSE CT labels: left/right carpal, metacarpal and finger bone groups, plus partial left/right radius and ulna references.

The 239 Denver/CT meshes replace or supplement the HRA reference. The expanded assembly excludes 102 HRA meshes due to overlap or pose, including its skeleton and skin surface. Mesh counts are not a percentage of anatomical completeness: some source meshes contain groups, while some organs are split into multiple pieces. The original HRA assembly remains a source dataset for rebuilding; the viewer offers only the expanded female model. Eight pregnancy reference meshes are hidden by default in the expanded female option.

**This is incomplete and anatomically unreviewed.** Forearm boundaries remain partial where the CT cuts off the arms, and hand bones are grouped. Most upper-body/arm/hand muscles and many small nerves, vessels and connective tissues remain absent or partial. HRA placement is experimental; automatic CT boundaries and registration require anatomical review. The viewer exposes source provenance per selection and coverage/limitations under Coverage & sources.

Composition 0.5 preserves per-mesh provenance and registration records, and groups multiple pieces of one canonical structure into a single search result. The 943 concepts include the ten added bone labels; fewer concepts reflects catalog deduplication, not removed meshes. The local hand/forearm extension uses the existing same-donor transform; its conversion and limitations are recorded separately. See [attribution](public/ATTRIBUTION.md), the [coverage report](public/female-sources/coverage.json), and [research notes](docs/female-anatomy-sources.md).

The full source registry, ontology crosswalk, cryosection preparation, composition, and review tools are retained in this repository. See [reproduction instructions](docs/REPRODUCIBILITY.md). After rebuilding the base composition, reattach the committed MOOSE extension:

```sh
python3 scripts/refresh-female-expansion.py
```

Coverage & sources provides the source catalog, per-structure provenance downloads, and alignment review. Source-specific datasets remain available for research and rebuilding, with their own frames and licenses.

## Infant anatomy

`/?model=infant` opens **85 neonatal brain regions** from the dHCP population
atlas at 40 weeks post-menstrual age. The existing model was found in the local
HumanAnatomyFemale project and imported with source hashes and credits. It is
brain-only: skull, body skeleton, muscles and internal organs are still missing.
The display keeps its source metric scale and uses a rigid rotation/translation;
no registration to an adult body is performed. The camera fits the smaller model.

The source data is CC BY 4.0. See [infant sources and remaining gaps](docs/infant-anatomy-sources.md)
and [import evidence](public/infant-sources/coverage.json). To reproduce:

```sh
python3 scripts/import-infant.py /path/to/HumanAnatomyFemale
node scripts/validate-atlas.mjs atlas-infant.json
```
