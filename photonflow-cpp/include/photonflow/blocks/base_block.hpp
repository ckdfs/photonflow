/**
 * @file base_block.hpp
 * @brief Abstract base class for all simulation blocks.
 *
 * Corresponds to: backend/src/photonflow/blocks/base.py
 */

#pragma once

#include "photonflow/core/signal.hpp"
#include "photonflow/core/sim_context.hpp"

#include <nlohmann/json.hpp>
#include <optional>
#include <string>
#include <unordered_map>

namespace photonflow {

using json = nlohmann::json;

/**
 * @class BaseBlock
 * @brief Abstract base class for simulation blocks.
 *
 * All optical, electrical, and detector blocks inherit from this class.
 * Subclasses must implement the process() method.
 */
class BaseBlock {
public:
  /**
   * @brief Construct a new BaseBlock.
   * @param id Unique block identifier
   * @param params Block parameters as JSON
   * @param nonideal Non-ideal parameters as JSON
   */
  BaseBlock(const std::string &id, const json &params = json::object(),
            const json &nonideal = json::object());

  virtual ~BaseBlock() = default;

  // Prevent copying but allow moving
  BaseBlock(const BaseBlock &) = delete;
  BaseBlock &operator=(const BaseBlock &) = delete;
  BaseBlock(BaseBlock &&) = default;
  BaseBlock &operator=(BaseBlock &&) = default;

  /// Get the block ID
  [[nodiscard]] const std::string &id() const { return id_; }

  /// Get the block parameters
  [[nodiscard]] const json &params() const { return params_; }

  /// Get the non-ideal parameters
  [[nodiscard]] const json &nonideal() const { return nonideal_; }

  /**
   * @brief Process input signals and produce output signals.
   * @param inputs Map of port names to input signals
   * @param ctx Simulation context
   * @return Map of port names to output signals
   */
  virtual std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> &inputs,
          SimContext &ctx) = 0;

  /**
   * @brief Get the type of a port.
   * @param port Port name
   * @return Port type ("optical", "electrical") or nullopt if not found
   */
  [[nodiscard]] virtual std::optional<std::string>
  port_type(const std::string &port) const = 0;

  /**
   * @brief Get the block type name.
   * @return Block type string (e.g., "Laser", "MZM")
   */
  [[nodiscard]] virtual std::string block_type() const = 0;

  /**
   * @brief Get block description including ports and parameters.
   * @return JSON object with block metadata
   */
  [[nodiscard]] virtual json describe() const = 0;

  /**
   * @brief Estimate maximum frequency for this block.
   * @return Maximum frequency in Hz, or nullopt if not applicable
   */
  [[nodiscard]] virtual std::optional<double> estimate_fmax() const {
    return std::nullopt;
  }

protected:
  std::string id_;
  json params_;
  json nonideal_;

  /**
   * @brief Get a parameter with default value.
   * @tparam T Value type
   * @param key Parameter key
   * @param default_value Default if key not found
   * @return Parameter value
   */
  template <typename T>
  T get_param(const std::string &key, const T &default_value) const {
    if (params_.contains(key)) {
      const auto &val = params_[key];
      if constexpr (std::is_arithmetic_v<T>) {
        if (val.is_string()) {
          try {
            if constexpr (std::is_floating_point_v<T>) {
              return static_cast<T>(std::stod(val.get<std::string>()));
            } else {
              return static_cast<T>(std::stoll(val.get<std::string>()));
            }
          } catch (...) {
            // Fallthrough to normal get (will throw type_error)
          }
        }
      }
      return val.get<T>();
    }
    return default_value;
  }

  /**
   * @brief Get a non-ideal parameter with default value.
   * @tparam T Value type
   * @param key Parameter key
   * @param default_value Default if key not found
   * @return Parameter value
   */
  template <typename T>
  T get_nonideal(const std::string &key, const T &default_value) const {
    if (nonideal_.contains(key)) {
      const auto &val = nonideal_[key];
      if constexpr (std::is_arithmetic_v<T>) {
        if (val.is_string()) {
          try {
            if constexpr (std::is_floating_point_v<T>) {
              return static_cast<T>(std::stod(val.get<std::string>()));
            } else {
              return static_cast<T>(std::stoll(val.get<std::string>()));
            }
          } catch (...) {
            // Fallthrough
          }
        }
      }
      return val.get<T>();
    }
    return default_value;
  }
};

} // namespace photonflow
