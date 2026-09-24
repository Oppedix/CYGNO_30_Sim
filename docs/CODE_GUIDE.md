# Architecture and event lifecycle

Start with `config/study/samuele.json` and a generated study macro, then follow this path:

```text
macro → primary sampler → Geant4 transport/TrackingAction → sensitive gas StepRecord
  ├─ raw Hits → analysis.raw.preprocess ───────────────┐
  └─ compact accumulator → trees → compact reader ───┤
                                                     ▼
                                              canonical groups
                                                     ▼
                              common spectra/normalization/reporting
                                                     ▼
                                          spectra / tables / figures
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
The worker analysis manager books the selected output trees once during action construction; closing
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
The latter extracts one StepRecord, including pre-step global time/ns. Enabled
raw and compact sinks consume that same record. Raw remains unfiltered; compact
uses the historical state machine and flushes at sensitive-detector EndOfEvent.
No output code calls an RNG or changes transport.

`analysis/reference_cpp/` is the optional CERN ROOT reference target group. `ProcessEvents.cc` implements
grouping, and the short `SimpleProcessEvents.cpp` handles paths/options. Plotters
share `analysis/reference_cpp/DetectorGeometry.hh`, an adapter over the selected numerical layout,
and `analysis/reference_cpp/FileIdentity.hh`, the raw/processed layout and model guard. RunAction
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
| `analysis/` | Canonical Python model, raw/compact readers, common analysis, active C++ references |
| `study/` | Matrix/config validation, isolated runner, decay preflight, figure/table export |
| `validation/` | Software regressions and diagnostic macros |
| `docs/` | Researcher documentation and migration record |
| `data/` | External Geant4 data examples, reference text and license |
| `legacy/` | Inactive custom physics/histograms, historical scripts and source copies |

The active CMake source list is explicit. `PhysicsList` and `HistoManager` in
`legacy/scaffolding` are not linked. Their behavior must not be mistaken for the
active reference physics list. The complete original-to-current move mapping is
[FILE_MOVES.json](FILE_MOVES.json).

## Legacy combined study entry points

`study/source_matrix.py` validates the Table 7.1 matrix, isotope boundaries and
kg/piece quantities. `legacy/study/combined/runner.py` creates exact macros and seeds, preflights the
effective environment, verifies actual generation/processing and preserves immutable
attempts. `legacy/study/combined/root_io.py` validates ROOT identity/accounting and exports the
existing plotter's exact windows. `legacy/study/combined/figures.py` formats plots/tables from those
normalized outputs; it does not simulate, regroup events or renormalize activities.
`study/preflight.py` tests long-lived daughters and full Th/Bi transport. C++ only
observes the RDM setting; explicit macros set it. Worker progress is logged every
500 completed events without changing RNG calls or transport.

## Two-stage entry points

- `study/simulate.py`: stdlib-only scheduling, accounting and resume.
- `study/runtime.py`, `campaign.py`, `archive.py`: shared provenance, portable
  integrity checks and complete-campaign packaging.
- `app/geometry_quantities.cc`: production metadata exporter, available without tests.
- `study/analyze.py` and the modules under `analysis/raw`, `analysis/compact`, `analysis/common`:
  chunked ROOT-free offline validation, grouping, normalization and reports.
- `tests/`: pure-Python fixtures and optional C++ reference parity.

The older combined `legacy/study/combined/runner.py` and its PyROOT adapters remain a legacy
comparison path. Use the [two-stage workflow](BACKGROUND_STUDY.md) for new campaigns.

## Output ownership and keys

`StepRecord.hh` is independent of Geant4. `HitOutput::ExtractStep` is the only
step extractor. The pure `CompactAccumulator.hh` owns group state and event-local
track metadata. `CompactOutput.cc` books/fills Groups, GroupVolumes, Tracks and
TrackGroups. The sensitive detector owns its accumulator; no state is shared
between workers. EndOfEvent emits the last group and clears tracks. Repeated
flushes are safe; subsequent runs reuse booking after ROOT row reset.

`analysis/common/model.py` is the sole canonical Python Group/GroupVolume model.
Raw preprocessing ports the historical state machine; compact preprocessing only
validates/reconstructs its persisted result. Explicit TrackGroups supports a
track contributing to multiple groups. Diagnostic IDs/times never drive spectra.

All specialized C++ plotters and PlotSpectrum.C were audited: existing validation
and CMake still use them, so they remain active references. Only the superseded
combined Python workflow moved to `legacy/study/combined/`; its intentional
regression tests still import it. No file was quarantined based on age alone.
