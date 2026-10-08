// Independent numerical contracts for profile fields consumed by simulation
// and, in Phase 2, analysis. Use exceptions: Release builds disable assert().
#include "common/DetectorGeometry.hh"
#include <cmath>
#include <iostream>
#include <set>
#include <tuple>
#include <stdexcept>

namespace geo = cygno::geometry;
void require(bool ok) { if (!ok) throw std::runtime_error("Layout profile contract failed"); }
void point(geo::Point actual, geo::Point expected) {
  require(std::abs(actual.x-expected.x)<1e-9 && std::abs(actual.y-expected.y)<1e-9
          && std::abs(actual.z-expected.z)<1e-9);
}
int main() {
  const auto& d=geo::module;
  require(d.stripCount==25 && d.stripLengthZ==10 && d.stripGapZ==10 && d.stripEndpointGapZ==5);
  require(d.supportThickness==.075 && d.stripThickness==.035 && d.booleanCutExtension==5);
  require(d.resistorX==1.6 && d.resistorY==.55 && d.resistorZ==3.2);
  for (int i=0;i<25;++i) {
    require(geo::StripCentreFromGasStart(i)==10+20*i);
    require(std::abs(geo::StripCentreZ(i)-(10.03+20*i))<1e-9);
  }
  require(geo::StripCentreFromGasStart(0)-d.stripLengthZ/2==5);
  require(geo::StripCentreFromGasStart(24)+d.stripLengthZ/2==495);
  require(d.stripCount*d.stripLengthZ/d.driftLength==.5);
  for (int i=0;i<26;++i) {
    const double center=geo::ResistorCentreFromGasStart(i);
    const double lo=i==0 ? 0 : 15+20*(i-1);
    const double hi=i==25 ? 500 : 5+20*i;
    require(center==(lo+hi)/2 && center-d.resistorZ/2>lo && center+d.resistorZ/2<hi);
  }
  require(2*d.stripCount==50 && 77*2*d.stripCount==3850);
  require(2*(d.stripCount+1)==52 && 77*2*(d.stripCount+1)==4004);
  for (auto id : {geo::LayoutId::Current5x5x3, geo::LayoutId::Legacy25x3, geo::LayoutId::Cygno11x7}) {
    const auto p = geo::BuildLayoutProfile(id);
    const bool legacy = id == geo::LayoutId::Legacy25x3;
    require(geo::ParseLayoutId(p.name)==id && p.id==id);
    const bool planar = id == geo::LayoutId::Cygno11x7;
    const int count = planar ? 77 : 75;
    require(p.expectedModuleCount==count && p.modules.size()==count);
    std::set<std::tuple<double,double,double>> centers;
    std::set<int> copies;
    for (int m=0; m<count; ++m) {
      const auto& placement=p.modules.at(m);
      require(placement.id==m);
      const geo::Point expected=planar
        ? geo::Point{(m/7-5)*504.0,(m%7-3)*804.0,0}
        : legacy
        ? geo::Point{(m/3-12)*504.0,(m%3-1)*804.0,0}
        : geo::Point{(m/15-2)*504.0,((m/3)%5-2)*804.0,(m%3-1)*2285.42};
      point(placement.center,expected);
      require(centers.emplace(expected.x,expected.y,expected.z).second);
      require(placement.ix==(planar ? m/7 : legacy ? m/3 : m/15));
      require(placement.iy==(planar ? m%7 : legacy ? m%3 : (m/3)%5));
      require(placement.iz==(legacy || planar ? 0 : m%3));
      for (int side=0; side<2; ++side) {
        const int copy=geo::GasCopyNumber(m,side,count);
        require(copy==side*count+m && copies.insert(copy).second);
        point(geo::GasCenter(placement,side),
              {expected.x,expected.y,expected.z+(side==0 ? 250.03 : -250.03)});
      }
    }
    require(copies.size()==2*count);
    require(*copies.begin()==0 && *copies.rbegin()==2*count-1);
    point(p.modules.at(planar ? 38 : 37).center,{0,0,0});
    point(p.occupiedEnvelope.min,planar ? geo::Point{-2770.145,-2812.1275,-1140.71} : legacy ? geo::Point{-6298.145,-1204.1275,-1140.71}
                                        : geo::Point{-1258.145,-2008.1275,-3426.13});
    point(p.occupiedEnvelope.max,planar ? geo::Point{2770.075,2812.660,1140.71} : legacy ? geo::Point{6298.075,1204.660,1140.71}
                                        : geo::Point{1258.075,2008.660,3426.13});
    point(p.vesselOuterHalfSize,planar ? geo::Point{2780,2822,514.21} : legacy ? geo::Point{6308,1214,514.21}
                                      : geo::Point{1268,2018,2799.63});
    point(p.worldHalfSize,planar ? geo::Point{7000,3322,1640.71} : legacy ? geo::Point{7000,1714,1640.71}
                                : geo::Point{7000,2518,3926.13});
    std::cout << p.name << ": profile, bounds and " << 2*count << " gas centers PASS\n";
  }
  // The default must preserve the baseline profile. Unknown profiles fail closed.
  require(geo::BuildLayoutProfile().id==geo::LayoutId::Current5x5x3);
  bool rejected=false;
  try { geo::ParseLayoutId("25x3"); } catch (const std::invalid_argument&) { rejected=true; }
  require(rejected);
}
