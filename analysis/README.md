> This is the authoritative **internal** analysis area, also exposed at
> `internal/analysis`. Its `raw`, `compact`, `common`, `common_c++`, notebooks and
> `reference_cpp` retain their internal scientific contracts. External has a
> [separate analysis pipeline](../external/README.md), reusing only explicit
> low-level schemas/models/validation. Do not use activity normalization on
> external files.

# Canonical analysis

Current internal v4 uses `cygno-copper-cathode-v4` and the matching
23-contribution `cygno-radioassay-v4` matrix by default, or the optional
25-contribution `cygno-radioassay-v4-gas-v1` with distinct C14/Rn222 gas categories
in every aggregate and plot. See [gas provenance](../docs/GAS_BACKGROUNDS.md). Both pipelines preserve the matrix
and record `normalization-scenario.json`. Lens activities are Bq/piece from
`CYGNO_radioactivity_excel_suprasil`; use the actual lens count, never surrogate
mass or another factor of 3.843 kg. New v4 transport is required for every job.
See [source provenance](../docs/STUDY_SOURCES.md) and
[workflow commands](../internal/README.md).

`study/analyze.py` orchestrates campaign validation and publishing. All numerical
analysis is here. No CERN ROOT or Geant4 installation is needed for Stage B.

```text
                    ┌─ raw Hits ─── raw.preprocess ──────┐
Geant4 StepRecord ───┤                                   │
                    └─ compact trees ─ compact reader ──┤
                                                        ▼
                                                canonical Group
                                                        │
                                   common.spectra / normalization / reporting
                                                        │
                                               spectra / tables / figures
```

- `raw/io.py` validates raw schemas; `raw/preprocess.py` is the only Python
  historical grouping algorithm. Chunk boundaries are irrelevant.
- `compact/io.py` validates typed trees; `compact/preprocess.py` checks keys and
  relationships and reconstructs existing groups, without regrouping steps.
- `common/model.py` defines `Group`, `GroupVolume`, and diagnostic `TrackRecord`.
  Ordered volume dictionaries retain encounter order. Times may be `None` only
  for legacy raw data. `ionization_seen` is internal raw state, excluded from
  canonical equality. Both paths preserve track membership and admitted step counts.
- `common/inputs.py` dispatches by validated metadata. `both` first executes
  exact parity, then supplies the canonical compact stream to shared analysis.
- `common/spectra.py` owns energy construction, first-position fiducialization,
  exact windows, ROOT-compatible 900-bin edges, aggregation and variances.
- `common/normalization.py` preserves per-contribution multiplication order.
- `common/reporting.py` owns tables, reference transcription and figures.
- `reference_cpp/` remains the active optional ROOT reference, including all three
  normalized plotters and the per-volume macro. These are not legacy files.

The three walkthroughs import these functions, show their source, and include
sanity/parity cells. They default to small **synthetic** examples and can read
validated real inputs. The common notebook is independent of storage format.
Run every code cell without a notebook framework:

```sh
python -m unittest discover -s tests -p test_notebooks.py -v
```

Storage contracts and timing are documented in [OUTPUT](../docs/OUTPUT.md).
Timing is diagnostic/future-use only. No canonical function selects on it.

Saved notebook outputs include production-code hashes. The execution test rejects
stale hashes after any implementation change; refresh all outputs deliberately:

```sh
python validation/execute_notebooks.py --output analysis
```

This lightweight helper runs plain Python cells and embeds the common figures.
It does not require or add a notebook execution framework. Normal Jupyter
execution is also supported. Saved examples are labeled synthetic throughout.
