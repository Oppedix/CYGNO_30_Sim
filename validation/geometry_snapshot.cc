// Dump geometry in construction order for exact before/after comparisons.
// No events or physics list are needed; output goes to the requested file.
#include "cygno/geometry/DetectorConstruction.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4SolidStore.hh"
#include "G4VSolid.hh"
#include "Randomize.hh"

#include <fstream>
#include <iomanip>
#include <map>

int main(int argc, char** argv)
{
  if (argc != 2 && argc != 3) return 1;
  std::ofstream out(argv[1]);
  if (!out) return 1;
  CLHEP::HepRandom::setTheEngine(new CLHEP::RanecuEngine);
  CLHEP::HepRandom::setTheSeed(12345);
  DetectorConstruction detector(argc == 3 ? cygno::geometry::ParseLayoutId(argv[2])
                                           : cygno::geometry::LayoutId::Current5x5x3);
  detector.Construct();
  // Invoke the public base interface (the override is private).
  static_cast<G4VUserDetectorConstruction&>(detector).ConstructSDandField();
  out << std::setprecision(17);
  std::map<G4String, int> counts;
  int sensitiveCount = 0;
  for (const auto* volume : *G4PhysicalVolumeStore::GetInstance()) {
    const auto* logical = volume->GetLogicalVolume();
    const bool sensitive = logical->GetSensitiveDetector() != nullptr;
    ++counts[logical->GetName()];
    sensitiveCount += sensitive;
    out << "placement " << volume->GetName() << ' ' << volume->GetCopyNo()
        << ' ' << volume->GetObjectTranslation() << ' '
        << volume->GetObjectRotationValue() << ' ' << logical->GetName()
        << ' ' << logical->GetSolid()->GetName() << ' '
        << logical->GetMaterial()->GetName() << ' ' << sensitive << ' '
        << (volume->GetMotherLogical() ? volume->GetMotherLogical()->GetName() : "none")
        << '\n';
  }
  for (const auto* solid : *G4SolidStore::GetInstance()) {
    solid->StreamInfo(out); // Includes constituent solids and Boolean offsets.
    out << std::setprecision(17) << '\n';
  }
  for (const auto* material : *G4Material::GetMaterialTable()) {
    out << "material " << material->GetName() << ' ' << material->GetDensity()
        << ' ' << material->GetState() << ' ' << material->GetTemperature()
        << ' ' << material->GetPressure() << '\n';
    for (std::size_t i = 0; i < material->GetNumberOfElements(); ++i) {
      const auto* element = material->GetElement(i);
      out << "element " << element->GetName() << ' ' << element->GetZ()
          << ' ' << element->GetA() << ' ' << material->GetFractionVector()[i] << '\n';
    }
  }
  const auto writeList = [&out](const char* name, const std::vector<G4String>& list) {
    out << "source-list " << name << '\n';
    for (const auto& entry : list) out << entry << '\n';
  };
  writeList("Cathodes", detector.GetCathodesList());
  writeList("GEMsOuter", detector.GetGEMsOuterLists());
  writeList("GEMsCore", detector.GetGEMsInnerLists());
  writeList("RingSupports", detector.GetRingsSupportList());
  writeList("RingStrips", detector.GetRingStripstList());
  writeList("Resistors", detector.GetResistorList());
  writeList("Lens", detector.GetLensList());
  writeList("Sensors", detector.GetSensorsList());
  for (const auto& entry : counts) out << "count " << entry.first << ' ' << entry.second << '\n';
  out << "sensitive-count " << sensitiveCount << '\n';
  return out ? 0 : 1;
}
