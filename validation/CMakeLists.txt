cmake_minimum_required(VERSION 3.16...3.21)
project(CYGNO_geometry_validation LANGUAGES CXX)
find_package(Geant4 REQUIRED)
include(${Geant4_USE_FILE})
# Separate opt-in tool: the simulation build and physics setup are untouched.
add_executable(geometry_snapshot geometry_snapshot.cc
  ../src/DetectorConstruction.cc ../src/SensitiveDetector.cc)
target_include_directories(geometry_snapshot PRIVATE ../include)
target_link_libraries(geometry_snapshot PRIVATE ${Geant4_LIBRARIES})
