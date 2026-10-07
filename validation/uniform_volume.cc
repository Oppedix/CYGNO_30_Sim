// Independent analytic first/second moments and rotation contract, no transport.
#include "cygno/geometry/DetectorConstruction.hh"
#include "cygno/source/RadioactiveSourceSampler.hh"
#include "G4Box.hh"
#include "G4LogicalVolume.hh"
#include "G4Tubs.hh"
#include "Randomize.hh"
#include <array>
#include <cmath>
#include <iostream>
#include <stdexcept>

void require(bool ok, const char* message) { if (!ok) throw std::runtime_error(message); }
struct Moments { double volume; G4ThreeVector mean, second; };
Moments box(G4ThreeVector lo, G4ThreeVector hi) {
  const auto size=hi-lo;
  return {size.x()*size.y()*size.z(),(lo+hi)/2,
          {(lo.x()*lo.x()+lo.x()*hi.x()+hi.x()*hi.x())/3,
           (lo.y()*lo.y()+lo.y()*hi.y()+hi.y()*hi.y())/3,
           (lo.z()*lo.z()+lo.z()*hi.z()+hi.z()*hi.z())/3}};
}
Moments shell(G4ThreeVector outer, G4ThreeVector inner, G4ThreeVector shift={}) {
  const auto a=box(-outer,outer), b=box(shift-inner,shift+inner);
  return {a.volume-b.volume,(a.volume*a.mean-b.volume*b.mean)/(a.volume-b.volume),
          (a.volume*a.second-b.volume*b.second)/(a.volume-b.volume)};
}
int main() {
  CLHEP::HepRandom::setTheEngine(new CLHEP::RanecuEngine);
  CLHEP::HepRandom::setTheSeed(271828);
  DetectorConstruction detector(cygno::geometry::LayoutId::Cygno11x7);
  detector.Construct();
  const std::map<G4String,std::vector<G4String>> sources{
    {"GEMsPolyimide",detector.GetGEMsPolyimideList()}, {"GEMsCopper",detector.GetGEMsCopperList()},
    {"CathodesPolyimide",detector.GetCathodesPolyimideList()}, {"CathodesCopper",detector.GetCathodesCopperList()},
    {"RingSupports",detector.GetRingsSupportList()}, {"RingStrips",detector.GetRingStripstList()},
    {"Resistors",detector.GetResistorList()}, {"Lens",detector.GetLensList()},
    {"Sensors",detector.GetSensorsList()}, {"Vessel",{"Vessel"}}};
  constexpr int n=100000;
  for (const auto& [family,names] : sources) {
    auto* physical=detector.GetVolumeStored()->GetVolume(names.front());
    auto* solid=physical->GetLogicalVolume()->GetSolid();
    // Uniform placement choice is valid only for equal solid/material families.
    for (const auto& name : names) {
      auto* logical=detector.GetVolumeStored()->GetVolume(name)->GetLogicalVolume();
      require(logical==physical->GetLogicalVolume(),"non-identical source placements");
    }
    Moments expected{};
    if (auto* b=dynamic_cast<G4Box*>(solid)) {
      const G4ThreeVector half{b->GetXHalfLength(),b->GetYHalfLength(),b->GetZHalfLength()};
      expected=box(-half,half);
    } else if (auto* lens=dynamic_cast<G4Tubs*>(solid)) {
      const double radius=lens->GetOuterRadius(), z=lens->GetZHalfLength();
      expected={0,{}, {radius*radius/4,radius*radius/4,z*z/3}};
    } else if (family=="RingSupports") {
      expected=shell({250.110,400.110,250},{250.035,400.035,250});
    } else if (family=="RingStrips") {
      expected=shell({250.035,400.035,27.5},{250,400,27.5},{-.0175,-.0175,0});
    } else {
      expected=shell({2780,2822,514.21},{2775,2817,509.21});
    }
    G4ThreeVector sum, square, lo{1e30,1e30,1e30}, hi{-1e30,-1e30,-1e30}, boundLo,boundHi;
    solid->BoundingLimits(boundLo,boundHi);
    for (int i=0; i<n; ++i) {
      const auto p=RadioactiveSourceSampler::SampleLocal(solid);
      require(solid->Inside(p)!=kOutside,"sample outside source solid");
      sum+=p;
      for (int axis=0; axis<3; ++axis) {
        square[axis]+=p[axis]*p[axis];
        lo[axis]=std::min(lo[axis],p[axis]);hi[axis]=std::max(hi[axis],p[axis]);
      }
    }
    for (int axis=0; axis<3; ++axis) {
      const double variance=expected.second[axis]-expected.mean[axis]*expected.mean[axis];
      require(std::abs(sum[axis]/n-expected.mean[axis])<7*std::sqrt(variance/n),"non-uniform source mean");
      require(std::abs(square[axis]/n-expected.second[axis])<.015*expected.second[axis],"non-uniform second moment");
      require(lo[axis]>=boundLo[axis]-1e-9 && hi[axis]<=boundHi[axis]+1e-9,"sample range outside bounds");
      require(lo[axis]<boundLo[axis]+.02*(boundHi[axis]-boundLo[axis]) &&
              hi[axis]>boundHi[axis]-.02*(boundHi[axis]-boundLo[axis]),"source range lacks volume extent");
    }
    std::cout << "UNIFORM_OK " << family << " " << n << " points; analytic moments/ranges\n";
  }
  // Exercise a nontrivial physical OBJECT rotation; fail on frame/inverse mixups.
  auto* vessel=detector.GetVessel();
  G4RotationMatrix rotation; rotation.rotateX(.31);rotation.rotateY(.67);
  vessel->SetRotation(&rotation);
  RadioactiveSourceSampler sampler(&detector);
  for (int i=0;i<10000;++i) {
    const auto sample=sampler.Sample("Vessel");
    const auto local=vessel->GetObjectRotationValue().inverse()*(sample.position-vessel->GetObjectTranslation());
    require(vessel->GetLogicalVolume()->GetSolid()->Inside(local)!=kOutside,"rotated placement sample outside");
  }
  vessel->SetRotation(nullptr);
}
