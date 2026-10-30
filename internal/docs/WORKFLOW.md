# Internal operation, recovery and transfer

Start with the [Internal guide](../README.md) for smoke, production and analysis;
[common setup](../../docs/SETUP.md) owns cloning, activation and the single
Geant4 build. All commands here use `CYGNO_SRC` = repository root. Historical
`study/`, `config/` and `analysis/` paths remain supported through relative links.

Gas contamination is optional: append `--gas-bkg yes` to any simulation or
cluster command below for C14 and Rn222. Default `--gas-bkg no` retains 23
material contributions; enabled campaigns have 25, with a separate fingerprint
and output directory. Keep the flag identical when resuming. Analysis discovers
the saved scenario. See [gas science and commands](../../docs/GAS_BACKGROUNDS.md).

## Cluster entry point

First select the [private Linux setup](../../docs/SETUP.md#private-linux-simulation-environment)
or the [CNAF setup](../../docs/SETUP.md#cnaf-analysis-worker). On the execution
node, export `CYGNO_SRC`, `CYGNO_BUILD`, `CYGNO_RUNS` and activate the actual
Geant4 environment. Enter a site-approved allocation before invoking the wrapper;
no scheduler/login command is specified because none is established here.

```bash
# Directory: $CYGNO_SRC on the allocated simulation node.
cd "$CYGNO_SRC"
export CYGNO_CAMPAIGN=internal-v4-cluster-smoke-NEW
export CYGNO_CONFIG="$CYGNO_SRC/internal/config/study/cygno-11x7-v4.json"
export CYGNO_PRIMARIES=2
export CYGNO_JOBS=1
export CYGNO_OUTPUT_MODE=compact
export CYGNO_PYTHON=python3
bash internal/cluster/run.sh --mode smoke
```

After qualification, production in a fresh campaign:

```bash
# Directory: $CYGNO_SRC, same allocation/environment; one CPU for CYGNO_JOBS=1.
cd "$CYGNO_SRC"
export CYGNO_CAMPAIGN=internal-v4-cluster-production-NEW
export CYGNO_PRIMARIES=10000000
bash internal/cluster/run.sh --mode production --archive
```

These commands inherit `CYGNO_SRC`, `CYGNO_BUILD`, `CYGNO_RUNS` from setup and
all other exports from the smoke block. If the allocation has 16 available CPUs,
`CYGNO_JOBS=16` permits up to 16 independent source contributions. Each Geant4
process is still single-worker; CPU, RAM and I/O grow with this limit. Never run
two owners of the same campaign directory.

| Wrapper variable | Required/default |
|---|---|
| `CYGNO_SRC`, `CYGNO_BUILD`, `CYGNO_RUNS`, `CYGNO_CAMPAIGN`, `CYGNO_PRIMARIES` | Required; repository root, shared build, campaign parent, unique name, count per contribution |
| `CYGNO_CONFIG` | Defaults to `internal/config/study/cygno-11x7-v4.json`; v4 selects 23 material contributions, or 25 with `--gas-bkg yes` |
| `CYGNO_JOBS` | Positive concurrency limit; default 1 |
| `CYGNO_OUTPUT_MODE` | Default compact |
| `CYGNO_PYTHON` | Default python3, version ≥3.10 |
| `G4LAB` | If set, wrapper sources `$G4LAB/activate.sh` again; only use for that actual private workspace |

Additional arguments pass directly to `study/simulate.py`, including `--archive`,
`--retry-failed` or `--only Lens_K40 Sensors_K40`. A subset remains partial and
exits 2. Use ordinary workflow variables for data paths; do not repurpose `HOME`
or `TMPDIR` (`TMPDIR` retains its normal temporary-extraction meaning).

## Output modes and parity

The direct Python runner defaults to **raw**; the cluster wrapper defaults to
**compact**. All main examples specify compact explicitly for native analysis.
Output mode is part of scientific identity; changing it requires a fresh output.

```bash
# Directory: $CYGNO_SRC; common Geant4 environment active, new parity campaign.
cd "$CYGNO_SRC"
python3 internal/study/simulate.py --config internal/config/study/cygno-11x7-v4.json \
  --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/internal-v4-parity-NEW" \
  --primaries 1000 --output-mode both --jobs 1
# Stage B checks raw/compact parity from the same transport.
python internal/study/analyze.py --input "$CYGNO_RUNS/internal-v4-parity-NEW" \
  --output "$CYGNO_RUNS/internal-v4-parity-analysis-NEW"
```

The last command needs the [Python analysis environment](../../docs/SETUP.md#python-analysis-environment-either-workflow);
it can run on a different machine after transfer. Raw, compact and both use the
same canonical Python report. Schema 3 records mode, `data_path`, accounting and
checksums; archived schema-2 raw campaigns remain readable. Full storage/timing
contracts are in [OUTPUT](OUTPUT.md); event-relative pre-step ns timing is
inactive in canonical analysis and does not connect independent primaries.

## Completion, resume and identity

Repeat an identical simulation command to resume (`--resume` is optional).
Complete contributions are verified/reused; interrupted jobs get new attempts;
failed jobs need `--retry-failed`. Individual failures do not stop other selected
jobs. Ctrl-C stops scheduling, terminates active simulation process groups and
retains interrupted attempts; completed jobs stay reusable and queued jobs
remain unstarted. Valid previous attempts are never overwritten.

Changing `--jobs` on resume is allowed: it only changes scheduling, not macros,
seeds or fingerprints. Config, source, build, output-mode or dataset/environment
changes need a **new campaign directory**. The runner retains the explicit
`1.0e+60 year` radioactive-decay threshold and authoritative full/split-chain
commands, regardless of statistics. A complete ROOT file cannot override failed
transport/preflight/accounting. See the [full workflow contract](BACKGROUND_STUDY.md).

## Archive and offline analysis

`--archive` writes `CAMPAIGN.tar.gz` plus `.tar.gz.sha256` beside a complete
campaign, retaining the unpacked data. To package separately:

```bash
# Directory: $CYGNO_SRC; production campaign completed successfully.
cd "$CYGNO_SRC"
python3 -m study.archive --input "$CYGNO_RUNS/internal-v4-production-NEW"
```

Archives contain selected data files, every attempt's logs/receipts/macros,
preflight, config/matrix/geometry/quantity snapshots, the actual source snapshot
(including dirty edits) and `SHA256SUMS.json`. Partial campaigns cannot be
packaged as complete. Copy archive **and checksum** to the analysis machine;
Python can read the archive directly. It needs temporary space for an unpacked
copy. Native ROOT needs the complete **unpacked compact** directory.

Use the [native ROOT recipe](../../analysis/common_c++/README.md#compile) or
[Python recipe](../README.md#python-analysis) after setting paths on the analysis
machine. The documented historical CNAF input
`/cnaf/cygno-sim/Users/goppedis/SolarNu/25x3Samuele-1M` is a retained input,
not a newly generated v4 campaign. Paths such as
`/cnaf/cygno-sim/Users/goppedis/SolarNu/internal/11x7-v4-complete` are configurable
transfer destinations and must exist/be complete before analysis.

## Scientific boundary

Internal normalization is per contribution:
`activity × constructed kg or pieces × 31536000 / generated primaries`.
Historical e-/e+/alpha grouping, first-position 20 mm fiducialization and native
optional topology cuts are specified in [ANALYSIS](ANALYSIS.md).
The last tracked ion label (`Nucleus`) is not guaranteed per-hit ancestry.
Published tables are comparisons, never normalization targets.

v4 changes transport for **all** source components crossing the solid copper
cathode. Lens activity is Bq/piece from `CYGNO_radioactivity_excel_suprasil`;
3.843 kg describes one physical lens and is already included in the activity. Do not replace `matrix.json`, relabel manifests or disable
identity/checksum/preflight gates to reuse historical data. Both analyses retain the
simulation matrix and a separate normalization-scenario descriptor; see
[source provenance](STUDY_SOURCES.md).

Internal heavy-ion stopping is retained: use External for environmental neutron
recoil transport. Its `SourcePolicy`/processing markers are deliberately
incompatible with internal activity analysis. Retained cage intersections and
vessel/optics assumptions are in [known issues](../../docs/KNOWN_ISSUES.md).
A passing software gate is not a validated physical background prediction.
