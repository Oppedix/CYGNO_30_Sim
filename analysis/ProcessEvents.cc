// Post-process step rows without changing the simulation. The inherited charged-
// particle/process grouping is retained WITHIN an event; groups cannot cross an
// event boundary and every nonempty final group is written at EOF.
#include "Analysis.hh"
#include "BuildInfo.hh"
#include "TFile.h"
#include "TTree.h"
#include "TLeaf.h"
#include "TLeafC.h"
#include "TNamed.h"
#include <array>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace cygno::analysis {
void RequireGeometry(TFile& file, const std::string& assumedGeometry) {
  if (auto* marker = dynamic_cast<TNamed*>(file.Get("CygnoGeometry"))) {
    if (std::string(marker->GetTitle()) != build::geometryHash)
      throw std::runtime_error("Processed file geometry does not match this build");
    return;
  }
  if (auto* metadata = dynamic_cast<TTree*>(file.Get("RunMetadata"))) {
    if (metadata->GetEntries()!=1 || !dynamic_cast<TLeafC*>(metadata->GetLeaf("GeometryHash")))
      throw std::runtime_error("Invalid RunMetadata geometry record");
    metadata->GetEntry(0);
    if (std::string(static_cast<TLeafC*>(metadata->GetLeaf("GeometryHash"))->GetValueString()) != build::geometryHash)
      throw std::runtime_error("Raw file geometry does not match this build");
    return;
  }
  if (assumedGeometry != build::geometryId)
    throw std::runtime_error("Unversioned file: identify its source revision first; use --assume-geometry cygno-5x5x3-v1 only for confirmed 5x5x3 data");
}
void CopyMetadata(TFile& input, TFile& output) {
  output.cd();
  TNamed("CygnoGeometry", build::geometryHash).Write();
  TNamed("CygnoLayout", build::geometryId).Write();
  if (auto* metadata = dynamic_cast<TTree*>(input.Get("RunMetadata")))
    metadata->CloneTree()->Write();
  else
    TNamed("GeometryProvenance", "Researcher explicitly identified unversioned data as current geometry").Write();
}
namespace {
struct Group {
  int event = -1;
  std::string particle, nucleus, process;
  bool ionizationSeen = false;
  std::map<int, std::size_t> index;
  std::vector<double> energies, volumes, x, y, z;
  bool Empty() const { return volumes.empty(); }
  void Add(int volume, double energy, double px, double py, double pz) {
    const auto inserted = index.emplace(volume, volumes.size());
    if (inserted.second) {
      volumes.push_back(volume); energies.push_back(energy);
      x.push_back(px); y.push_back(py); z.push_back(pz);
    } else energies[inserted.first->second] += energy;
  }
};
}
void ProcessEvents(const std::string& input, const std::string& output,
                   const std::string& assumedGeometry) {
  std::unique_ptr<TFile> source(TFile::Open(input.c_str()));
  if (!source || source->IsZombie()) throw std::runtime_error("Cannot open input " + input);
  RequireGeometry(*source, assumedGeometry);
  auto* tree=dynamic_cast<TTree*>(source->Get("Hits"));
  if (!tree) throw std::runtime_error("Missing Hits tree");
  // Read variable-length /C leaves using ROOT's managed buffers, avoiding the
  // former fixed 20-byte arrays (excited nucleus labels can exceed that size).
  const std::array<std::pair<const char*,const char*>,12> schema{{
    {"EventNumber","Int_t"},{"ParticleName","Char_t"},{"ParticleID","Int_t"},
    {"ParticleTag","Int_t"},{"ParentID","Int_t"},{"x_hits","Double_t"},
    {"y_hits","Double_t"},{"z_hits","Double_t"},{"EnergyDeposit","Double_t"},
    {"VolumeNumber","Int_t"},{"Nucleus","Char_t"},{"ProcessType","Char_t"}}};
  for(const auto& column:schema) {
    auto* leaf=tree->GetLeaf(column.first);
    if(!leaf || std::string(leaf->GetTypeName())!=column.second)
      throw std::runtime_error(std::string("Missing/wrong Hits field: ")+column.first);
  }
  const auto number=[&](const char* name){return tree->GetLeaf(name)->GetValue();};
  const auto text=[&](const char* name){return std::string(static_cast<TLeafC*>(tree->GetLeaf(name))->GetValueString());};
  TFile destination(output.c_str(),"RECREATE");
  if(destination.IsZombie()) throw std::runtime_error("Cannot create " + output);
  Group group;
  TTree result("elabHits","elabHits");
  result.Branch("evNumber",&group.event);
  result.Branch("PartName",&group.particle);
  result.Branch("EDep_Out",&group.energies);
  result.Branch("VolNnum_Out",&group.volumes);
  result.Branch("Nucleus",&group.nucleus);
  result.Branch("X_Vertex",&group.x);
  result.Branch("Y_Vertex",&group.y);
  result.Branch("Z_Vertex",&group.z);
  const auto flush=[&](){if(!group.Empty()) result.Fill(); group=Group{};};
  for(Long64_t entry=0;entry<tree->GetEntries();++entry) {
    tree->GetEntry(entry);
    const int event=static_cast<int>(number("EventNumber"));
    if(!group.Empty() && event!=group.event) flush();
    const auto particle=text("ParticleName");
    if(particle!="e-" && particle!="e+" && particle!="alpha") continue;
    const auto process=text("ProcessType"), nucleus=text("Nucleus");
    const bool ionization=process=="ionIoni" || process=="eIoni";
    if(!group.Empty()) {
      if(process==group.process && nucleus==group.nucleus && !group.ionizationSeen)
        group.particle=particle; // preserve the inherited group's label convention
      else if(ionization) group.ionizationSeen=true;
      else flush();
    }
    if(group.Empty()) {
      group.event=event; group.particle=particle; group.nucleus=nucleus; group.process=process;
    }
    const int volume=static_cast<int>(number("VolumeNumber"));
    if(volume<0 || volume>=150) throw std::runtime_error("Invalid gas copy number");
    group.Add(volume,number("EnergyDeposit"),number("x_hits"),number("y_hits"),number("z_hits"));
  }
  flush();
  destination.cd(); result.Write(); CopyMetadata(*source,destination);
  TNamed("ProcessingVersion","event-boundaries-and-eof-v2").Write();
  // The stack-allocated tree is destroyed before the file; do not close early.
}
}
