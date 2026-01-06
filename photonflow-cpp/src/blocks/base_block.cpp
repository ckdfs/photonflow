/**
 * @file base_block.cpp
 * @brief BaseBlock class implementation.
 */

#include "photonflow/blocks/base_block.hpp"

namespace photonflow {

BaseBlock::BaseBlock(const std::string &id, const json &params,
                     const json &nonideal)
    : id_(id), params_(params), nonideal_(nonideal) {}

} // namespace photonflow
