#ifndef CYGNO_ANALYSIS_HH
#define CYGNO_ANALYSIS_HH
#include "FileIdentity.hh"
#include <string>
namespace cygno::analysis {
void ProcessEvents(const std::string& input, const std::string& output,
                   const std::string& assumedLayout = "",
                   const std::string& assumedModel = "");
}
#endif
