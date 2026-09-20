# CYGNO_30_Sim

Geant4 simulation of the CYGNO module array and radioactive backgrounds, derived
from the `rdecay01` example. Geant4 transports particles and writes ROOT-format
step data; CERN ROOT is used separately for post-processing in `analysis/`.

Start with [the source reading guide](docs/CODE_GUIDE.md), then review
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
The current default is one worker; the optional thread-count argument has a
known bug documented below.

`/output/OutFile example` writes under `outfiles_V2/example.root` relative to the
working directory, with worker files such as `example_t0.root` in MT mode.
Without that command the basename is also `outfiles_V2`. Use distinct output
basenames or isolated working directories to avoid replacing earlier results.

## Scope of the first cleanup

Module XY positions are now calculated once and shared by all component loops.
Column grouping preserves the historical placement and source-list order.
Dimensions, materials, Z offsets, copy numbers, cuts, source sampling, active
physics and output columns remain unchanged. The disabled old field-ring model
was removed; scientific inconsistencies are recorded rather than corrected.

See [validation instructions and results](validation/README.md).
