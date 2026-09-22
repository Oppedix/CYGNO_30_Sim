# CYGNO internal-radioactivity background study

Reproduce the **workflow** of Samuele Torelli's background study: Geant4 source
macros → worker Hits ROOT → grouped events → activity normalization → seven
component categories → spectra and tables. The reference is **legacy-25x3**,
**code-compatible** detector internals, **historical** source sampling.

The long-lived decay setting is explicit. **The tested Geant4 11.4.2 environment
fails the Th/Bi full-chain preflight**; affected contributions remain incomplete.
Smoke outputs demonstrate software operation, not a production background estimate.
See [known issues](docs/KNOWN_ISSUES.md) before interpreting rates.

## Prerequisites and build

CMake ≥3.16, C++17 compiler, Geant4 11 with its matching datasets, CERN ROOT 6,
and Python ≥3.11 with PyROOT. Qt/OpenGL support is needed for the interactive
viewer. Source your Geant4 installation's `bin/geant4.sh` and ROOT environment.
From the repository root, use directories outside Git:

```sh
export REPO="$PWD"
export BUILD="$REPO/../cygno-build"
export RUNS="$REPO/../cygno-runs"
cmake -S "$REPO" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release \
  -DCYGNO_BUILD_ANALYSIS=ON -DPython3_EXECUTABLE="$(command -v python3)"
cmake --build "$BUILD" --parallel 6
```

For a headless build add `-DWITH_GEANT4_UIVIS=OFF`. If discovery needs help, supply
`-DGeant4_DIR=/path/to/geant4/lib/cmake/Geant4` and `-DROOT_DIR=/path/to/root/cmake`.
Simulation writes ROOT through Geant4; the separate analysis links CERN ROOT.

## Visualization and detector

```sh
(cd "$BUILD" && ./rdecay01 --layout legacy-25x3)
```

A tested headless image-export alternative is documented in
[the validation handoff](docs/FINALIZATION.md#visualization).

`legacy-25x3` retains 75 modules / 150 gas cells, centers `(504*i,804*j,0)` mm,
`i=-12..12`, `j=-1..1`, and gas copies `side*75 + 3*(i+12)+(j+1)`.
`cygno-5x5x3-v1` also remains supported and is the executable's compatibility
default; the canonical study explicitly selects legacy. Both share the same
numerically preserved detector and sampler. No 11x7 layout is implemented.
See [layout and copy numbers](docs/LAYOUT.md).

## Run one macro; inspect and process ROOT

Export all 26 explicit macros without running Geant4, then run one in its own
new directory (each macro uses output basename `raw`):

```sh
python3 study/runner.py --mode smoke --macros-dir "$RUNS/macros-smoke"
mkdir -p "$RUNS/manual-k40"
(cd "$RUNS/manual-k40" && "$BUILD/rdecay01" \
  "$RUNS/macros-smoke/GEMsCore_K40.mac" 1 --layout legacy-25x3 > simulation.log 2>&1)
rootls -t "$RUNS/manual-k40/outfiles_V2/raw_t0.root"
"$BUILD/analysis/SimpleProcessEvents" \
  "$RUNS/manual-k40/outfiles_V2/raw_t0.root" "$RUNS/manual-k40/processed.root"
```

Manual runs need a zero exit, no fatal log errors, and complete `RunAccounting`
before normalization. Do not reuse a run directory or overwrite valid results.
See [raw schema](docs/OUTPUT.md) and [processing/normalization](docs/ANALYSIS.md).

## Smoke, matrix, production and resume

```sh
# Inspect all jobs and exact macros; launches no Geant4:
python3 study/runner.py --list
# Full 26-job smoke (2 primaries per job):
python3 study/runner.py --mode smoke --build "$BUILD" --output "$RUNS/smoke"
# Independent environment preflight; directory must be new:
python3 study/preflight.py --build "$BUILD" --output "$RUNS/preflight"
# Production setting: 10^7 primaries per contribution, sequential:
python3 study/runner.py --build "$BUILD" --output "$RUNS/production"
# Resume after Ctrl-C: exactly the same command:
python3 study/runner.py --build "$BUILD" --output "$RUNS/production"
# Retry failed contributions in new attempt directories:
python3 study/runner.py --build "$BUILD" --output "$RUNS/production" --retry-failed
# Regenerate ROOT spectra, PNG/PDF figures and CSV/JSON/text tables, no Geant4:
python3 study/runner.py --build "$BUILD" --output "$RUNS/production" --analysis-only
```

Canonical configuration: [samuele.json](config/study/samuele.json). `--primaries N`
overrides counts; use the identical override on resume. `--only Lens_K40 Sensors_K40`
selects a subset. Without `--output`, campaigns go to `~/cygno-runs/samuele-MODE`.
Production automatically preflights the environment and blocks affected full Th
contributions if it fails. Reports display missing coverage explicitly. Exit 2
means incomplete/failed work, not a complete spectrum. Changing source, build,
configuration or data requires a new campaign directory.

Outputs are in the directory named by `latest-report.json`: `NormalizedHisto.root`,
`figure7.5.png/.pdf`, `figure7.6.png/.pdf`, `table7.2.csv`, `table7.3.csv`,
`tables.json`, `tables.txt` and `spectra.json`. Plot density is **counts / keV / year**;
ROOT source histograms remain counts/bin/year. Published table values are reference
comparisons only. Smoke regeneration uses the same command plus `--mode smoke`.

## Tests and detailed guides

```sh
ctest --test-dir "$BUILD" --output-on-failure
```

Tests include actual fast-isotope and long-lived U-238 transport, both layouts,
ROOT processing, normalization, and synthetic interruption/resume/retry cases.
Th/Bi failure is a separate preflight, never hidden inside a passing transport test.

[Complete study workflow](docs/BACKGROUND_STUDY.md) ·
[Code guide](docs/CODE_GUIDE.md) · [Layout](docs/LAYOUT.md) ·
[Sources](docs/SOURCES.md) · [Table 7.1 provenance](docs/STUDY_SOURCES.md) ·
[Output](docs/OUTPUT.md) · [Analysis](docs/ANALYSIS.md) ·
[Known issues](docs/KNOWN_ISSUES.md) · [Validation](validation/README.md) ·
[Progress and recovery](docs/STUDY_PROGRESS.md) · [License/provenance](legacy/README.md).
