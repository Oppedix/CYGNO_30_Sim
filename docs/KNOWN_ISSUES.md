# Known issues and scientific decisions

Software regression success does not establish the scientific correctness of
this detector, source model, normalization or decay data.

## Fixed during recovery

- Source sampling now precedes the same event's vertex creation; event zero no
  longer automatically starts at the origin. Raw fixed-seed results intentionally
  change. The sampling algorithm is retained.
- Isotope commands apply on the next event, including after an earlier run.
- GEM-core/resistor mass totals now use their own logical volumes on both sides;
  `RingSupports` and `Resistors` mass keys match source names.
- Primary summaries use the actual primary, invalid activity estimates are guarded,
  unsupported visible-energy summaries are omitted, and terminal-ion times are
  not relabeled as half-lives.
- Hits booking occurs once per analysis manager; multiple runs reset row data.
  Zero print-progress no longer causes modulo-by-zero.
- Analysis flushes at event boundaries and EOF, removes nonexistent translation
  branches and uses managed string buffers. Processed results intentionally change.
- All equal-integral spectra survive in stacks and individual keys. Study inputs
  are externalized and historical normalization is not loaded automatically.
- Inactive physics/histogram code is quarantined. Generated files are untracked;
  application and analysis build out of source without committed binaries.

Earlier baseline fixes remain: sensitive-detector success return, positive worker
count parsing, worker-local sensitive detector registration and source-list
validation. These were already present in 05a2b92.

## Geometry: unresolved, numerically preserved

| Issue | Evidence | Decision needed |
|---|---|---|
| Cathode/gas overlap | Cathode half-Z is 0.5 mm, while gas offset uses 0.25 mm; 0.25 mm overlap at each face | Choose intended 0.5 or 1 mm total cathode thickness, then derive offsets consistently |
| GEM copper/core | Copper cavity thickness 0.005 mm versus 0.029 mm PMMA core; shifted Boolean cut | Establish physical layer stack, cavity alignment and materials |
| Field cage | Translated supports intersect strips; shifted strips intrude into gas | Establish shell cross sections, alignment and clearances |
| Vessel meaning | One resized common copper shell; optics are partly inside and partly outside | Confirm enclosure/shielding model and assay mass basis |

Definitions are isolated in `common/DetectorGeometry.hh` and named detector
builders. Representative overlap scans report the same inherited categories
before/after; exact geometry/placement snapshots match 05a2b92. No inter-module
envelope intersections, vessel crossings or World protrusions were found. The
inherited module remains **not overlap-free**. Sampled warning counts are not
counts of all distinct physical intersections.

## Sources and decay: unresolved

The surface-point plus inward-depth model is not generally uniform volume and
can leave thin/Boolean solids. Diagnostic containment failures are reported in
[SOURCES.md](SOURCES.md). Decide surface/bulk contamination and component-specific
depth before any rejection/distribution change. The source lists are uniformly
selected by placement, not mass-weighted. Ambiguous historical GEMs/Rings labels
remain unresolved and unsupported.

`Nucleus` follows the last tracked ion, across event boundaries. It is not a
proven ancestry label; define intended attribution before changing it. Ion recoil
stopping, decay-chain handling and the effective long-decay-time threshold are
inherited behavior. Configuration presence alone does not prove useful transport
for every long-lived isotope. Two-worker tests check basic ownership and schema,
not all concurrency schedules. Geant4 11.4 solid-surface RNG state is separate
from `/random/setSeeds`, so use fresh processes for reproducible single-run work.

## Analysis and normalization: unresolved

The within-event process/ionization grouping is a historical heuristic, not track
ancestry. Normalized spectra test only the first grouped position for fiducial
selection; per-volume plots apply the inherited per-volume predicate. No cuts,
energy selections, bin counts or formulas were changed. YZ position histograms
still use world Z and the old visible range; outer layers can overflow.

The original masses, contaminations, branching factors and generated-event tables
have incomplete provenance and remain labeled historical, with exact transcription
tests. Phase 3 separately transcribes the thesis assays and exports constructed
quantities; see [source provenance](STUDY_SOURCES.md). Figure 7.5's exact production
inputs/revision and actual generated counts remain unresolved. The former vessel mass
1102.24 kg cannot automatically describe the current approximately 4203.49 kg
construction (legacy layout approximately 4116.56 kg). New raw worker files carry
separate layout/model/source metadata, checked by processing and all plotters.
Archive matching source and configuration, and explicitly identify both layout
and model for unversioned data before processing; see [analysis](ANALYSIS.md).

## Expected Bi-212 failure

`validation/macros/known_bi212_failure.mac` still aborts with `PART122` registering
Pb208 (excited Pb208[2614.52200] appears in the failing track report). It reproduced
on unchanged 05a2b92 and after the final corrections with Geant4 11.4.2, the same
installed datasets, Apple clang 21, macOS 27 arm64. ROOT 6.40.04 is used only for
analysis. The reproducer is outside the passing CTest suite. No radioactive-decay
behavior or nuclear data were altered to suppress it. The retained standalone
`validation/external_decay_probe.cc` offers a separate investigation starting
point; it is not evidence that the external issue has been resolved.
