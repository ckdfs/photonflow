/**
 * @file coupler.hpp
 * @brief 2x2 Optical coupler block.
 *
 * Corresponds to: backend/src/photonflow/blocks/optical/coupler.py
 */

#pragma once

#include "photonflow/blocks/base_block.hpp"

namespace photonflow {

/**
 * @class Coupler
 * @brief 2x2 optical coupler/splitter.
 *
 * Transfer matrix:
 *   [out1]   [  sqrt(k)     j*sqrt(1-k) ] [in1]
 *   [out2] = [ j*sqrt(1-k)    sqrt(k)   ] [in2]
 *
 * Parameters:
 * - split_ratio: Power splitting ratio k (default: 0.5 = 3dB coupler)
 */
class Coupler : public BaseBlock {
public:
  Coupler(const std::string &id, const json &params = json::object(),
          const json &nonideal = json::object());

  std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> &inputs,
          SimContext &ctx) override;

  [[nodiscard]] std::optional<std::string>
  port_type(const std::string &port) const override;
  [[nodiscard]] std::string block_type() const override { return "Coupler"; }
  [[nodiscard]] json describe() const override;
};

} // namespace photonflow
