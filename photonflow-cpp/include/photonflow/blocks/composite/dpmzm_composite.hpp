/**
 * @file dpmzm_composite.hpp
 * @brief DP-MZM Composite block (placeholder for frontend compatibility).
 */

#pragma once

#include "photonflow/blocks/base_block.hpp"

namespace photonflow {

/**
 * @class DPMZMComposite
 * @brief Dual-Parallel MZM composite block.
 */
class DPMZMComposite : public BaseBlock {
public:
  DPMZMComposite(const std::string &id, const json &params,
                 const json &nonideal);

  std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> &inputs,
          SimContext &ctx) override;

  [[nodiscard]] std::optional<std::string>
  port_type(const std::string &port) const override;

  [[nodiscard]] std::string block_type() const override {
    return "DPMZMComposite";
  }

  [[nodiscard]] json describe() const override;
};

} // namespace photonflow
