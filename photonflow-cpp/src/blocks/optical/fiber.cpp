/**
 * @file fiber.cpp
 * @brief Optical fiber propagation with SSFM implementation.
 */

#include "photonflow/blocks/optical/fiber.hpp"
#include "photonflow/blocks/block_registry.hpp"

#include <algorithm>
#include <cmath>
#include <complex>

namespace photonflow {

OpticalFiber::OpticalFiber(const std::string &id, const json &params,
                           const json &nonideal)
    : BaseBlock(id, params, nonideal) {}

std::unordered_map<std::string, Signal>
OpticalFiber::process(const std::unordered_map<std::string, Signal> &inputs,
                      SimContext & /*ctx*/) {
  const Signal &opt_in = inputs.at("opt_in");

  // Extract parameters
  double length_m = get_param("length_m", 0.0);
  double alpha_db_per_km = get_param("alpha_db_per_km", 0.0);
  double beta2 = get_param("beta2_s2_per_m", 0.0);
  double beta3 = get_param("beta3_s3_per_m", 0.0);
  int ssfm_steps = std::max(1, get_param("ssfm_steps", 1));

  // Non-ideal: nonlinear coefficient
  bool nonideal_enable = get_nonideal("enable", false);
  double gamma = 0.0;
  if (nonideal_enable) {
    gamma = get_nonideal("nonlin_gamma_w_inv_m", 0.0);
  }

  // Check if any effect is present
  bool has_linear =
      (alpha_db_per_km != 0.0) || (beta2 != 0.0) || (beta3 != 0.0);
  bool has_nonlinear = (gamma != 0.0);

  // If no length or no effects, just pass through
  if (length_m <= 0.0 || (!has_linear && !has_nonlinear)) {
    return {{"opt_out", opt_in.clone()}};
  }

  // Convert alpha from dB/km to power coefficient (1/m)
  double alpha_power = 0.0;
  if (alpha_db_per_km != 0.0) {
    alpha_power = std::log(10.0) / 10.0 * (alpha_db_per_km / 1000.0);
  }

  Eigen::VectorXcd data = opt_in.data;

  if (gamma != 0.0 && ssfm_steps > 1) {
    // Full SSFM with symmetrized split-step
    double dz = length_m / ssfm_steps;

    for (int step = 0; step < ssfm_steps; ++step) {
      // Half linear step
      apply_linear(data, opt_in.fs, dz / 2.0, alpha_power, beta2, beta3);
      // Full nonlinear step
      apply_nonlinear(data, dz, gamma);
      // Half linear step
      apply_linear(data, opt_in.fs, dz / 2.0, alpha_power, beta2, beta3);
    }
  } else {
    // Linear propagation only (or single-step approximation)
    apply_linear(data, opt_in.fs, length_m, alpha_power, beta2, beta3);

    if (gamma != 0.0) {
      // Apply nonlinear with effective length
      double l_eff;
      if (alpha_power != 0.0) {
        l_eff = (1.0 - std::exp(-alpha_power * length_m)) / alpha_power;
      } else {
        l_eff = length_m;
      }
      apply_nonlinear(data, l_eff, gamma);
    }
  }

  Signal output(data, opt_in.fs, opt_in.t0);
  output.center_freq = opt_in.center_freq;
  output.pol_mode = opt_in.pol_mode;
  output.meta = opt_in.meta;

  return {{"opt_out", std::move(output)}};
}

void OpticalFiber::apply_linear(Eigen::VectorXcd &data, double fs,
                                double seg_len, double alpha_power,
                                double beta2, double beta3) {
  // Thread-local FFT object to avoid member variable issues
  thread_local Eigen::FFT<double> fft;

  const Eigen::Index n = data.size();

  // Generate frequency vector (FFT frequencies)
  Eigen::VectorXd freq(n);
  for (Eigen::Index i = 0; i < n; ++i) {
    if (i <= n / 2) {
      freq[i] = static_cast<double>(i) * fs / n;
    } else {
      freq[i] = static_cast<double>(i - n) * fs / n;
    }
  }

  // Angular frequency
  Eigen::VectorXd omega = 2.0 * M_PI * freq;

  // Compute transfer function H(omega)
  // H = exp(j * phase) * exp(-alpha * L / 2)
  // phase = -0.5 * beta2 * L * omega^2 - (1/6) * beta3 * L * omega^3

  Eigen::VectorXcd H(n);
  for (Eigen::Index i = 0; i < n; ++i) {
    double w = omega[i];
    double phase = 0.0;

    if (beta2 != 0.0) {
      phase += -0.5 * beta2 * seg_len * w * w;
    }
    if (beta3 != 0.0) {
      phase += -(1.0 / 6.0) * beta3 * seg_len * w * w * w;
    }

    std::complex<double> h = std::exp(std::complex<double>(0.0, phase));

    // Apply attenuation (field amplitude)
    if (alpha_power != 0.0) {
      h *= std::exp(-alpha_power * seg_len / 2.0);
    }

    H[i] = h;
  }

  // FFT -> multiply by H -> IFFT
  Eigen::VectorXcd data_freq(n);
  fft.fwd(data_freq, data);

  for (Eigen::Index i = 0; i < n; ++i) {
    data_freq[i] *= H[i];
  }

  fft.inv(data, data_freq);
}

void OpticalFiber::apply_nonlinear(Eigen::VectorXcd &data, double seg_len,
                                   double gamma) {
  if (gamma == 0.0)
    return;

  // Self-phase modulation: E_out = E_in * exp(j * gamma * |E|^2 * L)
  for (Eigen::Index i = 0; i < data.size(); ++i) {
    double power = std::norm(data[i]); // |E|^2
    double phi_nl = gamma * seg_len * power;
    data[i] *= std::exp(std::complex<double>(0.0, phi_nl));
  }
}

std::optional<std::string>
OpticalFiber::port_type(const std::string &port) const {
  if (port == "opt_in" || port == "opt_out")
    return "optical";
  return std::nullopt;
}

json OpticalFiber::describe() const {
  return {
      {"ports", {{"opt_in", "optical"}, {"opt_out", "optical"}}},
      {"spec",
       {{"params",
         {{"length_m", {{"type", "float"}, {"default", 0.0}, {"unit", "m"}}},
          {"alpha_db_per_km",
           {{"type", "float"}, {"default", 0.0}, {"unit", "dB/km"}}},
          {"beta2_s2_per_m",
           {{"type", "float"}, {"default", 0.0}, {"unit", "s^2/m"}}},
          {"beta3_s3_per_m",
           {{"type", "float"}, {"default", 0.0}, {"unit", "s^3/m"}}},
          {"ssfm_steps", {{"type", "int"}, {"default", 1}}}}},
        {"nonideal",
         {{"enable", {{"type", "bool"}, {"default", false}}},
          {"nonlin_gamma_w_inv_m",
           {{"type", "float"}, {"default", 0.0}, {"unit", "1/W/m"}}}}}}}};
}

REGISTER_BLOCK(OpticalFiber, "OpticalFiber");

} // namespace photonflow
