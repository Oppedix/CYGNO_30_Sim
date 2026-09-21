find_package(ROOT 6 REQUIRED COMPONENTS Core RIO Tree Hist Graf Gpad Physics)
foreach(program SimpleProcessEvents PlotNormalizedSpectra PlotNormalizedSpectra_single PlotNormalizedSpectra_GEMchain)
  add_executable(${program} ${program}.cpp)
  target_compile_features(${program} PRIVATE cxx_std_17)
  target_link_libraries(${program} PRIVATE ROOT::Core ROOT::RIO ROOT::Tree ROOT::Hist ROOT::Graf ROOT::Gpad ROOT::Physics)
endforeach()

target_sources(SimpleProcessEvents PRIVATE ProcessEvents.cc)
target_include_directories(SimpleProcessEvents PRIVATE "${PROJECT_BINARY_DIR}/generated")
