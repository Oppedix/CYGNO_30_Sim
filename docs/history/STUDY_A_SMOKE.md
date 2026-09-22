> Historical record. The current supported workflow is [BACKGROUND_STUDY.md](../BACKGROUND_STUDY.md).

# Study A smoke result

2026-09-22. **Phase 5 is complete as a smoke diagnostic. Physical background
reproduction is blocked by absent primary decays.** All 26 software jobs finished,
but none transported decay secondaries. The zero spectra are not a prediction of
zero radioactive background, an efficiency measurement or agreement with the thesis.

The committed [audit record](../study-results/smoke-A.json) retains configuration,
quantities, dataset fingerprints, per-job seeds/counts/checksums and the six raw
rows. Original raw files, logs, manifests and reports remain outside the repository
at `../../validation-runs/study-A-smoke` (path relative to the repository root).

## Execution and provenance

The run used clean commit `ecf3eeba31082e5b53f3d522e543f3446d5a544b` on
`study/background-reproduction`. The existing Release build was up to date.
No simulation, analysis or configuration changes were needed. The command was:

```sh
source ../../software/geant4-11.4.2/bin/geant4.sh
python3 study/runner.py \
  --config config/study/smoke-A.json --build ../../build/cygno-study \
  --output ../../validation-runs/study-A-smoke
```

Configuration: legacy-25x3, code-compatible internals, historical sampler, the full
26-contribution Table 7.1 matrix, two primaries per job, one fresh single-worker
process per job, base seed 12345, 120-second child timeout. The A/B configurations
still differ only in layout. Split-chain boundaries and lower-segment resets came
unchanged from the Phase 3 helper. The constructed legacy vessel mass was
4116.5562738332474 kg; resistor normalization used 750 pieces, never resistor mass.

| Identity | Recorded value |
|---|---|
| Campaign fingerprint | `36f023b564c07fcdb1172a1c2da8f03110f9a1aca346f1517e2161c46b055062` |
| Compiled source hash | `43fcab213dcdde608b051875799d0d03b7e257e438a50bf864de944f217b6fc0` |
| Geometry hash | `af27bb2cdc0c3fc61ee3877c92c47756fdcd7f359866cf6ca4f79e2e3a8156b2` |
| Geant4 | 11.4.2, multithread build, one worker used |
| Physics | QGSP_BIC_EMZ + G4RadioactiveDecayPhysics |
| Effective decay-time threshold | 31,536,000 seconds (one 365-day year) |
| First report | `reports/report-1790064245127040000` |
| Resume report | `reports/report-1790064361458512000` |

The campaign stores resolved paths and content fingerprints for all 12 installed
Geant4 datasets. Relevant versions include RadioactiveDecay6.1.2,
PhotonEvaporation6.1.2 and G4ENSDFSTATE3.0. No dataset or physics parameter changed.

## Accounting and physical outcome

| Check | Result |
|---|---:|
| Completed simulation/processing jobs | 26/26 |
| Failed jobs / aborted events | 0 / 0 |
| Requested / generated / processed primary events | 52 / 52 / 52 |
| Tracked primary nuclei / tracked secondary particles | 52 / 0 |
| Jobs with zero raw hit rows | 22 |
| Raw hit rows across the other four jobs | 6 |
| Total raw deposited energy | 0 MeV |
| Processed electron, positron or alpha groups | 0 |
| Exact contribution-window records inspected | 312 |
| Category-window records / total-window records | 84 / 12 |

Every run-summary particle inventory contains exactly two tracks of its starting
nucleus and no secondary particles. Event zero's printed chain contains only the
starting nucleus; the run inventory covers both events. Terminal-ion global times
are zero. All primary mean lifetimes printed in these logs exceed the threshold:

| Starting isotope | Reported mean lifetime, years (rounded log value) | Jobs |
|---|---:|---:|
| U-238 | 6.45e9 | 9 |
| Th-232 | 2.021e10 | 9 |
| K-40 | 1.802e9 | 5 |
| U-235 | 1.016e9 | 1 |
| Ra-226 | 2310 | 1 |
| Th-228 | 2.76 | 1 |

These are **mean lifetimes**, not half-lives. Inspection of the installed
`G4VRadioactiveDecay.cc`, `IsApplicable()` (around lines 195–214) and
`GetMeanLifeTime()` (around lines 369–387), confirms that ground-state nuclei with
lifetimes above the effective threshold are rejected and assigned no finite
at-rest decay time. Together with the primary-only logs, this identifies threshold
suppression as the explanation for this smoke outcome. It does not validate a
replacement threshold or establish complete daughter-chain behavior.

The six raw rows are one each in Cathodes_U238/Cathodes_Th232 and two each in
RingStrips_U238/RingStrips_Th232. Every row has the parent isotope as ParticleName,
ParticleID=1, ParentID=0, an empty creator process, and EnergyDeposit=0. They record
primary steps, not radioactive products. Their presence is consistent with the
already documented cathode/cage overlaps and historical source sampling; no new
geometry or sampling correction was attempted. The processor excludes these
primary-ion rows under its existing selection. The audit retains all six rows,
including their positions and gas copy IDs, in the JSON evidence.

Bi-212 was never reached, so the absence of PART122 in these logs says nothing
about whether that known failure is resolved. Upper resistor chain boundaries and
equilibrium daughters were likewise not exercised by actual decays. Their configured
commands alone do not certify their transport.

## Spectra, normalization and verification

All 26 normalization rows were checked against the matrix, actual constructed
quantities and verified denominator of two generated primaries. Six resistor rows
use Bq/piece and 750 pieces; the other 20 use Bq/kg and constructed mass.

All individual and category spectra, both uncut and fiducial, are empty. The exact
`all`, `E>10`, `10<E<=400`, underflow, regular-range and overflow counts, normalized
rates and reported counting variances are zero. All 14 category density exports
(900 bins each), position plots and flow counts were inspected. Empty-spectrum
zero errors are arithmetic outputs of this suppressed-decay run, not evidence of
small physical uncertainty or upper limits. Do not compare these zeros to the
published rates or form a zero-over-zero layout ratio.

An independent audit rechecked every job manifest/artifact checksum, raw identity
and accounting tree, processed structure, macro, command receipt and particle
inventory, then all normalization rows and ROOT/JSON spectra. The first audit's
assumption that empty processed spectra implied no raw rows was rejected; inspection
identified the six zero-deposit primary steps above. The corrected audit passed.
This was an audit-assumption correction; no application change or simulation rerun
was required. The reusable local audit is saved with a fingerprint in the committed
record; from the repository root it can be run with:

```sh
python3 ../../validation-runs/study-A-smoke/audit/check_smoke_A.py
```

Before any repository edits, the identical runner command was repeated once. It
returned success with **26 REUSE results and no new attempts**. Original job files
still match their recorded artifact checksums and attempt manifests; normalization
text and exported spectra match the first report exactly. Both reports and both
runner transcripts are retained. No already completed phase's test suite was rerun.

Original manifests intentionally remain unchanged with `chain_validity: unvalidated`.
The separate audit records the stronger observation `failed-primary-transport` and
keeps software completion distinct from a scientifically usable result. Following
this documentation commit, the campaign's recorded revision remains the original
run revision; do not relabel it or bypass the strict resume provenance guard.

## Next gate

Phase 6 may run the equally small B configuration in its own directory, using the
same binaries, source matrix, seeds, counts, physics/data and source policy. Verify
those controls explicitly, allowing only layout and its derived vessel quantities
to change. The intervening Phase 5 commit changes documentation/evidence only.
If B is also suppressed, report that no physical layout effect can be inferred;
retain useful pipeline/identity/quantity checks without claiming background
reproduction. Keep decay-threshold remediation and Bi-212 investigation visible for
the planned preflight; do not change either silently to make A/B nonempty.
