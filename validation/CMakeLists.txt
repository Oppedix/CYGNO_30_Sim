# Validation reuses the same compiled simulation classes as the application.
foreach(tool geometry_snapshot geometry_audit)
  add_executable(${tool} ${tool}.cc)
  target_link_libraries(${tool} PRIVATE cygno_sim)
endforeach()

add_executable(source_checks source_checks.cc)
target_link_libraries(source_checks PRIVATE cygno_sim)
add_test(NAME source_and_mass COMMAND source_checks)
find_package(Python3 COMPONENTS Interpreter REQUIRED)
add_test(NAME geometry COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/run_checks.py geometry ${PROJECT_BINARY_DIR})
add_test(NAME transport COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/run_checks.py transport ${PROJECT_BINARY_DIR})
if(CYGNO_BUILD_ANALYSIS)
  add_test(NAME analysis COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test_analysis.py ${PROJECT_BINARY_DIR})
  add_test(NAME root_geometry COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/check_analysis.py ${PROJECT_BINARY_DIR}/validation-results/geometry/placements.tsv ${PROJECT_BINARY_DIR}/validation-results/root-geometry)
  set_tests_properties(root_geometry PROPERTIES DEPENDS geometry)
endif()
set_tests_properties(source_and_mass geometry transport PROPERTIES TIMEOUT 180)

# Optional manual external reproducer, deliberately not a passing test.
add_executable(external_decay_probe EXCLUDE_FROM_ALL external_decay_probe.cc)
target_link_libraries(external_decay_probe PRIVATE ${Geant4_LIBRARIES})
