/**
 * @file mzm.hpp
 * @brief Mach-Zehnder Modulator block.
 *
 * Corresponds to: backend/src/photonflow/blocks/optical/mzm.py
 */

#pragma once

#include "photonflow/blocks/base_block.hpp"

namespace photonflow {

/**
 * @class MZM
 * @brief Mach-Zehnder intensity/phase modulator.
 *
 * Transfer function: E_out = 0.5 * E_in * (exp(i*phi1) + exp(i*phi2))
 *
 * Parameters:
 * - Vpi: Half-wave voltage in V (default: 3.5)
 * - phi_bias: DC bias phase in radians (default: 0.0)
 * - drive_mode: "push_pull" or "single_arm" (default: push_pull)
 */
class MZM : public BaseBlock {
public:
  MZM(const std::string &id, const json &params = json::object(),
      const json &nonideal = json::object());

  std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> &inputs,
          SimContext &ctx) override;

  [[nodiscard]] std::optional<std::string>
  port_type(const std::string &port) const override;
  [[nodiscard]] std::string block_type() const override { return "MZM"; }
  [[nodiscard]] json describe() const override;
  [[nodiscard]] std::optional<double> estimate_fmax() const override;
};

} // namespace photonflow
