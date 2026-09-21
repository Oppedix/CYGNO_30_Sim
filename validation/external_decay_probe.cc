// Standalone Geant4 reproducer: no CYGNO geometry, source sampler, output or
// analysis code is linked. Retain the active reference physics and at-rest ions.
#include "G4RunManagerFactory.hh"
#include "G4VUserDetectorConstruction.hh"
#include "G4VUserActionInitialization.hh"
#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4UserTrackingAction.hh"
#include "G4PhysListFactory.hh"
#include "G4RadioactiveDecayPhysics.hh"
#include "G4Box.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4NistManager.hh"
#include "G4IonTable.hh"
#include "G4ParticleGun.hh"
#include "G4SystemOfUnits.hh"
#include "G4Track.hh"
#include "Randomize.hh"
class World : public G4VUserDetectorConstruction {
 G4VPhysicalVolume* Construct() override {
  auto* solid=new G4Box("World",1*m,1*m,1*m);
  auto* logical=new G4LogicalVolume(solid,G4NistManager::Instance()->FindOrBuildMaterial("G4_Galactic"),"World");
  return new G4PVPlacement(nullptr,{},logical,"World",nullptr,false,0);
 }
};
class Gun : public G4VUserPrimaryGeneratorAction {
 G4ParticleGun gun{1};
 void GeneratePrimaries(G4Event* event) override {
  gun.SetParticleDefinition(G4IonTable::GetIonTable()->GetIon(83,212,0));
  gun.SetParticleEnergy(0); gun.SetParticlePosition({}); gun.GeneratePrimaryVertex(event);
 }
};
class RestIons : public G4UserTrackingAction {
 void PreUserTrackingAction(const G4Track* track) override {
  if(track->GetDefinition()->GetPDGCharge()>2) {
    auto* ion=const_cast<G4Track*>(track);
    ion->SetKineticEnergy(0); ion->SetTrackStatus(fStopButAlive);
  }
 }
};
class Actions : public G4VUserActionInitialization {
 void Build() const override {SetUserAction(new Gun); SetUserAction(new RestIons);}
};
int main() {
 CLHEP::HepRandom::setTheEngine(new CLHEP::RanecuEngine);
 const long seeds[]={12345,67890}; CLHEP::HepRandom::setTheSeeds(seeds);
 auto* manager=G4RunManagerFactory::CreateRunManager(); manager->SetNumberOfThreads(1);
 manager->SetUserInitialization(new World);
 G4PhysListFactory factory; auto* physics=factory.GetReferencePhysList("QGSP_BIC_EMZ");
 physics->RegisterPhysics(new G4RadioactiveDecayPhysics);
 manager->SetUserInitialization(physics); manager->SetUserInitialization(new Actions);
 manager->Initialize(); manager->BeamOn(200);
 delete manager;
}
