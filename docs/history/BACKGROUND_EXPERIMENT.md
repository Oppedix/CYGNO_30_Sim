> Historical record. The current supported workflow is [BACKGROUND_STUDY.md](../BACKGROUND_STUDY.md).

# Controlled CYGNO background studies: experiment specification

Phase 0 audit, 2026-09-21. This document specifies future work; it does not add
profiles, change simulation/analysis, or claim to reproduce published rates.
The code-compatible baseline is `74cc26f`. Progress and local checkpoints are
tracked in [STUDY_PROGRESS.md](../STUDY_PROGRESS.md).

## Evidence and scope

The published specification is thesis Sec. 7.3, printed pp. 182-190, in the
read-only local extract `local_refs/context_solarnuwithcygno.pdf` (extract pp.
7-15). Table 7.1 is on p. 186; Figure 7.5/Table 7.2 on p. 189; Figure 7.6/Table
7.3 on p. 190. Those tables and figures were visually checked. Extract SHA-256:
`33d8b3c099c88bec4c7b1acaf0944305b0a85229ab4264e8f76445092c0d8825`.
Do not modify, stage or commit anything under `local_refs/` or `local_context/`.

Historical implementation evidence is the public
[SamueleTorelli/CYGNO_30_Sim repository](https://github.com/SamueleTorelli/CYGNO_30_Sim),
whose inspected master HEAD is `26ddbdbd110426c38ea71ba3d1341a2b26b6d090`.
It has one branch and no tags in the inspected clone. This commit also exists
locally; use `git show 26ddbdb:src/DetectorConstruction.cc` without checking out
or resetting the study branch. The public code is evidence, not proof of the
exact revision/input set behind Figure 7.5. That provenance remains unresolved.

## Independent experimental axes

| Study | Layout profile | Detector-internal model | Source policy |
|---|---|---|---|
| A | legacy-25x3 | code-compatible | historical |
| B | cygno-5x5x3-v1 | code-compatible | historical |
| C | legacy-25x3 | thesis-7.3 | explicit policy shared with D |
| D | cygno-5x5x3-v1 | thesis-7.3 | explicit policy shared with C |

A/B and C/D test a layout change. Hold internal solids, materials, local
component offsets, assays, decay treatment, source policy, generated-event
policy, analysis, cuts, binning and normalization convention fixed within each
pair. The single common vessel must follow the occupied array, so its dimensions,
mass and shielding paths change; this is an explicit part of the layout comparison.
A/C and B/D test detector corrections. If C/D use a different source policy,
those cross-model comparisons measure both changes and must say so; isolating
internals alone would require an additional common-source-policy comparison.

### Axis 1: module layout

Both profiles have 75 identically oriented modules, each with two drift regions:
150 sensitive gas volumes, with no new mother material or module rotations.
The smallest future layout abstraction should provide ID, ordered module centers
and IDs, expected counts, derived occupied bounds, gas-center information, and
vessel/world bounds or their inputs. One `DetectorConstruction` continues to
build the shared internal model. Select layout explicitly before construction,
without recompilation; the executable currently initializes before reading its
macro, so a command-line option is a suitable small extension.

**legacy-25x3:** recover the cathode and sensitive-volume loops at historical
`src/DetectorConstruction.cc`, lines 230-249 and 944-991. Units below are mm:

```text
for i = -12 ... 12:             # long direction, X; outer loop
    for j = -1 ... 1:           # transverse direction, Y; inner loop
        module_id = 3*(i+12) + (j+1)
        center = (504*i, 804*j, 0)
```

The pitches are the 500/800 mm cathode sides plus the implemented 4 mm gap,
not the older 3 mm value mentioned in a comment. All cathode centers lie at
Z=0; the three transverse rows are not three Z layers.

| Module ID | i | j | Cathode center (mm) | +Z / -Z gas IDs |
|---|---|---|---|---|
| 0 | -12 | -1 | (-6048, -804, 0) | 0 / 75 |
| 1 | -12 | 0 | (-6048, 0, 0) | 1 / 76 |
| 2 | -12 | 1 | (-6048, 804, 0) | 2 / 77 |
| 3 | -11 | -1 | (-5544, -804, 0) | 3 / 78 |
| 37 | 0 | 0 | (0, 0, 0) | 37 / 112 |
| 74 | 12 | 1 | (6048, 804, 0) | 74 / 149 |

Samuele's gas counter traverses the complete positive-side array, then the
complete negative-side array. Preserve `VolumeNumber = side*75 + module_id`,
side 0 = local +Z, side 1 = local -Z. For code-compatible, gas centers are
`module_center + (0,0,+/-250.25)` mm. This reproduces historical gas IDs exactly.
Historical cathode names were `Cathode_((j+2)*100+(i+12))`; their copy number
`i+37` repeats across Y and is not a unique module ID. Map those placements to
the gas-derived module index above; retain the current unique component naming
and `localCopy*75+module_id` convention rather than resurrecting duplicate copies.
Historical component/source-list ordering need not match the modern order;
historical fixed-seed trajectories are not a required reproduction target.

**cygno-5x5x3-v1:** preserve [common/DetectorGeometry.hh](../../common/DetectorGeometry.hh)
numerically, including arithmetic/placement ordering where it affects regression:

```text
ix=0..4, iy=0..4, iz=0..2        # nested loops; Z varies fastest
module_id = (ix*5+iy)*3+iz
center = ((ix-2)*504, (iy-2)*804, (iz-1)*2285.30) mm
VolumeNumber = side*75+module_id
```

IDs retain the same module/side semantics across layouts but generally identify
different world positions. Module 37 is at the origin in both. Layout identity
must accompany every reconstruction of `VolumeNumber`.

For code-compatible, complete local module bounds are
`(-250.145,-400.1275,-1140.65)` to `(250.075,400.660,1140.65)` mm.
The current Z pitch includes the optics plus a 4 mm envelope gap. Derive occupied
bounds from translated modules, not only the gas. Keep the 5 mm common copper
wall and baseline clearance formula: vessel outer half-sizes equal cathode-center
half-spans plus `(260,410,514.4)` mm. This gives:

| Profile | Vessel outer full size (mm) | World full size using baseline margin rule (mm) |
|---|---|---|
| legacy-25x3 | 12616 x 2428 x 1028.8 | 14000 x 3428 x 3281.3 |
| cygno-5x5x3-v1 | 2536 x 4036 x 5599.4 | 14000 x 5036 x 7851.9 |

Legacy values here are derived for the proposed profile. Samuele's fixed World
was 14000 x 3000 x 3000 mm; adopting the baseline 500 mm margin enlarges its Y/Z
extent without changing detector internals. World half-size minima remain
(7000,1500,1500) mm. Vessel containment means drift/GEM/cage components inside
the cavity, and no component crossing copper: outward optics intentionally sit
outside. In the 5x5x3 arrangement middle-layer optics are inside the common cavity.
Do not assert that the complete module envelope is inside the vessel.

Phase 1 acceptance: both profiles have 75 modules/150 sensitive volumes, all
module envelopes disjoint, every gas center/copy correct, all components inside
World, and no vessel-wall crossings. Test historical coordinates independently
against the formulas/reference entries above. Compare actual local solids,
materials and offsets between profiles; require the existing current-profile
geometry snapshot to remain numerically unchanged. Existing internal overlaps
must remain reported rather than silently fixed in A/B.

### Axis 2: detector-internal model

`code-compatible` means the current `74cc26f` internals, not an attempted return
to every old bug. Preserve all solids, materials, relative positions and
source-sampling behavior, including the existing same-event source-position fix.
The independent future `thesis-7.3` model must coexist with it.

| Item | Code-compatible | Thesis simulation specification / required follow-up |
|---|---|---|
| Cathode | 500 x 800 mm; 0.5 mm half-Z (1 mm total) | Same total thickness; gas boundary must use the full 0.5 mm half-Z |
| Gas | 500 mm drift each side; centers +/-250.25 mm | With cathode faces +/-0.5 mm, centers +/-250.5 mm; baseline overlaps each face by 0.25 mm |
| Field-cage support | 75 micrometre PMMA, translated Boolean shell | 75 micrometre acrylic; remove unintended misalignment only in thesis model |
| Copper bands | Four per side, 35 micrometre thickness, 55 mm drift extent; shifted Boolean shell | Five evenly spaced per side, 35 micrometres thick, 55 mm extent |
| Resistors | Al2O3; X/Y/Z = 1.6/0.55/3.2 mm; five per side, 750 total | 0.32 x 1.0 x 0.5 mm; between bands outside cage; exact axis assignment, end connections/count and positions unresolved |
| GEMs | Three per side, 500 x 800 mm; 50 micrometre outer box, shifted 5 micrometre cavity, separate 29 micrometre core | 40 micrometre acrylic core + 5 micrometre copper on each face; straightforward non-overlapping layers |
| Vessel | One copper shell, 5 mm wall | 10 mm copper wall; enclosure treatment for internal Z-layer optics unresolved |
| Lenses | Radius 10 mm (20 mm diameter), 2 mm thick; SiO2 at 2.65 g/cm3 | Diameter 10 mm, thickness 1 mm, Suprasil; material density needs supported provenance |
| Sensors | Silicon, 10.6 x 18.8 x 1 mm | 10.6 x 18.0 x 1 mm |
| Optics positions | Lens local Z +/-1080.15 mm, sensor +/-1140.15 mm; two cameras per side at Y +/-95 mm | Lens about 576 mm from GEMs, sensor 60 mm behind; exact GEM reference surface/transverse spacing not established by text |

The conceptual field-cage description on p. 183 says 50 mm bands and 50 mm
spacing; the explicit simulated design on p. 184 says five 55 mm bands. Use the
latter for the thesis model and record the distinction. Even spacing alone does
not fix end clearances. Historical 2 mm GEM separation is implementation evidence,
not a dimension stated in this extract. Do not infer new resistor counts or
precise placement/density values from the illustration alone. The text mentions
PMTs in the concept but excludes them from the listed simulated components and
Table 7.1; do not add a PMT background contribution to Figure 7.5's matrix.

### Axis 3: source policy and decay controls

[RadioactiveSourceSampler.cc](../../src/source/RadioactiveSourceSampler.cc) currently
selects one physical placement uniformly from its ordered component list, calls
`GetPointOnSurface()`, and moves along the inward normal by a uniform depth up to
the component's configured width. Translation is added last. This is the
`historical` policy for A/B, independent of layout; do not add containment
rejection or mass weighting silently. The baseline diagnostic finds 43/1000
GEM-copper and 247/1000 strip points outside their selected solid.

The thesis p. 188 describes a random element and a random point within its
volume; the existing policy does not establish that distribution. If a uniform
bulk sampler is implemented, give it an explicit separate policy ID, validate
both containment and distribution, and select the same policy for C/D. Layout
provides placements, while policy controls how to sample the selected solid.
Fresh single-worker processes and recorded seeds are required for controlled
runs: `/random/setSeeds` does not reset Geant4 11.4's separate solid-surface RNG
within an existing process; multiple workers add scheduling dependence.

Retain `QGSP_BIC_EMZ` plus `G4RadioactiveDecayPhysics`, ion recoil stopping,
`/rdecay01/fullChain`, and `/stopChain/ZStopDecay` / `AStopDecay` behavior for A/B.
Explicitly validate that long-lived primary/daughter decays are transported:
the installed environment reports a one-year very-long-decay threshold. A macro
that names U-238 is not sufficient evidence of a complete equilibrium chain.

## Processing and normalization audit

Reuse [SimpleProcessEvents.cpp](../../analysis/SimpleProcessEvents.cpp) and
[ProcessEvents.cc](../../analysis/ProcessEvents.cc). Current processing validates the
12 raw Hits branches, groups charged rows within event/process boundaries,
flushes at EOF, sums energy per volume, and retains first positions. This grouping
is a historical heuristic, not a verified ancestry reconstruction. `Nucleus`
follows the last tracked ion and is not itself a reliable ancestry label.

The processor checks the build geometry hash or an explicit unversioned-data
assumption, but only supports the current geometry. Raw simulation writes no
geometry metadata; processed files record `CygnoGeometry` and `CygnoLayout`.
The three normalized plotters and `PlotSpectrum.C` use a fixed current map and
do **not** call the geometry guard. Phase 2 must validate layout/model identity
before processing/plotting and reject conflicting assumptions. Prefer separate
run metadata, leaving raw Hits names/types/order unchanged; a runner-validated
manifest plus mandatory explicit profile is an acceptable fallback. The header
hash alone is insufficient to distinguish runtime layout choices.

Normalized spectra sum a group's electron/positron energy over volumes in keV;
the 20 mm fiducial inset tests the group's first saved position in its first
volume. Preserve that predicate within each layout comparison. `PlotSpectrum.C`
instead plots/cuts per volume; it is not an interchangeable normalization path.
The supported main normalized program uses 900 bins over 0-2000 keV; the two
variants use 1200. Current YZ position plots retain world Z and can overflow
for outer layers. Figure-style display ranges/units should be explicit: counts
per bin per year must be divided by bin width before labeling counts/keV/year.
Define energy-range integration/overflow conventions when adding the runner;
do not approximate a 10 keV threshold silently with a straddling histogram bin.

The current normalization input accepts only Bq/kg and a positive mass. Extend
the existing analysis for an explicit per-piece unit; do not disguise resistor
counts as kilograms. Normalize each physical submaterial separately before
summing `GEMsOuter + GEMsCore` into GEMs and `RingStrips + RingSupports` into
Field Cage. The other plot categories are Camera Lenses, Vessel, Camera Sensors,
Cathodes and Resistors. Each contribution uses activity x quantity x seconds/year
/ generated primaries: quantity is kg for Bq/kg or pieces for Bq/piece. Use actual
constructed quantities for each selected model/layout and record them; vessel
mass is layout-dependent. Preserve the current 365-day year (31,536,000 seconds),
documenting the thesis's rounded 3.15e7 seconds in Eq. 7.14.

## Published-source reconstruction requirements

Table 7.1 distinguishes nine physical contributions. These values establish the
Phase 3 transcription target; this is not yet the machine-readable study matrix:

| Material / components | U-238 | Th-232 | K-40 | Other | Unit |
|---|---|---|---|---|---|
| Acrylic / GEM core, cage support | 296e-6 | 56.9e-6 | 71.2e-6 | Upper limits used as values by thesis | Bq/kg |
| EFCu / GEM armor, cage strips, cathode, vessel | 0.131e-6 | 0.034e-6 | absent | Ra-226 and Th-228 in equilibrium | Bq/kg |
| Silicon / sensors | 2e-3 | 2.8e-3 | 9e-3 | Ra-226 and Th-228 in equilibrium | Bq/kg |
| Suprasil / lenses | 123e-6 | 40.7e-6 | 0.3e-3 | Ra-226 and Th-228 in equilibrium | Bq/kg |
| Al2O3 / resistors | 1e-6 | 0.14e-6 | 1.2e-6 | U-235 0.04e-6; Ra-226 0.18e-6; Th-228 0.13e-6 | Bq/piece |

Acrylic also assumes equilibrium for Ra-226/Th-228. All `x` entries are omitted.
Equilibrium rows simulate the full parent chain once; do not add separate
equilibrium Ra/Th jobs. Resistors require U-238 stopping before Ra-226 decay,
and a separate Ra-226 chain; Th-232 stopping before Th-228 decay, and a separate
Th-228 chain. U-235 and K-40 are additional resistor contributions. Encode
stop/restart nuclei explicitly and test daughter handling to avoid double counting.
This implies 26 component/chain-start contributions before any job subdivision.
The thesis states approximately 1e7 primaries per component/contaminant. Smoke
counts must be tiny, configurable and labeled as pipeline validation only.

Historical `analysis/PlotNormalizedSpectra.cpp` at `26ddbdb` uses ambiguous
GEMs/Rings labels, omits resistors, and disagrees with the thesis: e.g. vessel
U/Th/K activities are acrylic-like (296e-6/56.9e-6/71.2e-6 Bq/kg), sensors have
K-40 3.5 Bq/kg rather than 0.009, and lenses K-40 0.00031 rather than 0.00030.
Its masses (including vessel 1102.24 kg) and mixed 1e6/1e7 denominators do not
establish the published study's normalization. The separate GEMchain program
uses a U-235-only table; neither it nor `_single` resolves publication provenance.
Historical files remain quarantined references, not defaults.

The initial history audit located plotter changes at `0b0d1db`, `67239bd`,
`48b5b6a`, `f2ad08e`; it did not identify a Figure 7.5 release. Phase 3 must
inspect those inputs/history further and record unresolved provenance rather than
claiming absence of any matching historical version. The public single-daughter
generator includes Bi-212, Po-212 and Tl-208, but this alone establishes neither
correct branching weights nor a compatible historical Geant4/data environment.

Published Table 7.3 targets (no-cut / 2 cm cut, per year): Field Cage
313451/17738; GEMs 30540/1769; Resistors 12542/810; Cathodes 9293/196;
Camera Sensors 4278/1687; Vessel 1187/465; Camera Lenses 35/16. Table 7.2
quotes full-range totals 3.7e5/2.26e4, cut >10 keV 1.77e4, and cut 10-400 keV
1.76e4. Its no-cut 10-400 entry (3.3e5) exceeds its >10 entry (3.2e5): flag this
published inconsistency, do not force computed totals to match. No tuning scale
factors are permitted.

## Validation evidence and later gates

The unmodified baseline configured/built in `../../build/cygno-study` with
Geant4 11.4.2, ROOT 6.40.04, AppleClang 21.0.0 and Homebrew Python 3.14.7.
All five CTest groups passed in 34.28 s: source/mass, geometry, transport,
analysis and ROOT geometry. Logs and generated fixtures are outside the repository
under that build's `Testing/Temporary/LastTest.log` and `validation-results/`.
This suite checks current geometry, not the as-yet unimplemented legacy profile.
The geometry scan reports 48 inherited internal-overlap warnings; it is not an
overlap-free detector certification. The transport smoke produced 13,509 raw rows
for 20 Po-212 primaries. Raw hit counts are not generated-primary counts.

Commands used from the repository root:

```sh
source ../../software/geant4-11.4.2/bin/geant4.sh
cmake -S . -B ../../build/cygno-study -DCMAKE_BUILD_TYPE=Release \
  -DCYGNO_BUILD_ANALYSIS=ON -DPython3_EXECUTABLE=python3 \
  -DWITH_GEANT4_UIVIS=OFF
cmake --build ../../build/cygno-study --parallel 6
ctest --test-dir ../../build/cygno-study --output-on-failure
```

The known Bi-212 -> excited Pb-208 PART122 failure is documented in
[KNOWN_ISSUES.md](../KNOWN_ISSUES.md); the existing manual reproducer is
`python3 validation/run_checks.py bi212 ../../build/cygno-study`. It was not
rerun in Phase 0 and is deliberately outside passing CTest. Phase 9 must record
the exact effective Geant4/nuclear-data versions and test the complete Th-232
treatment. Do not alter data, suppress the failure, omit Bi-212 or invent daughter
branching weights. Failed chains must remain incomplete in resumable production.

Later phases add per-profile tests, the source matrix, the small resumable runner,
then smoke A/B, the separate thesis model, smoke C/D, preflight and final guide.
Preserve raw outputs and manifests with revision, layout, model, source policy,
physics/data environment, seeds, requested/generated counts and normalization
inputs. Reuse existing physics and analysis; completed valid production samples
must survive unrelated job failures. Phase 0 stops at this specification.
