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
tests. The source matrix separately transcribes the thesis assays and exports constructed
quantities; see [source provenance](STUDY_SOURCES.md). Figure 7.5's exact production
inputs/revision and actual generated counts remain unresolved. The former vessel mass
1102.24 kg cannot automatically describe the current approximately 4203.49 kg
construction (legacy layout approximately 4116.56 kg). New raw worker files carry
separate layout/model/source metadata, checked by processing and all plotters.
Archive matching source and configuration, and explicitly identify both layout
and model for unversioned data before processing; see [analysis](ANALYSIS.md).

## Environment-specific PART122 results (updated 2026-09-23)

The operator reports **4/4 passing preflight cases** on Ubuntu 22.04.5 LTS,
x86_64, GCC 11.4.0, private Geant4 11.3.1 with
`GEANT4_BUILD_MULTITHREADED=OFF`, installed at
`/private/SolarNu/MC30/geant4-private/software/geant4-11.3.1-serial`.
Matching nuclear datasets include PhotonEvaporation6.1, RadioactiveDecay6.1.2,
and G4ENSDFSTATE3.0. U238-enabled transports Th234; PART122 is absent in all four.
This external Linux result was supplied by the operator, not rerun from this Mac.

PART122 was independently reproduced on macOS Apple Silicon in CYGNO, a
geometry-free reproducer, stock Geant4 11.3.1 rdecay01, and a truly non-MT stock
11.3.1 build. It is not attributed to the CYGNO refactor. The present local
headless serial 11.3.1 check again passed the two U238 cases and failed Th232/Bi212.
No particle-table patch, exception suppression, excited-state removal or chain
alteration has been applied. Linux is the validated execution environment for
now; this is empirical environment validation, **not proof of a universal fix**.

The following earlier macOS 11.4.2 evidence is retained with its original scope.

## Historical macOS Geant4 11.4.2 decay-environment blocker


`validation/macros/known_bi212_failure.mac` still aborts with `PART122` registering
Pb208 (excited Pb208[2614.52200] appears in the failing track report). It reproduced
on unchanged 05a2b92 and after the final corrections with Geant4 11.4.2, the same
installed datasets, Apple clang 21, macOS 27 arm64. ROOT 6.40.04 is used only for
analysis. The reproducer is outside the passing CTest suite. No radioactive-decay
behavior or nuclear data were altered to suppress it. The retained standalone
`validation/external_decay_probe.cc` offers a separate investigation starting
point; it is not evidence that the external issue has been resolved.


Finalization preflight with explicit `1e60 year` threshold confirms that U-238
produces transported Th-234 daughters (two primaries, two ground-state daughters),
where the one-year default produces only primary tracks. Thus the suppression is
resolved by run configuration, independently of the retained detector geometry.

Forty-primary full-chain Th-232 preflight aborts at event 0 registering
`Th228[57.77300]`, during a `Th228[968.98400]` RadioactiveDecay track. Direct Bi-212
also aborts with PART122. The standalone vacuum-world reproducer (no CYGNO geometry,
sampler or ROOT code) aborts registering Tl208. Different reachable ion collisions
show that the failure is not restricted to the originally observed Pb208 track.
The minimal retained reproducer is `validation/external_decay_probe.cc`:

```sh
cmake --build "$BUILD" --target external_decay_probe
mkdir -p "$RUNS/external-probe"
(cd "$RUNS/external-probe" && "$BUILD/validation/external_decay_probe" > simulation.log 2>&1)
```

In the installed Geant4 source, `G4ParticleTable::Insert` raises PART122 when a
particle name is already registered. `G4IonTable` formats excited energies to five
decimal places in keV. This identifies the duplicate-registration failure point;
it does not by itself establish whether state matching, threading or datasets are
the underlying cause. No Geant4 or dataset patch was applied. A public-source
search did not establish a verified fix/version for this exact failure. At that earlier handoff only 11.4.2 had been tested; see the updated environment result above.

The observed matched nuclear data include RadioactiveDecay6.1.2,
PhotonEvaporation6.1.2 and ENSDFSTATE3.0 (all datasets are fingerprinted in campaign
manifests). See [preflight requirements](BACKGROUND_STUDY.md). A complete published
figure/table reproduction requires a separately validated compatible environment.
Affected production contributions are incomplete, excluded from normalization,
and listed as failures. Partial figure/table artifacts remain useful only as
software diagnostics. The complete 26-job smoke can reveal further affected chains;
any abort is a failed contribution, regardless of isotope.

Even with compatible transport, exact published-rate agreement is not established:
code-compatible dimensions differ from thesis descriptions, historical sampling is
not uniform bulk, internal overlaps persist, and grouping/fiducialization are
historical heuristics. Source provenance and actual thesis production revision are
not fully recovered. Published values must never be used to tune calculated rates.


The completed 26-job two-primary smoke broadened the observed failure scope:
only the five K-40 contributions pass. Nineteen attempts abort with PART122,
including U-238, U-235 and Ra-226 contributions; two tiny Th-232 attempts finish
but remain excluded because the independent full-chain preflight fails. Duplicate
ions include Pa234[73.92000X], Po214[609.31700], Ra224, Th228[57.77300], Th231,
Tl208 and U234. Retry reproduces the same incomplete 5/26 coverage. Thus this
11.4.2 environment is not qualified for complete U/Th-chain production either.
[Final evidence](study-results/finalization.json) preserves per-job outcomes.
