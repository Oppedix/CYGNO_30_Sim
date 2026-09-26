# Standalone compact-campaign ROOT analysis

`AnalyzeCompactCampaign.cpp` reproduces the current Samuele electron-recoil
analysis in `analysis/common/` using a native, streaming ROOT loop. It is a
separate implementation; the canonical Python packages and historical
`analysis/reference_cpp/` are unchanged.

Input is a **completed, unpacked, 26-contribution campaign** produced by
`study/simulate.py` with `output_mode=compact`, campaign schema 3, output schema 1.
The same executable handles `legacy-25x3` and `cygno-11x7-v1` using their saved
geometry and constructed quantities. No detector coordinates, assay activities,
component masses, resistor counts, primary counts, or contribution list are
compiled into the program.

## Compile

From the repository root:

```bash
g++ -O3 -std=c++17 -ffp-contract=off \
    analysis/common_c++/AnalyzeCompactCampaign.cpp \
    -I. \
    $(root-config --cflags --libs) \
    -lRooFitHS3 \
    -lRooFitJSONInterface \
    -o analysis/common_c++/AnalyzeCompactCampaign
```

This command has been verified with ROOT **6.30.02 on CNAF**. Requirements are a
C++17-capable compiler and ROOT with its RooFit/HS3 JSON support. The program has
also been tested with ROOT **6.40.04** and Apple Clang. `root-config` must be on
`PATH`, with ROOT's normal runtime library environment available. Use the
compiler/standard compatible with your ROOT installation; `root-config --cflags`
supplies that installation's flags.

`-lRooFitJSONInterface` is required on ROOT 6.30.02 because the program uses
ROOT's RooFit JSON support (`RooFit::Detail::JSONTree`) to read campaign JSON
metadata. Link it alongside `-lRooFitHS3` as shown above. This avoids vendoring
a JSON library or writing a custom parser. The source requires
`RooFit/Detail/JSONInterface.h` and the matching RooFit JSON libraries from that
ROOT installation; a minimal ROOT build without HS3 is insufficient. This is a ROOT
**Detail** interface, so a future ROOT API change may require a small adjustment
to the metadata reader. No RooFit modeling or fitting is performed.

**Keep `-ffp-contract=off` and do not enable `-ffast-math`/`-Ofast`.** Separate
multiplication and addition, and their order, must match the canonical Python
floating-point operations. Fast-math builds are explicitly rejected.

There is no Geant4, Python, Jupyter, CMake, or extra JSON-package requirement for
compiling or running this analysis. The include path is the repository root;
no generated geometry header is needed.

## Run

The interface takes exactly two arguments:

```bash
analysis/common_c++/AnalyzeCompactCampaign CAMPAIGN_DIR NEW_OUTPUT_DIR
```

For the 25×3 campaign:

```bash
analysis/common_c++/AnalyzeCompactCampaign \
    /cnaf/cygno-sim/Users/goppedis/SolarNu/25x3Samuele-1M \
    ./analysis-25x3
```

For the 11×7 campaign, with the **same executable**:

```bash
analysis/common_c++/AnalyzeCompactCampaign \
    /cnaf/cygno-sim/Users/goppedis/SolarNu/11x7Samuele-1M \
    ./analysis-11x7
```

The output directory must not exist and must be outside the input campaign.
The program reads the campaign without modifying it. It does not accept an
individual ROOT file, an archive, partial campaigns, raw mode, or both mode.
It exits with status 0 after success and 1 on error, identifying the current
contribution in its progress output.

Input files are all processed before output creation. Output is written into
`NEW_OUTPUT_DIR.partial` and renamed to the requested directory only after the
ROOT file, figures, and summary have been written successfully. If an output
operation fails, that clearly labeled staging directory can remain; inspect or
remove it before retrying. Existing output/staging directories are never reused.

## How inputs are discovered

The program reads:

```text
CAMPAIGN_DIR/
├── campaign.json
├── config.json
├── matrix.json
├── quantities.tsv
├── geometry.json
└── jobs/<contribution-id>/
    ├── manifest.json
    └── <manifest.attempt>/
        ├── manifest.json
        └── <manifest.data_path>
```

1. The ordered `matrix.json.contributions` array supplies all 26 physical rows,
   each row's activity, activity unit, component, and reporting category.
2. `jobs/<id>/manifest.json` supplies the completed job's **`attempt`** and
   **`data_path`**. The program checks agreement with `campaign.json.job_records`
   and the selected attempt's manifest.
3. The input file is `jobs/<id>/<attempt>/<data_path>`. Thus `attempt-0002`,
   `attempt-0007`, or any other recorded attempt works. So do the runner's
   `outfiles_V2/compact.root` and `outfiles_V2/compact_t0.root` names. Files are
   never selected by glob order or by guessing the newest attempt.
4. `RunMetadata` must match the campaign layout, geometry identity, detector
   model, and source policy. `OutputMetadata` must identify the supported compact
   representation and historical processing convention.
5. `RunAccounting` supplies the actual generated primaries. All five fields are
   compared with the manifest. Completed jobs require run 0, positive
   requested=generated=processed counts, and zero aborted events; recorded
   requested/generated values must also agree. The denominator is read from
   **`GeneratedPrimaries`**, even though valid completed jobs also match requests.

The small metadata copies are compared directly. No large ROOT artifact hashes
are computed, no simulation logs are rescanned, and no preflight is rerun.
This is the fast analysis of an already trusted, completed campaign, not a
replacement for `study/campaign.py`'s full integrity audit.

## Scientific rules preserved

The source follows the seven numbered analysis sections from reading a campaign
to rendering the figures. These are the contracts established by inspecting
`analysis/common/`, `analysis/compact/`, `analysis/reference_cpp/`,
`study/analyze.py`, `study/campaign.py`, `study/source_matrix.py`,
`study/simulate.py`, `docs/OUTPUT.md`, `docs/ANALYSIS.md`,
`common/DetectorGeometry.hh`, and `src/output/CompactOutput.cc`.

### Historical groups and streaming

A compact `Group` is the stored result of the existing historical grouping
heuristic, **not a track or an ancestry-defined physical event**. Only e−, e+,
and alpha steps were admitted by the producer. Creator-process/nucleus changes
and the inherited ionization-continuation rule determine group boundaries;
groups never cross events. The final admitted particle label determines the ER
selection. `GroupIndex` starts at zero for each event.

The producer writes a group's gas volumes consecutively in zero-based
`VolumeOrder`. Each gas copy appears once, in first-encounter order. Its energy
is the producer's ordered sum of admitted step deposits in MeV. Its first
position is from the first admitted step in that volume, including a zero-energy
step. Time and track provenance do not affect this analysis.

The C++ loop reads these stored groups directly, without regrouping:

- Count every historical group in `ProcessedGroups`.
- Admit only final `ParticleName == "e-"` or `"e+"` to the ER spectra.
- For an admitted group, start at zero and add **each volume's
  `EnergyDeposit * 1000`**, in stored order, obtaining keV. Summing in MeV first
  would be a different floating-point computation.
- Advance the volume cursor over non-ER groups without reading their volume
  payload. Check total cursor consumption against the volume-tree entry count.

Only `Groups` and `GroupVolumes`, plus the small metadata/accounting trees, are
read. `Tracks`, `TrackGroups`, `FirstHitTime_ns`, and unused labels/counts are not
read. Unused branches are disabled; each main tree has a 16 MiB read-ahead cache.
The program keeps fixed-size spectra and counters, not whole event trees or
millions of reconstructed objects.

Cheap checks cover typed required branches, group identities/order, positive
volume counts, cursor bounds, and, for ER groups, matching volume identities and
order, unique/valid gas IDs, and finite energies/positions. Non-ER payload and
track relationship validation are intentionally left to the trusted producer
and canonical validator.

### First-position 20 mm cut

`geometry.json` is the campaign's export of the shared detector geometry. Its
`gas_centers_mm` and `gas_size_mm` directly supply the cut. No second layout map
is maintained by this program.

Only the **first stored gas volume** is used. For its stored first position,
all three coordinates must satisfy:

```text
abs(position - gas_center) <= gas_size / 2 - 20 mm
```

Equality passes. Other positions/volumes in the group do not change the decision.
The no-cut histogram contains every accepted ER group; the fiducial histogram
contains the subset passing this predicate.

### Bins and exact windows

Both selections use **900 uniform bins, 0–2000 keV**. An explicit, short bin
calculation reproduces `analysis/common/spectra.py`, including ROOT 6.40's
rounding corrections at uniform bin edges, independently of the local ROOT
version's `TAxis::FindBin` implementation.

Exact integer counters are also accumulated before binning:

| Stored window | Definition |
|---|---|
| `all` | All finite accepted energies, including flows |
| `gt10` | E > 10 keV |
| `gt10_le400` | 10 < E ≤ 400 keV |
| `underflow` | E < 0 keV |
| `in_range` | 0 ≤ E < 2000 keV |
| `overflow` | E ≥ 2000 keV |

Thus 10 is excluded from both threshold windows, 400 is included in the finite
window, and 2000 is overflow. The summary's full-range rates are not estimated
from visible histogram integrals. Raw histogram entries count historical groups. ROOT energy moments are
reconstructed from bins; unbinned moments are not retained.

### Normalization and category sums

`quantities.tsv` supplies actual constructed `mass_kg` and `pieces`, checked
against the campaign's saved quantities and geometry/source identity. Selection
is determined by each matrix row's unit:

| Activity unit | Constructed quantity |
|---|---|
| `Bq/kg` | Component `mass_kg` |
| `Bq/piece` | Component `pieces` (including the resistor rows) |

For **each physical contribution**, with left-to-right multiplication:

```text
scale = activity * quantity * 60 * 60 * 24 * 365 / actual_generated_primaries
```

Raw bins/windows are multiplied by this scale **before** contributions are added,
in matrix order. Poisson group-count variance is `count * scale * scale`, with
the same operation order as the common implementation. No extra branching
weights or published-value rescaling are applied.

The reporting order is that of `analysis/common/reporting.py`. Current matrix
membership is shown for explanation only; the executable reads membership from
the campaign matrix:

| Reporting category | Physical components | Contributions |
|---|---|---:|
| Camera Lenses | Lens: U238, Th232, K40 | 3 |
| Vessel | Vessel: U238, Th232 | 2 |
| Camera Sensors | Sensors: U238, Th232, K40 | 3 |
| Cathodes | Cathodes: U238, Th232 | 2 |
| Resistors | Resistors: U238, Th232, K40, U235, Ra226, Th228 | 6 |
| GEMs | GEMsCore: U238, Th232, K40; GEMsOuter: U238, Th232 | 5 |
| Field Cage | RingSupports: U238, Th232, K40; RingStrips: U238, Th232 | 5 |

The resistor upper/lower chain segments remain distinct matrix contributions.
GEMs and Field Cage combine separately normalized component histograms. The
program does not implement or change decay-chain physics.

## Outputs

```text
NEW_OUTPUT_DIR/
├── analysis.root
├── figure7.5.png
├── figure7.5.pdf
├── figure7.6.png
├── figure7.6.pdf
└── summary.txt
```

- **figure7.5**: no fiducial cut; **figure7.6**: 20 mm fiducial cut.
- ROOT renders stacked category spectra in the canonical category/color order,
  with energy 0–2000 keV and **counts / keV / year**. The vertical axis is
  logarithmic when regular bins are nonzero; empty spectra use a linear axis.
- Figures identify the layout, campaign mode, complete coverage, and the
  existing physics-validation limitation. Small smoke samples are software
  checks, not statistically useful background-rate predictions.
- `summary.txt` records campaign/layout identity, each resolved input path,
  quantities, activities, generated primaries, scales, processed groups, all
  exact contribution windows and normalized total windows.

`analysis.root` contains:

```text
no_cut/
  categories/<category name>       TH1D, normalized density
  total                           TH1D, sum of the displayed categories
fiducial_20mm/
  categories/<category name>       TH1D, normalized density
  total                           TH1D, sum of the displayed categories
contributions/<contribution-id>/
  raw_no_cut                      TH1D, unweighted MC group counts
  raw_fiducial_20mm                TH1D, unweighted MC group counts
ExactEnergyWindows                TTree: 26 × 2 × 6 contribution windows
Normalization                     TTree: activity/unit, quantity, measured
                                        primaries, scale, processed groups, path
provenance/                       Campaign/layout/fingerprint/ROOT version,
                                  histogram-unit convention and input snapshots
```

Category histograms are **the same objects used to draw the figures**. Regular
bins are divided by the canonical uniform bin width `2000.0 / 900`, after
category sums, exactly as the common density calculation. **Underflow and
overflow bins stay counts/year**, matching common reporting; they are not
visible in the figures. Raw contribution histograms stay unweighted in all
bins. This intentionally differs from the historical C++ plotter's
counts/bin/year storage convention.

`ExactEnergyWindows` stores `Contribution`, `Category`, `Window`, `Fiducial`
(0 or 1), integer `Count`, `RatePerYear`, and `VariancePerYear2`. It can be summed
by category or across contributions; do not derive exact windows from bins.
The `Normalization` tree and raw contribution histograms also permit independent
reconstruction of each normalized contribution without rereading the campaign.

For example, in ROOT:

```cpp
TFile file("analysis-25x3/analysis.root");
file.Get<TH1D>("no_cut/total")->Draw("HIST");
file.Get<TTree>("ExactEnergyWindows")->Scan("Contribution:Window:Count:RatePerYear", "Fiducial==1");
```

## Equivalence checks

Validation uses the existing canonical `canonical_input`, `accumulate`,
`scale_for`, and `summarize` functions as the oracle, without changing them.
Python is used only for this development comparison, never by the new executable.

The already-generated `compact-refactor-k40-30` Geant4 sample has 30 generated
primaries, 11 stored groups, and 16 group-volume records. It produces 11 accepted
ER groups without a cut and 1 with the cut. Its exact windows are:

```text
                 all  gt10  gt10_le400  underflow  in_range  overflow
no_cut            11    11          10          0        11         0
fiducial_20mm      1     1           1          0         1         0
```

For campaign integration, this small real transport file was reused in a
**clearly labeled synthetic 26-job campaign fixture**, with actual exported
geometry/quantities and the saved matrix activities. This exercises differing
normalization scales and category sums; it is not a physically simulated
26-source campaign. Attempts alternate between `attempt-0002` and
`attempt-0007` to check manifest-based discovery.

Comparisons require exact equality for accepted/processed counts, all six
unbinned windows, every one of the 902 raw bins in both selections, scales,
annual window rates/variances, all category density bins and errors, and totals
summed in reporting order. Additional synthetic checks cover both supported
layouts, every internal histogram edge and adjacent floating-point values,
window endpoints/flows, inclusive fiducial faces and outside positions,
multiple-volume first-position decisions, conversion-before-summation, alpha
exclusion, and empty spectra. These fixtures and generated products are local
development artifacts, not new production dependencies or committed ROOT data.

Malformed-input checks also passed: zero volume counts, wrong volume order,
invalid gas IDs, nonfinite deposits, conflicting primary accounting/layout,
missing required branches, incomplete jobs, existing output directories, and
output inside the campaign are rejected. The worker filename
`compact_t0.root` was exercised successfully. The documented compile command
and PNG/PDF exports were also checked.
