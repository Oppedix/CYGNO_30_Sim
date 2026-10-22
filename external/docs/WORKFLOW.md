# External local/cluster operation

Use the single shared build documented in [README](../README.md). The runner is
Python standard-library-only and invokes Geant4 with one worker in an isolated
attempt directory. No CERN ROOT is needed on simulation nodes.

## Private cluster example

```bash
export G4LAB=/private/SolarNu/MC30/geant4-private
source "$G4LAB/activate.sh"
export CYGNO_SRC="$G4LAB/projects/CYGNO_30_Sim"
export CYGNO_BUILD="$G4LAB/build/cygno-common-11.3.1-linux"
export CYGNO_RUNS="$G4LAB/runs/external"
export CYGNO_CAMPAIGN=gamma-cu20-smoke-NEW
export CYGNO_PRIMARIES=1000
export CYGNO_CONFIG="$CYGNO_SRC/external/config/hall-c-gamma-2026-proxy.json"
cd "$CYGNO_SRC"
bash external/cluster/run.sh
# Alternatively, on a site using PBS, with a NEW campaign name:
qsub -V -l nodes=1:ppn=1,walltime=02:00:00 external/cluster/run.sh
```

For the neutron job choose `hall-c-neutron-wulandari-proxy.json` and another
campaign name. `CYGNO_OUTPUT_MODE` defaults to compact; `CYGNO_PYTHON` selects a
Python executable. The wrapper sources `$G4LAB/activate.sh` when G4LAB is set;
otherwise use the site's preconfigured Geant4 environment. The same commands
work locally after setting local paths. The `qsub` example is not a claim that
all CNAF queues use PBS; run the wrapper under the site's actual allocation
system, exporting these variables and requesting one CPU per invocation.
No scheduler submission or cluster production was performed during implementation.

Use `--shield none` for a separately named control. The sphere radius and incoming
flux are the same as in the Cu20 run. `--output-mode both` is a parity diagnostic;
it increases storage. `--primaries` overrides the config and is part of scientific
identity. `--seed` permits independent replicates in separate campaign directories.
There is intentionally no internal assay matrix, no mass-based normalization,
and no four-case *internal-decay* preflight on the external runner. The required
external gates are geometry/GPS checks, gamma **and neutron** transport smoke,
accounting, compact/raw parity, and physical input review on the target machine.

## Provenance, attempts and transfer

A campaign contains `campaign.json`, exact `config.json`, common `geometry.json`,
constructed `quantities.tsv` (diagnostic only), source snapshot, environment probes
and `attempt-NNNN/`. Each attempt retains its exact macro, command receipt, log,
ROOT product and SHA256 file inventory. Identity includes compiled source and
geometry hashes, source radius, shielding, spectrum, effective physics/data
paths and full dataset content hashes. No requested count substitutes for
successful generated/processed accounting.

The output must be outside the checkout. A lock rejects concurrent writers.
A repeated identical command checks and reuses complete output. After an error
or interruption, `--retry-failed` creates a fresh attempt without overwriting the
failed file. Changed code/config/build/datasets need a **new directory**. Failed
attempts are never analysable as complete campaigns. Do not discard logs merely
because a ROOT file exists.

Transfer the entire campaign with an ordinary archive or preserving directory
copy, including source and attempt manifests. External analysis currently reads
an **unpacked directory**; it does not use the internal source-matrix archive
schema. For example, from the campaign's parent:

```bash
tar -czf gamma-cu20.tar.gz gamma-cu20
sha256sum gamma-cu20.tar.gz > gamma-cu20.tar.gz.sha256
# After transfer, verify checksum and unpack before analysis.
```

## Native ROOT on an analysis node

An example input location is
`/cnaf/cygno-sim/Users/goppedis/SolarNu/external/gamma-cu20`.
Compile `external/analysis/common_c++/AnalyzeExternal.cpp` using that node's
`root-config`, as in the README; ROOT 6.30 needs both HS3 and JSONInterface,
while the tested ROOT 6.40.04 installation supplies JSON through HS3.
Run the resulting executable with the unpacked campaign and a new output directory.
The ROOT analyzer does not need Geant4, Python or the cluster's simulation datasets.
It reads the compact representation in compact/both campaigns.
It performs fast structural/identity checks; Python performs the full SHA256 audit
and track relationships, and accepts raw/compact/both.

Before a large campaign, run the tests in [VALIDATION](VALIDATION.md) and a
small smoke on the actual Linux environment. The local macOS neutron Cu capture
failure is open. A validated internal U/Th preflight does not certify external
HP capture/recoil transport; qualify both explicitly.
