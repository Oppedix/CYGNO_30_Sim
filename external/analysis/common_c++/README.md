# Native ROOT external analysis

Build and run from the common repository root, with ROOT/HS3 available:

```bash
c++ -O3 -std=c++17 -ffp-contract=off external/analysis/common_c++/AnalyzeExternal.cpp \
  $(root-config --cflags --libs) -lRooFitHS3 -lRooFitJSONInterface -o /path/to/AnalyzeExternal
/path/to/AnalyzeExternal /path/to/completed-external-campaign /path/to/NEW-analysis
```

ROOT 6.40 installations supplying JSON through HS3 omit `-lRooFitJSONInterface`.
The source follows the repository's existing ROOT JSON/typed-leaf idiom. No
extra JSON package, Python, Geant4 or detector build is needed. Do not enable
fast-math; the order of volume-to-keV summation matters.

Input is a completed, unpacked external campaign in compact or both mode.
The compact stream supplies one all-particle Group per track. The loop sums
deposited energies per **primary EventNumber**, counts positive-energy events
in each channel and scales by the saved flux/surface convention and actual
GeneratedPrimaries. It does not import internal activities or component masses.

Output includes ROOT spectra, PNG/PDF, per-bin MC counts and annual rates/variance,
unbinned positive and (10,400] keV counters and a provenance summary. Underflow
and overflow are explicit; spectra have 1000 1-keV bins in [0,1000).
See [full semantics](../../docs/OUTPUT.md), [source assumptions](../../docs/PHYSICS.md)
and [cluster examples](../../docs/WORKFLOW.md).

The fast native loop checks relevant metadata, accounting, event/group/volume
ordering, gas IDs and finite payloads. It trusts the completed campaign for
large-file SHA256 and unused track relationships. Run
`external/analysis/analyze.py` for that full audit and for raw/compact parity
in both mode. C++ and Python comparisons run in `tests/test_external.py` when
ROOT is installed.
