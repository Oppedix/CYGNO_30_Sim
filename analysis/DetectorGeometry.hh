#ifndef CYGNO_ROOT_DETECTOR_GEOMETRY_HH
#define CYGNO_ROOT_DETECTOR_GEOMETRY_HH

// ROOT adapter for the SAME layout used by DetectorConstruction. Positions and
// hit coordinates are millimetres. Select only after validating file identity.
#include "../common/DetectorGeometry.hh"
#include "TVector3.h"
#include <map>

inline void BuildDetectorMap(std::map<Int_t,TVector3>& centers,
                             cygno::geometry::LayoutId layout)
{
  centers.clear();
  const auto modules = cygno::geometry::BuildModuleLayout(layout);
  for (const auto& module : modules) {
    for (int side=0; side<2; ++side) {
      const auto center = cygno::geometry::GasCenter(module,side);
      centers[cygno::geometry::GasCopyNumber(module.id,side,static_cast<int>(modules.size()))] =
        TVector3(center.x,center.y,center.z);
    }
  }
}
#endif
