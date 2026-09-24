// Compile once per plotting program (see README). No production data are needed.
// Exercise its actual center-map and fiducial predicate at each cell boundary.
#include <cassert>
#include <cmath>
#include <iomanip>
#include <iostream>
#define main CygnoAnalysisMain
#include CYGNO_ANALYSIS_SOURCE
#undef main
int main(int argc, char** argv) {
  if (argc!=2) return 1;
  std::map<Int_t,TVector3> centers;
  BuildDetectorMap(centers, cygno::geometry::ParseLayoutId(argv[1]));
  assert(centers.size()==2*cygno::geometry::BuildModuleLayout(cygno::geometry::ParseLayoutId(argv[1])).size());
  std::cout << std::setprecision(17);
  for (const auto& entry : centers) {
    const int id=entry.first;
    const auto& c=entry.second;
    assert(isWithin(centers,c.X(),c.Y(),c.Z(),id));
    assert(isWithin(centers,c.X()+230,c.Y()+380,c.Z()+230,id));
    assert(!isWithin(centers,c.X()+231,c.Y(),c.Z(),id));
    assert(!isWithin(centers,c.X(),c.Y()+381,c.Z(),id));
    assert(!isWithin(centers,c.X(),c.Y(),c.Z()+231,id));
    std::cout << id << '\t' << c.X() << '\t' << c.Y() << '\t' << c.Z() << '\n';
  }
}
