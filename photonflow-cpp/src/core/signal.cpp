/**
 * @file signal.cpp
 * @brief Signal class implementation.
 */

#include "photonflow/core/signal.hpp"

namespace photonflow {

Signal::Signal(const Eigen::VectorXcd& data, double fs, double t0)
    : data(data)
    , fs(fs)
    , t0(t0)
    , center_freq(std::nullopt)
    , pol_mode("scalar")
{}

Signal Signal::clone() const {
    Signal copy(data, fs, t0);
    copy.center_freq = center_freq;
    copy.pol_mode = pol_mode;
    copy.meta = meta;
    return copy;
}

Eigen::VectorXd Signal::time() const {
    const Eigen::Index n = data.size();
    Eigen::VectorXd t(n);
    for (Eigen::Index i = 0; i < n; ++i) {
        t[i] = t0 + static_cast<double>(i) / fs;
    }
    return t;
}

bool Signal::is_optical() const {
    return center_freq.has_value();
}

bool Signal::is_jones() const {
    return pol_mode == "jones";
}

} // namespace photonflow
