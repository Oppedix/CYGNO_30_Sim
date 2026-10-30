# Current v4 radioactive-source specification

The canonical pair is **`cygno-copper-cathode-v4` / `cygno-radioassay-v4`**.
The [machine-readable matrix](../config/study/cygno-radioassay-v4.json) defines
**23 material contributions**, nine physical families and seven reporting categories
by default. Optional `--gas-bkg yes` extends it to `cygno-radioassay-v4-gas-v1`: 25
contributions, ten families and nine categories. [Gas provenance](GAS_BACKGROUNDS.md)
defines C14 = 4.716324681686152e-5 and Rn222 = 1e-6 Bq/kg of gas mixture,
the published benchmarks, calculations, short-chain boundary and limitations.
`config/study/cygno-11x7-v4.json`, `samuele.json` and smoke A/B select v4.
Both internal and external use the identical detector construction; external
uses environmental GPS sources and never this internal radioactive matrix.

## Cathode and GEM assays

The `Cathode` is a single solid EFCu-assayed copper slab, 500 × 800 × 0.060 mm,
at the unchanged module centre. There are no core or skin volumes or jobs.
Apply **U238 = 1.31e-7 Bq/kg** and **Th232 = 3.4e-8 Bq/kg** to its entire
constructed mass. These are retained thesis Table 7.1 EFCu values; K is absent
(table x), not measured zero. Transport copper is `G4_Cu`, density 8.96 g/cm³.
The retained envelope is an explicit model assumption; no new thickness
specification was supplied.

Only GEMs retain a 50 µm Acrylic/PMMA core with 5 µm Cu skins. The stable
`GEMsPolyimide` source identifier denotes PMMA, density 1.190 g/cm³.
Core activities are retained Table 7.1 Acrylic upper limits adopted as values:
U238 **2.96e-4**, Th232 **5.69e-5**, K40 **7.12e-5 Bq/kg**.
`GEMsCopper` uses the EFCu U/Th values above. The radiopure support assay is
not assigned to GEM cores. Machine provenance records the historical reference
matrix and SHA256; separate laminate assays are retained solely as provenance.

## Camera lenses: Bq per physical piece

Source/provenance name: **`CYGNO_radioactivity_excel_suprasil`**.
The supplied spreadsheet assigns **3.843 kg to ONE physical camera lens**.
The initial conversion is specific activity × 3.843 kg:

| Isotope | Spreadsheet Bq/kg | Exact matrix Bq/piece |
|---|---:|---:|
| U238 | 1.23e-4 | 4.72689e-4 |
| Th232 | 4.07e-5 | 1.564101e-4 |
| K40 | 3.10e-4 | 1.19133e-3 |

These exact Bq/piece literals are stored in the matrix. Normalize by the actual
exported `Lens` placement count: four/module, **308** for 11×7 or **300** for
75-module layouts. Never multiply by 3.843 again and never rescale by the
surrogate's much smaller Geant4 mass. For 308 lenses the source-head totals are
0.145588212 / 0.0481743108 / 0.36692964 Bq (U/Th/K).

**Geant4 lens geometry and transport are completely unchanged:** full cylinder
radius 10 mm, thickness 2 mm, `Silicon Dioxide` at 2.65 g/cm³, existing positions
and uniform-volume sampling. The reference physical mass defines activity only;
it does not assert that the compact surrogate models a full camera lens.
The source name, physical reference mass, input specific activities, exact
converted values and unchanged-transport statement appear in matrix provenance,
which is copied into campaign manifests and both analysis outputs.

## Other components retained

| Component | U238 | Th232 | K40 | Unit and basis |
|---|---:|---:|---:|---|
| RingSupports | 9.05e-6 | 5.05e-6 | 7.12e-5 | Bq/kg; radiopure solid PMMA; K is conservative unmeasured proxy |
| RingStrips, Vessel | 1.31e-7 | 3.4e-8 | omitted | Bq/kg; Table 7.1 EFCu |
| Sensors | 0.002 | 0.0028 | 0.009 | Bq/kg; Table 7.1 Silicon |
| Resistors | 3.13243176941e-8 | 4.770319949e-9 | 1.41552782228e-7 | Bq/reference-piece; nominal completed MBNL component |

Support U/Th comes from Arnquist et al., NIM A 943 (2019) 162443,
DOI 10.1016/j.nima.2019.162443, Table 1 p.7, second Pre- set sample 3 (0.1527 g):
finished Reynolds UVT acrylic, not installed-batch qualification. Published
activity columns are used directly, without re-rounding concentrations.
Completed resistor provenance combines Anker arXiv:2601.05985v2 Table 9 p.19
and MacLellan arXiv:2604.15406v1 Table IV row 60. The reference tube is 17 mm
long, OD 6 mm, ID 4 mm, density 2.20 g/cm³, mass 0.000587477826221 kg;
nominal activity is assigned per compact surrogate placement. Thin coating and
metal masses are omitted. Detailed paper rows, methods, concentration
uncertainties and assumptions remain in the JSON provenance.

## Counts, normalization and campaign identity

Contributions: GEM core3 + GEM copper2 + Cathode2 + supports3 + strips2 +
vessel2 + lenses3 + sensors3 + resistors3 = **23**. No cathode PMMA/Polyimide
jobs, duplicate cathode copper skins, extra equilibrium daughters or omitted-K
zero jobs exist. U/Th secular equilibrium is a modelling assumption; K40 is a
single parent. Material full-chain macros reset stop-before controls to 0/0. Gas C14 also
resets to 0/0; gas Rn222 alone stops before Pb210 (82/210).

Both Python and native ROOT use, in the same multiplication order:
`activity * quantity * 60 * 60 * 24 * 365 / actual_generated_primaries`.
For Bq/kg, quantity is actual constructed component kg (the full sensitive gas mass for
each optional gas contribution). For Bq/piece (Lens and
Resistors), quantity is actual placement count. Contributions are scaled before
category sums; no assay or geometry uncertainty is propagated into group-Poisson
errors. Geometry export supplies material, density, mass, volume and pieces.

**New v4 transport and new campaign directories are mandatory in both modes.**
Model/matrix matching, geometry/source hashes, ROOT metadata, receipts and
campaign fingerprints prevent old results being mistaken for v4. A cross-model
resume fails before new probes or attempts are written. Existing campaign
outputs remain untouched. Historical models and references are isolated in
[model history](history/DETECTOR_MODELS.md).

```bash
# Repository root; fresh build and new output paths from the setup guide.
python3 study/source_matrix.py config/study/cygno-radioassay-v4.json
python3 study/simulate.py --config config/study/cygno-11x7-v4.json --list
mkdir -p "$CYGNO_RUNS/geometry-v4-NEW"
"$CYGNO_BUILD/geometry_quantities" "$CYGNO_RUNS/geometry-v4-NEW/quantities.tsv" \
  cygno-11x7-v1 "$CYGNO_RUNS/geometry-v4-NEW/geometry.json" --model cygno-copper-cathode-v4
```

See the [internal guide](../internal/README.md) for preflight, smoke, production
and analysis commands; [validation](TWO_STAGE_VALIDATION.md) lists production gates.
