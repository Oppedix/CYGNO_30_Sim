#include "Analysis.hh"
#include <filesystem>
#include <iostream>
#include <stdexcept>
int main(int argc, char** argv) try {
  if (argc!=2 && argc!=3 && argc!=5) throw std::runtime_error("Usage: SimpleProcessEvents input.root [output.root [--assume-geometry cygno-5x5x3-v1]]");
  const std::filesystem::path input(argv[1]);
  const std::string output=argc>=3 ? argv[2] : (input.parent_path()/("elab_"+input.filename().string())).string();
  if (std::filesystem::absolute(input).lexically_normal()==std::filesystem::absolute(output).lexically_normal()) throw std::runtime_error("Input and output must differ");
  if(argc==5 && std::string(argv[3])!="--assume-geometry") throw std::runtime_error("Unknown option");
  cygno::analysis::ProcessEvents(input.string(),output,argc==5?argv[4]:"");
  return 0;
} catch(const std::exception& e) { std::cerr<<e.what()<<"\n"; return 1; }
