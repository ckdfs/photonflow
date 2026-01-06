/**
 * @file photodetector.hpp
 * @brief Photodiode detector block.
 *
 * Corresponds to: backend/src/photonflow/blocks/detectors/pd.py
 */

#pragma once

#include "photonflow/blocks/base_block.hpp"

namespace photonflow {

/**
 * @class PD
 * @brief Photodiode detector - converts optical power to electrical current.
 *
 * Transfer function: I = R * P_opt
 *
 * Parameters:
 * - responsivity: A/W (default: 1.0)
 * - bandwidth_hz: Electrical bandwidth (default: 0 = no filtering)
 */
class PD : public BaseBlock {
public:
  PD(const std::string &id, const json &params = json::object(),
     const json &nonideal = json::object());

  std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> &inputs,
          SimContext &ctx) override;

  [[nodiscard]] std::optional<std::string>
  port_type(const std::string &port) const override;
  [[nodiscard]] std::string block_type() const override { return "PD"; }
  [[nodiscard]] json describe() const override;
  [[nodiscard]] std::optional<double> estimate_fmax() const override;

private:
  static Eigen::VectorXd compute_noise(const Eigen::VectorXd &current,
                                       double bandwidth, bool shot_noise,
                                       bool thermal_noise,
                                       double load_resistance,
                                       double temperature_k, SimContext &ctx);
};

} // namespace photonflow
