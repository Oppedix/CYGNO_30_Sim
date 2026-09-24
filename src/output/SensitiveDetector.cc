// One extraction, two sinks; output never calls the random engine.
#include "cygno/output/SensitiveDetector.hh"
#include "cygno/output/HitOutput.hh"
SensitiveDetector::SensitiveDetector(G4String name) : G4VSensitiveDetector(name),
  compact(cygno::output::WriteGroup, cygno::output::WriteTrack) {}
SensitiveDetector::~SensitiveDetector() = default;
void SensitiveDetector::Initialize(G4HCofThisEvent*) {
  if (cygno::output::CompactEnabled()) compact.EndEvent();
  // Do not reset lastDecay: its historical cross-event behavior is intentional.
}
void SensitiveDetector::EndOfEvent(G4HCofThisEvent*) {
  if (cygno::output::CompactEnabled()) compact.EndEvent();
}
G4bool SensitiveDetector::ProcessHits(G4Step* step, G4TouchableHistory*) {
  const auto record=cygno::hits::ExtractStep(step, GetLastDecay());
  if (cygno::output::RawEnabled()) cygno::hits::Write(record);
  if (cygno::output::CompactEnabled()) compact.Add(record);
  return true;
}
