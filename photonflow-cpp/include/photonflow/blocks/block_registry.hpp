/**
 * @file block_registry.hpp
 * @brief Block factory and registry system.
 *
 * Corresponds to: backend/src/photonflow/blocks/base.py (BlockRegistry)
 */

#pragma once

#include "photonflow/blocks/base_block.hpp"

#include <functional>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

namespace photonflow {

/**
 * @brief Factory function type for creating blocks.
 */
using BlockFactory = std::function<std::unique_ptr<BaseBlock>(
    const std::string &id, const json &params, const json &nonideal)>;

/**
 * @class BlockRegistry
 * @brief Singleton registry for block types.
 *
 * Manages registration and creation of block types. Uses the factory
 * pattern to instantiate blocks by type name.
 */
class BlockRegistry {
public:
  /**
   * @brief Get the singleton instance.
   * @return Reference to the registry
   */
  static BlockRegistry &instance();

  /**
   * @brief Register a block type with a factory function.
   * @param name Block type name
   * @param factory Factory function
   */
  void register_factory(const std::string &name, BlockFactory factory);

  /**
   * @brief Register a block type using its class.
   * @tparam T Block class type
   * @param name Block type name
   */
  template <typename T> void register_block(const std::string &name) {
    register_factory(name, [](const std::string &id, const json &params,
                              const json &nonideal) {
      return std::make_unique<T>(id, params, nonideal);
    });
  }

  /**
   * @brief Create a block instance.
   * @param type Block type name
   * @param id Block instance ID
   * @param params Block parameters
   * @param nonideal Non-ideal parameters
   * @return Unique pointer to created block, or nullptr if type not found
   */
  [[nodiscard]] std::unique_ptr<BaseBlock>
  create(const std::string &type, const std::string &id,
         const json &params = json::object(),
         const json &nonideal = json::object()) const;

  /**
   * @brief List all registered block types.
   * @return Sorted vector of type names
   */
  [[nodiscard]] std::vector<std::string> list_types() const;

  /**
   * @brief Check if a block type is registered.
   * @param name Block type name
   * @return true if registered
   */
  [[nodiscard]] bool has_type(const std::string &name) const;

  /**
   * @brief Get block specs for all registered types.
   * @return JSON object mapping type names to descriptions
   */
  [[nodiscard]] json get_specs() const;

private:
  BlockRegistry() = default;
  ~BlockRegistry() = default;

  // Prevent copying
  BlockRegistry(const BlockRegistry &) = delete;
  BlockRegistry &operator=(const BlockRegistry &) = delete;

  std::unordered_map<std::string, BlockFactory> factories_;
};

/**
 * @brief Helper macro for automatic block registration.
 *
 * Usage: REGISTER_BLOCK(LaserBlock, "Laser")
 */
#define REGISTER_BLOCK(ClassName, BlockTypeName)                               \
  namespace {                                                                  \
  struct ClassName##Registrar {                                                \
    ClassName##Registrar() {                                                   \
      ::photonflow::BlockRegistry::instance().register_block<ClassName>(       \
          BlockTypeName);                                                      \
    }                                                                          \
  };                                                                           \
  [[maybe_unused]] static ClassName##Registrar ClassName##_registrar_;         \
  }

} // namespace photonflow
