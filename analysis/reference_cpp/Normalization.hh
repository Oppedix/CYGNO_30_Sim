#ifndef CYGNO_NORMALIZATION_HH
#define CYGNO_NORMALIZATION_HH
// Study inputs are supplied explicitly; no geometry-dependent mass defaults.
#include "FileIdentity.hh"
#include "TH1D.h"
#include "THStack.h"
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
  std::map<std::string,double> quantities;
  std::map<std::string,std::string> quantityUnits, activityUnits, categories;
  std::string configuration;
  double Scale(const std::string& component, const std::string& isotope) const {
    // Preserve the existing multiplication order and 365-day year.
    return activities.at(component).at(isotope)*quantities.at(component)*60*60*24*365/events.at(component).at(isotope);
  }
  std::map<std::string,std::map<std::string,double>> activities, events;
  std::map<std::string,std::map<std::string,std::string>> files;
};
inline Normalization ReadNormalization(const std::string& path) {
  std::ifstream in(path);
  if (!in) throw std::runtime_error("Cannot open normalization configuration: " + path);
  Normalization result;
  std::string line;
  bool provenance=false, quantityFormat=false, formatSeen=false;
  while (std::getline(in,line)) {
    result.configuration += line + '\n';
    if (line.rfind("# normalization-format:",0)==0) {
      if (formatSeen || !result.quantities.empty() || line!="# normalization-format: quantity-v2")
        throw std::runtime_error("Unsupported, duplicate or late normalization format");
      quantityFormat=true; formatSeen=true;
    }
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
    std::string component,isotope,file,extra,quantityUnit="kg",activityUnit="Bq/kg",category;
    double quantity,activity,events;
    if (quantityFormat) {
      if (!(row>>component>>isotope>>quantity>>quantityUnit>>activity>>activityUnit>>events>>std::quoted(category)>>std::quoted(file)) || row>>extra)
        throw std::runtime_error("Expected component isotope quantity quantity_unit activity activity_unit generated_events category input_file");
    } else {
      if (!(row>>component>>isotope>>quantity>>activity>>events>>std::quoted(file)) || row>>extra)
        throw std::runtime_error("Expected component isotope mass_kg activity_Bq_per_kg generated_events input_file");
      category=component;
    }
    if (!std::isfinite(quantity) || quantity<=0 || !std::isfinite(activity) || activity<0 || !std::isfinite(events) || events<=0)
      throw std::runtime_error("Invalid normalization value");
    if (!((quantityUnit=="kg" && activityUnit=="Bq/kg") || (quantityUnit=="piece" && activityUnit=="Bq/piece")))
      throw std::runtime_error("Quantity/activity unit mismatch; use kg with Bq/kg or piece with Bq/piece");
    if ((quantityUnit=="piece" && std::floor(quantity)!=quantity) || (quantityFormat && std::floor(events)!=events))
      throw std::runtime_error("Piece and generated-primary counts must be integers");
    if (category.empty() || category.find_first_of("/\\\n\r")!=std::string::npos)
      throw std::runtime_error("Invalid category name");
    if (std::filesystem::weakly_canonical(file)==std::filesystem::weakly_canonical("NormalizedHisto.root"))
      throw std::runtime_error("Input would be overwritten by normalized output");
    if (result.files[component].count(isotope)) throw std::runtime_error("Duplicate normalization row");
    if (result.quantities.count(component) &&
        (result.quantities.at(component)!=quantity || result.quantityUnits.at(component)!=quantityUnit ||
         result.activityUnits.at(component)!=activityUnit || result.categories.at(component)!=category))
      throw std::runtime_error("Inconsistent component quantity, units or category");
    result.quantities[component]=quantity; result.quantityUnits[component]=quantityUnit;
    result.activityUnits[component]=activityUnit; result.categories[component]=category;
    result.activities[component][isotope]=activity;
    result.events[component][isotope]=events; result.files[component][isotope]=file;
    if (!std::isfinite(result.Scale(component,isotope))) throw std::runtime_error("Nonfinite normalization scale");
  }
  if (!provenance || result.quantities.empty()) throw std::runtime_error("Configuration needs a # provenance: record and at least one row");
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
// Sum only AFTER each physical material/chain has received its own scale.
// Detached clones survive input file ownership and preserve sum-of-weights errors.
class NormalizedCategories {
  std::map<std::string,std::unique_ptr<TH1D>> uncut_, cut_;
  static void Add(std::map<std::string,std::unique_ptr<TH1D>>& target,
                  const std::string& category, const TH1D& histogram) {
    auto& sum=target[category];
    if (!sum) {
      sum.reset(static_cast<TH1D*>(histogram.Clone(category.c_str())));
      sum->SetDirectory(nullptr);
      sum->SetTitle(category.c_str());
    } else sum->Add(&histogram);
  }
public:
  void Add(const std::string& category, const TH1D& uncut, const TH1D& cut) {
    Add(uncut_,category,uncut); Add(cut_,category,cut);
  }
  void Write(TFile& output, const Normalization& settings) const {
    auto* directory=output.mkdir("Categories");
    directory->cd();
    THStack uncutStack("Hstack","Category spectra;Energy [keV];Counts/bin/year");
    THStack cutStack("Hstack_cut","Category spectra, fiducial cut;Energy [keV];Counts/bin/year");
    for (const auto& item : uncut_) { item.second->Write(); uncutStack.Add(item.second.get()); }
    for (const auto& item : cut_) { item.second->Write((item.first+"_cut").c_str()); cutStack.Add(item.second.get()); }
    uncutStack.Write(); cutStack.Write();
    output.cd();
    TNamed("NormalizationConfiguration",settings.configuration.c_str()).Write();
    TNamed("NormalizationConvention","activity * quantity * 31536000 / generated primaries; counts/bin/year; categories summed after scaling").Write();
  }
};
#endif
