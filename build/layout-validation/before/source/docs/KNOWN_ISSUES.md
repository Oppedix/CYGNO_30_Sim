# Existing issues requiring separate decisions

These findings are preserved by the first cleanup. Suggested fixes below are
proposals, not implemented changes. A passing regression means the refactor
matches the baseline; it does not establish that the baseline is scientifically
correct.

## Source generation and event ordering

- **Position assigned after vertex creation** — `EventAction::BeginOfEventAction`
  changes the gun after `GeneratePrimaries`. Event zero therefore starts at the
  default origin; later events use an earlier sampled position (per worker in MT).
  Geant4 11.4.2 source confirms `G4RunManager::ProcessOneEvent` calls
  `GenerateEvent` before `G4EventManager` calls `BeginOfEventAction`.
  Proposed fix: select and sample the component inside `GeneratePrimaries`, just
  before `GeneratePrimaryVertex`, retaining the same sampler initially. This
  changes the first source position and random-number ordering; validate separately.
- **Unsupported macro names** — several macros/generators use `GEMs` or `Rings`,
  while the sampler accepts `GEMsOuter`, `GEMsCore`, `RingSupports`, `RingStrips`.
  An unknown name leaves the list empty and `width` uninitialized, followed by
  invalid indexing. Proposed fix: reject unknown names clearly, then explicitly
  choose the intended material component in each macro. Do not guess aliases.
- **Surface-and-depth sampler** — it is not a uniform-volume sampler and does not
  test that the inward-shifted point remains in thin/Boolean solids. This can
  affect source normalization and spatial distributions. Proposed fix: agree on
  surface versus bulk contamination, then implement a contained sampler with
  distribution checks for each component. Preserve current sampling until then.
- **Ion selected only once** — the isotope properties are read only while the gun
  contains a geantino. Changing them later can leave the old ion selected.
  Proposed fix: update ion definition when properties change, with a multi-run
  regression. For now use a new process for each source configuration.

## Geometry and bookkeeping

- **Cathode half-length mismatch** — `CathodeSize_z = 0.05*cm` is passed directly
  to `G4Box` (actual total thickness 1 mm), but gas centers use `CathodeSize_z/2`
  (0.25 mm). Gas and cathode analytically overlap by 0.25 mm at each face.
  Proposed fix: decide whether 0.5 or 1 mm total cathode thickness was intended,
  then consistently derive all offsets from one half-thickness. This changes
  material boundaries and needs overlap and physics validation.
- **GEM Boolean/core dimensions** — copper removes a 0.005 mm-thick slice but the
  PMMA core is 0.029 mm thick at the same placement. A hand-set subtraction
  translation is also present. This suggests copper/core overlap; dimensions
  and material definitions are retained. Proposed fix: agree on the physical
  layer stack, align the cavity/core and run dedicated overlap checks.
- **Misleading labels** — the vessel was labeled PMMA but uses copper. The
  variable `LensDiameter = 1*cm` is passed as a radius (actual diameter 2 cm).
  Comments now identify the actual definitions. Any material or dimension change
  requires a scientific decision; a later unambiguous rename can clarify radius.
- **Mass printout mistakes** — negative-Z GEM cores add `logicGEM->GetMass()`;
  negative-Z resistors add `logicRingStrip->GetMass()`. The map initializes
  `Resistor` but accumulates `Resistors`, leaving an extra zero entry. These affect
  reported component masses, not the materials assigned to volumes; copying
  these numbers into analysis could affect normalization. Proposed fix: use the
  matching logical volume and one consistent map key, then revalidate masses.
- **Copy numbers are not universally unique** — cathode copies depend only on X;
  opposite-side lenses/sensors reuse copy numbers. Their names distinguish the
  placements. Gas copy numbers remain unique (0..149). Proposed fix: only redesign
  IDs with a documented mapping and compatibility plan if those component IDs
  become data inputs. Existing source lists select by name.

## Output and concurrency

- **Missing return in `SensitiveDetector::ProcessHits`** — the callback is declared
  `G4bool` but falls through after writing a row; Apple Clang reports this. This is
  C++ undefined behavior, even though the local baseline run completed. Proposed
  minimal fix: `return true;` after `AddNtupleRow(0)`, followed by a hit comparison.
- **Last-ion label is not ancestry** — `Nucleus` follows ion tracking order; it is
  not reset at event start. Branch users must not interpret it as a guaranteed
  parent nucleus. Proposed fix: define the intended attribution and propagate
  explicit ancestry. Merely clearing it would also change existing output.
- **Sensitive detector pointer in MT** — `ConstructSDandField` writes the shared
  detector-construction member `fSensitiveDetector`; `TrackingAction` accesses
  it to set ion labels. Multiple workers can overwrite/access another worker's
  pointer. Proposed fix: register/retrieve a worker-local detector or use
  Geant4 thread-local storage, then test multi-worker labels. The regression here
  uses the default single worker and does not establish MT correctness.
- **Thread-count argument ignored** — any third argument selects four workers
  even though `argv[2]` is parsed. Proposed fix: use the parsed value with range
  validation; first resolve the sensitive-detector concurrency issue.
- **Multiple runs in one process** — every run books another ntuple, while writes
  still target ID 0. Proposed fix: book once per analysis manager and reset data
  per run, tested with two `beamOn` calls. Worker files are currently separate;
  enabling merging would be a separate output change.
- **Run summary can mislead** — primary metadata is captured before the geantino
  placeholder becomes an ion, so the first run can print geantino/invalid activity.
  Event visible-energy forwarding is disabled, producing zero/uninitialized-range
  summaries. Proposed fix: capture actual ion metadata and either restore the
  intended accumulator or omit unsupported summary fields; agree on semantics first.

## Analysis compatibility

- **Reconstructed geometry differs** — all three `PlotNormalizedSpectra*.cpp`
  programs use a 3 mm module gap, versus 4 mm in the simulation. At X index 12,
  centers differ by 12 mm; Y differs by up to 1 mm. Analysis Z centers are
  +/-250 mm instead of +/-250.25 mm. Fiducial acceptance can therefore differ.
  Proposed minimal fix: update these constants together after approving the
  resulting selection change; longer term export versioned geometry metadata.
- **Missing branches** — `analysis/SimpleProcessEvents.cpp` and root-level older
  variants bind `VolumeTraslX/Y/Z`, which `RunAction` does not create. Proposed
  fix: remove unused bindings where confirmed, or supply a versioned geometry
  lookup if required. Do not add output columns silently.
- **Grouping/final flush** — `analysis/SimpleProcessEvents.cpp` only writes an
  accumulated group when a later row triggers its `else` branch; it does not
  flush the last group after the loop. Its ionization branch can also accumulate
  without testing the event ID. This can lose the last group or mix event data.
  Proposed fix: define grouping keys explicitly, flush on event/key changes and
  at EOF, with small hand-checked trees. This changes analysis results.
- **Hard-coded normalization** — masses, contaminations and generated-event counts
  in spectrum programs are independent of current geometry and macro settings.
  Proposed fix: document/validate each input against the production configuration,
  then store run metadata alongside output. Do not substitute printed masses
  until the mass-bookkeeping defects above are resolved.
