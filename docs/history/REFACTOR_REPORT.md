> Historical record. The current supported workflow is [BACKGROUND_STUDY.md](../BACKGROUND_STUDY.md).

# Interrupted-refactor recovery — 2026-09-21

## Starting state and preservation

The workspace root was `hep/`; the Git repository was
`projects/CYGNO_30_Sim`, on main at `05a2b92` with a valuable mixed staged/unstaged
refactor. The previous session had staged generated-build deletions and left
source moves/new files untracked. Nothing was reset, checked out, cleaned or
replaced with baseline source. No commits or pushes were made in this recovery.

Before edits, complete baseline/staged/unstaged patches, status, a diff inventory
and a source archive were saved outside the repository at
`../../validation-runs/CYGNO_30_Sim/recovery-20260921/`. Its
`interrupted-source.tar.gz` and patch files preserve the starting code/index
changes. Original references remain untouched at
`../../validation-runs/CYGNO_30_Sim/20260921-05a2b92/`, including six worker ROOT
files, content hashes, environment/dataset details, snapshots and logs.

The interruption was farther advanced than its last commentary implied:
bookkeeping, mass and ntuple-lifecycle fixes were already mixed with the moves.
An unfinished `ProcessEvents.cc`, `Analysis.hh` and build-header template existed
but were not connected. These were completed rather than discarded. Old
documentation still referred to moved paths and standalone validation CMake.

## Final structure and moves

```text
CMakeLists.txt  README.md  LICENSE  .gitignore
app/rdecay01.cc
common/                 shared geometry and build-header template
include/cygno/          geometry/, source/, actions/, output/ interfaces
src/                    matching implementation directories
config/                 vis.mac, cygno/, normalization/ historical tables
analysis/               ROOT processor, plotters, shared helpers
validation/             CTest harnesses, diagnostics, macros/
docs/                   architecture, sources, output, analysis, issues, layout
data/                   external Geant4 data/reference text
legacy/                 inactive code, old macros/generators/notes, source copies
```

[FILE_MOVES.json](../FILE_MOVES.json) lists individual moves. The inactive custom
physics/histogram classes retain their license headers under legacy/scaffolding.
Old example macros/reference text and ambiguous source scripts are retained in
clearly marked locations. The generator moved by the interruption to config was
found to still contain unsupported aliases, so it now lives in legacy/config.
Original analysis sources/constants are preserved under legacy/analysis/05a2b92.
Tracked build/CMake files, four compiled analysis programs and editor backups
remain removed from tracking. No generated products are needed for building.

## Behavior-preserving checkpoint

The fresh `../../build/cygno-recovered-structural` build passed before changing
source ordering. Smoke/full/partial/stopped-chain cases matched the saved baseline
exactly: respectively **7,637 / 25,318 / 24,361 / 24,395 rows**. All 12 branch
names/types/order and every value (IDs, particles, coordinates, energy, volume,
nucleus/process labels) matched. Geometry and placement files were byte-identical.
All six saved baseline schema+row hashes were verified, including two workers;
ROOT container byte hashes were not the previous session's hashing convention.

This validates structural changes plus already-present standard-single-run-neutral
bookkeeping: corrected mass totals/keys, actual-primary summary, once-only ntuple
booking, output-directory creation, message cleanup and unused scaffolding removal.
Geometry, materials, physics lists, stopping/decay policy and sampler distribution
remain unchanged. Hash equality is not promised across Geant4 versions or MT
scheduling changes.

## Intentional correctness changes

Source generation now samples before creating that event's vertex. Event 0 uses
its own sample. The sampler itself remains surface-point plus inward depth.
Updated isotope commands also apply to the next event in a later run. Historical
source-position fixed-seed equality is therefore no longer expected. Single-worker
reference rows after correction are **13,509 / 28,319 / 27,180 / 27,292**.

Analysis now flushes the final group, prevents ionization groups crossing events,
removes nonexistent translation bindings and handles long string labels safely.
Processed analysis values intentionally change. Equal-integral and empty spectra
survive both stacks and individual keys. Histogram definitions, fiducial/energy
cuts and normalization formula are preserved. Historical normalization tables
were externalized without inventing replacements, and exact transcription is
tested against the original compiled tables.

## Validation and limits

The source-only export (`final-source`, 173 source/reference files, no `.git` or
build products) configured and built successfully in `../../build/cygno-final-clean`.
**All 5 CTest groups passed**, followed by the separate expected Bi-212 failure.
Final geometry/placement snapshots are byte-identical to 05a2b92; both representative
scans produced 48 inherited internal-overlap warnings. Final two-worker output
contained 23,887 rows in two files with disjoint event IDs (worker assignment is
scheduling dependent). The second run in the lifecycle fixture uses only 10 events
to expose retained rows from its preceding 20-event run.

The complete suite covers source/RNG/mass checks, geometry, transport and chain
policies, two-worker ownership, repeated-run output, tiny ROOT grouping fixtures,
all three normalized stack implementations, historical constants and all four
ROOT geometry adapters. The final clean-source build and test logs are in the
recovery directory; see [validation instructions](../../validation/README.md).

Containment diagnostics found 43/1000 GEM-copper and 247/1000 ring-strip samples
outside their chosen solid; there was no rejection/resampling. Cathode/gas,
GEM/core and field-cage overlaps remain inherited. Matching baseline geometry
excludes newly introduced geometry from this refactor; software tests do not
resolve those scientific/engineering problems. Nucleus ancestry, contamination
model and normalization provenance remain unresolved. The resized vessel cannot
automatically use the historical 1102.24 kg mass. See [KNOWN_ISSUES.md](../KNOWN_ISSUES.md).

Bi-212 still reproduces Pb208 `PART122`, separately from passing tests, on Geant4
11.4.2 with the same installed datasets, Apple clang 21/macOS 27 arm64. No Geant4
radioactive-decay behavior was changed. Baseline data are retained.

## Migration and commands

Use top-level CMake; `cmake -S validation` is obsolete. Source headers are now
`cygno/<area>/<Class>.hh`. Validation macros are under `validation/macros/`;
current runnable examples are under `config/cygno/`. ROOT analysis executables
are under `<build>/analysis/`. The raw `Hits` schema and worker filename convention
are unchanged. Source ordering and processed grouping changed intentionally.
Normalized plotters now require an explicit study file with provenance; no old
tables are applied by default. Use matching source evidence for the processor's
explicit unversioned-geometry assumption.

From this repository after sourcing Geant4's environment:

```sh
cmake -S . -B ../../build/cygno-final -DCMAKE_BUILD_TYPE=Release \
  -DCYGNO_BUILD_ANALYSIS=ON -DPython3_EXECUTABLE="$(command -v python3)"
cmake --build ../../build/cygno-final --parallel
ctest --test-dir ../../build/cygno-final --output-on-failure
python3 validation/run_checks.py bi212 ../../build/cygno-final
```

Final Git status on `main`: 331 previously staged generated-file deletions,
127 unstaged old-path deletions, 15 modified tracked files and 152 untracked source,
documentation/reference files (including moves). Zero `build/` files remain in the
index. No executable/ROOT/object products were found among candidate source files;
`git diff --check`, project include checks and documentation-link checks passed.

The original main/index state is retained; intentional source/docs changes and
moves remain uncommitted for review. The final status and complete baseline-to-
final source diff are saved in the recovery directory, excluding runtime products
from the checkout-equivalent source archive. No push was performed.
