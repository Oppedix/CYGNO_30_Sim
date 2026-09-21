# Analysis and normalization

Build the four programs with `-DCYGNO_BUILD_ANALYSIS=ON`. The simulation does not
link ROOT; these executables do. Run the processor separately for each worker
file. Run-local event IDs can repeat across runs: do not concatenate unrelated
runs before grouping.

```sh
/path/to/build/analysis/SimpleProcessEvents input.root processed.root \
  --assume-geometry cygno-5x5x3-v1
/path/to/build/analysis/PlotNormalizedSpectra /absolute/path/to/study.tsv
```

Without an explicit output, the processor creates `elab_<basename>` beside the
input, including when the input has directory components. Raw files have no
geometry version. The explicit assumption must come from the saved source; it
cannot convert old 25 × 3 data. Processed output records `CygnoGeometry`,
`CygnoLayout`, geometry provenance and `ProcessingVersion` markers. A future
layout mismatch is rejected when reading those markers. No raw branches are added.

## Grouping semantics and intentional changes

Only e−, e+ and alpha rows contribute. Within one event, successive rows with the
same creator process/nucleus are accumulated under the inherited group rule.
Ionization-created rows (`ionIoni`, `eIoni`) can join the current group; once they
have done so, the next non-ionization transition closes it. This is a historical
heuristic, not a track-ancestry grouping. The event boundary is now unconditional,
including when its first row is an ignored particle. EOF flushes the last nonempty
group. Empty groups are not emitted. Per-volume energies preserve first-seen
volume ordering and the first position in that volume.

`elabHits` retains `evNumber`, `PartName`, `EDep_Out`, `VolNnum_Out`, `Nucleus`,
`X_Vertex`, `Y_Vertex`, `Z_Vertex`. Energies remain MeV. The nonexistent unused
`VolumeTraslX/Y/Z` bindings are gone. ROOT-managed string leaves replace fixed
20-byte buffers, including for long excited-ion names. Input schema is checked.
**Processed numerical results intentionally change** due to boundary/EOF fixes;
this is separate from the source-position correction in raw simulation output.

## Spectra

`PlotSpectrum.C` exposes `PlotSpectra("processed.root")` in ROOT and creates
`histo_<basename>` beside the input. It fills per-volume beta/alpha histograms.
The three normalized programs retain their original group-energy summation,
first-position fiducial test, 20 mm insets, keV conversion, position histograms
and energy selection. The main normalized program uses 900 bins in 0–2000 keV;
`_single` and `_GEMchain` use 1200. All write `NormalizedHisto.root` in the current
directory. Equal integrals now remain separate in a multimap: every histogram,
including empty ones, survives in both stacks and individual output keys.

The old YZ histogram still retains world Z and its old ±550 mm range. Outer layers
can enter overflow. No axes/cuts were silently redefined.

## Study configuration

Whitespace-separated text, with optional quoted input paths:

```text
# provenance: identify geometry/source revision, assay source, mass basis and generated-event accounting
# component isotope mass_kg activity_Bq_per_kg generated_events input_file
```

Add one row per component/isotope with your study's values. Input paths resolve
relative to the process working directory, so absolute paths are useful. Repeated
component rows must use a consistent mass; duplicates, nonfinite values, negative
activity and nonpositive mass/event counts are errors. Histograms use the unchanged
formula `activity_Bq_per_kg * mass_kg * 60*60*24*365 / generated_events`.
The program requires an explicit configuration argument and provenance record.
This records a researcher's stated basis; software cannot verify the assay.

`config/normalization/*.historical.tsv` faithfully transcribes the original
compiled tables, tested numerically against copies in `legacy/analysis/05a2b92`.
They are marked `historical-unverified` and rejected as production inputs. They
contain unexplained component masses, ambiguous GEMs/Rings labels, generated-event
counts and branching-weight denominators. `_single` includes the inherited
`1e5/0.9862`, `1e5/0.9973`, `1e5/0.0138`, `1e5/0.0027` factors; their scientific
applicability is unresolved. The historical vessel mass 1102.24 kg must not be
carried into the resized shell automatically. No replacement assay or generated
count has been invented. Create a separate study file only after resolving those
inputs. A passing transcription test does not establish their scientific validity.
