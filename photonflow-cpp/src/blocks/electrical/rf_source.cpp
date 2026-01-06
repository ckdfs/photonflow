/**
 * @file rf_source.cpp
 * @brief RF source block implementation.
 */

#include "photonflow/blocks/electrical/rf_source.hpp"
#include "photonflow/blocks/block_registry.hpp"

#include <cmath>

namespace photonflow {

RFSource::RFSource(const std::string &id, const json &params,
                   const json &nonideal)
    : BaseBlock(id, params, nonideal) {}

std::unordered_map<std::string, Signal>
RFSource::process(const std::unordered_map<std::string, Signal> & /*inputs*/,
                  SimContext &ctx) {
  double freq = get_param("freq_hz", 1.0e9);
  double amplitude = get_param("amplitude", 1.0);
  double phase = get_param("phase", 0.0);
  double offset = get_param("offset", 0.0);

  // Apply non-ideal effects if enabled
  bool nonideal_enable = get_nonideal("enable", false);
  double phase_noise_rms = 0.0;
  double amp_noise_rms = 0.0;

  if (nonideal_enable) {
    freq += get_nonideal("freq_offset_hz", 0.0);
    amplitude *= (1.0 + get_nonideal("amplitude_error_pct", 0.0) / 100.0);
    offset += get_nonideal("offset_error", 0.0);
    phase_noise_rms = get_nonideal("phase_noise_rms", 0.0);
    amp_noise_rms = get_nonideal("amplitude_noise_rms", 0.0);
  }

  const int n = ctx.n_samples();
  Eigen::VectorXd t = ctx.time();

  // Generate phase: 2*pi*f*t + phase0
  Eigen::VectorXd phi = 2.0 * M_PI * freq * t.array() + phase;

  // Add phase noise if enabled
  if (phase_noise_rms > 0.0) {
    phi += phase_noise_rms * ctx.randn(n);
  }

  // Generate sinusoidal signal
  Eigen::VectorXd real_data = amplitude * phi.array().sin() + offset;

  // Add amplitude noise if enabled
  if (amp_noise_rms > 0.0) {
    real_data += amp_noise_rms * ctx.randn(n);
  }

  // Convert to complex (electrical signals are real-valued stored as complex)
  Eigen::VectorXcd data(n);
  for (int i = 0; i < n; ++i) {
    data[i] = std::complex<double>(real_data[i], 0.0);
  }

  Signal output(data, ctx.fs(), ctx.t0());
  output.pol_mode = "scalar";

  return {{"elec_out", std::move(output)}};
}

std::optional<std::string> RFSource::port_type(const std::string &port) const {
  if (port == "elec_out")
    return "electrical";
  return std::nullopt;
}

std::optional<double> RFSource::estimate_fmax() const {
  if (params_.contains("freq_hz")) {
    return params_["freq_hz"].get<double>();
  }
  return std::nullopt;
}

json RFSource::describe() const {
  return {
      {"ports", {{"elec_out", "electrical"}}},
      {"spec",
       {{"params",
         {{"freq_hz", {{"type", "float"}, {"default", 1e9}, {"unit", "Hz"}}},
          {"amplitude", {{"type", "float"}, {"default", 1.0}, {"unit", "V"}}},
          {"phase", {{"type", "float"}, {"default", 0.0}, {"unit", "rad"}}},
          {"offset", {{"type", "float"}, {"default", 0.0}, {"unit", "V"}}}}},
        {"nonideal",
         {{"enable", {{"type", "bool"}, {"default", false}}},
          {"freq_offset_hz",
           {{"type", "float"}, {"default", 0.0}, {"unit", "Hz"}}},
          {"amplitude_error_pct",
           {{"type", "float"}, {"default", 0.0}, {"unit", "%"}}},
          {"amplitude_noise_rms",
           {{"type", "float"}, {"default", 0.0}, {"unit", "V"}}},
          {"phase_noise_rms",
           {{"type", "float"}, {"default", 0.0}, {"unit", "rad"}}},
          {"offset_error",
           {{"type", "float"}, {"default", 0.0}, {"unit", "V"}}}}}}}};
}

REGISTER_BLOCK(RFSource, "RFSource");

} // namespace photonflow
