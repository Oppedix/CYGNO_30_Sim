# v4 implementation and validation — 2026-10-29

Current detector: `cygno-copper-cathode-v4` in both modes.
Current internal matrix: `cygno-radioassay-v4`, **23 contributions**.

## Implemented contract

- One solid `Cathode`, 500 × 800 × 0.060 mm, at the retained position;
  copper density 8.96 g/cm³, 0.21504 kg/module, 16.55808 kg for 77 modules.
  Its whole mass uses EFCu U/Th. No cathode core/skin volume or source job exists.
- Only GEMs retain the 50 µm PMMA core and two 5 µm Cu skins.
- Lens geometry, material, density, placements and sampling are unchanged.
  `CYGNO_radioactivity_excel_suprasil` assigns 3.843 kg to ONE physical lens.
  Exact U/Th/K activities are 4.72689e-4 / 1.564101e-4 / 1.19133e-3 Bq/piece.
  Python, standalone ROOT and optional reference ROOT use actual lens placement
  counts (308 for 11×7), without another reference-mass or surrogate-mass factor.
- Configs, CLI/export defaults, preflight and cluster wrapper select v4.
  Old-model resume fails before probes or transport. Historical model/matrix
  support is explicit and documented separately. Existing campaigns are untouched.

## Executed checks

Fresh out-of-source build: `build/cygno-copper-cathode-v4` in the shared workspace,
macOS/arm64, Apple Clang 21, Geant4 11.4.2 (single worker on MT build),
matching datasets including G4NDL, ROOT 6.40.04, Python 3.14.7.
CMake enabled reference analysis, Python analysis tests and compact transport.

- Application, geometry exporter and all reference ROOT programs compile.
- **26 CTest checks pass**, including the 73-test Python suite with optional
  constructed-geometry, C++/ROOT reference, notebook and transport checks enabled.
  No optional Python integration was skipped in this verification.
- The complete suite and repeat of the source-snapshot-sensitive legacy runner
  cover final verification. Its first attempt during live editing correctly
  rejected a changed checkout fingerprint; repeating on the frozen tree passes.
- All three layouts: actual source material/mass/volume/count exports, complete
  internal/external detector placement equality (external World is enlarged for
  the GPS sphere), unchanged non-cathode construction against archived v3,
  cathode/GEM/gas disjointness and layout/source/RNG checks.
- V4 source schema and exact Decimal lens conversion; mutated units, specific
  activities, double reference mass and provenance are rejected. Old matrix/model
  pairs cannot become v4. Internal and external cross-model resume leaves the
  old directory byte-for-byte unchanged and launches no process.
- Native ROOT/Python synthetic v4 parity exercises all 23 source scales,
  windows, bins, flows, variances and category sums, with 308 lens pieces and a
  different lens mass. All three optional reference plotters also agree with
  Python's v4 lens scales and reject bad units/double reference mass before
  overwriting output.
- Both v4 and archived-v3 Stage A orchestration select the correct matrix,
  exporter/probe/transport model and manifest identity. Historical tests retain
  explicit original configs, rather than depending on current defaults.
- Separate actual external **gamma 2/2 and neutron 2/2** primary Cu20 smoke runs
  completed, no aborted events/PART122, correct external and v4 ROOT metadata.
  These tiny samples establish software operation, not useful physical rates.
- Three saved walkthrough notebooks re-executed with current implementation
  hashes. Shell-wrapper syntax, canonical matrix validation and final diff
  whitespace/identifier/default/documentation checks pass.

## Production gate and scientific assumptions

The full v4 four-case decay preflight is **2/4**, exit 2:

| Case | Result |
|---|---|
| U238 default threshold | passed |
| U238 enabled long-lived threshold | passed |
| Th232 full chain | failed, Geant4 PART122 |
| Bi212 full chain | failed, Geant4 PART122 |

This installation cannot qualify complete internal production. The gate remains
mandatory; no complete 23-job physical smoke/production campaign was launched.
A compatible target environment must pass 4/4 and a fresh 23-job smoke before
production. Other Geant4 versions and cluster installations were not qualified
by this change. Earlier documented environment failures are not waived.

Remaining assumptions: retained 60 µm cathode envelope; EFCu assay applied to
bulk transport copper; U/Th secular equilibrium; historical Acrylic GEM limits
adopted as values; absent Cu K omitted; support K proxy; nominal per-piece
resistor model; compact lens transport and supplied physical-lens reference
activity; retained cage transverse intersections, closed vessel/optics and
sensor dimensions. No detector-response or absolute-rate validation is claimed.
See [geometry](SINGLE_MODULE_GEOMETRY.md), [source provenance](STUDY_SOURCES.md)
and [known issues](KNOWN_ISSUES.md).

Existing campaign output directories and historical versioned matrices/configs
were not modified. The pre-existing README GUI-guide addition and unrelated
untracked GUI guide/text clipping remain outside the v4 commit.

## Changed files (85)

- `README.md`
- `analysis/README.md`
- `analysis/common/CYGNO30_background_analysis_walkthrough.ipynb`
- `analysis/common/examples.py`
- `analysis/common_c++/AnalyzeCompactCampaign.cpp`
- `analysis/common_c++/README.md`
- `analysis/compact/CYGNO30_compact_preprocessing_walkthrough.ipynb`
- `analysis/raw/CYGNO30_raw_preprocessing_walkthrough.ipynb`
- `analysis/reference_cpp/FileIdentity.hh`
- `analysis/reference_cpp/Normalization.hh`
- `analysis/reference_cpp/SimpleProcessEvents.cpp`
- `app/geometry_quantities.cc`
- `app/rdecay01.cc`
- `common/DetectorGeometry.hh`
- `common/SimulationMode.hh`
- `config/cygno/po212-smoke.mac`
- `config/study/cygno-11x7-v4.json`
- `config/study/cygno-radioassay-v4.json`
- `config/study/historical/smoke-A-v2.json`
- `config/study/historical/smoke-B-v2.json`
- `config/study/samuele.json`
- `config/study/smoke-A.json`
- `config/study/smoke-B.json`
- `docs/ANALYSIS.md`
- `docs/BACKGROUND_STUDY.md`
- `docs/CODE_GUIDE.md`
- `docs/KNOWN_ISSUES.md`
- `docs/LAYOUT.md`
- `docs/SETUP.md`
- `docs/SINGLE_MODULE_GEOMETRY.md`
- `docs/SOURCES.md`
- `docs/STUDY_SOURCES.md`
- `docs/TWO_STAGE_VALIDATION.md`
- `docs/V4_VALIDATION.md`
- `docs/history/ANALYSIS-pre-v4.md`
- `docs/history/DETECTOR_MODELS.md`
- `docs/history/EXTERNAL_VALIDATION-pre-v4.md`
- `docs/history/ROOT_EQUIVALENCE-pre-v4.md`
- `docs/history/SINGLE_MODULE_GEOMETRY-pre-v4.md`
- `docs/history/STUDY_SOURCES-pre-v4.md`
- `docs/history/TWO_STAGE_VALIDATION-pre-v4.md`
- `docs/history/VALIDATION-pre-v4.md`
- `external/README.md`
- `external/analysis/common_c++/AnalyzeExternal.cpp`
- `external/config/hall-c-gamma-2026-proxy.json`
- `external/config/hall-c-neutron-wulandari-proxy.json`
- `external/docs/VALIDATION.md`
- `external/study/config.py`
- `external/study/simulate.py`
- `include/cygno/geometry/DetectorConstruction.hh`
- `internal/README.md`
- `internal/cluster/run.sh`
- `internal/docs/DEVELOPMENT.md`
- `internal/docs/WORKFLOW.md`
- `src/geometry/DetectorConstruction.cc`
- `src/source/PrimaryGeneratorAction.cc`
- `src/source/RadioactiveSourceSampler.cc`
- `study/campaign.py`
- `study/preflight.py`
- `study/runtime.py`
- `study/simulate.py`
- `study/source_matrix.py`
- `tests/fixtures.py`
- `tests/test_acrylic.py`
- `tests/test_external.py`
- `tests/test_simulation.py`
- `tests/test_topology.py`
- `tests/test_v4.py`
- `tests/test_workflow.py`
- `validation/CMakeLists.txt`
- `validation/README.md`
- `validation/check_geometry.py`
- `validation/external_checks.cc`
- `validation/geometry_audit.cc`
- `validation/geometry_snapshot.cc`
- `validation/macros/chain.mac`
- `validation/macros/known_bi212_failure.mac`
- `validation/macros/partial_chain.mac`
- `validation/macros/smoke.mac`
- `validation/macros/stop_chain.mac`
- `validation/run_checks.py`
- `validation/source_checks.cc`
- `validation/test_source_matrix.py`
- `validation/test_study_runner.py`
- `validation/uniform_volume.cc`
