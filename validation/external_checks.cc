// Geometry and actual GPS sampling checks, independent of radioactive transport.
#include "common/SimulationMode.hh"
#include "common/ExternalGeometry.hh"
#include "cygno/geometry/DetectorConstruction.hh"
#include "cygno/source/PrimaryGeneratorAction.hh"
#include "G4Event.hh"
#include "G4PrimaryVertex.hh"
#include "G4PrimaryParticle.hh"
#include "G4Gamma.hh"
#include "G4UImanager.hh"
#include "G4Box.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4PhysicalVolumeStore.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"
#include "G4RunManager.hh"
#include "G4PhysListFactory.hh"
#include "G4RadioactiveDecayPhysics.hh"
#include "G4IonTable.hh"
#include "G4DynamicParticle.hh"
#include "G4Track.hh"
#include "cygno/actions/Run.hh"
#include "cygno/actions/EventAction.hh"
#include "cygno/actions/TrackingAction.hh"
#include <iostream>
#include <cmath>
#include <stdexcept>
void require(bool ok,const char* message) { if(!ok) throw std::runtime_error(message); }
class ProbeManager : public G4RunManager {
public:
  void BeginProbe() { currentRun=new Run; }
};
int main(int argc,char** argv) try {
  using namespace cygno::geometry;
  require(argc==2,"Expected layout");
  cygno::simulation::Configure("external","copper20");
  CLHEP::HepRandom::setTheEngine(new CLHEP::RanecuEngine);
  CLHEP::HepRandom::setTheSeed(17423);
  ProbeManager manager;
  auto* construction=new DetectorConstruction(ParseLayoutId(argv[1]));
  manager.SetUserInitialization(construction);
  G4PhysListFactory factory;
  auto* physics=factory.GetReferencePhysList(cygno::simulation::Physics());
  if (!physics->GetPhysics("G4RadioactiveDecay")) physics->RegisterPhysics(new G4RadioactiveDecayPhysics);
  manager.SetUserInitialization(physics);
  manager.Initialize();manager.BeginProbe();
  auto& detector=*construction;
  const auto& p=detector.GetLayoutProfile();
  const auto inner=ShieldBoundary(p,0),outer=ShieldBoundary(p,4);
  require(std::abs(outer.x-inner.x-200)<1e-9 && std::abs(outer.y-inner.y-200)<1e-9 &&
          std::abs(outer.z-inner.z-200)<1e-9,"Wrong total copper thickness");
  const double radius=SourceRadiusMm(p);
  require(radius>std::sqrt(outer.x*outer.x+outer.y*outer.y+outer.z*outer.z),"Sphere misses shield corners");
  for (auto* pv:*G4PhysicalVolumeStore::GetInstance()) {
    const auto name=pv->GetName();
    if(name=="World")continue;
    if(name.find("ExternalCu")==0) {
      require(pv->GetLogicalVolume()->GetMaterial()->GetName()=="G4_Cu","Wrong shield material");
      require(!pv->CheckOverlaps(100,0.,false,1),"Shield overlaps geometry or sibling shell");
      const int layer=pv->GetCopyNo();
      const auto a=ShieldBoundary(p,layer),b=ShieldBoundary(p,layer+1);
      const double av[]={a.x,a.y,a.z},bv[]={b.x,b.y,b.z};
      for(int axis=0;axis<3;++axis)for(int sign:{-1,1}) {
        G4ThreeVector pos,dir;pos[axis]=sign*(av[axis]+.1)*mm;dir[axis]=sign;
        auto* solid=pv->GetLogicalVolume()->GetSolid();
        require(solid->Inside(pos)==kInside,"Missing copper face");
        require(std::abs(solid->DistanceToOut(pos,dir)/mm-(bv[axis]-av[axis]-.1))<1e-7,"Wrong layer thickness");
      }
    } else {
      G4ThreeVector a,b;pv->GetLogicalVolume()->GetSolid()->BoundingLimits(a,b);
      a+=pv->GetTranslation();b+=pv->GetTranslation();
      require(a.x()/mm>-inner.x && b.x()/mm<inner.x && a.y()/mm>-inner.y && b.y()/mm<inner.y &&
              a.z()/mm>-inner.z && b.z()/mm<inner.z,"Detector/optics outside shield cavity");
    }
  }
  G4Gamma::Definition();
  EventAction eventAction;
  TrackingAction tracking(&eventAction,&detector);
  G4Track recoil(new G4DynamicParticle(G4IonTable::GetIonTable()->GetIon(6,12,0),G4ThreeVector(0,0,1),1*keV),0,{});
  recoil.SetTrackID(2);
  tracking.PreUserTrackingAction(&recoil);
  require(recoil.GetKineticEnergy()==1*keV && recoil.GetTrackStatus()==fAlive,"External ion recoil was stopped");
  PrimaryGeneratorAction generator(&detector);
  auto* ui=G4UImanager::GetUIpointer();
  for(const char* command:{"/gps/particle gamma","/gps/ene/type User","/gps/hist/type energy",
      "/gps/hist/point 0.1 0","/gps/hist/point 0.2 0.25","/gps/hist/point 1.2 0.75"})
    require(ui->ApplyCommand(command)==0,"GPS configuration failed");
  double mu=0,mu2=0,x=0,y=0,z=0;int low=0;
  constexpr int n=20000;
  for(int i=0;i<n;++i) {
    G4Event event(i);generator.GeneratePrimaries(&event);
    const auto* vertex=event.GetPrimaryVertex();const auto* primary=vertex->GetPrimary();
    const auto pos=vertex->GetPosition();const auto direction=primary->GetMomentum().unit();
    require(std::abs(pos.mag()/mm-radius)<1e-8,"Wrong source radius");
    const double cosine=-pos.unit().dot(direction);
    require(cosine>0 && cosine<=1,"Outward primary");
    mu+=cosine;mu2+=cosine*cosine;x+=pos.x()/radius;y+=pos.y()/radius;z+=pos.z()/radius;
    const double energy=primary->GetKineticEnergy()/MeV;
    require(energy>=.1 && energy<=1.2,"Energy outside source support");
    low+=energy<.2;
  }
  require(std::abs(mu/n-2./3)<.01 && std::abs(mu2/n-.5)<.01,"Not cosine-law incidence");
  require(std::abs(x/n)<.02 && std::abs(y/n)<.02 && std::abs(z/n)<.02,"Not uniform on sphere");
  require(std::abs(double(low)/n-.25)<.015,"GPS bin probabilities changed with bin width");
  std::cout << "External checks passed: " << argv[1] << "; radius_mm=" << radius << "; mean_cos=" << mu/n << '\n';
  return 0;
} catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
