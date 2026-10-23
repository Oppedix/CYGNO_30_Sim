# External operation, recovery and transfer

Start with the [External guide](../README.md) for smoke, production and analysis;
[common setup](../../docs/SETUP.md) owns cloning, activation and the single
Geant4 build. The runner uses Python's standard library and invokes one worker
per campaign in an isolated attempt directory. Simulation needs no CERN ROOT.

## Cluster entry point

First select the [private Linux setup](../../docs/SETUP.md#private-linux-simulation-environment)
or [CNAF setup](../../docs/SETUP.md#cnaf-analysis-worker). On the execution node,
export `CYGNO_SRC`, `CYGNO_BUILD`, `CYGNO_RUNS` and activate the actual Geant4
environment/datasets. Enter a site-approved allocation before invoking the
wrapper; no scheduler/login command is specified because none is established here.

```bash
# Directory: $CYGNO_SRC on the allocated simulation node; one CPU per invocation.
cd "$CYGNO_SRC"
export CYGNO_CAMPAIGN=external-gamma-cluster-smoke-NEW
export CYGNO_CONFIG="$CYGNO_SRC/external/config/hall-c-gamma-2026-proxy.json"
export CYGNO_PRIMARIES=1000
export CYGNO_OUTPUT_MODE=compact
export CYGNO_PYTHON=python3
bash external/cluster/run.sh

# Same directory/environment; independent neutron smoke campaign.
export CYGNO_CAMPAIGN=external-neutron-cluster-smoke-NEW
export CYGNO_CONFIG="$CYGNO_SRC/external/config/hall-c-neutron-wulandari-proxy.json"
bash external/cluster/run.sh
```

After qualifying both gamma and neutron transport, use fresh production campaigns:

```bash
# Directory: $CYGNO_SRC, same allocation/environment and inherited exports.
cd "$CYGNO_SRC"
export CYGNO_PRIMARIES=1000000
export CYGNO_CAMPAIGN=external-gamma-cluster-production-NEW
export CYGNO_CONFIG="$CYGNO_SRC/external/config/hall-c-gamma-2026-proxy.json"
bash external/cluster/run.sh
export CYGNO_CAMPAIGN=external-neutron-cluster-production-NEW
export CYGNO_CONFIG="$CYGNO_SRC/external/config/hall-c-neutron-wulandari-proxy.json"
bash external/cluster/run.sh
```

1M is an explicit statistics example, not a validated precision target. Review
the configs' 3600 s timeout before increasing counts; a changed config needs a
new campaign. Each invocation is sequential/single-worker; independent gamma
and neutron campaigns may use separate allocations and distinct output names.

| Wrapper variable | Required/default |
|---|---|
| `CYGNO_SRC`, `CYGNO_BUILD`, `CYGNO_RUNS`, `CYGNO_CAMPAIGN`, `CYGNO_PRIMARIES` | Required; repository root, shared build, campaign parent, unique name, count per campaign |
| `CYGNO_CONFIG` | Defaults to `external/config/hall-c-gamma-2026-proxy.json` |
| `CYGNO_OUTPUT_MODE` | Default compact |
| `CYGNO_PYTHON` | Default python3, version ≥3.10 |
| `G4LAB` | If set, wrapper sources `$G4LAB/activate.sh` again; only use for that actual private workspace |

Additional arguments pass to the runner, e.g. `--retry-failed`, `--seed N` or
`--shield none`. A shield/seed/count/output-mode change needs a separately named
campaign. There is no internal assay matrix, mass normalization or four-case
internal-decay preflight. Required external gates are geometry/GPS checks,
gamma **and neutron** transport smoke, accounting, raw/compact parity and physical
input review on the target machine. An internal U/Th preflight cannot certify
HP neutron capture/recoil transport; the local macOS Cu-capture failure is open.
See [validation](VALIDATION.md).

## Provenance, attempts and transfer

A campaign contains `campaign.json`, exact `config.json`, common `geometry.json`,
constructed `quantities.tsv` (diagnostic only), source snapshot, environment probes
and `attempt-NNNN/`. Each attempt retains the exact macro, command receipt, log,
ROOT product and SHA256 inventory. Identity includes compiled-source/geometry
hashes, source radius, shielding, spectrum, physics/data paths and full dataset
content hashes. Requested counts never substitute for successful actual accounting.

Output must be outside the checkout. A lock rejects concurrent writers. Repeat
an identical command to verify/reuse complete output. After failure/interruption,
`--retry-failed` makes a new immutable attempt. Changed source/config/build/data
requires a new campaign. Failed attempts cannot be analyzed as complete; retain
logs even when a ROOT file exists.

Transfer the entire campaign, including source and attempt manifests. External
analysis reads an **unpacked directory**, not the internal archive schema.
The following uses Linux checksum tools and the gamma production name from the
entry guide; use the corresponding neutron name for its separate transfer:

```bash
# Directory: campaign parent on the Linux simulation machine.
cd "$CYGNO_RUNS"
tar -czf external-gamma-production-NEW.tar.gz external-gamma-production-NEW
sha256sum external-gamma-production-NEW.tar.gz > external-gamma-production-NEW.tar.gz.sha256
```

Copy both files through your existing transfer method. At the destination:

```bash
# Directory: transfer destination on the Linux analysis worker; set its CYGNO_RUNS first.
cd "$CYGNO_RUNS"
sha256sum -c external-gamma-production-NEW.tar.gz.sha256
# Continue only after checksum verification succeeds and if the destination is absent.
tar -xzf external-gamma-production-NEW.tar.gz
```

On macOS, use `shasum -a 256` to create a checksum and `shasum -a 256 -c` to
verify it. An ordinary archive includes the complete campaign; do not copy only
the ROOT file or discard source/attempt metadata.

## Analysis on a separate worker

Set `CYGNO_SRC` to that worker's checkout and `CYGNO_RUNS` to the transferred
campaign parent. CNAF's known base is `/cnaf/cygno-sim/Users/goppedis/SolarNu`;
`external/gamma-cu20` under that base is a configurable example input, not an
assertion of an existing validated production. Use the complete
[native ROOT recipe](../analysis/common_c++/README.md#compile) or
[Python recipe](../README.md#python-analysis).

Native ROOT reads compact data in compact/both campaigns and checks structure
and identity. Python accepts raw/compact/both, performs the full SHA256/source
and track-relationship audit, and checks parity for both. Neither analysis
requires Geant4/datasets; ROOT compilation is separate from the detector build.
CNAF ROOT 6.30.02 needs HS3 plus JSONInterface; tested ROOT 6.40.04 supplies JSON
through HS3 alone. See [output semantics](OUTPUT.md) before interpreting rates.
