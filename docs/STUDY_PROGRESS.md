# Background-study finalization

Updated: 2026-09-22. Status: IN PROGRESS.

## Supported scope

Reference: `legacy-25x3`, `code-compatible`, `historical` source policy.
`cygno-5x5x3-v1` remains supported. Detector internals, historical source sampling,
assays, chain boundaries and datasets are preserved. No 11x7 layout is implemented.
The former Phase 7–10 detector-correction roadmap is cancelled.

## Recovery and baseline

Phase 6: `a9be61b` (`docs(study): record smoke B and controlled A/B diagnosis`).
Interrupted Phase 7 was preserved locally as `f82c823` on
`recovery/phase7-wip-20260922`: 17 modified implementation/analysis/validation
files, smoke-C/D configurations, STUDY_THESIS_MODEL.md and test_thesis_model.py
(21 files, 481 insertions, 51 deletions). No references, build/run outputs or ROOT
files were included. The public study branch was restored to clean Phase 6.
The recovery branch is not part of the intended merge or push.

The [Phase 0–6 ledger](history/PHASE0-6_PROGRESS.md) preserves previous validation
and A/B suppression evidence. Original campaigns must not be relabeled or rerun.

## Finalization plan

1. Fresh baseline build and complete tests; confirm existing architecture.
2. Explicit long-lived decay macro setting and daughter-production test; Th/Bi preflight.
3. Minimal smoke/production runner, progress, interruption/resume/retry and macro export.
4. Reuse normalized analysis; add Figure 7.5/7.6 and Table 7.2/7.3 exports.
5. Researcher documentation, final tree audit, clean build and complete validation.
6. Logical local commits and handoff; no merge, push or production-size validation.

## Current checkpoint

Implementation and researcher documentation are complete; final campaign validation
is next. Fresh Phase 6 baseline: 12/12 tests passed in 100.83 s. Updated full suite:
13/13 passed in 111.58 s, including actual long-lived U-238 daughters, synthetic
26-job scheduling, failed-preflight blocking, interrupt/resume/retry, real SIGINT
child cleanup and figure/table/analysis-only checks. Both layouts' geometry.txt and
placements.tsv snapshots are byte-identical to the baseline. Internals are unchanged.

Explicit RDM setting: 1e60 years in macros; observed worker value ~3.1536e67 s.
Two U-238 primaries yield two Th-234 daughters; the one-year control yields none.
Th-232 and Bi-212 preflight still fail PART122 on Geant4 11.4.2. The independent
vacuum-world Bi probe also fails. No verified replacement environment was found;
complete Th contributions require a separately validated compatible environment.
No nuclear data, branch ratios or source distributions were changed.

Runner supports smoke/production, configurable counts (production default 1e7),
explicit macros/list/subsets, sequential progress, immutable attempts, retry,
Ctrl-C resume, and analysis-only regeneration. Figures use actual bin-width
densities; tables retain exact windows and published comparisons separately.
Historical phase reports are retained under docs/history/ with superseded banners.

Next exact task: commit this coherent workflow, run the real 26-contribution smoke
and its unchanged resume/retry/analysis-only paths, validate a manual macro, inspect
rendered spectra and a nonempty detector view, then record final evidence and tree
in a documentation-only local commit. No production-sized Monte Carlo, push or merge.
