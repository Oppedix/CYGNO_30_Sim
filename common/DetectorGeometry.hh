#ifndef CYGNO_DETECTOR_GEOMETRY_HH
#define CYGNO_DETECTOR_GEOMETRY_HH

// Shared by Geant4 and ROOT: no dependency on either library.
// All lengths in this file are millimetres. Geant4 consumers multiply by mm;
// ROOT hit coordinates are already stored in mm. Do not duplicate these values.
#include <algorithm>
#include <stdexcept>
#include <string>
#include <vector>

namespace cygno {
namespace geometry {
constexpr double millimetre = 1.0;
constexpr double centimetre = 10.0 * millimetre;

struct ModuleDimensions {
  double cathodeX = 50 * centimetre;
  double cathodeY = 80 * centimetre;
  // Historical half-length, also used as the source sampling depth. Neighboring
  // offsets use half of this value; preserve the resulting internal overlap.
  double cathodeHalfZ = 0.05 * centimetre;
  double gemX = 50 * centimetre;
  double gemY = 80 * centimetre;
  double gemThickness = 0.05 * millimetre;
  double gemCavityX = 50.01 * centimetre;
  double gemCavityY = 80.01 * centimetre;
  double gemCavityThickness = 0.005 * millimetre;
  double gemCoreX = 50 * centimetre;
  double gemCoreY = 80 * centimetre;
  double gemCoreThickness = 0.029 * millimetre;
  double gemCavityShiftFraction = 0.095;
  int gemLayers = 3;
  double gemGap = 0.2 * centimetre;
  double driftLength = 50 * centimetre;
  double supportThickness = 0.075 * millimetre;
  double stripThickness = 0.035 * millimetre;
  double stripLengthZ = 5.5 * centimetre;
  int stripCount = 4;
  double stripShiftFractionX = 0.26;
  double booleanCutExtension = 0.5 * centimetre;
  double resistorX = 1.6 * millimetre;
  double resistorY = 0.55 * millimetre;
  double resistorZ = 3.2 * millimetre;
  double lensRadius = 1 * centimetre; // previously called LensDiameter
  double lensThickness = 2 * millimetre;
  double lensDistanceFromGEMs = 57.6 * centimetre;
  double verticalLensSpacing = 38 * centimetre; // offsets are +/- spacing/4
  double sensorX = 10.6 * millimetre;
  double sensorY = 18.8 * millimetre;
  double sensorZ = 1 * millimetre;
  double sensorDistanceFromLens = 6 * centimetre;
};
constexpr ModuleDimensions module{};
constexpr double GasOffsetZ() { return module.cathodeHalfZ/2 + module.driftLength/2; }
constexpr double StripSpacing() {
  return (module.driftLength-module.stripCount*module.stripLengthZ)/(module.stripCount+1);
}
constexpr double LensOffsetZ() {
  return module.driftLength + 2*module.gemGap + 3*module.gemThickness
       + module.lensDistanceFromGEMs;
}
constexpr double SensorOffsetZ() { return LensOffsetZ()+module.sensorDistanceFromLens; }

struct Point { double x, y, z; };
struct Bounds { Point min, max; };
// Complete module envelope, excluding the single shared vessel. Extremal parts
// are the translated support (-X,-Y), resistor (+Y), and sensors (+/-Z).
// validation/check_geometry.py verifies these bounds against every placed solid.
constexpr Bounds moduleEnvelope{
  {-module.gemX/2-module.supportThickness-2*module.stripThickness,
   -module.gemY/2-module.supportThickness-1.5*module.stripThickness,
   -SensorOffsetZ()-module.sensorZ/2},
  {module.gemX/2+module.supportThickness,
   module.cathodeY/2+module.supportThickness+module.stripThickness+module.resistorY,
   SensorOffsetZ()+module.sensorZ/2}
};

// Baseline current-layout constants. Both profiles use the SAME module above.
// All modules have the same orientation; X/Y retain the 4 mm nominal cathode gap.
constexpr int modulesX = 5;
constexpr int modulesY = 5;
constexpr int modulesZ = 3;
constexpr int moduleCount = modulesX*modulesY*modulesZ;
constexpr double moduleGapXY = 4 * millimetre;
constexpr double moduleGapZ = 4 * millimetre;
constexpr double modulePitchX = module.cathodeX + moduleGapXY;
constexpr double modulePitchY = module.cathodeY + moduleGapXY;
constexpr double modulePitchZ = moduleEnvelope.max.z-moduleEnvelope.min.z+moduleGapZ;
static_assert(modulesX > 0 && modulesY > 0 && modulesZ > 0, "Positive module counts required");
static_assert(modulePitchX > moduleEnvelope.max.x-moduleEnvelope.min.x, "X module envelopes overlap");
static_assert(modulePitchY > moduleEnvelope.max.y-moduleEnvelope.min.y, "Y module envelopes overlap");
static_assert(modulePitchZ > moduleEnvelope.max.z-moduleEnvelope.min.z, "Z module envelopes overlap");

struct ModulePlacement {
  int id;
  int ix, iy, iz; // zero-based grid indices; legacy has iz=0, Y varies fastest
  Point center;  // millimetres, translated without any rotation
};
enum class LayoutId { Current5x5x3, Legacy25x3 };
inline const char* LayoutName(LayoutId id) {
  switch (id) {
    case LayoutId::Current5x5x3: return "cygno-5x5x3-v1";
    case LayoutId::Legacy25x3: return "legacy-25x3";
  }
  throw std::invalid_argument("Unknown layout ID");
}
inline LayoutId ParseLayoutId(const std::string& name) {
  if (name == "cygno-5x5x3-v1") return LayoutId::Current5x5x3;
  if (name == "legacy-25x3") return LayoutId::Legacy25x3;
  throw std::invalid_argument("Unknown layout: " + name +
      ". Choose legacy-25x3 or cygno-5x5x3-v1");
}
constexpr int ModuleId(int ix, int iy, int iz) { return (ix*modulesY+iy)*modulesZ+iz; }
inline std::vector<ModulePlacement> BuildModuleLayout(LayoutId id = LayoutId::Current5x5x3) {
  LayoutName(id); // Reject invalid enum values rather than silently using current.
  std::vector<ModulePlacement> layout;
  layout.reserve(moduleCount);
  if (id == LayoutId::Legacy25x3) {
    // Samuele 26ddbdb: outer X loop -12..12, inner Y loop -1..1, all Z=0.
    // Gas counter follows this order on +Z first, then on -Z (copies 75..149).
    for (int i=-12; i<13; ++i)
      for (int j=-1; j<2; ++j)
        layout.push_back({3*(i+12)+(j+1), i+12,j+1,0,
                          {i*modulePitchX,j*modulePitchY,0}});
    return layout;
  }
  for (int ix=0; ix<modulesX; ++ix)
    for (int iy=0; iy<modulesY; ++iy)
      for (int iz=0; iz<modulesZ; ++iz)
        layout.push_back({ModuleId(ix,iy,iz), ix,iy,iz,
          {(ix-(modulesX-1)/2.0)*modulePitchX,
           (iy-(modulesY-1)/2.0)*modulePitchY,
           (iz-(modulesZ-1)/2.0)*modulePitchZ}});
  return layout;
}
// side=0 is local +Z, side=1 is local -Z (not necessarily global +/-Z).
constexpr int GasCopyNumber(int moduleId, int side) { return side*moduleCount+moduleId; }
inline Point GasCenter(const ModulePlacement& placement, int side) {
  return {placement.center.x, placement.center.y,
          placement.center.z+(side == 0 ? GasOffsetZ() : -GasOffsetZ())};
}

// One shared copper vessel, not a vessel per module. Keep the old 5 mm wall and
// 5 mm nominal inner clearance around the outer drift/GEM array. Middle-layer
// optics now lie inside this common shell; outer-facing optics remain outside.
constexpr double vesselWall = 0.5 * centimetre;
constexpr Point moduleCenterHalfSpan{
  (modulesX-1)*modulePitchX/2, (modulesY-1)*modulePitchY/2, (modulesZ-1)*modulePitchZ/2};
constexpr Point vesselOuterHalfSize{
  moduleCenterHalfSpan.x+module.cathodeX/2+2*vesselWall,
  moduleCenterHalfSpan.y+module.cathodeY/2+2*vesselWall,
  moduleCenterHalfSpan.z+module.cathodeHalfZ/2+module.driftLength
    +2*module.gemGap+3*module.gemThickness+2*vesselWall};
constexpr double worldMargin = 50 * centimetre;
// Enlarge only as needed; retain the previous minimum World half sizes.
inline Point WorldHalfSize(const Point& vessel = vesselOuterHalfSize,
                           const Point& span = moduleCenterHalfSpan) {
  return {std::max(7000.0, std::max(vessel.x,
            span.x+std::max(-moduleEnvelope.min.x,moduleEnvelope.max.x))+worldMargin),
          std::max(1500.0, std::max(vessel.y,
            span.y+std::max(-moduleEnvelope.min.y,moduleEnvelope.max.y))+worldMargin),
          std::max(1500.0, std::max(vessel.z,
            span.z+moduleEnvelope.max.z)+worldMargin)};
}

// Runtime profile data, with no Geant4/ROOT dependency and no source policy.
// ModulePlacement plus GasCenter/GasCopyNumber supplies reconstruction inputs.
struct LayoutProfile {
  LayoutId id;
  const char* name;
  int expectedModuleCount;
  std::vector<ModulePlacement> modules;
  Bounds occupiedEnvelope;
  Point vesselOuterHalfSize;
  Point worldHalfSize;
};
inline LayoutProfile BuildLayoutProfile(LayoutId id = LayoutId::Current5x5x3) {
  LayoutProfile profile{id, LayoutName(id), moduleCount, BuildModuleLayout(id), {}, {}, {}};
  const auto first = profile.modules.front().center;
  Bounds centers{first,first};
  for (const auto& placement : profile.modules) {
    const auto c = placement.center;
    centers.min = {std::min(centers.min.x,c.x), std::min(centers.min.y,c.y), std::min(centers.min.z,c.z)};
    centers.max = {std::max(centers.max.x,c.x), std::max(centers.max.y,c.y), std::max(centers.max.z,c.z)};
  }
  profile.occupiedEnvelope = {
    {centers.min.x+moduleEnvelope.min.x, centers.min.y+moduleEnvelope.min.y, centers.min.z+moduleEnvelope.min.z},
    {centers.max.x+moduleEnvelope.max.x, centers.max.y+moduleEnvelope.max.y, centers.max.z+moduleEnvelope.max.z}};
  // Both supported layouts are centered and symmetric. Preserve baseline
  // arithmetic order for the common shell and World, including optical clearance.
  const Point span{centers.max.x, centers.max.y, centers.max.z};
  profile.vesselOuterHalfSize = {
    span.x+module.cathodeX/2+2*vesselWall,
    span.y+module.cathodeY/2+2*vesselWall,
    span.z+module.cathodeHalfZ/2+module.driftLength
      +2*module.gemGap+3*module.gemThickness+2*vesselWall};
  profile.worldHalfSize = WorldHalfSize(profile.vesselOuterHalfSize,span);
  return profile;
}
} // namespace geometry
} // namespace cygno
#endif
