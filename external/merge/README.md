# Join completed external campaigns without copying ROOT data

```bash
python3 external/merge/merge.py \
  --output JOINED_CAMPAIGN --inputs CAMPAIGN_0 CAMPAIGN_1 CAMPAIGN_2
AnalyzeExternal JOINED_CAMPAIGN NEW_ANALYSIS_OUTPUT
```

A join is a small `campaign.json` referencing immutable **absolute paths** to the
original completed external campaigns. There is no `hadd`, ROOT copying, event
renumbering or mutation of any input (including locks/manifests). Empty primaries
remain in the denominator. Gamma and neutron, models, layouts, shielding or flux
conventions cannot be mixed. Only compact/both external campaigns are supported.

## Why a separate external analyzer entry point is necessary

The untouched `external/analysis/common_c++/AnalyzeExternal.cpp` accepts one ROOT
file and 32-bit event totals. A logical 9B/10B join cannot be encoded for that old
binary honestly. With the user's approval, `external/merge/AnalyzeExternal.cpp`
**includes and reuses that original source unchanged**. Build this entry point
as `AnalyzeExternal` to use the exact same two-argument command for both single
and joined campaigns. Internal analysis is unchanged. Existing standalone
campaigns dispatch directly into the original analyzer.

For a join, the entry point verifies every saved input checksum/manifest, then
runs the original analyzer independently per member in separate child processes.
It sums their **integer primary-event bin/window counts**, and applies one scale:

```
N = sum(GeneratedPrimaries_i)
scale_per_year = incident_rate_s * 31536000 / N
annual_events[b] = sum(MC_events_i[b]) * scale_per_year
annual_variance[b] = sum(MC_events_i[b]) * scale_per_year^2
```

It does not add already-normalized annual spectra or variances. The estimator is
for identical incident distributions, not a mixture of different fluxes.
Canonical 1000 one-keV bins, under/overflow, exact `10<E<=400` windows,
per-primary/channel counting, recoil handling, no quenching and existing Poisson
MC uncertainty semantics are retained. Flux/model uncertainties are excluded.
Totals use 64-bit integers, limited to 2^53-1 for exact ROOT JSON/double metadata;
each original simulation retains its valid Geant4 32-bit count limit.

The output keeps the original `spectra.tsv`, `windows.tsv`, `analysis.root`,
`spectra.png`, `spectra.pdf`, `summary.txt` conventions, plus the verbatim joined
manifest and `members/INDEX/` original analyzer reports. Member ROOT datasets
remain at their original paths. Bin-rate/count outputs, not a histogram's
ROOT-version-dependent summary statistics, define the quantitative result.

## Validation and compatibility

Creation streams all ROOT event/group/track/volume relationships through the
existing external reader. It verifies complete status, matching attempt manifest,
artifact SHA256 (including ROOT), source/config/geometry snapshots, canonical
macro, successful non-interrupted/non-timed-out simulation receipt, exact
requested/generated/processed primaries with no aborts, ROOT metadata/accounting,
physical radius and incident normalization. It requires two or more distinct
canonical input directories; repeated ROOT inode/content, base seeds or either
of the actual derived Ranecu seeds are rejected. Selected attempts must be
complete. Earlier retry attempts, if any, are preserved as historical files and
are never added to the sample; the active complete attempt alone contributes.

Historical attempts must have matching identities, terminal status and valid
artifact inventories. Every file in the originals is inventoried, including previous attempts, probes
and source snapshots; nothing is written there. A second inventory detects changes
during creation. Ordinary file permissions need not be changed; existing read-only
storage works. There must be no symlinks inside inputs. Keep the inputs immutable
and at the recorded paths; to relocate them, create a **new** join after moving.
New outputs and `.partial` paths must be separate from all inputs. Failures never
publish a completed join; stale `.partial` outputs are retained for inspection.

Physics compatibility compares the entire config except primary count, base seed,
source label `id`, and runner timeout. Full spectrum weights/edges, provenance
citations/scientific status, flux convention, layout, model and shielding agree.
It compares geometry, radius, physics/Geant4 environment and every dataset's file
count/content SHA256, allowing dataset relocation. Source/geometry hashes in each
ROOT file remain tied to that member's original source identity.

The compiled source hash is reconstructed from each saved snapshot. All transport
build inputs (`app/`, `src/`, `include/`, `common/`, top-level and validation CMake)
must agree. Different Git revisions/status or analysis-only files do not alone
imply changed physics; original identities are retained per member. If executable
bytes differ, compatibility is accepted **only** for differences in the compiled
analysis inputs with matching frozen worker compiler/flags/architecture, Geant4
configuration and linked non-system libraries. An older campaign without this
extra build evidence must have the same executable SHA256. Unknown/missing
provenance or unexplained binaries are rejected, never declared compatible by
an override flag. A rejected original can be omitted; newly frozen replicas share
one executable/source environment.

## CNAF worked example: original 1B plus nine new 1B replicas

Restore the new archives first using
[condor/campaign_transfer.py](../../condor/README.md#4-locate-s3-outputs-and-restore-safely-on-cnaf).
Use a **data/analysis terminal**, not the fresh submission terminal. Joining needs
Python >=3.10 and the existing analysis dependencies (uproot, awkward, numpy).
It needs no Geant4 runtime and does not open writable ROOT files.

```bash
export G4LAB=/private/SolarNu/MC30/geant4-private
cd "$G4LAB/projects/CYGNO_30_Sim"
export STORE=/cnaf/cygno-sim/Users/goppedis/SolarNu
python3 -m venv "$G4LAB/analysis-python"  # once, if no suitable environment exists
source "$G4LAB/analysis-python/bin/activate"
python3 -m pip install -r study/requirements-analysis.txt
# Replace this one path with the actual completed original 1B directory:
ORIGINAL="$STORE/ACTUAL_ORIGINAL_1B"
inputs=("$ORIGINAL")
for i in {01..09}; do inputs+=("$STORE/external-gamma-v4-11x7-1B-set01-r$i"); done
python3 external/merge/merge.py \
  --output "$STORE/external-gamma-v4-11x7-10B-joined-set01" --inputs "${inputs[@]}"
```

Expect 10 members and 10,000,000,000 primaries **only if** the original is truly
1B and passes all seed/physics/build checks. Its seed and exact source/build were
not available locally. Do not relabel an incompatible original to force a join.
For a new-only 9B sample, omit the original:

```bash
inputs=()
for i in {01..09}; do inputs+=("$STORE/external-gamma-v4-11x7-1B-set01-r$i"); done
python3 external/merge/merge.py \
  --output "$STORE/external-gamma-v4-11x7-9B-joined-set01" --inputs "${inputs[@]}"
```

Join only the specified complete runs, never a recursive glob selecting old
attempts/partial campaigns or a previous join. Nested joins are unsupported.
The input and output locations above stay on CNAF; analysis output may too.

## Compile and run with ROOT 6.30.02 or 6.40.x

Activate the site's **actual ROOT environment** in this data/analysis terminal
(no ROOT activation path is guessed), and keep Python >=3.10 on PATH. The
compiled executable records the absolute path of `merge.py`; keep this checkout
available or rebuild after moving it. Single-campaign dispatch remains ROOT-only;
joined dispatch additionally uses Python **stdlib** to recheck saved checksums and
manifests. Uproot is needed when creating/full-validating joins, not for the
normal joined C++ dispatch. The explicit verifier command is:

```bash
python3 external/merge/merge.py --output "$STORE/external-gamma-v4-11x7-10B-joined-set01" --verify --full
```

Build helper (both ROOT versions):

```bash
root-config --version
bash external/merge/build_analyzer.sh "$G4LAB/build/root-analysis/AnalyzeExternal"
export PATH="$G4LAB/build/root-analysis:$PATH"
AnalyzeExternal "$STORE/external-gamma-v4-11x7-10B-joined-set01" \
  "$STORE/external-gamma-v4-11x7-10B-analysis-set01"
```

For a manual **ROOT 6.30.02** build from the repository root:

```bash
mkdir -p "$G4LAB/build/root-analysis"
c++ -O3 -std=c++17 -ffp-contract=off external/merge/AnalyzeExternal.cpp \
  "-DCYGNO_MERGE_SCRIPT=\"$PWD/external/merge/merge.py\"" \
  $(root-config --cflags --libs) -lRooFitHS3 -lRooFitJSONInterface \
  -o "$G4LAB/build/root-analysis/AnalyzeExternal"
```

On tested ROOT 6.40.04, omit `-lRooFitJSONInterface` if that separate library is
absent; the helper detects it. Keep `-ffp-contract=off`, avoid fast math and let
`root-config` set the installation's language standard. No `JSONNode::is_null()`
is used. See [ROOT compatibility](../../docs/ROOT_COMPATIBILITY.md).

The analyzer verifies the current inputs against the saved inventories before
analysis; changed input or joined metadata is rejected. As with any reader,
concurrent external modification is unsupported: storage must remain immutable
throughout analysis. A failed analysis keeps its `.partial` output and does not
publish success. A retry uses a new analysis directory after investigating it.

## Offline scientific regression tests

```bash
python3 -m unittest discover -s tests -p test_external_merge.py -v
python3 -m unittest discover -s tests -p test_condor.py -v
python3 -m unittest discover -s tests -p test_external.py -v
```

Synthetic campaigns include billion-primary denominators with few stored hits
(zero-hit primaries remain counted), unequal primary counts totaling 2.5B,
independent count/rate/variance/window references, original single-campaign
analysis, read-only checks, duplicate seeds/inputs, failed receipts/campaigns,
incompatible physics/data/source, unexplained binaries and checksum tampering.
These fixtures are software tests, **not** transport results or worker-image
compatibility evidence. See the dated execution record in ROOT_COMPATIBILITY.md
for versions actually compiled/executed; missing ROOT explicitly skips C++ tests.
