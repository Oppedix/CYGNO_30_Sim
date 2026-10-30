// Export quantities from actual constructed source placements; no transport.
#include "cygno/geometry/DetectorConstruction.hh"
#include "BuildInfo.hh"
#include "common/SimulationMode.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4Element.hh"
#include "G4VSolid.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>

int main(int argc, char** argv) try {
  if (argc<3) throw std::runtime_error("Usage: geometry_quantities output.tsv LAYOUT [geometry.json] [--model MODEL] [--mode internal|external] [--gas-bkg yes|no]; default model: cygno-copper-cathode-v4");
  std::string model=cygno::simulation::defaultDetectorModel, mode="internal", geometryPath, gasBkg="no";
  int next=3;
  if (next<argc && std::string(argv[next]).rfind("--",0)!=0) geometryPath=argv[next++];
  std::set<std::string> options;
  while (next<argc) {
    const std::string option=argv[next++];
    if ((option!="--model" && option!="--mode" && option!="--gas-bkg") || next==argc || !options.insert(option).second)
      throw std::runtime_error("Specify --model/--mode/--gas-bkg once with a value");
    (option=="--model" ? model : option=="--mode" ? mode : gasBkg)=argv[next++];
  }
  if ((gasBkg!="no" && gasBkg!="yes") ||
      (gasBkg=="yes" && (mode!="internal" || model!="cygno-copper-cathode-v4")))
    throw std::runtime_error("--gas-bkg yes|no requires internal v4 when enabled");
  cygno::simulation::Configure(mode, "none", model);
  const auto layout=cygno::geometry::ParseLayoutId(argv[2]);
  CLHEP::HepRandom::setTheEngine(new CLHEP::RanecuEngine);
  CLHEP::HepRandom::setTheSeed(12345);
  DetectorConstruction detector(layout);
  detector.Construct();
  std::map<G4String,std::vector<G4String>> sources{
    {"Cathode",detector.GetCathodeList()}, {"CathodesPolyimide",detector.GetCathodesPolyimideList()}, {"CathodesCopper",detector.GetCathodesCopperList()}, {"GEMsCopper",detector.GetGEMsCopperList()},
    {"GEMsPolyimide",detector.GetGEMsPolyimideList()}, {"RingSupports",detector.GetRingsSupportList()},
    {"RingStrips",detector.GetRingStripstList()}, {"Resistors",detector.GetResistorList()},
    {"Lens",detector.GetLensList()}, {"Sensors",detector.GetSensorsList()}, {"Vessel",{"Vessel"}}};
  for (auto it=sources.begin(); it!=sources.end();) {
    if (it->second.empty()) it=sources.erase(it); else ++it;
  }
  std::ofstream out(argv[1]);
  if (!out) throw std::runtime_error("Cannot write quantities file");
  out << std::setprecision(17)
      << "# layout: " << detector.GetLayoutProfile().name << '\n'
      << "# detector-model: " << cygno::simulation::DetectorModel()
      << "\n# source-policy: " << cygno::simulation::SourcePolicy() << '\n'
      << "# compiled-source-hash: " << cygno::build::sourceHash << '\n'
      << "# geometry-hash: " << cygno::build::geometryHash << '\n'
      << "# provenance: actual source placements; sum of logical GetMass()/kg and list size\n"
      << "component\tmass_kg\tpieces\tgeometry_material\tdensity_g_cm3\tvolume_mm3\n";
  if (sources.size()!=detector.GetComponentMasses().size())
    throw std::runtime_error("Source and mass keys differ");
  if (gasBkg=="yes") sources["Gas"]=detector.GetGasList();
  std::set<G4String> seen;
  for (const auto& source : sources) {
    double mass=0, volume=0, density=0;
    G4String material;
    for (const auto& name : source.second) {
      if (!seen.insert(name).second) throw std::runtime_error("Duplicate source placement");
      const auto* physical=detector.GetVolumeStored()->GetVolume(name);
      if (!physical) throw std::runtime_error("Missing source placement");
      auto* logical=physical->GetLogicalVolume();
      if (source.first=="Gas") {
        const auto* gas=logical->GetMaterial();
        double carbonFraction=0;
        for (size_t i=0; i<gas->GetNumberOfElements(); ++i)
          if ((*gas->GetElementVector())[i]->GetZ()==6) carbonFraction+=gas->GetFractionVector()[i];
        const double expected=(3574.736*.4)/(162.488*.6+3574.736*.4)*12.0107/(12.0107+4*18.998);
        if (std::abs(carbonFraction/expected-1)>1e-12)
          throw std::runtime_error("Gas carbon fraction differs from the C14 normalization assumption");
      }
      const auto next=logical->GetMaterial()->GetName();
      if (!material.empty() && material!=next) throw std::runtime_error("Mixed-material source list");
      material=next;
      mass+=logical->GetMass();
      volume+=logical->GetSolid()->GetCubicVolume();
      density=logical->GetMaterial()->GetDensity();
    }
    if (mass<=0 || (source.first!="Gas" && std::abs(mass-detector.GetComponentMasses().at(source.first))>1e-12*mass))
      throw std::runtime_error("Constructed mass total mismatch");
    out << source.first << '\t' << mass/kg << '\t' << source.second.size() << '\t' << material
        << '\t' << density/(g/cm3) << '\t' << volume/mm3 << '\n';
  }
  if (!out) throw std::runtime_error("Failed to write quantities");
  if (!geometryPath.empty()) {
    std::ofstream geometry(geometryPath);
    using namespace cygno::geometry;
    geometry << std::setprecision(17)
      << "{\"layout\":\"" << LayoutName(layout)
      << "\",\"model\":\"" << cygno::simulation::DetectorModel()
      << "\",\"source_policy\":\"" << cygno::simulation::SourcePolicy()
      << "\",\"geometry_hash\":\"" << cygno::build::geometryHash
      << "\",\"source_hash\":\"" << cygno::build::sourceHash
      << "\",\"gas_size_mm\":[" << module.cathodeX << ',' << module.cathodeY << ',' << module.driftLength
      << "],\"gas_centers_mm\":{";
    const auto modules=BuildModuleLayout(layout);
    bool first=true;
    for (int side=0; side<2; ++side) for (const auto& placement : modules) {
      const auto center=GasCenter(placement,side);
      if (!first) geometry << ',';
      first=false;
      geometry << '\"' << GasCopyNumber(placement.id,side,modules.size()) << "\":["
               << center.x << ',' << center.y << ',' << center.z << ']';
    }
    geometry << "}}\n";
    if (!geometry) throw std::runtime_error("Failed to write geometry metadata");
  }
  return 0;
} catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
