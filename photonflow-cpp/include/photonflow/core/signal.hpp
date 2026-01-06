/**
 * @file signal.hpp
 * @brief Signal data structure for optical and electrical signals.
 * 
 * Corresponds to: backend/src/photonflow/core/signal.py
 */

#pragma once

#include <Eigen/Dense>
#include <complex>
#include <optional>
#include <string>
#include <unordered_map>

namespace photonflow {

/**
 * @class Signal
 * @brief Represents a time-domain signal (optical or electrical).
 * 
 * The Signal class stores complex-valued time-domain data along with
 * metadata such as sampling rate, time offset, and polarization mode.
 */
class Signal {
public:
    /// Complex time-domain data
    Eigen::VectorXcd data;
    
    /// Sampling rate in Hz
    double fs;
    
    /// Time offset in seconds
    double t0;
    
    /// Optional center frequency for optical signals (Hz)
    std::optional<double> center_freq;
    
    /// Polarization mode: "scalar" or "jones"
    std::string pol_mode;
    
    /// Metadata dictionary
    std::unordered_map<std::string, std::string> meta;

    /**
     * @brief Construct a new Signal.
     * @param data Complex time-domain samples
     * @param fs Sampling rate in Hz
     * @param t0 Time offset in seconds (default: 0.0)
     */
    Signal(const Eigen::VectorXcd& data, double fs, double t0 = 0.0);
    
    /// Default constructor
    Signal() : fs(0.0), t0(0.0), pol_mode("scalar") {}
    
    /// Copy constructor
    Signal(const Signal& other) = default;
    
    /// Move constructor
    Signal(Signal&& other) noexcept = default;
    
    /// Copy assignment
    Signal& operator=(const Signal& other) = default;
    
    /// Move assignment
    Signal& operator=(Signal&& other) noexcept = default;

    /**
     * @brief Create a deep copy of this signal.
     * @return A new Signal with copied data
     */
    [[nodiscard]] Signal clone() const;

    /**
     * @brief Generate the time vector for this signal.
     * @return Vector of time values in seconds
     */
    [[nodiscard]] Eigen::VectorXd time() const;

    /**
     * @brief Check if this is an optical signal.
     * @return true if center_freq is set
     */
    [[nodiscard]] bool is_optical() const;

    /**
     * @brief Check if this uses Jones vector polarization.
     * @return true if pol_mode == "jones"
     */
    [[nodiscard]] bool is_jones() const;

    /**
     * @brief Get the number of samples.
     * @return Number of samples in the data vector
     */
    [[nodiscard]] Eigen::Index n_samples() const { return data.size(); }
};

} // namespace photonflow
