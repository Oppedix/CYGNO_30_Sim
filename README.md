# CYGNO-30 simulation

One shared Geant4 application serves two independent background workflows.
Build it once; choose the workflow at run time.

| Area | Responsibility | Start here |
|---|---|---|
| **Common** | Geant4 application, geometry, materials, CAD/reference context and shared technical documentation | [Setup and build](docs/SETUP.md), [module geometry](docs/SINGLE_MODULE_GEOMETRY.md), [layouts](docs/LAYOUT.md), [shielding](docs/EXTERNAL_SHIELDING.md) |
| **Internal** | Component radioactivity; **v4** | [Internal guide](internal/README.md) |
| **External** | LNGS gamma/neutron proxy scenarios with **Cu20** shielding | [External guide](external/README.md) |

The active detector uses analytical Geant4 solids, not an imported CAD detector.
Both modes default to **`cygno-copper-cathode-v4`**: one solid EFCu cathode
per module, with Acrylic/PMMA cores and copper skins only in the GEMs.
The cathode envelope remains 500 × 800 × 0.060 mm. Internal radioactivity uses
23 contributions from `cygno-radioassay-v4`; lens activity is **Bq/piece**, from
`CYGNO_radioactivity_excel_suprasil`, normalized by actual lens placements.
The 3.843 kg reference mass describes **one physical lens**; Geant4 lens geometry
and transport remain unchanged. External gamma/neutron sources use this same
detector with their separate physics and environmental normalization.

**v4 requires new transport and new campaign directories in both modes.**
Existing results are never converted or resumed as v4. Historical reconstruction
is isolated in the [model history](docs/history/DETECTOR_MODELS.md).

## Install and build the common application

Requirements: Git, CMake ≥3.16, a C++17 compiler, Geant4 11 with matching datasets
(including G4NDL for external neutrons), and Python ≥3.10. Simulation writes ROOT
files through Geant4 and needs no CERN ROOT, PyROOT or analysis packages.

Follow [setup](docs/SETUP.md) for complete clone, activation and build commands,
with separate local, private Linux and CNAF examples. After selecting that
environment and defining its paths, the common build is:

```bash
# Directory: repository root ($CYGNO_SRC); Geant4 environment already active.
cd "$CYGNO_SRC"
cmake -S . -B "$CYGNO_BUILD" -DCMAKE_BUILD_TYPE=Release \
  -DWITH_GEANT4_UIVIS=OFF -DCYGNO_BUILD_ANALYSIS=OFF -DBUILD_TESTING=OFF \
  -DGeant4_DIR="$Geant4_DIR"
cmake --build "$CYGNO_BUILD" --target rdecay01 geometry_quantities --parallel
```

This is the only detector build. The two standalone C++ ROOT analyzers are
compiled separately on an analysis machine, as shown in their
[internal](analysis/common_c++/README.md#compile) and
[external](external/analysis/common_c++/README.md#compile) guides.
`internal/` preserves relative symlinks to the historical `study/`, `config/`,
`analysis/` and validation paths; keep those links when copying the checkout.

## Technical references

- [Source activities and v4 provenance](docs/STUDY_SOURCES.md)
- [Code guide](docs/CODE_GUIDE.md) and [directory/compatibility review](docs/INTERNAL_EXTERNAL_REVIEW.md)
- [Internal output](docs/OUTPUT.md), [analysis](docs/ANALYSIS.md), [validation](docs/TWO_STAGE_VALIDATION.md)
- [External physics](external/docs/PHYSICS.md), [output](external/docs/OUTPUT.md), [validation](external/docs/VALIDATION.md)
- [Known environment/geometry limits](docs/KNOWN_ISSUES.md), [development checks](internal/docs/DEVELOPMENT.md), [license/history](legacy/README.md)

Software completeness does not establish a physically validated background
prediction. Internal decay and external neutron transport require their own
qualification on the production environment.
