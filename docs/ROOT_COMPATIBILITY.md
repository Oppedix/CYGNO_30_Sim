# C++ analysis ROOT compatibility, 2026-10-31

ROOT **6.30.02 (CNAF baseline)** and **6.40.x** remain supported. This record
concerns analysis only: detector geometry, transport/physics, activities,
normalization, selections and existing campaign products are unchanged.

## Fixes and audit

`AnalyzeCompactCampaign.cpp` used `JSONNode::is_null()`, which does not exist
in ROOT 6.30.02. The current C14 check requires `has_child("stop_before")`
and checks `writeJSON()` output for the exact JSON literal `null`. It reuses
the analyzer's existing JSON serialization helper, with no extra dependency
or version-specific validation bypass. Empty maps/arrays, strings (including
`"null"`), booleans, numbers and missing keys fail. Rn222 must still specify
Z=82, A=210, name=Pb210. Both source-matrix snapshots must still agree.
See ROOT's [6.30 JSONNode API](https://root.cern.ch/doc/v630/classRooFit_1_1Detail_1_1JSONNode.html).

The audit covered the production internal/external analyzers, the four active
`analysis/reference_cpp` programs and `PlotSpectrum.C`, their shared headers,
ROOT calls, JSON reading, typed leaves, histograms, trees and linkage. The
quarantined `legacy/analysis/05a2b92` snapshots contain no analogous new JSON
API calls and remain archival; they are not production build targets.

Actual 6.30.02 execution exposed another compatibility difference: reference
plotters' native `TH1D::Fill` assigns some floating-point bin boundaries
differently from 6.40 and canonical Python. Shared `UniformBinning.hh` now
keeps the existing canonical uniform-edge definition in all three normalized
plotters and the per-volume macro. Normal native fills are retained where
the bin agrees. Otherwise the correct bin is filled while retaining the
original energy moments, entry count and unit-weight errors. This preserves
the current 6.40 results and makes older ROOT use the same analysis definition.
The internal analyzer already indexes these bins explicitly; external uses
its own unchanged 1-keV primary-event definition.

## Actual environments and checks

| Environment | Compiler/standard from ROOT | Actual compilation and execution |
|---|---|---|
| Official `rootproject/root:6.30.02-ubuntu22.04`, Linux amd64 under Docker on Apple Silicon | GCC 11.4, C++17 | Internal, external, four reference programs and compiled `PlotSpectrum.C` pass |
| Local ROOT 6.40.04, macOS arm64 | Apple Clang 21, C++20 | Same seven programs pass |

The full offline suite passed in both environments: **81 tests, 73 passed,
8 skipped** (optional constructed-geometry, transport and prebuilt-reference
checks). The new reference compatibility test independently compiled/executed
the reference programs in both environments; the final entry-count assertions
also passed in a separate focused rerun. The Linux full suite ran from a source
snapshot without Git metadata, exercising the supported archived-source
provenance path; the image has no Git. No optional Geant4 checks were enabled.

The unmodified internal source was compiled against real 6.30.02 first and
reproduced the reported missing-`is_null` error. The reference regression also
failed on its unmodified 6.30.02 binning before the fix. These are actual ROOT
builds and executable tests, not API stubs or header-only compatibility claims.
The 6.40 internal run also compares saved historical histograms/trees and
pixel-identical historical PNG exports against the pre-fix production binary.
The existing CMake reference targets were additionally built successfully on
6.40.04, using a fresh build directory and the real generated identity header.

Direct cross-version comparison of retained 11x7 material/gas campaign outputs
found **124/140 TH1D histograms** with exactly equal bin contents and variances,
**22 numerical/categorical TTree fields** exactly equal (input paths differ by
environment), and byte-identical `cutflow.md` files in both scenarios. Input
snapshots and normalization scenarios are preserved; ROOT-version provenance
correctly records the runtime used.

Coverage:

- Complete synthetic v4 material-only (23/23) and gas-enabled (25/25) campaigns,
  both legacy and 11x7 layouts, exact C14/Rn222 scales and activities, all four
  selections, cutflows, per-source/category/total spectra and variances,
  PNG/PDF products, matching scenario and verbatim provenance. Valid inputs
  remain byte-for-byte unchanged; malformed gas endpoints fail before output.
- Reference grouping and all three normalized plotters, material/gas categories,
  kg versus piece scaling, every 900/1200-bin edge and both adjacent floats,
  flow bins, entries, Poisson variances and original energy moments against
  Python; the compiled per-volume macro is exercised too.
- External gamma and neutron configurations, current v4 compact/both storage,
  historical models/layouts, recoil retention, primary-event spectra and
  annual scaling against Python, figures and mixed-identity rejection.

These campaign inputs are labelled **synthetic software tests**, not new
transport or a background-rate prediction. The saved real local gas/no-gas
campaigns remain `preflight_failed` (0/25 and 0/23), due to the existing
Geant4 PART122 problem. No real completed gas transport is claimed or gate
bypassed; see [gas transport evidence](GAS_VALIDATION.md).

The actual CNAF host was not accessed. The exact requested ROOT 6.30.02 was
tested in its official Linux image. In the 6.40 series, only **6.40.04** was
available/tested; other patch releases and future ROOT Detail API changes
must be checked in their own environment. Figures can differ between ROOT
versions/platforms in fonts or rendering; numerical definitions are shared.
ROOT-derived histogram summary metadata, especially density histograms'
effective `fEntries` after `ResetStats()`, can differ between these versions.
Use the explicit count/rate/variance trees and cutflow for scientific counts,
as already defined by the analyzer; those and the saved bin arrays match.

## Reproduce on each ROOT installation

Activate that installation's runtime and compiler, then install
`study/requirements-analysis.txt` in its Python environment. ROOT is required
for these executable checks; without `root-config` the integration classes
explicitly skip and do **not** establish compatibility. Geant4/PyROOT are
unnecessary for the three focused suites:

```bash
cd "$CYGNO_SRC"
root-config --version
root-config --cflags
python -m unittest discover -s tests -p test_topology.py -v
python -m unittest discover -s tests -p test_external.py -v
python -m unittest discover -s tests -p test_root_compatibility.py -v
# Broader offline workflows, notebooks, archives and scientific contracts:
python -m unittest discover -s tests -v
```

`test_root_compatibility.py` generates a clearly synthetic `BuildInfo.hh` in
a temporary directory using the checkout's actual geometry hashes, then
compiles all reference programs. Production reference builds still use
the real CMake-generated header and existing `CYGNO_BUILD_ANALYSIS=ON` targets.
No simulation or campaign data is used as writable test output.

For standalone production binaries, use the existing
[internal](../analysis/common_c++/README.md#compile) and
[external](../external/analysis/common_c++/README.md#compile) commands.
ROOT 6.30.02 requires both `-lRooFitHS3 -lRooFitJSONInterface`; this 6.40.04
installation needs only `-lRooFitHS3`. Keep `-ffp-contract=off`, avoid fast math,
and let `root-config --cflags` supply the installation's C++ standard (after
the source's minimum `-std=c++17`). Rebuild binaries when changing ROOT;
do not run binaries linked against another ROOT installation.
