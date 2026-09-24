# Raw/compact simulation refactor: implementation report

Completed from current main 60823ec in the existing working tree. Changes are
uncommitted for review. The implementation plan and audit preceded edits.

## Result and scientific invariants

The simulation supports raw (default), compact, and both. One StepRecord is
extracted per sensitive Geant4 step; raw writing and compact accumulation consume
it. No output code calls RNG or changes physics/transport. Compact stores groups
and per-volume sums instead of step repetition. Historical grouping—including
initial/inherited ionizationSeen, label changes, zero-energy first steps, volume
insertion order and sequential floating-point additions—is preserved.

Physics list, RadioactiveDecay policy, source sampler, geometry, deterministic
seeds, primary counts, matrix, normalization multiplication order, first-position
20 mm cut, exact windows, ROOT-compatible 900-bin edges, seven categories and
published table transcription remain unchanged. Baseline raw and both parity,
C++ reference comparisons and tests provide the evidence described below.

## Schemas and canonical flow

Raw Hits retains EventNumber, ParticleName, ParticleID, ParticleTag, ParentID,
x_hits/y_hits/z_hits, EnergyDeposit, VolumeNumber, Nucleus and ProcessType; its
only added field is float64 GlobalTime_ns. All sensitive steps remain present.

Compact contains Groups, GroupVolumes and Tracks, plus explicit TrackGroups
membership. Groups stores event-local identity, final historical labels and
step/track/volume counts. GroupVolumes stores ordered gas copies, energy sums,
first position and FirstHitTime_ns. Tracks stores one first-sensitive-step
provenance record per event-local track. GroupIndex is -1 (none), nonnegative
(single), or -2 (multiple); TrackGroups lists every membership. This handles
resumed tracks without silently choosing a group. Compact has no Hits tree.
Full branch/type definitions are in [OUTPUT.md](OUTPUT.md).

RunMetadata's geometry/source fields and RunAccounting are unchanged. A separate
OutputMetadata record declares format, output schema 1, timing definition and
processing version. Campaign/job schema 3 records output_mode,
output_schema_version and data_path. Mode changes require a new campaign;
--jobs remains scheduling-only, with one Geant4 worker per contribution.

Raw ROOT → analysis.raw.preprocess → common.model.Group/GroupVolume.
Compact ROOT → validated compact reconstruction → the same Group/GroupVolume.
Diagnostic TrackRecord objects retain provenance. Both requires exact parity,
then uses compact canonical groups. common.spectra, normalization and reporting
serve all formats. Both campaigns additionally compare the independently
accumulated raw summary against the compact summary for normalized rates,
variances, categories, densities, flows and Table 7.2/7.3 inputs.

Timing is pre-step GetGlobalTime()/ns, relative to one Geant4 event. Each compact
first time comes from the same step as its first position, even at zero deposit.
It is inactive in canonical spectra and cannot relate independent primaries in
absolute time. Old schema-0 raw data without timing produces None times. Archived
schema-2 raw campaigns remain readable by Stage B; they are not relabeled or
resumed under the new build/identity. Analysis output schema remains 1, with added
input-format and parity provenance. Archives preserve the selected product;
compact never requires raw files. Stage A stores parity pending Stage B; analysis
records results separately without mutating immutable simulation attempts.

## Reference and legacy audit

All 11 C++ analysis sources/headers/macros remain actively referenced by CMake,
geometry checks or parity tests, including specialized plotters. They moved to
analysis/reference_cpp, keeping executable paths under build/analysis unchanged.
The three old combined-workflow Python files moved to legacy/study/combined;
the dedicated regression still uses them. They are preserved, not deleted.
No file was declared legacy merely because it was old.

The three research notebooks import and expose production functions. The shared
notebook retains detailed scientific explanations; the preprocessing notebooks
teach their formats. Saved outputs are synthetic, executable and guarded by
production-source hashes. No copied production algorithms remain in the cells.

## Validation and measurement

The latest Python suite discovers 44 tests: 43 pass, with optional transport
excluded from that invocation because it already passed separately. Earlier the
same optional integration was enabled in a 44/44 passing run. All-mode synthetic
26-job archive/analysis round trips, C++ reference parity for both layouts/all
26 scales, and notebook execution pass. Serial CTest reports 12 passes and two
existing Geant4-11.3 skips. The final expanded repeated-run transport regression
passes on both serial and single-worker MT builds in all output modes.

Fresh baseline-main versus refactored raw: all 12 historical columns and 1,888
rows, scientific metadata and accounting match exactly. Raw-only versus both
transport is also exact. In a 30-primary GEMsCore_K40 serial run, raw stores
1,888 rows / 126,447 bytes, while compact stores 11 groups, 16 group-volume
records, 218 tracks and 197 membership records / 43,742 bytes: **65.4% less,
2.89× smaller**. Single-worker MT measures 141,651 → 44,624 bytes (68.5% less).
[Detailed evidence and limitations](TWO_STAGE_VALIDATION.md) includes environment
versions and remaining Linux campaign qualification gates.

The documented macOS PART122 full-chain failure remains. A real 26/26 production
campaign and large U238 benchmark were not run. No large diagnostic ROOT file is
committed. Notebook cells and saved figures were checked; an interactive Jupyter
frontend was not tested. No other implementation work is known to be unfinished.

## Example commands

```sh
# canonical raw
python3 study/simulate.py --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/raw-NEW" --primaries 1000 --output-mode raw
# production compact, after production qualification
python3 study/simulate.py --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/compact-NEW" --primaries 100000 --output-mode compact --jobs 16
# parity validation
python3 study/simulate.py --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/both-NEW" --primaries 1000 --output-mode both
# common analysis
python3 study/analyze.py --input "$CYGNO_RUNS/compact-NEW" --output "$CYGNO_RUNS/analysis-NEW"
```

## Files added

- `analysis/README.md`
- `analysis/__init__.py`
- `analysis/common/__init__.py`
- `analysis/common/examples.py`
- `analysis/common/inputs.py`
- `analysis/common/io.py`
- `analysis/common/model.py`
- `analysis/common/normalization.py`
- `analysis/compact/CYGNO30_compact_preprocessing_walkthrough.ipynb`
- `analysis/compact/__init__.py`
- `analysis/compact/benchmark.py`
- `analysis/compact/io.py`
- `analysis/compact/parity.py`
- `analysis/compact/preprocess.py`
- `analysis/raw/CYGNO30_raw_preprocessing_walkthrough.ipynb`
- `analysis/raw/__init__.py`
- `docs/COMPACT_REFACTOR_REPORT.md`
- `include/cygno/output/CompactAccumulator.hh`
- `include/cygno/output/CompactOutput.hh`
- `include/cygno/output/StepRecord.hh`
- `src/output/CompactOutput.cc`
- `tests/compact_fixtures.py`
- `tests/test_compact.py`
- `tests/test_notebooks.py`
- `validation/compact_accumulator.cc`
- `validation/compact_transport.py`
- `validation/execute_notebooks.py`

## Files moved

- `analysis/Analysis.hh` → `analysis/reference_cpp/Analysis.hh`
- `analysis/DetectorGeometry.hh` → `analysis/reference_cpp/DetectorGeometry.hh`
- `analysis/ExactEnergyWindows.hh` → `analysis/reference_cpp/ExactEnergyWindows.hh`
- `analysis/FileIdentity.hh` → `analysis/reference_cpp/FileIdentity.hh`
- `analysis/Normalization.hh` → `analysis/reference_cpp/Normalization.hh`
- `analysis/PlotNormalizedSpectra.cpp` → `analysis/reference_cpp/PlotNormalizedSpectra.cpp`
- `analysis/PlotNormalizedSpectra_GEMchain.cpp` → `analysis/reference_cpp/PlotNormalizedSpectra_GEMchain.cpp`
- `analysis/PlotNormalizedSpectra_single.cpp` → `analysis/reference_cpp/PlotNormalizedSpectra_single.cpp`
- `analysis/PlotSpectrum.C` → `analysis/reference_cpp/PlotSpectrum.C`
- `analysis/ProcessEvents.cc` → `analysis/reference_cpp/ProcessEvents.cc`
- `analysis/SimpleProcessEvents.cpp` → `analysis/reference_cpp/SimpleProcessEvents.cpp`
- `study/CYGNO30_background_analysis_walkthrough.ipynb` → `analysis/common/CYGNO30_background_analysis_walkthrough.ipynb`
- `study/figures.py` → `legacy/study/combined/figures.py`
- `study/processing.py` → `analysis/raw/preprocess.py`
- `study/raw_io.py` → `analysis/raw/io.py`
- `study/reporting.py` → `analysis/common/reporting.py`
- `study/root_io.py` → `legacy/study/combined/root_io.py`
- `study/runner.py` → `legacy/study/combined/runner.py`
- `study/spectra.py` → `analysis/common/spectra.py`

## Existing files changed

- `CMakeLists.txt`
- `README.md`
- `analysis/CMakeLists.txt`
- `app/rdecay01.cc`
- `docs/ANALYSIS.md`
- `docs/BACKGROUND_STUDY.md`
- `docs/CODE_GUIDE.md`
- `docs/FILE_MOVES.json`
- `docs/FINALIZATION.md`
- `docs/LAYOUT.md`
- `docs/OUTPUT.md`
- `docs/REPOSITORY_TREE.txt`
- `docs/STUDY_SOURCES.md`
- `docs/TWO_STAGE_VALIDATION.md`
- `include/cygno/output/HitOutput.hh`
- `include/cygno/output/SensitiveDetector.hh`
- `legacy/README.md`
- `src/actions/RunAction.cc`
- `src/output/HitOutput.cc`
- `src/output/SensitiveDetector.cc`
- `study/analyze.py`
- `study/campaign.py`
- `study/runtime.py`
- `study/simulate.py`
- `tests/fixtures.py`
- `tests/test_offline.py`
- `tests/test_parity.py`
- `tests/test_workflow.py`
- `validation/CMakeLists.txt`
- `validation/README.md`
- `validation/check_analysis.py`
- `validation/check_hits.py`
- `validation/run_checks.py`
- `validation/test_analysis.py`
- `validation/test_layout_analysis.py`
- `validation/test_study_runner.py`
