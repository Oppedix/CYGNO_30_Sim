# CYGNO_30_Sim

Geant4 radioactive-background simulation of 75 modules (5 × 5 × 3 or historical
25 × 3), with
150 sensitive gas cells and separate ROOT analysis. Derived from Geant4's
`rdecay01` example; see [license and provenance](legacy/README.md).

## Build

Requires CMake ≥3.16, a C++17 compiler and Geant4 11 with its datasets.
Qt/visualization is needed for the interactive viewer. CERN ROOT 6 and a Python
interpreter with PyROOT are needed for analysis and the complete test suite;
the simulation itself writes ROOT through Geant4 without linking CERN ROOT.
Source your installation's `geant4.sh` first. From this repository:

```sh
cmake -S . -B ../../build/cygno-final -DCMAKE_BUILD_TYPE=Release \
  -DCYGNO_BUILD_ANALYSIS=ON -DPython3_EXECUTABLE="$(command -v python3)"
cmake --build ../../build/cygno-final --parallel
```

Choose a **new** build directory when recovering old work. In-source builds are
rejected. For simulation only, omit `CYGNO_BUILD_ANALYSIS`; disable tests with
`-DBUILD_TESTING=OFF` if Python/PyROOT is unavailable. Headless configurations can
use `-DWITH_GEANT4_UIVIS=OFF`.

## Run and output

```sh
# Interactive geometry viewer:
(cd ../../build/cygno-final && ./rdecay01)
# A small radioactive run (Po-212 in cathodes, fixed seeds, 20 events):
(cd ../../build/cygno-final && ./rdecay01 config/cygno/po212-smoke.mac)
```

Files appear in `outfiles_V2/` relative to the process working directory, created
automatically. The example produces `cleanup_smoke_t0.root`; the optional second
argument selects workers, e.g. `./rdecay01 config/cygno/po212-smoke.mac 2`.
Use a separate run directory/basename to retain outputs. Each worker writes its
own `Hits` tree. Macro configuration and matching source must accompany raw files.

Select layout without rebuilding:

```sh
/path/to/build/rdecay01 /absolute/path/to/run.mac 1 --layout legacy-25x3
/path/to/build/rdecay01 /absolute/path/to/run.mac 1 --layout cygno-5x5x3-v1
```

The default remains `cygno-5x5x3-v1`. Both use the unchanged code-compatible
internals and historical sampler. Both layouts support processing and plotting
with validated layout/model identity recorded separately from Hits. See
[study progress](docs/STUDY_PROGRESS.md) and [layout details](docs/LAYOUT.md).

## Analysis and tests

```sh
../../build/cygno-final/analysis/SimpleProcessEvents \
  ../../build/cygno-final/outfiles_V2/cleanup_smoke_t0.root /tmp/processed.root
ctest --test-dir ../../build/cygno-final --output-on-failure
# Known failure, deliberately outside the passing suite:
python3 validation/run_checks.py bi212 ../../build/cygno-final
```

New raw files carry a separate `RunMetadata` tree. Unversioned files require both
`--assume-layout PROFILE --assume-model code-compatible`, after verifying their
source revision. Assumptions cannot override conflicting file metadata.
The published [26-contribution source matrix](docs/STUDY_SOURCES.md) now supports
explicit kg/piece normalization and categories from separately scaled materials.
Normalized plotters require a study configuration; old masses and assays are
**not production defaults**. See [analysis and normalization](docs/ANALYSIS.md).

The [resumable smoke runner](docs/STUDY_RUNNER.md) records counts, seeds, datasets,
quantities and failures, with exact energy windows and explicit unvalidated-chain
status. Follow the phase gate in [study progress](docs/STUDY_PROGRESS.md) before
starting a campaign.

Read [architecture and event lifecycle](docs/CODE_GUIDE.md),
[geometry](docs/LAYOUT.md), [source and decay policy](docs/SOURCES.md),
[output schema](docs/OUTPUT.md), [validation](validation/README.md),
[known scientific issues](docs/KNOWN_ISSUES.md) and the
[recovery report](docs/REFACTOR_REPORT.md). Software checks do not validate the
scientific detector or contamination model.
