# CNAF: run the existing campaigns through HTCondor

One vanilla job owns one complete campaign. `run.sh` activates the worker's
environment, checks shared paths/write access, then `exec`s the unchanged Python
runner. There is no splitting, merging, packaging or additional campaign manager.
All four campaigns use `cygno-copper-cathode-v4`, `cygno-11x7-v1` and compact ROOT.

| Submit file | Primaries | Output directory under `/cnaf/cygno-sim/Users/goppedis/SolarNu` |
|---|---|---|
| `internal-no-gas.sub` | 1,000,000 × 23 contributions; `--gas-bkg no` | `internal-no-gas-v4-11x7-1M` |
| `internal-with-gas.sub` | 1,000,000 × 25 contributions; `--gas-bkg yes` | `internal-with-gas-v4-11x7-1M` |
| `external-gamma.sub` | 1,000,000; existing Hall C gamma proxy, copper20 | `external-gamma-v4-11x7-1M` |
| `external-neutron.sub` | 1,000,000; existing Hall C neutron proxy, copper20 | `external-neutron-v4-11x7-1M` |

## 1. Establish the CNAF paths and software

Start in a **Bash terminal in Jupyter**. The historical `CYGNO-MC` notes establish
neither this repository's worker environment nor native scheduler access. Their
Python 3.9.12 is too old: this repository needs **Python ≥3.10**, Git, CMake ≥3.16,
a C++17 compiler and Geant4 11 with matching datasets. No CERN ROOT, PyROOT or
Python analysis packages are needed for simulation. Use a site-qualified Linux
Geant4 installation; the full internal radioactive-decay gate must pass there.
The historical Geant4 11.2 setup is not evidence that this application's gate or
all its required datasets will work.

Ask CNAF for the approved native submit host/schedd, worker software activation,
Python path, compatible OS/container, credentials, accounting requirements and
maximum job wall time. Put the supplied Condor settings in `site.conf`.
An activation script must work in noninteractive Bash, set the executable/library
search paths and matching Geant4 datasets, and fail if activation fails. It may
source the site's setup and modules; a Jupyter-only `cygno_setup` alias is not
available in the job. Do not inherit Jupyter's entire environment.

This setup deliberately uses **shared files**, with `should_transfer_files = NO`.
The checkout (including `.git` and relative symlinks), build, activation script,
Python and external config files must be reachable at their configured absolute
paths on workers. Shared libraries and datasets must also be readable there.
The runner checks effective dataset paths and hashes their contents, including
G4NDL for neutrons. An environment probe alone can take time for these hashes.

The requested `/cnaf/...` output path has **not been verified by a real CNAF batch
execution as part of this integration**. Jupyter historically used
`/jupyter-workspace/cnaf-storage/...`; that alias does not establish a `/cnaf`
mount on workers. Confirm the mapping with CNAF. If Jupyter cannot see the same
absolute paths, use its terminal to connect to the approved submit/build host
with those mounts before continuing. Do not simply point jobs at a Jupyter-local
`/jupyter-workspace/private` checkout. This shared-file setup needs mounts/OS
selection supplied by CNAF; it does not deploy software or mount storage.

## 2. Clone/update and compile once

These commands use the defaults from `site.conf`. Change the paths there if CNAF
requires another shared source/build location, and use those same paths here.

```bash
bash
export CYGNO_CNAF=/cnaf/cygno-sim/Users/goppedis/SolarNu
export CYGNO_SRC="$CYGNO_CNAF/CYGNO_30_Sim"
export CYGNO_BUILD="$CYGNO_CNAF/build/cygno-common"
cd "$CYGNO_CNAF"             # stop here if this mount is unavailable
test -w . && test -x .
git clone --branch main https://github.com/Oppedix/CYGNO_30_Sim.git "$CYGNO_SRC"
```

For an **existing** checkout, use this instead of cloning; save local work before
updating. Never update source or rebuild while campaigns are running or awaiting
an identical retry.

```bash
cd "$CYGNO_SRC"
git status --short
git switch main
git pull --ff-only origin main
```

Activate the actual CNAF software (replace the three explicit site placeholders):

```bash
export CYGNO_G4_SETUP=/EDIT/absolute/path/to/cnaf-geant4-activation.sh
export CYGNO_PYTHON=/EDIT/absolute/path/to/python3
source "$CYGNO_G4_SETUP"
export Geant4_DIR=/EDIT/absolute/path/to/geant4/lib/cmake/Geant4
"$CYGNO_PYTHON" -c 'import sys; assert sys.version_info >= (3,10); print(sys.version)'
geant4-config --version
cmake -S "$CYGNO_SRC" -B "$CYGNO_BUILD" -DCMAKE_BUILD_TYPE=Release \
  -DWITH_GEANT4_UIVIS=OFF -DCYGNO_BUILD_ANALYSIS=OFF -DBUILD_TESTING=OFF \
  -DGeant4_DIR="$Geant4_DIR"
cmake --build "$CYGNO_BUILD" --target rdecay01 geometry_quantities --parallel 2
```

Compile on the site-approved Linux build host/container compatible with execution
nodes. Do not reuse a macOS binary. The worker smoke test below is the check for
binary/library/dataset accessibility and compatibility, not a successful Jupyter
build alone.

## 3. Edit one settings file; set the external timeout before starting

Edit **`condor/site.conf`**. It uses HTCondor syntax, not shell syntax; do not
`source` it. Set `source_dir`, `build_dir`, `output_parent`, `log_dir`, `g4_setup`
and `python` to absolute paths. Set `internal_jobs` and memory as described below.
Add only the actual CNAF requirements/accounting/container/wall-time settings.
Paths containing literal quotes are not supported by this simple template.
Finish these edits before starting campaigns: `site.conf` itself is included in
the runners' source provenance. Keep it unchanged for subsequent retries; use
command-line resource overrides instead of editing it after a campaign starts.

Both supplied external JSON configs have **`timeout_seconds: 3600`**, a per-attempt
transport timeout, not the queue wall time. For million-primary runs, make
timeout-only copies **outside the checkout**, before the first smoke/production
submission. This example uses seven days per external attempt; measure smoke
throughput and choose an appropriate value and compatible site wall time.

```bash
"$CYGNO_PYTHON" - "$CYGNO_SRC" "$CYGNO_CNAF/condor-config" <<'PY'
import json, sys
from pathlib import Path
src, dest = map(Path, sys.argv[1:])
dest.mkdir(parents=True, exist_ok=True)
for name in ('hall-c-gamma-2026-proxy.json', 'hall-c-neutron-wulandari-proxy.json'):
    cfg = json.loads((src/'external/config'/name).read_text())
    cfg['timeout_seconds'] = 604800
    with (dest/name).open('x') as f:  # refuses to overwrite an existing config
        json.dump(cfg, f, indent=2)
        f.write('\n')
PY
```

Then set these two lines in `site.conf`:

```text
gamma_config = $(output_parent)/condor-config/hall-c-gamma-2026-proxy.json
neutron_config = $(output_parent)/condor-config/hall-c-neutron-wulandari-proxy.json
```

Keep their Hall C spectra, fluxes, shielding, layout and model unchanged. Internal
`cygno-11x7-v4.json` already has a 604800-second timeout **per contribution**.
With `--jobs 1`, a whole internal campaign can take much longer than one
contribution: request a suitable site wall-time class. Queue limits can still
interrupt a campaign before the runner timeout. No wall-time class is invented
here. Timeout changes are part of identity; do not change configs during a retry.
Choose a new output tag/directory when changing an existing campaign's identity.

Create the configured log directory **outside the checkout**, visible to the
submit host, so logs never enter the runners' source snapshots:

```bash
mkdir -p "$CYGNO_CNAF/condor-logs"
cd "$CYGNO_SRC/condor"
command -v condor_submit
condor_version
```

## 4. Check submission syntax and run small campaigns on workers

All `condor_*` commands here are **native HTCondor**. If unavailable or unable to
contact a schedd, obtain CNAF's native submit access first. Historical
`cygno_htc -m 2` / `cygno_htc -r JOBID 2` are site-specific monitoring/removal
examples from another repository; they are not substitutes for these submissions.
Do not feed these files to the old CYGNO-MC submission wrapper without CNAF
confirming that it can execute this shell entry point and honor these resources.

```bash
cd "$CYGNO_SRC/condor"
bash -n run.sh
# Optional local dispatch self-check: no Geant4 or scheduler needed.
"$CYGNO_PYTHON" ../validation/test_condor.py
for file in internal-no-gas.sub internal-with-gas.sub external-gamma.sub external-neutron.sub; do
  condor_submit -dry-run "$CYGNO_CNAF/condor-logs/$file.ad" "$file"
done
# Inspect generated ClassAds: command, environment, CPU, memory and requirements.
cat "$CYGNO_CNAF/condor-logs/internal-with-gas.sub.ad"

# Four separate SMALL campaigns, never the production directories.
# Keep this tag to repeat exactly the same smoke command later.
smoke_tag=smoke-$(date +%Y%m%d-%H%M%S)
for file in internal-no-gas.sub internal-with-gas.sub external-gamma.sub external-neutron.sub; do
  condor_submit "$file" primaries=2 tag="$smoke_tag" internal_jobs=1
done
```

Wait for all four to finish. The `.out` logs identify the worker, Git revision,
Python version, successful output-parent write probe and exact runner command.
The real runs verify source/build/library/dataset access; the internal runs retain
the full four-case decay preflight even at two primaries. The gas-enabled smoke
also actually runs C14 and **Rn222** contributions. Inspect its preflight and
per-contribution logs; a failed preflight or gas contribution must remain failed.
Do not disable the gate or accept a ROOT file alone as success. Use section 8
with `CYGNO_CHECK_TAG="$smoke_tag"` and `CYGNO_CHECK_PRIMARIES=2` to validate all
four smoke campaigns before submitting production. Smoke statistics do not
establish physical validity or a reliable full-run wall-time estimate.

## 5. Submit the four production campaigns

From `condor/`, with the configured defaults `primaries = 1000000`, `tag = 1M`:

```bash
condor_submit internal-no-gas.sub
condor_submit internal-with-gas.sub
condor_submit external-gamma.sub
condor_submit external-neutron.sub
```

Or submit all four with ordinary shell commands:

```bash
for file in internal-no-gas.sub internal-with-gas.sub external-gamma.sub external-neutron.sub; do
  condor_submit "$file" || break
done
```

Each command queues exactly one owner of its separate directory. Do not submit
another owner while that campaign is queued, running or held. The existing
runner lock is retained, but must not be used as scheduling. No `--archive` is
passed and no additional archives are created. All manifests, source/config
snapshots, probes, attempts and ROOT outputs keep their native structure.

## 6. CPUs and memory

`internal_jobs = 1` is the conservative default: each internal Condor job requests
one CPU and 5120 MiB. `internal_jobs = 13` runs the unchanged runner with
`--jobs 13`, requesting 13 CPUs and 54272 MiB (1 GiB runner allowance + 4 GiB per
simultaneous Geant4 process). External jobs always request one CPU and 5120 MiB.
The runner explicitly launches each Geant4 process with one worker. Four jobs at
the default can therefore use four CPUs in total; at 13, both internal campaigns
plus both external campaigns can use 28 CPUs.

Change `internal_jobs` in `site.conf`, or override it for an individual submission:

```bash
condor_submit internal-with-gas.sub internal_jobs=13
```

Do not override `request_cpus` independently of concurrency. Memory is a starting
budget, not a measurement; adjust `memory_per_process_mb` from observed peak
usage and CNAF limits before increasing concurrency. Disk/I/O and source/dataset
hashing overhead also grow. Changing only concurrency/resources on retry is
allowed by the existing runner; changing physics/config/source/build is not.
On retry, keep `site.conf` frozen and use, for example,
`condor_submit internal-with-gas.sub internal_jobs=13 memory_per_process_mb=6144`.

## 7. Queue, logs and retry

```bash
condor_q
condor_q -hold
condor_q -better-analyze JOBID       # replace JOBID with the returned cluster ID
condor_history JOBID -af ClusterId ProcId JobStatus ExitCode ExitBySignal MemoryUsage
ls -lt "$CYGNO_CNAF/condor-logs"
tail -f "$CYGNO_CNAF/condor-logs/internal-with-gas-1M.JOBID.0.out"
```

Check `.out` (runner progress), `.err` (runner errors), `.log` (Condor events and
exit/signal status), plus native `simulation.log` / `simulation.command.json`
inside campaign attempts and probes. Nonzero exits/signals are held by
`on_exit_hold`; absence from `condor_q` alone is not proof of success. Site
eviction/termination can still happen; the requested SIGINT and 60-second vacate
window allow the runner to retain interrupted attempts where site policy permits.

For an interrupted/failed campaign, first establish that no old owner is active.
For a held job, inspect the reason, fix environment/resource access **without
changing campaign identity**, and release that same owner:

```bash
condor_release JOBID
```

Alternatively remove the old job, wait until removal completes, then repeat the
same original `condor_submit` command (including any tag/count overrides):

```bash
condor_rm JOBID
condor_q JOBID                    # wait until removed; check its event log too
condor_submit internal-with-gas.sub
```

Every invocation includes the existing `--retry-failed`; internal also spells
out `--resume`. Completed contributions are checked/reused, interrupted/failed
ones get new numbered attempts. External retries rerun their single transport
in a new attempt, or verify/reuse a complete campaign. Never delete manifests,
locks or attempts to force success. Keep source (including Git revision/status),
build path/binaries, configs, datasets and relevant environment identical.
The internal identity includes Python/platform/environment, so heterogeneous
workers may reject a retry: constrain the pool to an equivalent worker/container
environment or return to the original environment. If identity really changes,
use a fresh tag, e.g. `tag=1M-v2`; earlier output is not overwritten or relabeled.
A failed radioactive-decay preflight cannot be repaired by `--retry-failed`:
qualify a working environment and start a new campaign/tag; the saved failed
gate must not be edited or bypassed.

## 8. Verify completion and locate ROOT files

After the queue jobs have stopped, run the repository's own validators from the
checkout with Python ≥3.10. They check manifests, preflight, receipts, generated
primary accounting, artifact checksums and saved provenance without running new
transport or requiring analysis packages. This snippet also checks the requested
model, layout, gas scenarios and statistics, and prints the selected ROOT paths:

```bash
cd "$CYGNO_SRC"
export CYGNO_CHECK_TAG=1M CYGNO_CHECK_PRIMARIES=1000000
# For smoke instead: export CYGNO_CHECK_TAG="$smoke_tag" CYGNO_CHECK_PRIMARIES=2
"$CYGNO_PYTHON" - "$CYGNO_CNAF" <<'PY'
import os, sys
from pathlib import Path
from study import runtime as rt
from study.campaign import validate_campaign
from external.study.simulate import check_campaign
base = Path(sys.argv[1])
tag = os.environ['CYGNO_CHECK_TAG']
n = int(os.environ['CYGNO_CHECK_PRIMARIES'])
for name, count, gas in [('internal-no-gas', 23, 'no'), ('internal-with-gas', 25, 'yes')]:
    out = base/f'{name}-v4-11x7-{tag}'
    jobs = validate_campaign(out)
    c = rt.read(out/'campaign.json')
    cfg = c['identity']['config']
    assert c['coverage'] == f'{count}/{count}' and len(jobs) == count
    assert cfg['model'] == 'cygno-copper-cathode-v4' and cfg['layout'] == 'cygno-11x7-v1'
    assert cfg['output_mode'] == 'compact' and cfg.get('gas_bkg', 'no') == gas
    assert cfg['primaries_per_job'] == n
    print(name, c['status'], c['coverage'])
    for job, root in jobs.values():
        print(root)
for particle in ('gamma', 'neutron'):
    out = base/f'external-{particle}-v4-11x7-{tag}'
    c, root = check_campaign(out)
    cfg = c['identity']['config']
    assert cfg['model'] == 'cygno-copper-cathode-v4' and cfg['layout'] == 'cygno-11x7-v1'
    assert cfg['output_mode'] == 'compact' and cfg['primaries'] == n
    assert cfg['particle'] == particle and cfg['hall'] == 'C' and cfg['shield'] == 'copper20'
    print('external-'+particle, c['status'], c['accounting'])
    print(root)
PY
```

Expect **23/23**, **25/25**, and both external campaigns **complete** with
RequestedEvents = GeneratedPrimaries = ProcessedEvents = 1000000 and AbortedEvents
= 0. For internal campaigns these counts apply to **each** contribution.
Validation failures exit nonzero; do not treat partial coverage as completion.

Internal selected ROOT files live at
`CAMPAIGN/jobs/CONTRIBUTION/attempt-NNNN/outfiles_V2/compact.root` (or
`compact_t0.root`); external files at
`CAMPAIGN/attempt-NNNN/outfiles_V2/compact.root` (or `compact_t0.root`). Use the
manifest-selected paths printed above; a recursive file search also finds old
failed attempts. ROOT structural/scientific analysis remains the separate
[internal](../internal/README.md) / [external](../external/README.md) workflow.

HTCondor syntax reference: [official condor_submit manual](https://htcondor.readthedocs.io/en/24.0/man-pages/condor_submit.html).
