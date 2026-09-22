# Background-study progress

Updated: 2026-09-22. Study status: IN PROGRESS. Current phase: **Phase 5 COMPLETE (smoke diagnostic)**.
First incomplete phase: **Phase 6**, Smoke B and A/B comparison. Study A completed
26/26 software jobs, but primary decay transport failed under the one-year threshold.
Its empty spectra are not physical background predictions. Study B has not started.

## Recovery contract

- Baseline: `74cc26f` (`code refactoring`). Branch: `study/background-reproduction`.
- At resume, inspect `git status`, branch, last ten commits, unstaged/staged diffs,
  then read this file and resume the first incomplete phase. Never reset the branch.
- Complete and validate each phase separately, update this file before committing,
  and make one logical local commit per completed phase (latest user instruction).
  A commit cannot contain its own final hash: identify the current phase commit
  by its exact subject below, and record its resolved hash in the next phase's
  progress update. Never automatically push or merge.
- Current authorization supersedes the earlier Phase-0-only stop: continue the
  first incomplete phase from this record, without repeating completed phases.
- `local_refs/` is read-only research material: never add, edit, move, commit or
  push it. The originally stated `local_context/` is absent and remains protected.
- Preserve the completed repository refactor; no broad architectural cleanup.

## Objective

| Study | Layout | Detector model | Source policy |
|---|---|---|---|
| A | legacy-25x3 | code-compatible | historical |
| B | cygno-5x5x3-v1 | code-compatible | historical |
| C | legacy-25x3 | future thesis-7.3 | explicitly chosen; same as D |
| D | cygno-5x5x3-v1 | future thesis-7.3 | explicitly chosen; same as C |

A/B and C/D isolate module layout, including its necessary effect on the common
vessel envelope/mass. A/C and B/D assess detector corrections, with any source
policy change identified separately. Smoke statistics demonstrate the pipeline,
not agreement with published physics. No full production matrix in this session.

## Phase 0 findings already established

- Public `SamueleTorelli/CYGNO_30_Sim` HEAD is
  `26ddbdbd110426c38ea71ba3d1341a2b26b6d090`, also in this checkout's history.
  A read-only bare reference clone was obtained at `/tmp/cygno-samuele-study.git`;
  its continued availability is not required because the revision exists locally.
- Thesis extract: `local_refs/context_solarnuwithcygno.pdf`, 33 pages;
  SHA-256 `33d8b3c099c88bec4c7b1acaf0944305b0a85229ab4264e8f76445092c0d8825`.
  Sec. 7.3 is on printed pp. 182-190 (extract pp. 7-15).
  Tables 7.1-7.3 and Figures 7.5-7.6 were rendered and visually inspected.
- The thesis simulation specifies five copper bands per side, a 40 micrometre
  GEM acrylic core and a 10 mm vessel wall. Current values are four, 29 micrometres
  and 5 mm respectively; code-compatible must retain them.
- Historical centers: X loop `i=-12..12`, inner Y loop `j=-1..1`,
  `(i*504, j*804, 0)` mm. Gas numbering is all +Z sides then all -Z sides;
  module index `3*(i+12)+(j+1)`, gas copy `side*75+module index`.
- The current source selects a placement uniformly, then uses a surface point
  plus inward random depth. It is not generally uniform bulk sampling and can
  leave Boolean/thin solids. Preserve it for A/B as an independent policy.
- The normalized plotters currently reconstruct only the present layout and do
  not check processed-file geometry markers. Phase 2 must address this.
- The thesis source matrix differs substantially from public historical
  normalization tables. Do not silently substitute those tables for Table 7.1.

## Validation already performed

- Configured and successfully built simulation, analysis and validation targets
  in `../../build/cygno-study`, Release, headless, analysis enabled.
- Environment: Geant4 11.4.2, AppleClang 21.0.0, Python
  `/opt/homebrew/bin/python3` (3.14.7), ROOT 6.40.04 from `/opt/homebrew`.
- All five baseline CTest groups passed in 34.28 seconds: source/mass, geometry,
  transport, analysis and ROOT geometry. Logs: `../../build/cygno-study/Testing/`
  `Temporary/LastTest.log`; artifacts: `../../build/cygno-study/validation-results/`.
  Twenty Po-212 primaries produced 13,509 raw hit rows. The geometry diagnostic
  retained 48 inherited overlap warnings; sampler diagnostics retained 43/1000
  outside GEM-copper samples and 247/1000 outside strip samples. Tests do not
  certify scientific validity or the unimplemented legacy profile.
- Known existing failure: Geant4 11.4.2 Bi-212 decay can abort with PART122 while
  registering excited Pb-208. Existing reproducer is outside passing CTest.
  No suppression, isotope omission, or nuclear-data edits are permitted. Exact
  data-version/preflight investigation belongs to Phase 9.

## Phase 0 completion

[BACKGROUND_EXPERIMENT.md](BACKGROUND_EXPERIMENT.md) defines the independent
axes, exact historical coordinates/order and copy mapping, current numerical
layout, vessel/world rules, thesis discrepancies, and analysis/validation gates.
It also records the Table 7.1 assay transcription target, broken-chain boundaries,
published rates and initial historical-table discrepancies. No simulation,
analysis, configuration or validation code was changed. Phase 0 was committed
locally as `7c02de287c5a1e88f360e00122fd5c0b8069d438` with message
`docs(study): complete phase 0 background experiment audit`. This subsequent
documentation-only checkpoint records that immutable hash; it is not another
study phase. No Phase 0 tasks remain.

Scientific questions explicitly deferred to their requested phases:

- Phase 3: identify the Figure 7.5 input/revision if possible; current public
  plotter tables do not establish it. Resolve normalization quantity provenance.
  Table 7.2's no-cut 10-400 total exceeds its >10 total; preserve as a discrepancy.
- Phase 7: exact resistor axes/count/end connections, band end clearances, Suprasil
  density, GEM/optics reference positions, and common-vessel interpretation when
  the 5x5x3 layout puts middle-layer optics inside the cavity.
- Source/decay validation: historical sampling is not bulk-uniform; cross-model
  comparisons must disclose any source-policy change. Demonstrate transport of
  long-lived equilibrium-chain members despite the installed time threshold.
- Phase 9: full Th-232 preflight and Bi-212/Pb-208 failure investigation, including
  effective dataset versions and historical environment/branching provenance.

## Phase 1 completion

- Added `LayoutId`/`LayoutProfile` to the existing shared geometry header, with
  ordered centers/IDs, expected count, occupied envelope and vessel/World bounds.
  Both profiles use the same code-compatible module dimensions and builders.
- `DetectorConstruction` now receives the immutable layout selection. The source
  sampler, internal solids/materials/offsets, physics and raw Hits schema are
  unchanged. Default selection remains `cygno-5x5x3-v1`.
- `rdecay01 [macro [workers]] --layout legacy-25x3|cygno-5x5x3-v1` selects before
  initialization; invalid/duplicate options are rejected. Startup logs identify
  layout, code-compatible detector model and historical source policy.
- Added an independent historical 75-center TSV fixture and three CTest groups:
  profile contracts, both constructed geometries/CLI/smoke transport, and legacy
  source/RNG/mass validation. Existing checks are reused and extended. Both have
  75 modules, 150 gas cells, 3,227 placements, matching 43-component local patterns,
  disjoint module envelopes, correct gas centers and vessel/World containment.
- Both retain 48 representative inherited overlap warnings; these are diagnostic,
  not an overlap-free certification. Source contamination policy remains unchanged.
  Constructed vessel masses reported by checks: legacy approximately 4116.56 kg,
  current approximately 4203.49 kg; future normalization must use actual geometry.
- Release build in `../../build/cygno-study` succeeded. All **8/8 CTest groups
  passed**, 40.77 seconds, in the Phase 0 environment. Tests include fresh
  20-primary Po-212 runs for both layouts and explicit/default current equality.
- Before changes, saved `geometry.txt`, `placements.tsv` and a fresh fixed-seed
  smoke run in `../../build/cygno-study-phase1-baseline/`. After changes, both
  geometry files are byte-identical and all 13,509 current-layout Hits rows and
  branch schema match exactly. Legacy smoke also produced 13,509 rows (local
  Po-212 smoke is not a layout-sensitive background comparison).
- Post-change profile artifacts: `../../build/cygno-study/validation-results/`
  `layouts-94nfze72/`; suite log: `../../build/cygno-study/Testing/Temporary/LastTest.log`.
  No production matrix was launched; these are geometry/transport checks, not
  completed Study A/B campaigns.
- README, layout guide and validation guide describe the new selection and
  explicitly state that legacy analysis requires Phase 2. No thesis/reference
  material was touched. Geometry-header fingerprint changes conservatively with
  header edits; backward metadata compatibility must be addressed in Phase 2.

Phase 1 local commit: `8589f3c99bebc632647ac7629137eb0003a40aac`,
subject `feat(study): add validated legacy and current layout profiles`.

## Phase 2 completion

- Added a separate one-row `RunMetadata` ntuple to each raw worker file, with
  `GeometryHash`, `Layout`, `DetectorModel` and `SourcePolicy` strings. Identity
  comes from the constructed runtime profile; the 12 raw Hits branches, ordering,
  values and random-number consumption are unchanged. No ROOT dependency was
  added to simulation. Master-only metadata files are avoided; repeated runs
  reset metadata along with Hits. This is identity, not completion/event accounting.
- `SimpleProcessEvents` resolves both supported layouts from metadata, retains
  the existing grouping/EOF behavior and copies run metadata into processed data.
  Unversioned inputs require both `--assume-layout PROFILE` and
  `--assume-model code-compatible`; the old `--assume-geometry` name is an alias.
  Assumptions cannot override mismatches or malformed/partial metadata.
- Shared `analysis/FileIdentity.hh` validates every available raw/processed
  identity record, including agreement between them. Processed and histogram
  outputs record layout, detector model, source policy, hash and provenance.
  The future thesis model remains unsupported and explicitly rejected rather
  than reconstructed with code-compatible dimensions.
- Backward compatibility accepts known pre-Phase-2 current-layout processed
  markers, preserving the original geometry hash and recording the interpretation.
  The verified baseline header hash at `74cc26f` is accepted only for current
  layout/code-compatible; it never establishes legacy layout. Unknown hashes and
  hash-only raw metadata cannot bypass the guard. See `docs/ANALYSIS.md` for the
  exact compatibility contract and the limits of researcher assumptions.
- The existing ROOT geometry adapter now requires an explicit profile. All three
  normalized plotters and `PlotSpectrum.C` use the checked profile. Normalization
  files require `# layout:`, `# detector-model:` and `# source-policy:` headers;
  every configured input is checked before creating/replacing output. Mixed-layout
  studies and conflicting model/policy settings fail. Assay/mass values are still
  explicit researcher inputs; resolving them remains Phase 3 and later work.
- Preserved A/B internals, historical sampler/decay settings, existing 20 mm
  fiducial predicates, first-position/group-energy conventions, binning,
  normalization formula and world-Z position plots. The known YZ overflow and
  scientific normalization/ancestry limitations remain documented.
- Release build succeeded in `../../build/cygno-study`. All **9 CTest groups now
  pass**: the first suite run passed 8/9 (60.12 s), with only the historical-table
  constants probe needing an explicit layout binding after the adapter API change.
  That test-only binding was corrected without editing quarantined references;
  targeted `ctest -R '^analysis$' --output-on-failure` passed (10.72 s). No production
  implementation changed after the other eight groups passed. CTest's old
  `LastTestsFailed.log` can retain the initial probe failure; the latest
  `LastTest.log` records its successful rerun.
- New synthetic checks use module 0 (different world coordinates in the two
  profiles): all four plotters give exactly 3 uncut / 2 fiducial entries for each.
  All 150 ROOT gas centers and original fiducial boundaries match constructed
  Geant4 cells for both layouts in every plotting source. Mismatch fixtures cover
  unknown layouts/models/policies/hashes, zero/multiple/partial metadata records,
  conflicting raw/processed markers, explicit assumptions, old fingerprints,
  mixed normalization inputs, and preservation of existing outputs on rejection.
- Fresh 20-primary Po-212 files for both layouts process without assumptions.
  Both profiles' full 12-branch schema and all **13,509 Hits rows** compare exactly
  against the saved Phase 1 `layouts-94nfze72` files. Multi-run and two-worker smoke
  checks verify metadata lifecycle. These are software smoke checks, not completed
  Study A/B campaigns or scientific rate agreement.
- Artifacts beneath `../../build/cygno-study/validation-results/`:
  `layouts-v64g10ci/` (both transport/automatic-processing paths),
  `transport-qmxdzrqq/` (worker/repeated-run checks),
  `layout-analysis-8kfs2hwq/` (identity/cut fixtures), `root-geometry/` (both maps),
  `analysis-__otg0ih/` (successful existing analysis/transcription rerun).
  README and analysis/layout/output/validation guides reflect the new contract.
  No thesis/reference files were touched; no production matrix, push or merge.

Phase 2 local commit: `298cd1e7db2ac4fa2daa703cc231ccf49b3ea550`,
subject `feat(study): validate layout identity throughout analysis`.

## Phase 3 completion

- Added `config/study/thesis-table7.1.json`: 26 explicit component/chain-start
  contributions, 20 in Bq/kg and six resistor contributions in Bq/piece. Each
  records assay material, plot category, activity, upper-limit interpretation,
  Z/A start, stop-before nucleus, equilibrium daughters and full-chain policy.
  Table 7.1 was visually verified; its surrounding chain/normalization discussion
  was read. The reference SHA-256 remains unchanged. No reference files were edited.
- `study/source_matrix.py` validates component/unit/chain structure and provides
  source/isotope/decay controls. It enforces the 26-job partition, excludes separate
  equilibrium Ra-226/Th-228 jobs, stops resistor upper segments before their
  respective boundary ground-state decay, and resets both stop controls for lower
  segments. It launches no jobs and supplies no assumed generated-primary counts.
- `geometry_quantities` reuses the existing detector construction and source lists
  to export all nine component masses, placement counts and actual material names,
  with layout/model/source/hash provenance. Totals agree with the construction
  mass map. Python consumers require matching identity and select kg or pieces
  by the activity unit. Both code-compatible profiles have 750 resistors;
  their 0.00838464 kg mass is never substituted for piece count.
- The two quantity exports agree for every non-vessel component. Vessel masses
  are 4116.556273833247 kg (legacy) and 4203.489372573545 kg (current). These are
  actual Geant4 construction totals, including its Boolean-volume estimation.
  Investigation of installed Geant4 11.4.2 source explains small differences from
  exact box subtraction: legacy -0.009965%, current +0.002142%. No geometry or mass
  correction was made. Export method, values and interpretation are documented in
  `docs/STUDY_SOURCES.md`; re-export for any new build/environment/model.
- Extended the existing three normalized plotters with `quantity-v2`: explicit
  quantity/activity units, generated-primary count and plot category. The legacy
  six-column kg format remains supported. Inconsistent units/quantities, fractional
  piece/primary counts and invalid scales are rejected before output creation.
  The existing 365-day scaling arithmetic, binning, cuts and individual spectra
  remain unchanged. New `Categories/` spectra/stacks sum already normalized
  materials/chains into the seven published categories and combine statistical
  bin errors. Outputs retain the exact normalization configuration and convention.
  Histograms remain counts/bin/year; density and threshold integration are runner
  concerns. Assay/geometric uncertainties are not included in bin errors.
- Historical-input investigation read `331f4e6`, `0b0d1db`, `67239bd`, `48b5b6a`,
  `f2ad08e` and public `26ddbdb` plotter sources/diffs. Early active inputs are
  explicitly test maps; later main maps omit resistors and use assays/masses that
  differ from Table 7.1. The main source is byte-identical at the final three
  inspected revisions. Chain variants do not resolve publication provenance.
  `docs/STUDY_SOURCES.md` records exact revisions and evidence. Figure 7.5's exact
  production inputs/revision remain **unresolved**, rather than asserted absent
  from all possible sources. Historical tables remain untouched/quarantined.
- Preserved Table 7.2's no-cut inconsistency (10–400 keV 3.3e5/year exceeds
  >10 keV 3.2e5/year), Eq. 7.14's rounded-year distinction, and all A/B model/source
  controls. No fitted scale factors, omitted isotopes, branching substitutions,
  lifetime-threshold edits or nuclear-data changes were introduced. The future
  thesis detector remains separately identified and unimplemented.
- Release build succeeded. **Five affected/new CTest groups pass**:
  `chain_boundaries`, `source_matrix`, `analysis`, `layout_analysis`, `root_geometry`.
  The initial targeted suite took 40.51 s, with four passing and `source_matrix`
  revealing an invalid test expectation of exact analytic Boolean volume. After
  confirming the installed estimator, the test was corrected to use an analytic
  diagnostic bound (5%) while preserving exact construction mass-map checks.
  `source_matrix` then passed in 10.02 s. No production code changed after the
  other four groups passed. Unaffected simulation/transport phases were not rerun.
- New tests independently check all published numerical activities, omission of
  x/equilibrium duplicate jobs, stop/reset commands, placement counts, both quantity
  sets, invalid units and quantities, all 26 normalized contributions and seven
  category sums/statistical errors in all three plotters for both layouts.
  The direct tracking test verifies Ra-226/Th-228 primary/daughter stop behavior,
  excited-state retention and lower-segment reset without any decay transport.
  **It does not certify full-chain transport**: the long-lived threshold and
  Bi-212/Pb-208 failure remain for subsequent smoke/preflight investigation.
- Phase 3 artifacts: `../../build/cygno-study/validation-results/`
  `source-matrix-2mfu02gj/` contains both full-precision quantities, hand-selected
  synthetic ROOT inputs, unit/category normalization files and spectra/logs.
  `phase3-reference/` contains read-only-reference derivatives outside the repo;
  `Testing/Temporary/LastTest.log` records the successful matrix rerun. Existing
  analysis/layout test artifacts also remain under `validation-results/`.
  No production Monte Carlo, Study A/B campaign, push or merge was performed.

Phase 3 local commit: `d939c7a1a3bf5614338e1aa406db13d9ab62e9e7`,
subject `feat(study): encode published source matrix and quantity normalization`.

## Phase 4 completion

- Added `study/runner.py`, a smoke-only sequential wrapper around the existing
  simulation, processor, constructed-quantity exporter and main normalized plotter.
  It validates the complete Phase 3 matrix and defaults to its 26 contributions.
  `smoke-A.json` and `smoke-B.json` differ only in layout; both request two primaries
  per contribution and the same base seed. Per-contribution seed pairs exclude
  layout from their derivation. Every attempt is a fresh isolated one-worker
  process with explicit identity, isotope/full-chain/boundary commands and timeout.
  Only smoke counts 1–1000 are accepted; no production override exists.
- Added independent `RunAccounting` output with requested events, actually generated
  primary particles, processed events, aborted events and run ID. Counters reset
  between runs. No Hits columns or random draws changed. The runner requires zero
  process exit, a single worker file, matching identity, consistent accounting and
  successful validated processing. A failed process has unknown (`null`) generated
  count unless successful accounting was already verified. Zero-hit output can be
  software-complete; neither it nor accounting certifies complete decay transport.
- Campaign manifests record revision/working-source fingerprints, config/matrix,
  exact commands and seeds, executable/build fingerprints, actual quantities,
  generated denominators, effective physics/data environment and scientific limits.
  The linked Geant4 reports its version, resolved dataset paths and the instantiated
  radioactive-decay process's actual threshold, observed here as 31,536,000 seconds.
  It is not read from the hadronic parameter's unset sentinel. All 12 effective
  dataset directory contents were independently fingerprinted successfully. No
  physics parameter, dataset or source policy was changed; this is provenance
  capture, not the Phase 9 nuclear-data/branching preflight.
- CMake embeds an active compiled-source fingerprint separately from geometry
  identity. Simulation startup, new processed/histogram `CygnoBuildSource` markers
  and the quantity export identify their build inputs. The runner rejects stale
  simulation/analysis/exporter builds, mismatching campaign identity or corrupted
  completed artifacts. Existing standalone analysis compatibility remains intact.
- Completed matching jobs are revalidated and reused; unrelated failures do not
  remove them. Default resume retains failures; `--retry-failed` creates a new
  attempt without replacing old files. Interrupted `running` jobs are incomplete.
  Atomic manifests, an OS-released advisory lock and output directories outside
  the source repository protect checkpoints. Explicit subsets remain labeled
  partial coverage; all reports retain unvalidated scientific/chain status.
- The existing main plotter now counts exact electron/positron group windows before
  binning, using its unchanged energy sum and first-position fiducial predicate.
  Windows are all finite energies, E>10 keV, 10<E<=400 keV, E<0 underflow,
  0<=E<2000 regular range, and E>=2000 overflow. >10 has no upper cap. Outputs
  retain original histograms plus `ExactEnergyWindows`; JSON adds per-contribution,
  category and selected-total rates/variances and regular-bin counts/keV/year
  densities, with flows separately in counts/year. No threshold-bin approximation,
  new cuts, branch weights or fitted scale factors were introduced.
- Release build succeeded. The **full 12/12 CTest suite passed in 74.70 seconds**,
  including new runner checks and generated/processed accounting across single-
  worker, two-worker and repeated-run transport fixtures. After the final build
  provenance additions, all **five affected groups passed in 63.27 seconds**:
  `study_runner`, `source_matrix`, `analysis`, `layout_analysis`, `root_geometry`.
  Initial development checks exposed a ROOT string-branch address error in the
  new counter writer; persistent branch storage fixed it before these passing
  runs. No implementation changed after the final passing checks.
- Runner fixtures cover zero-hit completion, rejection of nonempty ROOT output
  without accounting, incomplete/aborted counts, nonzero process exits/timeouts,
  failure retention/retry, artifact corruption, changed config/matrix/source,
  lock collision, all 26 synthetic scheduled jobs, per-piece input and both-layout
  exact endpoint/overflow/density calculations. They run the real processor and
  plotter, but replace matrix transport with explicitly labeled synthetic files.
  They are not Study A or a full-chain transport validation.
- Fresh fixed-seed 20-primary Po-212 files in both layouts retain exactly the old
  12-branch schema and all **13,509 Hits rows**, compared directly against Phase 2
  `layouts-v64g10ci/` artifacts. No detector solids, placements, source sampling,
  transport settings or historical grouping rules were changed.
- Artifacts under `../../build/cygno-study/validation-results/` include
  `layouts-ptfvnjhx/` (unchanged-hit regression), `transport-q37qjw2g/` (accounting),
  `study-runner-joo5ky76/` (final runner fixtures including synthetic 26-job matrix),
  `source-matrix-qycpdvx8/` (final matrix checks), and
  `phase4-dataset-fingerprints.json` (actual installed datasets). Full/targeted test
  transcripts were also saved at `/tmp/cygno-phase4-full-tests.log` and
  `/tmp/cygno-phase4-final-tests.log`; CTest retains its latest log in the build.
  Development fixture manifests record the then-dirty checkout; do not relabel or
  resume them as a post-commit study. Start Phase 5 in its own clean output directory.
- `docs/STUDY_RUNNER.md`, README and output/analysis/validation guides document
  operation, recovery, provenance, exact endpoints and scientific limits. Protected
  reference material was not touched. No Study A/B, production Monte Carlo,
  thesis-model work, push or merge was performed.

Phase 4 local commit: `ecf3eeba31082e5b53f3d522e543f3446d5a544b`,
subject `feat(study): add resumable smoke runner and exact energy accounting`.

## Phase 5 completion: Study A smoke diagnostic

- Ran the unchanged `config/study/smoke-A.json` from clean Phase 4 commit
  `ecf3eeba31082e5b53f3d522e543f3446d5a544b`, after confirming the existing Release
  build was up to date. All 26 Table 7.1 contributions used legacy-25x3,
  code-compatible internals, historical sampling, two primaries per job, one fresh
  single-worker process per job, common base seed 12345 and the unchanged split-chain
  commands. No simulation, analysis, source-matrix or configuration files changed.
- Original campaign: `../../validation-runs/study-A-smoke/`, fingerprint
  `36f023b564c07fcdb1172a1c2da8f03110f9a1aca346f1517e2161c46b055062`.
  The run and subsequent identical resume both returned zero. All **26/26 jobs**
  completed software checks; **52 requested/generated/processed primary events**,
  no aborted events and no failed processes. All raw files, manifests, logs and
  normalization inputs are preserved outside the repository.
- **Physical primary decay transport failed.** All 26 run-summary particle
  inventories contain only their two primary nuclei, with no secondaries. Every
  starting isotope (U-238, Th-232, K-40, U-235, Ra-226, Th-228) has a printed mean
  lifetime longer than the effective 31,536,000-second threshold; even Th-228 is
  2.76 years. Installed `G4VRadioactiveDecay::IsApplicable` and `GetMeanLifeTime`
  enforce this exclusion. The observed primary-only chains/zero terminal times
  are consistent with this mechanism. No threshold, branching, data or physics
  change was made to obtain nonempty output. Bi-212 was not reached, so PART122
  remains unresolved and was not exercised by this campaign.
- Twenty-two jobs have no raw rows. Cathodes_U238 and Cathodes_Th232 have one each;
  RingStrips_U238 and RingStrips_Th232 have two each: **six raw rows total**, all
  zero-deposit primary-ion steps (track 1, parent 0, empty creator process). These
  do not establish radioactive decays. The inherited processor excludes these
  ions, giving **zero processed groups** for all jobs. Positions/copy IDs are kept
  in the committed audit record. No inherited geometry/sampling issue was altered.
- Verified every normalization row against its matrix activity, actual quantity and
  denominator of two. Vessel mass is 4116.5562738332474 kg; all six resistor rows
  use 750 pieces. All 312 exact contribution-window records, 84 category-window
  records, 12 total-window records, individual/category ROOT spectra and 14
  900-bin category density exports are zero, including flows. They are pipeline
  outputs under suppressed decay, **not zero-background estimates, upper limits
  or a successful thesis reproduction**. Do not infer physics from their zero
  counting errors or form zero-over-zero A/B ratios.
- Independently audited every job's saved checksums, raw identity/accounting,
  processed structure, macro/seeds, simulation/processing receipts and complete
  particle inventory, then ROOT/JSON spectra and all 26 normalization rows. An
  initial audit assumption of zero raw rows was corrected after inspecting the
  six zero-energy primary rows; the corrected audit passed without application
  changes or a simulation rerun. Previously completed CTest phases were not rerun.
- Before repository edits, repeated the identical runner invocation once: **26
  REUSE results, zero new attempts**. Job artifacts still match original recorded
  checksums/attempt manifests; normalization text and exported spectra are identical
  to the initial report. Reports are `reports/report-1790064245127040000` and
  `reports/report-1790064361458512000`. Audit scripts, checksums and both runner
  transcripts are preserved in the campaign's `audit/` directory.
- [STUDY_A_SMOKE.md](STUDY_A_SMOKE.md) documents execution, negative transport
  outcome, exact counts and limits. [study-results/smoke-A.json](study-results/smoke-A.json)
  is the portable audited evidence, including per-job seeds/raw checksums and
  effective dataset content fingerprints. Original manifests remain unchanged
  (`unvalidated`); the separate audit explicitly classifies `failed-primary-transport`.
  Do not relabel the campaign to this documentation commit or bypass its strict
  resume guard. Its original revision is recorded above.
- Phase 5 is complete **as the prescribed smoke run and diagnosis**, not as physics
  validation. Phase 6 remains a layout-only smoke comparison with the same
  suppression unless a later explicitly separated physics study changes it.
  No Study B, production Monte Carlo, thesis-model changes, reference-file writes,
  push or merge was performed.

Phase 5 local commit subject: `docs(study): record smoke A and primary decay suppression`.
Resolve its hash at the next phase with:

```sh
git log -1 --format=%H --fixed-strings --grep='docs(study): record smoke A and primary decay suppression'
```

## Phase ledger

| Phase | Status | Local commit |
|---|---|---|
| 0 Audit and experiment specification | COMPLETE | `7c02de287c5a1e88f360e00122fd5c0b8069d438` |
| 1 Multiple layouts | COMPLETE | `8589f3c99bebc632647ac7629137eb0003a40aac` |
| 2 Layout-aware analysis | COMPLETE | `298cd1e7db2ac4fa2daa703cc231ccf49b3ea550` |
| 3 Published source matrix | COMPLETE | `d939c7a1a3bf5614338e1aa406db13d9ab62e9e7` |
| 4 Study runner | COMPLETE | `ecf3eeba31082e5b53f3d522e543f3446d5a544b` |
| 5 Smoke A | COMPLETE — diagnostic; primary decays suppressed | phase commit identified by exact subject above |
| 6 Smoke B and A/B comparison | NOT STARTED | - |
| 7 Separate thesis detector model | NOT STARTED | - |
| 8 Smoke C/D and comparisons | NOT STARTED | - |
| 9 Th-232 / Bi-212 preflight | NOT STARTED | - |
| 10 Guide and handoff | NOT STARTED | - |

## Continuation

Resume **Phase 6**, Smoke B and A/B comparison, after inspecting Git state and
reading this file. Record the Phase 5 commit hash and read `STUDY_A_SMOKE.md` and
`STUDY_RUNNER.md`. Preserve the completed A campaign; do not rerun A merely because
this documentation commit changes the checkout revision. Its independent audit can
still inspect the original artifacts without rewriting their source identity.

Verify that B shares A's compiled source hash, executable checksums, matrix, effective
physics/data, seeds, counts, internal model and source policy; this Phase 5 commit
changes documentation/evidence only. Launch the configured tiny B campaign in a new
directory, from the repository root:

```sh
source ../../software/geant4-11.4.2/bin/geant4.sh
cmake --build ../../build/cygno-study --parallel 6
/opt/homebrew/bin/python3 study/runner.py \
  --config config/study/smoke-B.json --build ../../build/cygno-study \
  --output ../../validation-runs/study-B-smoke
```

Inspect B's accounting, all particle inventories, raw primary steps, exact windows
and normalization inputs. Compare A/B only after explicitly checking that layout
and its derived vessel envelope/mass are the controlled differences. If B has the
same absent primary decays, document the negative transport result and pipeline/
quantity comparison; empty spectra cannot establish a physical layout effect or
published-rate agreement. Never form a 0/0 ratio or treat zero counting errors as
physical precision. Retain any runtime failures without omitting contributions.

Do not silently raise thresholds, omit Bi-212 or substitute daughter branch weights.
The known suppression and unexercised Bi-212 failure stay visible for the planned
preflight. After documenting/validating B and A/B, update this file and make its own
logical local phase commit before starting the separate thesis model in Phase 7.
Do not repeat Phases 0–5, launch production, push or merge to main.
