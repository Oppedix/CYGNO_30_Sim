# Validation of the 5 × 5 × 3 refactor

## Results (2026-09-20)

Tested with Geant4 11.4.2, Apple Clang 21, Qt and ROOT 6.40.04 on arm64 macOS.
The pre-edit source/executable and local results are in `build/layout-validation/`.
Those generated artifacts are not required to build the simulation.

- Release simulation build succeeds. No active physics-list, process, material,
  source-distribution, decay-policy or output-column change was introduced.
- Exactly **75 module centers, 150 sensitive gas placements and 3,227 physical
  volumes**, all physical names unique. Deterministic copy/center mapping passes.
- Every module's **43 local placements**, Geant4 solid descriptions, material
  assignments and sensitivity match the original 25 × 3 module. Material density,
  composition, temperature and pressure snapshots match. Solid descriptions use
  Geant4's printed precision; the source expressions were also reviewed.
- Complete module bounding boxes are disjoint, all placements fit in World, and
  no module component intersects the resized common vessel shell.
- All nine source lists resolve every name uniquely; 100 calls to each existing
  sampler produce finite positions. This tests addressability, not uniformity or
  guaranteed containment of the inherited surface/depth sampler.
- Geant4 `CheckOverlaps(2000, 0, true, 5)` was run on the central module and vessel
  before/after. Both produced the same **48 internal-overlap warnings**: 16
  strip/support, 16 gas/strip, 12 GEM/core and 4 cathode/gas reports. The new reports
  involve components of the same module. Vessel checks passed. Warning counts are
  sampled reports, not a count of distinct geometric intersections. The analytic
  full-array bounding-box check excludes inter-module collisions. The inherited
  module itself is **not overlap-free**; see `docs/KNOWN_ISSUES.md`.
- Interactive `./rdecay01` starts Qt and completes `vis.mac`. For native automation,
  an identical executable was copied into a temporary local app bundle and run
  from `build/`; its rendered oblique view was inspected and shows three separated
  layers of modules. The standalone command remains the normal launch path.
- All four ROOT plotting sources compile against the new adapter. Their 150
  reconstructed gas centers match actual Geant4 placements within 1e-9 mm; their
  existing 20 mm fiducial boundary predicates pass. `SimpleProcessEvents.cpp`
  also compiles. This is not a full production spectrum/normalization validation.

| Run | Requested events | Workers | Hit rows | Outcome |
| --- | ---: | ---: | ---: | --- |
| Po-212 smoke | 20 | 1 | 7,637 | Passed; 6 events produce gas hits |
| Bi-211 full chain | 40 | 1 | 25,318 | Passed; daughters tracked to Pb-207 |
| Bi-211 partial chain | 40 | 1 | 24,361 | Passed; secondary ions killed |
| Bi-211 stopped at ground-state Tl-207 | 40 | 1 | 24,395 | Passed; no Pb-207 in particle summary |
| Bi-211 full chain | 40 | 2 | 21,854 total | Passed; two worker files, disjoint event IDs |

For every passing run, `check_hits.py` checks the exact 12 `Hits` branch names and
types, finite/nonnegative energy deposits, particle tags, valid event/volume IDs,
and that pre-step positions lie inside their named gas boxes. Positive deposits
and radioactive-decay creator rows are present. The two-worker test exercises
worker-local labels but is not a general concurrency stress test. Different event
scheduling and the preserved per-worker first-event source ordering mean row
counts need not match one-worker results.

**Known failure:** a 40-event Bi-212 full-chain macro fails with `PART122` during
Pb-208 ion registration on this installation. It also fails with the saved
pre-refactor executable. `known_bi212_failure.mac` retains a reproducer; this test
is not claimed to pass, and no physics setting was changed to hide the failure.

## Repeat the build and geometry checks

From the repository root, after sourcing the installed `geant4.sh`:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
cmake -S validation -B build/layout-validation/tools-after -DCMAKE_BUILD_TYPE=Release
cmake --build build/layout-validation/tools-after --parallel
mkdir -p build/layout-validation/after/outfiles_V2
build/layout-validation/tools-after/geometry_snapshot build/layout-validation/after/geometry.txt > build/layout-validation/after/geometry.log 2>&1
build/layout-validation/tools-after/geometry_audit build/layout-validation/after/placements.tsv overlaps > build/layout-validation/after/audit.log 2>&1
python3 validation/check_geometry.py build/layout-validation/before/placements.tsv build/layout-validation/after/placements.tsv
```

`check_geometry.py` compares the original 25 × 3 baseline with the requested
5 × 5 × 3 result and expects adjacent `geometry.txt` material snapshots. It must
not compare two already-refactored geometries as if one were the old baseline.
For future changes, save a source copy/executable and snapshots **before editing**.
To build the validation tools against that saved source use:

```sh
cmake -S validation -B build/layout-validation/tools-before \
  -DCYGNO_SOURCE_DIR="$PWD/build/layout-validation/before/source" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build/layout-validation/tools-before --parallel
```

The harness is separate from the production build; it does not install alternate
physics in `rdecay01`. `geometry_snapshot` records materials, solids, placements
and source lists; `geometry_audit` writes bounds/signatures and tests source lookup.
The optional `overlaps` argument adds the representative Geant4 scan. Review its
warnings rather than interpreting process exit 0 as an overlap-free geometry.

## Repeat transport and ROOT checks

From the repository root (each macro runs in a fresh process):

```sh
(cd build/layout-validation/after && ../../rdecay01 ../../../validation/smoke.mac > smoke.log 2>&1)
(cd build/layout-validation/after && ../../rdecay01 ../../../validation/chain.mac > chain.log 2>&1)
(cd build/layout-validation/after && ../../rdecay01 ../../../validation/partial_chain.mac > partial_chain.log 2>&1)
(cd build/layout-validation/after && ../../rdecay01 ../../../validation/stop_chain.mac > stop_chain.log 2>&1)
mkdir -p build/layout-validation/threads/outfiles_V2
(cd build/layout-validation/threads && ../../rdecay01 ../../../validation/chain.mac 2 > chain.log 2>&1)
python3 validation/check_hits.py build/layout-validation/after/placements.tsv 20 build/layout-validation/after/outfiles_V2/cleanup_smoke_t0.root
python3 validation/check_hits.py build/layout-validation/after/placements.tsv 40 build/layout-validation/after/outfiles_V2/chain_t0.root
python3 validation/check_hits.py build/layout-validation/after/placements.tsv 40 build/layout-validation/after/outfiles_V2/partial_chain_t0.root
python3 validation/check_hits.py build/layout-validation/after/placements.tsv 40 build/layout-validation/after/outfiles_V2/stop_chain_t0.root
python3 validation/check_hits.py build/layout-validation/after/placements.tsv 40 build/layout-validation/threads/outfiles_V2/chain_t*.root
python3 validation/check_analysis.py build/layout-validation/after/placements.tsv build/layout-validation/root-checks
```

Use Python with PyROOT available; `check_analysis.py` uses `root-config` and the
system C++ compiler. Pass worker files from **one run** to each `check_hits.py`
invocation. Inspect logs for completed event counts and expected daughter-ion
summaries; an event with no gas step correctly has no ntuple row. Old files with
the same names are overwritten, so use a new working directory when retaining
results. Existing prebuilt analysis binaries are not automatically rebuilt by
the Geant4 CMake project; compile a plotting program, for example, with:

```sh
c++ -std=c++17 analysis/PlotNormalizedSpectra.cpp $(root-config --cflags --libs) -o build/PlotNormalizedSpectra
```

Run Qt from `build/` with `./rdecay01`. The default `vis.mac` has an oblique camera
for the three Z layers. Rotate/zoom and inspect the grid and optical components.

`compare_hits.py` remains available for exact fixed-seed comparisons of future
refactors that do **not** change geometry or ordering. Exact world-coordinate row
identity is not an acceptance criterion for the intentional layout change.
The historical first cleanup (2026-09-17) matched its unchanged geometry and all
7,637 Po-212 rows exactly; the checks above supersede that pass's pending GUI,
threading and known-return-warning notes.
