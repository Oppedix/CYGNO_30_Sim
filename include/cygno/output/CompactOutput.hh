#pragma once
#include "cygno/output/CompactAccumulator.hh"
namespace cygno::output {
void BookCompact();
void WriteGroup(const GroupRecord& group);
void WriteTrack(const TrackRecord& track);
}
