# Shared optional external copper shielding

Implemented in the **single** `src/geometry/DetectorConstruction.cc` using shared
`common/ExternalGeometry.hh`, for all three existing layouts. Geometry/CAD,
module dimensions, source-component masses and gas-copy maps are not duplicated
under internal/external. The active detector has no CADMesh/STL importer.

`--mode internal` (the default) constructs the exact previous unshielded detector.
`--mode external` adds four copper shells by default. `--shield none` disables
these four shells for the external control. `--shield copper20` with internal is
rejected, preventing unmarked shielded internal campaigns. Options are parsed
before initialization; shielding cannot be changed by an idle-state macro.

The centered inner cavity half-size per axis is the maximum of the common
vessel's outer half-size and both signs of the full occupied module envelope,
plus **10 mm clearance**. The module envelope includes the external optics and
sensors. The four adjacent World-daughter Boolean shells are
`ExternalCu0..3`, innermost first, with inner half-sizes h+50i mm and outer
half-sizes h+50(i+1) mm. Material is the same `G4_Cu` as the common vessel.
All six faces are closed. There are no intentional gaps between copper layers,
and total nominal thickness normal to a flat face is 200 mm. Diagonal paths
are longer. The previous 5 mm Cu vessel is additional detector material.

| Layout | Inner cavity half-size [mm] | Outer shield half-size [mm] |
|---|---|---|
| legacy-25x3 | (6318,1224,1150.710) | (6518,1424,1350.710) |
| cygno-5x5x3-v1 | (1278,2028,3436.130) | (1478,2228,3636.130) |
| cygno-11x7-v1 | (2790,2832,1150.710) | (2990,3032,1350.710) |

These are envelope-derived ideal shields, not imported engineering meshes. Future
changes to module bounds automatically reach all shells through the shared
provider. Tests independently check actual solid bounds, material, six-face
thickness, neighboring shell intersections and optical containment for every
layout. Existing field-cage intersections remain documented separately.

The external source radius is `norm(outer shield half-size)+100 mm`, even for
`--shield none`. External World half-sizes are at least that radius+100 mm in
all axes. Internal World dimensions/arithmetic remain unchanged. Thus neither
the source sphere nor shield corners lie outside World. This larger external
World is air, without the historical WIP cave/rock model.

`SimulationMetadata` and external campaign identity record the shielding,
external geometry hash, source radius, physics and source hash. The base detector
geometry hash is deliberately unchanged; use the complete identity when comparing
shielded and unshielded simulations. See [external output contract](../external/docs/OUTPUT.md).
