// Write one Hits ntuple row for every step delivered by a sensitive gas volume.
#ifndef DETECTOR_HH
#define DETECTOR_HH

#include "G4VSensitiveDetector.hh"
#include "G4Step.hh"
#include "G4TouchableHistory.hh"
#include "RunAction.hh"

class SensitiveDetector : public G4VSensitiveDetector
{

public:
  SensitiveDetector(G4String);
  ~SensitiveDetector();

  // TrackingAction updates this label when an ion begins tracking.
  void SetLastDecay(G4String aString){lastDecay = aString;}
  G4String GetLastDecay(){return lastDecay;}
  
private:
  virtual G4bool ProcessHits(G4Step *, G4TouchableHistory*);

  G4String lastDecay;
  
};


#endif
