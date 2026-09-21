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
#include "cygno/output/HitOutput.hh"
#include "G4Exception.hh"
#include <filesystem>
#include "G4UnitsTable.hh"
#include "G4PhysicalConstants.hh"
#include "G4SystemOfUnits.hh"
#include <iomanip>

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


}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

// Called after event processing; the master receives merged Run statistics.
void RunAction::EndOfRunAction(const G4Run*)
{
  if (isMaster) fRun->EndOfRun();
            
 //save histograms
 //
 G4AnalysisManager* analysisManager = G4AnalysisManager::Instance();
 //if ( analysisManager->IsActive() ) {
 analysisManager->Write();
 analysisManager->CloseFile();
  //} 
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
