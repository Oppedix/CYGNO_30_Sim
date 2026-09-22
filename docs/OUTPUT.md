# Raw output and run bookkeeping

`RunAction` opens `outfiles_V2/<OutFile>.root` relative to the process working
directory, creating the directory. Default basename is `outfiles_V2`.
Geant4 adds `_tN` for worker N. No ntuple merging is enabled. Files with the same
basename can be overwritten: use separate directories or names per run.

`HitOutput.cc` books/fills exactly this `Hits` schema, in this order:

| Column | ROOT type | Meaning |
|---|---|---|
| EventNumber | Int_t | Run-local Geant4 event ID |
| ParticleName | Char_t | Track's particle name |
| ParticleID | Int_t | Event-local track ID, not PDG code |
| ParticleTag | Int_t | e−:0, e+:1, gamma:2, alpha:3, other:−1 |
| ParentID | Int_t | Event-local parent track ID |
| x_hits | Double_t | Pre-step world X in mm |
| y_hits | Double_t | Pre-step world Y in mm |
| z_hits | Double_t | Pre-step world Z in mm |
| EnergyDeposit | Double_t | Step energy deposited in MeV |
| VolumeNumber | Int_t | Sensitive gas copy number, 0–149 |
| Nucleus | Char_t | Most recently tracked ion label |
| ProcessType | Char_t | Track creator process, empty for a primary |

Every sensitive gas step is written, including zero-deposit steps. An event with
no gas steps contributes no rows. `Nucleus` is **not guaranteed ancestry** and is
not reset at event boundaries; assigning a different meaning requires a separate
scientific decision. `ProcessType` is not the process responsible for the step.
The raw Hits tree has no added columns. A separate `RunMetadata` tree contains one
row per worker/run output with four string leaves: `GeometryHash`, `Layout`,
`DetectorModel` and `SourcePolicy`. It is filled without sampling randomness and
is reset between runs. The MT master does not write a metadata-only file. This
record establishes geometry identity, not run completeness or generated counts.

New outputs also contain one `RunAccounting` row, filled at end of run with five
integer fields: `RunID`, `RequestedEvents`, `GeneratedPrimaries`, `ProcessedEvents`
and `AbortedEvents`. Generated primaries count particles actually created by the
gun; processed/aborted events come from event bookkeeping. Counters reset for each
run. Worker counts can be summed for multiworker diagnostics; the study runner
requires one worker and one run. A crash can leave no usable accounting record.
The record and successful file closure establish software accounting only, never
full radioactive-chain transport. The Hits schema and random draws are unchanged.

Archive
source, macro, seeds, build/library/data versions, requested/generated event
counts and worker count alongside raw output.

Bookkeeping corrections use the matching GEM-core and resistor logical masses,
and `RingSupports`/`Resistors` keys consistently. These change printed masses,
not solids, materials or hit energy. Masses are construction totals, not automatic
assay/contamination normalization. The current-layout vessel construction mass is about
4203.49 kg (legacy layout about 4116.56 kg); adopting it for a study still requires matching the contamination model.

Run summaries use the actual primary, omit unsupported visible-energy summary
values, and label terminal-ion global times without interpreting the mean as a
half-life. The activity estimate is printed only with valid ion mass/lifetime and
sampled time. It is a Monte Carlo bookkeeping estimate, not an assay table.

## Study logs and run configuration

Study macros explicitly set the RDM long-decay threshold to `1e60 year`.
`CYGNO_RUN radioactive_decay_time_threshold_s` observes the worker process after
macro commands and before its first event. `CYGNO_ENV` records Geant4/data/build
identity and the post-macro threshold. A failed simulation may lack the latter;
its complete log and pre-transport worker observation are retained. Every 500
events `CYGNO_PROGRESS completed_events N` records observational progress; only
RunAccounting establishes the denominator. See [study manifests](BACKGROUND_STUDY.md).
