# Reading the simulation

## Run, event, track and step

A **run** is one `beamOn` request: a set of primary events with the initialized
geometry/physics. An **event** starts with primary vertices and includes all their
secondary tracks. A **track** is one transported particle, including a daughter
ion or decay product. A **step** is a finite transport interval of that track;
one track can produce many rows in `Hits`.

## Follow one event through the application

1. `rdecay01.cc` creates the random engine and run manager, registers geometry,
   reference physics and action initialization, then initializes the kernel.
   No arguments opens the Qt session and executes `vis.mac`; an argument executes
   that macro in batch mode. Initialization happens before the batch macro.
2. `DetectorConstruction::Construct` creates materials, solids, logical volumes
   and physical placements. `ConstructSDandField` attaches a sensitive detector
   to the shared gas logical volume. It does not install a drift electric field.
3. `ActionInitialization::Build` installs a primary generator, run action, event
   action and tracking action for each worker. `BuildForMaster` installs only a
   run action to summarize merged worker statistics.
4. `/run/beamOn N` starts a run. `RunAction` creates a `Run`, opens the output and
   books the `Hits` ntuple. `PrimaryGeneratorAction::GeneratePrimaries` creates
   each event's primary vertex. Initially the gun's geantino placeholder is
   replaced with the ground-state ion selected by `/isotope/AtomicNumber` and
   `/isotope/MassNumber` (default uranium-238, zero kinetic energy).
5. `EventAction::BeginOfEventAction` resets decay-chain text and visible-energy
   bookkeeping. **The primary vertex already exists at this point.** The source
   position sampled here changes the gun for the next event, not this event.
   The first event starts at the gun's default origin. This existing ordering is
   preserved and tracked as an issue.
6. Geant4 transports each track and its secondaries using the active physics.
   `TrackingAction::PreUserTrackingAction` counts particles and labels ions.
   With full-chain tracking (the default), ions are put at rest; a configured
   stopping isotope can be killed. Without full-chain tracking, secondary ions
   are killed. These are substantive existing physics policies.
7. Each step in a sensitive gas placement calls `SensitiveDetector::ProcessHits`.
   Every delivered step writes one row, including zero-energy deposits. There
   is no `G4VHit` collection or user `SteppingAction` in this application.
8. `TrackingAction::PostUserTrackingAction` summarizes decay-secondary kinetic
   energies, momentum balance and times. Its visible energy excludes neutrinos;
   it is not a sum of energy deposited in the detector gas. `EventAction` prints
   the chain; its forwarding of event visible energy to `Run` is disabled.
9. At run end, worker statistics merge through `Run::Merge`, the master prints
   the summary, and `RunAction` writes and closes analysis files. `HistoManager`
   is legacy scaffolding: histogram booking is disabled. The active data output
   is the ntuple booked by `RunAction`.

## Geometry vocabulary and placement order

A **solid** describes shape (`G4Box`, `G4Tubs`, or a Boolean subtraction). A
**logical volume** combines a solid with a material, visualization attributes
and optional sensitivity. A **physical volume** places that logical volume in a
mother volume with a translation, rotation, name and copy number. Many physical
volumes can share one logical volume; gas sensitivity applies to all 150 copies.
All current detector components are direct daughters of the air-filled World.
The vessel is a separate copper shell, not their mother volume.

Lengths in `G4Box` are half lengths; the outer size in `G4Tubs` is a radius.
Names such as `CathodeSize_z` and `LensDiameter` are historically misleading;
read the constructor arguments and the known-issues document before editing.

`common/DetectorGeometry.hh` is the dependency-free source of dimensions, pitches,
module centers and gas IDs, all expressed in millimetres. `BuildModuleLayout()`
returns the 75 placements of the 5 × 5 × 3 grid. `DetectorConstruction::Construct`
reads it once and calls `DefineMaterials`, `BuildWorld`, `BuildCathodes`, `BuildGEMs`,
`BuildFieldCage`, `BuildVessel`, `BuildOptics`, and `BuildSensitiveGasVolumes`.
Each builder still visibly constructs solids and logical volumes.
`PlaceInModule` adds `module.center + localOffset`, assigns a copy/name and fills
the corresponding source list. The module is a placement convention, not a new
material-filled mother volume. No rotations or hidden extra materials are added.

See [LAYOUT.md](LAYOUT.md) for the complete envelope, chosen spacing and vessel.

| Component | Placements | Material |
| --- | ---: | --- |
| Cathodes | 75 | Copper |
| GEM outer / core | 450 / 450 | Copper / PMMA |
| Field-cage supports / strips | 150 / 600 | PMMA / copper |
| Resistors | 750 | Al2O3 |
| Lenses / sensors | 300 / 300 | Silicon dioxide / silicon |
| Gas drift regions | 150 | He/CF4 mixture |
| Vessel / world | 1 / 1 | Copper / air |

The gas mixture uses the existing 60/40 partial-density construction, converted
to mass fractions for `AddMaterial`. Material definitions are not recalibrated
by this cleanup. Total physical placements, including World, are 3,227.

For sensitive copy number `v`, `side = v / 75` and `moduleId = v % 75`.
Side 0 is **local** +Z and side 1 is **local** -Z, relative to that module's cathode;
it no longer indicates the sign of the world Z coordinate.
`moduleId = (ix*5 + iy)*3 + iz`, with zero-based indices and Z fastest.
Gas centers are module centers plus `(0,0,+/-250.25)` mm. Gas box dimensions
remain 500 × 800 × 500 mm. Component names are unique and copy numbers are
unique within each component family (not globally across different families).
The singular physical-volume getters in `DetectorConstruction.hh` still return
the last placed member of a component group; name lists contain the full group.
`GetSensitiveDetector()` retrieves the worker's own logical-volume attachment so
tracking labels and step output refer to the same detector in multithreaded runs.

## Macro commands and source selection

Geant4's UI manager dispatches commands to built-in messengers or the application's
messengers. The same commands can be entered in the GUI or stored in a `.mac` file.

| Command | Code and effect |
| --- | --- |
| `/detector/RadElement Cathodes` | `EventAction`: choose the component name used for subsequent source sampling |
| `/isotope/AtomicNumber 84` / `/isotope/MassNumber 212` | `PrimaryGeneratorAction`: select the ion when replacing the initial geantino |
| `/rdecay01/fullChain true` | `TrackingMessenger` -> `TrackingAction`: follow daughter ions at rest |
| `/stopChain/ZStopDecay Z` / `/stopChain/AStopDecay A` | Kill the matching ground-state ion during tracking |
| `/rdecay01/timeWindow t1 unit dt unit` | Set the activity accounting window, not a gas-hit time cut |
| `/output/OutFile name` | `RunAction`: set output basename beneath `outfiles_V2/` |
| `/random/setSeeds s1 s2` | Override the startup wall-clock seed for repeatability |
| `/run/beamOn N` | Simulate N primary events |

Exact supported source names are `Cathodes`, `GEMsOuter`, `GEMsCore`,
`RingSupports`, `RingStrips`, `Resistors`, `Vessel`, `Lens`, `Sensors`.
Legacy names `GEMs` and `Rings` in some macros are not accepted by the sampler.
Unknown/empty names now produce an explicit fatal diagnostic instead of invalid indexing.
The sampler chooses a volume uniformly from its list, a surface point via
`GetPointOnSurface`, and an inward displacement along the normal with a random
depth. This does not guarantee uniform bulk sampling or containment, especially
for Boolean solids. No sampling distribution is changed in this pass.

Use a fresh process for each isotope/run: changing isotope properties after the
gun has become an ion does not replace it, and ntuple booking is repeated on
multiple `beamOn` calls. Legacy example macros using `/gun/...` can configure the
gun directly; do not assume every inherited macro represents a CYGNO study.

## Hits schema: one row per gas step

`RunAction` books columns in the order used by `SensitiveDetector`. Geant4 internal
units are written without conversion: positions in mm, deposited energy in MeV.

| Branch | Type | Meaning |
| --- | --- | --- |
| EventNumber | int | Event ID within the run |
| ParticleName | string | Geant4 particle name |
| ParticleID | int | Event-local track ID, not PDG code |
| ParticleTag | int | e-: 0, e+: 1, gamma: 2, alpha: 3, other: -1 |
| ParentID | int | Parent track ID; primaries have 0 |
| x_hits, y_hits, z_hits | double | World position at the start of the step, mm |
| EnergyDeposit | double | Total energy deposited by this step, MeV |
| VolumeNumber | int | Sensitive gas placement copy number, 0..149 |
| Nucleus | string | Most recently tracked ion label, not a verified ancestor |
| ProcessType | string | Track creator process; empty for primaries |

A hit coordinate is not necessarily a decay vertex. `ProcessType` is not the
process defining the current step. Events with no gas steps have no rows, so the
number of events cannot be inferred from tree entries or distinct event IDs alone.
No ntuple merging is enabled; inspect worker `_tN.root` files. The master file may
be empty/removed. Event ordering across multiple worker files is not guaranteed.

## ROOT analysis is a separate stage

`analysis/SimpleProcessEvents.cpp` reads `Hits`, retains electrons, positrons and
alphas, and groups deposits using its existing event/nucleus/creator-process logic.
It creates `elabHits` with per-volume energy vectors and first stored hit positions.
`PlotNormalizedSpectra*.cpp` reads processed data, uses hard-coded masses,
contaminations and generated-event counts, reconstructs module centers, and makes
spectra with and without fiducial cuts. These are analysis assumptions, not values
automatically obtained from the geometry or output file.

`analysis/DetectorGeometry.hh` adapts the common geometry to ROOT `TVector3`.
All three `PlotNormalizedSpectra*.cpp` files and `PlotSpectrum.C` use it. This
replaces the obsolete 25 × 3 / 3 mm-gap reconstruction with the actual 5 × 5 × 3
centers, including the 0.25 mm cathode offset. The fiducial inset remains 20 mm;
cut widths, energy selections, histogram definitions and normalization inputs are
unchanged. The geometry correction necessarily changes which world coordinates
pass those same cuts. Existing analysis executables must be recompiled.

Branch compatibility, normalization and grouping issues must be reviewed before
treating these scripts as a validated analysis pipeline; see `KNOWN_ISSUES.md`. Root-level `ProcessEvents*.C`
and `SimpleProcessEvents.C` are older variants, not additional simulation actions.

## Where to read next

| Files | Responsibility |
| --- | --- |
| `rdecay01.cc`, `CMakeLists.txt` | Application setup, active physics, batch/Qt startup, Geant4-only build |
| `include/`, `src/ActionInitialization.*` | Register per-worker actions and master run bookkeeping |
| `DetectorConstruction.*`, `common/DetectorGeometry.hh` | Material/solid/logical/physical geometry, shared layout, gas sensitivity |
| `PrimaryGeneratorAction.*`, `EventAction.*` | Ion gun and source selection; event bookkeeping and chain text |
| `TrackingAction.*`, `TrackingMessenger.*` | Ion/decay policies, full-chain flag, activity time window |
| `SensitiveDetector.*` | Step-to-ntuple conversion and last-ion label |
| `RunAction.*`, `Run.*` | Output lifecycle, particle/decay statistics, worker merging |
| `PhysicsList.*`, `PhysicsListMessenger.*` | Retained custom-list alternative; not instantiated by main |
| `HistoManager.*` | Retained histogram scaffolding with booking disabled |
| `mymacros/`, `mymacros_single/`, root `.mac` files | Source/run configurations and inherited example capabilities |
| `analysis/` | Independent ROOT post-processing and spectra |
| `validation/` | Geometry/material/source checks, small runs and ROOT invariants |

The custom physics-list messenger only exists if its owner is instantiated;
compilation alone does not activate that alternative or its UI commands.
`G4GenericMessenger` properties for isotope, source component and output name
remain in their owning actions. `TrackingMessenger` handles `fullChain` and the
multi-unit time-window command. No existing command path has been renamed.
