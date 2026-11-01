#!/usr/bin/env bash
# Run once in the activated Linux Geant4 11.3.1 environment, outside the submit terminal.
set -Eeuo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
: "${G4LAB:=/private/SolarNu/MC30/geant4-private}"
exec python3 "$HERE/assets.py" prepare \
  "${CYGNO_BUILD:-$G4LAB/build/cygno-common-11.3.1-linux}" \
  "${CYGNO_ASSETS:-$G4LAB/condor-assets}" "${CYGNO_TIMEOUT_SECONDS:-2592000}"
