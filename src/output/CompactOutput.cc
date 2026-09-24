#include "cygno/output/CompactOutput.hh"
#include "G4AnalysisManager.hh"
#include "G4Exception.hh"
namespace cygno::output {
namespace {
constexpr int groups=4, volumes=5, tracks=6, links=7;
void Book(int expected,const char* name,std::initializer_list<std::pair<const char*,char>> columns) {
  auto* m=G4AnalysisManager::Instance();
  const auto id=m->CreateNtuple(name,name);
  if (id!=expected) G4Exception("BookCompact","CYGNO_SCHEMA",FatalException,"Unexpected compact ntuple ID");
  for(const auto& c:columns) {
    if(c.second=='I') m->CreateNtupleIColumn(id,c.first);
    else if(c.second=='D') m->CreateNtupleDColumn(id,c.first);
    else m->CreateNtupleSColumn(id,c.first);
  }
  m->FinishNtuple(id);
}
}
void BookCompact() {
  Book(groups,"Groups",{{"EventNumber",'I'},{"GroupIndex",'I'},{"ParticleName",'S'},
    {"Nucleus",'S'},{"ProcessType",'S'},{"StepCount",'I'},{"TrackCount",'I'},{"VolumeCount",'I'}});
  Book(volumes,"GroupVolumes",{{"EventNumber",'I'},{"GroupIndex",'I'},{"VolumeOrder",'I'},
    {"VolumeNumber",'I'},{"EnergyDeposit",'D'},{"x_first",'D'},{"y_first",'D'},{"z_first",'D'},{"FirstHitTime_ns",'D'}});
  Book(tracks,"Tracks",{{"EventNumber",'I'},{"ParticleID",'I'},{"ParticleTag",'I'},{"ParentID",'I'},
    {"ParticleName",'S'},{"Nucleus",'S'},{"ProcessType",'S'},{"GroupIndex",'I'}});
  Book(links,"TrackGroups",{{"EventNumber",'I'},{"ParticleID",'I'},{"GroupIndex",'I'}});
}
void WriteGroup(const GroupRecord& g) {
  auto* m=G4AnalysisManager::Instance();
  m->FillNtupleIColumn(groups,0,g.eventNumber); m->FillNtupleIColumn(groups,1,g.groupIndex);
  m->FillNtupleSColumn(groups,2,g.particleName); m->FillNtupleSColumn(groups,3,g.nucleus);
  m->FillNtupleSColumn(groups,4,g.processType); m->FillNtupleIColumn(groups,5,g.stepCount);
  m->FillNtupleIColumn(groups,6,g.tracks.size()); m->FillNtupleIColumn(groups,7,g.volumes.size());
  m->AddNtupleRow(groups);
  int order=0;
  for (const auto& v:g.volumes) {
    m->FillNtupleIColumn(volumes,0,g.eventNumber); m->FillNtupleIColumn(volumes,1,g.groupIndex);
    m->FillNtupleIColumn(volumes,2,order++); m->FillNtupleIColumn(volumes,3,v.volumeNumber);
    m->FillNtupleDColumn(volumes,4,v.energy); m->FillNtupleDColumn(volumes,5,v.x);
    m->FillNtupleDColumn(volumes,6,v.y); m->FillNtupleDColumn(volumes,7,v.z);
    m->FillNtupleDColumn(volumes,8,v.firstTime); m->AddNtupleRow(volumes);
  }
}
void WriteTrack(const TrackRecord& t) {
  auto* m=G4AnalysisManager::Instance(); const auto& s=t.first;
  m->FillNtupleIColumn(tracks,0,s.eventNumber); m->FillNtupleIColumn(tracks,1,s.particleID);
  m->FillNtupleIColumn(tracks,2,s.particleTag); m->FillNtupleIColumn(tracks,3,s.parentID);
  m->FillNtupleSColumn(tracks,4,s.particleName); m->FillNtupleSColumn(tracks,5,s.nucleus);
  m->FillNtupleSColumn(tracks,6,s.processType);
  m->FillNtupleIColumn(tracks,7,t.groups.empty() ? -1 : t.groups.size()==1 ? t.groups.front() : -2);
  m->AddNtupleRow(tracks);
  for (int index:t.groups) {
    m->FillNtupleIColumn(links,0,s.eventNumber); m->FillNtupleIColumn(links,1,s.particleID);
    m->FillNtupleIColumn(links,2,index); m->AddNtupleRow(links);
  }
}
}
