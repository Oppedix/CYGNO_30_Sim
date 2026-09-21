// Export machine-readable placement/solid bounds and exercise every source list.
// Optional second argument "overlaps" runs Geant4 checks on the central module
// and common vessel. Existing INTERNAL overlaps are expected, not suppressed.
#include "cygno/geometry/DetectorConstruction.hh"
#include "cygno/source/PrimaryGeneratorAction.hh"
#include "G4Geantino.hh"
#include "G4RunManager.hh"
#include "G4PhysListFactory.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4VSolid.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"
#include <fstream>
#include <iomanip>
#include <map>
#include <set>
#include <sstream>

std::string SolidSignature(G4VSolid* solid) {
  std::ostringstream description, encoded;
  solid->StreamInfo(description);
  for (unsigned char c : description.str())
    encoded << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(c);
  return encoded.str();
}
int main(int argc, char** argv) {
  if (argc < 2) return 1;
  auto layout = cygno::geometry::LayoutId::Current5x5x3;
  bool overlaps = false;
  for (int i=2; i<argc; ++i) {
    const std::string arg = argv[i];
    if (arg == "overlaps") overlaps = true;
    else if (arg == "--layout" && i+1 < argc)
      layout = cygno::geometry::ParseLayoutId(argv[++i]);
    else return 1;
  }
  CLHEP::HepRandom::setTheEngine(new CLHEP::RanecuEngine);
  CLHEP::HepRandom::setTheSeed(12345);
  DetectorConstruction detector(layout);
  detector.Construct();
  static_cast<G4VUserDetectorConstruction&>(detector).ConstructSDandField();
  std::ofstream out(argv[1]);
  if (!out) return 1;
  out << std::setprecision(17);
  out << "name\tcopy\tlogical\tmaterial\tx\ty\tz\txmin\tymin\tzmin\txmax\tymax\tzmax\tsensitive\tshape\n";
  std::set<G4String> names;
  std::map<G4VSolid*,std::string> signatures;
  auto* store=G4PhysicalVolumeStore::GetInstance();
  for (auto* volume : *store) {
    if (!names.insert(volume->GetName()).second) return 2;
    auto* logical=volume->GetLogicalVolume();
    auto* solid=logical->GetSolid();
    G4ThreeVector min,max;
    solid->BoundingLimits(min,max);
    const auto p=volume->GetTranslation();
    if (!signatures.count(solid)) signatures[solid]=SolidSignature(solid);
    out << volume->GetName() << '\t' << volume->GetCopyNo() << '\t'
        << logical->GetName() << '\t' << logical->GetMaterial()->GetName() << '\t'
        << p.x()/mm << '\t' << p.y()/mm << '\t' << p.z()/mm << '\t'
        << min.x()/mm << '\t' << min.y()/mm << '\t' << min.z()/mm << '\t'
        << max.x()/mm << '\t' << max.y()/mm << '\t' << max.z()/mm << '\t'
        << (logical->GetSensitiveDetector() != nullptr) << '\t' << signatures[solid] << '\n';
    if (overlaps && (logical->GetName()=="Vessel" ||
        (std::abs(p.x()) < 1*mm && std::abs(p.y()) < 401*mm && std::abs(p.z()) < 1142*mm))) {
      if (logical->GetName() != "World") volume->CheckOverlaps(2000,0,true,5);
    }
  }
  const std::map<G4String,std::vector<G4String>> sources{
    {"Cathodes",detector.GetCathodesList()}, {"GEMsOuter",detector.GetGEMsOuterLists()},
    {"GEMsCore",detector.GetGEMsInnerLists()}, {"RingSupports",detector.GetRingsSupportList()},
    {"RingStrips",detector.GetRingStripstList()}, {"Resistors",detector.GetResistorList()},
    {"Lens",detector.GetLensList()}, {"Sensors",detector.GetSensorsList()}, {"Vessel",{"Vessel"}}};
  // Supply the normal particle-table readiness required by a primary action.
  // This harness samples positions only; it does not transport events.
  G4RunManager runManager;
  G4PhysListFactory factory;
  runManager.SetUserInitialization(factory.GetReferencePhysList("QGSP_BIC_EMZ"));
  G4Geantino::GeantinoDefinition();
  PrimaryGeneratorAction generator(&detector);
  for (const auto& source : sources) {
    std::set<G4String> unique;
    for (const auto& name : source.second)
      if (!unique.insert(name).second || !store->GetVolume(name,false)) return 3;
    for (int sample=0; sample<100; ++sample) {
      auto p=generator.GetPointOnDetectorElement(source.first);
      if (!std::isfinite(p.x()) || !std::isfinite(p.y()) || !std::isfinite(p.z())) return 4;
    }
    G4cout << "SOURCE_OK " << source.first << " " << unique.size() << G4endl;
  }
  return out ? 0 : 1;
}
