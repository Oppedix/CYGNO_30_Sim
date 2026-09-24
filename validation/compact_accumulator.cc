// No Geant4 required: replay synthetic StepRecords through the production C++ accumulator.
#include "cygno/output/CompactAccumulator.hh"
#include <iostream>
#include <iomanip>
using namespace cygno::output;
int main(int argc,char**) {
  std::cout << std::setprecision(17);
  CompactAccumulator a([](const GroupRecord& g) {
    std::cout << "G " << g.eventNumber << ' ' << g.groupIndex << ' ' << std::quoted(g.particleName)
      << ' ' << std::quoted(g.nucleus) << ' ' << std::quoted(g.processType) << ' '
      << g.stepCount << ' ' << g.tracks.size() << ' ' << g.volumes.size() << '\n';
    int order=0;
    for (const auto& v:g.volumes) std::cout << "V " << g.eventNumber << ' ' << g.groupIndex << ' '
      << order++ << ' ' << v.volumeNumber << ' ' << v.energy << ' ' << v.x << ' ' << v.y << ' '
      << v.z << ' ' << v.firstTime << '\n';
  },[](const TrackRecord& t) {
    const auto& s=t.first;
    std::cout << "T " << s.eventNumber << ' ' << s.particleID << ' ' << s.particleTag << ' ' << s.parentID
      << ' ' << std::quoted(s.particleName) << ' ' << std::quoted(s.nucleus) << ' ' << std::quoted(s.processType)
      << ' ' << (t.groups.empty() ? -1 : t.groups.size()==1 ? t.groups[0] : -2) << '\n';
    for(int g:t.groups) std::cout << "L " << s.eventNumber << ' ' << s.particleID << ' ' << g << '\n';
  });
  StepRecord s; int event=-1;
  while(std::cin >> s.eventNumber >> s.particleID >> s.particleTag >> s.parentID >> s.volumeNumber
      >> std::quoted(s.particleName) >> std::quoted(s.nucleus) >> std::quoted(s.processType)
      >> s.x >> s.y >> s.z >> s.energyDeposit >> s.globalTimeNs) {
    if (argc>1 && event!=s.eventNumber) a.EndEvent(); // compare explicit lifecycle vs inferred boundary
    event=s.eventNumber; a.Add(s);
  }
  a.EndEvent(); a.EndEvent(); // EOF and idempotent lifecycle flush
}
