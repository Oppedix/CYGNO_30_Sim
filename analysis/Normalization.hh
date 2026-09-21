#ifndef CYGNO_NORMALIZATION_HH
#define CYGNO_NORMALIZATION_HH
// Study inputs are supplied explicitly; no geometry-dependent mass defaults.
#include "FileIdentity.hh"
#include <cmath>
#include <fstream>
#include <filesystem>
#include <iomanip>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
struct Normalization {
  cygno::analysis::FileIdentity identity;
  std::map<std::string,double> masses;
  std::map<std::string,std::map<std::string,double>> activities, events;
  std::map<std::string,std::map<std::string,std::string>> files;
};
inline Normalization ReadNormalization(const std::string& path) {
  std::ifstream in(path);
  if (!in) throw std::runtime_error("Cannot open normalization configuration: " + path);
  Normalization result;
  std::string line;
  bool provenance=false;
  while (std::getline(in,line)) {
    if (line.find("historical-unverified")!=std::string::npos)
      throw std::runtime_error("Historical normalization is unverified; create a study configuration with documented provenance, including the resized vessel mass");
    if (line.rfind("# provenance:",0)==0 && line.size()>14) {
      provenance=true;
      result.identity.provenance=line.substr(14);
    }
    for (const auto& field : {std::pair<const char*,std::string*>{"# layout:", &result.identity.layout},
          {"# detector-model:", &result.identity.model}, {"# source-policy:", &result.identity.sourcePolicy}}) {
      if (line.rfind(field.first,0)!=0) continue;
      std::istringstream value(line.substr(std::string(field.first).size()));
      std::string extra;
      if (!field.second->empty() || !(value >> *field.second) || value >> extra)
        throw std::runtime_error("Missing, duplicate or malformed study identity header");
    }
    if (line.empty() || line[0]=='#') continue;
    std::istringstream row(line);
    std::string component,isotope,file,extra;
    double mass,activity,events;
    if (!(row>>component>>isotope>>mass>>activity>>events>>std::quoted(file)) || row>>extra)
      throw std::runtime_error("Expected component isotope mass_kg activity_Bq_per_kg generated_events input_file");
    if (!std::isfinite(mass) || mass<=0 || !std::isfinite(activity) || activity<0 || !std::isfinite(events) || events<=0)
      throw std::runtime_error("Invalid normalization value");
    if (std::filesystem::absolute(file).lexically_normal()==std::filesystem::absolute("NormalizedHisto.root").lexically_normal()) throw std::runtime_error("Input would be overwritten by normalized output");
    if (result.files[component].count(isotope)) throw std::runtime_error("Duplicate normalization row");
    if (result.masses.count(component) && result.masses.at(component)!=mass) throw std::runtime_error("Inconsistent component mass");
    result.masses[component]=mass; result.activities[component][isotope]=activity;
    result.events[component][isotope]=events; result.files[component][isotope]=file;
  }
  if (!provenance || result.masses.empty()) throw std::runtime_error("Configuration needs a # provenance: record and at least one row");
  result.identity.geometryHash=cygno::build::geometryHash;
  cygno::analysis::ValidateIdentity(result.identity);
  return result;
}
// Validate the complete input set before any output is opened or data plotted.
inline void ValidateNormalizationInputs(const Normalization& settings) {
  for (const auto& component : settings.files) for (const auto& isotope : component.second) {
    std::unique_ptr<TFile> input(TFile::Open(isotope.second.c_str(),"READ"));
    if (!input || input->IsZombie()) throw std::runtime_error("Cannot open configured input: " + isotope.second);
    const auto identity=cygno::analysis::RequireGeometry(*input);
    cygno::analysis::RequireExpected(identity, settings.identity.layout,
                                     settings.identity.model, settings.identity.sourcePolicy);
    if (!dynamic_cast<TTree*>(input->Get("elabHits"))) throw std::runtime_error("Missing elabHits tree");
  }
}
#endif
