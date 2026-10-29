# Current v4 software validation

Use a new build directory with matching Geant4 datasets, ROOT/PyROOT and the
Python analysis environment. Existing simulation output directories are never
used as test output. CTest writes only beneath the selected fresh build.

```bash
cmake -S . -B "$CYGNO_BUILD" -DWITH_GEANT4_UIVIS=OFF \
  -DCYGNO_BUILD_ANALYSIS=ON -DCYGNO_TEST_PYTHON_ANALYSIS=ON \
  -DCYGNO_TEST_COMPACT_TRANSPORT=ON -DPython3_EXECUTABLE="$(command -v python)"
cmake --build "$CYGNO_BUILD" --parallel
ctest --test-dir "$CYGNO_BUILD" --output-on-failure
```

| Checks | Coverage |
|---|---|
| detector_v4 | Exact physical-lens conversion, 23 rows, current defaults, old-model resume rejection before writes; all layouts' constructed masses/materials/counts and identical detector placements between modes; unchanged non-cathode geometry against archived v3 |
| acrylic_geometry | Historical reconstruction plus current CLI/export defaults in both modes |
| source_and_mass, uniform_volume | Nine v4 source families, all mass totals, uniform bulk sampling, containment and deterministic same-event RNG replay |
| external_* | Current detector, Cu20 shield bounds/overlaps, GPS spectrum/cosine sampling and ion recoil retention, plus historical compatibility |
| geometry, layout_geometry, layout_profiles | 137 placements/module, copper cathode interfaces/no overlap, GEMs, source lists, gas maps, bounds, all layouts and smoke transport |
| transport, compact_transport | Raw/compact/both parity, multiple runs, accounting, reset/EOF boundaries and metadata |
| offline_python | Full Python suite, v4 standalone ROOT parity, schemas, campaigns, archives, reports, notebook execution and historical compatibility |
| source_matrix | Retained assay regression plus all native reference plotters' v4 lens Bq/piece scales against Python with 308 actual placements; bad units/double reference mass rejected |
| analysis, layout_analysis, root_geometry, study_runner | Reference ROOT grouping, exact windows, material/unit guards, metadata, layout and historical-runner compatibility |
| long_lived_decay, chain_boundaries | Real U238 threshold behavior and retained chain-stop callback controls |

Set `CYGNO_ACRYLIC_BUILD`, `CYGNO_TRANSPORT_BUILD` and `CYGNO_REFERENCE_BUILD`
to the fresh build when running optional tests outside their CTest wrappers.
`geometry_audit` accepts `--layout`, `--model`, `--mode` and optional `overlaps`.
The external World expands to enclose the GPS sphere; detector placements are
identical. Source/geometry/model hashes and matrix pairing prevent relabeling.

The full four-case internal production preflight is a separate environment gate;
PART122 is a failure, never a waiver. See [v4 execution results](../docs/V4_VALIDATION.md)
and [production gates](../docs/TWO_STAGE_VALIDATION.md). Historical evidence is
isolated in [the archived validation record](../docs/history/VALIDATION-pre-v4.md).
