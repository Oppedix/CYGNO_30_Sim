# Detector layout profiles

The principal study profile is **legacy-25x3**. Three runtime profiles use the same **code-compatible** module internals and
historical source sampler. Select a profile before geometry construction:

```sh
/path/to/build/rdecay01 /absolute/path/to/run.mac 1 --layout legacy-25x3
/path/to/build/rdecay01 /absolute/path/to/run.mac 1 --layout cygno-5x5x3-v1
/path/to/build/rdecay01 /absolute/path/to/run.mac 1 --layout cygno-11x7-v1
```

The option also works before the macro. Omitting it retains `cygno-5x5x3-v1`;
unknown or duplicate layout options fail before initialization. `--help` prints
usage. With no macro the viewer uses the selected layout. Use separate working
directories for runs and retain the command and log: the application prints
layout, detector model and source policy at startup. The raw Hits schema is
unchanged. Processing and all plotters reconstruct each profile from validated
layout/model metadata; conflicting assumptions are rejected.

`common/DetectorGeometry.hh` provides `LayoutId`, `ParseLayoutId`,
`BuildModuleLayout(id)` and `BuildLayoutProfile(id)`. The profile supplies the
ordered placements and IDs, expected count, complete occupied bounds and derived
vessel/World half-sizes. `GasCenter` and `GasCopyNumber` reconstruct its sensitive
volumes. `DetectorConstruction` takes an immutable layout ID and uses the existing
component builders; there is no duplicate construction class or source policy.
The unqualified constants and no-argument helpers retain the current profile.

## Historical 25 × 3 profile

`legacy-25x3` reproduces the center ordering in Samuele's `26ddbdb` gas/cathode
loops: outer `i=-12..12`, inner `j=-1..1`, center `(i*504,j*804,0)` mm and module
ID `3*(i+12)+(j+1)`. Thus all 75 cathodes share Z=0; each module contains its
own positive/negative drift regions. Gas copy `side*75+moduleId` reproduces the
historical gas counter exactly. All profiles retain the current unique component
copy/name scheme. Samuele's repeated cathode copy `i+37` is not reused; see the
[exact mapping](history/BACKGROUND_EXPERIMENT.md#axis-1-module-layout) and independent
[75-center fixture](../validation/references/legacy-25x3-centers.tsv).

The legacy occupied bounds are (-6298.145,-1204.1275,-1140.65) to
(6298.075,1204.660,1140.65) mm. Its one common vessel has full outer dimensions
12616 × 2428 × 1028.8 mm, with the same 5 mm copper wall. World is
14000 × 3428 × 3281.3 mm, enlarged from Samuele's 14000 × 3000 × 3000 mm by the
current 500 mm margin rule. The drift/GEM/cage components fit inside the cavity;
the optics sit outside, with no wall crossings. Vessel mass changes with layout
and must be read from the constructed geometry for normalization.

Module IDs preserve ordering/side semantics, not world coordinates, across
the two 75-module layouts. They both have module 37 at the origin; the 11x7 profile has module 38. No sampler RNG draws or internal
dimensions changed. This does not promise trajectory equality to Samuele's
historical executable.

## Planar 11 × 7 comparison profile

`cygno-11x7-v1` deliberately contains **77 modules** in one Z plane. The
unrotated 500 mm short module dimension is along X, and the 800 mm long dimension
is along Y. Pitches remain 504 mm and 804 mm respectively. For `ix=0..10`,
`iy=0..6`, `iz=0`:

```text
moduleId = ix*7 + iy                     # 0..76, Y fastest
center = ((ix-5)*504, (iy-3)*804, 0) mm
central module = 38 at (0,0,0)
gasCopy = side*77 + moduleId             # side 0: 0..76; side 1: 77..153
gas center = module center + (0,0,side == 0 ? 250.25 : -250.25) mm
```

There are 154 gas cells and `77*43 + World + Vessel = 3313` physical placements.
The complete occupied bounds are **(-2770.145,-2812.1275,-1140.650)** to
**(2770.075,2812.6600,1140.650)** mm. The occupied XY aspect ratio Y/X is about
1.0153. These values follow the existing envelopes and vessel/World formulas;
they are independent numerical test contracts, not production overrides.

| Layout | Grid X × Y × Z | Modules / gas cells | Occupied full spans (mm) | Vessel outer full size (mm) | World full size (mm) |
| --- | --- | --- | --- | --- | --- |
| legacy-25x3 | 25 × 3 × 1 | 75 / 150 | 12596.220 × 2408.7875 × 2281.300 | 12616 × 2428 × 1028.8 | 14000 × 3428 × 3281.3 |
| cygno-5x5x3-v1 | 5 × 5 × 3 | 75 / 150 | 2516.220 × 4016.7875 × 6851.900 | 2536 × 4036 × 5599.4 | 14000 × 5036 × 7851.9 |
| cygno-11x7-v1 | 11 × 7 × 1 | 77 / 154 | 5540.220 × 5624.7875 × 2281.300 | 5560 × 5644 × 1028.8 | 14000 × 6644 × 3281.3 |

The new vessel half-size is `(2780,2822,514.4)` mm; World half-size is
`(7000,3322,1640.65)` mm. All envelopes are disjoint, non-optical components
are in the vessel cavity, no components cross the wall, and all fit inside World.
Inherited overlaps inside individual modules remain unchanged.

This topology is very similar to Samuele's 25 × 3 × 1: both use one plane,
identical module orientation, local/camera geometry, pitches and source sampler,
with no module rotations. They are **not scientifically identical**. There are
77 versus 75 modules, 154 versus 150 gas cells, component copy strides of 77
versus 75, and different vessel dimensions/mass, component quantities and source
placement populations. Different normalized total backgrounds are expected.

Use [cygno-11x7-v1.json](../config/study/cygno-11x7-v1.json) for this comparison.
[samuele.json](../config/study/samuele.json) remains the principal legacy reference.
Both use the unchanged Table 7.1 activities, model, sampler policy, RDM threshold
and canonical primary default. Masses and piece counts come from actual
`geometry_quantities` construction, never historical normalization constants.
Source counts are Cathodes 77, GEMsOuter 462, GEMsCore 462, RingSupports 154,
RingStrips 616, Resistors 770, Lens 308, Sensors 308 and Vessel 1.

Python raw, compact and both analysis consume the campaign's 154 exported gas
centers and constructed quantities. Gas copy 153 is valid and 154 is invalid;
150 remains invalid in either 75-module profile. No analysis assumes that module
37 is central. The three notebooks retain their intentionally synthetic legacy
teaching fixtures; the common walkthrough's real-campaign branch is tested with
constructed 11x7 geometry/quantities and synthetic both-mode events at cell 153.
This software test does not replace the real decay preflight.

The normal viewer is `(cd "$CYGNO_BUILD" && ./rdecay01 --layout cygno-11x7-v1)`.
For a face-on inspection, execute `/vis/viewer/set/viewpointThetaPhi 0 0` in its
UI and hide World/Vessel if needed. The optional
[offscreen macro](../config/vis-11x7-offscreen.mac) provides these visibility
settings without altering geometry. Copy it as `vis.mac` to a separate working
directory, then launch the executable there without a batch macro. Inspect 11 X
columns, 7 Y rows, one Z plane, a nearly square footprint, consistent orientations,
and no missing/duplicate modules. A human viewer review remains a release gate.

## Current 5 × 5 × 3 profile (unchanged numerical baseline)

This layout was already present at baseline `05a2b92`. References below to the
old layout describe the earlier 25 × 3 → 5 × 5 × 3 migration, not this recovery.
The current refactor preserves all geometry numerically.

## Definition and assumptions

`common/DetectorGeometry.hh` contains the shared dimensions, layout and copy-number
functions, without depending on Geant4 or ROOT. Values in it are millimetres;
Geant4 converts them explicitly with `*mm`. No material definition moved into this
header. All 75 modules retain their previous orientation and internal components.

The original module extends much farther along Z than its two drift volumes:
its sensors lie at local Z = ±1140.15 mm and are 1 mm thick. The envelope was
measured from every original physical placement, including Boolean supports,
strips, resistors and both optical systems, before choosing the new Z pitch.

| Axis | Complete local minimum (mm) | Complete local maximum (mm) | Envelope span (mm) | Center pitch (mm) | Envelope gap (mm) |
| --- | ---: | ---: | ---: | ---: | ---: |
| X | -250.145 | 250.075 | 500.220 | 504 | 3.780 |
| Y | -400.1275 | 400.6600 | 800.7875 | 804 | 3.2125 |
| Z | -1140.650 | 1140.650 | 2281.300 | 2285.300 | 4.000 |

X/Y pitches retain the original cathode widths plus a nominal 4 mm gap. Their
actual complete-envelope gaps are slightly smaller because the field cage and
resistors protrude beyond the cathode. Z pitch is the full two-sided module depth
plus **4 mm**, an explicit spacing assumption rather than a reduced drift/optical
distance. The extra Z space is necessary to avoid colliding opposing sensors.
All module envelopes are disjoint; existing overlaps *within* each module remain.

For indices `ix=0..4`, `iy=0..4`, `iz=0..2`:

```text
moduleId = (ix*5 + iy)*3 + iz             # 0..74, Z fastest
center.x = (ix - 2)*504 mm
center.y = (iy - 2)*804 mm
center.z = (iz - 1)*2285.30 mm
component position = center + original local component offset
```

There are five X positions, five Y positions and three Z positions. The module
at the origin is ID 37. Each module contains 43 physical placements, including
its two gas cells. Together with World and the common vessel this gives 3,227
physical volumes, including 150 sensitive placements.

## Components and IDs

Every module component passes through `DetectorConstruction::PlaceInModule`.
A component's copy number is `localCopy*moduleCount + moduleId` (stride 75 in
the two existing profiles, 77 in 11x7); its physical name is
`Prefix_copy`. Names are unique across the physical-volume store. Copy numbers
are unique within a family, not across families. World and Vessel remain
singletons with copy 0. Logical and solid names retain their existing definitions.

| Name prefix | Local copy convention | Placements per module |
| --- | --- | ---: |
| `Cathode` | 0 | 1 |
| `GEM`, `GEMCore` | `side*3 + layer`, layer 0..2 | 6 each |
| `RingSupport` | side | 2 |
| `RingStrip` | `side*4 + strip`, strip 0..3 | 8 |
| `Resistor` | `side*5 + resistor`, resistor 0..4 | 10 |
| `Lens`, `Sensor` | `side*2 + camera`, camera 0: Y=-95 mm, camera 1: Y=+95 mm | 4 each |
| `GasVolume` | side | 2 |

Side 0 means local +Z and side 1 means local -Z, relative to the cathode in the
same module. GEM layer 0 is nearest the cathode. The `VolumeNumber` output branch
continues to identify a physical sensitive gas cell:

```text
side = VolumeNumber / 75                  # integer division
moduleId = VolumeNumber % 75
ix = moduleId / 15
iy = (moduleId / 3) % 5
iz = moduleId % 3
gas center = module center + (0, 0, side == 0 ? 250.25 : -250.25) mm
```

The source-name lists are filled by actual placements, so every supported
contaminated component remains addressable through `G4PhysicalVolumeStore`.
The valid source-selection probabilities and surface/depth sampler are unchanged.
The layout, names and list ordering have changed; the same seed is not expected
to select the same historical module or give identical world-coordinate hits.

## Common vessel and World

The old design had **one copper shell**, not an individual enclosure per module.
This remains the design assumption. Its 5 mm wall and original clearance formulas
are preserved, while its outer extents follow the outer drift/GEM array:

| Volume | Full X × Y × Z extent (mm) |
| --- | --- |
| Vessel outside | 2536 × 4036 × 5599.4 |
| Vessel cavity | 2526 × 4026 × 5589.4 |
| World | 14000 × 5036 × 7851.9 |

The vessel has no holes; its material remains copper, despite an old PMMA label.
Middle-layer optics now lie inside the common cavity, and the outward-facing
optics of the outer Z layers remain outside the shell. No component crosses its
wall. This changes vessel area/mass and shielding paths as a necessary consequence
of the requested arrangement. It does not reproduce 75 separately enclosed
modules. The shell mass is approximately **4203.49 kg** in this configuration.

World retains its previous minimum half sizes and grows where needed to leave
at least 500 mm around the array or vessel. All components remain World daughters,
so empty space retains the same air material; no new gas mother volume is inserted.

Historical normalization constants were preserved as unverified reference tables;
active plotters now require explicit study configurations. In particular,
a historical vessel mass cannot be assumed valid for this resized shell. Review
vessel normalization before a new production background comparison; use the
same normalization formula with an explicitly approved mass for that study.

## Shared analysis geometry and future changes

`analysis/reference_cpp/DetectorGeometry.hh` converts `BuildModuleLayout(layout)` / `GasCenter()` to
ROOT vectors. All four plotting sources use that adapter, including the exact
0.25 mm cathode offset. There is no separate 3 mm detector-gap parameter anymore.
The original 20 mm fiducial inset and all other cuts are unchanged.

Select the three supported layouts with `--layout`; do not edit module counts to
switch studies. New profiles would need their own explicit ID and validation.
The scheme handles translations only; adding rotations requires transforming
both local component coordinates and source sampling consistently.

The envelope formulas describe the current internals. If internals are explicitly
changed in a later study, recompute the envelope and update its checks too. Compile-
time assertions reject pitches smaller than these bounds. Validation expectations
assert independent 75/150 and 77/154 contracts for their respective profiles.

`VolumeNumber` has no layout version encoded. A separate `RunMetadata` tree now
identifies layout, model and source policy without changing any Hits branches.
Unversioned 25 × 3 files require verified source provenance and explicit layout
and model assumptions; see [analysis](ANALYSIS.md). Preserve the matching source
revision/configuration with every simulation and analysis dataset. Legacy YZ
position histograms still use world Z and their old range; outer-layer entries
can fall in overflow. Their interpretation has not been silently changed to
module-local Z.

## Adding a future layout

Add future IDs and ordered centers in the shared layout provider, keeping a
single detector constructor and analysis adapter.
The profile count is derived from its placements; construction copy strides and
the ROOT map consume that count. Processing derives the valid gas count from the
selected profile. Update the Python `LAYOUT_MODULE_COUNTS` validation contract and
independent layout fixtures at the same time. Both current 75-module profiles keep
the exact `side*75 + moduleId` numbering. Default no-argument helpers retain the
75-module compatibility layout. Rotations would require an explicit transform
contract; do not silently reinterpret centers or copy IDs as orientations.

The Phase 1–6 geometry-header fingerprint remains accepted only for the two original
75-module layouts: the finalization changed count plumbing only, with the same placement
snapshots, geometry, materials and local offsets. Unsupported model IDs are rejected.

The 11x7 addition produces a new geometry-header hash. No historical hash is
accepted as the identity of this new profile.
