#!/usr/bin/env bash
# ROOT environment active; no Geant4 needed. Original analyzer source is untouched.
set -Eeuo pipefail
[[ $# == 1 ]] || { echo 'Usage: bash external/merge/build_analyzer.sh /absolute/bin/AnalyzeExternal' >&2; exit 2; }
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root-config --version
libs=(-lRooFitHS3)
libdir=$(root-config --libdir)
if compgen -G "$libdir/libRooFitJSONInterface.*" > /dev/null; then libs+=(-lRooFitJSONInterface); fi
mkdir -p "$(dirname -- "$1")"
# root-config supplies the ROOT installation's actual language standard.
c++ -O3 -std=c++17 -ffp-contract=off "$here/AnalyzeExternal.cpp" \
  "-DCYGNO_MERGE_SCRIPT=\"$here/merge.py\"" \
  $(root-config --cflags --libs) "${libs[@]}" -o "$1"
