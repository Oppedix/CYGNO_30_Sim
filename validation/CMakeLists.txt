cmake_minimum_required(VERSION 3.16...3.21)
project(CYGNO_geometry_validation LANGUAGES CXX)
find_package(Geant4 REQUIRED)
include(${Geant4_USE_FILE})
# Optional saved source directory permits comparison with a pre-refactor copy.
set(CYGNO_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/.." CACHE PATH "Simulation source tree")
foreach(tool geometry_snapshot geometry_audit)
  add_executable(${tool} ${tool}.cc
    ${CYGNO_SOURCE_DIR}/src/DetectorConstruction.cc
    ${CYGNO_SOURCE_DIR}/src/SensitiveDetector.cc
    ${CYGNO_SOURCE_DIR}/src/PrimaryGeneratorAction.cc)
  target_include_directories(${tool} PRIVATE ${CYGNO_SOURCE_DIR}/include)
  target_link_libraries(${tool} PRIVATE ${Geant4_LIBRARIES})
endforeach()
