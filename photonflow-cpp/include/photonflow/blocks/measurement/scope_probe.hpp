/**
 * @file scope_probe.hpp
 * @brief Oscilloscope probe.
 *
 * Corresponds to: backend/src/photonflow/blocks/measurement/scope_probe.py
 */

#pragma once

#include "photonflow/blocks/base_block.hpp"

namespace photonflow {

/**
 * @class ScopeProbe
 * @brief Oscilloscope probe for time-domain signal measurement.
 */
class ScopeProbe : public BaseBlock {
public:
  ScopeProbe(const std::string &id, const json &params, const json &nonideal);

  std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> &inputs,
          SimContext &ctx) override;

  [[nodiscard]] std::optional<std::string>
  port_type(const std::string &port) const override;

  [[nodiscard]] std::string block_type() const override { return "ScopeProbe"; }

  [[nodiscard]] json describe() const override;
};

} // namespace photonflow
