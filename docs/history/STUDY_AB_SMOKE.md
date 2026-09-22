> Historical record. The current supported workflow is [BACKGROUND_STUDY.md](../BACKGROUND_STUDY.md).

# Study B smoke and A/B comparison

2026-09-22. **Phase 6 is complete as a smoke diagnostic. Both A and B failed
physical primary decay transport.** B completed all 26 software jobs, but its
empty spectra cannot establish a physical layout effect, a background upper limit
or agreement with the thesis. No A/B rate ratio is defined or reported.

Portable evidence: [B audit](../study-results/smoke-B.json) and
[A/B comparison audit](../study-results/smoke-AB.json). The completed
[A result](STUDY_A_SMOKE.md) remains unchanged. Original B files are outside the
repository at `../../validation-runs/study-B-smoke`, relative to the repository root.

## Execution and controlled differences

B ran from clean commit `930327949aca0033dce48c489a63f47b27bdecba` on
`study/background-reproduction`. A retains its original clean run revision
`ecf3eeba31082e5b53f3d522e543f3446d5a544b`. The intervening commit changed only
`docs/STUDY_A_SMOKE.md`, `docs/STUDY_PROGRESS.md` and `docs/study-results/smoke-A.json`.
The existing Release build was up to date; no application or configuration edit
was necessary. From the repository root:

```sh
source ../../software/geant4-11.4.2/bin/geant4.sh
cmake --build ../../build/cygno-study --parallel 6
python3 study/runner.py \
  --config config/study/smoke-B.json --build ../../build/cygno-study \
  --output ../../validation-runs/study-B-smoke
```

Before launching B, verified equal compiled-source hashes, all four executable
checksums, build-cache checksum, matrix, all 26 macros/seeds, effective physics
environment and all 12 dataset content fingerprints. The final audit also checks
the complete campaign identities, allowing only configuration layout and the
documented source-revision/documentation changes. Python, ROOT, platform and
recorded execution environment match. All 26 simulation receipts have one worker
and the correct explicit layout; macros are byte-identical for each A/B pair.

| Control | A and B |
|---|---|
| Detector model / source policy | code-compatible / historical |
| Matrix / generated count | All 26 Table 7.1 contributions / two primaries each |
| Base seed | 12345; identical contribution-specific seed pairs |
| Compiled-source hash | `43fcab213dcdde608b051875799d0d03b7e257e438a50bf864de944f217b6fc0` |
| Geometry-header hash | `af27bb2cdc0c3fc61ee3877c92c47756fdcd7f359866cf6ca4f79e2e3a8156b2` |
| Physics | Geant4 11.4.2, QGSP_BIC_EMZ + G4RadioactiveDecayPhysics |
| Effective radioactive-decay threshold | 31,536,000 seconds |

The shared geometry-header hash describes code supporting both profiles; it does
not replace the distinct runtime layout identities. As established in Phase 1,
the layout changes ordered module centers and derived vessel/World bounds while
retaining local solids/materials/offsets and 75 modules/150 gas cells. Existing
validation was not repeated. The documented vessel outer sizes are
12616 x 2428 x 1028.8 mm (A) and 2536 x 4036 x 5599.4 mm (B); both retain the 5 mm
code-compatible wall and the existing common-vessel treatment of optics.

| Constructed quantity | A: legacy-25x3 | B: cygno-5x5x3-v1 |
|---|---:|---:|
| Vessel mass, kg | 4116.5562738332474 | 4203.489372573545 |
| Vessel placement count | 1 | 1 |
| Resistor pieces | 750 | 750 |
| Other eight components | Masses, materials and counts exactly equal | Same |

B's vessel mass increases by 86.93309874029728 kg, or 2.111791822035447%.
These are constructed Boolean-solid mass estimates, with the estimator caveat
already documented in [STUDY_SOURCES.md](../STUDY_SOURCES.md), not a newly applied
analytic correction. Only `Vessel_U238` and `Vessel_Th232` normalization quantities
change. All activities, units, categories and generated-primary denominators match;
the six resistor contributions use pieces. Layout headers and campaign file paths
are necessarily different. This quantity comparison is not a measured rate change.

## Observed transport and spectra

| Observation | A | B |
|---|---:|---:|
| Software-complete jobs | 26/26 | 26/26 |
| Requested / generated / processed primary events | 52 / 52 / 52 | 52 / 52 / 52 |
| Failed jobs / aborted events | 0 / 0 | 0 / 0 |
| Tracked primary nuclei / secondary particles | 52 / 0 | 52 / 0 |
| Raw rows / zero-hit jobs | 6 / 22 | 6 / 22 |
| Raw deposited energy, MeV | 0 | 0 |
| Processed groups | 0 | 0 |

All B run inventories contain only the two starting nuclei. The six starting
isotopes have the same printed mean lifetimes as A, all above the unchanged
one-year threshold, and terminal-ion global times are zero. This reproduces A's
observed primary-decay suppression; it does not validate any threshold replacement
or equilibrium daughter transport. Bi-212 was never reached, so PART122 remains
unresolved and unexercised. Split-chain commands alone do not certify transport.

B has one raw row each for `Cathodes_U238` and `Cathodes_Th232`, and two each for
`RingStrips_U238` and `RingStrips_Th232`. All are zero-deposit primary-ion steps
(track 1, parent 0, empty creator process), which the inherited processor excludes.
Their particle/event/copy fields match A. Subtracting the corresponding module
centers makes all six positions agree within 4.55e-13 mm; world positions differ
as expected. The portable B record preserves all raw row fields. This comparison
does not remove or certify the inherited geometry and historical-sampling issues.

Independently checked B's 26 normalization rows, 312 exact contribution-window
records, 84 category-window records, 12 total-window records and 14 category
density exports with 900 bins each, including flows. The ROOT and JSON exports
agree. All individual/category spectra and position plots are empty; A and B
`spectra.json` contents are identical. The uncut and fiducial `all`, E>10 keV,
10<E<=400 keV, underflow, regular-range and overflow records are zero, including
reported counting variances. These arithmetic zeros provide neither physical
precision nor an upper limit. **No 0/0 ratio or published-rate comparison is made.**

## Validation and recovery

B campaign fingerprint:
`c027ebbbe444fa8adb93b1993249853d6c8dec0fc7d16aefd19367a367793e2a`.
The initial runner invocation and one identical resume returned zero:

- Initial report: `reports/report-1790073854956279000`.
- Resume report: `reports/report-1790073946808033000`.
- Resume: 26 REUSE results, no new attempts; original job/attempt manifests and
  artifact checksums retained, normalization text and spectra unchanged.

The independent B audit checks all job artifacts, identity/accounting trees,
processed structures, command receipts, macros, full particle inventories and
analysis outputs. The A/B audit additionally reopens both campaigns' raw files,
checks paired controls and normalization, and verifies all **266 original A files**
against the read-only snapshot taken before B. A was never rerun, resumed or edited.
Both audits passed on their first execution. No previously completed CTest group
was rerun, because this phase changed no implementation.

Audit scripts, preflight evidence, runner transcripts, checksum snapshots and
validation transcripts remain under B's `audit/`. Script fingerprints are in the
portable records. They can inspect these original campaigns after the phase commit
without altering campaign provenance, from the repository root:

```sh
python3 ../../validation-runs/study-B-smoke/audit/check_smoke_B.py
python3 ../../validation-runs/study-B-smoke/audit/compare_AB.py
```

Original campaign manifests remain `unvalidated`; separate audit records classify
both as `failed-primary-transport`. Do not relabel either campaign to this phase's
documentation commit or bypass the runner's strict revision guard. No production
Monte Carlo, physics/data change, reference-file write, push or merge was performed.

The next phase is the separate `thesis-7.3` detector model. Resolve its documented
geometry/material ambiguities with supported evidence or explicitly recorded
choices, preserving code-compatible A/B. Decay-threshold remediation and the
Th-232/Bi-212 investigation remain separate planned preflight work.
