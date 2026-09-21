#ifndef CYGNO_EXACT_ENERGY_WINDOWS_HH
#define CYGNO_EXACT_ENERGY_WINDOWS_HH
#include "TTree.h"
#include <array>
#include <cmath>
#include <stdexcept>
#include <string>

// Count the same electron/positron groups as the main plotter, BEFORE binning.
// Full range includes flows; >10 has no upper cap; 10-400 means (10,400].
class ExactEnergyWindows {
  std::array<std::array<int,6>,2> counts_{};
public:
  void Observe(double energy, bool cut) {
    if (!std::isfinite(energy)) throw std::runtime_error("Nonfinite group energy");
    const std::array<bool,6> pass{{true, energy>10, energy>10 && energy<=400,
                                  energy<0, energy>=0 && energy<2000, energy>=2000}};
    for (int c=0;c<2;++c) if (c==0 || cut)
      for (int w=0;w<6;++w) if (pass[w]) ++counts_[c][w];
  }
  const auto& Counts() const { return counts_; }
};

// Persistent addresses for ROOT object branches throughout all contributions.
class ExactEnergyWindowOutput {
  TTree tree_{"ExactEnergyWindows", "Electron/positron groups counted before binning"};
  std::string id_, window_;
  int cut_=0, count_=0;
  double rate_=0, variance_=0;
public:
  ExactEnergyWindowOutput() {
    tree_.SetDirectory(nullptr);
    tree_.Branch("Contribution",&id_); tree_.Branch("Window",&window_);
    tree_.Branch("Fiducial",&cut_); tree_.Branch("Count",&count_);
    tree_.Branch("RatePerYear",&rate_); tree_.Branch("VariancePerYear2",&variance_);
  }
  void Add(const ExactEnergyWindows& counts, const std::string& id, double scale) {
    id_=id;
    const std::array<const char*,6> names{{"all", "gt10", "gt10_le400", "underflow", "in_range", "overflow"}};
    for (cut_=0;cut_<2;++cut_) for (int w=0;w<6;++w) {
      window_=names[w]; count_=counts.Counts()[cut_][w]; rate_=count_*scale;
      variance_=count_*scale*scale; tree_.Fill();
    }
  }
  void Write() { tree_.Write(); }
};
#endif
