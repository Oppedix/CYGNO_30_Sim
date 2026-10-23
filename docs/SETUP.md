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
| `/cnaf/cygno-sim/Users/goppedis/SolarNu` | Documented CNAF analysis/data base, including the historical `25x3Samuele-1M` input |
| Build/run names below | Configurable output choices, not assertions that those directories already exist |
| Local/CNAF Geant4 or ROOT activation | Site-specific; no login host, scheduler, ROOT setup script or CNAF Geant4 installation is established by this repository |

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
./rdecay01 --layout cygno-11x7-v1 --model cygno-acrylic-v3
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
export Geant4_DIR="$G4LAB/software/geant4-11.3.1-serial/lib/cmake/Geant4"
cd "$CYGNO_SRC"
mkdir -p "$CYGNO_RUNS"
```

Run the [common build](../README.md#install-and-build-the-common-application)
once, then either workflow. The four-case internal decay preflight was reported
passing on this Linux serial installation; this is empirical environment evidence,
not a universal Geant4 fix. See [known issues](KNOWN_ISSUES.md).

## CNAF analysis worker

First connect to the CNAF worker through your established access procedure.
The known base is **not** the private Linux Geant4 workspace. The following clone,
binary and run directories are explicit configurable choices under that base;
only the historical campaign path is a documented existing input.

```bash
# Directory: known CNAF SolarNu base, on the analysis worker.
export CYGNO_CNAF=/cnaf/cygno-sim/Users/goppedis/SolarNu
cd "$CYGNO_CNAF"
git clone --branch main git@github.com:Oppedix/CYGNO_30_Sim.git CYGNO_30_Sim
export CYGNO_SRC="$CYGNO_CNAF/CYGNO_30_Sim"
export CYGNO_BUILD="$CYGNO_CNAF/build/cygno-common"
export CYGNO_RUNS="$CYGNO_CNAF"
export CYGNO_ANALYSIS_BIN="$CYGNO_CNAF/build/root-analysis"
cd "$CYGNO_SRC"
mkdir -p "$CYGNO_ANALYSIS_BIN"
```

For analysis, activate the worker's actual ROOT environment using its site
instructions, then follow the complete
[internal analyzer](../analysis/common_c++/README.md#compile) or
[external analyzer](../external/analysis/common_c++/README.md#compile) recipe.
**ROOT 6.30.02 on CNAF needs both `-lRooFitHS3` and
`-lRooFitJSONInterface`; tested ROOT 6.40.04 provides JSON through HS3 alone.**
No ROOT activation path is assumed. Geant4 is unnecessary for either analyzer.

To simulate at CNAF, obtain the approved Geant4 environment/dataset activation
and actual `Geant4_DIR` from that site, then use the common build and the
[internal](../internal/docs/WORKFLOW.md#cluster-entry-point) or
[external](../external/docs/WORKFLOW.md#cluster-entry-point) wrapper inside an
allocation. No CNAF Geant4 installation or scheduler command is inferred here.

## Python analysis environment (either workflow)

On the local workstation or an analysis worker, set `CYGNO_SRC` to its checkout
and `CYGNO_RUNS` to its transferred/unpacked campaign parent. No Geant4 or CERN
ROOT is required. Use this environment for both Python analyzers:

```bash
# Directory: repository root on the analysis machine.
cd "$CYGNO_SRC"
python3 -m venv .venv-analysis
source .venv-analysis/bin/activate
python -m pip install -r study/requirements-analysis.txt
```

Then run the corresponding [internal](../internal/README.md#python-analysis)
or [external](../external/README.md#python-analysis) analysis. Do not use an
analysis virtual environment as the simulation interpreter unless its version
and environment also satisfy the campaign requirements.
