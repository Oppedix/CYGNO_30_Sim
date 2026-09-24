#pragma once
#include <string>
namespace cygno::output {
// Extracted exactly once; mm, MeV, and explicit event-relative nanoseconds.
struct StepRecord {
  int eventNumber, particleID, particleTag, parentID, volumeNumber;
  std::string particleName, nucleus, processType;
  double x, y, z, energyDeposit, globalTimeNs;
};
// Immutable after main() parses options, before workers are constructed.
void SetMode(const std::string& mode);
const std::string& Mode();
bool RawEnabled();
bool CompactEnabled();
constexpr int schemaVersion = 1;
constexpr const char* processingVersion = "event-boundaries-and-eof-v2";
constexpr const char* timingDefinition = "pre-step global time / ns; Geant4 event-relative, not inter-event time";
}
