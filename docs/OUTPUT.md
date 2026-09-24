# Simulation storage contract

Select `--output-mode raw|compact|both` on `study/simulate.py` or `rdecay01`.
Raw remains the default/reference/debugging product. Compact is recommended for
large production after same-transport parity validation. Both writes the two
representations from the **same transport**, in one worker ROOT file.
No output code calls an RNG. Physics, sampling, seeds and decay policy are unchanged.

## Common metadata

Every worker file retains the unchanged one-row scientific `RunMetadata` tree:
`GeometryHash`, `Layout`, `DetectorModel`, `SourcePolicy` (strings).
`RunAccounting` retains five int32 fields: `RunID`, `RequestedEvents`,
`GeneratedPrimaries`, `ProcessedEvents`, `AbortedEvents`. Successful campaign
accounting requires run ID 0, requested=generated=processed, aborted=0.

The separate one-row `OutputMetadata` TTree contains:

| Field | Type | Schema 1 value |
|---|---|---|
| OutputFormat | string | raw, compact, or both |
| OutputSchemaVersion | int32 | 1 |
| TimingDefinition | string | pre-step global time / ns; Geant4 event-relative, not inter-event time |
| CompactProcessingVersion | string | event-boundaries-and-eof-v2 |

Missing OutputMetadata explicitly means legacy schema-0 **raw only**, requiring
the historical 12-column schema and no compact trees. Missing metadata never
implies compact format. Unsupported versions, malformed metadata, extra/missing
columns or disagreement with the campaign are rejected.

## Raw Hits

Every sensitive-gas step is written, with no energy or particle filter.

| Fields | Type | Meaning |
|---|---|---|
| EventNumber | int32 | Run/worker-local event ID |
| ParticleID | int32 | Event-local track ID, not PDG code |
| ParticleTag | int32 | e-:0, e+:1, gamma:2, alpha:3, otherwise -1 |
| ParentID | int32 | Parent track, which need not enter sensitive gas |
| ParticleName | string | Geant4 particle name |
| x_hits, y_hits, z_hits | float64 | Pre-step WORLD coordinates in mm |
| EnergyDeposit | float64 | Step deposit in MeV, including zero |
| VolumeNumber | int32 | Sensitive-gas copy in the selected layout |
| Nucleus | string | Most recently tracked ion, not guaranteed ancestry |
| ProcessType | string | Track creator process, not current step process |
| GlobalTime_ns | float64 | Pre-step global time explicitly divided by ns |

GlobalTime_ns is the only extension to raw rows. Legacy files without it remain
analyzable: canonical times are `None`, never invented zeros. All other fields
retain their former extraction and units. The last-ion label remains intentionally
unreset across events, following existing TrackingAction semantics.

## Compact trees

Compact output has **no Hits tree**. Both output contains Hits and these tables.
All IDs/counts are int32 with event-local GroupIndex; all energies, coordinates
and times are float64. Strings are ROOT string leaves as in raw output.

| Tree | Fields |
|---|---|
| Groups | EventNumber, GroupIndex, ParticleName, Nucleus, ProcessType, StepCount, TrackCount, VolumeCount |
| GroupVolumes | EventNumber, GroupIndex, VolumeOrder, VolumeNumber, EnergyDeposit, x_first, y_first, z_first, FirstHitTime_ns |
| Tracks | EventNumber, ParticleID, ParticleTag, ParentID, ParticleName, Nucleus, ProcessType, GroupIndex |
| TrackGroups | EventNumber, ParticleID, GroupIndex |

Groups are written in historical order with zero-based GroupIndex reset per event.
StepCount counts admitted e-/e+/alpha steps; TrackCount counts distinct contributing
tracks. GroupVolumes has one row per group/gas copy, in consecutive zero-based
VolumeOrder. Energy adds exactly the same steps in exactly the same order as raw
preprocessing. First position and FirstHitTime_ns belong to the **same first step**,
even if it deposits zero energy. They are not energy-weighted or minimum-time values.

Tracks has one row per event-local track entering sensitive gas (including ignored
particles), sorted by ID within each event. Labels are from its first sensitive
step; in particular, Nucleus is diagnostic last-ion context, not reconstructed ancestry.
GroupIndex is -1 for no historical group, the index for one group, or -2 for multiple
groups. TrackGroups records every membership, sorted by track then group.

The historical state machine is not a track partition. A resumed non-ionization
track following an ionization continuation can enter another group. The explicit
relationship avoids silently selecting just one group and is tested by replay.
ParentID need not refer to a stored track. Keys must always include EventNumber.
Compact readers reject duplicate/orphan keys, invalid order or identities, incorrect
counts and inconsistent sentinels before exposing an event to analysis.

## Lifetime and timing

SensitiveDetector constructs one StepRecord from G4Step and feeds enabled sinks.
The compact state machine holds the current group plus per-event track provenance
and membership. It emits finished groups immediately, flushes the final group in
EndOfEvent, writes tracks, then clears event bookkeeping. No run-sized step buffer
is kept. RunAction writes/closes all trees after the event lifecycle completes.
The Python compact reader uses bounded chunks and one event of reconstructed data.

`GlobalTime_ns` and `FirstHitTime_ns` describe time **within a Geant4 event**. They
permit future intra-event timing/coincidence studies. They do not provide an
absolute relation between independently simulated primary events. The canonical
Samuele analysis never reads them for selection, energy, normalization or tables.

## Validation and storage measurement

```sh
python -m analysis.compact.parity --input both.root --geometry geometry.json
python validation/compact_transport.py --build "$CYGNO_BUILD" \
  --output "$CYGNO_RUNS/compact-check-NEW" --primaries 30
python -m analysis.compact.benchmark --raw raw.root --compact compact.root
```

The small integration defaults to the unchanged GEMsCore_K40 matrix contribution;
`--contribution GEMsCore_U238` selects the chain on a validated environment.
It compares raw-only against both-mode raw rows and accounting, then checks both
representations and standalone compact spectra. Benchmark bytes are separately
measured files, not estimated per-tree compressed bytes. Compression ratio is a
storage diagnostic, never a scientific acceptance criterion. No ROOT fixture is
committed. Full campaign preflight requirements remain in force.
