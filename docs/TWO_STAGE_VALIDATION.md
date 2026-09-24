# Raw/compact refactor validation — 2026-09-24

Baseline `main`: **60823eca4bd10c5f27cdc38e76f8d447c7ac050f**, verified against
freshly fetched origin/main. Work remains in the existing working tree, uncommitted;
no push, merge, large campaign or scientific-model change was performed.

## Final executed checks

- Current Python suite: **44 tests discovered, 43 passed, 1 optional transport
  test skipped**. That transport test was separately enabled and passed in the
  earlier 44/44 run, and standalone 30-primary checks passed on both serial
  Geant4 11.3.1 and single-worker MT Geant4 11.4.2. The last Python run rechecked
  campaign/schema compatibility and saved notebook source hashes after final edits.
- Includes old schema-2 archive analysis, new schema-3 raw/compact/both 26-job
  **synthetic** archive/analysis round trips, exact normalized spectra/tables,
  resume/identity/retry/cancellation/parallel scheduling, strict schemas and
  malformed relationships, first positions/times, pure C++ accumulator replay,
  explicit event-end versus inferred boundary/EOF, and timing independence.
- Active C++/ROOT reference parity passes for both layouts, all 26 scales and
  categories, every 900-bin edge and adjacent floats, exact windows/flows,
  rates and group-Poisson variances. Same-transport raw/compact comparisons are
  exact; no floating-point tolerance is used for representation parity.
- Serial reference-build CTest: **12 passed, 2 documented skips, no failures**.
  Skips are the existing Geant4-11.3 surface-RNG replay limitations. Geometry,
  layout, chain boundaries, long-lived checks, old combined workflow, source
  matrix, C++ analysis and transport regressions pass.
- After the final transport-regression extension, the directly affected test
  passes again on **serial and MT** builds. All three output modes execute two
  successive runs: correct filenames/trees/metadata, exact first-run parity,
  reset event/group/track keys and second-run accounting, no stale rows.
- A freshly built unmodified baseline at 60823ec and the refactored raw output
  agree exactly in all **12 historical fields and 1,888 rows**, scientific
  metadata and accounting for the same 30-primary K40 macro/seeds. Timing is
  the sole added raw field.
- All three notebooks execute top-to-bottom using the lightweight plain-Python
  cell runner. Saved outputs include implementation hashes; tests reject stale
  saved outputs after production changes. Both generated example PNGs were
  visually inspected. A full interactive Jupyter frontend/kernel was not used;
  no new notebook framework dependency was added.
- Active compiled-source provenance matches CMake's generated hash. All file-move
  destinations exist. Whitespace checks pass. No generated ROOT/log/object/image
  artifacts are present in the public working-tree file inventory; intentional
  saved notebook outputs are retained. Scientific geometry, source sampler,
  TrackingAction, source matrix and canonical config have no diff.

## Measured storage (30 primaries, unchanged GEMsCore_K40 contribution)

| Environment | Raw rows | Groups | Group volumes | Tracks | Raw bytes | Compact bytes | Reduction |
|---|---:|---:|---:|---:|---:|---:|---:|
| Serial Geant4 11.3.1 | 1,888 | 11 | 16 | 218 | 126,447 | 43,742 | 65.4%, 2.89× smaller |
| MT Geant4 11.4.2, one worker | 2,201 | 13 | 13 | 273 | 141,651 | 44,624 | 68.5%, 3.17× smaller |

These are separately measured raw and compact files. In each environment, raw-only
and both-mode raw physics/accounting rows are identical. Raw and compact groups,
first times, tracks, cuts, windows and bins match exactly. Different Geant4 builds
are not claimed to generate the same transport. Compression is diagnostic, not a
scientific pass threshold. Large U238 storage performance is not measured here.

## Limits and remaining production gates

Full-chain GEMsCore_U238 tests hit the documented macOS **PART122** failure in
both installed Geant4 environments. No workaround, isotope substitution inside
that contribution, gate bypass, or decay-physics change was made. The successful
local storage example uses the separately named, unchanged K40 matrix contribution.

A real full 26/26 compact campaign/archive on the validated Linux environment
remains an operator qualification step: rebuild, pass all four preflights, run
small both-mode parity, complete a small matrix campaign, and analyze its archive.
The existing campaign preflight still refuses production when any gate fails.
Synthetic archive checks and local K40 parity do not establish physical rates or
full-chain production qualification. Compact retains the specified historical
analysis information, not arbitrary step trajectories for future reconstructions.

[Implementation and file inventory](COMPACT_REFACTOR_REPORT.md) ·
[ROOT schema and timing](OUTPUT.md) · [Analysis modules/notebooks](../analysis/README.md)

---

The following section records the earlier two-stage refactor only. Statements
about unchanged raw schemas there refer to that earlier revision.

# Historical validation: two-stage refactor — 2026-09-23

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
- `legacy/study/combined/figures.py`
- `study/preflight.py`
- `analysis/raw/preprocess.py`
- `analysis/raw/io.py`
- `analysis/common/reporting.py`
- `study/requirements-analysis.txt`
- `legacy/study/combined/runner.py`
- `study/runtime.py`
- `study/simulate.py`
- `analysis/common/spectra.py`
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
