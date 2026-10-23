# Internal — component radioactivity

Independent scientific entry point for component radioactivity. **Preferred v3**
uses physical 50 µm PMMA/Acrylic cores in both GEM and cathode, with Table 7.1
Acrylic U/Th/K and EFCu skins (U/Th only): **26 contributions**. v2 remains
supported with Kapton cores and Arnquist Table 5 layer assays (28 contributions).
Dimensions, sampling, isotope-chain controls and other v2 components stay the same.
New physical v3 transport requires new ROOT files for all 26 contributions.
This area uses the **one common Geant4 application** in the repository root. It is not a second detector build.

`analysis`, `study`, `config`, `macros`, `legacy`, `validation` and the historical
guides in `docs` are relative symbolic links to their authoritative existing
locations. They are intentional compatibility views, not copied implementations.
Keep symlinks when cloning/copying the checkout. From this directory or the root,
Python resolves the real source location; archived campaigns retain their paths.

| Entry | Purpose |
|---|---|
| `macros/` | Internal diagnostic/historical Geant4 macros |
| `config/study/` | Source matrices, assays and campaign configurations |
| `study/simulate.py`, `study/preflight.py` | Simulation, resume, decay qualification |
| `analysis/common_c++/AnalyzeCompactCampaign.cpp` | Preferred native compact ROOT analysis |
| `analysis/raw/`, `analysis/compact/`, `analysis/common/` | Python readers, canonical groups, internal reports and notebooks |
| `analysis/reference_cpp/` | Historical C++ ROOT references and raw processing |
| `legacy/` | Archived combined runners/configuration; not production defaults |
| `cluster/run.sh` | Configurable cluster entry point |
| `docs/WORKFLOW.md` | Local/cluster execution and normalization contract |

## Build once, run internal

Set `CYGNO_SRC` to the **parent repository root**, `CYGNO_BUILD` to an external
build directory, and `CYGNO_RUNS` to an external results directory. Activate the
site's Geant4 environment first. Python ≥3.10 is required.

```bash
cmake -S "$CYGNO_SRC" -B "$CYGNO_BUILD" -DCMAKE_BUILD_TYPE=Release \
  -DWITH_GEANT4_UIVIS=OFF -DCYGNO_BUILD_ANALYSIS=OFF -DBUILD_TESTING=OFF \
  -DGeant4_DIR=/path/to/geant4/lib/cmake/Geant4
cmake --build "$CYGNO_BUILD" --parallel
cd "$CYGNO_SRC"
python3 internal/study/preflight.py --build "$CYGNO_BUILD" --model cygno-acrylic-v3 \
  --output "$CYGNO_RUNS/internal-v3-preflight-NEW"
python3 internal/study/simulate.py --config internal/config/study/cygno-11x7-v3.json \
  --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/internal-v3-smoke-NEW" \
  --mode smoke --primaries 2 --output-mode compact --jobs 4
```

Omitting `--mode` on `rdecay01` still means internal, unshielded,
`QGSP_BIC_EMZ + G4RadioactiveDecayPhysics`. `--mode internal` is equivalent.
The runner keeps the four-case U238/Th232/Bi212 preflight, even for tiny samples.
Use only an environment where that gate passes; PART122 on macOS remains open.

The configured `cygno-acrylic-v3` model selects the v3 matrix automatically.
An explicit mismatched `--matrix` is rejected. For a direct diagnostic invocation,
use `rdecay01 macro.mac 1 --mode internal --model cygno-acrylic-v3`; omitting
`--model` retains v2 for compatibility. External always retains v2 and rejects
`--model cygno-acrylic-v3`.

Old v2 campaigns can still be analyzed with the same analysis executable/Python
entry point and a new output directory. **Do not edit their manifests or reuse
their ROOT files as physical v3.** Every report retains the simulation matrix and
separately records `normalization-scenario.json`; ROOT embeds these in
`provenance/`, Python also saves the scenario in `analysis-manifest.json`.
The core source IDs still contain `Polyimide` for compatibility; the actual v3
quantity export and transport material is PMMA. PMMA50 is a historical-material
study choice, not a claim about installed CYGNO foils. The comparison with the
upstream C++ constants, the previous 29 µm core, the explicit cathode extension,
and the numerical activity estimate are documented in
[STUDY_SOURCES](docs/STUDY_SOURCES.md).

## Preferred C++ ROOT analysis

Compile from the root, with ROOT and its RooFit/HS3 JSON libraries available:

```bash
c++ -O3 -std=c++17 -ffp-contract=off \
  internal/analysis/common_c++/AnalyzeCompactCampaign.cpp -I"$CYGNO_SRC" \
  $(root-config --cflags --libs) -lRooFitHS3 -lRooFitJSONInterface \
  -o "$CYGNO_BUILD/AnalyzeCompactCampaign"
"$CYGNO_BUILD/AnalyzeCompactCampaign" "$CYGNO_RUNS/internal-v3-complete" "$CYGNO_RUNS/internal-v3-analysis-NEW"
```

On ROOT 6.40 installations supplying JSON through HS3 only, omit
`-lRooFitJSONInterface`. Input must be a **complete unpacked compact campaign: 26 contributions for v3,
28 for v2**, not the two-primary diagnostic above unless all jobs passed.
See [native ROOT guide](analysis/common_c++/README.md) for topology cuts and outputs.

Python supports raw, compact and both, including portable archives:

```bash
python3 -m pip install -r internal/study/requirements-analysis.txt
python3 internal/study/analyze.py --input "$CYGNO_RUNS/internal-v3-complete" \
  --output "$CYGNO_RUNS/internal-v3-python-analysis-NEW"
```

For cluster variables, PBS examples and repeat/resume behavior, see
[WORKFLOW](docs/WORKFLOW.md). Detector construction/dimensions remain in the
[shared geometry documentation](../docs/SINGLE_MODULE_GEOMETRY.md).
