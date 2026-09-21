//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.  It is provided  under  the terms  and *
// * conditions of the Geant4 Software License,  included in the file *
// * LICENSE and available at  http://cern.ch/geant4/license .  These *
// * include a list of copyright holders.                             *
// *                                                                  *
// * Neither the authors of this software system, nor their employing *
// * institutes,nor the agencies providing financial support for this *
// * work  make  any representation or  warranty, express or implied, *
// * regarding  this  software system or assume any liability for its *
// * use.  Please see the license in the file  LICENSE  and URL above *
// * for the full disclaimer and the limitation of liability.         *
// *                                                                  *
// * This  code  implementation is the result of  the  scientific and *
// * technical work of the GEANT4 collaboration.                      *
// * By using,  copying,  modifying or  distributing the software (or *
// * any work based  on the software)  you  agree  to acknowledge its *
// * use  in  resulting  scientific  publications,  and indicate your *
// * acceptance of all terms of the Geant4 Software license.          *
// ********************************************************************
//
/// \file DetectorConstruction.cc
/// \brief Build reusable component solids/materials, then place them in one shared module layout.
#include "cygno/geometry/DetectorConstruction.hh"
#include "G4Box.hh"
#include "G4Colour.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4PVPlacement.hh"
#include "G4SDManager.hh"
#include "G4SubtractionSolid.hh"
#include "G4SystemOfUnits.hh"
#include "G4Tubs.hh"
#include "G4UnitsTable.hh"
#include "G4VisAttributes.hh"

namespace geo = cygno::geometry;
namespace {
const auto& d = geo::module; // Shared values are mm; convert explicitly at Geant4 calls.
G4ThreeVector InGeant4Units(const geo::Point& point) {
  return G4ThreeVector(point.x*mm, point.y*mm, point.z*mm);
}
G4VisAttributes* SolidColour(const G4Colour& colour) {
  auto* attributes = new G4VisAttributes(colour);
  attributes->SetForceSolid(true);
  return attributes;
}
}

DetectorConstruction::DetectorConstruction() : G4VUserDetectorConstruction()
{
  const auto half = geo::WorldHalfSize();
  fWorldSize_x = 2*half.x*mm;
  fWorldSize_y = 2*half.y*mm;
  fWorldSize_z = 2*half.z*mm;
}
DetectorConstruction::~DetectorConstruction() = default;

G4VPhysicalVolume* DetectorConstruction::Construct()
{
  // Retain source lists across the application lifetime, rebuilding their contents
  // when Geant4 reconstructs geometry. Names resolve through its physical store.
  fListCathodes.clear(); fListGEMsOuter.clear(); fListGEMsCore.clear();
  fListSupportRings.clear(); fListRingStrips.clear(); fListResistors.clear();
  fListLens.clear(); fListSensors.clear(); fListDetector.clear();
  fMassMap = {{"Cathodes",0}, {"RingSupports",0}, {"RingStrips",0}, {"Resistors",0},
              {"GEMsOuter",0}, {"GEMsCore",0}, {"Vessel",0}, {"Lens",0}, {"Sensors",0}};
  fModuleLayout = geo::BuildModuleLayout();
  fMaterials = DefineMaterials();
  auto* world = BuildWorld();
  BuildCathodes();
  BuildGEMs();
  BuildFieldCage();
  BuildVessel();
  BuildOptics();
  BuildSensitiveGasVolumes();
  fPhysVolStore = G4PhysicalVolumeStore::GetInstance();
  for (const auto& entry : fMassMap)
    G4cout << "Mass of: " << entry.first << " = " << G4BestUnit(entry.second,"Mass") << G4endl;
  return world;
}

DetectorConstruction::Materials DetectorConstruction::DefineMaterials()
{
  G4NistManager* nist = G4NistManager::Instance();
  
  G4Material* Air =
    nist->FindOrBuildMaterial("G4_AIR"); 

  G4Material* Copper =
    nist->FindOrBuildMaterial("G4_Cu");

  //
  //defining Glass
  //

  G4double GlassDensity = 2.65*g/cm3;
  
  G4Material* Glass = new G4Material("Silicon Dioxide", GlassDensity, 2);

  Glass->AddElement(nist->FindOrBuildElement("Si"), 1);
  Glass->AddElement(nist->FindOrBuildElement("O"), 2);
  
  //
  //defining PMMA
  //

  std::vector<G4int> natoms;
  std::vector<G4String> elements;

  elements.push_back("C");     natoms.push_back(5);
  elements.push_back("H");     natoms.push_back(8);
  elements.push_back("O");     natoms.push_back(2);

  G4double PMMADensity = 1.190*g/cm3;

  G4Material* PMMA = nist->ConstructNewMaterial("PMMA", elements, natoms, PMMADensity);

  //
  //definition of Al2O3
  //

  G4Element* elAl = nist->FindOrBuildElement("Al");
  G4Element* elO = nist->FindOrBuildElement("O");
  
  G4Material* al2o3 = new G4Material("Al2O3", 3.97 * g/cm3, 2);
  al2o3->AddElement(elAl, 2);
  al2o3->AddElement(elO, 3);
    
  //
  //defining sensor material
  //

  G4Material* Silicon = nist->FindOrBuildMaterial("G4_Si");    

  //
  //defining detector gas mixture
  //

  G4double aHe = 4.002602*g/mole;
  G4Element* elHe = new G4Element("Helium","He", 2, aHe);
  
  G4double aC = 12.0107*g/mole;
  G4Element* elC = new G4Element("Carbon", "C", 6, aC);
  
  G4double aF=18.998*g/mole;
  G4Element* elF = new G4Element("Flourine"  ,"F" , 9., aF);

  // Partial gas densities are summed; AddMaterial below takes mass fractions.
  G4double He_frac = 0.6;
  G4double CF4_frac = 0.4;
  
  G4double densityHe = 162.488*He_frac*g/m3;
  G4double pressureHe = 1*He_frac*atmosphere;
  G4double temperatureHe = 300*kelvin;
  G4Material* He_gas = new G4Material("He_gas", densityHe, 1, kStateGas, temperatureHe, pressureHe);
  He_gas->AddElement(elHe, 1);

  //CF4_gas
  G4double densityCF4 = 3574.736*CF4_frac*g/m3;
  G4double pressureCF4 = 1*CF4_frac*atmosphere;
  G4double temperatureCF4 = 300*kelvin;
  G4Material* CF4_gas = new G4Material("CF4_gas", densityCF4, 2, kStateGas, temperatureCF4, pressureCF4);
  CF4_gas->AddElement(elC, 1);
  CF4_gas->AddElement(elF, 4);

  //CYGNO_gas
  G4double densityMix = He_gas->GetDensity()+CF4_gas->GetDensity();
  G4double pressureMix = He_gas->GetPressure()+CF4_gas->GetPressure();
  G4double temperatureMix = 300*kelvin;
  G4Material* CYGNO_gas = new G4Material("CYGNO_gas", densityMix, 2, kStateGas, temperatureMix, pressureMix);
  CYGNO_gas->AddMaterial(He_gas, He_gas->GetDensity()/densityMix*100*perCent);
  CYGNO_gas->AddMaterial(CF4_gas, CF4_gas->GetDensity()/densityMix*100*perCent);

  return {Air, Copper, Glass, PMMA, al2o3, Silicon, CYGNO_gas};
}

G4VPhysicalVolume* DetectorConstruction::BuildWorld()
{
  // A solid defines shape; the logical volume combines it with material.
  // Physical placements locate logical volumes inside a mother logical volume.
  auto* solid = new G4Box("World", fWorldSize_x/2, fWorldSize_y/2, fWorldSize_z/2);
  fWorldLogical = new G4LogicalVolume(solid, fMaterials.air, "World");
  return new G4PVPlacement(nullptr, G4ThreeVector(), fWorldLogical, "World", nullptr, false, 0);
}

G4VPhysicalVolume* DetectorConstruction::PlaceInModule(
    const geo::ModulePlacement& module, G4LogicalVolume* logical,
    const G4ThreeVector& localOffset, const G4String& namePrefix,
    G4int localCopy, std::vector<G4String>& sourceNames)
{
  // All module components remain direct World daughters, with no rotations or
  // extra mother material. This one translation rule applies even to the optics.
  const G4int copy = localCopy*geo::moduleCount + module.id;
  const G4String name = namePrefix + "_" + std::to_string(copy);
  auto* physical = new G4PVPlacement(nullptr, InGeant4Units(module.center)+localOffset,
                                    logical, name, fWorldLogical, false, copy);
  sourceNames.push_back(name);
  return physical;
}

void DetectorConstruction::BuildCathodes()
{
  // G4Box takes half lengths. Keep the historical Z half-length and sampling
  // depth; do not "correct" it to match neighboring offsets during this refactor.
  fCathodeWidth = d.cathodeHalfZ*mm;
  auto* solid = new G4Box("Cathode", d.cathodeX*mm/2, d.cathodeY*mm/2, d.cathodeHalfZ*mm);
  auto* logical = new G4LogicalVolume(solid, fMaterials.copper, "Cathode");
  logical->SetVisAttributes(SolidColour(G4Colour(0.6,0.4,0.2,0.0)));
  for (const auto& module : fModuleLayout) {
    fPhysicalCathodes = PlaceInModule(module, logical, {}, "Cathode", 0, fListCathodes);
    fMassMap["Cathodes"] += logical->GetMass();
  }
}

void DetectorConstruction::BuildGEMs()
{
  fGEMOuterWidth = (d.gemThickness-d.gemCavityThickness)*mm/2;
  fGEMCoreWidth = d.gemCoreThickness*mm/2;
  auto* outer = new G4Box("GEMOuter", d.gemX*mm/2, d.gemY*mm/2, d.gemThickness*mm/2);
  auto* cavity = new G4Box("GEMCore", d.gemCavityX*mm/2, d.gemCavityY*mm/2, d.gemCavityThickness*mm/2);
  // Preserve the hand-set Boolean translation and the different core/cavity
  // thicknesses. Their existing overlap is documented in KNOWN_ISSUES.md.
  auto* copperSolid = new G4SubtractionSolid("GEMSubSolid", outer, cavity, nullptr,
      G4ThreeVector(0,0,-d.gemCavityThickness*mm/2+d.gemCavityShiftFraction*(d.gemCavityThickness*mm/2)));
  auto* copperLogical = new G4LogicalVolume(copperSolid, fMaterials.copper, "logicGEM");
  copperLogical->SetVisAttributes(SolidColour(G4Colour(0.45,0.25,0.0,0.0)));
  auto* coreSolid = new G4Box("GEMInnner", d.gemCoreX*mm/2, d.gemCoreY*mm/2, d.gemCoreThickness*mm/2);
  auto* coreLogical = new G4LogicalVolume(coreSolid, fMaterials.pmma, "GEMInnerLogical");
  coreLogical->SetVisAttributes(SolidColour(G4Colour(1,1,1,0.0)));
  for (const auto& module : fModuleLayout) {
    for (G4int side=0; side<2; ++side) {
      const G4double sign = side == 0 ? 1 : -1;
      for (G4int layer=0; layer<d.gemLayers; ++layer) {
        const G4ThreeVector offset(0,0,sign*(d.cathodeHalfZ/2+d.driftLength
                                                 +layer*d.gemGap+d.gemThickness/2)*mm);
        const G4int localCopy = side*d.gemLayers+layer;
        auto* copper = PlaceInModule(module, copperLogical, offset, "GEM", localCopy, fListGEMsOuter);
        auto* core = PlaceInModule(module, coreLogical, offset, "GEMCore", localCopy, fListGEMsCore);
        if (side == 0) { fPhysicGEMsPlus=copper; fPhysicGEMsCorePlus=core; }
        else { fPhysicGEMsMinus=copper; fPhysicGEMsCoreMinus=core; }
        fMassMap["GEMsOuter"] += copperLogical->GetMass();
        fMassMap["GEMsCore"] += coreLogical->GetMass();
      }
    }
  }
}

void DetectorConstruction::BuildFieldCage()
{
  fRingSupportWidth=d.supportThickness*mm;
  fRingStripWidth=d.stripThickness*mm;
  fResistorWidth=d.resistorY*mm;
  auto* outerSupport = new G4Box("outerRingSupport",
      (d.gemX/2+d.supportThickness+d.stripThickness)*mm,
      (d.gemY/2+d.supportThickness+d.stripThickness)*mm, d.driftLength*mm/2);
  auto* innerSupport = new G4Box("innerRingSupport",
      (d.gemX/2+d.stripThickness)*mm, (d.gemY/2+d.stripThickness)*mm,
      (d.driftLength/2+d.booleanCutExtension)*mm);
  auto* supportSolid = new G4SubtractionSolid("solidRingSupport",outerSupport,innerSupport);
  auto* supportLogical = new G4LogicalVolume(supportSolid,fMaterials.pmma,"RingSupport");
  supportLogical->SetVisAttributes(SolidColour(G4Colour(1,1,0,0.4)));

  auto* outerStrip = new G4Box("outerRingStrip",(d.gemX/2+d.stripThickness)*mm,
                             (d.gemY/2+d.stripThickness)*mm,d.stripLengthZ*mm/2);
  auto* innerStrip = new G4Box("innerRingStrip",d.gemX*mm/2,d.gemY*mm/2,
                             (d.stripLengthZ/2+d.booleanCutExtension)*mm);
  auto* stripSolid = new G4SubtractionSolid("solidRingStrip",outerStrip,innerStrip,nullptr,
                                         G4ThreeVector(-d.stripThickness*mm/2,-d.stripThickness*mm/2,0));
  auto* stripLogical = new G4LogicalVolume(stripSolid,fMaterials.copper,"RingStrip");
  stripLogical->SetVisAttributes(SolidColour(G4Colour(0.5,0.5,0.5,0.4)));
  auto* resistorSolid = new G4Box("resistorShape",d.resistorX*mm/2,d.resistorY*mm/2,d.resistorZ*mm/2);
  auto* resistorLogical = new G4LogicalVolume(resistorSolid,fMaterials.alumina,"Resistor");

  for (const auto& module : fModuleLayout) {
    for (G4int side=0; side<2; ++side) {
      const G4double sign = side == 0 ? 1 : -1;
      auto* support = PlaceInModule(module,supportLogical,
          G4ThreeVector(-d.stripThickness*mm,-d.stripThickness*mm/2,sign*geo::GasOffsetZ()*mm),
          "RingSupport",side,fListSupportRings);
      if (side == 0) fPhysicRingsSupportPlus=support; else fPhysicRingsSupportMinus=support;
      fMassMap["RingSupports"] += supportLogical->GetMass();
      for (G4int ring=0; ring<d.stripCount; ++ring) {
        const G4double z=(ring+1)*geo::StripSpacing()+0.5*d.stripLengthZ+ring*d.stripLengthZ;
        auto* strip = PlaceInModule(module,stripLogical,
            G4ThreeVector(-d.stripShiftFractionX*d.stripThickness*mm,0,sign*z*mm),
            "RingStrip",side*d.stripCount+ring,fListRingStrips);
        if (side == 0) fPhysicRingStripsPlus=strip; else fPhysicRingStripsMinus=strip;
        fMassMap["RingStrips"] += stripLogical->GetMass();
      }
      for (G4int resistor=0; resistor<d.stripCount+1; ++resistor) {
        const G4double z=resistor*geo::StripSpacing()+0.5*d.stripLengthZ+resistor*d.stripLengthZ;
        const G4double y=d.cathodeY/2+d.supportThickness+d.stripThickness+d.resistorY/2;
        auto* physical = PlaceInModule(module,resistorLogical,G4ThreeVector(0,y*mm,sign*z*mm),
            "Resistor",side*(d.stripCount+1)+resistor,fListResistors);
        if (side == 0) fPhysicResistorsPlus=physical; else fPhysicResistorsMinus=physical;
        fMassMap["Resistors"] += resistorLogical->GetMass();
      }
    }
  }
}

void DetectorConstruction::BuildVessel()
{
  fVesselWidth=geo::vesselWall*mm;
  const auto half=InGeant4Units(geo::vesselOuterHalfSize);
  auto* outer = new G4Box("VesselOuterShape",half.x(),half.y(),half.z());
  auto* inner = new G4Box("VesselOuterShape",half.x()-fVesselWidth,
                         half.y()-fVesselWidth,half.z()-fVesselWidth);
  auto* solid = new G4SubtractionSolid("Vessel",outer,inner);
  // The old label said PMMA; the actual material has always been copper.
  auto* logical = new G4LogicalVolume(solid,fMaterials.copper,"Vessel");
  logical->SetVisAttributes(SolidColour(G4Colour(1,1,1,0.0)));
  fPhysicVessel = new G4PVPlacement(nullptr,{},logical,"Vessel",fWorldLogical,true,0);
  fMassMap["Vessel"] += logical->GetMass();
}

void DetectorConstruction::BuildOptics()
{
  fLensWidth=d.lensThickness*mm;
  fSensorWidth=d.sensorZ*mm;
  auto* lensSolid = new G4Tubs("Lens",0,d.lensRadius*mm,d.lensThickness*mm/2,0,360*deg);
  auto* lensLogical = new G4LogicalVolume(lensSolid,fMaterials.glass,"Lens");
  auto* sensorSolid = new G4Box("Sensor",d.sensorX*mm/2,d.sensorY*mm/2,d.sensorZ*mm/2);
  auto* sensorLogical = new G4LogicalVolume(sensorSolid,fMaterials.silicon,"Sensor");
  for (const auto& module : fModuleLayout) {
    for (G4int side=0; side<2; ++side) {
      const G4double sign = side == 0 ? 1 : -1;
      for (G4int camera=0; camera<2; ++camera) {
        const G4double y=(camera-0.5)*d.verticalLensSpacing/2;
        auto* lens = PlaceInModule(module,lensLogical,G4ThreeVector(0,y*mm,sign*geo::LensOffsetZ()*mm),
                                  "Lens",side*2+camera,fListLens);
        auto* sensor = PlaceInModule(module,sensorLogical,G4ThreeVector(0,y*mm,sign*geo::SensorOffsetZ()*mm),
                                    "Sensor",side*2+camera,fListSensors);
        if (side == 0) { fPhysicLensPlus=lens; fPhysicSensorsPlus=sensor; }
        else { fPhysicLensMinus=lens; fPhysicSensorsMinus=sensor; }
        fMassMap["Lens"] += lensLogical->GetMass();
        fMassMap["Sensors"] += sensorLogical->GetMass();
      }
    }
  }
}

void DetectorConstruction::BuildSensitiveGasVolumes()
{
  auto* solid = new G4Box("GasVolume",d.cathodeX*mm/2,d.cathodeY*mm/2,d.driftLength*mm/2);
  fLogicalGasVolume = new G4LogicalVolume(solid,fMaterials.gas,"GasVolume");
  fLogicalGasVolume->SetVisAttributes(SolidColour(G4Colour(0,0,1,0.2)));
  // Gas copy = side*75 + module ID. The side is local to each module's cathode.
  for (G4int side=0; side<2; ++side) {
    for (const auto& module : fModuleLayout) {
      const G4double sign = side == 0 ? 1 : -1;
      auto* gas = PlaceInModule(module,fLogicalGasVolume,G4ThreeVector(0,0,sign*geo::GasOffsetZ()*mm),
                               "GasVolume",side,fListDetector);
      const auto& center=gas->GetTranslation();
      G4cout << "detN " << gas->GetCopyNo() << "\t coord " << center.x()
             << " " << center.y() << " " << center.z() << G4endl;
    }
  }
}

void DetectorConstruction::ConstructSDandField()
{
  // Called on each worker. Geant4 keeps this logical volume's SD attachment
  // worker-local; do not store the SD in a shared DetectorConstruction pointer.
  auto* detector = new SensitiveDetector("SensitiveDetector");
  G4SDManager::GetSDMpointer()->AddNewDetector(detector);
  fLogicalGasVolume->SetSensitiveDetector(detector);
}

SensitiveDetector* DetectorConstruction::GetSensitiveDetector()
{
  return static_cast<SensitiveDetector*>(fLogicalGasVolume->GetSensitiveDetector());
}
