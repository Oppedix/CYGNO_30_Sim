# Two-stage Samuele background workflow

## Scientific identity

The canonical study is `legacy-25x3 / code-compatible / historical` with
`QGSP_BIC_EMZ + G4RadioactiveDecayPhysics`. `config/study/samuele.json` retains
10^7 primaries/contribution; `--primaries` overrides only statistics. Both supported
layouts still use the same common geometry. No physics, geometry, sampling,
activities, isotope controls, chain boundaries or normalization constants were
changed by the two-stage refactor.

`config/study/thesis-table7.1.json` and `study/source_matrix.py` remain authoritative:
26 contributions, nine explicit source components, seven final categories.
`GEMs = GEMsOuter + GEMsCore`; `Field Cage = RingStrips + RingSupports`. Each source
is scaled before category summation. Acrylic assay upper limits remain used as
values; omitted table entries do not become zero-rate jobs.

## Stage A: simulation only

`study/simulate.py` imports only standard-library modules. Shared macros, seeds,
process execution and provenance live in `study/runtime.py`. The existing seed
hash is unchanged: SHA256 of `seed:contribution`, two positive integers modulo
2,000,000,000. Layout is deliberately absent for historical A/B comparisons.

Two executables are needed: `rdecay01` and `geometry_quantities`. The latter moved
from validation into `app/`, links the same simulation geometry classes, and
exports actual component masses/piece counts plus gas centers/dimensions. It is
built with `BUILD_TESTING=OFF`, without CERN ROOT discovery. Python never retypes
detector dimensions or reconstructs module positions from guesses.

Every job macro uses:

```text
/process/had/rdm/thresholdForVeryLongDecayTime 1.0e+60 year
```

This is a run compatibility setting, not exposure time or a lifetime/branching
change. Annual normalization remains 31,536,000 seconds. Effective post-macro
`CYGNO_ENV` and worker `CYGNO_RUN` observations must match (~3.1536e67 seconds).

`study/preflight.py` remains ROOT-free: U238 default must show the one-year
threshold and no transported Th234; U238 enabled must transport Th234; full Th232
and Bi212 must transport Bi212 and terminal Pb208 without PART122. All four must
pass before **any new campaign job**, regardless of event count or mode label.
Accounting is checked too. Preflight proves environment behavior on a small
sample, not branching fractions or complete production statistics.

The operator reports all four pass on Ubuntu 22.04.5, x86_64, GCC 11.4.0, private
Geant4 11.3.1 with `GEANT4_BUILD_MULTITHREADED=OFF`, PhotonEvaporation6.1,
RadioactiveDecay6.1.2 and G4ENSDFSTATE3.0. PART122 remains reproducible on tested
macOS/arm64 installations, including geometry-free and stock Geant4 11.3.1
rdecay01/serial builds. No G4ParticleTable or excited-state workaround is used.
This is **environment-specific empirical validation**, not a universal release fix.

## Completion and recovery

Each contribution has `jobs/ID/manifest.json` pointing to an immutable
`attempt-NNNN/` with `run.mac`, `simulation.log`, `simulation.command.json`, raw
ROOT output and its own manifest. A serial job writes `outfiles_V2/raw.root`; a
single MT worker can write `raw_t0.root`. Exactly one nonempty raw file is required.

After successful ROOT write/close, C++ emits one `CYGNO_ACCOUNTING` JSON object
with the same five integer counters as `RunAccounting`. Requested, generated and
processed must equal the chosen count; run ID and aborted count must be zero.
Exit status must be zero, fatal/command/abort errors and PART122 absent, and all
environment/threshold checks must pass. Raw contents are structurally checked
later by uproot; Stage A completeness is explicitly **raw accounting completeness**.
`Hits`, `RunMetadata`, and `RunAccounting` schemas are unchanged.

An advisory lock prevents concurrent simulation/packaging. Repeat the same command
to verify and reuse completed jobs, and restart interrupted/running jobs in new
attempts. `--retry-failed` starts new attempts for failed jobs. Corrupt complete
jobs are rejected, never overwritten. `--only` is a scheduling subset, not a
campaign identity change; later invocations can fill the remaining matrix.
Any partial coverage exits 2. All four preflight failures block new work and
require a new campaign after the environment has been corrected.

Campaign identity includes Git revision/branch/dirty status and file hashes,
compiled source and geometry hashes, both executable checksums, CMake cache,
Python/platform/execution environment, effective Geant4 version/physics/dataset
paths, dataset directory versions/content hashes, config and full matrix. Jobs
retain seeds, count, exact macro/hash, command receipt, accounting and artifact
hashes. The actual source tree snapshot is included for dirty-checkout reproduction.
Moving a campaign for offline analysis does not require the original absolute
build/data paths to exist. Changing source/build/data/config cannot resume it.

## Packaging and transfer

`--archive` or `python3 -m study.archive --input CAMPAIGN` requires 26/26 valid
complete jobs. Archives include failed earlier attempts as well as successful
ones, probe/preflight logs, all snapshots and provenance. `SHA256SUMS.json` covers
every packaged regular file except itself; the external `.tar.gz.sha256` checks
the entire archive. The archive is verified before publication. Existing archives
are never overwritten; a later campaign inventory gets a distinct timestamp name.
No unpacked files are deleted. No partial-archive mode is currently implemented.

Extraction rejects traversal/absolute paths, links, devices and duplicate members
before writing files; all extracted checksums and manifests are then checked.
`analyze.py` extracts to a temporary directory, removed on completion. Set `TMPDIR`
to a filesystem with room for the uncompressed campaign, or analyze an unpacked
campaign directly. Packaging verifies compressed content as a stream without
creating another uncompressed copy. SHA256 detects corruption, not source authenticity.

## Stage B: offline analysis

`study/analyze.py` accepts a directory or archive and writes a **new** output
directory. Install `study/requirements-analysis.txt`; no Geant4/CERN ROOT needed.
`study/raw_io.py` validates TTree schemas, single metadata/accounting rows, identity,
actual counts, finite numerical hits, valid gas copies and ordered valid event IDs.
Campaign/job/macro/receipt/raw checksums and accounting must agree. Mixed campaigns
are rejected before results are published.

`study/processing.py` ports `analysis/ProcessEvents.cc` literally. Only e-, e+ and
alpha rows enter groups. Event boundaries flush even when the next row is ignored;
EOF flushes the last group. Matching creator process/nucleus before ionization
updates the inherited particle label; ionization otherwise sets `ionizationSeen`;
other changes flush. The initial row does **not** set that flag. Energies aggregate
per gas volume in first-encounter order; each volume keeps its first x/y/z. Chunk
boundaries do nothing to group state. Memory is bounded by one uproot chunk,
one group (at most 150 volumes) and fixed-size histograms.

`study/spectra.py` ports the main `PlotNormalizedSpectra` path: electron/positron
labeled groups only, sum each volume's MeV energy times 1000, and use only the first
volume/position for the inclusive 20 mm cut (`abs(position-center) <= size/2-20`).
Geometry metadata comes from the compiled exporter. Histogram bins remain 900 over
[0,2000) keV with explicit flows. Floating-point edge placement follows the
[ROOT TAxis implementation](https://root.cern.ch/doc/master/TAxis_8cxx_source.html)
verified against ROOT 6.40.04; older ROOT releases may differ at rounded edges.
Exact energy windows are counted before binning: all finite energies, E>10,
10<E<=400, E<0, 0<=E<2000 and E>=2000, each uncut/cut.

Normalization preserves multiplication order:
`activity * quantity * 60 * 60 * 24 * 365 / actual_generated_primaries`.
Quantity is constructed kg for Bq/kg or resistor placement count for Bq/piece.
The denominator is verified ROOT accounting, never a requested-only substitution.
Variance is selected group count times scale squared, summed across contributions.
It is a group-Poisson convention, not primary-level or assay/model uncertainty.

`study/reporting.py` shares table reference transcriptions with the legacy renderer
and draws matplotlib PNG/PDF spectra in counts/keV/year. Outputs include spectra,
CSV/JSON/text tables, figures, copied campaign identity, dependency versions, raw
checksums, analysis source provenance and explicit coverage/scientific validity.
Analysis can also run from the archived `source/` tree: without Git metadata it
records hashes of the Python implementation and dependency specification instead
of inventing a revision. Simulation retains the full Git provenance requirement.
`--allow-partial` writes labeled partial sums with missing categories left missing
and exits 2. Default analysis rejects incomplete campaigns.

## Reference implementation and scientific limits

The C++ analysis stays in `analysis/` behind `CYGNO_BUILD_ANALYSIS=ON`.
`study/runner.py`, `study/root_io.py` and `study/figures.py` retain the previous
combined PyROOT/C++ workflow for historical comparisons; they are not imported by
the new entry points. Old campaign schemas are not silently migrated/relabelled.

`tests/test_parity.py` optionally executes the real C++ processor/plotter on uproot
fixtures for both layouts and all 26 normalization rows, comparing group labels,
vectors, exact-window counts/rates, every bin/flow, variances and category sums.
It includes all histogram edges and adjacent floating-point values. See README
for its command. Tests require no large Monte Carlo campaign.

Inherited overlaps, historical nonuniform sampling, chain assumptions, grouping,
first-position cuts and source/revision uncertainties remain documented in
[KNOWN_ISSUES.md](KNOWN_ISSUES.md). `Nucleus` remains the last tracked ion, not
proven ancestry. Published Tables 7.2/7.3 are comparison data only. Neither 4/4
preflight nor software parity proves absolute physical correctness or agreement
with Samuele's production numbers.
