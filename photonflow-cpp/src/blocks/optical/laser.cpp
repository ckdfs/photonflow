/**
 * @file laser.cpp
 * @brief Laser source block implementation.
 */

#include "photonflow/blocks/optical/laser.hpp"
#include "photonflow/blocks/block_registry.hpp"

#include <cmath>
#include <complex>

namespace photonflow {

Laser::Laser(const std::string &id, const json &params, const json &nonideal)
    : BaseBlock(id, params, nonideal) {}

std::unordered_map<std::string, Signal>
Laser::process(const std::unordered_map<std::string, Signal> & /*inputs*/,
               SimContext &ctx) {
  // Extract parameters
  double power_dbm = get_param("power_dbm", 0.0);
  double center_freq = get_param("center_freq_hz", 193.1e12);
  double phase0 = get_param("phase0", 0.0);

  // Convert power to linear scale
  double power_w = 1e-3 * std::pow(10.0, power_dbm / 10.0);
  double amp = std::sqrt(power_w);

  // Check if non-ideal effects are enabled
  bool nonideal_enable = get_nonideal("enable", false);

  if (nonideal_enable) {
    // Power error
    double power_error_db = get_nonideal("power_error_db", 0.0);
    if (power_error_db != 0.0) {
      amp *= std::pow(10.0, power_error_db / 20.0);
    }

    // Frequency offset
    double freq_offset = get_nonideal("freq_offset_hz", 0.0);
    center_freq += freq_offset;
  }

  const int n = ctx.n_samples();
  Eigen::VectorXcd data(n);

  if (nonideal_enable) {
    double linewidth = get_nonideal("linewidth_hz", 0.0);
    double phase_noise_rms = get_nonideal("phase_noise_rms", 0.0);
    double rin_db = get_nonideal("rin_db_per_hz", -150.0);

    // Generate phase array
    Eigen::VectorXd phase = Eigen::VectorXd::Constant(n, phase0);

    // Add random phase noise
    if (phase_noise_rms > 0.0) {
      Eigen::VectorXd noise = ctx.randn(n);
      phase += phase_noise_rms * noise;
    }

    // Add linewidth-induced phase noise (Wiener process)
    if (linewidth > 0.0) {
      double sigma = std::sqrt(2.0 * M_PI * linewidth / ctx.fs());
      Eigen::VectorXd dphi = sigma * ctx.randn(n);
      // Cumulative sum
      for (int i = 1; i < n; ++i) {
        phase[i] = phase[i] + phase[i - 1] + dphi[i];
      }
      phase[0] += dphi[0];
    }

    // Handle RIN (Relative Intensity Noise)
    if (rin_db > -200.0) {
      double rin_linear = std::pow(10.0, rin_db / 10.0);
      double sigma_i = std::sqrt(rin_linear * ctx.fs() / 2.0);
      Eigen::VectorXd intensity_noise = ctx.randn(n);

      for (int i = 0; i < n; ++i) {
        double intensity = power_w * (1.0 + sigma_i * intensity_noise[i]);
        intensity = std::max(intensity, 0.0);
        double amp_i = std::sqrt(intensity);
        data[i] = amp_i * std::exp(std::complex<double>(0.0, phase[i]));
      }
    } else {
      // No RIN
      for (int i = 0; i < n; ++i) {
        data[i] = amp * std::exp(std::complex<double>(0.0, phase[i]));
      }
    }
  } else {
    // Ideal case: pure CW with constant amplitude and phase
    std::complex<double> field =
        amp * std::exp(std::complex<double>(0.0, phase0));
    data.setConstant(field);
  }

  Signal output(data, ctx.fs(), ctx.t0());
  output.center_freq = center_freq;
  output.pol_mode = "scalar";

  return {{"opt_out", std::move(output)}};
}

std::optional<std::string> Laser::port_type(const std::string &port) const {
  if (port == "opt_out")
    return "optical";
  return std::nullopt;
}

json Laser::describe() const {
  return {
      {"ports", {{"opt_out", "optical"}}},
      {"spec",
       {{"params",
         {{"power_dbm", {{"type", "float"}, {"default", 0.0}, {"unit", "dBm"}}},
          {"center_freq_hz",
           {{"type", "float"}, {"default", 193.1e12}, {"unit", "Hz"}}},
          {"phase0", {{"type", "float"}, {"default", 0.0}, {"unit", "rad"}}}}},
        {"nonideal",
         {{"enable", {{"type", "bool"}, {"default", false}}},
          {"linewidth_hz",
           {{"type", "float"}, {"default", 0.0}, {"unit", "Hz"}}},
          {"rin_db_per_hz",
           {{"type", "float"}, {"default", -150.0}, {"unit", "dB/Hz"}}},
          {"power_error_db",
           {{"type", "float"}, {"default", 0.0}, {"unit", "dB"}}},
          {"freq_offset_hz",
           {{"type", "float"}, {"default", 0.0}, {"unit", "Hz"}}},
          {"phase_noise_rms",
           {{"type", "float"}, {"default", 0.0}, {"unit", "rad"}}}}}}}};
}

// Auto-register
REGISTER_BLOCK(Laser, "Laser");

} // namespace photonflow
