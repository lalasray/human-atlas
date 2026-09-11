# Human Atlas — Male, Female & Infant

An interactive 3D anatomy explorer maintained by [lalasray](https://github.com/lalasray/human-atlas). Choose **Male**, **Female**, or **Infant** to explore anatomy through search, system layers, individual structure inspection, and exploded views.

## The three models

| Model | Included anatomy | Meshes | Named concepts |
| --- | --- | ---: | ---: |
| **Male** | Adult male reference from BodyParts3D 4.0 | 2,234 | 3,432 |
| **Female** | Expanded assembly combining HRA detail, Visible Human Female lower limbs and CT-derived structures | 1,025 | 943 |
| **Infant** | Brain and chest together: 85 brain regions and nine chest organ/tissue groups | 94 | 94 |

Mesh counts describe the imported geometry, not anatomical completeness. A mesh can contain several structures, and a named concept can select more than one mesh.

### Male

The BodyParts3D reference includes the skeleton, muscles, internal organs, nerves, vessels, and other anatomical systems. The browser model has 2,288,268 triangles and about 33 MB of compressed geometry. It represents one adult male reference rather than every anatomical variation.

### Female

The Female option uses the expanded assembly: 786 HRA detail meshes, 128 University of Denver lower-limb meshes, 101 NLM Visible Human Female CT labels, and 10 MOOSE hand/forearm labels. It includes female reproductive anatomy, trunk organs, the skeleton, and lower-limb muscles. Eight placenta and umbilical reference parts are available in the Pregnancy reference layer and hidden by default.

The model has 3,530,527 triangles and about 43 MB of compressed geometry. Hand bones remain grouped, forearms are partial, and many upper-body muscles, small nerves, vessels, and the whole-body skin surface are still missing. Automatic CT boundaries and alignment between sources remain unreviewed. See [female coverage](docs/female-anatomy-sources.md) and the [assembly record](public/female-sources/coverage.json).

### Infant

The Infant option combines the dHCP neonatal brain with the Tyndall newborn chest in one scene. The chest includes heart, lungs, trachea, an artery region, bones, cartilage, muscle, fat, and skin. The brain is uniformly resized and positioned above the chest; all 94 parts are searchable and selectable. Muscle, fat, and skin layers are hidden initially to reveal the internal anatomy.

The model has 1,969,076 triangles and about 20 MB of compressed geometry. The brain and chest come from different sources, so their relative proportions and placement are approximate. Skull, face, neck, limbs, pelvis, abdominal and pelvic organs, and complete peripheral nerves and vessels are still missing. See [infant coverage](docs/infant-anatomy-sources.md) and the [combined display record](public/infant-sources/assembly.json).

## Explore

- Switch between Male, Female, and Infant in the model selector.
- Drag to orbit, scroll or pinch to zoom, and select structures directly.
- Search anatomical names, isolate a structure, and inspect its source details.
- Show or hide anatomical systems and optional tissue layers.
- Use the explosion slider to arrange visible parts into a selectable inventory.
- View coverage and credits; download provenance where available.
- Review the female assembly's source catalog and alignment records.

The viewer supports desktop and mobile layouts. These are educational references with incomplete coverage and unreviewed adaptations; they are not diagnostic or surgical models.

## Run locally

Requires **Node.js 22.13 or newer**. Browser-ready geometry is included; no accounts or API keys are needed.

```sh
npm ci
npm run dev
```

Open **http://localhost:3016**. Direct model routes are `/?sex=male`, `/?sex=female`, and `/?model=infant`. Older female links open the expanded female model; older infant brain and chest links open the combined infant view.

```sh
npm run build
```

The production site is written to `dist/` and can be served by a static host. The included `vercel.json` configures Vite deployment for this repository.

## Validate

```sh
npm run check
node scripts/validate-atlas.mjs
node scripts/validate-atlas.mjs atlas-female-expanded.json
node scripts/validate-atlas.mjs atlas-infant-expanded.json
node --experimental-strip-types scripts/validate-interactions.mjs
npm run build
```

These checks cover geometry buffers and hashes, bounds, concept membership, infant display transforms, search and inspection, and exploded layouts. `scripts/browser-check.py` exercises the viewer in Playwright Chromium against a running local server; set `ATLAS_URL` to the server address and optionally `CHROMIUM_EXECUTABLE_PATH` to an installed Chromium binary. Geometry checks do not establish anatomical accuracy.

## Data and rebuilding

The app uses React, Three.js, shadcn/ui, and Vite. The three viewer manifests are `public/models/atlas.json`, `atlas-female-expanded.json`, and `atlas-infant-expanded.json`. Source-specific datasets remain available as inputs to the reproduction pipeline.

- **Male:** `scripts/convert-anatomy.py`, `scripts/optimize-anatomy.mjs`, and `scripts/compress-models.mjs` prepare BodyParts3D geometry.
- **Female:** follow [reproduction instructions](docs/REPRODUCIBILITY.md), then run `python3 scripts/refresh-female-expansion.py` to include the hand/forearm extension.
- **Infant:** run `python3 scripts/build-infant-assembly.py` to combine the imported brain and chest. Source imports use `scripts/import-infant.py` and `scripts/import-infant-thorax.py`; chest conversion dependencies are in `requirements-infant-thorax.txt`.

See [architecture](docs/ARCHITECTURE.md) for rendering and pipeline details.

## Credits and licenses

Application code is covered by the [MIT License](LICENSE). Anatomy data has its own terms:

- **Male:** BodyParts3D, CC BY 4.0.
- **Female:** Human Reference Atlas and University of Denver, CC BY 4.0; NLM Visible Human data under NLM terms. MOOSE model weights are CC BY 4.0. Inherited ontology metadata includes CC BY 3.0 material.
- **Infant:** Developing Human Connectome Project and Tyndall newborn thorax datasets, CC BY 4.0.

Preserve the original dataset credits and adaptation notices when redistributing. Full source links, licenses, and changes are documented in [ATTRIBUTION.md](public/ATTRIBUTION.md).
