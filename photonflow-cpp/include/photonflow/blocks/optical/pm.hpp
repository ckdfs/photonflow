/**
 * @file pm.hpp
 * @brief Phase Modulator block.
 *
 * Corresponds to: backend/src/photonflow/blocks/optical/pm.py
 */

#pragma once

#include "photonflow/blocks/base_block.hpp"

namespace photonflow {

/**
 * @class PM
 * @brief Electro-optic phase modulator.
 *
 * Transfer function: E_out = E_in * exp(i * phi)
 * where phi = phi_bias + pi * V / Vpi
 */
class PM : public BaseBlock {
public:
  PM(const std::string &id, const json &params = json::object(),
     const json &nonideal = json::object());

  std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> &inputs,
          SimContext &ctx) override;

  [[nodiscard]] std::optional<std::string>
  port_type(const std::string &port) const override;
  [[nodiscard]] std::string block_type() const override { return "PM"; }
  [[nodiscard]] json describe() const override;
  [[nodiscard]] std::optional<double> estimate_fmax() const override;
};

} // namespace photonflow
