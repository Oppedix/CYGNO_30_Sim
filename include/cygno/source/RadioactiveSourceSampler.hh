#ifndef CYGNO_RADIOACTIVE_SOURCE_SAMPLER_HH
#define CYGNO_RADIOACTIVE_SOURCE_SAMPLER_HH
// Source policy is separate from detector construction and event bookkeeping.
#include "G4ThreeVector.hh"
#include "globals.hh"
class DetectorConstruction;
class G4VPhysicalVolume;
struct SourcePoint {
  G4ThreeVector position;
  const G4VPhysicalVolume* volume = nullptr;
};
class RadioactiveSourceSampler {
 public:
  explicit RadioactiveSourceSampler(DetectorConstruction* detector) : fDetector(detector) {}
  // Exactly one uniform volume choice, the solid's GetPointOnSurface(), and one
  // depth draw. No rejection/resampling: containment is a diagnostic, not a cut.
  SourcePoint Sample(const G4String& component);
 private:
  DetectorConstruction* fDetector;
};
#endif
