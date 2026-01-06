/**
 * @file attenuator.hpp
 * @brief Optical attenuator block.
 *
 * Corresponds to: backend/src/photonflow/blocks/optical/attenuator.py
 */

#pragma once

#include "photonflow/blocks/base_block.hpp"

namespace photonflow {

/**
 * @class Attenuator
 * @brief Applies optical loss to the signal.
 *
 * Parameters:
 * - loss_db: Attenuation in dB (default: 0.0)
 */
class Attenuator : public BaseBlock {
public:
  Attenuator(const std::string &id, const json &params = json::object(),
             const json &nonideal = json::object());

  std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> &inputs,
          SimContext &ctx) override;

  [[nodiscard]] std::optional<std::string>
  port_type(const std::string &port) const override;
  [[nodiscard]] std::string block_type() const override { return "Attenuator"; }
  [[nodiscard]] json describe() const override;
};

} // namespace photonflow
