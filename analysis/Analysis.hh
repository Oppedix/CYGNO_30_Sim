#ifndef CYGNO_ANALYSIS_HH
#define CYGNO_ANALYSIS_HH
#include <string>
class TFile;
namespace cygno::analysis {
// Unknown geometry is rejected unless the researcher explicitly identifies an
// unversioned file as the current layout. An old 25x3 file is not convertible here.
void RequireGeometry(TFile& file, const std::string& assumedGeometry = "");
void CopyMetadata(TFile& input, TFile& output);
void ProcessEvents(const std::string& input, const std::string& output,
                   const std::string& assumedGeometry = "");
}
#endif
