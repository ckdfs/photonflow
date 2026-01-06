/**
 * @file dc_source.cpp
 * @brief DC source block implementation.
 */

#include "photonflow/blocks/electrical/dc_source.hpp"
#include "photonflow/blocks/block_registry.hpp"

namespace photonflow {

DCSource::DCSource(const std::string &id, const json &params,
                   const json &nonideal)
    : BaseBlock(id, params, nonideal) {}

std::unordered_map<std::string, Signal>
DCSource::process(const std::unordered_map<std::string, Signal> & /*inputs*/,
                  SimContext &ctx) {
  double voltage = get_param("voltage", 0.0);

  // Apply non-ideal effects if enabled
  bool nonideal_enable = get_nonideal("enable", false);
  double noise_rms = 0.0;

  if (nonideal_enable) {
    voltage += get_nonideal("offset_error", 0.0);
    noise_rms = get_nonideal("noise_rms", 0.0);
  }

  const int n = ctx.n_samples();
  Eigen::VectorXcd data(n);

  if (noise_rms > 0.0) {
    Eigen::VectorXd noise = ctx.randn(n);
    for (int i = 0; i < n; ++i) {
      data[i] = std::complex<double>(voltage + noise_rms * noise[i], 0.0);
    }
  } else {
    data.setConstant(std::complex<double>(voltage, 0.0));
  }

  Signal output(data, ctx.fs(), ctx.t0());
  output.pol_mode = "scalar";

  return {{"elec_out", std::move(output)}};
}

std::optional<std::string> DCSource::port_type(const std::string &port) const {
  if (port == "elec_out")
    return "electrical";
  return std::nullopt;
}

json DCSource::describe() const {
  return {
      {"ports", {{"elec_out", "electrical"}}},
      {"spec",
       {{"params",
         {{"voltage", {{"type", "float"}, {"default", 0.0}, {"unit", "V"}}}}},
        {"nonideal",
         {{"enable", {{"type", "bool"}, {"default", false}}},
          {"offset_error",
           {{"type", "float"}, {"default", 0.0}, {"unit", "V"}}},
          {"noise_rms",
           {{"type", "float"}, {"default", 0.0}, {"unit", "V"}}}}}}}};
}

REGISTER_BLOCK(DCSource, "DCSource");

} // namespace photonflow
