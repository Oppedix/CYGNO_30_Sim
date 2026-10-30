# Internal development and historical references

Operational commands are in the [Internal guide](../README.md); cloning and
Geant4 compilation are in [common setup](../../docs/SETUP.md). This page keeps
optional reference builds and developer checks separate from production.

## Checks

Use Python ≥3.10. The simulation-only suite uses the standard library; the full
suite needs the [analysis environment](../../docs/SETUP.md#python-analysis-environment-either-workflow).

```bash
# Directory: repository root.
cd "$CYGNO_SRC"
python3 -m unittest discover -s tests -p test_simulation.py -v
# Analysis venv active for synthetic ROOT fixtures and the rest of the suite:
python -m unittest discover -s tests -v
```

These tests do not launch large production. Optional C++/ROOT parity checks
cover layouts, historical v2's 28 scales/categories, grouping, chunk/EOF
boundaries, exact energy windows, histogram edges/flows and MC variances.
The standalone compact analyzer has its own historical/v4/topology regressions in
[its guide](../../analysis/common_c++/README.md#equivalence-checks).

## Optional historical C++ reference build

`CYGNO_BUILD_ANALYSIS=ON` enables `analysis/reference_cpp/`, **not** the two
standalone compact analyzers. This optional historical comparison requires both
Geant4 and CERN ROOT on the same machine. Choose a separate configurable build
so the normal ROOT-free common build remains easy to reproduce:

```bash
# Directory: $CYGNO_SRC; Geant4 and CERN ROOT environments already active.
cd "$CYGNO_SRC"
export REFERENCE_BUILD="${CYGNO_BUILD}-reference"
cmake -S . -B "$REFERENCE_BUILD" -DWITH_GEANT4_UIVIS=OFF \
  -DCYGNO_BUILD_ANALYSIS=ON -DBUILD_TESTING=OFF -DGeant4_DIR="$Geant4_DIR"
cmake --build "$REFERENCE_BUILD" --target SimpleProcessEvents \
  PlotNormalizedSpectra geometry_quantities --parallel
CYGNO_REFERENCE_BUILD="$REFERENCE_BUILD" \
  python -m unittest discover -s tests -p test_parity.py -v
```

`legacy/study/combined/runner.py` retains the combined PyROOT/reference workflow;
it is not the current production entry point. Numerical grouping/normalization
contracts and retained physical limits are in
[BACKGROUND_STUDY](BACKGROUND_STUDY.md) and [ANALYSIS](ANALYSIS.md).

## Validation evidence versus production gates

The final geometry report retains executed-check counts and environment details;
[TWO_STAGE_VALIDATION](TWO_STAGE_VALIDATION.md) records smoke/archive/offline/parity
evidence and remaining gates. Historical 28/28 Linux smoke requirements refer to
v2; current v4 must qualify all its 23 material contributions (25 with `--gas-bkg yes`) with new transport.
See [gas validation](../../docs/GAS_VALIDATION.md) for the additional source,
normalization, archive, plotting and decay-transport checks.
A fresh four-case decay preflight is required on the target environment before
smoke, followed by archive/offline validation and a controlled reference check
before scaling to 1M/10M. Tests do not bypass PART122 or establish physical rates.
