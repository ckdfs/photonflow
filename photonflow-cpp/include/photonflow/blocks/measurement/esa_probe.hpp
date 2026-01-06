/**
 * @file esa_probe.hpp
 * @brief Electrical Spectrum Analyzer probe.
 *
 * Corresponds to: backend/src/photonflow/blocks/measurement/esa_probe.py
 */

#pragma once

#include "photonflow/blocks/base_block.hpp"

namespace photonflow {

/**
 * @class ESAProbe
 * @brief Electrical spectrum analyzer probe for measuring electrical signals.
 */
class ESAProbe : public BaseBlock {
public:
  ESAProbe(const std::string &id, const json &params, const json &nonideal);

  std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> &inputs,
          SimContext &ctx) override;

  [[nodiscard]] std::optional<std::string>
  port_type(const std::string &port) const override;

  [[nodiscard]] std::string block_type() const override { return "ESAProbe"; }

  [[nodiscard]] json describe() const override;
};

} // namespace photonflow
