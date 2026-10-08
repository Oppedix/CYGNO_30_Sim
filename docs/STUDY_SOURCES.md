# Current radioactive-source matrix and normalization provenance

Canonical specification:
[`cygno-300elj-radioassay-v2.json`](../config/study/cygno-300elj-radioassay-v2.json),
validated by `study/source_matrix.py`. Detector `cygno-300elj-v2`, source policy
`uniform-volume-v1`; layout is independent. The original
[`thesis-table7.1.json`](../config/study/thesis-table7.1.json) is preserved as a
reference transcription, not rewritten or accepted for new production.

## Layer assays

GEM and cathode transport is Cu5/G4_KAPTON50/Cu5 µm. Separate-material assays
from [Arnquist et al., arXiv:1910.04317v1, Table 5](https://arxiv.org/abs/1910.04317v1)
apply independently to polyimide and each copper skin. Table 4 whole-laminate
values serve only as provenance/cross-check. The complete concentration table,
uncertainties, 26/74 paper consistency calculation, new 44.2092/55.7908 mass
fractions and nominal converted activities are in
[SINGLE_MODULE_GEOMETRY.md](SINGLE_MODULE_GEOMETRY.md#radioactive-sources-and-provenance).

Conversion uses the paper's section 2.2 convention: 12400 Bq/g U238,
4060 Bq/g Th232, 30.5 Bq/g natural K. Multiply pg/g by `1e-9` or ng/g by `1e-6`
then by specific activity to obtain Bq/kg. Natural K already includes K40
abundance. The paper's K convention differs by about 2% from 31.1 Bq/g; it is
explicitly versioned and tested. Nominal activities are PI U/Th/K =
`6.9192e-5 / 2.76892e-5 / 3.294e-3` Bq/kg and Cu =
`1.488e-4 / 4.872e-5 / 3.965e-3` Bq/kg. Concentrations are not rescaled by foil
thickness. Assay uncertainties stay in provenance; analysis still has only
statistical errors. No U235 assay is added to the laminate.

## Radiopure PMMA design material

Primary source: I.J. Arnquist et al., “Mass Spectrometric Assay of High Radiopurity
Solid Polymer Materials for Parts in Radiation and Rare Event Physics Detectors”,
NIM A 943 (2019) 162443, [DOI 10.1016/j.nima.2019.162443](https://doi.org/10.1016/j.nima.2019.162443).
Local accepted manuscript: section 2.1 p.3, cleaning/method sections 2.2–2.3
pp.4–5, PMMA section 3.2 pp.6–8, **Table 1 p.7, ninth data row: second Pre-
set, sample 3, 0.1527 g**.

UVT (ultraviolet-transmitting) acrylic from **Reynolds Polymer Technology, Inc.**
was obtained as a **solid 4×12×12-inch block**, cut into small cubes in a clean
machine shop, detergent/DI/6M-HNO3/DI cleaned, dry-ashed in ULB electroformed-Cu
boats with isotope-dilution tracers, then measured by ICP-MS. This is fabricated
solid stock, not raw resin/powder. It is the adopted radiopure PMMA design
material, without a claim of batch identity with Samuele's acrylic or constructed
support. Density and support geometry remain PMMA 1.190 g/cm³ and unchanged.

The selected same row reports **U238 0.730 pg/g = 9.05 µBq/kg** and
**Th232 1.23 pg/g = 5.05 µBq/kg**. Both are central measurements, not limits;
uncertainties are not provided for this row. These are the maxima of the 12
Cu-boat replicates, providing a conservative measured replicate envelope rather
than selecting an especially clean subsample. Other Table 1 rows include U
3.03–9.05 and Th 1.13–5.05 µBq/kg and several upper limits. The first Pre-2
row has U <3.57/Th <1.04, but is not selected as a lower model solely on that
replicate. Table 2 post-ashing quartz results agree; pre-ashing quartz results
are inflated by tracer loss (section 3.2 p.7), not an alternative material assay.
No raw precursor is selected. Published activity columns are used exactly,
without re-rounding concentration columns with the laminate conversion constants.

**No K assay is reported. K40 remains 71.2 µBq/kg**, the previous conservative
Table 7.1 acrylic proxy, explicitly `conservative-old-K-proxy`, never zero.
Historical acrylic U/Th limits are replaced; unchanged assumptions elsewhere are
not interpreted as newly measured quantities. If a selected row had upper limits,
the historical `upper-limit-used-as-value` convention would apply; it does not
apply to the chosen central U/Th measurements.

## Completed MBNL resistor assay

[A. Anker et al., arXiv:2601.05985v2](https://arxiv.org/abs/2601.05985v2),
“Novel High-Radiopurity Doped Amorphous Silicon Resistors for Low-Background
Detectors”, **section 6 pp.17–19, Table 9 p.19, “Prototype 2 MBNL - 2024,
Completed”** gives U238 4.30±0.20 and Th232 2.00±0.16 ppt.
[R. MacLellan et al., The nEXO Radioassay Program, arXiv:2604.15406v1](https://arxiv.org/abs/2604.15406v1),
**Table IV p.10, row 60**, identifies “MBNL Heraeus Suprasil 300, aSi CVD @
550 °C, Ti and Pd end metalized”, ICP-MS at PNNL, with the same early-chain
U/Th and **natural K 7.90±0.20 ppb**. No independent late-chain U value is given.
All nEXO uncertainties are 1σ (section VIII p.7); Anker describes full
dissolution and analytical precision from three ICP-MS acquisitions.

Anker reference 22 explicitly points to nEXO items 55–60. The matching U/Th
and finished-MBNL description establish a corresponding component technology
and assay record; neither publication supplies unique specimen/lot identifiers
that prove the same individual part or production batch. This is an explicit
**composite publication basis**, using all U/Th/K together from row 60 and Anker
for geometry/process context, not a claim that values from identified different
specimens were pooled. Control row 58 and unmetalized row 59 are not substituted
for the completed row.

Using existing `assay_activity()` conversions, nominal U/Th/K are
**53.32 / 8.12 / 240.95 µBq/kg**, respectively. The reference tube has
volume `π*(3²−2²)*17 = 267.035375555 mm³`, density 2.20 g/cm³ and nominal
mass **0.587477826221 g**. Thin aSi/metallization masses are neglected; their
contamination is retained in the measured completed-component assay.
Activities per reference piece are **0.0313243176941 / 0.004770319949 / 0.141552782228
µBq/piece** (U/Th/K), derived in `reference_resistor_mass_kg()` and
`resistor_activity()`, not rounded constants used in normalization.

Each compact 1.6×0.55×3.2-mm³ CYGNO fused-silica surrogate receives this activity
per piece. Its tiny transport mass does not rescale the assay. Source location
is effective, since processing/metallization dominates measured U/Th and the
assay cannot quantitatively partition it among silica/aSi/metals. No explicit
nanometre layers are constructed. U238 and Th232 each have one full-chain job;
secular equilibrium is an assumption for ICP-MS chain heads, not an assay result.
K40 is a single parent. Old resistor U235, Ra226, Th228 and split-chain assays
are absent from v2. GEM/cathode/gas/optics, decay physics, cuts, grouping and
normalization formulas are unchanged.

## Active assay membership

| Source family | U238 | Th232 | K40 | Unit/basis |
|---|---:|---:|---:|---|
| RingSupports | 9.05e-6 | 5.05e-6 | 71.2e-6 | Bq/kg; measured solid U/Th, retained K proxy |
| RingStrips, Vessel | 0.131e-6 | 0.034e-6 | omitted | Bq/kg; retained Table 7.1 EFCu |
| Lens | 123e-6 | 40.7e-6 | 300e-6 | Bq/kg; retained Table 7.1 Suprasil |
| Sensors | 2e-3 | 2.8e-3 | 9e-3 | Bq/kg; retained Table 7.1 Silicon |
| Resistors | derived 3.13243176941e-8 | derived 4.770319949e-9 | derived 1.41552782228e-7 | Bq/reference-piece; completed row 60 |

The schema derives **28 rows**: four layer families ×3, support3, strip2,
vessel2, lens3, sensor3, resistor3. Ten physical families map to the same seven
categories. Equilibrium daughters travel in parent jobs; they are not additional
jobs. Missing assays are not measured zeroes. Original v1 matrix and
`config/study/cygno-11x7-v1.json` are preserved as historical references;
production uses v2 and rejects v1. `read_matrix(..., historical=True)` is required
to validate the old matrix as a reference.

## Constructed quantities and normalization

```sh
/path/to/build/geometry_quantities /path/to/quantities.tsv cygno-11x7-v1 /path/to/geometry.json
python3 study/source_matrix.py config/study/cygno-300elj-radioassay-v2.json
```

Actual source lists and `GetMass()` sums produce the ten separate component rows.
The exporter verifies source/mass-map equality and records layout, model, policy,
geometry and compiled-source hashes. Boolean shell/frame volumes retain Geant4's
cached estimator; independent analytic checks do not replace exported masses.
The full quantity table is in the geometry report. Resistors use pieces, never kg.

Every scale remains `activity*quantity*31536000/generated_primaries`, with
Bq/kg×kg or Bq/piece×pieces. Generated counts come from successful run accounting,
not hit rows or thesis production statements. Campaign completeness is derived
from the validated matrix, not a literal 26/26 or 28/28 check. Failed chain
transport cannot become valid through a superficially complete ROOT file.

Group-Poisson errors combine in quadrature across independent contributions.
The ROOT reference retains counts/bin/year histograms; display copies are
counts/keV/year. The standalone compact analysis stores category density spectra
and exact counters. No new figure changes numerical histograms or energy windows.

## Limits of published comparisons

Historical normalization TSVs remain unverified and rejected by supported plotters.
Figure 7.5's original production revision/input set is unresolved. Published Table
7.2 contains a no-cut subset inconsistency; it is retained for comparison, never
used to adjust a calculated rate. Historical recovery records are under
`docs/history/`; the main model description covers the active geometry only.
The environment-specific PART122 full-chain failure remains a separate production
gate; see [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

## Constructed 11×7 sanity comparison and vessel decision

Geant4 11.4.2, Ranecu seed 12345; quantities from actual v1 and v2 exports.
`validation/material_sanity.py OLD.tsv NEW.tsv` reproduces this comparison;
new exports include actual density and summed material volume.
These are independent source-head activities, **not transported detector-rate
ratios**. No reported improvement comes from shrinking the resistor surrogate.

| Component | Old → new mass [kg] | Old → new placements | Old → new U238 [mBq] | Old → new Th232 [mBq] | Old → new K40 [mBq] |
|---|---:|---:|---:|---:|---:|
| RingSupports | 17.8260248094 → 17.8260248094 | 154 → 154 | 5.27650334 → 0.161325525 | 1.01430081 → 0.0900214253 | 1.26921297 → 1.26921297 |
| RingStrips | 28.1806349262 → 31.4979463002 | 616 → 3850 | 0.00369166318 → 0.00412623097 | 0.000958141587 → 0.00107093017 | omitted |
| Resistors | 0.0086082304 → 0.0248055808 | 770 → 4004 | 0.77 → 0.125422568 | 0.1078 → 0.0191003611 | 0.924 → 0.56677734 |
| Vessel | 3833.06578552 → 3833.06578552 | 1 → 1 | 0.502131618 → 0.502131618 | 0.130324237 → 0.130324237 | omitted |

Support old U/Th/K assay was 296/56.9/71.2 µBq/kg; new is 9.05/5.05/71.2.
The U and Th parent-activity reductions are 32.7071823× and 11.2673267×;
K is unchanged. Copper coverage is 44% → 50%, with EFCu assay unchanged;
constructed strip masses are canonical. Their ratio is not forced to the nominal
50/44 coverage ratio because Geant4 estimates thin Boolean volumes separately.

Old resistor source heads also included U235=0.0308, Ra226=0.1386 and
Th228=0.1001 mBq, giving total **2.0713 mBq** across 770 pieces.
The new 4004-piece total is **0.711300269164 mBq**,
a **2.91199103×** source-activity reduction.
This comparison mixes the old independently measured split heads with the new
equilibrium-assumption parent model; transport is required for a detector-rate
comparison.

The actual EFCu vessel weighs **3833.06578552 kg**, with constructed
shell volume **427797.520705 cm³** at 8.96 g/cm³. A same-volume
1.190-g/cm³ PMMA shell would weigh **509.079049639 kg**.
EFCu U/Th activities remain **0.502131617903 / 0.130324236708 mBq**.
For PMMA to improve BOTH totals requires specific activities strictly below
**0.986352941176 µBq/kg U238** and
**0.256 µBq/kg Th232**. Selected PMMA
9.05/5.05 exceeds both; hypothetical totals are
**4.60716539924 / 2.57084920068 mBq**.
PMMA also has no measured K. **Keep the vessel EFCu.** Lower density alone
does not establish lower total activity, and Cu/PMMA self-absorption and transport
are different. The PMMA design assay is adopted only for the existing PMMA
support; no vessel material switch is justified or performed.
