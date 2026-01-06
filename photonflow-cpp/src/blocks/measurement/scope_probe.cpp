/**
 * @file scope_probe.cpp
 * @brief ScopeProbe implementation.
 */

#include "photonflow/blocks/measurement/scope_probe.hpp"
#include "photonflow/blocks/block_registry.hpp"

namespace photonflow {

ScopeProbe::ScopeProbe(const std::string &id, const json &params,
                       const json &nonideal)
    : BaseBlock(id, params, nonideal) {}

std::unordered_map<std::string, Signal>
ScopeProbe::process(const std::unordered_map<std::string, Signal> &inputs,
                    SimContext & /*ctx*/) {
  auto it = inputs.find("elec_in");
  if (it == inputs.end()) {
    return {};
  }
  return {};
}

std::optional<std::string>
ScopeProbe::port_type(const std::string &port) const {
  if (port == "elec_in")
    return "electrical";
  return std::nullopt;
}

json ScopeProbe::describe() const {
  return {{"ports", {{"elec_in", "electrical"}}},
          {"spec", {{"params", json::object()}, {"nonideal", json::object()}}}};
}

REGISTER_BLOCK(ScopeProbe, "ScopeProbe");

} // namespace photonflow
