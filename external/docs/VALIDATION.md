# Executed validation and remaining production gates

Local execution: 2026-10-22, macOS/arm64, Apple Clang 21, Geant4 11.3.1 **serial**,
matching installed datasets including G4NDL 4.7.1, Python 3.14.7 analysis environment,
ROOT 6.40.04. These observations do not certify another installation.

## Software checks

| Check | Result |
|---|---|
| Pre-change Python baseline | 56 discovered: 53 passed, 3 optional tests skipped |
| Full post-change Python suite, all optional integrations enabled | **62/62 passed, none skipped** |
| CTest, common Geant4 build | 13/13 passed |
| Actual shield geometry and GPS on all three layouts | Passed; 20,000 sampled primaries/layout |
| Actual moving C12 recoil callback | External retains 1 keV and fAlive; existing internal chain-boundary tests still pass |
| GPS unequal-bin probabilities | Observed 0.25/0.75 probability test passed despite unequal energy widths |
| New external fixture tests | Passed: raw/compact/both, resumed recoil tracks, empty primaries, bin/window edges, typed metadata, track relationships, flux conventions, source config validation, immutable failed attempts/retry/reuse |
| Standalone external ROOT vs Python | Passed for all three layouts, including both mode; exact integer bins and counters, rates within floating-point roundoff |
| Cluster wrappers | Shell syntax and dry-run macro generation passed; external runner also runs with `python3 -S` |
| Internal notebooks | All three re-executed with the existing helper; saved outputs/source fingerprints refreshed |

The first default run discovered 62 tests and passed 59, skipping three optional
integrations. A separate fresh Geant4+ROOT reference build then enabled
`CYGNO_REFERENCE_BUILD` and `CYGNO_TRANSPORT_BUILD`: the final run executed and
passed all 62, including the three-layout 30-primary same-transport check,
constructed 11×7 campaign/notebook test and historical C++ reference parity.
The standalone internal topology and external ROOT comparisons also ran.

The common geometry tests check real constructed bounds, source/mass maps and
layout profiles, retained source sampling and existing transport. New tests check
four actual G4_Cu shells, all six faces at 50 mm per layer, adjacency/no added
shield overlaps, every detector/optical solid inside the cavity, and the sphere
outside shield corners. Existing field-cage intersections are not claimed fixed.
GPS checks radius, inward directions, mean cosθ≈2/3, mean cos²θ≈1/2, isotropic
surface-position means and energy-bin probabilities. These are software/statistical
sampling checks, not validation of environmental angular isotropy.

## Internal invariance check

A fresh build of baseline `d612785` was run before source changes, then compared
against the final common build. Both used the same 100-primary macro:

```text
/run/verbose 0
/event/verbose 0
/tracking/verbose 0
/random/setSeeds 12345 67890
/output/OutFile regression
/detector/RadElement GEMsPolyimide
/isotope/AtomicNumber 19
/isotope/MassNumber 40
/process/had/rdm/thresholdForVeryLongDecayTime 1.0e+60 year
/run/beamOn 100
```

Invocation: `rdecay01 run.mac 1 --layout cygno-11x7-v1 --output-mode both`.
Every field of every TTree is identical, including 10,471 raw rows, 49 Groups,
77 GroupVolumes, 1,051 Tracks, 989 TrackGroups, RunMetadata, OutputMetadata and
RunAccounting. This is equality of scientific payloads, not ROOT file bytes or
elapsed/log timing. The common detector geometry hash is unchanged.
It is a controlled K40 regression, not a proof for every isotope/seed.

## Real environmental transport diagnostics

Same provided source configs/seeds and 11×7 layout:

| Source / shield / representation | Requested=generated=processed | Result |
|---|---:|---|
| Gamma / none / compact | 2,000 | Complete; 11 primary events with positive total gas deposit |
| Neutron / none / both | 2,000 | Complete; 23 positive total events; raw/compact parity passed |
| Gamma / Cu20 / both | 1,000 | Complete; zero positive total events; empty raw/compact parity passed |
| Neutron / Cu20 / both, then compact reproduction | 1,000 requested | **Failed** locally with PART122 during RDM of a Cu capture product to Zn66 |

The unshielded neutron sample retains positive-deposit F19, C12, alpha, electron
and gamma tracks. It has 799 Groups/Tracks and 3,144 GroupVolumes; the primary
normalization denominator remains **2,000**, not any of those row counts.
Both languages agree on all per-bin primary counts in the successful real
samples and on normalized rates to roundoff. ROOT PNG/PDF export was executed
and the figures visually inspected. A display-only stat-box overlap was repaired.

Diagnostic products were kept outside the checkout under
`$HEP/validation-runs/external-*`; the final campaign pair is
`external-final-gamma-none`, `external-final-neutron-none`; the final Cu pair is
`external-final-gamma-cu20`, `external-final-neutron-cu20`.
Earlier `external-gamma-copper20-both` and the failed
`external-neutron-copper20-both` retain the first shield diagnostics. No ROOT
binary/test product is committed. No rate from a failed attempt is reported.

Removing a redundant RDM registration already supplied by the HP physics list
removed duplicate-process warnings; **it did not fix PART122**. The final
one-registration reproduction still fails on Zn66[1039.228] in ExternalCu2.
No exception suppression, ion-table patch, dataset edit, recoil killing or
artificial decay removal is used. The unshielded neutron success does not
qualify shielded capture/activation transport on this machine.

## Reproduce the software checks

```bash
cmake -S "$CYGNO_SRC" -B "$CYGNO_BUILD" -DWITH_GEANT4_UIVIS=OFF \
  -DBUILD_TESTING=ON -DGeant4_DIR=/path/to/geant4/lib/cmake/Geant4 \
  -DPython3_EXECUTABLE=/path/to/analysis-env/bin/python
cmake --build "$CYGNO_BUILD" --parallel
ctest --test-dir "$CYGNO_BUILD" --output-on-failure
cd "$CYGNO_SRC"
CYGNO_REFERENCE_BUILD=/path/to/fresh-Geant4-ROOT-reference-build \
CYGNO_TRANSPORT_BUILD="$CYGNO_BUILD" \
/path/to/analysis-env/bin/python -m unittest discover -s tests -v
```

For just external fixtures: `python -m unittest discover -s tests -p test_external.py -v`.
ROOT is optional for Python-only checks; native integration is explicitly skipped
without `root-config`. Simulation tests never launch large production.
The local build required explicit Homebrew zlib paths because its Geant4 install
expects zlib 1.3.2 while the SDK advertises 1.2.12; this is environment setup, not
a project physics/code change.

## Still open before scientific production

1. Confirm installation hall and location. Hall C sources do not qualify Hall F.
2. Obtain a response-corrected continuum at that site. The gamma shape proxy is
   not the 2026 spectrum, and the neutron broad-bin approximation is especially
   weak for moderation/capture. Confirm the neutron tally's scalar/current
   convention; the provisional choice permits a factor-four difference.
3. Qualify neutron Cu capture, secondary cascades and ion recoil transport on the
   actual Linux cluster. The existing internal decay preflight is insufficient.
4. Review production cuts, thermal treatment, missing-isotope HP fallbacks and
   delayed activity; validate quenching/readout before claiming observable NR/ER rates.
5. Validate the retained mechanical detector assumptions, real shield penetrations
   and source anisotropy. Obtain sufficient statistics/uncertainty treatment;
   zero deposits in 1,000 gamma primaries is not a shielding performance limit.

No Linux cluster job, scheduler submission, full internal matrix production or
large external production was executed in this session. Use the documented
cluster wrappers only after the corresponding environment/scientific gates pass.
