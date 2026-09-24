# Background-study finalization

> Layout update (2026-09-24): `cygno-11x7-v1` is now implemented; see
> [current layout contracts](LAYOUT.md). The dated findings below describe the earlier two-profile baseline.

> Current workflow: [two-stage simulation/offline analysis](BACKGROUND_STUDY.md).
> The earlier macOS PART122 results below remain historical evidence. The operator
> now reports a Linux x86_64 private Geant4 11.3.1 serial environment passing all
> four preflight cases; this is not a universal Geant4 fix.


Updated: 2026-09-22. Status: SOFTWARE FINALIZED — complete published U/Th background blocked by PART122.

## Supported scope

Reference: `legacy-25x3`, `code-compatible`, `historical` source policy.
`cygno-5x5x3-v1` remains supported. Detector internals, historical source sampling,
assays, chain boundaries and datasets are preserved. No 11x7 layout is implemented.
The former Phase 7–10 detector-correction roadmap is cancelled. The finalized
scope is Samuele's workflow and analysis infrastructure using thesis Table 7.1;
the tested Geant4 11.4.2/data environment cannot yet produce the complete published
U/Th background because of `PART122`.

## Recovery and baseline

Phase 6: `a9be61b` (`docs(study): record smoke B and controlled A/B diagnosis`).
Interrupted Phase 7 was preserved locally as `f82c823` on
`recovery/phase7-wip-20260922`: 17 modified implementation/analysis/validation
files, smoke-C/D configurations, STUDY_THESIS_MODEL.md and test_thesis_model.py
(21 files, 481 insertions, 51 deletions). No references, build/run outputs or ROOT
files were included. The public study branch was restored to clean Phase 6.
The recovery commit is not an ancestor of the public study branch. The deferred
`thesis-7.3` implementation exists only on that separate local recovery branch,
which must not be included when publishing.

The [Phase 0–6 ledger](history/PHASE0-6_PROGRESS.md) preserves previous validation
and A/B suppression evidence. Original campaigns must not be relabeled or rerun.

## Completed finalization scope

1. Fresh baseline build and complete tests confirming the existing architecture.
2. Explicit long-lived decay macro setting and daughter-production test; Th/Bi preflight.
3. Minimal smoke/production runner, progress, interruption/resume/retry and macro export.
4. Existing normalized analysis with Figure 7.5/7.6 and Table 7.2/7.3 exports.
5. Researcher documentation, final tree audit, clean build and complete validation.
6. Logical local commits and handoff; no merge, push or production-size validation.

## Completion

Software finalization is COMPLETE, with a documented external scientific blocker.
Reference detector/layout/source scope is unchanged. No production-sized campaign,
merge or push was performed. See [final handoff](FINALIZATION.md) for exact commands,
full recovery-file list, repository tree and [portable evidence](study-results/finalization.json).

- Fresh Phase 6 baseline: 12/12 tests, 100.83 s.
- Final clean out-of-source Release build with UI/vis enabled: 13/13 tests, 105.18 s.
- Both layouts' geometry and placement snapshots remain byte-identical to Phase 6.
- Explicit macro threshold 1e60 years observed on the worker (~3.1536e67 s).
  Two U-238 primaries produce two Th-234 daughters; default control produces none.
- Full Th-232/Bi-212 and independent vacuum-world Bi preflights fail PART122.
  The real 26-job smoke broadens this to U/Th chains: five K-40 contributions pass,
  21 remain incomplete (19 abort; two tiny Th runs excluded by failed preflight).
- Resume reuses five completed jobs without new attempts; retry retains them and
  creates 21 new failed attempts. Exact exports remain identical across reports.
- Actual Ctrl-C exits 130, preserves completed GEMsCore_K40 and resumes Lens_K40
  into attempt-0002. Synthetic safeguards also test corruption and identity mismatch.
- Manual GEMsCore_K40: two primaries, 352 Hits rows, two processed groups. All
  requested ROOT/PNG/PDF/CSV/JSON/text artifacts generated with incomplete labels.
- Nonempty Geant4 ToolsSG image inspected: 25×3 array visible. Sandboxed Qt fails
  on macOS services; tested offscreen macro supplies a portable validation path.
- Final manifest audit embeds constructed quantities plus per-job seeds, counts
  and state directly in campaign.json, in addition to authoritative job manifests.
  Targeted runner tests passed after this additive change (19.75 s).

Implementation campaign revision: `113d7132c17b384870c891c5c7e8769160a6b32a`.
Later manifest/reporting documentation must not relabel or force-resume those runs.
A new campaign requires the final checkout/build; existing validation artifacts
remain archived at their original identity.

**Next scientific task:** validate an official matched Geant4/nuclear-data environment
that executes full U/Th chains without PART122, then run a fresh statistically useful
campaign. At that historical handoff, no compatible replacement environment had been verified. Preserve
all original attempts; no data edits, branch weights or omitted isotopes are allowed.
The repository is technically ready for fast-forward integration; this is not a
claim that the current environment reproduces complete published background rates.
