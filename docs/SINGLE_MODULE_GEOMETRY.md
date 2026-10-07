# Single-module geometry: final active 300ELJ model

“What is actually simulated now?” Model `cygno-300elj-v1`, source policy
`uniform-volume-v1`, canonical matrix `cygno-300elj-radioassay-v1`.
Layout is a separate identity; production configuration is `cygno-11x7-v1`.
Lengths below are millimetres unless explicitly marked µm. Exported quantities
were obtained with Geant4 11.4.2 and fixed Ranecu seed 12345 using the final
`geometry_quantities` build. Re-export for a different Geant4/data environment.

## Module and coordinates

X is the 500 mm foil direction, Y the 800 mm direction, and Z the drift axis.
The cathode mid-plane is local Z=0. Two back-to-back 500 mm sensitive drift
regions each lead to three GEM foils. One support frame, four copper strip
frames and five resistors serve each side. Two cameras per side each have one
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

Each module has **55 physical placements**: 3 cathode layers + 18 GEM layers +
4 transfer-gas boxes + 2 support frames + 8 strip frames + 10 resistors +
4 lenses + 4 sensors + 2 sensitive gas boxes. The 11×7 construction has
**4237 physical volumes**, including World and the common vessel.

## Constructed quantities

| Component | Transport material | Dimensions [mm] | Thickness [mm] | Pieces/module | Pieces/11×7 | kg/piece | kg/module | kg/11×7 | Source family | Assay provenance | Geometry status |
|---|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| Cathode centre | G4_KAPTON | 500 × 800 | 0.050 | 1 | 77 | 0.0284 | 0.0284 | 2.1868 | `CathodesPolyimide` | 300ELJ separate assay | Agreed stack |
| Cathode skin | G4_Cu | 500 × 800 | 0.005 | 2 | 154 | 0.01792 | 0.03584 | 2.75968 | `CathodesCopper` | Laminate-Cu separate assay | Agreed stack |
| GEM centre | G4_KAPTON | 500 × 800 | 0.050 | 6 | 462 | 0.0284 | 0.1704 | 13.1208 | `GEMsPolyimide` | 300ELJ separate assay | Agreed stack |
| GEM skin | G4_Cu | 500 × 800 | 0.005 | 12 | 924 | 0.01792 | 0.21504 | 16.55808 | `GEMsCopper` | Laminate-Cu separate assay | Agreed stack |
| Support frame | PMMA | 500.220 × 800.220 × 500 outer | 0.075 | 2 | 154 | 0.115753407853 | 0.231506815706 | 17.8260248094 | `RingSupports` | Table 7.1 Acrylic upper limits | Retained assumption |
| Copper strip frame | G4_Cu | 500.070 × 800.070 × 55 outer | 0.035 nominal | 8 | 616 | 0.0457477839711 | 0.365982271768 | 28.1806349262 | `RingStrips` | Table 7.1 EFCu | Retained asymmetric frame |
| Resistor | Al2O3 | 1.6 × 0.55 × 3.2 | 0.55 in Y | 10 | 770 | 1.117952e-05 | 0.0001117952 | 0.0086082304 | `Resistors` | Table 7.1 per piece | Retained assumption |
| Lens | Silicon Dioxide | Ø20 × 2 | 2 | 4 | 308 | 0.0016650441064 | 0.00666017642561 | 0.512833584772 | `Lens` | Table 7.1 Suprasil | Retained assumption |
| Sensor | G4_Si | 10.6 × 18.8 × 1 | 1 | 4 | 308 | 0.0004643224 | 0.0018572896 | 0.1430112992 | `Sensors` | Table 7.1 Silicon | Retained assumption |
| Common vessel | G4_Cu | 5560 × 5644 × 1028.42 outer | 5 | shared | 1 | 3833.06578552 | 49.7800751366 | 3833.06578552 | `Vessel` | Table 7.1 EFCu | Retained shell model |
| Sensitive drift gas | CYGNO_gas | 500 × 800 × 500 | 500 in Z | 2 | 154 | 0.30547744 | 0.61095488 | 47.04352576 | none | no bulk assay | Retained mixture |
| GEM transfer gas | CYGNO_gas | 500 × 800 × 2 | 2 in Z | 4 | 308 | 0.00122190976 | 0.00488763904 | 0.37634820608 | none | no bulk assay | Specified gas gap |

The vessel “kg/module” entry is an accounting allocation (total/77), not an
individual enclosure. Masses of source components are the actual sums of
`G4LogicalVolume::GetMass()/kg`; gas mass is calculated from the constructed
mixture density and box volume. Shell/frame masses retain Geant4's cached
Boolean-volume estimator, so they can differ slightly from exact analytic
box subtraction. No analytic mass correction is substituted in normalization.

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

Each Cu strip is outer box 500.070×800.070×55 minus inner box
500×800×65 translated `(-0.0175,-0.0175,0)` **inside the Boolean solid**.
Its physical placement adds `(-0.0091,0,±z)`. Hence actual walls are asymmetric:
17.5 µm on −X/−Y, 52.5 µm on +X/+Y. The nominal 35 µm parameter is not four
equal physical wall thicknesses. This offset geometry is retained exactly.

```cpp
auto* stripSolid = new G4SubtractionSolid("solidRingStrip",outerStrip,innerStrip,nullptr,
                                       G4ThreeVector(-d.stripThickness*mm/2,-d.stripThickness*mm/2,0));
```

There are four strips per side, at |Z| = 83.5, 194.5, 305.5, 416.5 mm.
`StripSpacing()=(500-4*55)/5=56 mm`. Longitudinal copper coverage is
**4×55/500 = 44%**. The current transverse offsets allow retained small
strip/support and strip/gas intersections; GEM/cathode fixes do not certify the
entire module as overlap-free. The unresolved mechanical geometry is not guessed.

## Resistors

`BuildFieldCage()` uses a 1.6×0.55×3.2 mm³ `G4Box` with Al2O3 at
3.97 g/cm³ (two Al and three O atoms). Five per side, ten/module, at X=0,
Y=400.385 and |Z|=27.5, 138.5, 249.5, 360.5, 471.5 mm. Every piece has the
same constructed mass. Source normalization uses **770 pieces**, not resistor kg.

```cpp
auto* resistorSolid = new G4Box("resistorShape",d.resistorX*mm/2,d.resistorY*mm/2,d.resistorZ*mm/2);
const G4double z=resistor*geo::StripSpacing()+0.5*d.stripLengthZ+resistor*d.stripLengthZ;
```

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

The canonical JSON preserves uncertainties but uses central values only.
No U235 assay is invented. U/Th full-chain/secular-equilibrium policy is retained;
K40 is one parent contribution. The six resistor contributions retain the
existing upper/lower segments, U235 and K40. Ra226/Th228 equilibrium daughters
of non-resistor parents are not separate jobs. Original `thesis-table7.1.json`
is preserved byte-for-byte as reference; the new matrix names its checksum and
copies only the unchanged cage, vessel, lens, sensor and resistor activities.
There are **31 contributions** derived from the schema: 12 layer + 3 support +
2 strip + 2 vessel + 3 lens + 3 sensor + 6 resistor, in seven reporting categories.
`GEMsPolyimide+GEMsCopper→GEMs`; `CathodesPolyimide+CathodesCopper→Cathodes`.

Normalization is unchanged:
`activity[Bq/kg]*constructed_mass[kg]*31536000/generated_primaries`, or
`activity[Bq/piece]*constructed_pieces*31536000/generated_primaries`.
Analysis uncertainties remain statistical group-count errors only; quoted assay
uncertainties are not a newly propagated systematic uncertainty model. Campaigns
record model, source policy, layout, geometry and compiled-source hashes; older
model/policy/hash records are rejected, not relabelled.

## Filling factors and unresolved current geometry assumptions

- GEM in-plane model fill: 100%; microscopic holes are absent. No physical hole fraction is inferred.
- Cage longitudinal Cu coverage: 44%; support transverse shell fraction `0.0004872602999` and strip transverse shell fraction `0.0002274604999`, derived from the implemented outer-minus-inner cross-sectional areas. The shifted strip changes wall distribution, not total cut area.
- Common vessel analytic shell-volume fraction: `0.01325613539` (1.325614%), computed as `1-(5550*5634*1018.42)/(5560*5644*1028.42)`; this is geometry, not porosity.

| Retained assumption | Exact active model | Unresolved physical evidence |
|---|---|---|
| Field cage | 4 strips/side, 44% coverage, shifted frames with small internal intersections | Thesis prose says 5 bands; mechanical truth independently unestablished |
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
| `config/study/cygno-300elj-radioassay-v1.json` | `provenance`, `contributions` | `"matrix_id": "cygno-300elj-radioassay-v1"`; `"assay_material": "300ELJPolyimide"`, `"activity_basis": "separate-material-assay"` |
| `app/geometry_quantities.cc` | `main` | `mass+=logical->GetMass();` checked against `GetComponentMasses()` and source-list sizes |
| `validation/check_geometry.py` | `check` | Independent sizes, foil interfaces, cathode/gas/GEM boundaries, layout IDs, World/vessel containment and module separation |
| `validation/source_checks.cc`, `validation/uniform_volume.cc` | `main` | 20000 placed samples/family/profile plus 100000 local samples/family, zero outside, analytic moments/ranges and rotated transform |

Run `geometry_quantities quantities.tsv cygno-11x7-v1 geometry.json` after
building. Run CTest and the Python suite; do not normalize failed radioactive
transport. [KNOWN_ISSUES.md](KNOWN_ISSUES.md) describes the independently observed
macOS Geant4 PART122 full-chain environment issue; no physics patch suppresses it.

Final local validation (macOS/arm64, Geant4 11.4.2, ROOT 6.40.04): 18/18
CTest checks passed; the full Python suite passed 55/55 with reference and
raw/compact transport checks enabled, without skips. Containment checks cover
20,000 placed points/family in each layout; the independent uniform-volume
check covers 100,000 local points/family plus 10,000 rotated-vessel samples.
The 11×7 exporter confirms all source counts/masses above. Against the saved
pre-change audit, 2,100 retained cage/resistor/lens/sensor placements have
identical names, copy IDs, solids, materials and X/Y positions. Z offsets and
vessel/World extents follow the updated laminate boundaries.

The standalone analysis compiles and passes full Python/ROOT numerical parity.
Its presentation regression confirms unchanged histogram bins/errors, TTree
counters and four original PNGs, while adding two total overlays and eight
range stacks, each PNG/PDF. The separate four-case decay preflight passes the
two U238 cases and fails Th232/Bi212 with PART122 in this local environment;
failed logs are retained and the production gate remains closed here.
