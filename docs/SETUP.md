# Common checkout, environment and build

Both workflows require the full parent repository. Select **one** environment
below, then build from the [root instructions](../README.md#install-and-build-the-common-application).
Use one shared `CYGNO_BUILD` for Internal and External on the same machine.
Build/results must be outside the checkout. Paths on different hosts are not
interchangeable; transferred campaigns can be analyzed without the original
Geant4 installation.

| Path | What is known |
|---|---|
| `/private/SolarNu/MC30/geant4-private` | Documented private Linux Geant4 workspace, with `activate.sh` and the serial 11.3.1 installation below |
| `$G4LAB/projects/CYGNO_30_Sim` | Documented source-checkout convention inside that private workspace |
| `/cnaf/cygno-sim/Users/goppedis/SolarNu` | CNAF campaign storage only, including the historical `25x3Samuele-1M` input; source, builds and analysis output stay in the private workspace |
| Build/run names below | Configurable output choices, not assertions that those directories already exist |
| Worker access and ROOT activation | Site-specific; private Geant4 paths are documented below, but worker mount visibility, native scheduler access and a ROOT setup script still need confirmation |

## Local workstation

Open a terminal on the workstation. Choose an existing writable parent for the
clone; replace the explicit `/absolute/path/...` settings with your paths.
Do not run the placeholders literally. SSH cloning requires your GitHub access;
it does not log in to a simulation host.

```bash
# Directory: chosen local workspace, outside any existing checkout.
export CYGNO_WORK=/absolute/path/to/your/workspace
cd "$CYGNO_WORK"
git clone --branch main git@github.com:Oppedix/CYGNO_30_Sim.git CYGNO_30_Sim
export CYGNO_SRC="$CYGNO_WORK/CYGNO_30_Sim"
export CYGNO_BUILD="$CYGNO_WORK/build/cygno-common"
export CYGNO_RUNS="$CYGNO_WORK/runs"
export CYGNO_ANALYSIS_RUNS="$CYGNO_WORK/runs"
cd "$CYGNO_SRC"

# Directory: $CYGNO_SRC. Use your installed Geant4 prefix, not a ROOT prefix.
export CYGNO_G4_PREFIX=/absolute/path/to/your/geant4-install
source "$CYGNO_G4_PREFIX/bin/geant4.sh"
export Geant4_DIR="$CYGNO_G4_PREFIX/lib/cmake/Geant4"
mkdir -p "$CYGNO_RUNS"
```

If your installation exports its CMake package elsewhere, set `Geant4_DIR` to
that actual directory. Activate the matching datasets as prescribed by the
installation. On macOS, if this Geant4 installation was built against an existing
Homebrew zlib, expose that dependency before configuring. This prevents CMake
from selecting an older SDK zlib (observed locally: SDK 1.2.12 versus required
Homebrew 1.3.2); it does not install a package:

```bash
# Directory: $CYGNO_SRC on a macOS workstation with Homebrew zlib already installed.
cd "$CYGNO_SRC"
export CMAKE_PREFIX_PATH="$(brew --prefix zlib)${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
```

Now run the [common build](../README.md#install-and-build-the-common-application),
then the [internal](../internal/README.md#smoke-simulation) or
[external](../external/README.md#smoke-simulation) commands.
The tested macOS/arm64 decay environments still exhibit PART122; local geometry
viewing or external gamma success does not open the internal production gate.

For interactive viewing, configure the same build with `WITH_GEANT4_UIVIS=ON`
only if Geant4 has the required UI/visualization support, then rebuild. A single
binary supports all layouts:

```bash
# Directory: shared Geant4 build (after a UI-enabled build).
cd "$CYGNO_BUILD"
./rdecay01 --layout legacy-25x3
# After closing the first session:
./rdecay01 --layout cygno-11x7-v1 --model cygno-copper-cathode-v4
```

## Private Linux simulation environment

First connect to the private Linux machine using your existing institutional
access instructions. The login hostname/command is not recorded here. On that
machine, use the documented workspace below. Clone only if the checkout is
absent; for an existing checkout, inspect local changes before updating `main`.

```bash
# Directory: the private Linux workspace's projects parent.
# Start a clean shell before activating this environment.
bash --noprofile --norc
export G4LAB=/private/SolarNu/MC30/geant4-private
source "$G4LAB/activate.sh"
mkdir -p "$G4LAB/projects"
cd "$G4LAB/projects"
git clone --branch main git@github.com:Oppedix/CYGNO_30_Sim.git CYGNO_30_Sim
export CYGNO_SRC="$G4LAB/projects/CYGNO_30_Sim"
export CYGNO_BUILD="$G4LAB/build/cygno-common-11.3.1-linux"
export CYGNO_RUNS="$G4LAB/runs"
export CYGNO_ANALYSIS_RUNS="$G4LAB/runs"
export CYGNO_ANALYSIS_BIN="$G4LAB/build/root-analysis"
export Geant4_DIR="$G4LAB/software/geant4-11.3.1-serial/lib/cmake/Geant4"
cd "$CYGNO_SRC"
mkdir -p "$CYGNO_RUNS"
```

Run the [common build](../README.md#install-and-build-the-common-application)
once, then either workflow. The four-case internal decay preflight was reported
passing on this Linux serial installation; this is empirical environment evidence,
not a universal Geant4 fix. See [known issues](KNOWN_ISSUES.md).

## CNAF analysis worker

First connect through your established access procedure. The `/cnaf/...` mount
is **storage only**. Use the private workspace for the checkout, builds, software
and analysis results. Clone under `projects/` only if the checkout is absent;
otherwise update the existing `$G4LAB/projects/CYGNO_30_Sim` with
`git switch main` and `git pull --ff-only origin main` after inspecting/saving
local changes. Never update a checkout while its campaigns are active or need
an identical retry.

```bash
# Directory: private workspace, with the CNAF storage mount available.
export G4LAB=/private/SolarNu/MC30/geant4-private
export CYGNO_CNAF=/cnaf/cygno-sim/Users/goppedis/SolarNu
mkdir -p "$G4LAB/projects"
cd "$G4LAB/projects"
git clone --branch main git@github.com:Oppedix/CYGNO_30_Sim.git CYGNO_30_Sim
export CYGNO_SRC="$G4LAB/projects/CYGNO_30_Sim"
export CYGNO_BUILD="$G4LAB/build/cygno-common-11.3.1-linux"
export CYGNO_RUNS="$CYGNO_CNAF"
export CYGNO_ANALYSIS_RUNS="$G4LAB/runs"
export CYGNO_ANALYSIS_BIN="$G4LAB/build/root-analysis"
cd "$CYGNO_SRC"
mkdir -p "$CYGNO_ANALYSIS_BIN" "$CYGNO_ANALYSIS_RUNS"
```

For analysis, activate the worker's actual ROOT environment using its site
instructions, then follow the complete
[internal analyzer](../analysis/common_c++/README.md#compile) or
[external analyzer](../external/analysis/common_c++/README.md#compile) recipe.
**ROOT 6.30.02 on CNAF needs both `-lRooFitHS3` and
`-lRooFitJSONInterface`; tested ROOT 6.40.04 provides JSON through HS3 alone.**
No ROOT activation path is assumed. Geant4 is unnecessary for either analyzer.

For simulation, source `$G4LAB/activate.sh` and use
`Geant4_DIR=$G4LAB/software/geant4-11.3.1-serial/lib/cmake/Geant4` as in the private
Linux setup above. The build subdirectory is a documented configurable choice;
set `CYGNO_BUILD` to your actual compatible build containing `rdecay01` and
`geometry_quantities`, or compile both there. For batch jobs follow the
[CNAF HTCondor instructions](../condor/README.md). Workers must see both the
private workspace (source/build/software) and CNAF storage (campaign data);
submit-host visibility does not prove worker access.

`CYGNO_RUNS` is the simulation campaign/input parent; `CYGNO_ANALYSIS_RUNS` is the
separate analysis output parent. With this setup, analysis reads stored campaigns
from `/cnaf/...` and writes results below `$G4LAB/runs`. `src/` and `tools/` remain
private workspace directories, not locations for the detector checkout.

## Python analysis environment (either workflow)

On the local workstation or an analysis worker, set `CYGNO_SRC` to its checkout
and `CYGNO_RUNS` to its transferred/unpacked campaign parent. No Geant4 or CERN
ROOT is required. Use this environment for both Python analyzers:

```bash
# Directory: repository root on the analysis machine.
cd "$CYGNO_SRC"
export CYGNO_ANALYSIS_RUNS="${CYGNO_ANALYSIS_RUNS:-$CYGNO_RUNS}"
python3 -m venv .venv-analysis
source .venv-analysis/bin/activate
python -m pip install -r study/requirements-analysis.txt
```

Then run the corresponding [internal](../internal/README.md#python-analysis)
or [external](../external/README.md#python-analysis) analysis. Do not use an
analysis virtual environment as the simulation interpreter unless its version
and environment also satisfy the campaign requirements.
