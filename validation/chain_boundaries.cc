// Directly exercise the existing tracking policy, without transporting chains.
// This does not certify long-lived decay transport or nuclear-data behavior.
#include "cygno/actions/TrackingAction.hh"
#include "cygno/actions/EventAction.hh"
#include "cygno/actions/Run.hh"
#include "cygno/geometry/DetectorConstruction.hh"
#include "G4RunManager.hh"
#include "G4PhysListFactory.hh"
#include "G4RadioactiveDecayPhysics.hh"
#include "G4IonTable.hh"
#include "G4DynamicParticle.hh"
#include "G4Track.hh"
#include "G4SystemOfUnits.hh"
#include "G4UImanager.hh"
#include <stdexcept>

class ProbeManager : public G4RunManager {
public:
  void BeginProbe() { currentRun=new Run; } // owned by G4RunManager
};
void require(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}
int main() {
  ProbeManager manager;
  auto* detector=new DetectorConstruction;
  manager.SetUserInitialization(detector);
  G4PhysListFactory factory;
  auto* physics=factory.GetReferencePhysList("QGSP_BIC_EMZ");
  physics->RegisterPhysics(new G4RadioactiveDecayPhysics);
  manager.SetUserInitialization(physics);
  manager.Initialize(); manager.BeginProbe();
  EventAction event;
  TrackingAction tracking(&event,detector);
  auto* ui=G4UImanager::GetUIpointer();
  require(ui->ApplyCommand("/rdecay01/fullChain true")==0,"fullChain command failed");
  const auto probe=[&](int z,int a,int trackId,double excitation) {
    auto* ion=G4IonTable::GetIonTable()->GetIon(z,a,excitation);
    require(ion!=nullptr,"Missing probe ion");
    G4Track track(new G4DynamicParticle(ion,G4ThreeVector(0,0,1),1*keV),0,G4ThreeVector());
    track.SetTrackID(trackId);
    tracking.PreUserTrackingAction(&track);
    require(track.GetKineticEnergy()==0,"Inherited recoil stopping changed");
    return track.GetTrackStatus();
  };
  for (const auto& boundary : {std::pair<int,int>{88,226},{90,228}}) {
    const auto z=boundary.first,a=boundary.second;
    require(ui->ApplyCommand("/stopChain/ZStopDecay "+std::to_string(z))==0,"stop Z failed");
    require(ui->ApplyCommand("/stopChain/AStopDecay "+std::to_string(a))==0,"stop A failed");
    require(probe(z,a,2,0)==fStopAndKill,"Boundary daughter must stop before decay");
    require(probe(z,a,1,0)==fStopAndKill,"Boundary also applies to a primary");
    require(probe(z,a,2,100*keV)==fStopButAlive,"Retain excited-state de-excitation policy");
    require(probe(92,238,2,0)==fStopButAlive,"Do not kill other nuclides");
    require(ui->ApplyCommand("/stopChain/ZStopDecay 0")==0,"reset Z failed");
    require(ui->ApplyCommand("/stopChain/AStopDecay 0")==0,"reset A failed");
    require(probe(z,a,1,0)==fStopButAlive,"Restart must permit boundary primary decay");
    require(probe(z,a,2,0)==fStopButAlive,"Reset must permit downstream tracking");
  }
  G4cout << "PASS: Ra226/Th228 ground-state stop-before, excited-state policy, explicit restart/reset; no decay transport" << G4endl;
}
