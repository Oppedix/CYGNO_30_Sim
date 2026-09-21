#ifndef CYGNO_FILE_IDENTITY_HH
#define CYGNO_FILE_IDENTITY_HH
// Shared by the compiled analysis and ROOT macro. For interpreted ROOT, add
// <build>/generated to the include path before loading PlotSpectrum.C.
#include "BuildInfo.hh"
#include "../common/DetectorGeometry.hh"
#include "TFile.h"
#include "TLeafC.h"
#include "TNamed.h"
#include "TTree.h"
#include <memory>
#include <stdexcept>
#include <string>

namespace cygno::analysis {
struct FileIdentity {
  std::string layout, model, sourcePolicy, geometryHash, provenance;
};
inline void ValidateIdentity(const FileIdentity& identity) {
  geometry::ParseLayoutId(identity.layout);
  if (identity.model != "code-compatible")
    throw std::runtime_error("Unsupported detector model: " + identity.model);
  if (identity.sourcePolicy != "historical")
    throw std::runtime_error("Unsupported source policy: " + identity.sourcePolicy);
  // The baseline header predates runtime profiles, but its current layout and
  // internals are numerically identical (Phase 1 regression). No other old hash
  // is accepted. In particular it can never identify legacy-25x3 data.
  const bool baseline = identity.geometryHash ==
    "d0e9f189266be3f0a608bba332b4fe5e5f17d9c7c2c6ef4bd95f53408f73c039";
  if (identity.geometryHash != build::geometryHash &&
      !(baseline && identity.layout == "cygno-5x5x3-v1"))
    throw std::runtime_error("File geometry fingerprint does not match a supported geometry");
}
inline void RequireExpected(const FileIdentity& actual, const std::string& layout,
                            const std::string& model, const std::string& policy = "") {
  if (!layout.empty() && actual.layout != layout)
    throw std::runtime_error("Layout mismatch: file=" + actual.layout + ", requested=" + layout);
  if (!model.empty() && actual.model != model)
    throw std::runtime_error("Detector model mismatch: file=" + actual.model + ", requested=" + model);
  if (!policy.empty() && actual.sourcePolicy != policy)
    throw std::runtime_error("Source policy mismatch");
}
inline FileIdentity RequireGeometry(TFile& file, const std::string& assumedLayout = "",
                                    const std::string& assumedModel = "") {
  FileIdentity identity;
  bool found = false;
  const auto marker = [&](const char* name) {
    auto* object = file.Get(name);
    auto* named = dynamic_cast<TNamed*>(object);
    if (object && (!named || dynamic_cast<TTree*>(object)))
      throw std::runtime_error(std::string("Invalid identity marker: ") + name);
    return named ? std::string(named->GetTitle()) : std::string();
  };
  if (file.Get("CygnoGeometry") || file.Get("CygnoLayout") ||
      file.Get("CygnoDetectorModel") || file.Get("CygnoSourcePolicy")) {
    identity = {marker("CygnoLayout"), marker("CygnoDetectorModel"),
                marker("CygnoSourcePolicy"), marker("CygnoGeometry"),
                marker("GeometryProvenance")};
    // Pre-Phase-2 processed files have exactly these two identity markers.
    // Their known processor could only label the current code-compatible model.
    if (!file.Get("CygnoDetectorModel") && !file.Get("CygnoSourcePolicy") &&
        identity.layout == "cygno-5x5x3-v1") {
      identity.model = "code-compatible";
      identity.sourcePolicy = "historical";
      identity.provenance += "; compatible pre-Phase-2 current-layout markers";
    }
    ValidateIdentity(identity);
    found = true;
  }
  if (auto* object = file.Get("RunMetadata")) {
    auto* metadata = dynamic_cast<TTree*>(object);
    if (!metadata || metadata->GetEntries() != 1)
      throw std::runtime_error("RunMetadata must contain exactly one identity record per worker file");
    const auto text = [&](const char* name) {
      auto* leaf = dynamic_cast<TLeafC*>(metadata->GetLeaf(name));
      if (!leaf) throw std::runtime_error(std::string("Missing/wrong RunMetadata field: ") + name);
      return std::string(leaf->GetValueString());
    };
    metadata->GetEntry(0);
    FileIdentity raw{text("Layout"), text("DetectorModel"), text("SourcePolicy"),
                     text("GeometryHash"), "RunMetadata recorded by simulation"};
    ValidateIdentity(raw);
    if (found) {
      RequireExpected(raw, identity.layout, identity.model, identity.sourcePolicy);
      if (raw.geometryHash != identity.geometryHash)
        throw std::runtime_error("Conflicting raw and processed geometry fingerprints");
    } else identity = raw;
    found = true;
  }
  if (!found) {
    if (assumedLayout.empty() || assumedModel.empty())
      throw std::runtime_error("Unversioned file: verify its source revision, then supply both --assume-layout PROFILE and --assume-model code-compatible");
    identity = {assumedLayout, assumedModel, "historical", build::geometryHash,
      "Researcher explicitly identified unversioned data: layout=" + assumedLayout +
      ", detector_model=" + assumedModel + ", source_policy=historical"};
    ValidateIdentity(identity);
  }
  RequireExpected(identity, assumedLayout, assumedModel);
  return identity;
}
inline void WriteIdentity(TFile& output, const FileIdentity& identity) {
  output.cd();
  TNamed("CygnoGeometry", identity.geometryHash.c_str()).Write();
  TNamed("CygnoLayout", identity.layout.c_str()).Write();
  TNamed("CygnoDetectorModel", identity.model.c_str()).Write();
  TNamed("CygnoSourcePolicy", identity.sourcePolicy.c_str()).Write();
  TNamed("GeometryProvenance", identity.provenance.c_str()).Write();
}
inline void CopyMetadata(TFile& input, TFile& output, const FileIdentity& identity) {
  WriteIdentity(output, identity);
  if (auto* metadata = dynamic_cast<TTree*>(input.Get("RunMetadata")))
    metadata->CloneTree()->Write();
}
}
#endif
