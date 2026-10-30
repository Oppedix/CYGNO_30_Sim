# Known issues and scientific decisions

The current model is `cygno-copper-cathode-v4` in both modes. All 23 internal material
contributions (25 with optional gas) and external transport require new campaigns. The solid EFCu
cathode fills the retained 60 µm envelope; GEMs alone retain PMMA50/Cu5 skins.
The 500 mm gas volumes meet cathode and first GEM faces exactly.
Lens activity uses physical-lens Bq/piece from `CYGNO_radioactivity_excel_suprasil`;
its 3.843 kg reference mass changes no Geant4 geometry or transport.
See [geometry and masses](SINGLE_MODULE_GEOMETRY.md) and [assays](STUDY_SOURCES.md).
Dated model qualifications below are historical evidence, not v4 rate validation.

## Optional gas scenario

`--gas-bkg yes` adds C14 and Rn222 under [explicit optimistic assumptions](GAS_BACKGROUNDS.md),
not measured CYGNO gas activities. Stationary bulk short-lived Rn daughters are
tracked only to Pb210; ion drift, plate-out, recoil motion, purification kinetics
and the long-lived tail are excluded. The local macOS serial Geant4 11.3.1
Rn222 test also fails with PART122 while registering Po214; C14 passes in all
three storage modes. [Gas validation](GAS_VALIDATION.md) separates passing
software/analysis checks from incomplete transport qualification.

## Unresolved current geometry assumptions

| Component | Active implementation retained | Unresolved evidence |
|---|---|---|
| Field cage | 25 Cu bands/side, agreed 50% longitudinal coverage; shifted Boolean frames retain small transverse strip/gas and strip/support intersections | Transverse mechanical cross sections/alignment remain unverified |
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
normalization TSVs and the historical Table 7.1 geometry are references; their
old masses/model cannot normalize the updated detector. v4 retains
selected Table 7.1 component activities, with the separate per-piece lens update with its own new transport and actual
constructed quantities, as detailed in [source provenance](STUDY_SOURCES.md).
Published Table 7.2's no-cut (10,400] value
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

## External mode qualification

[External physics assumptions](../external/docs/PHYSICS.md) and
[executed validation](../external/docs/VALIDATION.md) are separate from internal
chain qualification. External uses HP neutron physics, preserves moving ion
recoils and stores all gas deposits. It does not add a quenching/readout model.
Hall C integral/shape and neutron flux-convention assumptions are explicit.
The local macOS/arm64 Geant4 11.3.1 neutron Cu20 smoke also reproduces PART122
while decaying a Cu-capture product to Zn66. The failed attempt is retained and
rejected as complete; no particle-table/data patch or decay suppression is used.
Qualify capture/recoil transport on the target Linux environment before production.
