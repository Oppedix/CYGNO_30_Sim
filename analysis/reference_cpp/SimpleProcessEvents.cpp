#include "Analysis.hh"
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <vector>
int main(int argc, char** argv) try {
  std::vector<std::string> paths;
  std::string layout, model;
  for (int i=1; i<argc; ++i) {
    const std::string arg(argv[i]);
    if (arg=="--assume-layout" || arg=="--assume-geometry" || arg=="--assume-model") {
      auto& value = arg=="--assume-model" ? model : layout;
      if (!value.empty() || i+1==argc) throw std::runtime_error("Missing or duplicate assumption");
      value=argv[++i];
      if (value.empty() || value.rfind("--",0)==0) throw std::runtime_error("Missing assumption value");
    } else if (arg.rfind("--",0)==0) throw std::runtime_error("Unknown option: " + arg);
    else paths.push_back(arg);
  }
  if (paths.empty() || paths.size()>2)
    throw std::runtime_error("Usage: SimpleProcessEvents input.root [output.root] [--assume-layout PROFILE --assume-model code-compatible]");
  const std::filesystem::path input(paths[0]);
  const std::string output=paths.size()==2 ? paths[1] : (input.parent_path()/("elab_"+input.filename().string())).string();
  if (std::filesystem::weakly_canonical(input)==std::filesystem::weakly_canonical(output) ||
      (std::filesystem::exists(output) && std::filesystem::equivalent(input,output)))
    throw std::runtime_error("Input and output must differ");
  cygno::analysis::ProcessEvents(input.string(),output,layout,model);
  return 0;
} catch(const std::exception& e) { std::cerr<<e.what()<<"\n"; return 1; }
