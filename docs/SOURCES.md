# Source generation and decay policy

The current internal identity is `cygno-copper-cathode-v4 / uniform-volume-v1`.
Both modes share v4 construction; external has a
[separate environmental source contract](../external/docs/PHYSICS.md).
Current `/detector/RadElement` families: `Cathode`, `GEMsPolyimide`, `GEMsCopper`,
`RingSupports`, `RingStrips`, `Resistors`, `Vessel`, `Lens`, `Sensors`.
The cathode is one solid copper slab; no cathode core/skin source exists in v4.
The stable `GEMsPolyimide` identifier denotes the retained 50 µm PMMA core.

`RadioactiveSourceSampler::Sample()` chooses a physical placement uniformly from
its family, then samples its material volume uniformly. Every placement in a
family has identical solid/material, verified by tests; one common vessel is a
singleton. GEM copper skins remain independently selectable.

- Boxes: independent uniform X/Y/Z.
- Cylinders: uniform phi, radius `sqrt(r0²+(r1²-r0²)*U)`, uniform Z.
- Rectangular shells/frames: subtract the clipped, displaced inner box bounds;
  peel non-overlapping axis slabs and select one proportional to volume. No
  inefficient thin-shell bounding-box rejection.

Points use Geant4's physical OBJECT rotation and translation. Current parts are
direct World daughters. `SampleLocal()` asserts containment in debug builds;
validation explicitly checks containment in Release, analytic moments and ranges,
including the asymmetric strip frame and a rotated vessel. No production
surface/depth sampling remains. CLHEP owns all source draws, so no Geant4 surface
RNG seed API is needed on 11.3. `source_checks` replays 90 same-event vertices
across nine families and tests 20000 placed points/family/profile;
`uniform_volume` tests 100000 local points/family and 10000 rotated samples.

`PrimaryGeneratorAction::GeneratePrimaries()` samples immediately before that
event's vertex. `/isotope/AtomicNumber` and `/isotope/MassNumber` select a neutral,
zero-energy ground-state ion on the next event, including later runs. Default is
U238; `/gun/particle` remains usable until an isotope update. Multi-worker
scheduling can change source histories; archive seeds, build/data and metadata.

## Assays and normalization

The [v4 matrix](../config/study/cygno-radioassay-v4.json) has 23 contributions.
EFCu U/Th applies to the entire `Cathode` mass; Acrylic U/Th/K applies only to
GEM cores. Lenses use exact Bq/piece values from
`CYGNO_radioactivity_excel_suprasil`: 3.843 kg is ONE physical lens, converted
once; normalize by actual placements without changing lens transport.
[STUDY_SOURCES.md](STUDY_SOURCES.md) specifies activities and assumptions.

## Retained decay physics

Physics remains `QGSP_BIC_EMZ + G4RadioactiveDecayPhysics`. Tracking stops ions
with charge >2 at rest. `/rdecay01/fullChain false` kills secondary ions; true
permits full chains. `/stopChain/ZStopDecay` and `/stopChain/AStopDecay` stop the
selected ground-state ion before radioactive decay, retaining existing excited
state treatment. `/rdecay01/timeWindow` controls activity bookkeeping.

U/Th use full-chain transport with secular equilibrium as a modelling assumption.
The completed MBNL resistor contributes U238, Th232 and K40 only; each macro
resets both stop controls to 0/0. K40 is one parent contribution. Historical
Al2O3 split-chain measurements are not transferred to the new component. No U235 assay
is invented for the laminate. Study macros set the very-long-decay threshold to
`1e60 year`; effective settings are recorded. Four-case preflight failures,
including environment-specific PART122, remain failures;
[KNOWN_ISSUES.md](KNOWN_ISSUES.md) documents their scope.
