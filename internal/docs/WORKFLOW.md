# Internal local and cluster workflow

All commands run from `$CYGNO_SRC`, the root containing `CMakeLists.txt`.
`internal/` is a coherent view of the established pipeline; the original
`study/`, `config/` and `analysis/` paths remain fully supported.

## Cluster example, private Linux environment

These are configurable examples, not directories required by the software:

```bash
export G4LAB=/private/SolarNu/MC30/geant4-private
source "$G4LAB/activate.sh"
export CYGNO_SRC="$G4LAB/projects/CYGNO_30_Sim"
export CYGNO_BUILD="$G4LAB/build/cygno-common-11.3.1-linux"
export CYGNO_RUNS="$G4LAB/runs/internal"
export CYGNO_CAMPAIGN=11x7-v3-smoke-NEW
export CYGNO_PRIMARIES=2
export CYGNO_JOBS=1
cd "$CYGNO_SRC"
# Common build instructions are in internal/README.md.
bash internal/cluster/run.sh --mode smoke
# Example only, if the allocation system is PBS:
qsub -V -l nodes=1:ppn=1,walltime=02:00:00 internal/cluster/run.sh
```

Use a different campaign name for the PBS example; do not submit a second owner
of the same campaign. For an allocation with 16 CPUs, use `CYGNO_JOBS=16` and
request 16 CPUs. Each Geant4 process still uses one worker. The wrapper accepts
extra runner options, e.g. `--archive`, `--only Lens_K40`, `--retry-failed`.
`CYGNO_CONFIG` defaults to `internal/config/study/cygno-11x7-v3.json` (26 jobs)
and can select the retained v2 config (28 jobs); `CYGNO_OUTPUT_MODE` defaults to
compact; `CYGNO_PYTHON` selects the Python executable. Never set shell `HOME` or
`TMPDIR` as workflow data paths.

For production, keep the canonical 10,000,000 primaries/contribution or explicitly
choose another count after the documented preflight, smoke, archive and parity
gates. Repeat an identical command to resume. Failed contributions need
`--retry-failed`; complete contributions are checked and reused. Changed config,
source, binary, output mode or data environment requires a new campaign.

Analysis can run on a separate ROOT worker, e.g. reading
`/cnaf/cygno-sim/Users/goppedis/SolarNu/internal/11x7-complete` and writing to a
new sibling analysis directory. No Geant4 is needed by native ROOT analysis.
Python analysis needs `study/requirements-analysis.txt`, not CERN ROOT.

## Native ROOT analysis on the cluster

After loading the cluster's ROOT environment, from `$CYGNO_SRC`:

```bash
c++ -O3 -std=c++17 -ffp-contract=off \
  internal/analysis/common_c++/AnalyzeCompactCampaign.cpp -I"$CYGNO_SRC" \
  $(root-config --cflags --libs) -lRooFitHS3 -lRooFitJSONInterface \
  -o "$CYGNO_BUILD/AnalyzeCompactCampaign"
"$CYGNO_BUILD/AnalyzeCompactCampaign" \
  "$CYGNO_RUNS/11x7-v3-complete" "$CYGNO_RUNS/11x7-v3-analysis-NEW" \
  --coincidence-ns 1
```

ROOT 6.30.02 at CNAF needs both JSON libraries; omit
`-lRooFitJSONInterface` only when ROOT 6.40 supplies JSON through HS3 alone.
No Geant4 environment is needed to analyze an unpacked complete compact campaign.
The same binary reads saved v2 campaigns without relabeling or changing them.
Python uses `python3 internal/study/analyze.py --input CAMPAIGN --output NEW_DIR`.
Both record their normalization scenario separately from the saved matrix.

Physical PMMA v3 needs a new Geant4 campaign for **every contribution**, including
unchanged source components whose radiation crosses the changed cores. There is
no valid v2-to-v3 weight factor for transport. Never replace `matrix.json` or a
campaign/job manifest to force reuse; identity checks and the four-case decay
preflight remain enabled. See [version comparison](STUDY_SOURCES.md).

## Scientific boundary

Internal normalization is the unchanged per-contribution
`activity × constructed kg or pieces × seconds/year / generated primaries`.
The historical e-/e+/alpha grouping, first-position 20 mm fiducial cut and native
optional topology cuts remain as documented in [ANALYSIS](ANALYSIS.md).
The internal heavy-ion stopping policy is retained. Do not use this pipeline to
infer neutron nuclear-recoil rates, or give an external file a component assay.
External `SourcePolicy` and processing markers are deliberately incompatible.

The shared detector has retained cage intersections and vessel/optics assumptions;
see [known issues](../../docs/KNOWN_ISSUES.md). A passing software gate does not
establish a physically validated internal background prediction.
