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
#include "G4QuickRand.hh"
#include <sstream>
#include <stdexcept>
#include <cmath>
void require(bool ok, const char* message) { if(!ok) throw std::runtime_error(message); }
int main() {
  CLHEP::HepRandom::setTheEngine(new CLHEP::RanecuEngine);
  CLHEP::HepRandom::setTheSeed(12345);
  G4RunManager manager;
  auto* detector=new DetectorConstruction;
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
    {"Cathodes",detector->GetCathodesList()}, {"GEMsOuter",detector->GetGEMsOuterLists()},
    {"GEMsCore",detector->GetGEMsInnerLists()}, {"RingSupports",detector->GetRingsSupportList()},
    {"RingStrips",detector->GetRingStripstList()}, {"Resistors",detector->GetResistorList()},
    {"Lens",detector->GetLensList()}, {"Sensors",detector->GetSensorsList()}, {"Vessel",{"Vessel"}}};
  require(detector->GetComponentMasses().size()==sources.size(),"extra mass map keys");
  int event=0;
  for(const auto& source:sources) {
    require(ui->ApplyCommand("/detector/RadElement "+source.first)==0,"source command");
    double mass=0;
    for(const auto& name:source.second) mass+=detector->GetVolumeStored()->GetVolume(name)->GetLogicalVolume()->GetMass();
    require(std::abs(mass-detector->GetComponentMasses().at(source.first))<=1e-12*mass,"component mass mismatch");
    G4cout<<"MASS_OK "<<source.first<<" "<<mass/CLHEP::kg<<" kg"<<G4endl;
    for(int n=0;n<10;++n) {
      std::stringstream before, expectedState, actualState;
      auto* engine=CLHEP::HepRandom::getTheEngine(); engine->put(before);
      // Geant4 11.4 surface solids also use a separate thread-local RNG.
      G4QuickRand(123456u+event);
      const auto expected=sampler.Sample(source.first).position;
      const auto expectedQuick=G4QuickRand();
      engine->put(expectedState); engine->get(before);
      G4QuickRand(123456u+event);
      G4Event evt(event++); generator.GeneratePrimaries(&evt);
      require(evt.GetNumberOfPrimaryVertex()==1,"one vertex required");
      if(evt.GetPrimaryVertex()->GetPosition()!=expected) G4cerr<<"MISMATCH event "<<evt.GetEventID()<<" component "<<source.first<<" expected "<<expected<<" actual "<<evt.GetPrimaryVertex()->GetPosition()<<G4endl;
      require(evt.GetPrimaryVertex()->GetPosition()==expected,"vertex must use same-event sample");
      require(expected.mag2()>0,"fixed-seed first vertex must not be origin");
      action.BeginOfEventAction(&evt); engine->put(actualState);
      require(G4QuickRand()==expectedQuick,"unexpected solid RNG draws");
      require(actualState.str()==expectedState.str(),"unexpected RNG draws or event-action sampling");
    }
    int outside=0;
    for(int n=0;n<1000;++n) {
      const auto sample=sampler.Sample(source.first);
      outside+=sample.volume->GetLogicalVolume()->GetSolid()->Inside(sample.position-sample.volume->GetObjectTranslation())==kOutside;
    }
    G4cout<<"CONTAINMENT_DIAGNOSTIC "<<source.first<<" "<<outside<<" / 1000 outside; no rejection/resampling"<<G4endl;
  }
  require(ui->ApplyCommand("/isotope/AtomicNumber 83")==0,"isotope change");
  require(ui->ApplyCommand("/isotope/MassNumber 211")==0,"isotope change");
  G4Event changed(event); generator.GeneratePrimaries(&changed);
  require(changed.GetPrimaryVertex()->GetPrimary()->GetG4code()->GetAtomicNumber()==83,"updated Z");
  require(changed.GetPrimaryVertex()->GetPrimary()->GetG4code()->GetAtomicMass()==211,"updated A");
  G4cout<<"PASS: 90 vertices equal their own samples, event zero non-origin, exact RNG replay, all mass keys/totals"<<G4endl;
}
