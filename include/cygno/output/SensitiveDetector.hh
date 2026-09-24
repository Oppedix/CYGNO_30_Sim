// Write one Hits ntuple row for every step delivered by a sensitive gas volume.
#ifndef DETECTOR_HH
#define DETECTOR_HH

#include "G4VSensitiveDetector.hh"
#include "cygno/output/CompactOutput.hh"
#include "G4Step.hh"
#include "G4TouchableHistory.hh"

class SensitiveDetector : public G4VSensitiveDetector
{

public:
  SensitiveDetector(G4String);
  ~SensitiveDetector();
  void Initialize(G4HCofThisEvent*) override;
  void EndOfEvent(G4HCofThisEvent*) override;

  // TrackingAction updates this label when an ion begins tracking.
  void SetLastDecay(G4String aString){lastDecay = aString;}
  G4String GetLastDecay(){return lastDecay;}
  
private:
  G4bool ProcessHits(G4Step *, G4TouchableHistory*) override;

  G4String lastDecay;
  cygno::output::CompactAccumulator compact;
  
};


#endif
