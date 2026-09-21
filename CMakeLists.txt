cmake_minimum_required(VERSION 3.16...3.31)
project(CYGNO_30_Sim VERSION 1.0 LANGUAGES CXX)

if(PROJECT_SOURCE_DIR STREQUAL PROJECT_BINARY_DIR)
  message(FATAL_ERROR "Use an out-of-source build directory")
endif()
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS common/DetectorGeometry.hh)
file(SHA256 "${PROJECT_SOURCE_DIR}/common/DetectorGeometry.hh" CYGNO_GEOMETRY_HASH)
configure_file(common/BuildInfo.hh.in generated/BuildInfo.hh @ONLY)

option(WITH_GEANT4_UIVIS "Enable Geant4 interactive visualization" ON)
option(CYGNO_BUILD_ANALYSIS "Build the separate CERN ROOT post-processing programs" OFF)
if(WITH_GEANT4_UIVIS)
  find_package(Geant4 11 REQUIRED ui_all vis_all)
else()
  find_package(Geant4 11 REQUIRED)
endif()

# A single explicit target owns the active application code. The quarantined
# alternative physics/histogram classes in legacy/ are not linked into it.
add_library(cygno_sim
  src/geometry/DetectorConstruction.cc
  src/source/PrimaryGeneratorAction.cc
  src/source/RadioactiveSourceSampler.cc
  src/actions/ActionInitialization.cc
  src/actions/EventAction.cc
  src/actions/TrackingAction.cc
  src/actions/TrackingMessenger.cc
  src/actions/Run.cc
  src/actions/RunAction.cc
  src/output/SensitiveDetector.cc
  src/output/HitOutput.cc)
target_compile_features(cygno_sim PUBLIC cxx_std_17)
target_include_directories(cygno_sim PUBLIC include "${PROJECT_SOURCE_DIR}" "${PROJECT_BINARY_DIR}/generated")
target_link_libraries(cygno_sim PUBLIC ${Geant4_LIBRARIES})
target_compile_definitions(cygno_sim PUBLIC ${Geant4_DEFINITIONS})
add_executable(rdecay01 app/rdecay01.cc)
target_link_libraries(rdecay01 PRIVATE cygno_sim)

# Preserve `cd build && ./rdecay01` while organizing the source macros in config/.
configure_file(config/vis.mac vis.mac COPYONLY)
file(COPY config DESTINATION "${PROJECT_BINARY_DIR}")
file(MAKE_DIRECTORY "${PROJECT_BINARY_DIR}/outfiles_V2")

if(CYGNO_BUILD_ANALYSIS)
  add_subdirectory(analysis)
endif()
include(CTest)
if(BUILD_TESTING)
  add_subdirectory(validation)
endif()
install(TARGETS rdecay01 RUNTIME DESTINATION bin)
install(DIRECTORY config DESTINATION share/CYGNO_30_Sim)
