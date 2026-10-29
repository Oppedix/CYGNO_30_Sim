# Historical detector reproducibility

The single current model is [v4](../SINGLE_MODULE_GEOMETRY.md).
Explicit `cygno-acrylic-v3` and `cygno-300elj-v2` selection is retained only to
reconstruct archived campaigns with their original matching matrix and source
snapshot. Historical matrix/config files are immutable. Source snapshots and
old binaries are needed when compiled geometry hashes differ. No old result is
converted, relabeled or resumed as v4.

The preserved pre-v4 [geometry](SINGLE_MODULE_GEOMETRY-pre-v4.md),
[assays](STUDY_SOURCES-pre-v4.md), [analysis reference](ANALYSIS-pre-v4.md) and
[validation](TWO_STAGE_VALIDATION-pre-v4.md) describe superseded models, never
alternative current configurations. Historical smoke configs live in
`config/study/historical/`; versioned v1/v2/v3 JSON paths remain stable for callers.
