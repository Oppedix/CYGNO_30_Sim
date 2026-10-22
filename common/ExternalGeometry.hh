#pragma once
#include "common/DetectorGeometry.hh"
#include <cmath>
namespace cygno::geometry {
constexpr int shieldingLayers = 4;
constexpr double shieldingLayerMm = 50.;
constexpr double shieldingClearanceMm = 10.;
inline Point ShieldInnerHalfSize(const LayoutProfile& p) {
  return {std::max({p.vesselOuterHalfSize.x, -p.occupiedEnvelope.min.x, p.occupiedEnvelope.max.x})+shieldingClearanceMm,
          std::max({p.vesselOuterHalfSize.y, -p.occupiedEnvelope.min.y, p.occupiedEnvelope.max.y})+shieldingClearanceMm,
          std::max({p.vesselOuterHalfSize.z, -p.occupiedEnvelope.min.z, p.occupiedEnvelope.max.z})+shieldingClearanceMm};
}
inline Point ShieldBoundary(const LayoutProfile& p, int layer) {
  if (layer < 0 || layer > shieldingLayers) throw std::invalid_argument("Invalid shielding boundary");
  const auto h = ShieldInnerHalfSize(p);
  return {h.x+layer*shieldingLayerMm, h.y+layer*shieldingLayerMm, h.z+layer*shieldingLayerMm};
}
inline double SourceRadiusMm(const LayoutProfile& p) {
  // Same source sphere with and without Cu, enclosing every shielding corner.
  const auto h = ShieldBoundary(p, shieldingLayers);
  return std::sqrt(h.x*h.x+h.y*h.y+h.z*h.z)+100.;
}
}
