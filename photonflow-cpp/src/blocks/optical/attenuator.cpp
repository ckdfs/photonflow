/**
 * @file attenuator.cpp
 * @brief Optical attenuator block implementation.
 */

#include "photonflow/blocks/optical/attenuator.hpp"
#include "photonflow/blocks/block_registry.hpp"

#include <cmath>

namespace photonflow {

Attenuator::Attenuator(const std::string &id, const json &params,
                       const json &nonideal)
    : BaseBlock(id, params, nonideal) {}

std::unordered_map<std::string, Signal>
Attenuator::process(const std::unordered_map<std::string, Signal> &inputs,
                    SimContext & /*ctx*/) {
  const Signal &opt_in = inputs.at("opt_in");
  double loss_db = get_param("loss_db", 0.0);

  // Convert dB to linear (field, not power)
  double loss_linear = std::pow(10.0, -loss_db / 20.0);

  Eigen::VectorXcd data = opt_in.data * loss_linear;

  Signal output(data, opt_in.fs, opt_in.t0);
  output.center_freq = opt_in.center_freq;
  output.pol_mode = opt_in.pol_mode;
  output.meta = opt_in.meta;

  return {{"opt_out", std::move(output)}};
}

std::optional<std::string>
Attenuator::port_type(const std::string &port) const {
  if (port == "opt_in" || port == "opt_out")
    return "optical";
  return std::nullopt;
}

json Attenuator::describe() const {
  return {
      {"ports", {{"opt_in", "optical"}, {"opt_out", "optical"}}},
      {"spec",
       {{"params",
         {{"loss_db", {{"type", "float"}, {"default", 0.0}, {"unit", "dB"}}}}},
        {"nonideal", {{"enable", {{"type", "bool"}, {"default", false}}}}}}}};
}

REGISTER_BLOCK(Attenuator, "Attenuator");

} // namespace photonflow
