// Raw output consumes the same extracted record as compact accumulation.
#include "cygno/output/HitOutput.hh"
#include "G4AnalysisManager.hh"
#include "G4Exception.hh"
#include "G4RunManager.hh"
#include "G4Step.hh"
#include "G4Track.hh"
#include <array>
#include "G4SystemOfUnits.hh"
#include <stdexcept>
namespace cygno::output {
namespace { std::string mode = "raw"; }
void SetMode(const std::string& value) {
  if (value!="raw" && value!="compact" && value!="both") throw std::invalid_argument("Invalid output mode: " + value);
  mode=value;
}
const std::string& Mode() { return mode; }
bool RawEnabled() { return mode!="compact"; }
bool CompactEnabled() { return mode!="raw"; }
}
namespace cygno::hits {
void Book() {
  enum Type { Integer, String, Double };
  struct Definition { Column id; const char* name; Type type; };
  constexpr std::array<Definition, Count> columns{{
    {EventNumber,"EventNumber",Integer}, {ParticleName,"ParticleName",String},
    {ParticleID,"ParticleID",Integer}, {ParticleTag,"ParticleTag",Integer},
    {ParentID,"ParentID",Integer}, {X,"x_hits",Double}, {Y,"y_hits",Double},
    {Z,"z_hits",Double}, {EnergyDeposit,"EnergyDeposit",Double},
    {VolumeNumber,"VolumeNumber",Integer}, {Nucleus,"Nucleus",String},
    {ProcessType,"ProcessType",String}, {GlobalTime,"GlobalTime_ns",Double}
  }};
  auto* manager=G4AnalysisManager::Instance();
  const auto id=manager->CreateNtuple("Hits","Hits");
  if (id != ntupleId) G4Exception("hits::Book", "CYGNO_SCHEMA", FatalException, "Unexpected Hits ntuple ID");
  for (const auto& column : columns) {
    G4int booked=-1;
    switch(column.type) {
      case Integer: booked=manager->CreateNtupleIColumn(id,column.name); break;
      case String: booked=manager->CreateNtupleSColumn(id,column.name); break;
      case Double: booked=manager->CreateNtupleDColumn(id,column.name); break;
    }
    if (booked != column.id) G4Exception("hits::Book", "CYGNO_SCHEMA", FatalException, "Column ordering mismatch");
  }
  manager->FinishNtuple(id);
}
cygno::output::StepRecord ExtractStep(const G4Step* step, const G4String& lastIon) {
  const auto* track=step->GetTrack();
  const auto* pre=step->GetPreStepPoint();
  const auto pos=pre->GetPosition();
  const auto name=track->GetParticleDefinition()->GetParticleName();
  const int tag=name=="e-" ? 0 : name=="e+" ? 1 : name=="gamma" ? 2 : name=="alpha" ? 3 : -1;
  // Nucleus is last tracked ion; ProcessType is CREATOR, not step process.
  return {G4RunManager::GetRunManager()->GetCurrentEvent()->GetEventID(),
    track->GetTrackID(), tag, track->GetParentID(), track->GetVolume()->GetCopyNo(),
    name, lastIon, track->GetCreatorProcess() ? track->GetCreatorProcess()->GetProcessName() : "",
    pos.x(), pos.y(), pos.z(), step->GetTotalEnergyDeposit(), pre->GetGlobalTime()/ns};
}
void Write(const cygno::output::StepRecord& s) {
  auto* m=G4AnalysisManager::Instance();
  m->FillNtupleIColumn(ntupleId,EventNumber,s.eventNumber);
  m->FillNtupleSColumn(ntupleId,ParticleName,s.particleName);
  m->FillNtupleIColumn(ntupleId,ParticleID,s.particleID);
  m->FillNtupleIColumn(ntupleId,ParticleTag,s.particleTag);
  m->FillNtupleIColumn(ntupleId,ParentID,s.parentID);
  m->FillNtupleDColumn(ntupleId,X,s.x);
  m->FillNtupleDColumn(ntupleId,Y,s.y);
  m->FillNtupleDColumn(ntupleId,Z,s.z);
  m->FillNtupleDColumn(ntupleId,EnergyDeposit,s.energyDeposit);
  m->FillNtupleIColumn(ntupleId,VolumeNumber,s.volumeNumber);
  m->FillNtupleSColumn(ntupleId,Nucleus,s.nucleus);
  m->FillNtupleSColumn(ntupleId,ProcessType,s.processType);
  m->FillNtupleDColumn(ntupleId,GlobalTime,s.globalTimeNs);
  m->AddNtupleRow(ntupleId);
}
}
