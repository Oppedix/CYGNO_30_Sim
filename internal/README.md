# Internal — component radioactivity

An independent workflow using the [common Geant4 build](../README.md).
**Current v4** uses a solid EFCu cathode, Acrylic-core GEMs and
**23 contributions** in `cygno-radioassay-v4.json`. Lens activity is Bq/piece
from `CYGNO_radioactivity_excel_suprasil`: the reference mass is 3.843 kg for
**one physical lens**, converted once, then multiplied by actual lens count.
Geant4 lens transport is unchanged. `uniform-volume-v1` and chain controls remain.
**Every v4 contribution needs new transport in a new campaign directory.**
Old results and manifests retain their original identities.

## Checkout and common build

Follow [setup](../docs/SETUP.md) in order: connect/open a terminal, clone in the
chosen parent, define `CYGNO_SRC`, `CYGNO_BUILD`, `CYGNO_RUNS`, activate Geant4,
and compile `rdecay01` plus `geometry_quantities` once. Separate examples cover
local, private Linux and CNAF. `CYGNO_SRC` always means the **repository root**,
not its `internal/` directory. Simulation requires Python ≥3.10, not CERN ROOT.
All commands below start from that root and use external output directories.

## Smoke simulation

```bash
# Directory: $CYGNO_SRC; common Geant4 environment/build from setup.
cd "$CYGNO_SRC"
python3 internal/study/preflight.py --build "$CYGNO_BUILD" --model cygno-copper-cathode-v4 \
  --output "$CYGNO_RUNS/internal-v4-preflight-NEW"
python3 internal/study/simulate.py --config internal/config/study/cygno-11x7-v4.json \
  --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/internal-v4-smoke-NEW" \
  --mode smoke --primaries 2 --output-mode compact --jobs 1
```

The runner also performs its own mandatory four-case U238/Th232/Bi212 preflight.
All 23 jobs must pass even for a tiny complete smoke. The macOS PART122 failure
remains open; use an environment where this gate passes. A complete smoke tests
software, not a statistically meaningful background prediction.

## Production campaign

After the target-environment preflight, smoke, archive/offline and parity gates
in [validation](../docs/TWO_STAGE_VALIDATION.md), run:

```bash
# Directory: $CYGNO_SRC; same common build/environment, fresh campaign directory.
cd "$CYGNO_SRC"
python3 internal/study/simulate.py --config internal/config/study/cygno-11x7-v4.json \
  --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/internal-v4-production-NEW" \
  --primaries 10000000 --output-mode compact --jobs 1 --archive
```

10,000,000 primaries **per contribution** is the configured production target;
1M or 100k is an explicit `--primaries` override. Raise `--jobs` only within
allocated CPU/RAM/I/O resources (e.g. 16 for 16 independent contributions).
Each Geant4 process still has one worker. Repeat the identical command to resume;
failed jobs require `--retry-failed`. Scientific identity changes require a new
campaign directory. See [operation, storage and recovery](docs/WORKFLOW.md).

The executable defaults to v4 in both modes; the runner always passes the
configured model. Historical workflows are documented separately in
[model history](../docs/history/DETECTOR_MODELS.md).

## Cluster

Use [the cluster recipe](docs/WORKFLOW.md#cluster-entry-point), which defines every
wrapper variable and invokes **`internal/cluster/run.sh`**. It uses the same
build, config and production rules as above. Private Linux activation is known;
CNAF login, scheduler and Geant4 activation must come from the site.

## C++ ROOT compact analysis

The standalone [native ROOT guide](analysis/common_c++/README.md#compile) gives
complete compile/run commands, including CNAF ROOT 6.30.02 and ROOT 6.40.04
link differences. It compiles `AnalyzeCompactCampaign` separately from Geant4
into `CYGNO_ANALYSIS_BIN`; no Geant4 or Python is needed on the ROOT worker.

Use the complete unpacked compact campaign above as input and a **new** analysis
directory. The current v4 analyzer checks the matching matrix. Raw, both, partial campaigns and
archives are not native inputs; use Python for those storage modes. Output
includes `analysis.root`, historical Figure 7.5/7.6 spectra, topology figures,
`summary.txt`, `cutflow.md` and normalization provenance. The extra topology
selections are native-analysis studies; Python's canonical report retains the
two historical selections.

## Python analysis

Create/activate the [shared Python environment](../docs/SETUP.md#python-analysis-environment-either-workflow),
then run either input form below (different outputs):

```bash
# Directory: $CYGNO_SRC on the analysis machine; Python venv active.
cd "$CYGNO_SRC"
python internal/study/analyze.py --input "$CYGNO_RUNS/internal-v4-production-NEW" \
  --output "$CYGNO_RUNS/internal-v4-python-NEW"
python internal/study/analyze.py --input "$CYGNO_RUNS/internal-v4-production-NEW.tar.gz" \
  --output "$CYGNO_RUNS/internal-v4-python-archive-NEW"
```

Python accepts raw/compact/both, verifies full artifact integrity, and checks
raw/compact parity for both. It writes spectra/tables JSON/text, `table7.2.csv`,
`table7.3.csv`, `figure7.5.png/.pdf`, `figure7.6.png/.pdf`, copied `campaign.json`
and `analysis-manifest.json`. `--allow-partial` permits labeled diagnostics only
(exit 2). Actual generated counts and constructed masses/pieces normalize each
source before category summation. Both analyses preserve the simulation matrix
and separately record `normalization-scenario.json`.

## Scientific references and compatibility

- [Complete geometry/material tables](../docs/SINGLE_MODULE_GEOMETRY.md) and [source provenance](docs/STUDY_SOURCES.md): activities, upper limits, proxies, omitted isotopes and the solid EFCu cathode and physical-lens per-piece activity.
- [Workflow contract](docs/BACKGROUND_STUDY.md), [output/timing](docs/OUTPUT.md), [analysis semantics](docs/ANALYSIS.md), [notebooks](analysis/README.md).
- [Known issues](docs/KNOWN_ISSUES.md) and [development/reference checks](docs/DEVELOPMENT.md).

`analysis`, `study`, `config`, `macros`, `legacy`, `validation` and several guides
are intentional relative symlinks to their historical locations. Keep them when
copying the checkout; root paths remain supported. `macros` exposes `config/cygno`;
`legacy` contains historical combined workflows, not production defaults.
The stable `GEMsPolyimide` ID denotes GEM PMMA cores in v4; PMMA50 is a
study choice, not a claim about installed CYGNO foils. Internal physics is
`QGSP_BIC_EMZ + G4RadioactiveDecayPhysics`, unshielded. Retained grouping,
first-position fiducialization and heavy-ion stopping are internal assumptions;
use External for environmental neutron recoil transport.
