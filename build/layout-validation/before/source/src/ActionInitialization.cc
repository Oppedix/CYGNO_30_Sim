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
//
/// \file ActionInitialization.cc
/// \brief Register run/event/tracking callbacks and a primary generator for each worker.

#include "ActionInitialization.hh"
#include "PrimaryGeneratorAction.hh"
#include "RunAction.hh"
#include "EventAction.hh"
#include "TrackingAction.hh"
#include "DetectorConstruction.hh"

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

ActionInitialization::ActionInitialization(DetectorConstruction* Detector)
  : G4VUserActionInitialization(),
    fDetector(Detector)
    //construct base geant4 class and store pointer to detector construction (store Detector inside fDetector)
{}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

ActionInitialization::~ActionInitialization()
{}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

// In MT mode the master summarizes merged runs; it does not generate events.
void ActionInitialization::BuildForMaster() const
{
  RunAction* runAction = new RunAction(0);
  SetUserAction(runAction);

}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

// Each worker gets its own actions. Geant4 invokes these at run, event and
// track boundaries; gas steps go directly to SensitiveDetector (no SteppingAction).
void ActionInitialization::Build() const
{
  
  PrimaryGeneratorAction* primary = new PrimaryGeneratorAction(fDetector);
  SetUserAction(primary);
  
  RunAction* runAction = new RunAction(primary);
  SetUserAction(runAction);
  
  EventAction* eventAction = new EventAction(primary);
  SetUserAction(eventAction);
  
  TrackingAction* trackingAction = new TrackingAction(eventAction,fDetector);
  SetUserAction(trackingAction);

}  

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
