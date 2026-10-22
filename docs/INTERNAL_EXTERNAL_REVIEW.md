# Repository review and scientific separation

Review performed before implementation on 2026-10-22, baseline commit `d612785`.
The pre-existing README insertion and untracked local GUI guide/text clipping
were retained; they are not part of this feature commit.

## Scope reviewed

| Area | Existing behavior and consequence for this change |
|---|---|
| CMake, app entry points, generated BuildInfo | One explicit Geant4 library; serial/single-worker runner; batch macro errors must propagate; preserve old CLI and source hash gates |
| `common/DetectorGeometry.hh`, full construction/materials, geometry exporter | Three layouts, analytical solids, one common 5 mm vessel, external optics, no active CAD importer; no new detector tree |
| Source sampler, gun/messengers, actions | Internal uniform material volume and isotope/full/split chains; RNG draw/order must remain unchanged; heavy ions are stopped in internal |
| Step extraction, sensitive detector, compact accumulator/writer, metadata | Raw admits all steps but compact groups only e-/e+/alpha; last-ion context is not ancestry; external needs explicit all-track semantics |
| `analysis/raw`, `compact`, `common`, notebooks | Schema/type, relational, grouping and parity checks; preserve internal normalization and report semantics; reuse transport-independent schemas/models/validators |
| `analysis/common_c++` | Preferred standalone native compact campaign analysis, four internal topology stages, HS3 metadata parsing; source-matrix-specific, not an external normalizer |
| `analysis/reference_cpp` and legacy ROOT macros | Internal historical processing/plot parity and separate layout/model guards; retain as internal references, do not adapt assays to environmental flux |
| `study` config/matrix/preflight/runtime/campaign/archive/analyze | Immutable identity and attempts, accounting, dataset hashes, source snapshots, archive integrity, concurrency/cancellation; reuse neutral process/provenance helpers |
| Tests and validation | Pure-C++ state-machine replay, synthetic ROOT, C++/Python parity, source/mass, actual geometry and decay smoke; extend rather than replace |
| Docs, history, reference matrices, legacy config/runners/scaffolding | Scientific caveats, cluster path conventions and environment-specific PART122; inactive physics is not the actual physics list |
| Collaboration repositories, spectra, CAD and primary literature | Four-layer construction pattern retained conceptually; WIP cave and CYGNO-04 dimensions not imported; flux definition and spectrum normalization made explicit |

The review distinguishes active code from archived/scaffolding/reference material.
Numerical source tables, all three layout providers, raw/compact lifecycles and
native ROOT campaign assumptions were inspected, as were local and cluster
execution recipes. Private reference PDFs were inventoried but not copied into
source or treated as new authoritative detector/CAD specifications.

## Structure and compatibility choice

```
CMakeLists.txt, app/, src/, include/, common/   one shared transport/geometry
 docs/LAYOUT.md, SINGLE_MODULE_GEOMETRY.md,
 docs/EXTERNAL_SHIELDING.md                    shared detector documentation
 internal/
   README.md, cluster/, docs/WORKFLOW.md       internal entry points/guides
   study -> ../study, config -> ../config
   macros -> ../config/cygno
   analysis -> ../analysis                    all established Python/C++/notebooks
   validation -> ../validation
   legacy -> ../legacy
 external/
   README.md, config/, macros/, study/        independent environmental sources/runner
   analysis/raw/, compact/, common_c++/       external scientific semantics
   cluster/, docs/                            external operations/physics/validation
```

The existing authoritative internal directories stay in place. Relative symlink
views make them accessible from a self-contained internal area while preserving
old CLI paths, Python imports, ROOT relative includes, notebook paths, archive
layouts and existing source-hash inventories. A wholesale move would change all
of those for no physical benefit. The two areas require their **common parent
checkout**; neither pretends to be a separately exportable Geant4 repository.

`analysis/common` remains the authoritative internal science plus low-level
format/model utilities used explicitly by external. `analysis/common_c++` remains
internal, not a misleading universal normalizer. External has its own native
ROOT executable and separate primary-event normalization. Generic schema and
relationship validation are reused with an explicit external argument whose
default remains internal. Internal readers reject external processing markers.
No existing scientific selection/assay algorithm is rewritten or copied.

## Reach and risks checked

Changes reach app option parsing, common World/shield construction, generator,
tracking policy, sensitive-detector accumulator selection, output identity,
external source configs/runner, both analysis languages, CMake validation,
cluster wrappers and docs. Internal source matrices, component masses, geometry
header, gun defaults, RNG draws, transport list, group rules and scales are
unchanged. A fixed-seed K40 before/after transport regression compares every raw,
compact and metadata branch. Standalone ROOT regressions cover internal reports.

There is no destructive migration or production data rewrite. New runners and
analysis write outside source and refuse identity changes/overwriting results.
Failure receipts and attempt data survive. Source/dataset snapshots stay within
campaign storage; copying a campaign includes the source checkout snapshot as in
the pre-existing workflow. Statistical smokes do not certify flux assumptions,
mechanical reality or detector response. See [external validation](../external/docs/VALIDATION.md).
