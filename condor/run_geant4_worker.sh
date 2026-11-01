#!/usr/bin/env bash
# ONE serial transport process; no private/Jupyter filesystem is needed here.
set -Eeuo pipefail
trap 'printf "WORKER FAILED at line %s; retrieve stdout/stderr with cygno_htc -f JOBID CE.\n" "$LINENO" >&2' ERR
[[ $# == 5 ]] || { echo 'Expected assets SHA256 particle campaign primaries seed' >&2; exit 2; }
ASSET_SHA=$1 PARTICLE=$2 SAMPLE=$3 EVENTS=$4 SEED=$5
[[ $ASSET_SHA =~ ^[a-f0-9]{64}$ && $SAMPLE =~ ^[a-zA-Z0-9_-]+$ && $EVENTS =~ ^[1-9][0-9]*$ && $SEED =~ ^[1-9][0-9]*$ ]]
[[ $PARTICLE == gamma || $PARTICLE == neutron ]]
[[ ! -e runtime && ! -e "$SAMPLE" && ! -e "$SAMPLE.tar" ]]
printf '%s  worker-assets.tar\n' "$ASSET_SHA" | sha256sum -c -
# Archive produced and checksummed by prepare; never unpack a substituted asset.
mkdir runtime
tar -xf worker-assets.tar -C runtime
export PYTHONDONTWRITEBYTECODE=1
export G4FORCENUMBEROFTHREADS=1 G4RUN_MANAGER_TYPE=Serial OMP_NUM_THREADS=1
export LD_LIBRARY_PATH="$PWD/runtime/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
python3 -c 'import sys; assert sys.version_info >= (3,10), "Worker requires Python >=3.10"'
for binary in rdecay01 geometry_quantities; do
  ldd "runtime/build/$binary" > "$binary.ldd"
  if grep -q 'not found' "$binary.ldd"; then
    cat "$binary.ldd" >&2; echo 'Incompatible worker libraries/ABI; no Geant4 fallback allowed.' >&2; exit 1
  fi
done
for key in G4NEUTRONHPDATA G4LEDATA G4LEVELGAMMADATA G4RADIOACTIVEDATA G4PARTICLEXSDATA G4PIIDATA G4REALSURFACEDATA G4SAIDXSDATA G4ABLADATA G4INCLDATA G4ENSDFSTATEDATA G4CHANNELINGDATA; do
  export "$key=$PWD/runtime/datasets/$key"
done
python3 runtime/source/condor/assets.py check "$PWD/runtime"
python3 runtime/source/external/study/simulate.py \
  --config "runtime/$PARTICLE.json" --build runtime/build --output "$SAMPLE" \
  --primaries "$EVENTS" --seed "$SEED" --output-mode compact
mkdir "$SAMPLE/worker"
cp -r worker-preflight "$SAMPLE/worker/"
cp rdecay01.ldd geometry_quantities.ldd runtime/requirements.json "$SAMPLE/worker/"
printf '%s  worker-assets.tar\n' "$ASSET_SHA" > "$SAMPLE/worker/assets.sha256"
# Preserve all probes, source snapshots, manifests, receipts, logs and ROOT data.
python3 runtime/source/condor/campaign_transfer.py pack "$SAMPLE" "$SAMPLE.tar"
echo "SUCCESS: $SAMPLE.tar and $SAMPLE.tar.sha256 (complete verified campaign)"
