//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.  It is provided  under  the terms  and *
// * conditions of the Geant4 Software License,  included in the file *
// * LICENSE and available at  http://cern.ch/geant4/license .  These *
// * include a list of copyright holders.                             *
// *                                                                  *
// * Neither the authors of this software system, nor their employing *
// * institutes,nor the agencies providing financial support for this *
// * work  make  any representation or  warranty, express or implied, *
// * regarding  this  software system or assume any liability for its *
// * use.  Please see the license in the file  LICENSE  and URL above *
// * for the full disclaimer and the limitation of liability.         *
// *                                                                  *
// * This  code  implementation is the result of  the  scientific and *
// * technical work of the GEANT4 collaboration.                      *
// * By using,  copying,  modifying or  distributing the software (or *
// * any work based  on the software)  you  agree  to acknowledge its *
// * use  in  resulting  scientific  publications,  and indicate your *
// * acceptance of all terms of the Geant4 Software license.          *
// ********************************************************************
//
// Exact bulk sampling for the active box, cylinder and rectangular-shell solids.
#include "cygno/source/RadioactiveSourceSampler.hh"
#include "cygno/geometry/DetectorConstruction.hh"
#include "G4Box.hh"
#include "G4DisplacedSolid.hh"
#include "G4LogicalVolume.hh"
#include "G4SubtractionSolid.hh"
#include "G4Tubs.hh"
#include "G4Exception.hh"
#include "Randomize.hh"
#include <cassert>
#include <stdexcept>

namespace {
struct Slab {
  G4ThreeVector lo, hi;
  double Volume() const { const auto size=hi-lo; return size.x()*size.y()*size.z(); }
  G4ThreeVector Sample() const {
    return {lo.x()+(hi.x()-lo.x())*G4UniformRand(),
            lo.y()+(hi.y()-lo.y())*G4UniformRand(),
            lo.z()+(hi.z()-lo.z())*G4UniformRand()};
  }
};
Slab BoxBounds(G4VSolid* solid) {
  if (auto* displaced=dynamic_cast<G4DisplacedSolid*>(solid)) {
    if (!displaced->GetObjectRotation().isIdentity() ||
        !dynamic_cast<G4Box*>(displaced->GetConstituentMovedSolid()))
      throw std::runtime_error("Uniform frame sampler requires translated, axis-aligned boxes");
  } else if (!dynamic_cast<G4Box*>(solid)) {
    throw std::runtime_error("Uniform frame sampler requires box operands");
  }
  Slab bounds;
  solid->BoundingLimits(bounds.lo,bounds.hi);
  return bounds;
}
}

G4ThreeVector RadioactiveSourceSampler::SampleLocal(G4VSolid* solid) {
  G4ThreeVector point;
  if (dynamic_cast<G4Box*>(solid)) {
    point=BoxBounds(solid).Sample();
  } else if (auto* lens=dynamic_cast<G4Tubs*>(solid)) {
    const double r0=lens->GetInnerRadius(), r1=lens->GetOuterRadius();
    const double radius=std::sqrt(r0*r0+(r1*r1-r0*r0)*G4UniformRand());
    const double phi=lens->GetStartPhiAngle()+lens->GetDeltaPhiAngle()*G4UniformRand();
    point={radius*std::cos(phi),radius*std::sin(phi),
           (2*G4UniformRand()-1)*lens->GetZHalfLength()};
  } else if (auto* frame=dynamic_cast<G4SubtractionSolid*>(solid)) {
    const auto outer=BoxBounds(frame->GetConstituentSolid(0));
    auto inner=BoxBounds(frame->GetConstituentSolid(1));
    for (int axis=0; axis<3; ++axis) {
      inner.lo[axis]=std::max(outer.lo[axis],inner.lo[axis]);
      inner.hi[axis]=std::min(outer.hi[axis],inner.hi[axis]);
      if (inner.lo[axis]>=inner.hi[axis]) throw std::runtime_error("Empty rectangular frame cut");
    }
    // Peel two slabs per axis. Later slabs are restricted to the preceding
    // inner bounds, so all six pieces are disjoint, including frame corners.
    std::vector<Slab> pieces;
    Slab remaining=outer;
    double volume=0;
    for (int axis=0; axis<3; ++axis) {
      auto lower=remaining, upper=remaining;
      lower.hi[axis]=inner.lo[axis]; upper.lo[axis]=inner.hi[axis];
      for (const auto& slab : {lower,upper}) if (slab.Volume()>0) {
        pieces.push_back(slab); volume+=slab.Volume();
      }
      remaining.lo[axis]=inner.lo[axis]; remaining.hi[axis]=inner.hi[axis];
    }
    if (pieces.empty()) throw std::runtime_error("Empty source frame");
    double choice=G4UniformRand()*volume;
    const Slab* selected=&pieces.back();
    for (const auto& slab : pieces) {
      choice-=slab.Volume();
      if (choice<0) { selected=&slab; break; }
    }
    point=selected->Sample();
  } else {
    throw std::runtime_error("Unsupported uniform-volume source solid: "+solid->GetName());
  }
  assert(solid->Inside(point)!=kOutside);
  return point;
}

SourcePoint RadioactiveSourceSampler::Sample(const G4String& component) {
  std::vector<G4String> elements;
  if (component=="Cathode") elements=fDetector->GetCathodeList();
  else if (component=="CathodesPolyimide") elements=fDetector->GetCathodesPolyimideList();
  else if (component=="CathodesCopper") elements=fDetector->GetCathodesCopperList();
  else if (component=="GEMsPolyimide") elements=fDetector->GetGEMsPolyimideList();
  else if (component=="GEMsCopper") elements=fDetector->GetGEMsCopperList();
  else if (component=="RingSupports") elements=fDetector->GetRingsSupportList();
  else if (component=="RingStrips") elements=fDetector->GetRingStripstList();
  else if (component=="Resistors") elements=fDetector->GetResistorList();
  else if (component=="Lens") elements=fDetector->GetLensList();
  else if (component=="Sensors") elements=fDetector->GetSensorsList();
  else if (component=="Vessel") elements={"Vessel"};
  if (elements.empty()) {
    G4ExceptionDescription message;
    message << "Unknown or empty radioactive component: " << component;
    G4Exception("RadioactiveSourceSampler::Sample", "CYGNO_SOURCE", FatalException, message);
    return {};
  }
  // Each family consists of equal-volume, same-material placements. Their
  // uniform selection therefore gives uniform bulk contamination by mass.
  const auto name=elements.at(static_cast<size_t>(G4UniformRand()*elements.size()));
  auto* volume=fDetector->GetVolumeStored()->GetVolume(name);
  const auto local=SampleLocal(volume->GetLogicalVolume()->GetSolid());
  // Current components are direct World daughters. Geant4's OBJECT transform
  // maps local to mother/world coordinates, including any placement rotation.
  return {volume->GetObjectRotationValue()*local+volume->GetObjectTranslation(),volume};
}
