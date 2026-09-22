//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.  It is provided  under  the terms  and *
// * conditions of the Geant4 Software License,  included in the file *
// * LICENSE and available at  http://cern.ch/geant4/license .  These *
// * include a list of copyright holders.                             *
// *                                                                  *
// * Neither the authors of this software system, nor their employing *
// * institutes,nor the agencies providing financial support for this *
// * work  make  any representation or  warranty, express or implied, *
// * regarding  this  software system or assume any liability for its *
// * use.  Please see the license in the file  LICENSE  and URL above *
// * for the full disclaimer and the limitation of liability.         *
// *                                                                  *
// * This  code  implementation is the result of  the  scientific and *
// * technical work of the GEANT4 collaboration.                      *
// * By using,  copying,  modifying or  distributing the software (or *
// * any work based  on the software)  you  agree  to acknowledge its *
// * use  in  resulting  scientific  publications,  and indicate your *
// * acceptance of all terms of the Geant4 Software license.          *
// ********************************************************************
//
/// \file RunAction.cc
/// \brief Book the Hits ntuple and open/write/close the Geant4 ROOT-format output.
//
// 
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#include "cygno/actions/RunAction.hh"
#include "cygno/actions/Run.hh"
#include "cygno/source/PrimaryGeneratorAction.hh"
#include "G4AnalysisManager.hh"
#include "G4Run.hh"
#include "G4RunManager.hh"
#include "cygno/geometry/DetectorConstruction.hh"
#include "BuildInfo.hh"
#include "cygno/output/HitOutput.hh"
#include "G4Exception.hh"
#include <filesystem>
#include "G4UnitsTable.hh"
#include "G4PhysicalConstants.hh"
#include "G4SystemOfUnits.hh"
#include <iomanip>
#include "G4VRadioactiveDecay.hh"
#include "G4ProcessTable.hh"
#include "G4GenericIon.hh"
#include "G4HadronicProcessType.hh"

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

RunAction::RunAction(PrimaryGeneratorAction* kin)
:G4UserRunAction(),
 fPrimary(kin),
 fRun(0) 
{
  fRunMessenger = new G4GenericMessenger(this, "/output/","Output file");
  fRunMessenger->DeclareProperty("OutFile", fOutFileName, "Output file name");

  // /output/OutFile supplies a basename, not a directory. The fixed output
  // directory is created relative to the process working directory.
  fOutFileName="outfiles_V2";
  cygno::hits::Book(); // once per analysis manager; CloseFile resets rows, not booking
  // Keep Hits unchanged. Each worker file carries one independent identity row.
  // The MT master has no events/output; do not create a metadata-only master file.
  if (fPrimary) {
    auto* manager=G4AnalysisManager::Instance();
    const auto id=manager->CreateNtuple("RunMetadata","Run geometry identity");
    if (id!=1) G4Exception("RunAction", "CYGNO_METADATA", FatalException, "Unexpected metadata ntuple ID");
    for (const auto* name : {"GeometryHash", "Layout", "DetectorModel", "SourcePolicy"})
      manager->CreateNtupleSColumn(id,name);
    manager->FinishNtuple(id);
    const auto accounting=manager->CreateNtuple("RunAccounting", "Event accounting, not chain certification");
    if (accounting!=2) G4Exception("RunAction", "CYGNO_ACCOUNTING", FatalException, "Unexpected accounting ntuple ID");
    for (const auto* name : {"RunID", "RequestedEvents", "GeneratedPrimaries", "ProcessedEvents", "AbortedEvents"})
      manager->CreateNtupleIColumn(accounting,name);
    manager->FinishNtuple(accounting);
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

RunAction::~RunAction()
{ delete fRunMessenger; }
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4Run* RunAction::GenerateRun()
{ 
  fRun = new Run();
  return fRun;
}
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

// Called once per run on master/workers, before the first event is generated.
void RunAction::BeginOfRunAction(const G4Run*)
{ 
  // keep run condition
  if (fPrimary) { 
    // Read the actual worker process after UI command propagation. This records
    // run configuration only; it never changes the decay physics or RNG state.
    const auto* decay=dynamic_cast<G4VRadioactiveDecay*>(
      G4ProcessTable::GetProcessTable()->FindProcess(fRadioactiveDecay, G4GenericIon::GenericIon()));
    if (!decay) G4Exception("RunAction", "CYGNO_RDM", FatalException, "Missing radioactive decay process");
    G4cout << "CYGNO_RUN radioactive_decay_time_threshold_s " << std::setprecision(17)
           << decay->GetThresholdForVeryLongDecayTime()/second << G4endl;
    fPrimary->ResetGeneratedCount();
    G4ParticleDefinition* particle 
      = fPrimary->GetParticleGun()->GetParticleDefinition();
    G4double energy = fPrimary->GetParticleGun()->GetParticleEnergy();
    fRun->SetPrimary(particle, energy);
  }    
      
  //histograms
  //
  G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
  //if ( analysisManager->IsActive() ) {
  std::filesystem::create_directories("outfiles_V2");
  if (!analysisManager->OpenFile("outfiles_V2/"+fOutFileName+".root"))
    G4Exception("RunAction::BeginOfRunAction", "CYGNO_OUTPUT", FatalException, "Cannot open output file");
    //}
  if (fPrimary) {
    const auto* detector=dynamic_cast<const DetectorConstruction*>(
      G4RunManager::GetRunManager()->GetUserDetectorConstruction());
    if (!detector) G4Exception("RunAction", "CYGNO_METADATA", FatalException, "Missing detector identity");
    analysisManager->FillNtupleSColumn(1,0,cygno::build::geometryHash);
    analysisManager->FillNtupleSColumn(1,1,detector->GetLayoutProfile().name);
    analysisManager->FillNtupleSColumn(1,2,"code-compatible");
    analysisManager->FillNtupleSColumn(1,3,"historical");
    analysisManager->AddNtupleRow(1);
  }


}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

// Called after event processing; the master receives merged Run statistics.
void RunAction::EndOfRunAction(const G4Run* run)
{
  if (isMaster) fRun->EndOfRun();
            
 //save histograms
 //
 G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
 //if ( analysisManager->IsActive() ) {
 if (fPrimary) {
   analysisManager->FillNtupleIColumn(2,0,run->GetRunID());
   analysisManager->FillNtupleIColumn(2,1,run->GetNumberOfEventToBeProcessed());
   analysisManager->FillNtupleIColumn(2,2,fPrimary->GetGeneratedCount());
   analysisManager->FillNtupleIColumn(2,3,run->GetNumberOfEvent());
   analysisManager->FillNtupleIColumn(2,4,fRun->GetAbortedEvents());
   analysisManager->AddNtupleRow(2);
 }
 if (!analysisManager->Write() || !analysisManager->CloseFile())
   G4Exception("RunAction::EndOfRunAction", "CYGNO_OUTPUT", FatalException, "Cannot finish output file");
  //} 
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
