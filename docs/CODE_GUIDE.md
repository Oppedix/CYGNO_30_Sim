# Architecture and event lifecycle

Start with `config/study/samuele.json` and a generated study macro, then follow this path:

```text
macro → PrimaryGeneratorAction configuration → source sampler → primary vertex
      → Geant4 transport/TrackingAction → sensitive gas step → HitOutput
      → worker Hits ROOT tree → SimpleProcessEvents → elabHits
      → contribution normalization → seven categories → ROOT spectra / figures / tables
```

`app/rdecay01.cc` chooses interactive/batch mode, the Ranecu RNG, the run manager,
`DetectorConstruction`, the active `QGSP_BIC_EMZ` reference list plus
`G4RadioactiveDecayPhysics`, and `ActionInitialization`. It initializes the kernel
before executing the macro. Batch macro errors now return a failure status.

`src/geometry/DetectorConstruction.cc` defines materials, builds named solids and
logical volumes, and places them using the shared layout in
`common/DetectorGeometry.hh`. A solid is a shape; a logical volume adds material;
a physical placement supplies position and copy number. All component placements
are World daughters with translations only. The shared gas logical volume gets a
worker-local `SensitiveDetector` in `ConstructSDandField`.

`src/source/PrimaryGeneratorAction.cc` owns isotope and source-component UI
commands and the particle gun. `RadioactiveSourceSampler.cc` resolves a component
list, picks a placement and samples its surface/depth model. It does not own or
modify detector solids. Invalid source lists fail explicitly.

For each run, `RunAction` creates a new `Run` accumulator and opens an output file.
The worker analysis manager books `Hits` once during action construction; closing
a run resets rows while preserving the booking. Give successive runs distinct
`/output/OutFile` basenames to retain both files. The master merges worker run
statistics; ROOT worker files remain separate.

For each event, Geant4 calls `GeneratePrimaries` **before**
`BeginOfEventAction`. The generator applies pending isotope settings, samples the
source position, sets the gun and immediately creates that event's vertex.
`EventAction` resets bookkeeping, then prints the completed decay-chain summary
at event end. It no longer selects or samples the source.

`TrackingAction` implements the inherited decay policy and updates the sensitive
detector's last-ion label. It records actual track-1 primary metadata, fixing the
former first-run geantino summary. During transport every gas step calls
`SensitiveDetector::ProcessHits`, which delegates to `src/output/HitOutput.cc`.
The latter centrally defines the 12 columns and writes rows directly; there is
no separate `G4VHit` collection or energy filter.

`analysis/` is a separate CERN ROOT target group. `ProcessEvents.cc` implements
grouping, and the short `SimpleProcessEvents.cpp` handles paths/options. Plotters
share `analysis/DetectorGeometry.hh`, an adapter over the selected numerical layout,
and `analysis/FileIdentity.hh`, the raw/processed layout and model guard. RunAction
records a separate one-row identity ntuple per worker file without altering Hits.
`validation/` links the actual simulation library, builds diagnostic tools and
runs synthetic ROOT fixtures. Test output stays in the build tree.

## Directory responsibilities

| Directory | Responsibility |
|---|---|
| `app/` | Application entry point |
| `include/cygno/`, `src/` | Matching geometry, source, actions and output classes |
| `common/` | Library-independent geometry definitions; generated-header template |
| `config/` | Current example, visualization, historical run and normalization inputs |
| `analysis/` | ROOT processing and normalization |
| `study/` | Matrix/config validation, isolated runner, decay preflight, figure/table export |
| `validation/` | Software regressions and diagnostic macros |
| `docs/` | Researcher documentation and migration record |
| `data/` | External Geant4 data examples, reference text and license |
| `legacy/` | Inactive custom physics/histograms, historical scripts and source copies |

The active CMake source list is explicit. `PhysicsList` and `HistoManager` in
`legacy/scaffolding` are not linked. Their behavior must not be mistaken for the
active reference physics list. The complete original-to-current move mapping is
[FILE_MOVES.json](FILE_MOVES.json).

## Study entry points

`study/source_matrix.py` validates the Table 7.1 matrix, isotope boundaries and
kg/piece quantities. `study/runner.py` creates exact macros and seeds, preflights the
effective environment, verifies actual generation/processing and preserves immutable
attempts. `study/root_io.py` validates ROOT identity/accounting and exports the
existing plotter's exact windows. `study/figures.py` formats plots/tables from those
normalized outputs; it does not simulate, regroup events or renormalize activities.
`study/preflight.py` tests long-lived daughters and full Th/Bi transport. C++ only
observes the RDM setting; explicit macros set it. Worker progress is logged every
500 completed events without changing RNG calls or transport.
