# Refactor validation

These checks compare behavior with a saved baseline; they do not validate the
underlying detector model, overlap freedom, source distribution or analysis cuts.
Use the same Geant4 installation, compiler, seed, worker count and macro for both
runs. CERN ROOT/PyROOT is required only for the hit-file comparison.

## Geometry snapshot

From the repository root, after sourcing `geant4.sh`:

```sh
cmake -S validation -B build/geometry-validation -DCMAKE_BUILD_TYPE=Release
cmake --build build/geometry-validation --parallel
mkdir -p build/cleanup-validation/before build/cleanup-validation/after
build/geometry-validation/geometry_snapshot build/cleanup-validation/before/geometry.txt
# Make the refactor, then rebuild both tools:
cmake --build build --parallel
cmake --build build/geometry-validation --parallel
build/geometry-validation/geometry_snapshot build/cleanup-validation/after/geometry.txt
cmp build/cleanup-validation/before/geometry.txt build/cleanup-validation/after/geometry.txt
```

Capture `before` before editing; do not overwrite it with an already-refactored
build. The separate snapshot executable constructs the same detector and dumps
physical placements in store order: name, copy number, translation, rotation,
logical volume, solid, material, sensitive flag and mother. It also records
Geant4 solid descriptions, material properties/composition, ordered source lists
and counts. The standalone target does not alter the simulation CMake setup.
It invokes sensitivity initialization without starting a run or transport.
Solid descriptions use Geant4's own printed precision; this is not a replacement
for reviewing changed dimension expressions or running overlap checks.

## Fixed-event output comparison

Save the original executable before editing, and use isolated working directories
so the two runs cannot overwrite each other's output:

```sh
mkdir -p build/cleanup-validation/before/outfiles_V2
mkdir -p build/cleanup-validation/after/outfiles_V2
cp build/rdecay01 build/cleanup-validation/before/rdecay01  # BEFORE edits
(cd build/cleanup-validation/before && ./rdecay01 ../../../validation/smoke.mac > run.log 2>&1)
# After edits and a successful simulation rebuild:
(cd build/cleanup-validation/after && ../../rdecay01 ../../../validation/smoke.mac > run.log 2>&1)
python3 validation/compare_hits.py \
  build/cleanup-validation/before/outfiles_V2 \
  build/cleanup-validation/after/outfiles_V2
```

`smoke.mac` runs 20 Po-212 events using Cathodes and two fixed seeds. It changes no
production macro. The default single worker is deliberate: multiple workers can
change output ordering and have separately documented label-sharing risks.
The comparator checks ROOT filenames, branch names/types, row counts and every
stored scalar/string value in order; ROOT timestamps/compression metadata are
irrelevant. Empty output is rejected. This small test is not statistical proof
of physics equivalence for every source configuration.

## First-pass results (2026-09-17)

- Geant4 11.4.2 Release build passed before and after the cleanup.
- Geometry snapshots compare exactly, including placement order, source lists,
  copy numbers, materials and solid descriptions: 3,227 placements, 75 cathodes
  and 150 sensitive gas placements.
- Fixed-seed run completed all 20 events before and after. Worker file
  `cleanup_smoke_t0.root` has 12 branches and 7,637 rows; every value matches.
- Existing missing-return warning in `SensitiveDetector::ProcessHits` remains;
  it is documented for a separate fix rather than hidden by this refactor.
- Interactive `./rdecay01` launched successfully outside the shell sandbox,
  initialized Qt/visualization and completed `vis.mac` through viewer refresh.
  The initial sandboxed launch failed to connect to macOS GUI services.
  Automated window inspection could not complete: the UI tool could not access
  the standalone executable, and a temporary app wrapper timed out. **Visual
  geometry inspection is therefore still pending.** Launch from `build/` and
  inspect/rotate the module array in Qt before accepting the visual check.
- No exhaustive overlap scan, multi-worker regression or ROOT analysis rerun
  was performed. Known geometry and analysis inconsistencies remain unchanged.

Local baseline/after snapshots, run logs and output are in
`build/cleanup-validation/`; they are validation artifacts, not source files.
