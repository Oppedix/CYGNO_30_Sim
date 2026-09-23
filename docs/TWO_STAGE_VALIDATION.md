# Two-stage refactor validation — 2026-09-23

These are software checks on the local macOS/arm64 workstation, not a Linux
production qualification or a background-rate estimate. Starting repository
revision: `83a0a3e`; changes remain uncommitted for review. No push/merge or large
campaign was performed.

## Implemented architecture

Stage A (`study/simulate.py`) uses the Python standard library, `rdecay01` and the
ROOT-free production exporter `geometry_quantities`. It validates JSON/log
accounting and immutable provenance, retains attempts, and optionally packages
complete campaigns. Stage B (`study/analyze.py`) validates raw TTrees with uproot,
streams historical grouping across chunks and writes normalized spectra/tables
and matplotlib figures. C++/ROOT analysis remains an optional reference.

Scientific input files, common geometry, sampler, active physics, Hits schema,
RunMetadata and the Table 7.1 matrix are unchanged. The only simulation change is
an accounting log emitted after successful ROOT closure. The canonical 10^7
setting, full-chain commands and 1e60-year threshold are retained.

## Executed checks

- Fresh Release build against local **serial Geant4 11.3.1**, with UI/vis,
  CERN ROOT analysis and BUILD_TESTING all OFF: `rdecay01` and
  `geometry_quantities` build. No ROOT discovery variables in CMakeCache.
  Local macOS required explicit Homebrew ZLIB paths to match its Geant4 build;
  this is not an additional Linux dependency or project flag requirement.
- **20 tests passed** in the standalone suite, including optional C++ parity;
  a subsequent focused test also verifies Git-free archived analysis provenance.
  Standard-library simulation tests and synthetic uproot tests cover: counts,
  deterministic macros/seeds, fatal/abort rejection, resume/retry/interruption,
  1M CLI override with synthetic transport, failed preflight gate, identity
  mismatches, archive/checksum round-trip, traversal/link/device/duplicate
  rejection, raw schema/row count/data checks, chunk/event/EOF boundaries,
  fiducial/window boundaries, scaling/categories and partial report labels.
- Optional parity executes actual C++/ROOT executables (ROOT 6.40.04) against
  uproot fixtures for **both layouts and all 26 contribution scales**. Group
  labels, volume/energy/position vectors match exactly. Every histogram bin,
  under/overflow, variance, exact-window count/rate and category sum agrees
  within floating-point summation tolerance. Tests include all 900-bin edges
  and their adjacent floating-point values. The ROOT edge-rounding correction
  was ported after the test exposed it; no scientific window was changed.
- A real standalone **two-primary GEMsCore_K40** serial run produced 159 Hits
  rows and one grouped event. Log and ROOT counters both read requested=2,
  generated=2, processed=2, aborted=0. Python and C++ groups/vectors are identical.
  This isolates output/reader equivalence; it does not bypass the campaign gate.
- Local four-case preflight: U238-default and U238-enabled pass; Th232-full and
  Bi212-full fail with PART122. A real Stage A invocation refused to create jobs
  after this failed preflight. No workaround or decay change was attempted.
- Existing C++ analysis, layout analysis, source matrix, layout profiles,
  chain-boundary, long-lived and legacy combined-runner checks pass.
  The older exact solid-surface RNG replay tests explicitly **skip on 11.3**:
  its private surface RNG has no public state/seed reset API. Their 11.4 checks
  remain enabled. This is a disclosed test limitation, not a passing replay test.
- A 26-contribution **synthetic** campaign was packaged, checksum-verified,
  extracted and analyzed without CERN ROOT. PNG/PDF/CSV/JSON outputs were produced;
  the PNG was visually inspected. This is not a real 26-job transport smoke.

Run the standalone suite after installing `study/requirements-analysis.txt`:

```sh
CYGNO_REFERENCE_BUILD=/path/to/reference-build \
  python -m unittest discover -s tests -v
```

Omit the environment variable to skip optional C++ parity. Standard-library-only
checks: `python3 -m unittest discover -s tests -p test_simulation.py -v`.

## Remaining human gates

The operator reports a separate Ubuntu 22.04.5 x86_64 / GCC 11.4.0 / private
serial Geant4 11.3.1 installation passing all four preflights. That result is
**empirical and environment-specific**; it was not rerun from this workstation.
After transferring this refactor:

1. Build headlessly on that Linux installation and repeat 4/4 preflight.
2. Run the actual 26/26 small smoke with `study/simulate.py`.
3. Package it and validate/analyze the archive offline.
4. Run the controlled Python/C++ reference comparison with the matching build.
5. Only then consider `--primaries 1000000` for each contribution.

Copyable commands are in [README](../README.md). Exact published-rate agreement
is not established: inherited geometry/sampling/grouping limitations and the
last-ion `Nucleus` meaning remain. Group-Poisson uncertainties are not primary-level
uncertainties. Archive analysis needs temporary disk space for unpacking; Hits
processing itself is chunked. No new intermediate event store is generated.

## Changed files

`validation/geometry_quantities.cc` moved to `app/geometry_quantities.cc`.
New and modified files retained for review:

- `.gitignore`
- `CMakeLists.txt`
- `README.md`
- `app/geometry_quantities.cc`
- `docs/ANALYSIS.md`
- `docs/BACKGROUND_STUDY.md`
- `docs/CODE_GUIDE.md`
- `docs/FINALIZATION.md`
- `docs/KNOWN_ISSUES.md`
- `docs/OUTPUT.md`
- `docs/REPOSITORY_TREE.txt`
- `docs/SOURCES.md`
- `docs/STUDY_PROGRESS.md`
- `docs/STUDY_SOURCES.md`
- `docs/TWO_STAGE_VALIDATION.md`
- `src/actions/RunAction.cc`
- `study/analyze.py`
- `study/archive.py`
- `study/campaign.py`
- `study/figures.py`
- `study/preflight.py`
- `study/processing.py`
- `study/raw_io.py`
- `study/reporting.py`
- `study/requirements-analysis.txt`
- `study/runner.py`
- `study/runtime.py`
- `study/simulate.py`
- `study/spectra.py`
- `tests/fixtures.py`
- `tests/test_offline.py`
- `tests/test_parity.py`
- `tests/test_simulation.py`
- `tests/test_workflow.py`
- `validation/CMakeLists.txt`
- `validation/README.md`
- `validation/geometry_quantities.cc`
- `validation/source_checks.cc`
- `validation/test_long_lived.py`
- `validation/test_source_matrix.py`
