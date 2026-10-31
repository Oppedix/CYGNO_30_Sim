#ifndef CYGNO_UNIFORM_BINNING_HH
#define CYGNO_UNIFORM_BINNING_HH
#include "TH1D.h"

// Unit-weight spectra: keep the canonical ROOT 6.40/Python uniform edges on 6.30 too.
inline void FillSpectrum(TH1D& histogram, double energy) {
  const auto& axis=*histogram.GetXaxis();
  if (energy<axis.GetXmin() || !(energy<axis.GetXmax())) {
    histogram.Fill(energy);
    return;
  }
  const double width=(axis.GetXmax()-axis.GetXmin())/axis.GetNbins();
  const int approximate=static_cast<int>((energy-axis.GetXmin())/width);
  const int bin=1+approximate-(energy<axis.GetXmin()+width*approximate)
                +(axis.GetXmin()+width*(approximate+1)<=energy);
  if (axis.FindFixBin(energy)==bin) {
    histogram.Fill(energy);
    return;
  }
  // Fill the chosen bin while retaining entries, errors and ORIGINAL energy moments.
  double stats[4];
  histogram.GetStats(stats);
  histogram.Fill(axis.GetBinCenter(bin));
  stats[0]+=1.; stats[1]+=1.; stats[2]+=energy; stats[3]+=energy*energy;
  histogram.PutStats(stats);
}
#endif
