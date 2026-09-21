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
// Resolve a physical component and sample the inherited surface/depth model.
#include "cygno/source/RadioactiveSourceSampler.hh"
#include "cygno/geometry/DetectorConstruction.hh"
#include "G4LogicalVolume.hh"
#include "G4VSolid.hh"
#include "G4Exception.hh"
#include "Randomize.hh"

// Choose a component uniformly from its ordered list, then move a surface point
// inward by a random depth along the surface normal. This is the existing source
// model, not a uniform-in-volume sampler. All placements currently have no rotation.
// Accepted names are the exact strings below; invalid names fail explicitly.
SourcePoint RadioactiveSourceSampler::Sample(const G4String& El){

  std::vector<G4String> Elements;
  G4double width;
  
  if(El == "Cathodes"){
    Elements = fDetector->GetCathodesList();
    width = fDetector->GetCathodeWidth();
  } else if (El == "GEMsOuter"){
    Elements = fDetector->GetGEMsOuterLists();
    width = fDetector->GetGEMOuterWidth();
  } else if (El == "GEMsCore"){
    Elements = fDetector->GetGEMsInnerLists();
    width = fDetector->GetGEMInnerWidth();
  } else if (El == "RingSupports"){
    Elements = fDetector->GetRingsSupportList();
    width = fDetector->GetRingsSupportWidth();
  } else if (El == "RingStrips"){
    Elements = fDetector->GetRingStripstList();
    width = fDetector->GetRingStripsWidth();
  } else if (El == "Resistors"){
    Elements = fDetector->GetResistorList();
    width = fDetector->GetResistorWidth();
  } else if (El == "Vessel"){
    Elements.push_back("Vessel");
    width = fDetector->GetVesselWidth();
  } else if (El == "Lens"){
    Elements = fDetector->GetLensList();
    width = fDetector->GetLensWidth();
  } else if (El == "Sensors"){
    Elements = fDetector->GetSensorsList();
    width = fDetector->GetSensorWidth();
  }

  
  // Reject an invalid component instead of indexing an empty source list. Do
  // not guess what the legacy ambiguous names "GEMs" or "Rings" should mean.
  if (Elements.empty()) {
    G4ExceptionDescription message;
    message << "Unknown or empty radioactive component: " << El
            << ". Choose Cathodes, GEMsOuter, GEMsCore, RingSupports, RingStrips, "
            << "Resistors, Vessel, Lens or Sensors.";
    G4Exception("RadioactiveSourceSampler::Sample",
                "CYGNO_SOURCE", FatalException, message);
    return {};
  }

  G4int min = 0;
  G4int max = Elements.size();
  
  G4int nEl = min + (int)(G4UniformRand() * (max - min));  //select a random element in the vector
    
  G4VPhysicalVolume* vol = fDetector->GetVolumeStored()->GetVolume(Elements[nEl]); // get the corresponding random physical volume

  G4VSolid* solid = vol->GetLogicalVolume()->GetSolid(); // get the corresponding solid
  
  G4ThreeVector PointOnSurface = solid->GetPointOnSurface(); // get a random point on the surface

  G4ThreeVector Normal = solid->SurfaceNormal(PointOnSurface); // get the normal to the surface in that point
  
  G4ThreeVector TranslationVolume = vol->GetObjectTranslation(); // get the translation vector of that physical volume
  
  G4ThreeVector Point = TranslationVolume + PointOnSurface - G4UniformRand()*width*Normal; //random point in the random volume as the translation vector + a point on the surface + a random depth 

  return {Point, vol};
}
