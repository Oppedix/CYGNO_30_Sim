#!/usr/bin/env bash
# Run from a FRESH CYGNO Jupyter terminal. DO NOT run cygno_setup here.
set -eo pipefail
[[ $# == 4 || $# == 5 ]] || { echo 'Usage: bash condor/subber_geant4.sh gamma|neutron NAME PRIMARIES SEED [CE=2]' >&2; exit 2; }
PARTICLE=$1 SAMPLE=$2 EVENTS=$3 SEED=$4
export CE=${5:-2}
[[ $PARTICLE == gamma || $PARTICLE == neutron ]]
[[ $SAMPLE =~ ^[a-zA-Z0-9_-]+$ && $EVENTS =~ ^[1-9][0-9]*$ && $SEED =~ ^[1-9][0-9]*$ && $CE =~ ^[1-9][0-9]*$ ]]
(( ${#EVENTS} <= 10 && ${#SEED} <= 10 && ${#CE} <= 3 && EVENTS <= 2147483647 && SEED <= 2000000000 ))
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
G4LAB=${G4LAB:-/private/SolarNu/MC30/geant4-private}
ASSETS=${CYGNO_ASSETS:-$G4LAB/condor-assets}
# Submission bookkeeping MUST live outside the frozen source and survive terminal closure.
STATE=${CYGNO_SUBMISSIONS:-$G4LAB/condor-submissions}
[[ $ASSETS != *[[:space:],]* && $HERE != *[[:space:],]* ]] || { echo 'CYGNO transfer paths must not contain whitespace or commas' >&2; exit 1; }
(cd "$ASSETS" && sha256sum -c submission-assets.sha256)
SHA=$(awk '$2 == "worker-assets.tar" {print $1}' "$ASSETS/submission-assets.sha256")
# Reserve BEFORE contacting the scheduler: even ambiguous failures must not be resubmitted blindly.
mkdir -p "$STATE"
mkdir "$STATE/$SAMPLE" || { echo "REFUSED: $SAMPLE already reserved; inspect $STATE/$SAMPLE/submission.log before retrying" >&2; exit 1; }
mkdir -p "$STATE/seeds"
mkdir "$STATE/seeds/$SEED" || { echo "REFUSED: seed $SEED already reserved; choose a fresh independent seed" >&2; exit 1; }
printf '%s\n' "$SAMPLE" > "$STATE/seeds/$SEED/campaign"
export BATCHNAME="G4_$SAMPLE"
export IMAGE=${CYGNO_WORKER_IMAGE:-/cvmfs/sft-cygno.infn.it/dockers/images/cygno-wn_v2.4.sif}
export CPUs=1
export EXECUTEPATH="$ASSETS"
export EXECUTE=run_geant4_worker.sh
export ARGUMENTS="$SHA $PARTICLE $SAMPLE $EVENTS $SEED"
export OTHERFILE="$ASSETS/worker-assets.tar"
declare -a FILENAMES=("$SAMPLE.tar" "$SAMPLE.tar.sha256")
export ENDPOINT_URL='https://s3.cr.cnaf.infn.it:7480/'
export BACKET=cygno-sim
# A fresh random leaf prevents S3 collisions even if a different submit host lost the ledger.
nonce=$(python3 -c 'import uuid; print(uuid.uuid4().hex)')
export TAG="${CYGNO_S3_PREFIX:-Users/goppedis/SolarNu}/$SAMPLE/$nonce"
printf 'replica=%s seed=%s primaries=%s CE=%s destination=s3://%s/%s/ assets=%s image=%s\n' \
  "$SAMPLE" "$SEED" "$EVENTS" "$CE" "$BACKET" "$TAG" "$SHA" "$IMAGE" | tee "$STATE/$SAMPLE/request.txt"
# Preserve the proven site interface, including BACKET's intentional spelling.
# The complete site response (including its job identifier) is printed and saved verbatim.
set +e
(
  set -e
  source /cvmfs/sft-cygno.infn.it/config/lib/subcreator.sh
  source /cvmfs/sft-cygno.infn.it/config/cygno_htc -s "$CONFOUTPATH/sub" "$CE"
) 2>&1 | tee "$STATE/$SAMPLE/submission.log"
statuses=("${PIPESTATUS[@]}")
status=${statuses[0]}
if [[ ${statuses[1]} != 0 ]]; then status=${statuses[1]}; fi
set -e
if [[ $status != 0 ]]; then
  echo "SUBMISSION FAILED/UNCERTAIN: $SAMPLE; reservation retained. Inspect the queue and saved response; do not blindly retry." >&2
  exit "$status"
fi
printf 'Submission command returned success; job identifier is in the site response above.\n' | tee "$STATE/$SAMPLE/submitted.txt"
