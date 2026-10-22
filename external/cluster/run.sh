#!/usr/bin/env bash
# Run inside an allocated cluster job; paths are supplied by the operator.
set -euo pipefail
: "${CYGNO_SRC:?repository root}" "${CYGNO_BUILD:?shared Geant4 build}" "${CYGNO_RUNS:?campaign parent}" "${CYGNO_CAMPAIGN:?unique campaign name}" "${CYGNO_PRIMARIES:?primaries for this job}"
if [[ -n ${G4LAB:-} ]]; then source "$G4LAB/activate.sh"; fi
cd "$CYGNO_SRC"
exec "${CYGNO_PYTHON:-python3}" external/study/simulate.py \
  --config "${CYGNO_CONFIG:-$CYGNO_SRC/external/config/hall-c-gamma-2026-proxy.json}" \
  --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/$CYGNO_CAMPAIGN" \
  --primaries "$CYGNO_PRIMARIES" --output-mode "${CYGNO_OUTPUT_MODE:-compact}" "$@"
