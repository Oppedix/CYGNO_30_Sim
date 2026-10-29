## Equivalence checks

Validation uses the existing canonical `canonical_input`, `accumulate`,
`scale_for`, and `summarize` functions as the oracle, without changing them.
Python is used only for this development comparison, never by the new executable.

The already-generated `compact-refactor-k40-30` Geant4 sample has 30 generated
primaries, 11 stored groups, and 16 group-volume records. It produces 11 accepted
ER groups without a cut and 1 with the cut. Its exact windows are:

```text
                 all  gt10  gt10_le400  underflow  in_range  overflow
no_cut            11    11          10          0        11         0
fiducial_20mm      1     1           1          0         1         0
```

For campaign integration, this small real transport file was reused in a
**clearly labeled synthetic 28-job campaign fixture**, with actual exported
geometry/quantities and the saved matrix activities. This exercises differing
normalization scales and category sums; it is not a physically simulated
28-source campaign. Attempts alternate between `attempt-0002` and
`attempt-0007` to check manifest-based discovery.

Comparisons require exact equality for accepted/processed counts, all six
unbinned windows, every one of the 902 raw bins in both selections, scales,
annual window rates/variances, all category density bins and errors, and totals
summed in reporting order. Additional synthetic checks cover both supported
layouts, every internal histogram edge and adjacent floating-point values,
window endpoints/flows, inclusive fiducial faces and outside positions,
multiple-volume first-position decisions, conversion-before-summation, alpha
exclusion, and empty spectra. These fixtures and generated products are local
development artifacts, not new production dependencies or committed ROOT data.

Malformed-input checks also passed: zero volume counts, wrong volume order,
invalid gas IDs, nonfinite deposits, conflicting primary accounting/layout,
missing required branches, incomplete jobs, existing output directories, and
output inside the campaign are rejected. The worker filename
`compact_t0.root` was exercised successfully. The documented compile command
and PNG/PDF exports were also checked.
