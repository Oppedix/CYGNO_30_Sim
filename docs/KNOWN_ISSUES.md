# Findings and decisions

## 1. Harmless code-quality changes

Module placement, dimensions and analysis centers now have one definition;
large geometry construction is split into named builders. Clear names distinguish
half-thicknesses and lens radius. Lifecycle comments describe the actual callbacks.
Unused local pointers in `ProcessHits` were removed. Existing alternative physics,
commands and capabilities were retained.

## 2. Unambiguous implementation bugs fixed

- `SensitiveDetector::ProcessHits` now returns `true` after recording its row,
  avoiding an undefined C++ return without adding any hit filter.
- The optional command-line worker count now uses the parsed positive value,
  instead of selecting four workers for any supplied value. Default remains one.
- `ConstructSDandField` registers each worker's sensitive detector with Geant4.
  `GetSensitiveDetector` reads the logical volume's worker-local attachment instead
  of a shared pointer that workers could overwrite. This keeps tracking labels
  associated with the worker writing the hits. Two-worker transport was checked.
- An unknown or empty radioactive-component list fails with a clear diagnostic
  before indexing. No aliases are invented for ambiguous legacy source names.

Physical names and component copy numbers are made deterministic and unique
within each family as required by the new layout. ROOT center reconstruction is
updated to the shared new geometry, replacing both the old array and inconsistent
3 mm gap. Those intentional geometry changes are detailed in [LAYOUT.md](LAYOUT.md).

## 3. Scientific/behavioral ambiguities preserved

The findings below remain. Suggested fixes are proposals, not implemented
changes. Passing build and regression checks does not establish that the inherited
scientific model is correct.

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
  Unknown names now fail explicitly. The macros themselves are preserved:
  choose the intended material component explicitly before using those legacy
  configurations; copper/core or support/strip are not interchangeable aliases.
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
- **Field-cage overlaps** — the translated PMMA supports intersect copper strips;
  the offset Boolean strips also intrude into gas. Representative Geant4 scans
  report the same overlap categories before and after the layout change.
  Proposed fix: agree on aligned shell cross sections and intended clearances,
  then change Boolean offsets/dimensions in a separate physics-reviewed change.
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
## Output and concurrency

- **Last-ion label is not ancestry** — `Nucleus` follows ion tracking order; it is
  not reset at event start. Branch users must not interpret it as a guaranteed
  parent nucleus. Proposed fix: define the intended attribution and propagate
  explicit ancestry. Merely clearing it would also change existing output.
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

- **Old data versus new geometry** — the shared map is for 5 × 5 × 3 files only.
  The 12-column output carries no geometry version. Use the matching historical
  code for old 25 × 3 data and archive the source/configuration beside new output.
- **Position histogram range** — `RelativePos` recenters X/Y but retains world Z.
  Legacy YZ plots bounded near ±550 mm omit outer-layer hits from visible bins
  (they enter overflow). Proposed fix: explicitly choose world Z with a wider axis
  or module-local Z with relabeled axes in a separately reviewed plotting change.
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

## Decay regression finding

A fixed-seed 40-event Bi-212 full-chain run failed with Geant4 `PART122` while
registering a Pb-208 excitation. The same failure was reproduced with the saved
pre-refactor executable on the same Geant4 11.4.2 installation. The reproducer is
`validation/known_bi212_failure.mac`; it is not a passing smoke test. No decay
physics or nuclide data were changed to suppress it. A minimal next investigation
is to isolate this ion registration in the installed Geant4 radioactive-decay
example and check the matching data/library versions before proposing a fix.

Po-212 smoke and Bi-211 full/partial/stopped-chain runs complete, including a
Bi-211 two-worker run. These do not prove that every isotope chain works. The
active reference-list initialization also prints a one-year threshold for very
long decay times at rest; the presence of a U-238 macro alone does not establish
that all long-lived parent/daughter decays are transported. Review the effective
Geant4 settings for a production isotope without silently changing them here.
