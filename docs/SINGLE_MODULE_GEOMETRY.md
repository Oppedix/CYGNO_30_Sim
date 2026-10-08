# Single-module geometry: final active 300ELJ model

Use this report for the final active v2 detector. “What is actually simulated now?” Model `cygno-300elj-v2`, source policy
`uniform-volume-v1`, canonical matrix `cygno-300elj-radioassay-v2`.
Layout remains `cygno-11x7-v1`; production configuration is
`config/study/cygno-11x7-v2.json`.
Lengths below are millimetres unless explicitly marked µm. Exported quantities
were obtained with Geant4 11.4.2 and fixed Ranecu seed 12345 using the final
`geometry_quantities` build. Re-export for a different Geant4/data environment.

## Module and coordinates

X is the 500 mm foil direction, Y the 800 mm direction, and Z the drift axis.
The cathode mid-plane is local Z=0. Two back-to-back 500 mm sensitive drift
regions each lead to three GEM foils. One support frame, 25 copper strip
frames and 26 resistors serve each side. Two cameras per side each have one
lens and one silicon sensor. All parts are direct World daughters; empty World
space is `G4_AIR`. The vessel is a single shared copper shell with no optical
apertures. In a planar layout the lenses and sensors are outside it.

```text
 -Z                              module z=0                              +Z
 sensors lens GEM3--2--GEM2--2--GEM1 | 500 drift | Cu5/PI50/Cu5 | 500 drift | GEM1--2--GEM2--2--GEM3 lens sensors
          [each GEM is 0.060 mm]                 [µm]                     [clear gap is 2.000 mm]
 cathode faces:                    -0.030, +0.030
 drift boundaries:       [-500.030,-0.030]          [0.030,500.030]
 GEM centres:       -(500.060,502.120,504.180)    +(500.060,502.120,504.180)
 final GEM outer faces:            ±504.210
 lens / sensor centres:            ±1080.210 / ±1140.210
```

The complete module envelope is `(-250.145,-400.1275,-1140.710)` to
`(250.075,400.660,1140.710)`. The 11×7 layout has 77 unrotated modules at
`((ix-5)*504,(iy-3)*804,0)`, with `ix=0..10`, `iy=0..6`, module ID `ix*7+iy`.
The origin module is ID 38. Gas copy ID is `side*77+moduleId`: 0–153, with side
0 at +Z and side 1 at −Z. Physical names are unique `Prefix_copy`; copy IDs
are unique within each family, not across families. The two other supported
layouts reuse exactly these module internals (see [LAYOUT.md](LAYOUT.md)).

Each module has **139 physical placements**: 3 cathode layers + 18 GEM layers +
4 transfer-gas boxes + 2 support frames + 50 strip frames + 52 resistors +
4 lenses + 4 sensors + 2 sensitive gas boxes. The 11×7 construction has
**10705 physical volumes**, including World and the common vessel.

## Constructed quantities

Boolean solid = outer primitive - translated inner primitive.
“Outer primitive/envelope” is only the bounding primitive used before subtraction.
It does NOT mean the entire stated box is filled with material. Simple boxes/slabs
have “—” in subtraction columns. All dimensions below are mm; material volumes
and masses are in the second table.

| Component | Transport material | Outer primitive/envelope | Subtracted inner primitive | Inner-cut translation | Resulting constructed solid | Physical wall/thickness/Z extent | Pieces/module | Pieces/11×7 |
|---|---|---|---|---|---|---|---:|---:|
| Cathode centre | G4_KAPTON | box 500 × 800 × 0.050 | — | — | solid slab | 50 µm Z | 1 | 77 |
| Cathode skin | G4_Cu | box 500 × 800 × 0.005 | — | — | solid slab | 5 µm Z | 2 | 154 |
| GEM centre | G4_KAPTON | box 500 × 800 × 0.050 | — | — | solid slab; no holes | 50 µm Z | 6 | 462 |
| GEM skin | G4_Cu | box 500 × 800 × 0.005 | — | — | solid slab; no holes | 5 µm Z | 12 | 924 |
| Support frame | PMMA | box 500.220 × 800.220 × 500 | box 500.070 × 800.070 × 510 | centered | open four-wall rectangular frame | nominal 75 µm transverse walls; 500 Z | 2 | 154 |
| Copper strip frame | G4_Cu | box 500.070 × 800.070 × 10 | box 500 × 800 × (10 + 2×5) | (−0.0175, −0.0175, 0) | hollow rectangular Cu ring/frame | 10 Z; walls 17.5/52.5 µm on −/+X and −/+Y | 50 | 3850 |
| Resistor | ResistorFusedSilica | box 1.6 × 0.55 × 3.2 | — | — | solid transport surrogate | 3.2 Z; 0.55 Y | 52 | 4004 |
| Lens | Silicon Dioxide | cylinder Ø20 × 2 | — | — | full cylinder | 2 Z | 4 | 308 |
| Sensor | G4_Si | box 10.6 × 18.8 × 1 | — | — | solid box | 1 Z | 4 | 308 |
| Common vessel | G4_Cu | box 5560 × 5644 × 1028.420 | box 5550 × 5634 × 1018.420 | centered | closed rectangular shell | 5-mm walls | shared | 1 |
| Sensitive drift gas | CYGNO_gas | box 500 × 800 × 500 | — | — | sensitive gas box | 500 Z | 2 | 154 |
| GEM transfer gas | CYGNO_gas | box 500 × 800 × 2 | — | — | non-sensitive gas box | 2 Z | 4 | 308 |

| Component | Density [g/cm³] | Material volume/piece [mm³] | kg/piece | kg/module | kg/11×7 | Source family | Assay provenance | Status/approximation | Construction source |
|---|---:|---:|---:|---:|---:|---|---|---|---|
| Cathode centre | 1.42 | 20000 | 0.0284 | 0.0284 | 2.1868 | `CathodesPolyimide` | Arnquist 1910.04317 Table 5, separate 300ELJ | agreed slab | `DetectorConstruction.cc::BuildCathodes` |
| Cathode skin | 8.96 | 2000 | 0.01792 | 0.03584 | 2.75968 | `CathodesCopper` | Arnquist 1910.04317 Table 5, separate Cu | agreed slab | `DetectorConstruction.cc::BuildCathodes` |
| GEM centre | 1.42 | 20000 | 0.0284 | 0.1704 | 13.1208 | `GEMsPolyimide` | Arnquist 1910.04317 Table 5, separate 300ELJ | agreed slab | `DetectorConstruction.cc::BuildGEMs` |
| GEM skin | 8.96 | 2000 | 0.01792 | 0.21504 | 16.55808 | `GEMsCopper` | Arnquist 1910.04317 Table 5, separate Cu | agreed slab | `DetectorConstruction.cc::BuildGEMs` |
| Support frame | 1.19 | 97271.7713051 | 0.115753407853 | 0.231506815706 | 17.8260248094 | `RingSupports` | Arnquist 2019 Table 1 p.7 Pre-3 (second set); K Table 7.1 proxy | retained transverse frame | `DetectorConstruction.cc::BuildFieldCage` |
| Copper strip frame | 8.96 | 913.089816217 | 0.0081812847533 | 0.409064237665 | 31.4979463002 | `RingStrips` | retained thesis Table 7.1 EFCu | retained transverse frame | `DetectorConstruction.cc::BuildFieldCage` |
| Resistor | 2.2 | 2.816 | 6.1952e-06 | 0.0003221504 | 0.0248055808 | `Resistors` | Anker Table 9 p.19; nEXO Table IV row 60 p.10 | effective completed-component assay on compact box | `DetectorConstruction.cc::BuildFieldCage` |
| Lens | 2.65 | 628.318530718 | 0.0016650441064 | 0.00666017642561 | 0.512833584772 | `Lens` | retained thesis Table 7.1 Suprasil | retained dimensions/material assumption | `DetectorConstruction.cc::BuildOptics` |
| Sensor | 2.33 | 199.28 | 0.0004643224 | 0.0018572896 | 0.1430112992 | `Sensors` | retained thesis Table 7.1 Silicon | retained dimensions/material assumption | `DetectorConstruction.cc::BuildOptics` |
| Common vessel | 8.96 | 427797520.705 | 3833.06578552 | 49.7800751366 | 3833.06578552 | `Vessel` | retained thesis Table 7.1 EFCu | retained dimensions/material assumption | `DetectorConstruction.cc::BuildVessel` |
| Sensitive drift gas | 0.0015273872 | 200000000 | 0.30547744 | 0.61095488 | 47.04352576 | none | no bulk assay | retained He/CF4 mixture | `DetectorConstruction.cc::BuildSensitiveGasVolumes` |
| GEM transfer gas | 0.0015273872 | 800000 | 0.00122190976 | 0.00488763904 | 0.37634820608 | none | no bulk assay | retained He/CF4 mixture | `DetectorConstruction.cc::BuildGEMs` |

The vessel kg/module entry is an accounting allocation (total/77), not a module
shell. Source masses, densities and volumes are exported from actual logical
volumes. Boolean volumes use Geant4's cached estimator; analytic subtraction
is a check, never a mass correction. Gas rows use the constructed mixture
density and exact box volumes. Bibliographic sample/row/page locators are in
[STUDY_SOURCES.md](STUDY_SOURCES.md) and the v2 matrix JSON.

## Cathode and gas interfaces

`common/DetectorGeometry.hh`, `ModuleDimensions` and `GasOffsetZ()`:

```cpp
double cathodePolyimideThickness = 0.050 * millimetre;
double cathodeCopperThickness = 0.005 * millimetre;
double cathodeTotalThickness = cathodePolyimideThickness + 2*cathodeCopperThickness;
double cathodeHalfThickness = cathodeTotalThickness/2;
constexpr double GasOffsetZ() { return module.cathodeHalfThickness + module.driftLength/2; }
```

`src/geometry/DetectorConstruction.cc`, `BuildCathodes()` constructs a
50 µm `G4_KAPTON` box centred at 0 and two independent 5 µm `G4_Cu` boxes at
Z=±0.0275. Their boundaries are `[-0.030,-0.025]`, `[-0.025,0.025]`,
`[0.025,0.030]`. They touch exactly without overlap. The polyimide transport
composition/density is NIST `G4_KAPTON`, approximately 1.42 g/cm³; the assay
is measured 300ELJ. Copper is never mixed into that transport material.

```cpp
const double z = (skin == 0 ? 1 : -1)*(d.cathodePolyimideThickness+d.cathodeCopperThickness)/2;
PlaceInModule(module, copper, {0,0,z*mm}, "CathodesCopper", skin, fListCathodesCopper);
```

`BuildSensitiveGasVolumes()` constructs two `G4Box` volumes, each
500×800×500 mm³, centred at local Z=±250.030. Their inner faces coincide with
the cathode outer faces and their far faces coincide with the first GEM inner
faces. Only these drift boxes are sensitive. Four additional He/CF4 boxes fill the two
2 mm GEM transfer gaps on each side; they are non-sensitive and have no source assay.

```cpp
auto* solid = new G4Box("GasVolume",d.cathodeX*mm/2,d.cathodeY*mm/2,d.driftLength*mm/2);
```

`DefineMaterials()` keeps He/CF4 partial fractions 0.6/0.4, temperature 300 K
and total pressure 1 atmosphere (101325 Pa). Partial densities are
`162.488*0.6` and `3574.736*0.4` g/m³. Total density is
**1527.3872 g/m³ = 1.5273872 kg/m³**; Geant4 `AddMaterial` uses their density
ratios as mass fractions (He≈6.383%, CF4≈93.617%), not 60/40 mass fractions.
CF4 has one C and four F atoms. The 154 sensitive boxes total 30.8 m³.

```cpp
G4double densityMix = He_gas->GetDensity()+CF4_gas->GetDensity();
CYGNO_gas->AddMaterial(He_gas, He_gas->GetDensity()/densityMix*100*perCent);
CYGNO_gas->AddMaterial(CF4_gas, CF4_gas->GetDensity()/densityMix*100*perCent);
```

## Triple-GEM system

Each foil is 500×800 mm², Cu5/300ELJ50/Cu5 µm. `BuildGEMs()` places six
polyimide boxes and twelve independent copper boxes per module. There is no
Boolean cavity/core construction and no microscopic hole pattern. The modelled
material fill factor in the foil plane is **100%**; a real perforation fraction
cannot be inferred without a hole diameter/pitch specification.

`common/DetectorGeometry.hh` separates clear transfer gap, foil thickness,
centre pitch and total stack thickness:

```cpp
constexpr double GEMCentrePitch() { return module.gemThickness + module.gemClearGap; }
constexpr double GEMStackThickness() {
  return module.gemLayers*module.gemThickness + (module.gemLayers-1)*module.gemClearGap;
}
constexpr double GEMInnerFaceZ() { return module.cathodeHalfThickness + module.driftLength; }
constexpr double GEMCentreZ(int layer) {
  return GEMInnerFaceZ() + module.gemThickness/2 + layer*GEMCentrePitch();
}
```

Clear spacing is 2.000 mm, centre pitch 2.060 mm and stack thickness 4.180 mm.
On +Z the foil intervals are `[500.030,500.090]`, `[502.090,502.150]`,
`[504.150,504.210]`; −Z is their mirror. Within every foil the Cu/PI/Cu
boundaries touch exactly. Copper skins have separate placement/source IDs.

```cpp
const double z = sign*geo::GEMCentreZ(layer);
const int foil = side*d.gemLayers+layer;
PlaceInModule(module, polyimide, {0,0,z*mm}, "GEMsPolyimide", foil, fListGEMsPolyimide);
const double offset = (skin == 0 ? 1 : -1)*(d.gemPolyimideThickness+d.gemCopperThickness)/2;
PlaceInModule(module, copper, {0,0,(z+offset)*mm}, "GEMsCopper", 2*foil+skin, fListGEMsCopper);
```

The two clear transfer regions per side are He/CF4 `CYGNO_gas`, centred at
|Z|=501.090 and 503.150, 500×800×2 mm³ each. They touch the adjacent foil
outer faces exactly and are non-sensitive; empty regions elsewhere still use
World air. `BuildGEMs()` implements:

```cpp
auto* transferGas = new G4LogicalVolume(new G4Box("GEMTransferGas",
    d.gemX*mm/2, d.gemY*mm/2, d.gemClearGap*mm/2), fMaterials.gas, "GEMTransferGas");
const double gapCentre=sign*(geo::GEMCentreZ(layer)+d.gemThickness/2+d.gemClearGap/2);
```

## Field cage: retained implemented solids

`BuildFieldCage()` retains PMMA support (1.190 g/cm³): outer box
500.220×800.220×500 minus a concentric 500.070×800.070×510 cut box. The cut
extends beyond both Z ends, leaving an open four-wall frame of 75 µm nominal
wall thickness. Physical offset is `(-0.035,-0.0175,±250.030)`.

```cpp
auto* supportSolid = new G4SubtractionSolid("solidRingSupport",outerSupport,innerSupport);
auto* supportLogical = new G4LogicalVolume(supportSolid,fMaterials.pmma,"RingSupport");
```

Each Cu strip is outer box 500.070×800.070×10 minus inner box
500×800×20 translated `(-0.0175,-0.0175,0)` **inside the Boolean solid**.
Its physical placement adds `(-0.0091,0,±z)`. Hence actual walls are asymmetric:
17.5 µm on −X/−Y, 52.5 µm on +X/+Y. The nominal 35 µm parameter is not four
equal physical wall thicknesses. This offset geometry is retained exactly.

```cpp
auto* stripSolid = new G4SubtractionSolid("solidRingStrip",outerStrip,innerStrip,nullptr,
                                       G4ThreeVector(-d.stripThickness*mm/2,-d.stripThickness*mm/2,0));
```

The agreed longitudinal design is:

```text
cathode |5 empty|10 Cu|10 empty|10 Cu| ... |10 Cu|5 empty| GEM
```

There are **25 Cu bands/side**, **50% longitudinal Cu fill**, and **26 resistor
intervals/side**. From the cathode-facing gas boundary, strip i=0..24 occupies
`[5+20*i,15+20*i]`, centred at `10+20*i` mm. Every internal gap is 10 mm;
end gaps are 5 mm. The exact local absolute centres are
`10.030,30.030,50.030,70.030,90.030,110.030,130.030,150.030,170.030,190.030,
210.030,230.030,250.030,270.030,290.030,310.030,330.030,350.030,370.030,
390.030,410.030,430.030,450.030,470.030,490.030` mm on both ±Z sides.
`StripCentreZ(i)` adds the derived cathode half-thickness to the gas-relative
centre. Static assertions enforce `2*5+25*10+24*10=500` and `25*10/500=0.5`.
The physical strip translation remains X=−0.0091, Y=0 mm. Existing small
transverse strip/support and strip/gas intersections remain unresolved; the
agreed longitudinal segmentation is no longer an open mechanical decision.

## Resistors: surrogate, reference hardware and normalization

The **simulated CYGNO surrogate** is a 1.6×0.55×3.2 mm³ solid fused-silica box,
`ResistorFusedSilica`, SiO2 at 2.20 g/cm³. It has 26 pieces/side, 52/module,
4004/11×7; X=0 and Y=400.385 mm, outside/on the existing support as implemented.
The material is separate from the 2.65 g/cm³ lens. NIST `G4_SILICON_DIOXIDE`
uses 2.32 g/cm³ in this installation; a separate nominal fused-silica definition
keeps the Suprasil approximation at 2.20 without changing optics.

`ResistorCentreFromGasStart(j)` gives 2.5 mm for j=0, `20*j` for j=1..24,
and 497.5 mm for j=25. Absolute local centres are
`2.530,20.030,40.030,60.030,80.030,100.030,120.030,140.030,160.030,180.030,
200.030,220.030,240.030,260.030,280.030,300.030,320.030,340.030,360.030,
380.030,400.030,420.030,440.030,460.030,480.030,497.530` mm on both sides.
Every ±1.6-mm resistor Z extent is strictly within its empty interval; no
longitudinal resistor/strip intersection is introduced.

The **assay reference hardware** is a 17-mm-long Heraeus Suprasil 300 tube,
6-mm OD, 4-mm ID, with approximately 300-nm phosphorus-doped amorphous-Si
coating deposited at 550 °C and Ti/Pd end metallization. See Anker section 3
p.5 and sections 4/6, Table 9 p.19; nEXO Table IV row 60 p.10.
The compact box is not mechanically identical to that reference part.

The **normalization policy** converts measured completed-component concentrations
into effective Bq/reference-piece using nominal mass
`π*((6/2)^2-(4/2)^2)*17*2.20*1e-6 = 0.000587477826221 kg`.
The approximately 300-nm aSi and nanometre Ti/Pd masses are omitted. Each
surrogate receives the same reference-piece activity, independent of its tiny
transport mass. This preserves measured component-level contamination without
obtaining an artificial reduction because the box is smaller. Most measured U/Th
is attributed to metallization/processing by Anker section 6 pp.18–19.
Uniform source location within the surrogate is an effective approximation:
the assay does not permit quantitative contamination partition among silica,
aSi and metallization. Equilibrium is a modelling assumption for ICP-MS U/Th
chain-head measurements, not experimentally proven. Exact conversions and
publication/sample correspondence are recorded in [STUDY_SOURCES.md](STUDY_SOURCES.md).

## Optics

`BuildOptics()` retains a full `G4Tubs` lens of radius 10 mm, diameter 20 mm
and thickness 2 mm, SiO2 stoichiometry and density 2.65 g/cm³. Four lenses/module,
at X=0, Y=±95 mm and Z=±1080.210 mm. Lens centre is 576 mm beyond the final
GEM outer face; closest lens surface is 575 mm beyond it. `LensOffsetZ()` derives
that distance from the completed stack.

```cpp
auto* lensSolid = new G4Tubs("Lens",0,d.lensRadius*mm,d.lensThickness*mm/2,0,360*deg);
constexpr double LensOffsetZ() { return GEMOuterFaceZ() + module.lensDistanceFromGEMs; }
```

Each sensor is 10.6×18.8×1 mm³ silicon (`G4_Si`, 2.33 g/cm³), four/module.
Centres are X=0, Y=±95, Z=±1140.210; centre-to-centre lens/sensor spacing is
60 mm. The lens assay is Suprasil; transport remains the retained SiO2-like
material, not an independently verified commercial lens composition.

```cpp
auto* sensorSolid = new G4Box("Sensor",d.sensorX*mm/2,d.sensorY*mm/2,d.sensorZ*mm/2);
constexpr double SensorOffsetZ() { return LensOffsetZ()+module.sensorDistanceFromLens; }
```

## Shared vessel and World

`BuildVessel()` constructs **one** centred copper box shell, outer dimensions
5560×5644×1028.420 mm³, inner 5550×5634×1018.420 mm³. Every wall is 5 mm.
Outer half-Z is final GEM face 504.210 + 10 mm; inner half-Z is 509.210,
leaving 5 mm beyond the last GEM. There are no vessel apertures. All drift,
GEM and cage pieces lie inside the cavity; planar optics are wholly outside,
without crossing the shell. Its exported mass is **3833.06578552 kg**.

```cpp
auto* inner = new G4Box("VesselOuterShape",half.x()-fVesselWidth,
                       half.y()-fVesselWidth,half.z()-fVesselWidth);
auto* solid = new G4SubtractionSolid("Vessel",outer,inner);
```

`BuildLayoutProfile()` derives vessel extents from module-centre spans and
`GEMOuterFaceZ()`. World is 14000×6644×3281.420 mm³, enlarged as necessary for
500 mm clearance and the retained minimum dimensions. Module pitches are
504/804 mm in X/Y and 2285.420 mm in Z for the three-plane profile.

## Radioactive sources and provenance

All ten source families are in the quantity table. Choose a physical placement
uniformly within the requested family; all its placements share one logical
solid/material (verified by tests). Then sample **uniformly in the actual
material volume**. `RadioactiveSourceSampler::SampleLocal()` uses uniform X/Y/Z
for boxes; uniform phi, `sqrt(r0²+(r1²-r0²)*U)` radius and uniform Z for cylinders;
and volume-weighted disjoint rectangular slabs for box-subtraction frames.
Boolean inner bounds include the actual displacement and are clipped to outer
bounds. Six peeled slabs partition a closed shell; the open cage frames need
only four. No thin-frame bounding-box rejection or surface-depth approximation
is used. Debug assertions and deterministic tests require `Inside()!=kOutside`.
The partition in `SampleLocal()` peels the lower/upper slabs on each axis:

```cpp
for (int axis=0; axis<3; ++axis) {
  auto lower=remaining, upper=remaining;
  lower.hi[axis]=inner.lo[axis]; upper.lo[axis]=inner.hi[axis];
  for (const auto& slab : {lower,upper}) if (slab.Volume()>0) {
    pieces.push_back(slab); volume+=slab.Volume();
  }
  remaining.lo[axis]=inner.lo[axis]; remaining.hi[axis]=inner.hi[axis];
}
```

The local point uses the physical OBJECT rotation plus translation to world
coordinates; current parts are direct World daughters. A rotated-vessel test
exercises this convention.

```cpp
return {volume->GetObjectRotationValue()*local+volume->GetObjectTranslation(),volume};
```

The researcher's specified layer assays agree with Table 5 of
[Arnquist et al., Ultra-low radioactivity Kapton and copper-Kapton laminates](https://arxiv.org/abs/1910.04317v1).
Whole laminate data are from Table 4 and are provenance only.

| Assayed sample | U238 [pg/g] | Th232 [pg/g] | natural K [ng/g] |
|---|---:|---:|---:|
| Separate 300ELJ polyimide | 5.58 ± 0.16 | 6.82 ± 0.09 | 108 ± 38 |
| Separate laminate copper | 12 ± 13 | 12 ± 12 | 130 ± 180 |
| Whole 300ELJ+Cu laminate, DuPont R&D | 8.6 ± 3.6 | 20 ± 14 | 164 ± 82 |

The measured laminate has 76.2 µm polyimide and two 17.0 µm copper layers, with
paper mass fractions 26%/74%. The independent cross-check is
`0.26*5.58+0.74*12=10.3308 pg/g U`,
`0.26*6.82+0.74*12=10.6532 pg/g Th`,
`0.26*108+0.74*130=124.28 ng/g K`; all are compatible with whole-laminate
measurements given the quoted uncertainties. The new 50/10 µm foil instead has
`50*1.42/(50*1.42+10*8.96)=44.2092%` polyimide and 55.7908% Cu by mass.
Whole-laminate activity must therefore never be assigned to its polyimide layer.
Concentrations are per material mass and are **not thickness-rescaled**.

`study/source_matrix.py`, `assay_activity()` uses the paper's section 2.2
conversion convention: U238 12400 Bq/g, Th232 4060 Bq/g, natural K 30.5 Bq/g
(the latter already includes K40 abundance). For pg/g multiply by `1e-9`,
for ng/g by `1e-6`, then by that specific activity to obtain Bq/kg. These
versioned constants avoid undocumented rounding or conversion conventions.
Natural-K conversions using 31.1 Bq/g would be about 2% higher than this paper
convention; the nominal matrix deliberately follows the paper consistently.

```python
return concentration * (1e-6 if isotope == 'K40' else 1e-9) * SPECIFIC_ACTIVITIES_BQ_G[isotope]
```

| Physical layer assay | U238 [Bq/kg] | Th232 [Bq/kg] | K40 [Bq/kg] |
|---|---:|---:|---:|
| 300ELJ polyimide | 6.9192e-5 | 2.76892e-5 | 3.294e-3 |
| Laminate copper | 1.488e-4 | 4.872e-5 | 3.965e-3 |

The canonical JSON retains reported uncertainties as provenance and uses nominal
central values. RingSupports adopts the radiopure solid PMMA U/Th design assay;
its unmeasured K stays the conservative old-K proxy. This is not a measured
batch identification for Samuele's original acrylic. Resistors have exactly
U238/Th232/K40 jobs with full-chain equilibrium assumed for U/Th and a single
K40 parent; no old Al2O3 U235/Ra226/Th228 or split-chain assays transfer.
`thesis-table7.1.json` and `cygno-300elj-radioassay-v1.json` remain unchanged
historical references. Production rejects v1 model/matrix products.
The schema derives **28 contributions**: 12 layer + 3 support + 2 strip +
2 vessel + 3 lens + 3 sensor + 3 resistor, in seven reporting categories.

Normalization is unchanged:
`activity[Bq/kg]*constructed_mass[kg]*31536000/generated_primaries`, or
`activity[Bq/piece]*constructed_pieces*31536000/generated_primaries`.
Analysis uncertainties remain statistical group-count errors only; quoted assay
uncertainties are not a newly propagated systematic uncertainty model. Campaigns
record model, source policy, layout, geometry and compiled-source hashes; older
model/policy/hash records are rejected, not relabelled.

## Filling factors and unresolved current geometry assumptions

- GEM in-plane model fill: 100%; microscopic holes are absent. No physical hole fraction is inferred.
- Cage longitudinal Cu coverage: 50%; support transverse shell fraction `0.0004872602999` and strip transverse shell fraction `0.0002274604999`, derived from the implemented outer-minus-inner cross-sectional areas. The shifted strip changes wall distribution, not total cut area.
- Common vessel analytic shell-volume fraction: `0.01325613539` (1.325614%), computed as `1-(5550*5634*1018.42)/(5560*5644*1028.42)`; this is geometry, not porosity.

| Retained assumption | Exact active model | Unresolved physical evidence |
|---|---|---|
| Field cage | 25 bands/side, 50% fill; shifted frames retain small transverse intersections | Transverse wall/alignment mechanics independently unestablished |
| Vessel | One common 5 mm Cu shell; optical systems can lie outside | Thesis prose says 10 mm; enclosure/shielding/optical paths need confirmation |
| Lens | Ø20×2 mm, SiO2-like | Thesis prose Ø10×1 mm |
| Sensor | 10.6×18.8×1 mm silicon | Thesis prose gives 18.0 mm in one dimension |

These components are preserved because inference from prose alone cannot establish
mechanical truth. No overlap claim is made for their retained transverse offsets.
The new cathode and GEM layers and gas interfaces are explicitly overlap-free.

## Code map and checks

| File | Function/struct | What to inspect |
|---|---|---|
| `common/DetectorGeometry.hh` | `ModuleDimensions`, `GasOffsetZ`, `GEMCentrePitch`, `GEMStackThickness`, `GEMCentreZ`, `LensOffsetZ`, `SensorOffsetZ` | Dimensions and interface formulas quoted above |
| `common/DetectorGeometry.hh` | `BuildModuleLayout`, `BuildLayoutProfile`, `GasCopyNumber` | `layout.push_back({ix*7+iy, ix,iy,0,{(ix-5)*modulePitchX,(iy-3)*modulePitchY,0}})`; `return side*count+moduleId;` |
| `src/geometry/DetectorConstruction.cc` | `DefineMaterials`, `BuildCathodes`, `BuildGEMs`, `BuildSensitiveGasVolumes` | Slabs, gas and density snippets above; `nist->FindOrBuildMaterial("G4_KAPTON")` |
| `src/geometry/DetectorConstruction.cc` | `BuildFieldCage` | Support, shifted-strip and resistor snippets above |
| `src/geometry/DetectorConstruction.cc` | `BuildOptics`, `BuildVessel`, `PlaceInModule` | Optics/shell snippets above; `copy=localCopy*fLayoutProfile.expectedModuleCount + module.id` |
| `src/source/RadioactiveSourceSampler.cc` | `SampleLocal`, `Sample`, `BoxBounds` | Exact material-volume partition and OBJECT transform quoted above |
| `study/source_matrix.py` | `assay_activity`, `expected_contributions`, `validate_matrix`, `quantity_for` | Conversion above; `return quantities[row['component']]['mass_kg' if unit == 'Bq/kg' else 'pieces']` |
| `config/study/cygno-300elj-radioassay-v2.json` | `provenance`, `contributions` | `"matrix_id": "cygno-300elj-radioassay-v2"`; `"assay_material": "300ELJPolyimide"`, `"activity_basis": "separate-material-assay"` |
| `app/geometry_quantities.cc` | `main` | `mass+=logical->GetMass();` checked against `GetComponentMasses()` and source-list sizes |
| `validation/check_geometry.py` | `check` | Independent sizes, foil interfaces, cathode/gas/GEM boundaries, layout IDs, World/vessel containment and module separation |
| `validation/source_checks.cc`, `validation/uniform_volume.cc` | `main` | 20000 placed samples/family/profile plus 100000 local samples/family, zero outside, analytic moments/ranges and rotated transform |

Run `geometry_quantities quantities.tsv cygno-11x7-v1 geometry.json` after
building. Run CTest and the Python suite; do not normalize failed radioactive
transport. [KNOWN_ISSUES.md](KNOWN_ISSUES.md) describes the independently observed
macOS Geant4 PART122 full-chain environment issue; no physics patch suppresses it.

Final v2 local validation, 2026-10-08 (macOS/arm64, Geant4 11.4.2,
ROOT 6.40.04): configure/build succeeded, 18/18 CTest checks passed, and
56/56 Python tests passed with both real C++/ROOT reference parity and
raw/compact transport enabled, without skips. All three notebooks were
regenerated and executed, including the constructed 77-module campaign path.
Containment covers 20,000 placed points/family in each layout; uniform-volume
checks cover 100,000 local points/family plus 10,000 rotated-vessel samples.
The 11×7 exporter confirms the counts, materials, densities, volumes and masses
above. A side projection of constructed placements confirms 25 bands and
26 resistor centres in the gaps. Against the saved v1 audit, all 2,851
unaffected physical placements (cathodes, GEMs, gas, supports, optics, vessel
and World) have identical placement/rotation/solid/material records.

The standalone C++ analysis compiles and passes Python/ROOT numerical parity;
presentation regression checks histogram bins/errors and counters. The fresh
four-case v2 decay preflight passes the two U238 cases and fails Th232/Bi212
with PART122 in this local environment. Failed logs are retained outside the
repository and the production gate remains closed here; no decay physics was
changed or failure suppressed.

## Material selection

The vessel remains EFCu: its constructed 3833.06578552 kg shell has U/Th
0.502131617903/0.130324236708 mBq. The same constructed volume at PMMA
density would weigh 509.079049639 kg; crossover limits are
0.986352941176/0.256 µBq/kg. Adopted Reynolds UVT PMMA at 9.05/5.05
µBq/kg fails both, and its K is unmeasured. Lower density is not lower background.
The helper-derived comparison and before/after support, strip and resistor
source activities are in [STUDY_SOURCES.md](STUDY_SOURCES.md#constructed-11×7-sanity-comparison-and-vessel-decision).
