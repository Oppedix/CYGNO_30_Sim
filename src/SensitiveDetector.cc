// Write one Hits ntuple row for every step delivered by a sensitive gas volume.
#include "SensitiveDetector.hh"
#include "G4Step.hh"
#include "G4TouchableHistory.hh"
#include "G4Track.hh"
#include "G4StepPoint.hh"
#include "G4ThreeVector.hh"
#include "G4RunManager.hh"
#include "G4AnalysisManager.hh"
#include "EventAction.hh"

SensitiveDetector::SensitiveDetector(G4String name) :
  G4VSensitiveDetector(name)
{}

SensitiveDetector::~SensitiveDetector()
{}

// Called for steps in the shared GasVolume logical volume. There is no energy
// threshold or particle filter: even zero-deposit steps become ntuple rows.
// This implementation writes directly, without a G4VHit/hits-collection layer.
G4bool SensitiveDetector::ProcessHits(G4Step * aStep, G4TouchableHistory* Rohist)
{

  G4Track* track = aStep->GetTrack();

  G4StepPoint* preStepPoint = aStep->GetPreStepPoint();

  // Pre-step WORLD coordinates, in Geant4 internal length units (mm).
  G4ThreeVector posParticle = preStepPoint->GetPosition();

  G4String particleName = track->GetParticleDefinition()->GetParticleName();
  // ParticleID is the event-local track ID, not a PDG particle code.
  G4int particleID = track->GetTrackID();
  G4double EdepStep = aStep->GetTotalEnergyDeposit();
  // Gas copy number: 0..74 on local +Z, 75..149 on local -Z.
  // Module ID = (ix*5+iy)*3+iz; see common/DetectorGeometry.hh.
  G4int VolumeCopyNumber = track->GetVolume()->GetCopyNo();
  G4int particleParentID = track->GetParentID();

  // Nucleus is the most recently tracked ion label, not an ancestry lookup.
  // ProcessType is the track CREATOR process, not the process for this step.
  G4String DecayElement = GetLastDecay();
  G4String ProcessType = "";
  
  if(track->GetCreatorProcess()){
    ProcessType= track->GetCreatorProcess()->GetProcessName();
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
  AnalysisManager->FillNtupleIColumn(0,evt);
  AnalysisManager->FillNtupleSColumn(1,particleName);
  AnalysisManager->FillNtupleIColumn(2,particleID);
  AnalysisManager->FillNtupleIColumn(3,particleTag);
  AnalysisManager->FillNtupleIColumn(4,particleParentID);
  AnalysisManager->FillNtupleDColumn(5,posParticle[0]);
  AnalysisManager->FillNtupleDColumn(6,posParticle[1]);
  AnalysisManager->FillNtupleDColumn(7,posParticle[2]);
  AnalysisManager->FillNtupleDColumn(8,EdepStep);
  AnalysisManager->FillNtupleIColumn(9,VolumeCopyNumber);
  AnalysisManager->FillNtupleSColumn(10,DecayElement);
  AnalysisManager->FillNtupleSColumn(11,ProcessType);
  
  AnalysisManager->AddNtupleRow(0);

  // A row was recorded. Returning success fixes the former undefined return
  // without changing which steps are stored or any of their column values.
  return true;

}
