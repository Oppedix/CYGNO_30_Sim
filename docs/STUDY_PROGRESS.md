# Background-study progress

Updated: 2026-09-21. Study status: IN PROGRESS. Current phase: **Phase 2 COMPLETE**.
First incomplete phase: **Phase 3**, published source matrix. No Phase 3 changes
are included in this checkpoint.

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

Phase 2 local commit subject: `feat(study): validate layout identity throughout analysis`.
Resolve its hash at the next phase with:

```sh
git log -1 --format=%H --fixed-strings --grep='feat(study): validate layout identity throughout analysis'
```

## Phase ledger

| Phase | Status | Local commit |
|---|---|---|
| 0 Audit and experiment specification | COMPLETE | `7c02de287c5a1e88f360e00122fd5c0b8069d438` |
| 1 Multiple layouts | COMPLETE | `8589f3c99bebc632647ac7629137eb0003a40aac` |
| 2 Layout-aware analysis | COMPLETE | phase commit identified by exact subject above |
| 3 Published source matrix | NOT STARTED | - |
| 4 Study runner | NOT STARTED | - |
| 5 Smoke A | NOT STARTED | - |
| 6 Smoke B and A/B comparison | NOT STARTED | - |
| 7 Separate thesis detector model | NOT STARTED | - |
| 8 Smoke C/D and comparisons | NOT STARTED | - |
| 9 Th-232 / Bi-212 preflight | NOT STARTED | - |
| 10 Guide and handoff | NOT STARTED | - |

## Continuation

Resume **Phase 3**, published source matrix, after inspecting Git state and
reading this file. Record the Phase 2 commit hash, then inspect the normalization
provenance and source-matrix requirements in `BACKGROUND_EXPERIMENT.md` against
the read-only Sec. 7.3/Table 7.1 reference. Inspect the already identified public
plotter revisions (`0b0d1db`, `67239bd`, `48b5b6a`, `f2ad08e`) to investigate the
Figure 7.5 input/revision; record unresolved provenance rather than inventing it.
Create the explicit 26 component/chain-start contribution matrix with Bq/kg and
Bq/piece units, equilibrium treatment and resistor stop/restart boundaries. Keep
historical unverified normalization tables separate; do not substitute them for
Table 7.1 or disguise resistor counts as kilograms. Preserve Table 7.2's stated
inconsistency. Validate Phase 3 with small fixtures before its local phase commit.

Do not repeat Phases 0-2 or restart the refactor. No Phase 3 changes have begun.
The remaining ledger and `BACKGROUND_EXPERIMENT.md` retain the follow-on study
requirements. Keep A/B layout-only and the future thesis model separate. Do not
launch a production matrix, push, or merge to main.
