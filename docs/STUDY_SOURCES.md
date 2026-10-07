# Current radioactive-source matrix and normalization provenance

Canonical specification:
[`cygno-300elj-radioassay-v1.json`](../config/study/cygno-300elj-radioassay-v1.json),
validated by `study/source_matrix.py`. Detector `cygno-300elj-v1`, source policy
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

## Retained assays and chain policy

| Source family | Assay | U238 | Th232 | K40 | Units |
|---|---|---:|---:|---:|---|
| RingSupports | Acrylic upper limits used as values | 296e-6 | 56.9e-6 | 71.2e-6 | Bq/kg |
| RingStrips, Vessel | EFCu | 0.131e-6 | 0.034e-6 | omitted | Bq/kg |
| Lens | Suprasil | 123e-6 | 40.7e-6 | 300e-6 | Bq/kg |
| Sensors | Silicon | 2e-3 | 2.8e-3 | 9e-3 | Bq/kg |
| Resistors | Al2O3 | 1e-6 | 0.14e-6 | 1.2e-6 | Bq/piece |

Resistors additionally retain U235=0.04e-6, Ra226=0.18e-6 and Th228=0.13e-6
Bq/piece. U238 upper segment stops before ground-state Ra226; Th232 before
Th228. Lower segments reset both stop controls. Full-chain transport remains
requested for all rows; K40 is one parent contribution. Non-resistor equilibrium
daughters are part of parent jobs, never duplicate jobs. Omitted assays are not
measured zeroes. The matrix records both the original transcription checksum
and its thesis-reference provenance.

The schema derives **31 rows**: four layer families ×3, support3, strip2,
vessel2, lens3, sensor3, resistor6. There are ten physical families and the same
seven reporting categories. GEMs joins PI/Cu; Cathodes joins PI/Cu; Field Cage
joins support/strip. Each contribution is normalized before categories are summed.
All nominal activities, categories, units, isotope membership, provenance and
chain boundaries are validated; missing/extra/malformed rows fail.

## Constructed quantities and normalization

```sh
/path/to/build/geometry_quantities /path/to/quantities.tsv cygno-11x7-v1 /path/to/geometry.json
python3 study/source_matrix.py config/study/cygno-300elj-radioassay-v1.json
```

Actual source lists and `GetMass()` sums produce the ten separate component rows.
The exporter verifies source/mass-map equality and records layout, model, policy,
geometry and compiled-source hashes. Boolean shell/frame volumes retain Geant4's
cached estimator; independent analytic checks do not replace exported masses.
The full quantity table is in the geometry report. Resistors use pieces, never kg.

Every scale remains `activity*quantity*31536000/generated_primaries`, with
Bq/kg×kg or Bq/piece×pieces. Generated counts come from successful run accounting,
not hit rows or thesis production statements. Campaign completeness is derived
from the validated matrix, not a literal 26/26 or 31/31 check. Failed chain
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
