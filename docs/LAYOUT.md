# Detector layout profiles

All profiles share module dimensions; internal sources use `uniform-volume-v1`.
Preferred internal v3 uses `cygno-acrylic-v3` and
`config/study/cygno-11x7-v3.json`; supported v2 uses `cygno-300elj-v2` and
`config/study/cygno-11x7-v2.json`. External retains v2 with its own source policy.
Layout identity is separate from detector construction and source policy. Select it before
initialization:

```sh
# Directory: shared build; run.mac is an operator-supplied diagnostic macro here.
cd "$CYGNO_BUILD"
./rdecay01 "$CYGNO_BUILD/run.mac" 1 --layout cygno-11x7-v1 --model cygno-acrylic-v3
```

`legacy-25x3` and `cygno-5x5x3-v1` remain supported; the application's omitted
layout option still selects 5×5×3. These names describe placement layouts, not
permission to reuse old detector/source results. Metadata checks require the
new model/policy and exact geometry hash. Unknown/duplicate options fail closed.

## Shared layout and dimensions

`common/DetectorGeometry.hh`: `BuildModuleLayout`, `BuildLayoutProfile`,
`GasCenter`, `GasCopyNumber`. Shared dimensions are millimetres. Modules are
unrotated translations. [SINGLE_MODULE_GEOMETRY.md](SINGLE_MODULE_GEOMETRY.md)
contains the full component dimensions/materials/masses and construction map.

| Profile | Module ordering and centres [mm] | Modules / sensitive gas / total placements |
|---|---|---|
| cygno-11x7-v1 | `m=ix*7+iy`; `((ix-5)*504,(iy-3)*804,0)` | 77 / 154 / 10705 |
| legacy-25x3 | `m=ix*3+iy`; `((ix-12)*504,(iy-1)*804,0)` | 75 / 150 / 10427 |
| cygno-5x5x3-v1 | `m=(ix*5+iy)*3+iz`; `((ix-2)*504,(iy-2)*804,(iz-1)*2285.42)` | 75 / 150 / 10427 |

Every module has 139 placements: cathode core1/Cu2, GEM core6/Cu12, transfer gas4,
support2, strip50, resistor52, lens4, sensor4, sensitive drift2. Add one common
vessel and one World. Gas copy is `side*moduleCount+m`, centred at
`moduleCentre+(0,0,±250.030)`. Side 0 is +Z. Foil layers and transfer gaps have
separate local copies. Physical `Prefix_copy` names are unique; copies are unique
within a family. The transfer gas is non-sensitive and has no source assay.

Complete local envelope: `(-250.145,-400.1275,-1140.710)` to
`(250.075,400.660,1140.710)`. Pitches 504/804/2285.420 give complete-envelope gaps
3.780/3.2125/4.000 mm. Geometry checks independently verify every centre, source
count, 500 mm gas boundaries, laminate interfaces and inter-module separation.
Retained field-cage internal intersections are documented, not silently repaired.

## Shared vessel and World

| Profile | Vessel outer size [mm] | World size [mm] |
|---|---|---|
| cygno-11x7-v1 | 5560×5644×1028.420 | 14000×6644×3281.420 |
| legacy-25x3 | 12616×2428×1028.420 | 14000×3428×3281.420 |
| cygno-5x5x3-v1 | 2536×4036×5599.260 | 14000×5036×7852.260 |

There is one 5 mm Cu shell per layout, with no apertures. Inner dimensions are
outer dimensions minus 10 mm in every axis. Extents derive from module spans
and the final GEM outer face. Drift/GEM/cage pieces lie inside the cavity;
planar optics lie outside, middle-plane optics in 5×5×3 lie inside. No component
crosses the wall. World grows to retain 500 mm clearance and minimum half sizes.
Empty space remains air; drift and GEM transfer boxes contain He/CF4.

## Analysis and future layout changes

The ROOT adapter consumes the same layout/GasCenter functions. Portable offline
analysis consumes the campaign's exported gas size/centres. 20 mm fiducial insets
and group semantics are unchanged. Old model/policy records and historical
geometry hashes are rejected; explicit assumptions cannot override metadata.

Future profiles require a new layout ID and independent centre/ID/bounds tests.
Update `LAYOUT_MODULE_COUNTS` together with the C++ provider. Source transforms
are rotation-safe, but rotated module reconstruction/envelopes would require an
explicit new layout contract. Neither layout IDs nor gas copies encode arbitrary
orientations.
