/**
 * @file mzm_composite.hpp
 * @brief MZM Composite block (placeholder for frontend compatibility).
 *
 * Note: In Python, this is a composite template that expands into multiple
 * blocks. For C++ initial implementation, this is a placeholder that mimics MZM
 * behavior.
 */

#pragma once

#include "photonflow/blocks/base_block.hpp"

namespace photonflow {

/**
 * @class MZMComposite
 * @brief Mach-Zehnder Modulator composite block.
 */
class MZMComposite : public BaseBlock {
public:
  MZMComposite(const std::string &id, const json &params, const json &nonideal);

  std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> &inputs,
          SimContext &ctx) override;

  [[nodiscard]] std::optional<std::string>
  port_type(const std::string &port) const override;

  [[nodiscard]] std::string block_type() const override {
    return "MZMComposite";
  }

  [[nodiscard]] json describe() const override;
};

} // namespace photonflow
