# CYGNO_30_Sim

Geant4 simulation of the CYGNO module array and radioactive backgrounds, derived
from the `rdecay01` example. Geant4 transports particles and writes ROOT-format
step data; CERN ROOT is used separately for post-processing in `analysis/`.

The current array has **5 × 5 × 3 modules**, with two sensitive gas cells per
module. Start with [the source reading guide](docs/CODE_GUIDE.md) and
[the layout definition](docs/LAYOUT.md), then review
[known issues](docs/KNOWN_ISSUES.md) before producing a new background study.
The inherited `README` describes the original Geant4 example and is not the
specification of the current CYGNO application.

## Build and run locally

```sh
export HEP_HOME="/Users/giuseppemariaoppedisano/Desktop/GSSI/PHD/CYGNO/SolarNu/SimSamuele/hep"
source "$HEP_HOME/software/geant4-11.4.2/bin/geant4.sh"
cd "$HEP_HOME/projects/CYGNO_30_Sim"
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
mkdir -p build/outfiles_V2
cd build
./rdecay01                         # Qt UI, executing vis.mac
# Or, in a separate process:
./rdecay01 ../validation/smoke.mac  # 20 fixed-seed Po-212 events
```

The tested local setup uses Geant4 11.4.2 with Qt and multithreading, Apple Silicon
and Apple Clang 21. ROOT 6.40.04 is available for analysis but is not linked into
the simulation executable. After source edits, repeat just the build command.
CMake copies its listed macros into `build/`; macros under `mymacros/` and
`mymacros_single/` need an explicit relative or absolute path.

The active physics is `QGSP_BIC_EMZ` plus `G4RadioactiveDecayPhysics`, selected in
`rdecay01.cc`. The custom `PhysicsList` class is compiled but not selected.
The default is one worker. An optional second argument sets the worker count:
`./rdecay01 ../validation/chain.mac 2`.

`/output/OutFile example` writes under `outfiles_V2/example.root` relative to the
working directory, with worker files such as `example_t0.root` in MT mode.
Without that command the basename is also `outfiles_V2`. Use distinct output
basenames or isolated working directories to avoid replacing earlier results.

## Configure a radioactive run without editing C++

Save this as a macro, then pass its path to `rdecay01` from `build/`:

```text
/random/setSeeds 12345 67890
/isotope/AtomicNumber 83
/isotope/MassNumber 211
/detector/RadElement Cathodes
/rdecay01/fullChain true
/rdecay01/timeWindow 0 s 2 h
/output/OutFile bi211_cathodes
/run/beamOn 40
```

Use a fresh process for each isotope/run. Component choices are `Cathodes`,
`GEMsOuter`, `GEMsCore`, `RingSupports`, `RingStrips`, `Resistors`, `Vessel`, `Lens`,
`Sensors`. `/stopChain/ZStopDecay` and `/stopChain/AStopDecay` select a ground-state
stopping ion; `/rdecay01/fullChain false` disables daughter-ion tracking.
See the [command and output guide](docs/CODE_GUIDE.md) for exact semantics and
preserved limitations, including the first-event source-position ordering.

## Change the layout

Edit the counts and pitches in [common/DetectorGeometry.hh](common/DetectorGeometry.hh).
Geant4 placement and the four ROOT plotting programs consume that same definition.
Current pitches are **504, 804, 2285.30 mm**. The Z pitch includes both drift regions,
GEMs, lenses and sensors, with a 4 mm gap between complete module envelopes.
Do not change internal dimensions to adjust the grid. Rebuild the simulation and
ROOT programs together and repeat the [validation checks](validation/README.md).
The current ROOT geometry map is for new 5 × 5 × 3 files; use historical code for
old 25 × 3 output. Save the source revision/configuration beside production data.

`DetectorConstruction` now separates materials, world, cathodes, GEMs, field cage,
vessel, optics and gas construction. Every component uses a common module-center
translation. Physics, material definitions, module internals, valid source sampling,
decay policies, hit columns, cuts and normalization constants are retained.
The single copper vessel and World are resized to the new array; details and
physical consequences are documented in [LAYOUT.md](docs/LAYOUT.md).

Build, Qt visualization, geometry/material comparisons, source lookup, ROOT geometry
checks and small radioactive runs passed. Existing internal overlaps and a
reproducible Bi-212 decay failure remain documented in
[KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md); the tests are not a validation of the
underlying scientific model or the complete legacy analysis pipeline.
