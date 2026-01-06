/**
 * @file dpmzm_composite.cpp
 * @brief DPMZMComposite implementation.
 *
 * Dual-Parallel MZM for IQ modulation.
 */

#include "photonflow/blocks/composite/dpmzm_composite.hpp"
#include "photonflow/blocks/block_registry.hpp"

#include <cmath>

namespace photonflow {

DPMZMComposite::DPMZMComposite(const std::string &id, const json &params,
                               const json &nonideal)
    : BaseBlock(id, params, nonideal) {}

std::unordered_map<std::string, Signal>
DPMZMComposite::process(const std::unordered_map<std::string, Signal> &inputs,
                        SimContext &ctx) {
  // Get optical input
  auto opt_it = inputs.find("opt_in");
  if (opt_it == inputs.end()) {
    return {};
  }
  const Signal &opt_in = opt_it->second;

  // Get I and Q electrical inputs
  auto elec_i_it = inputs.find("elec_i");
  auto elec_q_it = inputs.find("elec_q");

  Signal elec_i(Eigen::VectorXcd::Zero(ctx.n_samples()), ctx.fs(), ctx.t0());
  Signal elec_q(Eigen::VectorXcd::Zero(ctx.n_samples()), ctx.fs(), ctx.t0());

  if (elec_i_it != inputs.end())
    elec_i = elec_i_it->second;
  if (elec_q_it != inputs.end())
    elec_q = elec_q_it->second;

  // Get parameters
  double Vpi = get_param("Vpi", 3.5);
  double phi_bias_i = get_param("phi_bias_i", 0.0);
  double phi_bias_q = get_param("phi_bias_q", 0.0);
  double phi_q = get_param("phi_q", M_PI / 2.0);

  const int n = ctx.n_samples();
  Eigen::VectorXcd data(n);

  for (int i = 0; i < n; ++i) {
    // Get drive voltages
    double V_i = elec_i.data[i].real();
    double V_q = elec_q.data[i].real();

    // Calculate I and Q phase modulation
    double phase_i = M_PI * V_i / Vpi + phi_bias_i;
    double phase_q = M_PI * V_q / Vpi + phi_bias_q;

    // MZM I transfer
    std::complex<double> E_i = opt_in.data[i] * std::cos(phase_i / 2.0) * 0.5;

    // MZM Q transfer with quadrature phase shift
    std::complex<double> E_q = opt_in.data[i] * std::cos(phase_q / 2.0) * 0.5 *
                               std::exp(std::complex<double>(0, phi_q));

    // Combine at output coupler
    data[i] = E_i + E_q;
  }

  Signal output(std::move(data), ctx.fs(), ctx.t0());
  output.center_freq = opt_in.center_freq;
  output.pol_mode = opt_in.pol_mode;

  return {{"opt_out", std::move(output)}};
}

std::optional<std::string>
DPMZMComposite::port_type(const std::string &port) const {
  if (port == "opt_in" || port == "opt_out")
    return "optical";
  if (port == "elec_i" || port == "elec_q")
    return "electrical";
  return std::nullopt;
}

json DPMZMComposite::describe() const {
  return {
      {"ports",
       {{"opt_in", "optical"},
        {"elec_i", "electrical"},
        {"elec_q", "electrical"},
        {"opt_out", "optical"}}},
      {"spec",
       {{"params",
         {{"Vpi", {{"type", "float"}, {"default", 3.5}, {"unit", "V"}}},
          {"drive_mode",
           {{"type", "enum"},
            {"default", "push_pull"},
            {"options", json::array({"push_pull", "single_arm"})}}},
          {"phi_bias_i",
           {{"type", "float"}, {"default", 0.0}, {"unit", "rad"}}},
          {"phi_bias_q",
           {{"type", "float"}, {"default", 0.0}, {"unit", "rad"}}},
          {"phi_q",
           {{"type", "float"}, {"default", 1.57079632679}, {"unit", "rad"}}},
          {"bandwidth_hz",
           {{"type", "float"}, {"default", 0.0}, {"unit", "Hz"}}},
          {"bandwidth_kind",
           {{"type", "enum"},
            {"default", "rect"},
            {"options", json::array({"rect", "rc"})}}}}},
        {"nonideal",
         {{"enable", {{"type", "bool"}, {"default", false}}},
          {"loss_db", {{"type", "float"}, {"default", 0.0}, {"unit", "dB"}}},
          {"iq_phase_error",
           {{"type", "float"}, {"default", 0.0}, {"unit", "rad"}}},
          {"iq_imbalance_db",
           {{"type", "float"}, {"default", 0.0}, {"unit", "dB"}}},
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

REGISTER_BLOCK(DPMZMComposite, "DPMZMComposite");

} // namespace photonflow
