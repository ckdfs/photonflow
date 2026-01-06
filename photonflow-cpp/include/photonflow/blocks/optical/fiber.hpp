/**
 * @file fiber.hpp
 * @brief Optical fiber propagation block with SSFM.
 *
 * Corresponds to: backend/src/photonflow/blocks/optical/fiber.py
 */

#pragma once

#include "photonflow/blocks/base_block.hpp"

#include <unsupported/Eigen/FFT>

namespace photonflow {

/**
 * @class OpticalFiber
 * @brief Simulates optical fiber propagation using Split-Step Fourier Method.
 *
 * Implements:
 * - Linear effects: attenuation (alpha), dispersion (beta2, beta3)
 * - Nonlinear effects: self-phase modulation (gamma)
 *
 * Parameters:
 * - length_m: Fiber length in meters
 * - alpha_db_per_km: Attenuation coefficient
 * - beta2_s2_per_m: Group velocity dispersion parameter
 * - beta3_s3_per_m: Third-order dispersion
 * - ssfm_steps: Number of SSFM steps
 */
class OpticalFiber : public BaseBlock {
public:
  OpticalFiber(const std::string &id, const json &params = json::object(),
               const json &nonideal = json::object());

  std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> &inputs,
          SimContext &ctx) override;

  [[nodiscard]] std::optional<std::string>
  port_type(const std::string &port) const override;
  [[nodiscard]] std::string block_type() const override {
    return "OpticalFiber";
  }
  [[nodiscard]] json describe() const override;

private:
  // Apply linear propagation (dispersion + attenuation) in frequency domain
  static void apply_linear(Eigen::VectorXcd &data, double fs, double seg_len,
                           double alpha_power, double beta2, double beta3);

  // Apply nonlinear phase shift (SPM) in time domain
  static void apply_nonlinear(Eigen::VectorXcd &data, double seg_len,
                              double gamma);
};

} // namespace photonflow
