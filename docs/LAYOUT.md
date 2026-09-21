# The 5 × 5 × 3 detector layout

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
A component's copy number is `localCopy*75 + moduleId`; its physical name is
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

`analysis/DetectorGeometry.hh` converts `BuildModuleLayout()` / `GasCenter()` to
ROOT vectors. All four plotting sources use that adapter, including the exact
0.25 mm cathode offset. There is no separate 3 mm detector-gap parameter anymore.
The original 20 mm fiducial inset and all other cuts are unchanged.

To change the layout, edit `modulesX/Y/Z` and the named gap/pitch definitions in
`common/DetectorGeometry.hh`, then rebuild both simulation and analysis. The
component builders do not need their placement loops rewritten. The current
scheme handles translations only; adding rotations requires transforming both
local component coordinates and source sampling consistently.

The envelope formulas describe the current internals. If internals are explicitly
changed in a later study, recompute the envelope and update its checks too. Compile-
time assertions reject pitches smaller than these bounds. Validation expectations
currently assert the requested 75 modules and 150 gas cells; update those only
when intentionally changing the study configuration.

Do not apply this new center map to old 25 × 3 output. `VolumeNumber` has no layout
version encoded, and no metadata branch was added. Preserve the matching source
revision/configuration with every simulation and analysis dataset. Legacy YZ
position histograms still use world Z and their old range; outer-layer entries
can fall in overflow. Their interpretation has not been silently changed to
module-local Z.
