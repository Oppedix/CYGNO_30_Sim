# Known issues and scientific decisions

The active detector is `cygno-300elj-v1`, with `uniform-volume-v1` sources and
`cygno-300elj-radioassay-v1` assays. [SINGLE_MODULE_GEOMETRY.md](SINGLE_MODULE_GEOMETRY.md)
describes the constructed geometry and masses. Software checks alone do not
establish physical background-rate accuracy.

## Resolved geometry and source issues

GEMs and the cathode are explicit Cu5/300ELJ50/Cu5 µm slabs without material
intersections. The 500 mm gas boundaries meet the cathode and first GEM exactly.
GEM clear spacing is 2.000 mm (2.060 mm centre pitch), filled with non-sensitive
He/CF4. Uniform-volume sampling replaces the surface/inward-depth shortcut;
deterministic containment, analytic moments, ranges and rotated placements are
tested. Model/policy/hash gates reject earlier data rather than relabel them.
Same-event primary placement, isotope updates, mass-map accounting, event/EOF
flushes and output ownership checks remain in place.

## Unresolved current geometry assumptions

| Component | Active implementation retained | Unresolved evidence |
|---|---|---|
| Field cage | 4 Cu strips/side, 44% longitudinal coverage; shifted Boolean frames retain small strip/gas and strip/support intersections | Thesis prose describes 5 bands; mechanical cross sections/alignment are unverified |
| Vessel | One common rectangular 5 mm copper shell, with no optical apertures; planar optics outside | Thesis prose describes 10 mm; physical enclosure/shielding paths unverified |
| Lens | Radius 10 mm, thickness 2 mm, SiO2-like transport | Thesis prose says diameter 10 mm, thickness 1 mm |
| Sensor | Silicon 10.6×18.8×1 mm³ | Thesis prose gives 18.0 mm in one direction |

No inter-module intersections, World protrusions or vessel crossings are allowed
by geometry validation. This does not make the retained field cage overlap-free.
GEM holes are absent: simulated foil fill is 100%, without an inferred physical
perforation factor. Assay uncertainty is retained as provenance, not propagated
into the existing statistical-error analysis.

## Analysis and attribution

`Nucleus` follows the last tracked ion and is not proven per-hit ancestry.
Inherited process/ionization groups can merge tracks and are not physical sites.
The fiducial cut uses the first grouped position. The optional topology selection
cannot distinguish separate sites compressed into the same group/gas volume.
Poisson group-count errors are not independent-primary or material-systematic
errors. World-Z position plots retain their historical range and can overflow.
The new overlay/range figures change presentation only.

The original Figure 7.5 production inputs/revision remain unresolved. Historical
normalization TSVs and Table 7.1 are references; their old masses/model cannot
normalize the updated detector. Published Table 7.2's no-cut (10,400] value
exceeds its >10 value; it remains a reference discrepancy, never a rate-tuning
constraint.

## Environment-specific Geant4 PART122

Full-chain Th232/Bi212 transport has independently failed with duplicate-ion
registration `PART122` on macOS/arm64, including a geometry-free reproducer,
stock Geant4 11.3.1 rdecay01 and a truly serial build. Earlier 11.4.2 matrix smoke
also failed across U/Th chains. These dated results are in
[the retained finalization evidence](study-results/finalization.json).

The operator reported four passing preflight cases on Ubuntu 22.04.5 x86_64,
GCC 11.4.0, private Geant4 11.3.1 serial, with matching datasets. This is empirical
environment qualification, not evidence of a universal version fix. Local U238
threshold checks pass: explicitly enabling `1e60 year` permits daughter decay,
where the one-year default suppresses it.

The four-case production preflight remains mandatory. A transport failure is
retained and excluded from complete production; a ROOT file is not proof of
successful transport. No particle-table patch, exception suppression, nuclear
state removal, decay-chain alteration or dataset edit is used to pass tests.
`validation/external_decay_probe.cc` and the Bi212 macro remain diagnostic
reproducers. Geometry tests and short passing decay tests do not certify full
U/Th chains in this environment.
