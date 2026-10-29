# v4 validation and production gates

Current model: `cygno-copper-cathode-v4`; internal matrix: `cygno-radioassay-v4`
(23 contributions). [Current module](SINGLE_MODULE_GEOMETRY.md) and
[source provenance](STUDY_SOURCES.md) define the scientific contract.

Use a fresh build with testing enabled, matching Geant4 datasets, ROOT and the
Python analysis environment. `ctest --test-dir "$CYGNO_BUILD" --output-on-failure`
runs the available suites. `detector_v4` independently checks 60 µm solid copper,
Acrylic GEMs, all exported masses/counts and complete internal/external detector placement
identity (external enlarges only World to enclose the GPS source sphere) on all layouts. It compares unchanged optics against archived v3.
Python/ROOT synthetic campaign parity checks v4 lens Bq/piece normalization,
per-source scales, spectra, category sums and rejected historical-model relabeling.
Campaign tests reject cross-model resume before transport or probe writes.

Before production, run the four-case internal U238/Th232/Bi212 decay preflight,
then all 23 small smoke jobs on the target installation and offline validation.
External gamma/neutron smoke and production qualification are independent.
PART122 environment failures remain failures. Software parity alone does not
validate physical background rates, detector response or source assumptions.

[Dated pre-v4 validation](history/TWO_STAGE_VALIDATION-pre-v4.md) is historical
reproducibility evidence only. The execution report for this change is
[V4_VALIDATION.md](V4_VALIDATION.md).
