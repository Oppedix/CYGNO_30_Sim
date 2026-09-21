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
/// \file rdecay01.cc
/// \brief Application entry point: select UI/batch mode, geometry, active physics and actions.
//
//
//
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......
//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#include "G4Types.hh"

#include "G4RunManagerFactory.hh"
#include "G4UImanager.hh"
#include "G4SteppingVerbose.hh"
#include "Randomize.hh"
#include "G4EmStandardPhysics.hh"
#include "G4RadioactiveDecayPhysics.hh"

#include "cygno/geometry/DetectorConstruction.hh"
#include "cygno/actions/ActionInitialization.hh"

#include "G4UIExecutive.hh"
#include "G4VisExecutive.hh"
#include "G4PhysListFactory.hh"

#include "BuildInfo.hh"
#include "G4Version.hh"
#include "G4EnvironmentUtils.hh"
#include "G4VRadioactiveDecay.hh"
#include "G4ProcessTable.hh"
#include "G4GenericIon.hh"
#include "G4HadronicProcessType.hh"
#include "G4SystemOfUnits.hh"
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

int main(int argc,char** argv) {
  // Select the immutable layout before Geant4 initializes (before macro execution).
  // Existing `rdecay01 macro [workers]` invocations still select the current layout.
  auto layout = cygno::geometry::LayoutId::Current5x5x3;
  std::vector<std::string> positional;
  bool layoutSpecified = false;
  int workers = 1;
  try {
    for (int i=1; i<argc; ++i) {
      const std::string arg = argv[i];
      if (arg == "--help") {
        std::cout << "Usage: rdecay01 [macro [workers]] [--layout legacy-25x3|cygno-5x5x3-v1]\n";
        return 0;
      }
      if (arg == "--layout") {
        if (layoutSpecified || i+1 == argc)
          throw std::invalid_argument("Specify --layout exactly once with a profile name");
        layout = cygno::geometry::ParseLayoutId(argv[++i]);
        layoutSpecified = true;
      } else if (arg.rfind("--",0) == 0) {
        throw std::invalid_argument("Unknown option: " + arg);
      } else positional.push_back(arg);
    }
    if (positional.size() > 2) throw std::invalid_argument("Expected macro and optional worker count");
    if (positional.size() == 2) {
      std::size_t end = 0;
      workers = std::stoi(positional[1],&end);
      if (end != positional[1].size() || workers < 1)
        throw std::invalid_argument("The number of worker threads must be a positive integer");
    }
  } catch (const std::exception& error) {
    std::cerr << error.what() << "\nUse --help for usage.\n";
    return 1;
  }
  std::cout << "CYGNO layout=" << cygno::geometry::LayoutName(layout)
            << " detector_model=code-compatible source_model=historical\n";
  G4UIExecutive* ui = nullptr;
  if (positional.empty()) {
    int uiArgc = 1; // Geometry options belong to this application, not the UI.
    ui = new G4UIExecutive(uiArgc,argv);
  }

  // Macro /random/setSeeds can override this wall-clock seed for regression runs.
  //choose the Random engine
  CLHEP::HepRandom::setTheEngine(new CLHEP::RanecuEngine);
  //seed the random number generator with the current time
  CLHEP::HepRandom::setTheSeed(time(0));
  
  //use G4SteppingVerboseWithUnits
  G4int precision = 1;
  G4SteppingVerbose::UseBestUnit(precision);

  //construct the run manager
  auto runManager = G4RunManagerFactory::CreateRunManager();  

  runManager->SetNumberOfThreads(workers);
  
  //
  //set mandatory initialization classes
  //

  DetectorConstruction* theDetector = new DetectorConstruction(layout);
  
  runManager->SetUserInitialization(theDetector);
  //the above makes sure geant calls the Construct() method of DetectorConstruction to build the geometry.

  G4PhysListFactory factory;

  // This reference list is the active physics configuration. The custom
  // PhysicsList class in legacy/scaffolding/PhysicsList.cc is not used here.
  G4VModularPhysicsList* physicsList = factory.GetReferencePhysList("QGSP_BIC_EMZ");
  //you can modify the above to add or remove physics processes, for example to add radioactive decay:
  //physicsList->RegisterPhysics(new G4RadioactiveDecayPhysics); as done below
  physicsList->SetVerboseLevel(0);
  physicsList->RegisterPhysics(new G4RadioactiveDecayPhysics); 

  runManager->SetUserInitialization(physicsList);

  runManager->SetUserInitialization(new ActionInitialization(theDetector));

  // Construct geometry/physics before executing the user macro. Commands that
  // require the PreInit state may therefore be unsuitable in batch macros.
  //initialize G4 kernel
  runManager->Initialize();

  // Machine-readable effective environment, resolved by this linked Geant4.
  // These observations do not alter physics, data selection or random state.
  const auto* decay=dynamic_cast<G4VRadioactiveDecay*>(
      G4ProcessTable::GetProcessTable()->FindProcess(fRadioactiveDecay, G4GenericIon::GenericIon()));
  if (!decay) G4Exception("rdecay01", "CYGNO_ENVIRONMENT", FatalException, "Cannot inspect radioactive decay process");
  std::cout << "CYGNO_ENV source_hash " << cygno::build::sourceHash << "\n"
            << "CYGNO_ENV geometry_hash " << cygno::build::geometryHash << "\n"
            << "CYGNO_ENV geant4 " << G4Version << "\n"
            << "CYGNO_ENV physics QGSP_BIC_EMZ+G4RadioactiveDecayPhysics\n"
            << "CYGNO_ENV radioactive_decay_time_threshold_s " << std::setprecision(17)
            << decay->GetThresholdForVeryLongDecayTime()/second << "\n";
  for (const auto* key : {"G4NEUTRONHPDATA", "G4LEDATA", "G4LEVELGAMMADATA",
       "G4RADIOACTIVEDATA", "G4PARTICLEXSDATA", "G4PIIDATA", "G4REALSURFACEDATA",
       "G4SAIDXSDATA", "G4ABLADATA", "G4INCLDATA", "G4ENSDFSTATEDATA", "G4CHANNELINGDATA"}) {
    const char* path=G4FindDataDir(key);
    std::cout << "CYGNO_ENV " << key << " " << (path ? path : "UNRESOLVED") << "\n";
  }

  //initialize visualization
  G4VisManager* visManager = nullptr;

  //get the pointer to the User Interface manager
  G4UImanager* UImanager = G4UImanager::GetUIpointer();

  G4int commandStatus=0;
  if (ui)  {
    //interactive mode
    visManager = new G4VisExecutive;
    visManager->Initialize();
    UImanager->ApplyCommand("/control/execute vis.mac");
    ui->SessionStart();
    delete ui;
  }
  else  {
    //batch mode
    G4String command = "/control/execute ";
    G4String fileName = positional.front();
    commandStatus=UImanager->ApplyCommand(command+fileName);
  }
  
  //job termination
  delete visManager;
  delete runManager;
  return commandStatus == 0 ? 0 : 1;
}

