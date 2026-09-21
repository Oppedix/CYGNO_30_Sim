# Analysis and normalization

Build the four programs with `-DCYGNO_BUILD_ANALYSIS=ON`. The simulation does not
link ROOT; these executables do. Run the processor separately for each worker
file. Run-local event IDs can repeat across runs: do not concatenate unrelated
runs before grouping.

```sh
/path/to/build/analysis/SimpleProcessEvents input.root processed.root
/path/to/build/analysis/PlotNormalizedSpectra /absolute/path/to/study.tsv
```

Without an explicit output, the processor creates `elab_<basename>` beside the
input, including when the input has directory components. New raw worker files
have a separate one-row `RunMetadata` tree with `GeometryHash`, `Layout`,
`DetectorModel` and `SourcePolicy` string leaves. Both `legacy-25x3` and
`cygno-5x5x3-v1` are supported with `code-compatible` and `historical`. The future
`thesis-7.3` model is not yet implemented and is rejected.

Processed output records `CygnoGeometry`, `CygnoLayout`, `CygnoDetectorModel`,
`CygnoSourcePolicy`, `GeometryProvenance` and `ProcessingVersion`, and copies the
raw metadata when present. Every available record must agree; malformed or
partial metadata and conflicting assumptions are rejected before output creation.
Geometry identity does not establish successful production or generated counts.

For an **unversioned** file, first verify the source revision, internals and source
policy, then explicitly identify both axes:

```sh
/path/to/build/analysis/SimpleProcessEvents old.root processed.root \
  --assume-layout legacy-25x3 --assume-model code-compatible
```

The assumption records `historical` source policy; it is not suitable for data
from a different sampler. `--assume-geometry` remains an alias of `--assume-layout`.
For already versioned data, either assumption acts as an additional consistency
check and cannot override the file. Neither option transforms coordinates or
converts another detector model. Older public code revisions must be checked
against the code-compatible model before using this path.

Backward compatibility is intentionally narrow. Pre-Phase-2 processed files with
both `CygnoGeometry` and `CygnoLayout=cygno-5x5x3-v1` are accepted for the current
header fingerprint or the verified `74cc26f` header fingerprint
`d0e9f189266be3f0a608bba332b4fe5e5f17d9c7c2c6ef4bd95f53408f73c039`.
That older hash is never accepted for `legacy-25x3`. Their code-compatible model
and historical policy are recorded with explicit compatibility provenance. A
hash-only raw metadata record cannot identify a runtime layout and is rejected.
Unknown hashes cannot be bypassed by assumptions. The header fingerprint remains
a conservative source/configuration guard, not a hash of all simulation physics.

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

For interpreted ROOT, make the matching build header visible before loading:

```cpp
gInterpreter->AddIncludePath("/absolute/path/to/build/generated");
.L /absolute/path/to/repository/analysis/PlotSpectrum.C
PlotSpectra("processed.root");
```

`PlotSpectrum.C` exposes `PlotSpectra("processed.root")` in ROOT and creates
`histo_<basename>` beside the input. It fills per-volume beta/alpha histograms.
It validates file identity; optional second and third arguments require a specific
layout and detector model. The output carries the checked identity.
The three normalized programs retain their original group-energy summation,
first-position fiducial test, 20 mm insets, keV conversion, position histograms
and energy selection. The main normalized program uses 900 bins in 0–2000 keV;
`_single` and `_GEMchain` use 1200. All write `NormalizedHisto.root` in the current
directory. Equal integrals now remain separate in a multimap: every histogram,
including empty ones, survives in both stacks and individual output keys.
Additional `Categories/` histograms and stacks sum contributions after individual
normalization. `NormalizationConfiguration` preserves the full configuration text,
and `NormalizationConvention` records the scale and counts/bin/year convention.
No division by bin width is performed.

The old YZ histogram still retains world Z and its old ±550 mm range. Outer layers
can enter overflow. No axes/cuts were silently redefined.

## Study configuration

Phase 3 adds explicit quantities/units and category grouping. Use this format for
new source-matrix studies (the format header must precede all data rows):

```text
# normalization-format: quantity-v2
# layout: legacy-25x3
# detector-model: code-compatible
# source-policy: historical
# provenance: Table 7.1 plus matching geometry_quantities export and validated generated-primary counts
# component isotope quantity quantity_unit activity activity_unit generated_events category input_file
```

Each data row has nine whitespace-separated fields. Quote categories and paths
containing spaces. `kg` pairs with `Bq/kg`; `piece` pairs with `Bq/piece`. Piece
counts and generated-primary counts must be positive integers; quantities must
be finite/positive and activities finite/nonnegative. Repeated components must
have the same quantity, units and category. Unrecognized or mismatched units,
duplicates and nonfinite scales fail before creating output. There is no implicit
micro-/milli-Bq conversion: the matrix already supplies Bq values.

Use the 26 contributions in `config/study/thesis-table7.1.json` and the actual
constructed mass/piece export; see [source provenance](STUDY_SOURCES.md). The
assay matrix has no layout or detector-model default and launches no simulations.
The forthcoming runner must attach actual completed generated-primary counts.

The existing six-column mass-only format remains supported when the format header
is absent, with its original meaning (kg and Bq/kg) and category equal to component:

```text
# layout: legacy-25x3
# detector-model: code-compatible
# source-policy: historical
# provenance: identify source revision, assay source, mass basis and generated-event accounting
# component isotope mass_kg activity_Bq_per_kg generated_events input_file
```

The three identity headers are mandatory. All input files are checked before any
output file is opened: mixing layouts/models/policies, missing metadata and a
conflicting configuration fail without replacing an existing spectrum. The output
records the configured identity and provenance. This does not verify stated masses
or assay values; those must still come from the selected constructed detector.

Add one row per component/isotope with your study's values. Input paths resolve
relative to the process working directory, so absolute paths are useful. Repeated
component rows must use a consistent mass; duplicates, nonfinite values, negative
activity and nonpositive mass/event counts are errors. Histograms use the unchanged
formula `activity * quantity * 60*60*24*365 / generated_events`, where the legacy
six-column format always means Bq/kg and kg.
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
