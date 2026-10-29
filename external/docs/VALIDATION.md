# External v4 validation

Both modes default to `cygno-copper-cathode-v4`. `detector_v4` compares complete
placement audits and material/mass/count exports between modes on all layouts.
It proves the single copper cathode and unchanged lens transport against the
explicit archived v3 model. `external_*` exercises Cu20 shielding, GPS spectra,
cosine incidence and retained recoil transport. Python and ROOT checks reject
model mismatches and retain read-only historical compatibility.

```bash
ctest --test-dir "$CYGNO_BUILD" --output-on-failure -R 'detector_v4|external_'
python -m unittest discover -s tests -p test_external.py -v
```

The runner checks model in config, probes, receipts, geometry and ROOT headers.
Changing models requires a new directory before any probe is written.
No internal radioactive matrix or source jobs enter external transport.
Results and remaining production gates: [v4 validation](../../docs/TWO_STAGE_VALIDATION.md).
The [historical execution record](../../docs/history/EXTERNAL_VALIDATION-pre-v4.md)
is retained separately; it does not qualify v4 rates.
