# CYGNO internal-radioactivity background study

Two stages reproduce the **workflow and analysis infrastructure** of Samuele
Torelli's study: Geant4 generates raw ROOT files; Python analyzes them offline.
The canonical identity remains **legacy-25x3 / code-compatible / historical**,
with exactly the 26 contributions in [Table 7.1](config/study/thesis-table7.1.json).
Physics remains `QGSP_BIC_EMZ + G4RadioactiveDecayPhysics`.

The privately installed **Linux x86_64 Geant4 11.3.1 serial environment** has passed
the four-case decay preflight (operator-reported). PART122 remains reproducible in
the tested macOS/arm64 environments, including stock Geant4 examples and a serial
build. This is empirical environment validation, **not a universal Geant4 fix**.
See [environment evidence and limitations](docs/KNOWN_ISSUES.md).

## Cluster: build and simulate

Requirements: CMake ≥3.16, C++17 compiler, Geant4 11 and matching datasets, Python
≥3.10 standard library. **No CERN ROOT, PyROOT, Qt, OpenGL, or analysis packages are
required.** Geant4 itself writes ROOT format. Start from the private environment:

```sh
bash --noprofile --norc
export G4LAB="/private/SolarNu/MC30/geant4-private"
source "$G4LAB/activate.sh"
export CYGNO_SRC="$G4LAB/projects/CYGNO_30_Sim"
export CYGNO_BUILD="$G4LAB/build/cygno-g4-11.3.1-linux"
export CYGNO_RUNS="$G4LAB/runs/g4-11.3.1-linux"
cd "$CYGNO_SRC"

cmake -S . -B "$CYGNO_BUILD" \
  -DCMAKE_BUILD_TYPE=Release -DWITH_GEANT4_UIVIS=OFF \
  -DCYGNO_BUILD_ANALYSIS=OFF -DBUILD_TESTING=OFF \
  -DGeant4_DIR="$G4LAB/software/geant4-11.3.1-serial/lib/cmake/Geant4"
cmake --build "$CYGNO_BUILD" --target rdecay01 geometry_quantities --parallel

python3 study/preflight.py --build "$CYGNO_BUILD" \
  --output "$CYGNO_RUNS/preflight-NEW"
python3 study/simulate.py --build "$CYGNO_BUILD" \
  --output "$CYGNO_RUNS/smoke" --mode smoke --primaries 2
```

The exporter `geometry_quantities` uses actual constructed component masses,
placement counts and the common gas layout; it is available with tests disabled.
Both executables are ROOT-free. Each campaign also retains its own four-case
preflight and refuses simulation if any case fails, independent of statistics.

After the Linux smoke/archive/offline/parity gates, the first statistics check is:

```sh
python3 study/simulate.py --build "$CYGNO_BUILD" \
  --output "$CYGNO_RUNS/samuele-1M" --primaries 1000000 --archive
```

`--primaries N` is the normal event-count control. The canonical default in
[samuele.json](config/study/samuele.json) remains **10,000,000 per contribution**;
1,000,000 is an explicit override, not a redefinition of production. Every job
keeps the explicit `1.0e+60 year` radioactive-decay threshold and full-chain/split
boundary commands from the authoritative matrix.

Repeat an identical command to resume (`--resume` is optional). Complete jobs are
verified and reused. Interrupted jobs get new attempts; `--retry-failed` retries
failed jobs. Valid previous attempts are never overwritten. `--only Lens_K40
Sensors_K40` selects diagnostics; coverage remains partial and exits 2. Config,
source, build or dataset changes require a **new campaign directory**.

## Archive and offline analysis

`--archive` creates `samuele-1M.tar.gz` and `samuele-1M.tar.gz.sha256`, retaining the
unpacked campaign. Complete archives contain raw files, manifests, exact macros,
logs/receipts, preflight, config/matrix/geometry/quantity snapshots, the actual
source snapshot (including dirty edits), and `SHA256SUMS.json`. Partial campaigns
cannot be packaged as complete. To package separately:

```sh
python3 -m study.archive --input "$CYGNO_RUNS/samuele-1M"
```

Copy the archive and checksum to the workstation. Analysis needs Python ≥3.10,
uproot, awkward, numpy and matplotlib, **not CERN ROOT or Geant4**:

```sh
python3 -m venv .venv-analysis
. .venv-analysis/bin/activate
python -m pip install -r study/requirements-analysis.txt
python study/analyze.py --input /path/to/samuele-1M.tar.gz \
  --output /path/to/analysis-samuele-1M
# An unpacked campaign is also accepted:
python study/analyze.py --input /path/to/samuele-1M \
  --output /path/to/analysis-samuele-1M-directory
```

The report includes `spectra.json`, `tables.json`, `tables.txt`, `table7.2.csv`,
`table7.3.csv`, `figure7.5.png/.pdf`, `figure7.6.png/.pdf`, `campaign.json` and
`analysis-manifest.json`. It validates every raw tree and provenance record,
streams Hits in chunks, and uses actual generated-primary accounting.
`--allow-partial` explicitly permits labeled diagnostic reports (exit 2).
See [the workflow contract](docs/BACKGROUND_STUDY.md) for integrity and disk needs.

## Development and reference analysis

`WITH_GEANT4_UIVIS=ON` retains interactive local visualization:
`(cd "$CYGNO_BUILD" && ./rdecay01 --layout legacy-25x3)`.
`CYGNO_BUILD_ANALYSIS=ON` optionally builds the existing CERN ROOT/C++ reference
executables in `analysis/`; `study/runner.py` is the legacy combined workflow.
Neither is used by the two-stage workflow.

```sh
# Standard-library-only simulation tests:
python3 -m unittest discover -s tests -p test_simulation.py -v
# Synthetic ROOT fixtures; no Geant4 or CERN ROOT required:
python -m unittest discover -s tests -v
# Optional parity with freshly built C++/ROOT reference executables:
CYGNO_REFERENCE_BUILD=/path/to/reference-build \
  python -m unittest discover -s tests -p test_parity.py -v
```

To build that optional reference (on a machine with Geant4 and CERN ROOT):

```sh
export REFERENCE_BUILD=/path/to/reference-build
cmake -S . -B "$REFERENCE_BUILD" -DWITH_GEANT4_UIVIS=OFF \
  -DCYGNO_BUILD_ANALYSIS=ON -DBUILD_TESTING=OFF \
  -DGeant4_DIR=/path/to/geant4/lib/cmake/Geant4
cmake --build "$REFERENCE_BUILD" --target SimpleProcessEvents \
  PlotNormalizedSpectra geometry_quantities --parallel
```

The parity test uses both layouts, all 26 scales/categories, grouping, chunk/EOF
boundaries, exact windows, histogram edges/flows and MC variances. Linux still
needs a fresh 4/4 preflight and 26/26 smoke after this refactor, followed by
archive/offline validation and a controlled reference comparison before 1M jobs.
No large production is launched by tests. See the [executed checks and remaining gates](docs/TWO_STAGE_VALIDATION.md).

Historical limitations remain: inherited geometry overlaps and source sampling,
process/nucleus grouping, and first-position fiducialization. **Nucleus is the most
recently tracked ion label, not guaranteed per-hit ancestry.** Published tables
are comparisons only, never normalization targets. Software-complete output does
not establish a validated physical background estimate.

[Code guide](docs/CODE_GUIDE.md) · [Layout](docs/LAYOUT.md) ·
[Sources](docs/SOURCES.md) · [Table 7.1 provenance](docs/STUDY_SOURCES.md) ·
[Raw output](docs/OUTPUT.md) · [Analysis/reference semantics](docs/ANALYSIS.md) ·
[Validation](validation/README.md) · [License/history](legacy/README.md).
