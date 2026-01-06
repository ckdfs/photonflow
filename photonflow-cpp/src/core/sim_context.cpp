/**
 * @file sim_context.cpp
 * @brief SimContext class implementation.
 */

#include "photonflow/core/sim_context.hpp"

namespace photonflow {

SimContext::SimContext(const SimConfig &config, double fs, int n_samples,
                       double t0, int seed_offset)
    : config_(config), fs_(fs), n_samples_(n_samples), t0_(t0),
      rng_(static_cast<unsigned int>(config.seed + seed_offset)),
      normal_dist_(0.0, 1.0) {}

Eigen::VectorXd SimContext::time(double offset) const {
  Eigen::VectorXd t(n_samples_);
  for (int i = 0; i < n_samples_; ++i) {
    t[i] = t0_ + offset + static_cast<double>(i) / fs_;
  }
  return t;
}

Eigen::VectorXcd SimContext::zeros_complex(int n) const {
  return Eigen::VectorXcd::Zero(n);
}

Eigen::VectorXd SimContext::randn(int n) {
  Eigen::VectorXd result(n);
  for (int i = 0; i < n; ++i) {
    result[i] = normal_dist_(rng_);
  }
  return result;
}

double SimContext::randn_scalar() { return normal_dist_(rng_); }

} // namespace photonflow
