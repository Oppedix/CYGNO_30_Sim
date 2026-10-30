# Gas-background validation, 2026-10-30

Scope: current v4 internal gas extension. [Scientific assumptions](GAS_BACKGROUNDS.md)
and the unchanged [production gates](TWO_STAGE_VALIDATION.md) remain authoritative.
Passing synthetic analysis tests does not qualify decay transport or predict rates.

## Executable checks

The added `tests/test_gas.py` checks the isotope-ratio calculation independently,
canonical matrix/provenance, C14 and Rn chain controls, unchanged default/no
macros, both directions of resume rejection before writes, complete 25-source
raw/compact/both offline analysis, archive validation, individual gas categories,
total sums, Table 7.3 gas rows and final PNG/PDF generation. The common notebook
is also executed against a complete synthetic gas campaign.

`tests/test_workflow.py` exercises the Stage A CLI gas flag with synthetic
transport and the actual campaign orchestration. `tests/test_topology.py`
compiles and runs the standalone ROOT analyzer on the 25-source fixture and
compares all four selections, contribution counters/rates/variances, category
histograms, stacked totals and cutflow tables against the Python oracle. It
rejects a gas flag/matrix mismatch. Existing 23-source and historical-model
checks remain enabled. `tests/test_parity.py` also exercises all three older
ROOT reference plotters with the gas-enabled v4 matrix, verifying both gas
categories after independent normalization.

Constructed gas mass/material/count checks cover all three layouts; default
quantity exports and explicit `--gas-bkg no` are byte-identical for the same
build. Existing material rows are unchanged with gas enabled. The sampler
checks all gas placements, same-event source generation and containment;
analytic uniform-volume moments include gas. Tracking boundary tests include
ground-state Pb210 stopping, excited-state de-excitation and reset behavior.
Shared detector geometry and external source code have not been changed.

Reproduce with a matching Geant4 environment and the analysis dependencies:

```bash
cd "$CYGNO_SRC"
export CYGNO_ACRYLIC_BUILD="$CYGNO_BUILD"
export CYGNO_REFERENCE_BUILD="$CYGNO_BUILD"
python -m unittest discover -s tests -v
ctest --test-dir "$CYGNO_BUILD" --output-on-failure

# Explicit real gas transport diagnostic; leaves evidence under the build.
CYGNO_GAS_TRANSPORT_BUILD="$CYGNO_BUILD" \
  python -m unittest discover -s tests -p test_gas.py -k GasTransportTests -v
```

ROOT reference comparisons need `CYGNO_BUILD_ANALYSIS=ON`, ROOT and PyROOT.
The standard-library-only production simulation build still needs neither
ROOT nor Python analysis packages. On this machine, PyROOT is supplied by
`PYTHONPATH=/opt/homebrew/lib/root`; this is a local installation detail, not a
portable activation recipe. Saved notebook outputs are refreshed with
`python validation/execute_notebooks.py --output analysis`.

## Real transport and limitations

Local build: Apple Silicon/macOS, Apple Clang 21, **serial Geant4 11.3.1**, its
matching installed datasets, ROOT 6.40.04 and Python 3.14.7. A fresh out-of-tree
build compiled the common application, quantities exporter, geometry/source
validators and ROOT reference programs. The native compact analyzer is compiled
separately by the integration tests.

Final executed regression results:

| Run | Result |
|---|---|
| CTest, analysis targets enabled, matching PyROOT environment | **24/24 passed** |
| Full Python suite with constructed geometry, ROOT reference and compact transport options enabled | **79 tests: 78 passed, 1 skipped** |
| Separately enabled real gas diagnostic | C14 passes all three storage modes; Rn222 fails with PART122, as detailed below |
| Real Stage A CLI, `--gas-bkg no` | Existing Th232/Bi212 PART122 preflight failure; retained `preflight_failed`, 0/23 |
| Real Stage A CLI, `--gas-bkg yes` | Same preflight failure; retained `preflight_failed`, 0/25, correct gas matrix and 47.04352576 kg export |

The one skipped Python test is the opt-in real gas diagnostic, which was run
separately and **did not pass for radon**. The 24 passing CTest checks do not
include the full four-case production preflight. Both failed real campaigns
are rejected by portable campaign validation; neither can produce an accepted
complete analysis. Their local directories are
`build/cygno-gas-v4/validation-results/REAL-internal-gas-no` and
`REAL-internal-gas-yes` under the same parent.

Complete synthetic gas reports were generated and visually inspected in
`build/cygno-gas-v4/validation-results/SYNTHETIC-gas-python` and
`SYNTHETIC-gas-native`. Both show separate gas legend entries; automated checks
verify the numerical stacks and totals. These reports use artificial events,
not a simulated background prediction. Three saved tutorial notebooks were
re-executed and their implementation fingerprints refreshed.

The real gas diagnostic used **100 primaries per isotope per storage mode**
on the 77-module layout. C14 completed in raw, compact and both, produced N14
and electron deposits below the beta endpoint, and gave identical canonical
counts and spectra across all three storage modes. This is a software/transport
smoke, not a precision validation of the beta spectral shape.

Rn222 failed in the first raw-mode event with fatal **PART122** in
`G4ParticleTable::Insert()`: duplicate registration of Po214 while transporting
`Po214[1847.446]`. No radon raw/compact parity or complete real gas campaign is
claimed. The failure was retained at
`build/cygno-gas-v4/validation-results/gas-transport-m0dn16je/Gas_Rn222-raw/`
relative to the local parent `hep/` workspace; these large outputs are not
versioned. C14 evidence is in the same diagnostic directory.

This is consistent with the existing [macOS PART122 limitation](KNOWN_ISSUES.md),
not a reason to remove daughter states, patch nuclear data, suppress fatal
exceptions, change decay physics or bypass campaign gates. Full U/Th preflight
and complete Rn222 transport must pass on the production environment before a
gas-enabled result can be accepted. Bulk uniform daughters and the optimistic
contamination inputs remain separate scientific limitations even there.
