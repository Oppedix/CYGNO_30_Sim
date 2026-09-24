# Finalization and reproducibility handoff

> Current workflow: [two-stage simulation/offline analysis](BACKGROUND_STUDY.md).
> The earlier macOS PART122 results below remain historical evidence. The operator
> now reports a Linux x86_64 private Geant4 11.3.1 serial environment passing all
> four preflight cases; this is not a universal Geant4 fix.


Branch: `study/background-reproduction`. No merge or push performed.
Phase 6: `a9be61bcc209e403f00275bcfae51787fcadb765`.
Implementation: `113d7132c17b384870c891c5c7e8769160a6b32a`
(`feat(study): finalize code-compatible production workflow and decay gates`).
Additive manifest completion: `c7058d0`
(`fix(study): embed quantities and job accounting in campaign manifests`),
validated by the runner suite in 19.75 s. It embeds quantities, seeds and verified
counts directly in the campaign manifest; transport and normalization are unchanged.
Original documentation/export-macro handoff:
`f74ca7c3dea1059279d03b5f0d217206c706d992`
(`docs(study): record final validation and reproducibility handoff`).

The branch is technically ready for a fast-forward merge into local `main`:
main is an ancestor, tests pass, and the public tree contains no active deferred
model. The repository reproduces Samuele's workflow and analysis infrastructure
using thesis Table 7.1. **This does not certify a complete scientific reproduction.**
The tested Geant4 11.4.2/data environment cannot produce the complete published
U/Th background because of `PART122`; 21 smoke contributions remain incomplete.
The software correctly refuses to call those spectra complete.

## Supported combinations

| Layout | Detector model | Source policy | Role |
|---|---|---|---|
| legacy-25x3 | code-compatible | historical | Principal Samuele reference |
| cygno-5x5x3-v1 | code-compatible | historical | Retained alternative |

Both have 75 modules / 150 cells, unchanged internal geometry. A future 11x7
(77-module) layout is not implemented; counts now flow from the profile to
placement and analysis without duplicated construction. Independent geometry.txt and placements.tsv
snapshots are byte-identical to Phase 6 for both layouts.

## Validation evidence

[Portable evidence](study-results/finalization.json) and
[full public tree](REPOSITORY_TREE.txt) accompany this handoff.
All generated artifacts remain outside the repository, under `../../build/` or
`../../validation-runs/`. Real campaigns use implementation commit `113d713`;
the final documentation commit does not relabel them. Strict resume requires the
original checkout/build identity. Use a new output directory for a new revision.

| Check | Outcome |
|---|---|
| Fresh Phase 6 Release build | 12/12 original tests passed, 100.83 s |
| Updated complete suite | 13/13 passed, 111.58 s |
| Final clean Release build with UI/vis enabled | 13/13 passed, 105.18 s |
| Fast isotope | Po-212 transport covered by full CTest in both layouts |
| Long-lived U-238 | Two primaries produce two Th-234 daughters with 1e60 year; default control none |
| Th-232 and Bi-212 full-chain preflight | PART122; logs retained, no data/branch changes |
| Detector-independent vacuum Bi probe | PART122; no CYGNO geometry or ROOT linked |
| Full 26-job smoke | All 26 attempted; five K-40 jobs complete, 21 incomplete |
| Unchanged resume | Five REUSE, 21 retained failures, no new attempts |
| Explicit retry | Five valid jobs untouched; 21 new failed attempts, original attempts retained |
| Analysis-only | No Geant4; identical normalization, spectra JSON and CSV tables across reports |
| Real Ctrl-C | Exit 130; 100-primary GEMsCore_K40 complete preserved; Lens_K40 resumes in attempt-0002 |
| Tiny production-mode check | Two-primary Lens_K40 succeeds; full GEMsCore_Th232 blocked by preflight |
| Manual GEMsCore_K40 macro | Two verified primaries, 352 raw rows, two processed groups |
| Manual Lens_K40 macro | Two verified primaries, zero gas hits/groups; valid zero-hit example |
| Detector visualization | Nonempty ToolsSG offscreen PNG inspected; all 25×3 modules visible |
| Figures/tables | Real partial PNGs and synthetic full-category PNGs inspected; ROOT/PDF/CSV/JSON/text generated |

The five complete smoke jobs generate 10 primaries in total. Failed runs have an
unknown denominator unless their accounting was verified; no partial raw file is
normalized. Nineteen jobs abort, while two tiny Th runs finish but fail the campaign
preflight gate. The figure header reads **SMOKE | 5/26 | INCOMPLETE; partial sums only**.
Tiny Monte Carlo rates and zero counting errors are not physical estimates or limits.
Published comparisons are never fitted normalizations.

The final smoke is `../../validation-runs/samuele-final-smoke` and its current
report is identified by `latest-report.json`. Manual and interruption checks are
in `samuele-manual-gem-k40`, `samuele-manual-k40`, `samuele-interrupt-check`;
the tiny production-mode check is `samuele-production-check`. Final CTest evidence
is summarized in the portable evidence above. The latest CTest invocation writes
`../../build/cygno-samuele-release/Testing/Temporary/LastTest.log`.

## Exact local build and commands

From this repository root, with the Geant4 and ROOT environments loaded as in the
[README](../README.md). These are the same build/run options; only the external
build/run directories and local Geant4 discovery path differ:

```sh
export REPO="$PWD"
export BUILD="$REPO/../../build/cygno-samuele-release"
# Choose a NEW campaign root for this checkout revision:
export RUNS="$REPO/../../validation-runs/samuele-next"
cmake -S . -B "$BUILD" -DCMAKE_BUILD_TYPE=Release -DWITH_GEANT4_UIVIS=ON \
  -DCYGNO_BUILD_ANALYSIS=ON -DPython3_EXECUTABLE="$(command -v python3)" \
  -DGeant4_DIR="$REPO/../../software/geant4-11.4.2/lib/cmake/Geant4"
cmake --build "$BUILD" --parallel 6
ctest --test-dir "$BUILD" --output-on-failure

# Generate explicit manual macros; no Geant4:
python3 legacy/study/combined/runner.py --mode smoke --macros-dir "$RUNS/macros"
mkdir -p "$RUNS/manual"
(cd "$RUNS/manual" && "$BUILD/rdecay01" "$RUNS/macros/GEMsCore_K40.mac" 1 --layout legacy-25x3 > simulation.log 2>&1)
"$BUILD/analysis/SimpleProcessEvents" "$RUNS/manual/outfiles_V2/raw_t0.root" "$RUNS/manual/processed.root"

# Matrix; full smoke; independent full-chain preflight:
python3 legacy/study/combined/runner.py --list
python3 legacy/study/combined/runner.py --mode smoke --build "$BUILD" --output "$RUNS/smoke"
python3 study/preflight.py --build "$BUILD" --output "$RUNS/preflight"

# Production (default 10^7); repeat unchanged to resume:
python3 legacy/study/combined/runner.py --build "$BUILD" --output "$RUNS/production"
python3 legacy/study/combined/runner.py --build "$BUILD" --output "$RUNS/production"
python3 legacy/study/combined/runner.py --build "$BUILD" --output "$RUNS/production" --retry-failed

# ROOT/PNG/PDF/CSV/JSON/text regeneration, no Geant4:
python3 legacy/study/combined/runner.py --build "$BUILD" --output "$RUNS/production" --analysis-only
python3 legacy/study/combined/runner.py --mode smoke --build "$BUILD" --output "$RUNS/smoke" --analysis-only
```

No 26×10^7 production campaign was launched. `--primaries N` must be repeated on
resume if supplied initially. In this environment the full smoke returns 2 for
incomplete coverage; that is the expected honest outcome, not a successful chain.

## Visualization

Interactive command, from a normal desktop terminal with GUI access:

```sh
(cd "$BUILD" && ./rdecay01 --layout legacy-25x3)
```

The sandboxed Qt launch failed on macOS GUI service access; the native launch
initialized the viewer, but UI automation could not inspect its window. The
following Geant4 ToolsSG offscreen path was rendered and visually verified:

```sh
mkdir -p "$RUNS/view"
cp config/vis-legacy-offscreen.mac "$RUNS/view/vis.mac"
(cd "$RUNS/view" && printf 'exit\n' | G4UI_USE_TCSH=1 "$BUILD/rdecay01" --layout legacy-25x3)
```

It writes `legacy-25x3.png`. World and vessel visibility are disabled **only for
this view**, exposing the module array; geometry/transport are unchanged. ToolsSG
support is required (present in the tested 11.4.2 installation). An initial
RayTracer attempt gave a blank image and is not counted as validated visualization.

## Remaining scientific limitations

Explicit long-lived threshold configuration is resolved and tested. Complete
U/Th-chain transport remains blocked by `PART122` duplicate-ion registration in
the tested Geant4/data environment. No verified replacement environment is claimed; a complete
reproduction requires a separately validated matched Geant4/data installation.
Historical sampling is not uniform bulk; inherited internal overlaps, stopped ion
recoil, group heuristics and first-position fiducialization remain. Exact thesis
production inputs/revision are unresolved, and code-compatible dimensions differ
from the thesis description. See [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

## Preserved Phase 7 WIP

Local recovery branch `recovery/phase7-wip-20260922`, commit
`f82c823144237accdc99b4c351a7ce96b90329d8`; 21 files, 481 insertions and 51 deletions.
Only the following work was preserved; no references, build/run outputs or ROOT:

- `analysis/reference_cpp/DetectorGeometry.hh`
- `analysis/reference_cpp/FileIdentity.hh`
- `analysis/reference_cpp/PlotNormalizedSpectra.cpp`
- `analysis/reference_cpp/PlotNormalizedSpectra_GEMchain.cpp`
- `analysis/reference_cpp/PlotNormalizedSpectra_single.cpp`
- `analysis/reference_cpp/PlotSpectrum.C`
- `analysis/reference_cpp/SimpleProcessEvents.cpp`
- `app/rdecay01.cc`
- `common/DetectorGeometry.hh`
- `config/study/smoke-C.json`
- `config/study/smoke-D.json`
- `docs/STUDY_THESIS_MODEL.md`
- `include/cygno/geometry/DetectorConstruction.hh`
- `src/actions/RunAction.cc`
- `src/geometry/DetectorConstruction.cc`
- `legacy/study/combined/runner.py`
- `study/source_matrix.py`
- `validation/geometry_audit.cc`
- `validation/geometry_quantities.cc`
- `validation/geometry_snapshot.cc`
- `validation/test_thesis_model.py`

The recovery commit is not an ancestor of the final public branch. Do not include
that separate recovery branch when publishing. The retired model appears only in
historical provenance, not active supported code or configurations.

## Repository audit

No tracked generated ROOT, compiled binaries, build/validation-run directories,
private reference directories, editor backups or platform-specific absolute paths.
Geant4 license headers and scientifically useful historical code/reports remain.
An old ignored 44 MB in-repository build was preserved outside Git at
`../../build/archived-inrepo-build-20260922`. Generated Python caches and Finder
metadata were removed. Private local references remain excluded and were not
edited, moved or deleted.
Final expected status after this handoff commit: clean `study/background-reproduction`.
No merge or push is performed.


## Final documentation audit (2026-09-22)

The active documentation consistently describes finalized workflow/analysis
infrastructure, the tested environment's PART122 U/Th blocker, and the unsupported,
deferred model. The 11x7 layout remains future work. README and handoff commands
agree; external directory choices and local dependency discovery are documented.
All 56 local links across 15 active Markdown files resolve. The three study
configurations validate, the matrix contains 26 contributions, and `--list`
succeeds without transport. Relevant CTest groups `study_runner` and `source_matrix`
pass (2/2, 31.46 s); `git diff --check` passes. No implementation, configuration or
test files changed. Branch ancestry confirms that local `main` is an ancestor and
`recovery/phase7-wip-20260922` is not. No merge or push was performed.
