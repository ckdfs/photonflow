/**
 * @file rf_source.hpp
 * @brief RF sine wave source block.
 *
 * Corresponds to: backend/src/photonflow/blocks/electrical/rf_source.py
 */

#pragma once

#include "photonflow/blocks/base_block.hpp"

namespace photonflow {

/**
 * @class RFSource
 * @brief Generates an RF sinusoidal electrical signal.
 *
 * Parameters:
 * - freq_hz: Frequency in Hz (default: 1e9)
 * - amplitude: Amplitude in V (default: 1.0)
 * - phase: Initial phase in radians (default: 0.0)
 * - offset: DC offset in V (default: 0.0)
 */
class RFSource : public BaseBlock {
public:
  RFSource(const std::string &id, const json &params = json::object(),
           const json &nonideal = json::object());

  std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> &inputs,
          SimContext &ctx) override;

  [[nodiscard]] std::optional<std::string>
  port_type(const std::string &port) const override;
  [[nodiscard]] std::string block_type() const override { return "RFSource"; }
  [[nodiscard]] json describe() const override;
  [[nodiscard]] std::optional<double> estimate_fmax() const override;
};

} // namespace photonflow
