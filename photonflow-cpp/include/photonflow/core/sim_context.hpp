/**
 * @file sim_context.hpp
 * @brief Simulation configuration and context.
 *
 * Corresponds to: backend/src/photonflow/core/sim.py
 */

#pragma once

#include <Eigen/Dense>
#include <optional>
#include <random>
#include <string>


namespace photonflow {

/**
 * @struct SimConfig
 * @brief Configuration parameters for a simulation run.
 */
struct SimConfig {
  /// Backend type (always "cpp" for C++ version)
  std::string backend = "cpp";

  /// Device to run on ("cpu" or future GPU support)
  std::string device = "cpu";

  /// Sampling rate in Hz (0 = auto-determine)
  double fs = 0.0;

  /// Minimum sampling rate in Hz
  double fs_min = 0.0;

  /// Maximum sampling rate in Hz
  double fs_max = 0.0;

  /// Oversampling factor
  int oversample = 4;

  /// Random seed
  int seed = 0;

  /// Window function type
  std::string window = "hann";

  /// Simulation duration in seconds
  double duration_s = 1e-6;

  /// Number of samples (nullopt = auto-calculate)
  std::optional<int> n_samples = std::nullopt;

  /// Minimum number of samples
  int min_samples = 0;

  /// Maximum number of samples
  int max_samples = 0;

  /// Chunk size for chunked processing (0 = disabled)
  int chunk = 0;
};

/**
 * @class SimContext
 * @brief Runtime context for simulation execution.
 *
 * Provides utilities for generating time vectors, noise, and managing
 * the simulation state during graph execution.
 */
class SimContext {
public:
  /**
   * @brief Construct a new SimContext.
   * @param config Simulation configuration
   * @param fs Resolved sampling rate in Hz
   * @param n_samples Number of samples
   * @param t0 Time offset in seconds (default: 0.0)
   * @param seed_offset Additional seed offset (default: 0)
   */
  SimContext(const SimConfig &config, double fs, int n_samples, double t0 = 0.0,
             int seed_offset = 0);

  /// Get the simulation configuration
  [[nodiscard]] const SimConfig &config() const { return config_; }

  /// Get the sampling rate in Hz
  [[nodiscard]] double fs() const { return fs_; }

  /// Get the number of samples
  [[nodiscard]] int n_samples() const { return n_samples_; }

  /// Get the time offset
  [[nodiscard]] double t0() const { return t0_; }

  /**
   * @brief Generate a time vector.
   * @param offset Additional time offset (default: 0.0)
   * @return Vector of time values in seconds
   */
  [[nodiscard]] Eigen::VectorXd time(double offset = 0.0) const;

  /**
   * @brief Create a zero-initialized complex vector.
   * @param n Number of elements
   * @return Zero-initialized complex vector
   */
  [[nodiscard]] Eigen::VectorXcd zeros_complex(int n) const;

  /**
   * @brief Generate Gaussian random noise.
   * @param n Number of samples
   * @return Vector of normally distributed random values
   */
  [[nodiscard]] Eigen::VectorXd randn(int n);

  /**
   * @brief Generate a single Gaussian random value.
   * @return Normally distributed random value
   */
  [[nodiscard]] double randn_scalar();

private:
  SimConfig config_;
  double fs_;
  int n_samples_;
  double t0_;
  std::mt19937 rng_;
  std::normal_distribution<double> normal_dist_;
};

} // namespace photonflow
