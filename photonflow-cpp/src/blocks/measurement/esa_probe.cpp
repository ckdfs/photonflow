/**
 * @file esa_probe.cpp
 * @brief ESAProbe implementation.
 */

#include "photonflow/blocks/measurement/esa_probe.hpp"
#include "photonflow/blocks/block_registry.hpp"

namespace photonflow {

ESAProbe::ESAProbe(const std::string &id, const json &params,
                   const json &nonideal)
    : BaseBlock(id, params, nonideal) {}

std::unordered_map<std::string, Signal>
ESAProbe::process(const std::unordered_map<std::string, Signal> &inputs,
                  SimContext & /*ctx*/) {
  auto it = inputs.find("elec_in");
  if (it == inputs.end()) {
    return {};
  }
  return {};
}

std::optional<std::string> ESAProbe::port_type(const std::string &port) const {
  if (port == "elec_in")
    return "electrical";
  return std::nullopt;
}

json ESAProbe::describe() const {
  return {{"ports", {{"elec_in", "electrical"}}},
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

REGISTER_BLOCK(ESAProbe, "ESAProbe");

} // namespace photonflow
