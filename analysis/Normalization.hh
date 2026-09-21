#ifndef CYGNO_NORMALIZATION_HH
#define CYGNO_NORMALIZATION_HH
// Study inputs are supplied explicitly; no geometry-dependent mass defaults.
#include <cmath>
#include <fstream>
#include <filesystem>
#include <iomanip>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
struct Normalization {
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
    if (line.rfind("# provenance:",0)==0 && line.size()>14) provenance=true;
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
  return result;
}
#endif
