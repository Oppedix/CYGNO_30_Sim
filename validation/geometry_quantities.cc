// Export quantities from actual constructed source placements; no transport.
#include "cygno/geometry/DetectorConstruction.hh"
#include "BuildInfo.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
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
  if (argc!=3) throw std::runtime_error("Usage: geometry_quantities output.tsv LAYOUT");
  const auto layout=cygno::geometry::ParseLayoutId(argv[2]);
  CLHEP::HepRandom::setTheEngine(new CLHEP::RanecuEngine);
  CLHEP::HepRandom::setTheSeed(12345);
  DetectorConstruction detector(layout);
  detector.Construct();
  const std::map<G4String,std::vector<G4String>> sources{
    {"Cathodes",detector.GetCathodesList()}, {"GEMsOuter",detector.GetGEMsOuterLists()},
    {"GEMsCore",detector.GetGEMsInnerLists()}, {"RingSupports",detector.GetRingsSupportList()},
    {"RingStrips",detector.GetRingStripstList()}, {"Resistors",detector.GetResistorList()},
    {"Lens",detector.GetLensList()}, {"Sensors",detector.GetSensorsList()}, {"Vessel",{"Vessel"}}};
  std::ofstream out(argv[1]);
  if (!out) throw std::runtime_error("Cannot write quantities file");
  out << std::setprecision(17)
      << "# layout: " << detector.GetLayoutProfile().name << '\n'
      << "# detector-model: code-compatible\n# source-policy: historical\n"
      << "# compiled-source-hash: " << cygno::build::sourceHash << '\n'
      << "# geometry-hash: " << cygno::build::geometryHash << '\n'
      << "# provenance: actual source placements; sum of logical GetMass()/kg and list size\n"
      << "component\tmass_kg\tpieces\tgeometry_material\n";
  if (sources.size()!=detector.GetComponentMasses().size())
    throw std::runtime_error("Source and mass keys differ");
  std::set<G4String> seen;
  for (const auto& source : sources) {
    double mass=0;
    G4String material;
    for (const auto& name : source.second) {
      if (!seen.insert(name).second) throw std::runtime_error("Duplicate source placement");
      const auto* physical=detector.GetVolumeStored()->GetVolume(name);
      if (!physical) throw std::runtime_error("Missing source placement");
      auto* logical=physical->GetLogicalVolume();
      const auto next=logical->GetMaterial()->GetName();
      if (!material.empty() && material!=next) throw std::runtime_error("Mixed-material source list");
      material=next;
      mass+=logical->GetMass();
    }
    if (mass<=0 || std::abs(mass-detector.GetComponentMasses().at(source.first))>1e-12*mass)
      throw std::runtime_error("Constructed mass total mismatch");
    out << source.first << '\t' << mass/kg << '\t' << source.second.size() << '\t' << material << '\n';
  }
  if (!out) throw std::runtime_error("Failed to write quantities");
  return 0;
} catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
