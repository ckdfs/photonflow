/**
 * @file osa_probe.hpp
 * @brief Optical Spectrum Analyzer probe.
 *
 * Corresponds to: backend/src/photonflow/blocks/measurement/osa_probe.py
 */

#pragma once

#include "photonflow/blocks/base_block.hpp"

namespace photonflow {

/**
 * @class OSAProbe
 * @brief Optical spectrum analyzer probe for measuring optical signals.
 *
 * This is a measurement point that captures optical signal data for
 * spectrum analysis. The actual FFT processing happens in the output handler.
 */
class OSAProbe : public BaseBlock {
public:
  OSAProbe(const std::string &id, const json &params, const json &nonideal);

  std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> &inputs,
          SimContext &ctx) override;

  [[nodiscard]] std::optional<std::string>
  port_type(const std::string &port) const override;

  [[nodiscard]] std::string block_type() const override { return "OSAProbe"; }

  [[nodiscard]] json describe() const override;
};

} // namespace photonflow
