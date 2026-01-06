/**
 * @file osa_probe.cpp
 * @brief OSAProbe implementation.
 */

#include "photonflow/blocks/measurement/osa_probe.hpp"
#include "photonflow/blocks/block_registry.hpp"

namespace photonflow {

OSAProbe::OSAProbe(const std::string &id, const json &params,
                   const json &nonideal)
    : BaseBlock(id, params, nonideal) {}

std::unordered_map<std::string, Signal>
OSAProbe::process(const std::unordered_map<std::string, Signal> &inputs,
                  SimContext & /*ctx*/) {
  // Get input signal for measurement capture
  auto it = inputs.find("opt_in");
  if (it == inputs.end()) {
    return {};
  }

  // Probes don't output anything - they are measurement points
  // The signal is captured via the graph execution logic
  return {};
}

std::optional<std::string> OSAProbe::port_type(const std::string &port) const {
  if (port == "opt_in")
    return "optical";
  return std::nullopt;
}

json OSAProbe::describe() const {
  return {{"ports", {{"opt_in", "optical"}}},
          {"spec",
           {{"params",
             {{"window",
               {{"type", "enum"},
                {"default", "hann"},
                {"options", json::array({"hann", "hamming", "blackman", "rect",
                                         "kaiser"})}}},
              {"ref", {{"type", "float"}, {"default", 1.0}, {"unit", ""}}},
              {"include_power", {{"type", "bool"}, {"default", false}}}}},
            {"nonideal", json::object()}}}};
}

REGISTER_BLOCK(OSAProbe, "OSAProbe");

} // namespace photonflow
