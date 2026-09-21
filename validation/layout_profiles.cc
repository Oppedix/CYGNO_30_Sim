// Independent numerical contracts for profile fields consumed by simulation
// and, in Phase 2, analysis. Use exceptions: Release builds disable assert().
#include "common/DetectorGeometry.hh"
#include <cmath>
#include <iostream>
#include <set>
#include <stdexcept>

namespace geo = cygno::geometry;
void require(bool ok) { if (!ok) throw std::runtime_error("Layout profile contract failed"); }
void point(geo::Point actual, geo::Point expected) {
  require(std::abs(actual.x-expected.x)<1e-9 && std::abs(actual.y-expected.y)<1e-9
          && std::abs(actual.z-expected.z)<1e-9);
}
int main() {
  for (auto id : {geo::LayoutId::Current5x5x3, geo::LayoutId::Legacy25x3}) {
    const auto p = geo::BuildLayoutProfile(id);
    const bool legacy = id == geo::LayoutId::Legacy25x3;
    require(geo::ParseLayoutId(p.name)==id && p.id==id);
    require(p.expectedModuleCount==75 && p.modules.size()==75);
    std::set<int> copies;
    for (int m=0; m<75; ++m) {
      const auto& placement=p.modules.at(m);
      require(placement.id==m);
      const geo::Point expected=legacy
        ? geo::Point{(m/3-12)*504.0,(m%3-1)*804.0,0}
        : geo::Point{(m/15-2)*504.0,((m/3)%5-2)*804.0,(m%3-1)*2285.3};
      point(placement.center,expected);
      require(placement.ix==(legacy ? m/3 : m/15));
      require(placement.iy==(legacy ? m%3 : (m/3)%5));
      require(placement.iz==(legacy ? 0 : m%3));
      for (int side=0; side<2; ++side) {
        const int copy=geo::GasCopyNumber(m,side);
        require(copy==side*75+m && copies.insert(copy).second);
        point(geo::GasCenter(placement,side),
              {expected.x,expected.y,expected.z+(side==0 ? 250.25 : -250.25)});
      }
    }
    require(copies.size()==150);
    point(p.occupiedEnvelope.min,legacy ? geo::Point{-6298.145,-1204.1275,-1140.65}
                                        : geo::Point{-1258.145,-2008.1275,-3425.95});
    point(p.occupiedEnvelope.max,legacy ? geo::Point{6298.075,1204.660,1140.65}
                                        : geo::Point{1258.075,2008.660,3425.95});
    point(p.vesselOuterHalfSize,legacy ? geo::Point{6308,1214,514.4}
                                      : geo::Point{1268,2018,2799.7});
    point(p.worldHalfSize,legacy ? geo::Point{7000,1714,1640.65}
                                : geo::Point{7000,2518,3925.95});
    std::cout << p.name << ": profile, bounds and 150 gas centers PASS\n";
  }
  // The default must preserve the baseline profile. Unknown profiles fail closed.
  require(geo::BuildLayoutProfile().id==geo::LayoutId::Current5x5x3);
  bool rejected=false;
  try { geo::ParseLayoutId("25x3"); } catch (const std::invalid_argument&) { rejected=true; }
  require(rejected);
}
