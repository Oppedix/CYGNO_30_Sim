#!/usr/bin/env bash
# The existing internal runner and its four-case decay gate remain authoritative.
set -euo pipefail
: "${CYGNO_SRC:?repository root}" "${CYGNO_BUILD:?shared Geant4 build}" "${CYGNO_RUNS:?campaign parent}" "${CYGNO_CAMPAIGN:?unique campaign name}" "${CYGNO_PRIMARIES:?primaries per contribution}"
if [[ -n ${G4LAB:-} ]]; then source "$G4LAB/activate.sh"; fi
cd "$CYGNO_SRC"
exec "${CYGNO_PYTHON:-python3}" internal/study/simulate.py \
  --config "${CYGNO_CONFIG:-$CYGNO_SRC/internal/config/study/cygno-11x7-v4.json}" \
  --build "$CYGNO_BUILD" --output "$CYGNO_RUNS/$CYGNO_CAMPAIGN" \
  --primaries "$CYGNO_PRIMARIES" --jobs "${CYGNO_JOBS:-1}" \
  --output-mode "${CYGNO_OUTPUT_MODE:-compact}" "$@"
