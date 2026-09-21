# Historical module-center reference

`legacy-25x3-centers.tsv` transcribes the cathode-center and gas-counter loops
in SamueleTorelli/CYGNO_30_Sim commit
`26ddbdbd110426c38ea71ba3d1341a2b26b6d090`, `src/DetectorConstruction.cc`,
lines 230-249 and 944-991. Coordinates are mm. The outer loop is X=-12..12,
the inner loop Y=-1..1; pitches are 500+4 and 800+4 mm. All Z centers are zero.
The module ID is the positive-side gas counter. Negative-side gas IDs add 75;
local gas offsets are +/-250.25 mm in the code-compatible model.

This fixture is intentionally independent of the profile factory. Do not
regenerate it from the current implementation to make a failing test pass.
