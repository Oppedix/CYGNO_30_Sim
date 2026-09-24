#pragma once
// Pure C++ state machine: no Geant4, ROOT, random calls, or run-sized buffers.
#include "cygno/output/StepRecord.hh"
#include <functional>
#include <map>
#include <set>
#include <vector>
#include <limits>
#include <stdexcept>
namespace cygno::output {
struct GroupVolume {
  int volumeNumber;
  double energy, x, y, z, firstTime;
};
struct GroupRecord {
  int eventNumber=-1, groupIndex=0, stepCount=0;
  std::string particleName, nucleus, processType;
  bool ionizationSeen=false;
  std::vector<GroupVolume> volumes;
  std::map<int,std::size_t> volumeIndex;
  std::set<int> tracks;
};
struct TrackRecord {
  StepRecord first;
  std::vector<int> groups;
};
class CompactAccumulator {
public:
  using GroupSink=std::function<void(const GroupRecord&)>;
  using TrackSink=std::function<void(const TrackRecord&)>;
  CompactAccumulator(GroupSink groupSink, TrackSink trackSink)
    : emitGroup(std::move(groupSink)), emitTrack(std::move(trackSink)) {}
  void Add(const StepRecord& s) {
    if (event!=s.eventNumber) { EndEvent(); event=s.eventNumber; }
    auto& track=tracks.try_emplace(s.particleID,TrackRecord{s,{}}).first->second;
    if (s.particleName!="e-" && s.particleName!="e+" && s.particleName!="alpha") return;
    if (!group.volumes.empty()) {
      if (s.processType==group.processType && s.nucleus==group.nucleus && !group.ionizationSeen)
        group.particleName=s.particleName;
      else if (s.processType=="ionIoni" || s.processType=="eIoni") group.ionizationSeen=true;
      else Flush();
    }
    if (group.volumes.empty()) {
      group.eventNumber=event; group.groupIndex=nextGroup;
      group.particleName=s.particleName; group.nucleus=s.nucleus; group.processType=s.processType;
      // The first row deliberately does NOT set ionizationSeen.
    }
    if (group.stepCount==std::numeric_limits<int>::max()) throw std::overflow_error("Group StepCount overflow");
    ++group.stepCount;
    if (group.tracks.insert(s.particleID).second) track.groups.push_back(group.groupIndex);
    const auto inserted=group.volumeIndex.emplace(s.volumeNumber,group.volumes.size());
    if (inserted.second) group.volumes.push_back({s.volumeNumber,s.energyDeposit,s.x,s.y,s.z,s.globalTimeNs});
    else group.volumes[inserted.first->second].energy+=s.energyDeposit;
  }
  void EndEvent() {
    Flush();
    // Sort by event-local track ID for a deterministic diagnostic table.
    for (const auto& entry: tracks) emitTrack(entry.second);
    tracks.clear(); event=-1; nextGroup=0;
  }
private:
  void Flush() {
    if (group.volumes.empty()) return;
    emitGroup(group);
    if (nextGroup==std::numeric_limits<int>::max()) throw std::overflow_error("GroupIndex overflow");
    ++nextGroup; group=GroupRecord{};
  }
  GroupSink emitGroup;
  TrackSink emitTrack;
  int event=-1, nextGroup=0;
  GroupRecord group;
  std::map<int,TrackRecord> tracks;
};
}
