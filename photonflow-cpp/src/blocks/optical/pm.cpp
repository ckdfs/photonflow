/**
 * @file pm.cpp
 * @brief Phase Modulator block implementation.
 */

#include "photonflow/blocks/optical/pm.hpp"
#include "photonflow/blocks/block_registry.hpp"

#include <cmath>
#include <complex>

namespace photonflow {

PM::PM(const std::string &id, const json &params, const json &nonideal)
    : BaseBlock(id, params, nonideal) {}

std::unordered_map<std::string, Signal>
PM::process(const std::unordered_map<std::string, Signal> &inputs,
            SimContext &ctx) {
  const Signal &opt_in = inputs.at("opt_in");

  // Get electrical input
  Eigen::VectorXd v;
  if (inputs.contains("elec_in")) {
    const Signal &elec_in = inputs.at("elec_in");
    v.resize(elec_in.n_samples());
    for (Eigen::Index i = 0; i < elec_in.n_samples(); ++i) {
      v[i] = elec_in.data[i].real();
    }
  } else {
    v = Eigen::VectorXd::Zero(opt_in.n_samples());
  }

  double vpi = get_param("Vpi", 3.5);
  double phi_bias = get_param("phi_bias", 0.0);

  bool nonideal_enable = get_nonideal("enable", false);
  double bias_error = 0.0;
  double loss_db = 0.0;

  if (nonideal_enable) {
    double vpi_error = get_nonideal("vpi_error_pct", 0.0);
    vpi *= (1.0 + vpi_error / 100.0);

    bias_error = get_nonideal("bias_error_rad", 0.0);
    loss_db = get_nonideal("loss_db", 0.0);

    double drive_noise_rms = get_nonideal("drive_noise_rms", 0.0);
    if (drive_noise_rms > 0.0) {
      v += drive_noise_rms * ctx.randn(static_cast<int>(v.size()));
    }
  }

  const Eigen::Index n = opt_in.n_samples();
  Eigen::VectorXcd data(n);

  for (Eigen::Index i = 0; i < n; ++i) {
    double phi = (phi_bias + bias_error) + M_PI * v[i] / vpi;
    std::complex<double> phase_term = std::exp(std::complex<double>(0.0, phi));
    data[i] = opt_in.data[i] * phase_term;
  }

  if (nonideal_enable && loss_db != 0.0) {
    double loss_linear = std::pow(10.0, -loss_db / 20.0);
    data *= loss_linear;
  }

  Signal output(data, opt_in.fs, opt_in.t0);
  output.center_freq = opt_in.center_freq;
  output.pol_mode = opt_in.pol_mode;
  output.meta = opt_in.meta;

  return {{"opt_out", std::move(output)}};
}

std::optional<std::string> PM::port_type(const std::string &port) const {
  if (port == "opt_in" || port == "opt_out")
    return "optical";
  if (port == "elec_in")
    return "electrical";
  return std::nullopt;
}

std::optional<double> PM::estimate_fmax() const {
  if (params_.contains("bandwidth_hz")) {
    double bw = params_["bandwidth_hz"].get<double>();
    if (bw > 0.0)
      return bw;
  }
  return std::nullopt;
}

json PM::describe() const {
  return {
      {"ports",
       {{"opt_in", "optical"},
        {"elec_in", "electrical"},
        {"opt_out", "optical"}}},
      {"spec",
       {{"params",
         {{"Vpi", {{"type", "float"}, {"default", 3.5}, {"unit", "V"}}},
          {"phi_bias", {{"type", "float"}, {"default", 0.0}, {"unit", "rad"}}},
          {"bandwidth_hz",
           {{"type", "float"}, {"default", 0.0}, {"unit", "Hz"}}}}},
        {"nonideal",
         {{"enable", {{"type", "bool"}, {"default", false}}},
          {"loss_db", {{"type", "float"}, {"default", 0.0}, {"unit", "dB"}}},
          {"vpi_error_pct",
           {{"type", "float"}, {"default", 0.0}, {"unit", "%"}}},
          {"drive_noise_rms",
           {{"type", "float"}, {"default", 0.0}, {"unit", "V"}}},
          {"bias_error_rad",
           {{"type", "float"}, {"default", 0.0}, {"unit", "rad"}}}}}}}};
}

REGISTER_BLOCK(PM, "PM");

} // namespace photonflow
