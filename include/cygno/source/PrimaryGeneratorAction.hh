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
/// \file PrimaryGeneratorAction.hh
/// \brief Configure the particle gun and sample source-component positions.
//
// 
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo...... 

#ifndef PrimaryGeneratorAction_h
#define PrimaryGeneratorAction_h 1

#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4ParticleGun.hh"
#include "globals.hh"
#include "cygno/geometry/DetectorConstruction.hh"
#include "G4ThreeVector.hh"
#include "G4String.hh"
#include "G4LogicalVolume.hh"
#include "G4VSolid.hh"
#include "cygno/source/RadioactiveSourceSampler.hh"
#include "G4GenericMessenger.hh" 

class G4Event;

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

class PrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction
{

public:
  PrimaryGeneratorAction(DetectorConstruction*);
  ~PrimaryGeneratorAction();
  
public:
  virtual void GeneratePrimaries(G4Event*);
  G4ParticleGun* GetParticleGun() { return fParticleGun;};
  G4ThreeVector GetPointOnDetectorElement(G4String);
  
  void ResetGeneratedCount() { fGeneratedPrimaries=0; }
  G4int GetGeneratedCount() const { return fGeneratedPrimaries; }
  void SetAtomicNumber(G4int value) { fZIsotope=value; fIonNeedsUpdate=true; }
  void SetMassNumber(G4int value) { fAIsotope=value; fIonNeedsUpdate=true; }
private:
  G4ParticleGun*  fParticleGun;
  RadioactiveSourceSampler fSourceSampler;
  G4int fGeneratedPrimaries = 0;
  bool fIonNeedsUpdate = false;
  G4int fZIsotope;
  G4int fAIsotope;   
  G4GenericMessenger* fPrimaryMessenger;
  G4GenericMessenger* fSourceMessenger;
  G4String fElement = "Vessel";
  
};

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#endif
