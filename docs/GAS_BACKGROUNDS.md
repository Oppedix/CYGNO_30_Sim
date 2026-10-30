# Optional internal gas backgrounds

`--gas-bkg yes` adds `Gas_C14` and `Gas_Rn222` to the current v4 internal
campaign. Default `--gas-bkg no` retains the original 23 material contributions,
their seeds, macros, source activities, normalization and reporting categories.
The enabled matrix is `cygno-radioassay-v4-gas-v1`: 25 contributions, ten physical
source families, nine reporting categories. The detector model remains
`cygno-copper-cathode-v4 / uniform-volume-v1`. External is unchanged.

## Scientific choices

These are **optimistic feasibility assumptions, not CYGNO gas measurements**,
procurement specifications, contamination upper bounds or demonstrated CYGNO
purification performance. Both must be revisited after gas-batch assays and
measurements in an operating recirculation system.

| Contribution | Adopted input | Activity per kg of the complete He/CF4 mixture | Basis |
|---|---|---:|---|
| C14 | C14/C12 atom ratio = 1.94e-18 | 4.716324681686152e-5 Bq/kg | Borexino scintillator benchmark transferred to CF4 carbon |
| Rn222 | Constant parent activity = 1 microBq/kg | 1e-6 Bq/kg | Rounded XENONnT benchmark transferred to detector gas |

[G. Alimonti et al., *Measurement of the 14C abundance in a low-background
liquid scintillator*, Phys. Lett. B 422 (1998) 349–358](https://doi.org/10.1016/S0370-2693(97)01565-7)
measured C14/C12 = (1.94 ± 0.09)e-18 in high-purity liquid scintillator.
The paper also gives the approximately 156 keV beta endpoint and conventional
5730-year half-life. We transfer its isotope ratio to the carbon in CF4;
chemical purification alone does not establish that CF4 attains this ratio.
Feedstock origin, synthesis, air contamination and cosmogenic production matter.
The helium and fluorine mass must not be counted as carbon.

[E. Aprile et al., *Radon Removal in XENONnT down to the Solar Neutrino
Level*, Phys. Rev. X 15 (2025) 031079](https://doi.org/10.1103/zc1w-88p6)
reports 0.90 ± 0.02(stat) ± 0.07(syst) microBq/kg in liquid xenon after material
selection and online cryogenic distillation. We adopt a rounded 1 microBq/kg
**of gas mixture**, rather than claiming that xenon purification transfers to
He/CF4. This is an ambitious target: emanation depends on materials, surfaces,
leaks and circulation, not simply target mass.

There is also gas-supply precedent at a comparable volumetric scale:
[G. Alimonti et al., *Science and technology of Borexino*, Astropart. Phys.
16 (2002) 205–234](https://doi.org/10.1016/S0927-6505(01)00110-4)
describes high-purity nitrogen at approximately 1 microBq/m3 produced by charcoal
purification of liquid nitrogen before evaporation. This supports the
feasibility scale of purified supply gas, **not** the activity inside an
emanating He/CF4 detector. Its gas/volume conditions differ; no STP-to-detector
volume equality is assumed. Our Rn input corresponds to 1.5273872 microBq/m3
at the mixture density implemented here.

## Calculation and normalization

Use the existing material definition, without changing gas composition,
density, pressure, temperature, volumes or placements. Its nominal partial
densities are 0.6 × 162.488 and 0.4 × 3574.736 g/m3, so the mixture density is
1.5273872 kg/m3. The fraction of mixture mass carried by carbon is

```text
wC = [0.4*3574.736 / (0.6*162.488 + 0.4*3574.736)]
     * [12.0107 / (12.0107 + 4*18.998)]
   = 0.1277694840552402

aC14 = ln(2)/(5730*31536000) * 6.02214076e23
       * (1000/12.0107) * wC * 0.9893 * 1.94e-18
     = 4.716324681686152e-5 Bq/kg mixture
```

12.0107 g/mol and 18.998 g/mol are the constructed carbon/fluorine molar masses;
0.9893 is the assumed natural C12 atom fraction. Avogadro's constant is exact.
5730 years is the adopted activity-conversion convention, using the same
365-day year as the campaign. Geant4 decay lifetimes, branching, atomic
relaxation and beta spectral data remain those of the recorded nuclear datasets;
no spectrum or nuclear data is replaced with an analytic approximation.

`geometry_quantities --gas-bkg yes` exports one additional `Gas` row by summing
the masses of the actual sensitive `GasVolume` placements. It checks the
constructed carbon fraction against the normalization assumption. Readers
check gas material, density, mass/volume and placement count. Both gas sources
use this **same total mass once each**, never the vessel mass, carbon mass alone,
gas-side count as a mass, or an already fiducialized mass.

For the planar 77-module layout there are 154 sensitive gas boxes, each
0.5 × 0.8 × 0.5 m3: 30.8 m3, 47.04352576 kg of mixture and about 6.010727 kg
of carbon. The nominal source-head rates are:

| Source | Total parent activity [Bq] | Parent decays / 365-day year |
|---|---:|---:|
| C14 | 0.002218725416554263 | 69969.72473645523 |
| Rn222 | 0.00004704352576 | 1483.56462836736 |

These are source-parent counts, **not selected electron-recoil rates**. Each
contribution uses `activity * constructed_gas_kg * 60 * 60 * 24 * 365 /
actual_generated_primaries`. Detector acceptance and all analysis cuts follow
transport. Do not multiply radon activity by the number of daughters: one
primary already generates the modeled short chain.

## Decays, sampling and scope

The existing uniform-volume sampler selects one equal-volume gas placement,
then a point uniformly throughout it, on both sides and across all modules.
Only sensitive drift gas is included. GEM transfer gaps, plumbing, reservoirs,
and any other unmodeled gas inventory are excluded.

C14 (Z=6, A=14) beta-decays to stable N14. Rn222 (Z=86, A=222; half-life about
3.82 days) initiates the short chain Rn222 → Po218 → Pb214 → Bi214 → Po214 →
Pb210, with Geant4 retaining branching and excited-state de-excitation.
The existing stop-before control kills ground-state Pb210 (Z=82, A=210) before
its decay. The approximately 22-year Pb210 tail, Bi210 and Po210 are excluded;
they are not assumed to be in secular equilibrium with newly introduced radon.
This models a constant radon inventory with retained short-lived daughters
after equilibration over hours. It does not model startup transients or an
exposure-dependent buildup of long-lived daughters.

The inherited internal tracking policy stops heavy ions at birth positions.
Alpha particles, electrons and photons transport normally, and existing output
selection rules apply; the standard spectra select electron/positron groups.
Ion drift, diffusion, recoil motion, plate-out, daughter removal by circulation,
alpha/recoil discrimination, detector response and gas purification kinetics
are outside this bulk ER feasibility model. They can change daughter yields
and spatial acceptance in either direction. Gas-TPC radon progeny are a real
additional concern, as demonstrated by
[J.B.R. Battat et al., JINST 9 (2014) P11004](https://doi.org/10.1088/1748-0221/9/11/P11004).
Neither this scenario nor its group-Poisson errors bound those effects.

Gas Rn is an independent residual dissolved-radon budget. It is not calculated
as emanation from the material U238 assays, which retain their original
stationary full-chain assumption. There is no transfer of nuclei from materials
to gas and no additional U238/Ra226 gas job. An eventual coupled emanation and
surface model must replace these assumptions consistently.

## Run, resume and analyze

Start at the repository root with the common build/environment from
[setup](SETUP.md). Use distinct new campaign directories:

```bash
# Original 23-source campaign; omitting --gas-bkg is identical.
python3 internal/study/simulate.py --config internal/config/study/cygno-11x7-v4.json \
  --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/internal-materials-NEW" \
  --mode smoke --primaries 2 --output-mode compact --gas-bkg no

# 25-source campaign with both gas contributions.
python3 internal/study/simulate.py --config internal/config/study/cygno-11x7-v4.json \
  --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/internal-gas-NEW" \
  --mode smoke --primaries 2 --output-mode compact --gas-bkg yes

# Inspect all 25 macros without Geant4; --macros-dir NEW_DIR exports them.
python3 internal/study/simulate.py --gas-bkg yes --list
```

For production use `--mode production --primaries 10000000`, after the existing
four-case environment preflight and transport gates. The cluster wrapper forwards
`--gas-bkg yes` unchanged. `--only Gas_C14 Gas_Rn222` is a partial diagnostic,
not a complete campaign. Repeat an identical command to resume; failed jobs need
`--retry-failed`. Changing gas selection fails before probes or attempts are
written. No automatic merge or reuse across source/build/scenario identities
is allowed. Old campaigns remain readable with their recorded identities;
new source builds cannot resume an old fingerprint, even when gas is disabled.

Python analysis automatically reads the saved matrix for raw/compact/both and
archives. Native ROOT automatically handles complete unpacked compact campaigns.
Use the existing [analysis commands](ANALYSIS.md); there is no analysis gas flag.
Both retain gas provenance and the separate normalization scenario, and include
`Gas C14` and `Gas Rn222` individually in contribution results, categories,
legends, stacked spectra and totals. Native ROOT includes both in all four
selection cutflows and associated full/zoom/overlay figures. Gas rows in the
Table 7.3-style Python table have no historical published reference value.
Systematic contamination uncertainties are recorded, not propagated.

See [gas validation](GAS_VALIDATION.md) for executed checks and the current
macOS Geant4 transport limitation. Failed decay transport must never be used
as a completed prediction.
