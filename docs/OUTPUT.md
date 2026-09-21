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
The raw tree intentionally has no added geometry/run metadata columns. Archive
source, macro, seeds, build/library/data versions, requested/generated event
counts and worker count alongside raw output.

Bookkeeping corrections use the matching GEM-core and resistor logical masses,
and `RingSupports`/`Resistors` keys consistently. These change printed masses,
not solids, materials or hit energy. Masses are construction totals, not automatic
assay/contamination normalization. The resized vessel construction mass is about
4203.49 kg; adopting it for a study still requires matching the contamination model.

Run summaries use the actual primary, omit unsupported visible-energy summary
values, and label terminal-ion global times without interpreting the mean as a
half-life. The activity estimate is printed only with valid ion mass/lifetime and
sampled time. It is a Monte Carlo bookkeeping estimate, not an assay table.
