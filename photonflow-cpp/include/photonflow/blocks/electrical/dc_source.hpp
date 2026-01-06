/**
 * @file dc_source.hpp
 * @brief DC bias source block.
 *
 * Corresponds to: backend/src/photonflow/blocks/electrical/dc_source.py
 */

#pragma once

#include "photonflow/blocks/base_block.hpp"

namespace photonflow {

/**
 * @class DCSource
 * @brief Generates a constant DC voltage signal.
 *
 * Parameters:
 * - voltage: DC voltage in V (default: 0.0)
 */
class DCSource : public BaseBlock {
public:
  DCSource(const std::string &id, const json &params = json::object(),
           const json &nonideal = json::object());

  std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> &inputs,
          SimContext &ctx) override;

  [[nodiscard]] std::optional<std::string>
  port_type(const std::string &port) const override;
  [[nodiscard]] std::string block_type() const override { return "DCSource"; }
  [[nodiscard]] json describe() const override;
};

} // namespace photonflow
