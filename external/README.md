# External — environmental gamma and neutrons at LNGS

A separate scientific workflow using the **same** Geant4 detector construction,
materials and layouts as [internal](../internal/README.md). The active detector is
analytical Geant4 geometry, not an imported CYGNO-04 CAD. No detector or CAD is
copied here. Start with [physics and source provenance](docs/PHYSICS.md),
[cluster usage](docs/WORKFLOW.md), and [output/analysis semantics](docs/OUTPUT.md).

| Path | Purpose |
|---|---|
| `config/` | Explicit flux convention, hall, energy probabilities and source provenance |
| `macros/` | Small standalone gamma/neutron examples; exact campaign macros are generated |
| `study/simulate.py` | ROOT-free runner, receipts, immutable attempts and complete accounting |
| `analysis/common_c++/AnalyzeExternal.cpp` | Preferred standalone compact ROOT analysis |
| `analysis/raw/`, `analysis/compact/`, `analysis/analyze.py` | Python raw/compact readers, parity and primary-event spectra |
| `cluster/run.sh` | Configurable batch entry point |
| `docs/` | External scientific contract, usage, limitations and validation evidence |

## Build and simulate locally

Build **once from the parent repository root**, exactly as in internal. Simulation
requires Geant4 11, matching datasets including G4NDL, C++17, CMake and Python ≥3.10.
It does not need CERN ROOT, uproot or notebooks.

```bash
export CYGNO_SRC=/path/to/CYGNO_30_Sim
export CYGNO_BUILD=/path/to/build/cygno-common
export CYGNO_RUNS=/path/to/runs/external
cmake -S "$CYGNO_SRC" -B "$CYGNO_BUILD" -DCMAKE_BUILD_TYPE=Release \
  -DWITH_GEANT4_UIVIS=OFF -DCYGNO_BUILD_ANALYSIS=OFF -DBUILD_TESTING=OFF \
  -DGeant4_DIR=/path/to/geant4/lib/cmake/Geant4
cmake --build "$CYGNO_BUILD" --parallel
cd "$CYGNO_SRC"
python3 external/study/simulate.py --config external/config/hall-c-gamma-2026-proxy.json \
  --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/gamma-smoke-NEW" --primaries 1000
python3 external/study/simulate.py --config external/config/hall-c-neutron-wulandari-proxy.json \
  --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/neutron-smoke-NEW" --primaries 1000
```

Both provided configurations are **explicit proxy scenarios**, not validated
predictions at the actual installation point. Gamma uses the 2026 Hall C integral
with a cropped historical shape; neutrons use broad Hall C dry Wulandari bin
integrals with a provisional scalar-flux interpretation. Do not transfer Hall C
rates to Hall F or assume the source shape is measured in 2026.

External defaults: 20 cm Cu in four adjacent 5 cm closed layers,
`QGSP_BIC_HP_EMZ + G4RadioactiveDecayPhysics`, inward Lambert/cosine GPS source
on a sphere outside all shielding corners. For the unshielded control use a new
output and `--shield none`. `--output-mode both` enables same-transport Python
parity validation; `--dry-run` prints the exact macro without Geant4. One source
spectrum and one worker per campaign; run gamma and neutron campaigns independently.
Repeat the same command to verify/reuse a completed result; use `--retry-failed`
for a fresh attempt after failure/interruption. No existing attempt is overwritten.

## Analyze with C++ ROOT (preferred)

ROOT with RooFit/HS3 JSON support is required; Geant4 and Python are not:

```bash
c++ -O3 -std=c++17 -ffp-contract=off external/analysis/common_c++/AnalyzeExternal.cpp \
  $(root-config --cflags --libs) -lRooFitHS3 -lRooFitJSONInterface \
  -o "$CYGNO_BUILD/AnalyzeExternal"
"$CYGNO_BUILD/AnalyzeExternal" "$CYGNO_RUNS/gamma-smoke-NEW" "$CYGNO_RUNS/gamma-root-NEW"
```

On ROOT 6.40 installations without `libRooFitJSONInterface`, omit that library.
Input is a complete, unpacked external campaign containing **compact** data
(`compact` or `both`; Python checks raw/compact parity for `both`). Output is
`analysis.root`, `spectra.tsv`, `windows.tsv`, `summary.txt`, `spectra.png/.pdf`.
It sums the whole detector's deposited energy per primary, separately for total,
e-/e+, charged hadrons/ions, and other particles. It does not apply internal
Samuele grouping, activity normalization or detector reconstruction cuts.

Python also supports raw, compact and both, performs full artifact/source checks,
and validates compact track relationships. Both mode checks raw/compact parity:

```bash
python3 -m pip install -r "$CYGNO_SRC/study/requirements-analysis.txt"
python3 external/analysis/analyze.py --input "$CYGNO_RUNS/gamma-smoke-NEW" \
  --output "$CYGNO_RUNS/gamma-python-NEW"
```

No quenching, detector response, signal efficiency, trigger, or calibrated NR/ER
discrimination is included. The charged-hadron channel includes nuclear recoils
**and reaction products**. Small/zero samples cannot constrain a shielded rate.
See [validation](docs/VALIDATION.md) before interpreting annual numbers.
