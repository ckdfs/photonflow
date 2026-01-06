/**
 * @file laser.hpp
 * @brief Laser source block.
 * 
 * Corresponds to: backend/src/photonflow/blocks/optical/laser.py
 */

#pragma once

#include "photonflow/blocks/base_block.hpp"

namespace photonflow {

/**
 * @class Laser
 * @brief Generates an optical carrier signal.
 * 
 * Parameters:
 * - power_dbm: Output power in dBm (default: 0.0)
 * - center_freq_hz: Optical center frequency in Hz (default: 193.1e12)
 * - phase0: Initial phase in radians (default: 0.0)
 * 
 * Non-ideal parameters:
 * - linewidth_hz: Laser linewidth for phase noise
 * - rin_db_per_hz: Relative intensity noise
 * - power_error_db: Power deviation
 * - freq_offset_hz: Frequency offset
 * - phase_noise_rms: Random phase noise
 */
class Laser : public BaseBlock {
public:
    Laser(const std::string& id, 
          const json& params = json::object(),
          const json& nonideal = json::object());

    std::unordered_map<std::string, Signal> process(
        const std::unordered_map<std::string, Signal>& inputs,
        SimContext& ctx) override;

    [[nodiscard]] std::optional<std::string> port_type(const std::string& port) const override;
    [[nodiscard]] std::string block_type() const override { return "Laser"; }
    [[nodiscard]] json describe() const override;
};

} // namespace photonflow
