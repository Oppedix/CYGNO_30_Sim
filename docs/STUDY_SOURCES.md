# Published source matrix and normalization provenance

Transcribed and validated on 2026-09-21 (historical Phase 3).
The executable source specification is
[`config/study/thesis-table7.1.json`](../config/study/thesis-table7.1.json).
It contains 26 component/chain-start contributions, independent of layout and
of the detector-internal model. It declares assays and chain boundaries; it is
not a completed simulation campaign or evidence of agreement with published rates.
The canonical study and historical A/B campaigns use this same matrix with
code-compatible internals and the historical sampler. The `thesis-7.3` work is
deferred, unsupported, and preserved only on the separate local recovery branch;
see [recovery provenance](STUDY_PROGRESS.md#recovery-and-baseline).
The workflow and analysis infrastructure are finalized, but `PART122` in the tested
Geant4 11.4.2/data environment prevents a complete published U/Th background;
see [known issues](KNOWN_ISSUES.md).

## Reference and transcription

Source: read-only `local_refs/context_solarnuwithcygno.pdf`, Table 7.1, printed
p. 186 (extract p. 11), with chain and normalization discussion on pp. 186–188.
SHA-256: `33d8b3c099c88bec4c7b1acaf0944305b0a85229ab4264e8f76445092c0d8825`.
Table 7.1 was visually checked in Phase 3; the adjoining discussion was extracted
and inspected. Rendered/extracted scratch material is outside the repository at
`../../build/cygno-study/validation-results/phase3-reference/`.

| Assay material | Source components | U-238 | Th-232 | K-40 | Units |
|---|---|---:|---:|---:|---|
| Acrylic | GEMsCore, RingSupports | 296e-6 | 56.9e-6 | 71.2e-6 | Bq/kg |
| EFCu | GEMsOuter, RingStrips, Cathodes, Vessel | 0.131e-6 | 0.034e-6 | omitted | Bq/kg |
| Silicon | Sensors | 2e-3 | 2.8e-3 | 9e-3 | Bq/kg |
| Suprasil | Lens | 123e-6 | 40.7e-6 | 0.3e-3 | Bq/kg |
| Al2O3 | Resistors | 1e-6 | 0.14e-6 | 1.2e-6 | Bq/piece |

Resistors additionally have U-235 = 0.04e-6, Ra-226 = 0.18e-6 and Th-228 =
0.13e-6 Bq/piece. Acrylic values are upper limits used as values, as explicitly
stated in the thesis; the matrix retains that qualification. Entries marked
`x` are omitted. An omitted assay is not a measured zero.

For all non-resistor U-238 and Th-232 contributions, the table's equilibrium
Ra-226/Th-228 entries belong to the parent job. They are not additional jobs.
There are 20 mass-normalized contributions and six piece-normalized resistor
contributions, spanning nine physical source components and seven plot categories.

| Resistor segment | Start Z/A | Stop before ground-state decay | Activity, Bq/piece |
|---|---|---|---:|
| U-238 upper | 92/238 | Ra-226, 88/226 | 1e-6 |
| Ra-226 lower | 88/226 | none | 0.18e-6 |
| Th-232 upper | 90/232 | Th-228, 90/228 | 0.14e-6 |
| Th-228 lower | 90/228 | none | 0.13e-6 |
| U-235 full | 92/235 | none | 0.04e-6 |
| K-40 parent | 19/40 | none | 1.2e-6 |

`study/source_matrix.py` validates the component/unit/chain structure and provides
`decay_commands()`. Every segment uses `/rdecay01/fullChain true`. A lower segment
explicitly resets both stop controls to zero, preventing an inherited boundary
from killing its primary. The existing tracking policy allows excited-state
nuclear de-excitation and kills the selected ground-state boundary before its
radioactive decay. A direct test of the actual tracking callback checks both
boundaries, primary/daughter behavior, excited states and resets without
transporting full chains. It does **not** validate lifetime thresholds or branching.

The installed one-year long-lived-decay threshold and Bi-212/Pb-208 issue remain
unresolved. No lifetime, decay probability, dataset, isotope list or physics
setting has been changed. The matrix's full-chain flag is a requested treatment,
not proof that all long-lived members were transported. The runner and subsequent
preflight must retain failures/incompleteness and must not manufacture valid
normalization from the presence of a ROOT file or from its hit count.

## Historical Figure 7.5 input investigation

The following local Git objects were read without switching branches. The earlier
`331f4e6:analysis/PlotNormalizedSpectra.C` was also inspected to distinguish active
maps from commented material. Scope is the available public history through
`26ddbdb`, not unpublished files or unknown external production runs.

| Revision | Inspected active inputs and change | Consequence |
|---|---|---|
| `0b0d1dbdb5e3a38e35c1bb060384fd76ff961241` | Main `.cpp` activates a block explicitly described as testing maps: GEMs Co-60/Cs-137, Rings Th-232, Cathodes U-238. Larger maps are commented out. | Not the thesis matrix. |
| `67239bd13db0ab0c65b255f1df0056d5160c0197` | Retains those testing maps; changes histogram ordering/stack writing. | No published assay match established. |
| `48b5b6a88afd0ed56c2cf008aa0aa5874472db95` | Activates six-component main maps, changes cathode mass to 809.7 kg and GEM mass to 18.75 kg. Adds single-daughter and GEMchain variants. Main inputs omit resistors and retain ambiguous GEMs/Rings. | Not Table 7.1's nine physical contributions. |
| `f2ad08ef4c8a902979ebf5fae6d4a1d034c83f94` | Main plotter unchanged; GEMchain switches Th-232 to U-235 at 5.45e-3 Bq/kg and 1e5 events; `_single` changes 900 to 1200 bins. | A chain diagnostic, not Figure 7.5 provenance. |
| `26ddbdbd110426c38ea71ba3d1341a2b26b6d090` | Main plotter is byte-identical to `48b5b6a`; U-235 daughter diagnostic remains separate. | No later main-map resolution in this inspected public lineage. |

The main `.cpp` SHA-256 at each of the last three revisions is
`6e78305154ec5aa3c363bdff24e61863b547faf255f7c75a4af4242bae5bd2d1`.
For reproducibility, inspect `git show REVISION:analysis/reference_cpp/PlotNormalizedSpectra.cpp`
and the corresponding `_single.cpp` / `_GEMchain.cpp` objects.

Concrete mismatches in the active main map include vessel U/Th/K activities
296e-6 / 56.9e-6 / 71.2e-6 Bq/kg (acrylic-like values instead of EFCu U/Th only),
sensor K-40 = 3.5 Bq/kg instead of 0.009, and lens K-40 = 0.00031 instead of
0.00030. The 1102.24 kg vessel mass has no demonstrated relationship to either
current constructed layout. Other masses and mixed 1e6/1e7 denominators likewise
do not identify the thesis production inputs. `_single` has U-235 daughters and
branch-adjusted denominators; these are not substituted for generated-primary
counts in the new matrix. The historical TSVs remain untouched and rejected as
`historical-unverified` by the supported plotters.

**Figure 7.5's exact input set and simulation revision remain unresolved.**
The investigation rules out treating these inspected active maps as the published
source specification; it does not prove no matching private or other historical
input ever existed. No scale factor has been chosen to match the published totals.

## Constructed quantities

Export from the existing detector construction without transporting particles:

```sh
/path/to/build/geometry_quantities /path/to/quantities.tsv legacy-25x3
/path/to/build/geometry_quantities /path/to/quantities-current.tsv cygno-5x5x3-v1
python3 study/source_matrix.py config/study/thesis-table7.1.json
```

The exporter sums `GetLogicalVolume()->GetMass()/kg` over the actual ordered source
lists, records their sizes as pieces, and checks the sums against the detector's
component mass map. Output includes layout, model, source policy, geometry hash,
method and actual material names. `read_quantities()` requires matching identity
and all nine components. `quantity_for()` selects kg or pieces from the assay unit.
It does not infer a missing quantity from old tables. The exporter currently
supports the code-compatible geometry for both runtime layouts. Detector-model
corrections are deferred and are not a supported configuration.

Phase 3 export on Geant4 11.4.2 (rounded for display; TSV retains 17-digit precision):

| Component | Constructed mass, kg | Pieces | Constructed material |
|---|---:|---:|---|
| Cathodes | 268.8 | 75 | G4_Cu |
| GEMsOuter | 72.5738647796 | 450 | G4_Cu |
| GEMsCore | 6.2118 | 450 | PMMA |
| RingStrips | 27.4486703826 | 600 | G4_Cu |
| RingSupports | 17.3630111780 | 150 | PMMA |
| Resistors | 0.00838464 | **750** | Al2O3 |
| Lens | 0.499513231921 | 300 | Silicon Dioxide |
| Sensors | 0.13929672 | 300 | G4_Si |
| Vessel, legacy-25x3 | 4116.55627383 | 1 | G4_Cu |
| Vessel, cygno-5x5x3-v1 | 4203.48937257 | 1 | G4_Cu |

All non-vessel quantities are identical between A/B. Resistor normalization uses
750 pieces, never its 0.00838464 kg mass. Assay labels such as Suprasil and EFCu
identify the thesis radioactivity inputs; they do not rename or correct the
code-compatible materials or dimensions.

Geant4's Boolean-solid volumes are estimated, not necessarily exact analytic
volumes. Inspection of the installed 11.4.2 source (`G4SubtractionSolid.cc`,
`G4BooleanSolid.cc`, `G4VSolid.cc`) shows the cached volume estimate using the
configured 1,000,000 samples and 0.001 mm epsilon, with a fixed internal volume
estimator seed. The legacy vessel's exact box-shell expression gives
4116.96653312 kg, versus the constructed 4116.55627383 kg (about -0.010%).
The software intentionally exports the actual construction totals and does not
replace them with an analytic correction. Validation separately checks exact
list/mass-map agreement and an analytic vessel diagnostic within 5%; this bound
is not a scientific uncertainty estimate. Future environments must re-export
quantities and record their library/build provenance.

## Normalization and categories

The existing normalized plotters accept the explicit `quantity-v2` format described
in [ANALYSIS.md](ANALYSIS.md). Each contribution receives
`activity * quantity * 31,536,000 / generated_primaries`, using kg with Bq/kg or
pieces with Bq/piece. Eq. 7.14 rounds the year to 3.15e7 seconds; the retained
365-day convention is larger by approximately 0.1143%. No generated event counts
are taken from the thesis's 1e7 production statement or inferred from hit rows.

Only after scaling, `GEMsOuter + GEMsCore` are summed into GEMs and
`RingStrips + RingSupports` into Field Cage, including all their chain starts.
The remaining categories are Camera Lenses, Vessel, Camera Sensors, Cathodes and
Resistors. Individual contribution histograms and existing stacks remain available;
new category histograms/stacks are written under `Categories/`. Statistical bin
errors combine in quadrature under the independent-job assumption. Assay and
geometric systematic uncertainties are not included. Binning, first-position
fiducial cuts, group-energy convention and world-Z position plots are unchanged.
Spectra remain **counts per bin per year**, not counts/keV/year; divide by the
bin width for a density display. Energy-window boundary/overflow accounting is
a runner task, including the 10 keV threshold that can straddle a histogram bin.

## Published comparison limits

Table 7.2's no-cut 10–400 keV value, 3.3e5/year, exceeds its >10 keV value,
3.2e5/year, despite the former interval being a subset. This inconsistency is
preserved; neither entry has been corrected or used to tune a scale factor.
The Table 7.3 targets remain as recorded in `BACKGROUND_EXPERIMENT.md`.
Finite smoke fixtures only verify the calculation and pipeline. They cannot
establish agreement with Figure 7.5/7.6, full decay-chain completeness, or the
scientific validity of the code-compatible detector and historical source sampler.
