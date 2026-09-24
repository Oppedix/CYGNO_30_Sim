# Historical material and provenance

These files are retained for study and reproducibility and are **not active
application code**. `scaffolding/` holds the unused custom PhysicsList and
HistoManager, including original backups. `rdecay01/` holds inherited Geant4
example macros, README, history and build instructions; they are historical,
not current instructions. Some commands assume example histogram booking that
is inactive in CYGNO. File references in its data macros resolve from the current
repository root, not from an arbitrary build directory.

`analysis/05a2b92/` preserves original analysis implementations/tables.
`analysis/` also holds older ROOT macros. Their relative includes reflect their
historical context; the normalization transcription test supplies the current
analysis include path when compiling reference tables. `config/` preserves old
macro generators and ambiguous GEMs/Rings runs. Do not automatically map these
to copper/core or support/strip. `notes/` holds inherited notes without elevating
them to authoritative physics input.

The application derives from the Geant4 rdecay01 example. Original license
headers were retained; see [LICENSE](../LICENSE) and the identical external copy
[data/Geant4-LICENSE](../data/Geant4-LICENSE). Reference outputs under
`data/references/rdecay01/` are historical text, not binaries to execute or current
regression expectations. Generated executables, ROOT files, editor backups and
CMake products were removed from Git tracking, not restored for the build.


`study/combined/` retains runner.py, root_io.py and figures.py from the superseded
combined PyROOT/C++ workflow. Active Stage A/B imports were audited before moving:
only its dedicated regression path still uses them, and that test now imports
this explicit legacy package. The renderer shares canonical table transcription.
These files were moved, not deleted. New campaigns use study/simulate.py and
study/analyze.py. All currently tested C++ reference tools, including specialized
plotters/macros, remain in analysis/reference_cpp rather than legacy.
