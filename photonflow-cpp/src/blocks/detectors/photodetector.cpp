/**
 * @file photodetector.cpp
 * @brief Photodiode detector block implementation.
 */

#include "photonflow/blocks/detectors/photodetector.hpp"
#include "photonflow/blocks/block_registry.hpp"

#include <algorithm>
#include <cmath>


namespace photonflow {

// Physical constants
constexpr double ELECTRON_CHARGE = 1.602176634e-19; // Coulombs
constexpr double BOLTZMANN_CONST = 1.380649e-23;    // J/K

PD::PD(const std::string &id, const json &params, const json &nonideal)
    : BaseBlock(id, params, nonideal) {}

std::unordered_map<std::string, Signal>
PD::process(const std::unordered_map<std::string, Signal> &inputs,
            SimContext &ctx) {
  const Signal &opt_in = inputs.at("opt_in");
  double responsivity = get_param("responsivity", 1.0);

  // Calculate optical power: |E|^2
  const Eigen::Index n = opt_in.n_samples();
  Eigen::VectorXd power(n);

  if (opt_in.pol_mode == "jones" && opt_in.data.rows() == 2) {
    // Jones vector: sum power from both polarizations
    // This would require 2D data handling - simplified for scalar
    for (Eigen::Index i = 0; i < n; ++i) {
      power[i] = std::norm(opt_in.data[i]);
    }
  } else {
    for (Eigen::Index i = 0; i < n; ++i) {
      power[i] = std::norm(opt_in.data[i]); // |E|^2
    }
  }

  // Non-ideal effects
  bool nonideal_enable = get_nonideal("enable", false);
  double dark_current = 0.0;
  double bandwidth = ctx.fs() / 2.0;
  bool shot_noise = false;
  bool thermal_noise = false;
  double load_resistance = 50.0;
  double temperature_k = 300.0;
  double saturation_current = 0.0;
  double extra_noise_rms = 0.0;

  if (nonideal_enable) {
    double resp_error = get_nonideal("responsivity_error_pct", 0.0);
    responsivity *= (1.0 + resp_error / 100.0);

    dark_current = get_nonideal("dark_current", 0.0);
    shot_noise = get_nonideal("shot_noise", true);
    thermal_noise = get_nonideal("thermal_noise", true);
    load_resistance = get_nonideal("load_resistance", 50.0);
    temperature_k = get_nonideal("temperature_k", 300.0);
    saturation_current = get_nonideal("saturation_current", 0.0);
    extra_noise_rms = get_nonideal("noise_current_rms", 0.0);
  }

  // Get bandwidth from params
  double bw_param = get_param("bandwidth_hz", 0.0);
  if (bw_param > 0.0 && bw_param < ctx.fs() / 2.0) {
    bandwidth = bw_param;
  }

  // Convert power to current
  Eigen::VectorXd current = responsivity * power;

  // Add dark current
  if (dark_current != 0.0) {
    current = current.array() + dark_current;
  }

  // Apply saturation
  if (saturation_current > 0.0) {
    for (Eigen::Index i = 0; i < n; ++i) {
      current[i] = std::min(current[i], saturation_current);
    }
  }

  // Add shot and thermal noise
  if (nonideal_enable && (shot_noise || thermal_noise)) {
    Eigen::VectorXd noise =
        compute_noise(current, bandwidth, shot_noise, thermal_noise,
                      load_resistance, temperature_k, ctx);
    current += noise;
  }

  // Add extra user-specified noise
  if (extra_noise_rms > 0.0) {
    current += extra_noise_rms * ctx.randn(static_cast<int>(n));
  }

  // Convert to complex signal (electrical)
  Eigen::VectorXcd data(n);
  for (Eigen::Index i = 0; i < n; ++i) {
    data[i] = std::complex<double>(current[i], 0.0);
  }

  Signal output(data, opt_in.fs, opt_in.t0);
  output.pol_mode = "scalar";

  return {{"elec_out", std::move(output)}};
}

Eigen::VectorXd PD::compute_noise(const Eigen::VectorXd &current,
                                  double bandwidth, bool shot_noise,
                                  bool thermal_noise, double load_resistance,
                                  double temperature_k, SimContext &ctx) {
  double mean_current = current.mean();

  double sigma_shot = 0.0;
  if (shot_noise && mean_current > 0.0) {
    sigma_shot = std::sqrt(2.0 * ELECTRON_CHARGE * mean_current * bandwidth);
  }

  double sigma_thermal = 0.0;
  if (thermal_noise) {
    sigma_thermal = std::sqrt(4.0 * BOLTZMANN_CONST * temperature_k *
                              bandwidth / load_resistance);
  }

  double sigma_total =
      std::sqrt(sigma_shot * sigma_shot + sigma_thermal * sigma_thermal);

  if (sigma_total == 0.0) {
    return Eigen::VectorXd::Zero(current.size());
  }

  return sigma_total * ctx.randn(static_cast<int>(current.size()));
}

std::optional<std::string> PD::port_type(const std::string &port) const {
  if (port == "opt_in")
    return "optical";
  if (port == "elec_out")
    return "electrical";
  return std::nullopt;
}

std::optional<double> PD::estimate_fmax() const {
  if (params_.contains("bandwidth_hz")) {
    double bw = params_["bandwidth_hz"].get<double>();
    if (bw > 0.0)
      return bw;
  }
  return std::nullopt;
}

json PD::describe() const {
  return {{"ports", {{"opt_in", "optical"}, {"elec_out", "electrical"}}},
          {"spec",
           {{"params",
             {{"responsivity",
               {{"type", "float"}, {"default", 1.0}, {"unit", "A/W"}}},
              {"bandwidth_hz",
               {{"type", "float"}, {"default", 0.0}, {"unit", "Hz"}}}}},
            {"nonideal",
             {{"enable", {{"type", "bool"}, {"default", false}}},
              {"shot_noise", {{"type", "bool"}, {"default", true}}},
              {"thermal_noise", {{"type", "bool"}, {"default", true}}},
              {"load_resistance",
               {{"type", "float"}, {"default", 50.0}, {"unit", "Ohm"}}},
              {"temperature_k",
               {{"type", "float"}, {"default", 300.0}, {"unit", "K"}}},
              {"dark_current",
               {{"type", "float"}, {"default", 0.0}, {"unit", "A"}}},
              {"responsivity_error_pct",
               {{"type", "float"}, {"default", 0.0}, {"unit", "%"}}},
              {"saturation_current",
               {{"type", "float"}, {"default", 0.0}, {"unit", "A"}}},
              {"noise_current_rms",
               {{"type", "float"}, {"default", 0.0}, {"unit", "A"}}}}}}}};
}

REGISTER_BLOCK(PD, "PD");

} // namespace photonflow
