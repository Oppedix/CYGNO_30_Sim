#ifndef CYGNO_HIT_OUTPUT_HH
#define CYGNO_HIT_OUTPUT_HH
// The raw Hits interface: column IDs, names and types belong to one schema.
#include "globals.hh"
class G4Step;
namespace cygno::hits {
constexpr G4int ntupleId = 0;
enum Column { EventNumber, ParticleName, ParticleID, ParticleTag, ParentID,
              X, Y, Z, EnergyDeposit, VolumeNumber, Nucleus, ProcessType, Count };
void Book();
void WriteStep(const G4Step* step, const G4String& lastIon);
}
#endif
