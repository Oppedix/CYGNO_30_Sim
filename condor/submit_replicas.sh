#!/usr/bin/env bash
# Nine invocations of the original submission pattern mean nine independent jobs.
set -Eeuo pipefail
[[ $# == 3 || $# == 4 ]] || { echo 'Usage: bash condor/submit_replicas.sh gamma|neutron REPLICAS PRIMARIES [CE=2]' >&2; exit 2; }
particle=$1 count=$2 events=$3 ce=${4:-2}
[[ $particle == gamma || $particle == neutron ]]
[[ $count =~ ^[1-9][0-9]*$ && $events =~ ^[1-9][0-9]*$ && $ce =~ ^[1-9][0-9]*$ ]]
# Fixed default namespace makes repeating a command refuse old reservations, never duplicate them.
prefix=${CYGNO_REPLICA_PREFIX:-external-$particle-v4-11x7-1B-set01}
seed_base=${CYGNO_SEED_BASE:-730000000}
[[ $prefix =~ ^[a-zA-Z0-9_-]+$ && $seed_base =~ ^[1-9][0-9]*$ ]]
(( ${#count} <= 5 && ${#events} <= 10 && ${#ce} <= 3 && ${#seed_base} <= 10 && count <= 10000 && events <= 2147483647 && seed_base + count <= 2000000000 ))
if [[ -n ${CYGNO_EXISTING_CAMPAIGN:-} ]]; then
  old_seed=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]+"/campaign.json"))["identity"]["config"]["seed"])' "$CYGNO_EXISTING_CAMPAIGN")
  [[ $old_seed =~ ^[1-9][0-9]*$ && ${#old_seed} -le 10 ]]
  if (( old_seed > seed_base && old_seed <= seed_base + count )); then
    echo "REFUSED: seed range overlaps existing campaign seed $old_seed" >&2; exit 1
  fi
  echo "Inspected existing campaign seed: $old_seed (does not overlap). Join will check the full random stream and physics identity."
else
  echo 'Existing CNAF 1B seed is unavailable: use only new replicas unless the original passes join validation.'
fi
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
echo "Seeds: $((seed_base+1))..$((seed_base+count)); join validation also rejects overlapping derived random seeds."
for (( i=1; i<=count; i++ )); do
  printf -v name '%s-r%02d' "$prefix" "$i"
  if ! bash "$here/subber_geant4.sh" "$particle" "$name" "$events" "$((seed_base+i))" "$ce"; then
    echo "STOPPED at replica $i/$count ($name). Previous submissions remain active. Inspect reservations and the queue before any further submission." >&2
    exit 1
  fi
done
