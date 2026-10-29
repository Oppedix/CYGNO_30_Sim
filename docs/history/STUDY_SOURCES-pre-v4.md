> Historical pre-v4 record; [current v4 model](../SINGLE_MODULE_GEOMETRY.md).

# Current radioactive-source matrix and normalization provenance

Preferred **internal v3**: [`cygno-300elj-radioassay-v3.json`](../../config/study/cygno-300elj-radioassay-v3.json),
physical model `cygno-acrylic-v3`, 26 contributions. **v2** remains supported with
[`cygno-300elj-radioassay-v2.json`](../../config/study/cygno-300elj-radioassay-v2.json),
physical model `cygno-300elj-v2`, 28 contributions. Both use `uniform-volume-v1`.
`study/source_matrix.py` validates each version and rejects matrix/model mixing.
External defaults to the same v3 detector, supports explicit v2 selection, and
keeps its independent environmental sources and normalization.

The [geometry report](../SINGLE_MODULE_GEOMETRY.md#component-activities-v2-and-v3)
places the v2/v3 activities beside constructed masses, materials and densities.
This page retains the detailed bibliographic basis and interpretation.

## Historical activities: original C++ versus Table 7.1

The authority for v3 is the preserved [`thesis-table7.1.json`](../../config/study/thesis-table7.1.json),
SHA256 `de7eddc44076f0697d36a693894eb0d927da964770dc9762f684b34eb0a65836`.
It was the production matrix at commit `990a287`, before the 300ELJ material
change in `35e4eb0`. Do not confuse `thesis-table7.1-v1` with the later
`cygno-300elj-radioassay-v1`: that later v1 already uses Arnquist layer assays.

The upstream [Samuele PlotNormalizedSpectra.cpp](https://github.com/SamueleTorelli/CYGNO_30_Sim/blob/master/analysis/PlotNormalizedSpectra.cpp)
(blob `543796a833f58c1c078c9fd890f2e890aa87753f`) has different, lumped assays:

| Reference/component | U238 [µBq/kg] | Th232 [µBq/kg] | K40 [µBq/kg] |
|---|---:|---:|---:|
| Upstream C++ GEMs, lumped | 13200 | 5450 | 63100 |
| Upstream C++ Cathodes | 12 | 4.1 | 61 |
| Table 7.1 GEMsCore Acrylic | 296 | 56.9 | 71.2 |
| Table 7.1 GEMsOuter and Cathodes EFCu | 0.131 | 0.034 | omitted (x) |

The upstream C++ additionally lists GEM U235/Co60/Cs137 and cathode Co60/Cs137.
Those are not the chosen Table 7.1 model; no such source is silently added or
approximated. Reproducing those extra terms would require their own definitions
and new transport, since v2 does not simulate them in these components.

The upstream [DetectorConstruction.cc](https://github.com/SamueleTorelli/CYGNO_30_Sim/blob/master/src/DetectorConstruction.cc)
(blob `5a09d4da657f802f922175d66081697e4d4063f0`) constructs a **29 µm PMMA GEM
core**, a Boolean copper GEM exterior and a **1 mm solid copper cathode** (the
cathode G4Box receives 0.05 cm as half-Z). The historical source matrix therefore
has no polymer cathode core. v3 deliberately retains the v2 **50 µm core plus
two 5 µm copper skins** for both GEM and cathode, changes the two core transport
materials to PMMA at 1.190 g/cm³, and assigns the historical GEM-core Acrylic
assay to the cathode core too. This cathode extension is an explicit study
choice, not a Table 7.1 cathode measurement. Acrylic upper limits are used as
stated values, following the old pipeline; they are not a new batch assay.

| Internal scenario | GEM core | Cathode core | Copper activity | Jobs |
|---|---|---|---|---:|
| v2, retained comparison | Kapton50; Arnquist Table 5 | Kapton50; Arnquist Table 5 | separate laminate Cu U/Th/K | 28 |
| **v3 (preferred for this internal study)** | PMMA50; Table 7.1 Acrylic U/Th/K | PMMA50; same Acrylic U/Th/K | Table 7.1 EFCu U/Th; K omitted | 26 |

`GEMsPolyimide` and `CathodesPolyimide` remain stable **source identifiers** in
v3 for compatibility with the sampler and source lists; their actual exported
material is **PMMA**, not polyimide. `GEMsCopper_K40` and `CathodesCopper_K40`
are absent from the v3 matrix, not zero-activity jobs. Cage, supports, resistors,
vessel, optics, source sampling, isotope controls and geometry dimensions retain
v2 behavior. The historical Acrylic core assay differs from the newer radiopure
PMMA support assay; the latter is not transferred to the cores.

PMMA50 is a historical-material study scenario, not a claim about installed
CYGNO GEM composition. The collaboration's [December 2025 material inventory,
slide 16](https://agenda.infn.it/event/48480/contributions/274879/attachments/144292/219180/25_12_18_CYGNO_collaboration_meeting.pdf#page=16)
identifies GEM and cathode as Kapton+Cu. GEM microscopic holes remain absent in
both versions; the cathode is unperforated. No new hole model is implied.

## Campaign reuse, normalization and new transport

**The selected physical v3 cannot be obtained by reweighting v2 ROOT files.**
Changing Kapton to PMMA changes composition, density, source mass and transport.
All **26 v3 contributions** need new Geant4 runs: particles from the other
components also traverse the changed cores. There is no new isotope requirement
for the selected v3; its source heads are a subset of v2. A 29 µm core, old
Boolean copper shape, solid-copper historical cathode or physical GEM holes would
also require new transport and are not implemented here.

Old campaigns remain analyzable as v2, without editing their matrices/manifests,
relabeling metadata, modifying fingerprints or disabling preflight/checksums.
The runner chooses the matrix from the configured model and rejects an explicit
mismatched `--matrix`. Use a **new** v3 campaign directory; resume only with the
same identity. Each analysis keeps the original simulation matrix and separately
records `normalization-scenario.json`; Python also records it in
`analysis-manifest.json`, native ROOT in `provenance/`. There is no activity
replacement switch that could pass v2 transport off as physical v3.

The scale stays `activity * constructed mass-or-piece-count * 31536000 / actual
generated primaries`, applied independently before category sums, with statistical
variances scaled quadratically. Both analyses use the matching saved matrix and
actual masses; their shared historical two selections are regression checked.
The extra topology selections remain specific to the native ROOT analysis.
Reports always use a new output directory. Cluster commands are in
[internal README](../../internal/README.md) and [native ROOT guide](../../analysis/common_c++/README.md).

For a 500×800 mm² foil, core50 weighs 28.4 g in Kapton or 23.8 g in PMMA.
Each module has six GEMs and one cathode; its copper skins weigh 250.88 g.
A same-EFCu-copper source-head comparison gives:

| Core/scenario, per module | U238 [µBq] | Th232 [µBq] | K40 [µBq] | Sum [µBq] |
|---|---:|---:|---:|---:|
| Kapton50, v2 core assays + EFCu skins | 13.788235 | 5.513143 | 654.847200 | 674.148578 |
| PMMA50, v3 Acrylic assays + EFCu skins | 49.346465 | 9.488070 | 11.861920 | 70.696455 |

This first comparison row already substitutes EFCu for v2's laminate copper to
isolate the core choice. The total source-head sum falls by 9.53582×, dominated
by K; U and Th increase. It is not a detector-rate prediction and does not sum
all daughter decays. The corresponding v3 77-module GEM+cathode sum is
5.44362705 mBq. Actual exports, not rounded table entries, normalize analyses.

## v2 layer assays (retained reference)

In **v2**, GEM and cathode transport is Cu5/G4_KAPTON50/Cu5 µm. Separate-material assays
from [Arnquist et al., arXiv:1910.04317v1, Table 5](https://arxiv.org/abs/1910.04317v1)
apply independently to polyimide and each copper skin. Table 4 whole-laminate
values serve only as provenance/cross-check. The complete concentration table,
uncertainties, 26/74 paper consistency calculation, new 44.2092/55.7908 mass
fractions and nominal converted activities are in
[SINGLE_MODULE_GEOMETRY.md](../SINGLE_MODULE_GEOMETRY.md#radioactive-sources-and-provenance).

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
are absent from v2 and v3. The resistor update itself does not change
GEM/cathode/gas/optics, decay physics, cuts, grouping or normalization formulas;
the separate v3 core-material change is described above.

## Active assay membership

| Source family | U238 | Th232 | K40 | Unit/basis |
|---|---:|---:|---:|---|
| RingSupports | 9.05e-6 | 5.05e-6 | 71.2e-6 | Bq/kg; measured solid U/Th, retained K proxy |
| RingStrips, Vessel | 0.131e-6 | 0.034e-6 | omitted | Bq/kg; retained Table 7.1 EFCu |
| Lens | 123e-6 | 40.7e-6 | 300e-6 | Bq/kg; retained Table 7.1 Suprasil |
| Sensors | 2e-3 | 2.8e-3 | 9e-3 | Bq/kg; retained Table 7.1 Silicon |
| Resistors | derived 3.13243176941e-8 | derived 4.770319949e-9 | derived 1.41552782228e-7 | Bq/reference-piece; completed row 60 |

The **v2** schema derives **28 rows**: four layer families ×3, support3, strip2,
vessel2, lens3, sensor3, resistor3. Ten physical families map to the same seven
categories. Equilibrium daughters travel in parent jobs; they are not additional
jobs. Missing assays are not measured zeroes. Original v1 matrix and
`config/study/cygno-11x7-v1.json` are preserved as historical references;
v2 production rejects v1; preferred internal v3 uses the separate 26-row matrix above. `read_matrix(..., historical=True)` is required
to validate the old matrix as a reference.

## Constructed quantities and normalization

Activate Geant4 and define paths via [common setup](../SETUP.md). Export each
model explicitly to a fresh diagnostic directory outside campaigns:

```bash
# Directory: repository root; common Geant4 environment/build active.
cd "$CYGNO_SRC"
mkdir -p "$CYGNO_RUNS/geometry-v3-NEW" "$CYGNO_RUNS/geometry-v2-NEW"
"$CYGNO_BUILD/geometry_quantities" "$CYGNO_RUNS/geometry-v3-NEW/quantities.tsv" \
  cygno-11x7-v1 "$CYGNO_RUNS/geometry-v3-NEW/geometry.json" --model cygno-acrylic-v3
"$CYGNO_BUILD/geometry_quantities" "$CYGNO_RUNS/geometry-v2-NEW/quantities.tsv" \
  cygno-11x7-v1 "$CYGNO_RUNS/geometry-v2-NEW/geometry.json" --model cygno-300elj-v2
```

Do not replace a campaign's saved quantities/geometry with these diagnostics.
Omitting `--model` on the exporter selects v3, as in the simulation CLI.
Historical v2 exports require `--model cygno-300elj-v2`. Matrix validation
is performed by the runner; `study/source_matrix.py` is a library, not a CLI.

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
gate; see [KNOWN_ISSUES.md](../KNOWN_ISSUES.md).

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
