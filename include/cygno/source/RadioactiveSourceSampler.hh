#ifndef CYGNO_RADIOACTIVE_SOURCE_SAMPLER_HH
#define CYGNO_RADIOACTIVE_SOURCE_SAMPLER_HH
// Source policy is separate from detector construction and event bookkeeping.
#include "G4ThreeVector.hh"
#include "globals.hh"
class DetectorConstruction;
class G4VPhysicalVolume;
class G4VSolid;
struct SourcePoint {
  G4ThreeVector position;
  const G4VPhysicalVolume* volume = nullptr;
};
class RadioactiveSourceSampler {
 public:
  explicit RadioactiveSourceSampler(DetectorConstruction* detector) : fDetector(detector) {}
  // Uniform bulk sampling; no rejection or surface-depth approximation.
  static G4ThreeVector SampleLocal(G4VSolid* solid);
  SourcePoint Sample(const G4String& component);
 private:
  DetectorConstruction* fDetector;
};
#endif
