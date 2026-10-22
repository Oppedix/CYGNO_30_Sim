# LNGS sources, shielding and open physical assumptions

References inspected on 2026-10-22. Provided configurations are reproducible
**scenarios**, not a newly measured background model. Flux, its angular convention,
energy support and spectral shape are separate inputs; each must be justified.

## Hall and gamma reference

For a **Hall C CYGNO-30 feasibility study**, the recent Hall C measurement is the
appropriate integral reference: [Luzzi et al., PRD 114 (2026), DOI rm39-mmyk](https://doi.org/10.1103/rm39-mmyk),
[full manuscript v3](https://arxiv.org/html/2605.09835v3). It reports
0.46 ± 0.06 ± 0.03 cm⁻²s⁻¹ in 57–2800 keV. Section V.B uses uniform surface
positions and inward cosine directions; Eq. 8 divides by the full source sphere
area. Therefore use `inward_current`, with **no additional factor 1/4**.
The hall has spatial/radon-dependent variations; this is not a site-independent constant.

The [collaboration's preliminary CYGNO-30 Hall C concept](https://agenda.infn.it/event/41250/contributions/230475/attachments/118947/172261/Baracchini_CYGNO_LNGS_SC_April_2024_closed.pdf)
provides a rationale for a Hall C scenario. It does **not** confirm the installation
point of this simulated 11×7 detector. CYGNO-04 Hall F plans must not be confused
with the CYGNO-30 concept. No authoritative hall/position is encoded in the
current repository; a confirmed installation point and local spectrum remain a
production gate. If the intended site is Hall F, neither Hall C integral is a
validated Hall F normalization.

[Malczewski, Kisiel and Dorda, published July 2012 / issue 2013](https://doi.org/10.1007/s10967-012-1990-9)
reports multiple LNGS locations and a laboratory mean near 0.25 cm⁻²s⁻¹, over a
different energy band and with a different efficiency treatment. It is not a
replacement Hall C spectrum. The recent paper explains these method differences.
The old approximate 0.56 value is retained only as historical context, never
silently converted into the new integral or treated as a normalized probability.

`hall-c-gamma-2026-proxy.json` combines the recent **integral** with the numerical
shape in CYGNO-MC `CYGNOtest_surface_gamma.mac`, cropped to [0.057,2.8] MeV.
This is an explicit **shape proxy**, not the 2026 unfolded spectrum. No tabulated
2026 full continuum was supplied by the sources inspected. Obtain it from the
measurement authors, with its response/unfolding and position convention, before
claiming a 2026-spectrum prediction. Published line fluxes alone cannot reconstruct
that continuum. Flux uncertainties are provenance, not propagated by the report.

## Neutrons

[Wulandari et al. (2004)](https://doi.org/10.1016/j.astropartphys.2004.07.005),
[full paper](https://arxiv.org/pdf/hep-ex/0312050), Table 8 gives Hall C dry
radiogenic bin integrals 0.24, 0.93, 0.91, 0.15, 0.03 in units 10⁻⁶ n/cm²/s,
with boundaries 0, 5×10⁻⁸, 10⁻³, 2.5, 5, 10 MeV. Their sum is 2.26×10⁻⁶.
These are **integrated bins**, not differential heights. The example uses their
relative integrals and assumes constant density inside each broad bin. This
poorly resolves thermal/epithermal/fast shapes, which matter for Cu capture.
The calculation includes hall scattering and humidity dependence; it is not a
measured Hall F spectrum or a cosmic-muon neutron model.

The tally's scalar-versus-surface-current convention is not established by the
paper text inspected. The example **provisionally assumes scalar flux**, giving
an inward current Φ/4. Treat a factor-four convention check as open; change the
explicit `flux_convention` in a separately named configuration only with evidence.
The old CYGNO-MC neutron macro extends to 2 GeV with ambiguous differential
weights and a FIXME on normalization. It is inspected and recorded as historical
provenance, but is not relabeled as the Wulandari radiogenic distribution.
Muon-induced neutrons and any independently measured fast tail require a
separate source configuration, not an extra normalization on these same bins.

## Collaboration code and CAD inspected

- [CYGNO-MC at 3a7f8c088b90503a84af9d70febf1de1ee1471c2](https://github.com/CYGNUS-RD/CYGNO-MC/tree/3a7f8c088b90503a84af9d70febf1de1ee1471c2):
  `CYGNODetectorConstruction.cc` constructs four nested material boxes with an
  inner air cavity, GPS generates primaries, `CYGNODetectorLNGS.cc` describes a
  historical Hall B/rock model without concrete by default. The constructor
  explicitly warns that laboratory translations are WIP and advises NoCave.
  No cave model is imported or certified here.
- Both `CYGNOtest_surface_*.mac` files use GPS `User` energy histograms, surface
  spheres, global `iso` directions and a normalization FIXME. The new source uses
  local inward **cosine** incidence, not these historical angular settings.
- `CYGNO_surface_gamma_50Water5Cu_inputdist50Water.mac` reads
  `input_distribution/E_after_50cmWater_MeV.txt`, already downstream of 50 cm
  water, and also has a derived angular distribution. It is deliberately excluded
  from an unattenuated environmental source transported through Cu. Using it
  here would conflate source boundaries and risk double-counting attenuation.
- `config_lngs.py` / `submit_jobs_lngs.py` are Python-2/PBS-era workflows with
  hard-coded software/storage paths and destructive scratch cleanup. Their
  isolation/seed/log ideas are retained through the existing modern runtime;
  those scripts are not copied into production.
- [geometry at dbf18a370568b5e12d8562950c4a4276d819e949](https://github.com/CYGNUS-RD/geometry/tree/dbf18a370568b5e12d8562950c4a4276d819e949):
  inspected all shield STL meshes in `cygno_04_v2` and `cygno_04_v3`. v2 has the
  combined `shield_Cu` and split `shield0..3_Cu`, a camera shield, PE and water;
  v3 has `InnerShieldCu`/`OuterShieldCu`. Their mesh bounds and facet counts were
  checked, not just filenames. They are translated, detector-specific mechanical
  assemblies, not four universal 5-cm shells. None is substituted for our detector.

Numerical historical spectrum points, upstream revision, file paths and SHA256
are saved in `external/config/historical-gps-spectra.json`. Conversion of the
historical gamma heights treats the `User` points as upper-edge bins with
constant density and integrates the clipped widths before normalization. This
interpretation is explicit because the upstream weights are not certified fluxes.

## Neutron transport and detector response

Internal keeps `QGSP_BIC_EMZ` and its inherited Z>2 recoil-stopping/decay policy.
That policy cannot describe fluorine/carbon recoil transport. External uses
`QGSP_BIC_HP_EMZ`, including HP elastic/inelastic/capture/fission below its
high-precision range, with matching G4NDL; RDM is present once. The external
tracking callback does not stop heavy ions. All gas deposits and species are
preserved in raw and compact, including neutral local deposits from model cuts.

Geant4 11 reference-list behavior and datasets must be requalified on each target
environment. HP isotope-file fallback messages (observed for Ar in air) remain
visible in logs; they are not replaced by an invented local cross section.
This implementation does not validate thermal bound-atom scattering, recoil
production thresholds, gas ionization/scintillation yields, quenching, capture
cascades, delayed activation, optical efficiency or NR discrimination. It reports
**deposited energy**, never keVee or a calibrated observed nuclear-recoil rate.

The 20 cm copper enclosure is a requested ideal closed shield, not a mechanical
engineering design, a neutron moderator, or a guaranteed background reduction.
It has no penetrations/supports/seams and adds no radioactive Cu assay. The
existing 5 mm vessel remains a separate common detector component with its known
closed-wall/optics assumptions. See [shared shielding geometry](../../docs/EXTERNAL_SHIELDING.md).
