// Book/fill the unchanged 12-column step ntuple. Units are mm and MeV.
#include "cygno/output/HitOutput.hh"
#include "G4AnalysisManager.hh"
#include "G4Exception.hh"
#include "G4RunManager.hh"
#include "G4Step.hh"
#include "G4Track.hh"
#include <array>
namespace cygno::hits {
void Book() {
  enum Type { Integer, String, Double };
  struct Definition { Column id; const char* name; Type type; };
  constexpr std::array<Definition, Count> columns{{
    {EventNumber,"EventNumber",Integer}, {ParticleName,"ParticleName",String},
    {ParticleID,"ParticleID",Integer}, {ParticleTag,"ParticleTag",Integer},
    {ParentID,"ParentID",Integer}, {X,"x_hits",Double}, {Y,"y_hits",Double},
    {Z,"z_hits",Double}, {EnergyDeposit,"EnergyDeposit",Double},
    {VolumeNumber,"VolumeNumber",Integer}, {Nucleus,"Nucleus",String},
    {ProcessType,"ProcessType",String}
  }};
  auto* manager=G4AnalysisManager::Instance();
  const auto id=manager->CreateNtuple("Hits","Hits");
  if (id != ntupleId) G4Exception("hits::Book", "CYGNO_SCHEMA", FatalException, "Unexpected Hits ntuple ID");
  for (const auto& column : columns) {
    G4int booked=-1;
    switch(column.type) {
      case Integer: booked=manager->CreateNtupleIColumn(id,column.name); break;
      case String: booked=manager->CreateNtupleSColumn(id,column.name); break;
      case Double: booked=manager->CreateNtupleDColumn(id,column.name); break;
    }
    if (booked != column.id) G4Exception("hits::Book", "CYGNO_SCHEMA", FatalException, "Column ordering mismatch");
  }
  manager->FinishNtuple(id);
}
void WriteStep(const G4Step* aStep, const G4String& lastIon) {
  G4Track* track = aStep->GetTrack();

  G4StepPoint* preStepPoint = aStep->GetPreStepPoint();

  // Pre-step WORLD coordinates, in Geant4 internal length units (mm).
  G4ThreeVector posParticle = preStepPoint->GetPosition();

  G4String particleName = track->GetParticleDefinition()->GetParticleName();
  // ParticleID is the event-local track ID, not a PDG particle code.
  G4int particleID = track->GetTrackID();
  G4double EdepStep = aStep->GetTotalEnergyDeposit();
  // Gas copy number: 0..74 on local +Z, 75..149 on local -Z.
  // Module order follows RunMetadata.Layout; see common/DetectorGeometry.hh.
  G4int VolumeCopyNumber = track->GetVolume()->GetCopyNo();
  G4int particleParentID = track->GetParentID();

  // Nucleus is the most recently tracked ion label, not an ancestry lookup.
  // ProcessType is the track CREATOR process, not the process for this step.
  G4String DecayElement = lastIon;
  G4String creatorProcess = "";
  
  if(track->GetCreatorProcess()){
    creatorProcess= track->GetCreatorProcess()->GetProcessName();
  } 
    
  G4int particleTag=-1;

  if(particleName == "e-"){
    particleTag=0;
  } else if(particleName == "e+"){
    particleTag=1;
  } else if(particleName == "gamma"){
    particleTag=2;
  } else if(particleName == "alpha"){
    particleTag=3;
  } else {
    particleTag=-1;
  }
  
  //G4cout << "position of: " << particleName <<" " << track->GetTrackID() << "  is:  "<< posParticle << " Energy deposited:  " << EdepStep << "  in volume:  " << VolumeCopyNumber << " ParentID: "  << track->GetParentID()<< " lastdecay: " << DecayElement << "  Process: " << ProcessType << G4endl;

  G4int evt = G4RunManager::GetRunManager()->GetCurrentEvent()->GetEventID();
  
  
  G4AnalysisManager* AnalysisManager = G4AnalysisManager::Instance(); 

  // Column order must match RunAction::BeginOfRunAction. EnergyDeposit is in
  // internal energy units (MeV); coordinates/energy are stored without conversion.
  AnalysisManager->FillNtupleIColumn(ntupleId, EventNumber,evt);
  AnalysisManager->FillNtupleSColumn(ntupleId, ParticleName,particleName);
  AnalysisManager->FillNtupleIColumn(ntupleId, ParticleID,particleID);
  AnalysisManager->FillNtupleIColumn(ntupleId, ParticleTag,particleTag);
  AnalysisManager->FillNtupleIColumn(ntupleId, ParentID,particleParentID);
  AnalysisManager->FillNtupleDColumn(ntupleId, X,posParticle[0]);
  AnalysisManager->FillNtupleDColumn(ntupleId, Y,posParticle[1]);
  AnalysisManager->FillNtupleDColumn(ntupleId, Z,posParticle[2]);
  AnalysisManager->FillNtupleDColumn(ntupleId, EnergyDeposit,EdepStep);
  AnalysisManager->FillNtupleIColumn(ntupleId, VolumeNumber,VolumeCopyNumber);
  AnalysisManager->FillNtupleSColumn(ntupleId, Nucleus,DecayElement);
  AnalysisManager->FillNtupleSColumn(ntupleId, ProcessType,creatorProcess);
  
  AnalysisManager->AddNtupleRow(ntupleId);

}
}
