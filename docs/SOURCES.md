# Source generation and decay policy

Active identity: detector `cygno-300elj-v2`, source `uniform-volume-v1`.
The exact `/detector/RadElement` families are `GEMsPolyimide`, `GEMsCopper`,
`CathodesPolyimide`, `CathodesCopper`, `RingSupports`, `RingStrips`, `Resistors`,
`Vessel`, `Lens`, `Sensors`. Old ambiguous/core/outer/cathode names are rejected.

`RadioactiveSourceSampler::Sample()` chooses a physical placement uniformly from
its family, then samples its material volume uniformly. Every placement in a
family has identical solid/material, verified by tests; one common vessel is a
singleton. The copper skins remain independently selectable.

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
RNG seed API is needed on 11.3. `source_checks` replays 100 same-event vertices
across ten families and tests 20000 placed points/family/profile;
`uniform_volume` tests 100000 local points/family and 10000 rotated samples.

`PrimaryGeneratorAction::GeneratePrimaries()` samples immediately before that
event's vertex. `/isotope/AtomicNumber` and `/isotope/MassNumber` select a neutral,
zero-energy ground-state ion on the next event, including later runs. Default is
U238; `/gun/particle` remains usable until an isotope update. Multi-worker
scheduling can change source histories; archive seeds, build/data and metadata.

## Assays and normalization

The canonical [matrix](../config/study/cygno-300elj-radioassay-v2.json) has 28
contributions in seven categories. Separate 300ELJ and laminate-copper assays
apply to GEM and cathode layers; `G4_KAPTON` supplies polyimide transport only.
Concentration is per material mass. Whole-laminate assay is a cross-check, not a
layer concentration. [STUDY_SOURCES.md](STUDY_SOURCES.md) and
[SINGLE_MODULE_GEOMETRY.md](SINGLE_MODULE_GEOMETRY.md) give assays, uncertainties,
conversion constants, mass fractions and actual constructed quantities.

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
