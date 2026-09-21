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
/// \file PrimaryGeneratorAction.cc
/// \brief Configure the particle gun and sample source-component positions.
//
// 
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
#include "cygno/source/PrimaryGeneratorAction.hh"
#include "G4LogicalVolume.hh"
#include "G4Event.hh"
#include "G4ParticleTable.hh"
#include "G4IonTable.hh"
#include "G4ParticleDefinition.hh"
#include "G4Geantino.hh"
#include "G4ParticleTable.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"
#include "G4VSolid.hh"
#include "G4Exception.hh"

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

PrimaryGeneratorAction::PrimaryGeneratorAction(DetectorConstruction* Detector)
  : G4VUserPrimaryGeneratorAction(),
    fParticleGun(0),
    fSourceSampler(Detector)
{
  
  G4int n_particle = 1;
  fParticleGun  = new G4ParticleGun(n_particle);
  
  G4ParticleTable* particleTable = G4ParticleTable::GetParticleTable();
  G4ParticleDefinition* particle = particleTable->FindParticle("geantino");  
    
  // Legacy unused draw: retain it because removing it changes the RNG sequence.
  (void)G4UniformRand();

  fParticleGun->SetParticleEnergy(0*eV);
  //fParticleGun->SetParticlePosition(GetPointOnDetectorElement("Cathodes"));
  fParticleGun->SetParticleMomentumDirection(G4ThreeVector(1.,0.,0.));          
  fParticleGun->SetParticleDefinition(particle);

  fPrimaryMessenger = new G4GenericMessenger(this, "/isotope/","Radioactive isotope");
  fPrimaryMessenger->DeclareMethod("AtomicNumber", &PrimaryGeneratorAction::SetAtomicNumber, "Select atomic number");
  fPrimaryMessenger->DeclareMethod("MassNumber", &PrimaryGeneratorAction::SetMassNumber, "Select mass number");
    
  // default isotope is Uranium-238, the most common isotope of Uranium. The user can change it via the /isotope command in the macro file or interactive session.
  fZIsotope = 92, fAIsotope = 238;
  fSourceMessenger = new G4GenericMessenger(this, "/detector/", "Radioactive source");
  fSourceMessenger->DeclareProperty("RadElement", fElement, "Select radioactive component");
  
}


//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

PrimaryGeneratorAction::~PrimaryGeneratorAction()
{
  delete fPrimaryMessenger;
  delete fSourceMessenger;
  delete fParticleGun;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

// Called once per event, before BeginOfEventAction, to create primary vertices.
void PrimaryGeneratorAction::GeneratePrimaries(G4Event* anEvent)
{

  // Explicit isotope commands apply on the next event, including later runs.
  // A manually selected gun particle remains usable until an isotope command.
  if (fParticleGun->GetParticleDefinition() == G4Geantino::Geantino() || fIonNeedsUpdate) {    
    G4double ionCharge   = 0.*eplus;
    G4double excitEnergy = 0.*keV;
    
    G4ParticleDefinition* ion
      = G4IonTable::GetIonTable()->GetIon(fZIsotope,fAIsotope,excitEnergy);
    if (!ion) G4Exception("PrimaryGeneratorAction", "CYGNO_ISOTOPE", FatalException, "Invalid isotope");
    fParticleGun->SetParticleDefinition(ion);
    fIonNeedsUpdate=false;
    fParticleGun->SetParticleCharge(ionCharge);
  }    
    
  // Sample before this same event creates its vertex. The algorithm is unchanged.
  fParticleGun->SetParticlePosition(fSourceSampler.Sample(fElement).position);
  fParticleGun->GeneratePrimaryVertex(anEvent);
}
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......


G4ThreeVector PrimaryGeneratorAction::GetPointOnDetectorElement(G4String component)
{
  return fSourceSampler.Sample(component).position;
}
