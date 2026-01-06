/**
 * @file block_registry.cpp
 * @brief BlockRegistry class implementation.
 */

#include "photonflow/blocks/block_registry.hpp"

#include <algorithm>
#include <spdlog/spdlog.h>

namespace photonflow {

BlockRegistry &BlockRegistry::instance() {
  static BlockRegistry instance;
  return instance;
}

void BlockRegistry::register_factory(const std::string &name,
                                     BlockFactory factory) {
  if (factories_.contains(name)) {
    spdlog::warn("BlockRegistry: Overwriting existing block type '{}'", name);
  }
  factories_[name] = std::move(factory);
  spdlog::debug("BlockRegistry: Registered block type '{}'", name);
}

std::unique_ptr<BaseBlock> BlockRegistry::create(const std::string &type,
                                                 const std::string &id,
                                                 const json &params,
                                                 const json &nonideal) const {
  auto it = factories_.find(type);
  if (it == factories_.end()) {
    spdlog::error("BlockRegistry: Unknown block type '{}'", type);
    return nullptr;
  }
  return it->second(id, params, nonideal);
}

std::vector<std::string> BlockRegistry::list_types() const {
  std::vector<std::string> types;
  types.reserve(factories_.size());
  for (const auto &[name, _] : factories_) {
    types.push_back(name);
  }
  std::sort(types.begin(), types.end());
  return types;
}

bool BlockRegistry::has_type(const std::string &name) const {
  return factories_.contains(name);
}

json BlockRegistry::get_specs() const {
  json specs = json::object();
  for (const auto &[name, factory] : factories_) {
    // Create a temporary instance to get its description
    auto block = factory("_temp", json::object(), json::object());
    if (block) {
      specs[name] = block->describe();
      specs[name]["composite"] = false;
    }
  }
  return specs;
}

} // namespace photonflow
