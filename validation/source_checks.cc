// Deterministic same-event and RNG test; containment is diagnostic only.
#include "cygno/source/PrimaryGeneratorAction.hh"
#include "cygno/actions/EventAction.hh"
#include "cygno/geometry/DetectorConstruction.hh"
#include "G4RunManager.hh"
#include "G4PhysListFactory.hh"
#include "G4RadioactiveDecayPhysics.hh"
#include "G4Event.hh"
#include "G4IonTable.hh"
#include "G4SystemOfUnits.hh"
#include "G4PrimaryVertex.hh"
#include "G4UImanager.hh"
#include "Randomize.hh"
#include <sstream>
#include <stdexcept>
#include <cmath>
void require(bool ok, const char* message) { if(!ok) throw std::runtime_error(message); }
int main(int argc, char** argv) {
  if (argc > 2) return 1;
  CLHEP::HepRandom::setTheEngine(new CLHEP::RanecuEngine);
  CLHEP::HepRandom::setTheSeed(12345);
  G4RunManager manager;
  auto* detector=new DetectorConstruction(argc == 2 ? cygno::geometry::ParseLayoutId(argv[1])
                                                    : cygno::geometry::LayoutId::Current5x5x3);
  manager.SetUserInitialization(detector);
  G4PhysListFactory factory;
  auto* physics=factory.GetReferencePhysList("QGSP_BIC_EMZ");
  physics->RegisterPhysics(new G4RadioactiveDecayPhysics);
  manager.SetUserInitialization(physics);
  manager.Initialize();
  PrimaryGeneratorAction generator(detector);
  EventAction action;
  auto* ui=G4UImanager::GetUIpointer();
  require(ui->ApplyCommand("/isotope/AtomicNumber 84")==0,"isotope command");
  require(ui->ApplyCommand("/isotope/MassNumber 212")==0,"isotope command");
  // Build ion definitions before independently replaying sampler draws.
  G4IonTable::GetIonTable()->GetIon(84,212,0.);
  RadioactiveSourceSampler sampler(detector);
  const std::map<G4String,std::vector<G4String>> sources{
    {"CathodesPolyimide",detector->GetCathodesPolyimideList()}, {"CathodesCopper",detector->GetCathodesCopperList()}, {"GEMsCopper",detector->GetGEMsCopperList()},
    {"GEMsPolyimide",detector->GetGEMsPolyimideList()}, {"RingSupports",detector->GetRingsSupportList()},
    {"RingStrips",detector->GetRingStripstList()}, {"Resistors",detector->GetResistorList()},
    {"Lens",detector->GetLensList()}, {"Sensors",detector->GetSensorsList()}, {"Vessel",{"Vessel"}}};
  require(detector->GetComponentMasses().size()==sources.size(),"extra mass map keys");
  const int count=detector->GetLayoutProfile().expectedModuleCount;
  const std::map<G4String,int> perModule{{"CathodesPolyimide",1},{"CathodesCopper",2},{"GEMsCopper",12},{"GEMsPolyimide",6},
    {"RingSupports",2},{"RingStrips",2*cygno::geometry::module.stripCount},{"Resistors",2*(cygno::geometry::module.stripCount+1)},{"Lens",4},{"Sensors",4}};
  int event=0;
  for(const auto& source:sources) {
    require(ui->ApplyCommand("/detector/RadElement "+source.first)==0,"source command");
    require(source.second.size()==(source.first=="Vessel" ? 1 : count*perModule.at(source.first)),"source count mismatch");
    double mass=0;
    for(const auto& name:source.second) mass+=detector->GetVolumeStored()->GetVolume(name)->GetLogicalVolume()->GetMass();
    require(std::abs(mass-detector->GetComponentMasses().at(source.first))<=1e-12*mass,"component mass mismatch");
    require(mass>0 && std::isfinite(mass),"invalid constructed mass");
    G4cout<<"MASS_OK "<<source.first<<" "<<mass/CLHEP::kg<<" kg"<<G4endl;
    for(int n=0;n<10;++n) {
      std::stringstream before, expectedState, actualState;
      auto* engine=CLHEP::HepRandom::getTheEngine(); engine->put(before);
      const auto expected=sampler.Sample(source.first).position;
      engine->put(expectedState); engine->get(before);
      G4Event evt(event++); generator.GeneratePrimaries(&evt);
      require(evt.GetNumberOfPrimaryVertex()==1,"one vertex required");
      if(evt.GetPrimaryVertex()->GetPosition()!=expected) G4cerr<<"MISMATCH event "<<evt.GetEventID()<<" component "<<source.first<<" expected "<<expected<<" actual "<<evt.GetPrimaryVertex()->GetPosition()<<G4endl;
      require(evt.GetPrimaryVertex()->GetPosition()==expected,"vertex must use same-event sample");
      require(expected.mag2()>0,"fixed-seed first vertex must not be origin");
      action.BeginOfEventAction(&evt); engine->put(actualState);
      require(actualState.str()==expectedState.str(),"unexpected RNG draws or event-action sampling");
    }
    int outside=0;
    for(int n=0;n<20000;++n) {
      const auto sample=sampler.Sample(source.first);
      outside+=sample.volume->GetLogicalVolume()->GetSolid()->Inside(sample.volume->GetObjectRotationValue().inverse()*(sample.position-sample.volume->GetObjectTranslation()))==kOutside;
    }
    require(outside==0,"uniform-volume sample outside solid");
    G4cout<<"CONTAINMENT_DIAGNOSTIC "<<source.first<<" "<<outside<<" / 20000 outside; no rejection/resampling"<<G4endl;
  }
  require(ui->ApplyCommand("/isotope/AtomicNumber 83")==0,"isotope change");
  require(ui->ApplyCommand("/isotope/MassNumber 211")==0,"isotope change");
  G4Event changed(event); generator.GeneratePrimaries(&changed);
  require(changed.GetPrimaryVertex()->GetPrimary()->GetG4code()->GetAtomicNumber()==83,"updated Z");
  require(changed.GetPrimaryVertex()->GetPrimary()->GetG4code()->GetAtomicMass()==211,"updated A");
  G4cout<<"PASS: 100 vertices equal their own samples, event zero non-origin, exact RNG replay, all mass keys/totals"<<G4endl;
}
