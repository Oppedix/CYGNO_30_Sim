#pragma once
#include "globals.hh"
#include "cygno/output/StepRecord.hh"
class G4Step;
namespace cygno::hits {
// IDs 1/2 remain scientific metadata/accounting in every mode.
constexpr G4int ntupleId = 0;
enum Column { EventNumber, ParticleName, ParticleID, ParticleTag, ParentID,
              X, Y, Z, EnergyDeposit, VolumeNumber, Nucleus, ProcessType, GlobalTime, Count };
void Book();
cygno::output::StepRecord ExtractStep(const G4Step* step, const G4String& lastIon);
void Write(const cygno::output::StepRecord& step);
}
