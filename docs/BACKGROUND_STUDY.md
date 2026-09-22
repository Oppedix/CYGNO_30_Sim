# Samuele background reproduction workflow

## Scope and provenance

The supported scientific reference is `legacy-25x3` / `code-compatible` /
`historical`. The alternative `cygno-5x5x3-v1` shares internals and analysis.
No detector dimensions or source distributions were corrected to match the thesis.
The future 11x7 layout is not implemented. This repository reproduces the workflow
and analysis infrastructure using thesis Table 7.1; the tested Geant4 11.4.2/data
environment cannot yet produce the complete published U/Th background because of
`PART122`. These three origins must stay distinct:

| Origin | What it supplies |
|---|---|
| Thesis specification | Table 7.1 assays, equilibrium/split-chain assumptions, approximately 10^7 primaries per contribution, 20 mm cut, published comparison values |
| Samuele/current implementation | Code-compatible solids/materials/offsets, historical surface/depth source sampler, stopped ion recoil, process/nucleus grouping, first-position fiducial predicate |
| New infrastructure | Runtime layout identity, actual quantities/count validation, explicit RDM environment setting, manifests, isolated attempts, progress/resume, category and figure/table exports |

The [source matrix](../config/study/thesis-table7.1.json) has exactly 26
contributions. Explicit components: Cathodes, GEMsOuter, GEMsCore, RingSupports,
RingStrips, Resistors, Vessel, Lens and Sensors. Historical GEMs/Rings aliases are
not accepted. All 26 macros are generated from this matrix by `study/runner.py`;
there is no second hand-maintained set. `--list`/`--dry-run` prints their contents.
`--macros-dir NEW_DIRECTORY` exports them without requiring a build.

## Required radioactive-decay setting

Every study macro uses, after kernel initialization and before beamOn:

```text
/process/had/rdm/thresholdForVeryLongDecayTime 1.0e+60 year
```

This follows the [Geant4 application guide](https://geant4.web.cern.ch/documentation/pipelines/master/bfad_html/ForApplicationDevelopers/TrackingAndPhysics/physicsProcess.html#note-on-the-time-threshold-for-radioactive-decay-of-ions).
Geant4 >=11.2 changed the default to one year; see its
[release notes](https://geant4.web.cern.ch/download/release-notes/notes-v11.2.0.html).
The explicit setting allows long-lived parent/daughter decays in an analogue chain
study. It is a **run-environment compatibility setting**, not a detector correction,
exposure duration, lifetime modification or branch reweighting. The effective value
is approximately 3.1536e67 seconds. Annual normalization still uses 31,536,000 s.

The executable initializes before reading the user macro. Startup observations
alone therefore cannot verify a macro's threshold. `CYGNO_RUN` logs the actual
worker process value before transport; `CYGNO_ENV` records the post-macro value.
The runner checks both against configuration and stores the effective environment
in the campaign manifest. Failed runs retain the worker observation and full log.
No global C++ threshold is changed. Old manual/reference macros do not acquire this
setting automatically; use the generated study macros for long-lived parents.

## Preflight and incomplete chains

`python3 study/preflight.py --build "$BUILD" --output "$RUNS/preflight"` runs:

1. Two U-238 primaries at the environment default, stopping before ground-state Th-234 decay.
2. The same two with the explicit threshold, requiring transported Th-234 daughters.
3. Forty full-chain Th-232 primaries.
4. Forty direct Bi-212 full-chain primaries.

Every campaign runs this preflight once before jobs and retains its result/logs.
It is an environment test, not a measurement of branching fractions or convergence.
The standalone `external_decay_probe` target removes CYGNO geometry, sampler and
ROOT from the Bi test. See [known issues](KNOWN_ISSUES.md) for observed PART122.

The tested Geant4 11.4.2/data environment fails. The complete 26-job smoke also
exposes `PART122` in U chains: only five K-40 contributions pass and 21 remain
incomplete (see [validation evidence](FINALIZATION.md#validation-evidence)).
Production does not launch the affected full Th-232/Th-228 contributions under
that failed preflight; their attempt manifests say failed/incomplete. Smoke still exercises all 26 scheduled jobs, but even a tiny
Th attempt that happens to exit successfully cannot override the failed preflight.
Resistor upper Th stops before Th-228 and is assessed by its own execution; any
exception, including one before that boundary, fails the job. No isotope is omitted
from the matrix, and no partially written file is normalized.

A complete Figure 7.5/7.6 reproduction **requires a Geant4/data environment that
passes these preflights and all 26 contributions**. No replacement version has
been verified here. Do not claim an arbitrary older version is compatible. Install
an official matched version/data set separately, build afresh, run the same tests
and preflight, and start a new campaign (environment changes cannot resume old jobs).
Never edit nuclear data, suppress exceptions or invent branch factors to obtain a plot.

## Running and recovery

See the [README](../README.md) for copyable build, visualization, manual, smoke,
production, resume, retry and analysis commands. `samuele.json` defaults to
production, 10^7 primaries per contribution, one worker and sequential jobs.
`--mode smoke` selects two primaries; `--primaries N` overrides it (smoke cap 1000).
Counts are configurable up to Geant4's signed event-counter limit in production.
`timeout_seconds` is a per-process ceiling: canonical production allows seven days;
choose a suitable configuration before a campaign. Counts do not imply runtime.

Overall progress prints job number/total, percentage of scheduled jobs handled and
current contribution. During transport it forwards the last completed-event marker
(printed every 500 events); this is observational progress, not the denominator.
The end-of-run generated-primary record alone supplies normalization.

Ctrl-C terminates the child process group, saves an interrupted attempt and exits
130. Repeat the same command to retain completed jobs and start a new attempt for
the interrupted/running job. Failed jobs stay retained unless `--retry-failed` is
specified. Old attempt directories and valid raw/processed results are never
replaced. An OS advisory lock excludes concurrent runners on the same campaign.
Hard-killed running attempts are likewise retried into a new directory. Corrupted
completed artifacts are rejected even with `--retry-failed`; they are not silently
regenerated. Restore them from an archive or create a new campaign.

`--only` may name multiple exact contribution IDs and is not part of campaign
identity: a campaign may be filled incrementally. Each report labels its selected
coverage. To report all completed contributions, omit `--only`.
`--analysis-only` validates completed artifacts and reruns the existing normalized
plotter plus figure/table export without launching Geant4 or retrying transport.
A new report directory is created each time. Incomplete reports return exit 2.

## Manifest and immutable identity

`campaign.json` stores Git revision/branch and working-source hashes, exact effective
configuration, source matrix and fingerprint, executable/build fingerprints, ROOT
and Python versions, Geant4 version, effective threshold, resolved nuclear-data
version directories/content hashes, environment, quantities checksum, preflight
status and job status. Constructed quantities and per-job seeds/requested/generated
counts are also embedded directly in the campaign manifest. `quantities.tsv` records all constructed component masses
and placement counts. Each `jobs/ID/manifest.json` and immutable attempt manifest
records contribution, seeds, requested count, verified actual generated count (null
when unavailable), accounting, processed path, status/error, previous attempt and
artifact checksums. Command receipts and logs retain execution/exit information.

The same command only resumes identical source/build/configuration/data. Even a
new documentation commit changes strict source identity; archive the original
checkout with its campaign. Never edit manifests to force a resume. Analysis-only
also requires the matching checkout/build. Reports never relabel old simulations
with a new commit. Outputs default outside Git; paths under the repository fail.

## Raw to figures and tables

```text
matrix + study configuration → explicit macro → isotope/component sampler
→ Geant4 radioactive transport → worker Hits + identity + RunAccounting
→ SimpleProcessEvents → elabHits
→ PlotNormalizedSpectra (per-contribution activity × quantity × year / actual primaries)
→ seven separately summed detector categories → figure/table exports
```

See [ANALYSIS.md](ANALYSIS.md) for the exact grouping, cuts, units and schemas.
The runner reuses this analysis; `study/figures.py` only renders normalized data and
formats exact-window results. No histogram is fitted to thesis values.

Each report includes:

- `NormalizedHisto.root`: individual contributions, cut variants, category histograms,
  stacks, identity, normalization configuration and exact unbinned energy-window tree.
- `figure7.5.png/.pdf`: no-cut stack; `figure7.6.png/.pdf`: 20 mm cut stack.
  Display range 0–2000 keV, density counts/keV/year, actual bin-width division.
- `spectra.json`: exact contribution/category/total windows, MC variances and bin densities.
- `table7.2.csv`: all energies, E>10, 10<E<=400, with and without cut.
- `table7.3.csv`: seven component categories over all energies, with and without cut.
- `tables.json`, `tables.txt`: machine/human summaries, published comparison values,
  coverage and limitations; the same summary is printed in the terminal.

Missing contributions are excluded and visibly labeled incomplete; a missing
category is null/missing, never a zero estimate. Poisson group-count errors omit
correlations among groups from one primary, assay uncertainty, geometry uncertainty
and systematic source/model errors. Zero smoke counts do not establish upper limits.
Published Table 7.2's no-cut 10–400 value exceeds its >10 value; keep that discrepancy.
The exact unpublished Figure 7.5 production revision/input set remains unknown.
