# Native ROOT external analysis

## Compile

Activate the analysis machine's actual ROOT environment (`root-config` and
runtime libraries available), then use the
[local/private Linux/CNAF path setup](../../../docs/SETUP.md).
`CYGNO_SRC` is the repository root; `CYGNO_RUNS` is the campaign parent on this
machine. `CYGNO_ANALYSIS_BIN` is a configurable binary directory outside source.
This compilation is separate from the common Geant4 build. No Geant4, Python,
CMake or extra JSON package is needed; minimal ROOT without RooFit/HS3 is
insufficient. The source uses the existing ROOT JSON/typed-leaf idiom.

For **ROOT 6.30.02 on CNAF**, link both JSON libraries:

```bash
# Directory: repository root on the ROOT analysis worker.
cd "$CYGNO_SRC"
export CYGNO_ANALYSIS_BIN="${CYGNO_ANALYSIS_BIN:-$CYGNO_BUILD/root-analysis}"
mkdir -p "$CYGNO_ANALYSIS_BIN"
root-config --version
c++ -O3 -std=c++17 -ffp-contract=off external/analysis/common_c++/AnalyzeExternal.cpp \
  $(root-config --cflags --libs) -lRooFitHS3 -lRooFitJSONInterface \
  -o "$CYGNO_ANALYSIS_BIN/AnalyzeExternal"
```

For the tested **ROOT 6.40.04** installation, JSON comes through HS3 alone:

```bash
# Directory: repository root on the ROOT 6.40 analysis machine.
cd "$CYGNO_SRC"
export CYGNO_ANALYSIS_BIN="${CYGNO_ANALYSIS_BIN:-$CYGNO_BUILD/root-analysis}"
mkdir -p "$CYGNO_ANALYSIS_BIN"
c++ -O3 -std=c++17 -ffp-contract=off external/analysis/common_c++/AnalyzeExternal.cpp \
  $(root-config --cflags --libs) -lRooFitHS3 \
  -o "$CYGNO_ANALYSIS_BIN/AnalyzeExternal"
```

Use a compiler compatible with your ROOT installation and its `root-config`
flags. Keep `-ffp-contract=off` and do not enable `-ffast-math`/`-Ofast`;
volume-to-keV summation order matters.

## Run

Use complete unpacked campaigns from the External guide, transferred first if
analysis runs elsewhere. Output directories must be new and outside the inputs:

```bash
# Directory: $CYGNO_SRC on the analysis machine; ROOT runtime active.
cd "$CYGNO_SRC"
"$CYGNO_ANALYSIS_BIN/AnalyzeExternal" \
  "$CYGNO_RUNS/external-gamma-production-NEW" "$CYGNO_RUNS/external-gamma-root-NEW"
"$CYGNO_ANALYSIS_BIN/AnalyzeExternal" \
  "$CYGNO_RUNS/external-neutron-production-NEW" "$CYGNO_RUNS/external-neutron-root-NEW"
```

With the CNAF setup, these inputs are below
`/cnaf/cygno-sim/Users/goppedis/SolarNu`; they are configurable transfer
locations, not a claim that production data already exist there.

## Inputs, outputs and checks

Input is a completed, unpacked external campaign in compact or both mode.
The compact stream supplies one all-particle Group per track. The loop sums
deposited energies per **primary EventNumber**, counts positive-energy events
in each channel and scales by the saved flux/surface convention and actual
GeneratedPrimaries. It does not import internal activities or component masses.

Output includes ROOT spectra, PNG/PDF, per-bin MC counts and annual rates/variance,
unbinned positive and (10,400] keV counters and a provenance summary. Underflow
and overflow are explicit; spectra have 1000 1-keV bins in [0,1000).
See [full semantics](../../docs/OUTPUT.md), [source assumptions](../../docs/PHYSICS.md)
and [cluster examples](../../docs/WORKFLOW.md).

The fast native loop checks relevant metadata, accounting, event/group/volume
ordering, gas IDs and finite payloads. It trusts the completed campaign for
large-file SHA256 and unused track relationships. Run
`external/analysis/analyze.py` for that full audit and for raw/compact parity
in both mode. C++ and Python comparisons run in `tests/test_external.py` when
ROOT is installed.
