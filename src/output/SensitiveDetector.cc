// A sensitive gas step becomes a row immediately; no energy/particle filter.
#include "cygno/output/SensitiveDetector.hh"
#include "cygno/output/HitOutput.hh"
SensitiveDetector::SensitiveDetector(G4String name) : G4VSensitiveDetector(name) {}
SensitiveDetector::~SensitiveDetector() = default;
G4bool SensitiveDetector::ProcessHits(G4Step* step, G4TouchableHistory*) {
  cygno::hits::WriteStep(step, GetLastDecay());
  return true;
}
