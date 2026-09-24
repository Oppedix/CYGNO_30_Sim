# cygno-11x7-v1 layout handoff

Validated 2026-09-24 on macOS/arm64, Geant4 11.4.2, starting from clean `main`
commit `d326b6341c44bb84ba5a4fd1d26eee810d99c069`. No push, merge or commit was made.

## Change scope and preserved behavior

Added one explicit profile and a separate study configuration. The existing
profile/envelope/vessel/World formulas, shared construction builders, source
sampler, materials, optics, field cage, drift, GEMs, physics, RDM threshold,
Table 7.1, chain boundaries, normalization, grouping, cut and raw/compact semantics
are unchanged. `samuele.json` and `thesis-table7.1.json` have zero diff.
The new configuration differs from `samuele.json` only in `layout`.
Default no-argument selection remains `cygno-5x5x3-v1`.

`app/geometry_quantities.cc` and canonical Python analysis were inspected and
already consume profile counts/exported centers correctly; no refactor was needed.
The optional C++ old-hash compatibility rule is now explicitly restricted to the
two original layouts. No old hash is accepted for the new profile.
New geometry hash: `ff9a647fff30def4a01db710deddd7584e491e1e0aba59dd9e98fdf2c46c5cba`.

Before editing, both existing profiles were exported from a freshly built baseline.
After editing, their complete `placements.tsv`, `geometry.txt` and quantity data
rows were **byte-identical**; all gas centers/sizes were identical. Only expected
source/geometry fingerprints changed in exporter metadata. The explicit current
profile also still matches default same-seed smoke hits.

## Independent geometry contracts

All dimensions below are mm; full sizes are X × Y × Z.

| Profile | Modules / gas / placements | Occupied full spans | Vessel outer full size | World full size |
| --- | --- | --- | --- | --- |
| legacy-25x3 | 75 / 150 / 3227 | 12596.220 × 2408.7875 × 2281.300 | 12616 × 2428 × 1028.8 | 14000 × 3428 × 3281.3 |
| cygno-5x5x3-v1 | 75 / 150 / 3227 | 2516.220 × 4016.7875 × 6851.900 | 2536 × 4036 × 5599.4 | 14000 × 5036 × 7851.9 |
| cygno-11x7-v1 | 77 / 154 / 3313 | 5540.220 × 5624.7875 × 2281.300 | 5560 × 5644 × 1028.8 | 14000 × 6644 × 3281.3 |

The 11x7 occupied minimum is `(-2770.145,-2812.1275,-1140.650)` and maximum
`(2770.075,2812.6600,1140.650)`. Vessel half-size is `(2780,2822,514.4)`;
World half-size is `(7000,3322,1640.65)`. XY occupied aspect ratio Y/X ≈1.0153.

```text
ix = 0..10; iy = 0..6; iz = 0
moduleId = ix*7 + iy                       # Y fastest, exactly 0..76
center = ((ix-5)*504, (iy-3)*804, 0) mm
module 38 = (0,0,0)
gasCopy = side*77 + moduleId
side 0 = 0..76; side 1 = 77..153
GasCenter = center + (0,0,side == 0 ? 250.25 : -250.25) mm
```

All module centers and gas copies are unique. All 77 module envelopes are
disjoint. All 43 local placements per module match the existing solid/material
signatures; no component crosses the common vessel wall, every non-optical
component is inside its cavity, and every component is inside World. Inherited
internal overlap warnings remain diagnostic and were not repaired.

The 25x3 and 11x7 profiles share planar topology, orientation, 504/804 mm pitches,
local/camera geometry and source sampling. They are not scientifically identical:
77 versus 75 modules, stride 77 versus 75, vessel mass/dimensions and source
population change. Different normalized total background is expected.

## Actual constructed quantities

These are exporter observations from Geant4 `GetMass()` and source placement
lists, not normalization constants or analytic replacement masses. Boolean-solid
mass estimates remain subject to the existing Geant4 estimator.

| Component | Placements | Constructed mass (kg) |
| --- | ---: | ---: |
| Cathodes | 77 | 275.968 |
| GEMsCore | 462 | 6.377448 |
| GEMsOuter | 462 | 74.5091678404 |
| Lens | 308 | 0.512833584772 |
| Resistors | 770 | 0.0086082304 |
| RingStrips | 616 | 28.1806349262 |
| RingSupports | 154 | 17.8260248094 |
| Sensors | 308 | 0.1430112992 |
| Vessel | 1 | 3833.44698722 |

`geometry.json` contains exactly 154 centers, each compared against an actual
sensitive placement by the extended layout CTest. The headless exporter produced
byte-identical JSON and quantity TSV to the visualization-enabled build.

## Executed validation

- Visualization-enabled/reference build: passed.
- Fresh ROOT-free headless build (`WITH_GEANT4_UIVIS=OFF`, `CYGNO_BUILD_ANALYSIS=OFF`,
  `BUILD_TESTING=OFF`): passed on macOS; Linux build remains an operator gate.
- CTest: **15/15 passed**, including all three profile/source/mass tests, actual
  geometry, CLI, transport, source matrix, optional C++ analysis and ROOT maps.
- Layout CTest rerun after adding exporter-versus-placement comparison: passed.
- Full Python suite with reference and transport integration enabled: **47/47 passed**.
- Tutorial outputs refreshed through `validation/execute_notebooks.py --output analysis`.
- Explicit notebook suite after refresh: **2/2 passed**, including the three saved
  tutorials and the constructed 11x7 real-campaign branch.
- Synthetic fixtures retain legacy/150 semantics. Both raw and compact reject
  copy 150 for either 75-module layout; all copies 0..153 pass for 11x7 and 154 fails.
- Real same-seed K40 diagnostic transport: 30 primaries per output mode for each
  layout; raw/compact/both exact parity passed. The 11x7 both result had 2203 raw
  hit rows, 14 groups, 19 group-volume records and 265 track records.
- Fresh headless 11x7 Po212 diagnostic: 20 primaries, both-mode parity passed
  (7 groups, 2381 track records). No large campaign was run.
- The notebook integration uses **constructed geometry and quantities plus
  synthetic events/preflight**. It tests volume 153 at the exported center and
  the unchanged 20 mm boundary, verifies 26 contribution scales, normalized
  parity, spectra, tables and figures against Stage B. It is not radioactive
  transport evidence or a substituted physics gate.
- Geant4 offscreen face-on and oblique cathode-outline views generated and
  inspected: 11 X columns, 7 Y rows, one plane, nearly square XY footprint,
  consistent short-X/long-Y orientation and no missing/duplicate footprints.
- `git diff --check`: passed.

The fresh **real four-case preflight failed 2/4** on this macOS environment:
`u238-default` and `u238-enabled` passed; `th232-full` and `bi212-full` failed
with the inherited `PART122`. No physics or gate was changed. A complete
26-contribution campaign was not launched through this failed gate.

Local evidence is under `../../validation-runs/11x7-baseline`,
`11x7-validation`, `11x7-headless`, `11x7-view` and `11x7-decay-preflight`.
CTest evidence is under `../../build/cygno-samuele-release/Testing/Temporary`
and `validation-results`. Top-level test logs are `/tmp/cygno-11x7-ctest.log`,
`/tmp/cygno-11x7-python.log`, `/tmp/cygno-11x7-notebook-tests.log`,
`/tmp/cygno-11x7-headless.log` and `/tmp/cygno-11x7-layout-export.log`.

## Assumption search classification

The active tracked tree was searched for 75, 150, module 37 and both existing
profile names, including notebook source cells. No mechanical numeric replacement
was used.

- Generic supported-layout lists: shared enum/parser, CLI help and Python count
  registry extended. Raw/compact readers, campaign map validation and fiducial
  reconstruction already consume these contracts and exported centers.
- Validation expectations: layout bounds/counts/strides, gas maps, placement
  audits, source lists/quantities, optional reference analysis, parity and
  notebook campaign coverage extended to 77/154. The diagnostic transport helper
  gained an explicit layout argument while retaining its legacy default.
- Historical fixtures/references: default teaching examples, legacy source-matrix
  and scheduler fixtures, historical TSV normalization constants, published
  reference numbers, baseline center fixtures, prior study-result records,
  old-hash markers and preflight's legacy layout retained. Dated status reports
  gained a pointer to the new layout without rewriting historical findings.
- Local physical dimensions (including `0.075` mm), 1500 mm World minima,
  isotope labels, seeds, and hash substrings are unrelated numeric occurrences
  and remain unchanged.
- Documentation that enumerates current supported profiles/counts was extended;
  sections explicitly describing the original 75-module profiles remain valid.

## Commands and remaining human gates

Exact local interactive viewer:

```sh
cd "/Users/giuseppemariaoppedisano/Desktop/GSSI/PHD/CYGNO/SolarNu/SimSamuele/hep/build/cygno-samuele-release"
./rdecay01 --layout cygno-11x7-v1
```

The normal viewer macro remains unchanged. For an unobstructed face-on footprint
image, copy `config/vis-11x7-offscreen.mac` to a fresh external directory as
`vis.mac`, run the same executable there without a batch macro, and exit the UI.
The dedicated macro only changes visualization attributes (cathode outlines).

Exact Linux headless build in the documented private environment:

```sh
bash --noprofile --norc
export G4LAB="/private/SolarNu/MC30/geant4-private"
source "$G4LAB/activate.sh"
export CYGNO_SRC="$G4LAB/projects/CYGNO_30_Sim"
export CYGNO_BUILD="$G4LAB/build/cygno-11x7-linux"
export CYGNO_RUNS="$G4LAB/runs/g4-11.3.1-linux"
cd "$CYGNO_SRC"
cmake -S . -B "$CYGNO_BUILD" \
  -DCMAKE_BUILD_TYPE=Release -DWITH_GEANT4_UIVIS=OFF \
  -DCYGNO_BUILD_ANALYSIS=OFF -DBUILD_TESTING=OFF \
  -DGeant4_DIR="$G4LAB/software/geant4-11.3.1-serial/lib/cmake/Geant4"
cmake --build "$CYGNO_BUILD" --target rdecay01 geometry_quantities --parallel

python3 study/preflight.py --build "$CYGNO_BUILD" \
  --output "$CYGNO_RUNS/11x7-preflight"
python3 study/simulate.py \
  --config config/study/cygno-11x7-v1.json \
  --build "$CYGNO_BUILD" \
  --output "$CYGNO_RUNS/11x7-smoke" \
  --mode smoke --primaries 2 --jobs 8 --output-mode both --archive
```

The campaign also enforces its own four-case preflight. Use fresh directories;
never bypass a failure. On the analysis workstation, activate the analysis Python
environment and run:

```sh
python study/analyze.py --input /path/to/11x7-smoke.tar.gz \
  --output /path/to/11x7-smoke-analysis
```

Remaining gates: human confirmation of the normal viewer; fresh Linux build and
4/4 decay preflight; tiny 26/26 both-mode smoke, archive transfer/integrity and
offline normalized parity. No 1e6/1e7 campaign was launched.

## Exact changed files / git status

28 tracked files modified; three new files (including this report). Main remains
at the starting commit; no files staged. Diff scope is the additive profile,
configuration/view macro, validation, documentation and regenerated tutorial outputs.

```text
 M README.md
 M analysis/common/CYGNO30_background_analysis_walkthrough.ipynb
 M analysis/compact/CYGNO30_compact_preprocessing_walkthrough.ipynb
 M analysis/raw/CYGNO30_raw_preprocessing_walkthrough.ipynb
 M analysis/reference_cpp/FileIdentity.hh
 M app/rdecay01.cc
 M common/DetectorGeometry.hh
 M docs/ANALYSIS.md
 M docs/FINALIZATION.md
 M docs/LAYOUT.md
 M docs/STUDY_PROGRESS.md
 M src/geometry/DetectorConstruction.cc
 M study/source_matrix.py
 M tests/test_compact.py
 M tests/test_notebooks.py
 M tests/test_offline.py
 M tests/test_parity.py
 M validation/CMakeLists.txt
 M validation/analysis_geometry.cc
 M validation/check_analysis.py
 M validation/check_geometry.py
 M validation/check_hits.py
 M validation/compact_transport.py
 M validation/layout_profiles.cc
 M validation/run_checks.py
 M validation/source_checks.cc
 M validation/test_layout_analysis.py
 M validation/test_source_matrix.py
?? config/study/cygno-11x7-v1.json
?? config/vis-11x7-offscreen.mac
?? docs/CYGNO_11X7_VALIDATION.md
```
