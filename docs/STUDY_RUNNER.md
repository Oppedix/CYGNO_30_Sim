# Resumable background-study smoke runner

Phase 4 adds `study/runner.py` around the existing simulation, processor,
constructed-quantity exporter and **main** normalized plotter. It implements no
new detector, source sampler, physics list or event grouping. Study A/B configuration
files differ only in layout; their source matrix, count, seed policy, timeout,
code-compatible internals and historical source policy are identical. The future
thesis model is rejected until separately implemented.

## Running a smoke study

Source the installed Geant4 environment and build all existing targets, including
analysis and validation. Use the Python installation that can import ROOT. From
the repository root, the planned Phase 5 invocation is:

```sh
source ../../software/geant4-11.4.2/bin/geant4.sh
cmake --build ../../build/cygno-study --parallel 6
/opt/homebrew/bin/python3 study/runner.py \
  --config config/study/smoke-A.json --build ../../build/cygno-study \
  --output ../../validation-runs/study-A-smoke
```

The supplied A/B configurations request **two primaries per contribution**. The
runner defaults to all 26 Table 7.1 contributions. Each gets a fresh process,
isolated working directory, one worker, a generated macro and two deterministic
Ranecu seeds. Seeds depend on the common base seed and contribution ID, never
layout, so corresponding A/B jobs retain the same pair. Every macro explicitly
sets full-chain mode and both stop controls via the Phase 3 helper. It changes no
lifetime threshold, branching probability, isotope list or nuclear data.

Use `--config config/study/smoke-B.json` and a **different output directory** for
Phase 6. Do not launch B before A has been examined and documented. Consult
[STUDY_PROGRESS.md](STUDY_PROGRESS.md) for the actual phase gate; these examples
are not evidence that A/B have been run.

For a deliberately partial diagnostic, `--only GEMsCore_K40 Resistors_K40` selects
explicit IDs. Reports record the selected completed coverage out of 26; previously
completed unselected jobs are preserved but excluded from that report. A subset
is never reported as a complete matrix. Only `mode: smoke` is accepted, with
1–1000 primaries per job and 1–3600 seconds per child process. These are protective
smoke bounds, not a production interface. There is no production override.

## Completion, failure and resume

Repeat the identical command to resume. `--retry-failed` permits new attempts for
failed or interrupted jobs; it never overwrites an old attempt. A process failure,
timeout, command error, missing/malformed ROOT structure, mismatched identity,
missing end-of-run accounting, wrong counts or an aborted event prevents completion.
The default retains failed/interrupted jobs until explicitly retried, while
continuing other selected jobs. A hard interruption can leave `running` state;
treat it as incomplete and retry into a new attempt directory.

A completed job requires a zero process exit, exactly one raw worker file, matching
metadata, one accounting record with requested = generated = processed and zero
aborted events, successful processing and valid processed data. `RunAccounting`
counts primary particles created by the gun and completed/aborted events; it does
not count gas hits. Zero gas-hit rows can therefore be valid software output.
When a process aborts before verifiable accounting is available, the manifest
records `generated_primaries: null`, not the requested count or a hit-derived guess.

On reuse, the runner checks the campaign identity, every saved job artifact's
SHA-256, raw accounting and processed structure again. Changes to source revision
or working files, build executables, configuration, matrix, effective environment,
dataset contents or constructed quantities reject reuse. Corrupted completed jobs
are marked invalid in the report; they are never silently rerun, even with
`--retry-failed`. Investigate and use a new output directory. Valid sibling jobs
and all failed artifacts remain untouched.

A filesystem lock prevents two runners from writing the same campaign. The OS
releases the lock on process death; the lock file itself need not be deleted.
Outputs must live **outside the source repository**, avoiding accidental reference
or source writes. Manifests are replaced atomically. Commands run without a shell;
timeouts terminate the direct child and preserve its output log/command receipt.

Exit codes: 0 means every **selected** job and its diagnostic analysis completed;
2 means job or analysis failure/incompleteness; 1 means setup/provenance rejection.
**None of these codes certifies decay-chain completeness or scientific rates.**
All manifests/reports retain `scientific_validity: unvalidated` or
`chain_validity: unvalidated`. In particular, the installed one-year threshold and
Bi-212/Pb-208 failure are unresolved. Synthetic fixtures verify scheduling and
arithmetic, not radioactive transport. A completed 26/26 pipeline remains a smoke
study with unvalidated physics, never production ready by implication.

## Preserved evidence

- `campaign.json`: source revision/branch/status and individual source-file
  fingerprints (excluding protected reference directories), canonical configuration
  and full matrix, binary checksums, build-cache fingerprint, effective physics/data
  environment, Python/ROOT/platform versions, dataset directory versions/content
  fingerprints and scientific limitations.
- `config.json`, `matrix.json`, `quantities.tsv`: explicit study inputs and actual
  nine-component quantities, including 750 resistor pieces and layout-specific vessel
  mass. The campaign verifies the quantity file checksum on every resume.
- `probes/`: fresh initialization-only environment probes and initial quantity export
  with exact command receipts and logs. Failed probes are retained.
- `jobs/ID/manifest.json`: latest attempt state, request/counts, recorded seeds,
  artifact fingerprints and processing result; `attempt-NNNN/` retains each macro,
  log, command receipt, raw ROOT file, processed ROOT file and attempt manifest.
- `reports/report-TIMESTAMP/`: coverage/status summary, exact normalization input,
  plotting command/log, `NormalizedHisto.root` and `spectra.json` diagnostic exports.
  New invocations create new reports; `latest-report.json` points to the latest one.

The application prints `CYGNO_ENV` records after initialization. The decay-time
threshold is read from the **instantiated radioactive-decay process**, not the
hadronic configuration's unset sentinel. Data paths are resolved by the linked
Geant4 via `G4FindDataDir`; the runner hashes all files in those 12 directories.
The effective environment is checked again against every simulation's startup log.
The macro is entirely runner-generated and contains no environment/threshold edits.
This is provenance capture, not the later nuclear-data/branching preflight.

CMake embeds a hash of the active compiled source inputs. The simulation reports
it, processed/histogram outputs record `CygnoBuildSource`, and the quantity exporter
records `# compiled-source-hash:`. The runner rejects stale tools even when the
geometry hash has not changed. Geometry/model identity remains a separate contract;
old analysis inputs remain readable under the existing Phase 2 compatibility rules.
A commit or any source/documentation edit conservatively changes campaign identity;
start a new campaign after committing rather than relabeling development fixtures.
No files under `local_refs/` or `local_context/` are read by runner provenance capture.

## Exact energy windows and display units

The main plotter adds `ExactEnergyWindows`, counted from the same electron/positron
group energy sums and first-position 20 mm fiducial predicate **before binning**.
The other two normalized plotters retain their existing behavior and are not used
by this runner. Each contribution has uncut and fiducial counts for:

| Key | Definition |
|---|---|
| `all` | All finite energies, including underflow and overflow |
| `gt10` | E > 10 keV, with no upper cap |
| `gt10_le400` | 10 < E <= 400 keV |
| `underflow` | E < 0 keV |
| `in_range` | 0 <= E < 2000 keV |
| `overflow` | E >= 2000 keV |

Thus 10 keV is excluded from both threshold windows, 400 keV is included in the
restricted window, and 2000 keV belongs to overflow. The JSON export records these
bounds explicitly. No threshold is approximated by a straddling histogram bin.
`all = underflow + in_range + overflow`; the three are not double-counted in totals.
The old histogram `Integral()` values still exclude flows; use the exact windows
for comparisons and identify the selected convention.

Rates use actual verified generated counts with the unchanged
`activity * quantity * 60 * 60 * 24 * 365 / generated_primaries` convention. Individual
rates are summed into the seven published categories and a selected-job total.
The reported variance is count × scale², summed across independent jobs. It treats
processed groups as Poisson counts; it does not model within-primary correlations,
assay errors, geometry uncertainty or scientific validity.

ROOT spectra retain counts/bin/year. `spectra.json` additionally divides each
regular bin and its statistical error by that bin's width for counts/keV/year;
underflow/overflow remain separate counts/year, never a density. Position plots,
including their known world-Z overflow, are unchanged. Published discrepancies
and normalization provenance remain in [STUDY_SOURCES.md](STUDY_SOURCES.md).
