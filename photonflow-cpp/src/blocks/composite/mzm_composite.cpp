/**
 * @file mzm_composite.cpp
 * @brief MZMComposite implementation.
 *
 * This implements a simplified MZM using push-pull configuration.
 * Uses internal Coupler + PM + PM + Coupler structure.
 */

#include "photonflow/blocks/composite/mzm_composite.hpp"
#include "photonflow/blocks/block_registry.hpp"

#include <cmath>

namespace photonflow {

MZMComposite::MZMComposite(const std::string &id, const json &params,
                           const json &nonideal)
    : BaseBlock(id, params, nonideal) {}

std::unordered_map<std::string, Signal>
MZMComposite::process(const std::unordered_map<std::string, Signal> &inputs,
                      SimContext &ctx) {
  // Get optical input
  auto opt_it = inputs.find("opt_in");
  if (opt_it == inputs.end()) {
    return {};
  }
  const Signal &opt_in = opt_it->second;

  // Get electrical input
  auto elec_it = inputs.find("elec_in");
  Signal elec_in(Eigen::VectorXcd::Zero(ctx.n_samples()), ctx.fs(), ctx.t0());
  if (elec_it != inputs.end()) {
    elec_in = elec_it->second;
  }

  // Get parameters
  double Vpi = get_param("Vpi", 3.5);
  double phi_bias = get_param("phi_bias", 0.0);

  // Simple MZM transfer function: E_out = E_in * cos(phase/2)
  // where phase = pi * V / Vpi + phi_bias
  const int n = ctx.n_samples();
  Eigen::VectorXcd data(n);

  for (int i = 0; i < n; ++i) {
    // Get drive voltage (real part of electrical signal)
    double V = elec_in.data[i].real();

    // Calculate phase modulation
    double phase = M_PI * V / Vpi + phi_bias;

    // MZM transfer: cos(phase/2)
    std::complex<double> transfer = std::cos(phase / 2.0);

    data[i] = opt_in.data[i] * transfer;
  }

  Signal output(std::move(data), ctx.fs(), ctx.t0());
  output.center_freq = opt_in.center_freq;
  output.pol_mode = opt_in.pol_mode;

  return {{"opt_out", std::move(output)}};
}

std::optional<std::string>
MZMComposite::port_type(const std::string &port) const {
  if (port == "opt_in" || port == "opt_out")
    return "optical";
  if (port == "elec_in")
    return "electrical";
  return std::nullopt;
}

json MZMComposite::describe() const {
  return {
      {"ports",
       {{"opt_in", "optical"},
        {"elec_in", "electrical"},
        {"opt_out", "optical"}}},
      {"spec",
       {{"params",
         {{"Vpi", {{"type", "float"}, {"default", 3.5}, {"unit", "V"}}},
          {"phi_bias", {{"type", "float"}, {"default", 0.0}, {"unit", "rad"}}},
          {"drive_mode",
           {{"type", "enum"},
            {"default", "push_pull"},
            {"options", json::array({"push_pull", "single_arm"})}}},
          {"bandwidth_hz",
           {{"type", "float"}, {"default", 0.0}, {"unit", "Hz"}}},
          {"bandwidth_kind",
           {{"type", "enum"},
            {"default", "rect"},
            {"options", json::array({"rect", "rc"})}}}}},
        {"nonideal",
         {{"enable", {{"type", "bool"}, {"default", false}}},
          {"loss_db", {{"type", "float"}, {"default", 0.0}, {"unit", "dB"}}},
          {"vpi_error_pct",
           {{"type", "float"}, {"default", 0.0}, {"unit", "%"}}},
          {"arm_ratio_db",
           {{"type", "float"}, {"default", 0.0}, {"unit", "dB"}}},
          {"phase_error",
           {{"type", "float"}, {"default", 0.0}, {"unit", "rad"}}},
          {"drive_noise_rms",
           {{"type", "float"}, {"default", 0.0}, {"unit", "V"}}},
          {"bias_error_rad",
           {{"type", "float"}, {"default", 0.0}, {"unit", "rad"}}}}}}}};
}

REGISTER_BLOCK(MZMComposite, "MZMComposite");

} // namespace photonflow
