#!/bin/bash
# Only environment checks and dispatch; the existing runners own each campaign.
set -eo pipefail
: "${CYGNO_SRC:?}" "${CYGNO_BUILD:?}" "${CYGNO_RUNS:?}" "${CYGNO_G4_SETUP:?}" "${CYGNO_PYTHON:?}"
: "${CYGNO_JOBS:?}" "${CYGNO_PRIMARIES:?}" "${CYGNO_TAG:?}"
source "$CYGNO_G4_SETUP"
set -euo pipefail
[[ $# == 1 && $CYGNO_JOBS =~ ^[1-9][0-9]*$ && $CYGNO_PRIMARIES =~ ^[1-9][0-9]*$ && $CYGNO_TAG =~ ^[a-zA-Z0-9_-]+$ ]] || {
    echo 'Expected one campaign name, positive jobs/primaries and an alphanumeric tag (also _ or -).' >&2
    exit 1
}
cd "$CYGNO_SRC"
git rev-parse HEAD
"$CYGNO_PYTHON" -c 'import sys; assert sys.version_info >= (3, 10), "Python >=3.10 required"; print(sys.version)'
for tool in rdecay01 geometry_quantities; do
    [[ -x $CYGNO_BUILD/$tool ]] || { echo "Missing executable: $CYGNO_BUILD/$tool" >&2; exit 1; }
done
[[ -d $CYGNO_RUNS && -w $CYGNO_RUNS && -x $CYGNO_RUNS ]] || {
    echo "Output parent unavailable or not writable on $(hostname): $CYGNO_RUNS" >&2
    exit 1
}
probe=$(mktemp "$CYGNO_RUNS/.condor-write-test.XXXXXX")
printf 'Worker %s can write %s\n' "$(hostname)" "$CYGNO_RUNS"
rm -- "$probe"

campaign=$1
output="$CYGNO_RUNS/$campaign-v4-11x7-$CYGNO_TAG"
common=(--build "$CYGNO_BUILD" --output "$output" --primaries "$CYGNO_PRIMARIES" --output-mode compact --retry-failed)
case "$campaign" in
    internal-no-gas|internal-with-gas)
        gas=no
        if [[ $campaign == internal-with-gas ]]; then gas=yes; fi
        command=("$CYGNO_PYTHON" internal/study/simulate.py
            --config "$CYGNO_SRC/internal/config/study/cygno-11x7-v4.json"
            "${common[@]}" --jobs "$CYGNO_JOBS" --gas-bkg "$gas" --resume)
        ;;
    external-gamma|external-neutron)
        config=${CYGNO_GAMMA_CONFIG:?}
        if [[ $campaign == external-neutron ]]; then config=${CYGNO_NEUTRON_CONFIG:?}; fi
        command=("$CYGNO_PYTHON" external/study/simulate.py --config "$config" "${common[@]}")
        ;;
    *) echo "Unknown campaign: $campaign" >&2; exit 1 ;;
esac
printf 'Running: '; printf '%q ' "${command[@]}"; printf '\n'
exec "${command[@]}"
