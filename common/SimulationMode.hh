#pragma once
// Set once by main, before geometry, actions or workers exist.
#include <stdexcept>
#include <string>
namespace cygno::simulation {
inline bool external = false;
inline bool shielded = false;
inline void Configure(const std::string& mode, const std::string& shield) {
  if (mode != "internal" && mode != "external") throw std::invalid_argument("Invalid simulation mode");
  if (shield != "none" && shield != "copper20") throw std::invalid_argument("Invalid shielding");
  if (mode == "internal" && shield != "none") throw std::invalid_argument("Shielding belongs to external mode");
  external = mode == "external";
  shielded = shield == "copper20";
}
inline const char* Physics() { return external ? "QGSP_BIC_HP_EMZ" : "QGSP_BIC_EMZ"; }
inline const char* SourcePolicy() { return external ? "environmental-surface-v1" : "uniform-volume-v1"; }
inline const char* Processing() { return external ? "external-track-volumes-v1" : "event-boundaries-and-eof-v2"; }
}
