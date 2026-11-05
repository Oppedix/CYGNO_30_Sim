# Current v4 radioactive-source specification

The only active default is **`cygno-copper-cathode-v4` / `cygno-radioassay-v4`**,
with the combined SNO acrylic GEM-core and Heraeus quartz lens assay substitution.
The [canonical JSON](../config/study/cygno-radioassay-v4.json) has **22 material
contributions**, nine component families and seven reporting categories.
Optional `--gas-bkg yes` adds C14/Rn222: **24 contributions**, ten families and
nine categories, under the existing `cygno-radioassay-v4-gas-v1` identity.
Model IDs, component IDs and CLI are retained. External GPS transport uses the
same detector but its own environmental source normalization.

## All active component assays at a glance

Activities are source-head values. `<` means an upper limit used numerically as
the nominal activity, not a measurement. Missing K sources are omitted. Transport
materials describe the existing Geant4 solids, not proven manufacturing choices.

| Component | Transport material | Assay reference | U238 | Th232 | K40 | Units | Status and source |
|---|---|---|---:|---:|---:|---|---|
| GEMsPolyimide | PMMA, C5H8O2 | SNO acrylic | <1.364e-5 | <4.466e-6 | omitted | Bq/kg | U/Th 95% CL per Table 3 caption; imported SNO NAA [19]. K unreported: agreed optimistic K40=0 assumption, not measured zero. [Leonard Table 3 row 38][sno] |
| GEMsCopper | G4_Cu | EFCu | 1.31e-7 | 3.4e-8 | omitted | Bq/kg | Retained table values; K absent (x), not measured zero. [Thesis Table 7.1][thesis] |
| Cathode | G4_Cu | EFCu | 1.31e-7 | 3.4e-8 | omitted | Bq/kg | Same retained assay, applied to entire solid slab. [Thesis Table 7.1][thesis] |
| RingSupports | PMMA, C5H8O2 | Reynolds UVT solid acrylic | 9.05e-6 | 5.05e-6 | 7.12e-5 | Bq/kg | U/Th measurements, uncertainties unreported for chosen conservative replicate; K unmeasured old-table proxy. [Arnquist Table 1 p.7][pmma]; K [Table 7.1][thesis] |
| RingStrips | G4_Cu | EFCu | 1.31e-7 | 3.4e-8 | omitted | Bq/kg | Retained table values; K absent. [Thesis Table 7.1][thesis] |
| Vessel | G4_Cu | EFCu | 1.31e-7 | 3.4e-8 | omitted | Bq/kg | Retained table values; K absent. [Thesis Table 7.1][thesis] |
| Lens | Silicon Dioxide, SiO2 | Heraeus quartz, NAA | <7.14798e-5 | <3.5885934e-6 | (6.4466325 ± 0.468846)e-5 | Bq/piece | U/Th 90% CL flip-flop limits; K central measurement and published Gaussian error. 3.843 kg/physical lens. [nEXO Table 6.1, printed p.141][lens] |
| Sensors | G4_Si | Silicon | 0.002 | 0.0028 | 0.009 | Bq/kg | Retained table values; measurement/limit confidence not established by retained transcription. [Thesis Table 7.1][thesis] |
| Resistors | ResistorFusedSilica, SiO2 | Completed MBNL, Suprasil 300/aSi/Ti/Pd | 3.1324317694119256e-8 | 4.770319948916886e-9 | 1.4155278222802016e-7 | Bq/reference-piece | Measurements: U 4.30±0.20 ppt, Th 2.00±0.16 ppt, natural K 7.90±0.20 ppb; analytical precision, not propagated. [Anker Table 9][resistor], [MacLellan Table IV row 60][radioassay] |
| Gas (optional) | CYGNO_gas, He/CF4 | Optimistic transferred benchmarks | — | — | — | Bq/kg mixture | C14=4.716324681686152e-5; Rn222=1e-6. Assumptions, not CYGNO measurements. [Gas sources and provenance](GAS_BACKGROUNDS.md) |

[sno]: https://arxiv.org/abs/0709.4524v2
[lens]: https://arxiv.org/abs/1805.11142v2
[pmma]: https://doi.org/10.1016/j.nima.2019.162443
[resistor]: https://arxiv.org/abs/2601.05985v2
[radioassay]: https://arxiv.org/abs/2604.15406v1
[thesis]: ../config/study/thesis-table7.1.json

## Conversions and physical reference pieces

Use the existing specific activities: U **12400**, Th **4060**, natural K
**30.5 Bq/g** (K already includes natural K40 abundance):

- U/Th: `pg/g = ppt = 1e-9 g/kg`; activity = concentration × 1e-9 × specific activity.
  SNO: 1.1 × 1e-9 × 12400 = **1.364e-5 Bq/kg**;
  1.1 × 1e-9 × 4060 = **4.466e-6 Bq/kg** (both limits).
- Natural K: `ppb = 1e-6 g/kg`; activity = ppb × 1e-6 × 30.5.
  Heraeus: (0.55 ± 0.04) × 1e-6 × 30.5 = **(1.6775 ± 0.122)e-5 Bq/kg**.

| Heraeus lens isotope | Specific activity Bq/kg | × 3.843 kg = Bq/physical piece |
|---|---:|---:|
| U238: <1.5 ppt | <1.86e-5 | <7.14798e-5 |
| Th232: <0.23 ppt | <9.338e-7 | <3.5885934e-6 |
| K40: natural K 0.55±0.04 ppb | (1.6775 ± 0.122)e-5 | (6.4466325 ± 0.468846)e-5 |

These exact per-piece central/limit values are stored in the matrix. Multiply
only by the actual lens placement count: four/module, **308** for 11×7 or
**300** for 75 modules. Never multiply by 3.843 twice or by the much smaller
Geant4 surrogate mass. The reference mass is retained from the physical-lens
normalization; it is not a new mass measurement of the Heraeus sample.

The Heraeus sample's exact optical grade and equivalence to a finished CYGNO
lens are **not demonstrated**. Neither assay substitution verifies a change in
manufacturing or optical performance. GEM transport remains 50 µm PMMA with
5 µm copper skins; lens transport remains the existing SiO2 cylinder at
2.65 g/cm³. Geometry, densities, dimensions, placements and sampling are unchanged.

Resistor concentrations use a nominal tube: length 17 mm, OD 6 mm, ID 4 mm,
density 2.20 g/cm³, mass 0.000587477826221 kg. Convert once to Bq/reference-piece
and assign each compact surrogate one piece; coating and metal masses are omitted.
The publications establish matching technology/results, not unique batch identity.
Machine provenance retains concentrations, uncertainties, sample limitations,
confidence conventions, upper-limit flags, chain assumptions and conversion constants.

## Normalization, integrity and execution

Contributions: GEM core2 + GEM copper2 + cathode2 + supports3 + strips2 + vessel2
+ lenses3 + sensors3 + resistors3 = **22** (24 with gas). There is no GEM K job.
U/Th secular equilibrium is a modelling assumption, not proven by chain-head
assays; K40 is a single parent. Material macros reset stop controls to 0/0;
optional Rn222 alone stops before Pb210 (82/210).

Python and native ROOT both use, left to right:
`activity * quantity * 60 * 60 * 24 * 365 / actual_generated_primaries`.
Quantity is actual constructed kg for Bq/kg, actual placement count for Bq/piece.
Scale contributions before category sums. Group-Poisson errors do not propagate
assay uncertainty or geometry/model uncertainty.

**Fresh internal campaigns in new directories are required for this assay update.**
Transport geometry is unchanged, so the individual Monte Carlo responses would
in principle permit activity reweighting. The existing CLI has no independent
normalization override: it validates the stored matrix against canonical values,
and matrix snapshots enter campaign/job fingerprints and checksums. Editing a
stored matrix, deleting its GEM K job, or replacing checksums would invalidate
its scientific identity. No validation bypass or reweighting pipeline is added.
Old campaigns remain intact and can retain their original interpretation through
their archived source snapshot. This assay-only update does not require fresh
external GPS transport; external normalization does not use these assays.

```bash
# Repository root; environment/path setup from SETUP.md.
python3 study/source_matrix.py config/study/cygno-radioassay-v4.json
python3 study/simulate.py --config config/study/cygno-11x7-v4.json --list
```

See the [internal guide](../internal/README.md), [cluster/CNAF commands](../internal/docs/WORKFLOW.md)
and [validation gates](TWO_STAGE_VALIDATION.md). `internal/cluster/run.sh` runs
the internal campaign inside an allocated node; `condor/submit_replicas.sh` is
an **external-only** frozen-replica submitter. Historical specifications remain
in [history](history/DETECTOR_MODELS.md).
