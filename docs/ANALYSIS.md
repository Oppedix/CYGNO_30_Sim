# Internal v4 analysis and normalization

The current model/matrix pair is `cygno-copper-cathode-v4` /
`cygno-radioassay-v4` (23 contributions). Analyze newly transported v4 campaigns
in new output directories. Existing v3 transport cannot be relabeled or
reweighted into v4. Model, matrix, geometry hashes, receipts, metadata and
campaign fingerprints must agree.

Python: `study/analyze.py`, using uproot/numpy/matplotlib. Native ROOT:
[`AnalyzeCompactCampaign`](../analysis/common_c++/README.md), consuming a completed,
unpacked compact campaign. Both preserve the source matrix and write
`normalization-scenario.json` with the matching model/matrix identity.

Both use the same operation order:
`activity * quantity * 60 * 60 * 24 * 365 / actual_generated_primaries`.
Bq/kg uses constructed component kg; **Bq/piece uses actual placement count**.
Lens and Resistors are per piece. Lens U/Th/K activities are exactly
4.72689e-4 / 1.564101e-4 / 1.19133e-3 Bq/piece, from
**`CYGNO_radioactivity_excel_suprasil`**. The spreadsheet's 3.843 kg is ONE
physical lens, already included in those values. Never multiply by it again or
use the Geant4 lens mass. Lens transport geometry remains unchanged.
For planar 11×7, 308 actual lens placements enter normalization.

The entire solid `Cathode` mass uses EFCu U/Th. There are no cathode-core or
copper-skin source contributions. Scale each source before combining the seven
categories. `Cathodes = Cathode`, `GEMs = GEMsPolyimide + GEMsCopper`,
`Field Cage = RingSupports + RingStrips`.

Existing grouping, event/EOF boundaries, first-position fiducialization, exact
energy windows, 365-day year, flow bins, topology cuts and group-Poisson errors
are retained. Systematic assay/geometry uncertainties are not propagated.
The provenance source matrix is copied into Python reports/manifests and
embedded verbatim in native ROOT output, including physical-lens metadata.

[Workflow commands](../internal/README.md), [source specification](STUDY_SOURCES.md),
[Python analysis architecture](../analysis/README.md), and
[validation](TWO_STAGE_VALIDATION.md) give operating details. Optional historical
ROOT reference programs still accept explicit unit-paired normalization files;
that interface and historical unversioned-input rules are archived in
[the pre-v4 reference](history/ANALYSIS-pre-v4.md).
External uses [its own environmental normalization](../external/docs/OUTPUT.md),
never internal activity weights.
