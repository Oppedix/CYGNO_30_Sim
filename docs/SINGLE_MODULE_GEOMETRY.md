# Shared v4 detector geometry and materials

The single current detector model is **`cygno-copper-cathode-v4`**, default in
both internal and external modes. The shared builder is
`src/geometry/DetectorConstruction.cc`; millimetre dimensions and placement
formulas are in `common/DetectorGeometry.hh`. Source mode changes physics and
primary generation, never detector materials or geometry. External may add Cu20
shielding around this same detector. No internal source jobs enter external GPS.

## Solid copper cathode and Acrylic-core GEMs

Each module has **one `Cathode`**, a solid `G4_Cu` box 500 × 800 × 0.060 mm,
centred at the original module centre, with faces at local Z = ±0.030 mm.
It fills exactly the former sandwich envelope: position, external dimensions
and thickness are retained. There is no cathode PMMA/Polyimide core or separate
copper skin. Its entire mass is EFCu-assayed. This retained thickness is a
scientific assumption pending authoritative mechanical specification.

Only GEMs have 50 µm PMMA cores (`GEMsPolyimide`, stable source identifier) and
two 5 µm copper skins. Three GEMs per side: six cores and twelve skins/module.
Foil thickness is 0.060 mm, clear gas gap 2.000 mm, centre pitch 2.060 mm.
Core centres are local |Z| = 500.060, 502.120, 504.180 mm; the last outer face
is 504.210 mm. Non-sensitive He/CF4 fills the four transfer gaps. Sensitive
drift boxes are 500 × 800 × 500 mm, centred at local Z = ±250.030 mm.
Cathode, gas and first foil meet without overlap or extra copper.

## Constructed dimensions, material, mass and placements

The following masses use actual dimensions/densities; Boolean frame/vessel
masses are constructed `GetMass()` estimates, with export as authoritative.
There are 77 unrotated modules for `cygno-11x7-v1`.

| Component ID | Material; density g/cm³ | Shape/dimensions mm | Pieces/module; 11×7 | kg/piece; kg for 11×7 |
|---|---|---|---:|---:|
| Cathode | G4_Cu; 8.96 | box 500 × 800 × 0.060 | 1; 77 | 0.21504; 16.55808 |
| GEMsPolyimide | PMMA; 1.19 | box 500 × 800 × 0.050 | 6; 462 | 0.0238; 10.9956 |
| GEMsCopper | G4_Cu; 8.96 | box 500 × 800 × 0.005 | 12; 924 | 0.01792; 16.55808 |
| RingSupports | PMMA; 1.19 | outer 500.220 × 800.220 × 500, cut 500.070 × 800.070 × 510 | 2; 154 | ≈0.1157534; ≈17.8260 |
| RingStrips | G4_Cu; 8.96 | outer 500.070 × 800.070 × 10; cut 500 × 800 × 20, shifted −0.0175 in X/Y | 50; 3850 | ≈0.00818128; ≈31.49795 |
| Resistors | ResistorFusedSilica; 2.20 | box 1.6 × 0.55 × 3.2 | 52; 4004 | 6.1952e-6; 0.0248055808 |
| Lens | Silicon Dioxide; 2.65 | full cylinder radius 10, thickness 2 | 4; 308 | 0.0016650441064; 0.512833584772 |
| Sensors | G4_Si; 2.33 | box 10.6 × 18.8 × 1 | 4; 308 | 0.0004643224; 0.1430112992 |
| Vessel | G4_Cu; 8.96 | outer 5560 × 5644 × 1028.420; inner 5550 × 5634 × 1018.420 | shared; 1 | constructed shell mass in export |

PMMA is C5H8O2. Gas is retained He/CF4 60/40 by volume at the existing density
and state. Copper transport uses the existing NIST material, without any
radioactive primary generation in external mode. EFCu describes the source
assay, not a modified copper transport composition.

A module has **137 placements**: cathode1 + GEM core6/skin12 + transfer gas4 +
support2 + strip50 + resistor52 + lens4 + sensor4 + drift2. Including the shared
vessel and World gives **10,551** placements for 77 modules or **10,277** for
75 modules. Gas copies are `side*moduleCount+moduleID`.

## Retained cage, optics and enclosure

Each drift side has 25 copper bands of length 10 mm, separated by 24 clear
10 mm gaps with 5 mm endpoint half-gaps: 50% longitudinal copper fill.
Band centres are local |Z| = 10.030 + 20i mm, i=0…24. Twenty-six resistors
per side lie in the gap centres at |Z| = 2.530, 20.030, …, 480.030, 497.530 mm,
Y=400.385 mm. Supports are shifted −0.035 mm in X and −0.0175 mm in Y.
Strip placements retain the −0.0091 mm X shift. The retained small transverse
strip/gas and strip/support intersections remain documented limitations.

**Lens geometry and transport are unchanged.** Four/module, X=0, Y=±95 mm,
Z=±1080.210 mm, full Ø20 × 2 mm cylinder at 2.65 g/cm³. Sensors lie at
Z=±1140.210 mm with the same X/Y. The lens reference mass **3.843 kg is one
physical lens**, used only to convert the spreadsheet activities to Bq/piece.
`CYGNO_radioactivity_excel_suprasil` does not rescale these transport solids.

The single copper vessel has closed 5 mm walls, no optical apertures; planar
optics are outside. Current planar World is 14000 × 6644 × 3281.420 mm.
Module envelopes and pitches are unchanged, including 504/804 mm in X/Y and
2285.420 mm in Z for the three-plane layout. Layouts and bounds are in
[LAYOUT.md](LAYOUT.md); external [Cu20 shielding](EXTERNAL_SHIELDING.md) is separate.

## Export, assays and validation

`geometry_quantities` sums actual logical masses over actual source placements,
checks unique placements and matching component mass totals, and exports kg,
pieces, material, density and volume. `geometry.json` carries model, layout,
policy, compiled-source/geometry hashes and the actual gas map. Native and
Python analyses choose mass or pieces from each matrix row's unit.
See [source activities and provenance](STUDY_SOURCES.md).

`detector_v4` compares complete placement/material/solid audits between internal
and external (excluding the externally enlarged GPS World), checks masses/counts on all layouts and compares all non-cathode
parts against archived v3. Geometry checks enforce cathode/GEM/gas disjointness,
interfaces, envelope clearance and counts. GEM microscopic holes remain absent;
full solid foils are a transport approximation. Lens/sensor dimensions, vessel
wall and transverse cage alignment are retained assumptions, described in
[known issues](KNOWN_ISSUES.md). Old models are [historical only](history/DETECTOR_MODELS.md).
