# Source generation and decay policy

The supported `/detector/RadElement` names are exactly `Cathodes`, `GEMsOuter`,
`GEMsCore`, `RingSupports`, `RingStrips`, `Resistors`, `Vessel`, `Lens`, `Sensors`.
Lists are populated from actual placements. Ambiguous `GEMs` and `Rings` are not
aliases: choosing copper/core or strip/support is a scientific choice. Old
scripts using those names are quarantined under `legacy/config/`.

`/isotope/AtomicNumber` and `/isotope/MassNumber` select a neutral ground-state ion.
The default is U-238, with zero kinetic energy and gun direction +X. Isotope
commands now take effect on the next event, including a later run. An explicit
`/gun/particle` remains usable until an isotope command requests an ion update.
Use fresh processes to compare source configurations reproducibly.

## Same-event source position

Historically, event 0 used the default origin and each later event used a position
sampled in the preceding event callback, per worker. This was incorrect callback
ordering. Sampling now occurs directly before `GeneratePrimaryVertex`.
**Fixed-seed raw results intentionally differ from 05a2b92 after this correction.**
The sampler's algorithm and the retained constructor RNG draw are unchanged.

`source_checks` replays both Ranecu and Geant4 11.4's separate `G4QuickRand`
solid-surface RNG, checks 90 actual vertices across all nine source families,
checks a non-origin event 0, and verifies neither vertex generation nor
`BeginOfEventAction` adds sampler draws. It also checks an isotope update.
Geant4's `/random/setSeeds` does not reset that separate solid RNG. A second run
in one process need not match a fresh process, even after repeating those seeds.
Multiple workers introduce scheduling-dependent source histories as well.

## Inherited sampling model

1. Choose one physical placement uniformly from the ordered component list.
2. Call its solid's `GetPointOnSurface()`.
3. Move inward along the surface normal by `uniform(0, configured width)`.
4. Add the placement translation. There are currently no rotations.

This is generally **not uniform-volume contamination**. Surface area weighting,
edge/corner normals, thin walls and Boolean subtractions can affect the density
and can place samples outside the selected solid. There is no rejection loop,
containment cut or automatic bulk sampler. The source depth definitions remain
in the geometry accessors and shared module definitions.

The deterministic diagnostic found 43/1000 GEM-copper and 247/1000 ring-strip
samples outside their selected solids on Geant4 11.4.2; other tested families had
0/1000. These are diagnostic samples, not precision efficiency estimates or a
proof of containment for the other families. Distribution/containment corrections
require a decision on surface versus bulk contamination and intended depth.

## Decay policy

The active physics is `QGSP_BIC_EMZ` plus `G4RadioactiveDecayPhysics`. The inherited
tracking action stops ions with charge greater than two at rest. This affects
recoil transport and is retained. `/rdecay01/fullChain false` kills secondary ions;
true permits the chain. `/stopChain/ZStopDecay` and `/stopChain/AStopDecay` stop the
specified ground-state ion; excited states are treated by the existing policy.
`/rdecay01/timeWindow t1 unit dt unit` controls activity bookkeeping, not a new
particle transport cut. No physics settings or nuclear data were changed.

Geant4 >=11.2 defaults to a one-year very-long-decay-time threshold. Generated
study macros explicitly set 1e60 years, and the worker logs its effective value.
The focused U-238 test demonstrates daughter transport. Full Th/Bi preflights and
U-chain smoke contributions still fail with `PART122` in the tested Geant4 11.4.2/data
environment, preventing a complete published U/Th background; see
[known issues](KNOWN_ISSUES.md).

## Published source matrix

[STUDY_SOURCES.md](STUDY_SOURCES.md) records the Table 7.1 transcription,
26 declared contributions, split resistor chains, historical input investigation
and constructed-quantity provenance. `study/source_matrix.py` validates that
specification and provides the existing source/isotope/chain commands. It does
not launch a run or bypass the unresolved full-chain environment preflight. Both
supported layouts use the same assays and chain policies with the code-compatible
detector model. Other detector models are deferred.
