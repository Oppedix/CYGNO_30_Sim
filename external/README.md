# External — LNGS gamma and neutrons with Cu20

An independent workflow using the [common Geant4 build](../README.md), geometry
and materials. External retains the **v2 detector** and rejects internal PMMA v3.
Default shielding is **20 cm Cu in four adjacent 5 cm closed layers**.
The supplied Hall C gamma and neutron inputs are explicit **proxy scenarios**,
not validated site predictions. See [physics and source provenance](docs/PHYSICS.md).

## Checkout and common build

Follow [setup](../docs/SETUP.md) in order: connect/open a terminal, clone in the
chosen parent, define `CYGNO_SRC`, `CYGNO_BUILD`, `CYGNO_RUNS`, activate Geant4,
and compile `rdecay01` plus `geometry_quantities` once. Separate examples cover
local, private Linux and CNAF. Reuse the Internal build on the same machine.
Simulation needs Python ≥3.10 and matching Geant4 datasets including G4NDL,
not CERN ROOT. All commands below start from the repository root.

## Smoke simulation

Gamma and neutrons are separate campaigns, one source spectrum and one worker
each. Qualify **both** on the target machine:

```bash
# Directory: $CYGNO_SRC; common Geant4 environment/build from setup.
cd "$CYGNO_SRC"
python3 external/study/simulate.py --config external/config/hall-c-gamma-2026-proxy.json \
  --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/external-gamma-smoke-NEW" \
  --primaries 1000 --output-mode compact
python3 external/study/simulate.py --config external/config/hall-c-neutron-wulandari-proxy.json \
  --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/external-neutron-smoke-NEW" \
  --primaries 1000 --output-mode compact
```

Defaults are Cu20, `QGSP_BIC_HP_EMZ + G4RadioactiveDecayPhysics`, and an inward
Lambert/cosine GPS source on a sphere outside all shielding corners. For an
unshielded control, choose a new campaign and add `--shield none`; the source
radius and incoming flux stay the same. `--output-mode both` enables Python
same-transport parity checks in a separate diagnostic campaign. `--dry-run`
prints the macro without transporting particles.

## Production campaigns

After geometry/GPS, gamma **and neutron** smoke, accounting, raw/compact parity
and physical-input review on the target environment, choose explicit statistics.
The 1M counts below are **configurable examples**, not a validated precision
target; the supplied configs default to only 1000 primaries.

```bash
# Directory: $CYGNO_SRC; qualified common environment, two fresh campaign directories.
cd "$CYGNO_SRC"
python3 external/study/simulate.py --config external/config/hall-c-gamma-2026-proxy.json \
  --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/external-gamma-production-NEW" \
  --primaries 1000000 --output-mode compact
python3 external/study/simulate.py --config external/config/hall-c-neutron-wulandari-proxy.json \
  --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/external-neutron-production-NEW" \
  --primaries 1000000 --output-mode compact
```

Review the configured 3600 s timeout before scaling statistics; a changed config
requires a new campaign. Repeat an identical command to verify/reuse complete
output; add `--retry-failed` after failure/interruption. A separate `--seed` and
new output allow independent replicates. There is no external `--mode production`
or internal decay preflight. See [validation](docs/VALIDATION.md); the local
macOS neutron Cu-capture failure remains open.

## Cluster

Use [the cluster recipe](docs/WORKFLOW.md#cluster-entry-point), which defines every
wrapper variable and invokes **`external/cluster/run.sh`**. It uses the same
build/configs and one CPU per invocation. Private Linux activation is known;
CNAF login, scheduler and Geant4 activation must come from the site.

## C++ ROOT compact analysis

The standalone [native ROOT guide](analysis/common_c++/README.md#compile) gives
complete compile/run commands, including CNAF ROOT 6.30.02 and ROOT 6.40.04
link differences. It compiles `AnalyzeExternal` separately from Geant4 into
`CYGNO_ANALYSIS_BIN`; no Geant4 or Python is needed on the ROOT worker.

Use a complete **unpacked** external compact/both campaign and a new analysis
directory. Output: `analysis.root`, `spectra.tsv`, `windows.tsv`, `summary.txt`,
`spectra.png/.pdf`. Deposits are summed over the whole detector per primary,
separately for total, e-/e+, charged hadrons/ions and other particles. Native
checks are structural/identity checks; Python performs the full SHA256/track
relationship audit and raw/compact parity.

## Python analysis

Create/activate the [shared Python environment](../docs/SETUP.md#python-analysis-environment-either-workflow),
then analyze both complete campaigns:

```bash
# Directory: $CYGNO_SRC on the analysis machine; Python venv active.
cd "$CYGNO_SRC"
python external/analysis/analyze.py --input "$CYGNO_RUNS/external-gamma-production-NEW" \
  --output "$CYGNO_RUNS/external-gamma-python-NEW"
python external/analysis/analyze.py --input "$CYGNO_RUNS/external-neutron-production-NEW" \
  --output "$CYGNO_RUNS/external-neutron-python-NEW"
```

Python accepts raw/compact/both **unpacked directories**, not internal archives;
it checks raw/compact parity for both. [Transfer instructions](docs/WORKFLOW.md#provenance-attempts-and-transfer)
retain the entire campaign and verify an ordinary archive before unpacking.

## Scientific references and boundaries

- [Physics/flux provenance](docs/PHYSICS.md), [output/normalization](docs/OUTPUT.md), [validation and limitations](docs/VALIDATION.md).
- [Common geometry](../docs/SINGLE_MODULE_GEOMETRY.md) and [Cu20 shielding](../docs/EXTERNAL_SHIELDING.md).
- `config/` holds flux/hall/energy probabilities; `macros/` holds standalone examples; the runner generates exact campaign macros.
- `study/`, `analysis/raw/`, `analysis/compact/` and `analysis/common_c++/` own the external workflow. No detector or CAD is copied here.

Gamma combines a 2026 Hall C integral with a cropped historical shape; neutron
bins use Hall C dry Wulandari integrals with a provisional scalar-flux convention.
Do not transfer rates to Hall F or claim a 2026 measured spectral shape.
Normalization uses saved flux/surface conventions and actual generated primaries,
never internal component activities/masses or Samuele grouping. No quenching,
response, efficiency, trigger or calibrated NR/ER discrimination is included.
Charged hadrons include recoil nuclei **and reaction products**. Small/zero
samples cannot constrain a shielded rate; software success alone is insufficient.
