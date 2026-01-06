/**
 * @file coupler.cpp
 * @brief 2x2 Optical coupler block implementation.
 */

#include "photonflow/blocks/optical/coupler.hpp"
#include "photonflow/blocks/block_registry.hpp"

#include <algorithm>
#include <cmath>
#include <complex>


namespace photonflow {

Coupler::Coupler(const std::string &id, const json &params,
                 const json &nonideal)
    : BaseBlock(id, params, nonideal) {}

std::unordered_map<std::string, Signal>
Coupler::process(const std::unordered_map<std::string, Signal> &inputs,
                 SimContext & /*ctx*/) {
  const Signal &in1 = inputs.at("opt_in1");

  // Get second input or create zero signal
  Eigen::VectorXcd in2_data;
  if (inputs.contains("opt_in2")) {
    in2_data = inputs.at("opt_in2").data;
  } else {
    in2_data = Eigen::VectorXcd::Zero(in1.n_samples());
  }

  // Get splitting ratio and clamp to [0, 1]
  double k = get_param("split_ratio", 0.5);
  k = std::clamp(k, 0.0, 1.0);

  // Non-ideal effects
  bool nonideal_enable = get_nonideal("enable", false);
  double phi_err = 0.0;
  double loss_db = 0.0;

  if (nonideal_enable) {
    double delta_k = get_nonideal("split_ratio_error", 0.0);
    k = std::clamp(k + delta_k, 0.0, 1.0);
    phi_err = get_nonideal("phase_error", 0.0);
    loss_db = get_nonideal("loss_db", 0.0);
  }

  // Coupler matrix coefficients
  // [a  b]   [  sqrt(k)           j*sqrt(1-k)*exp(j*phi_err) ]
  // [c  d] = [ j*sqrt(1-k)        sqrt(k)                     ]
  double a = std::sqrt(k);
  std::complex<double> b = std::complex<double>(0.0, 1.0) * std::sqrt(1.0 - k) *
                           std::exp(std::complex<double>(0.0, phi_err));
  std::complex<double> c = std::complex<double>(0.0, 1.0) * std::sqrt(1.0 - k);
  double d = std::sqrt(k);

  const Eigen::Index n = in1.n_samples();
  Eigen::VectorXcd out1_data(n);
  Eigen::VectorXcd out2_data(n);

  for (Eigen::Index i = 0; i < n; ++i) {
    out1_data[i] = a * in1.data[i] + b * in2_data[i];
    out2_data[i] = c * in1.data[i] + d * in2_data[i];
  }

  // Apply loss
  if (nonideal_enable && loss_db != 0.0) {
    double loss_linear = std::pow(10.0, -loss_db / 20.0);
    out1_data *= loss_linear;
    out2_data *= loss_linear;
  }

  Signal sig1(out1_data, in1.fs, in1.t0);
  sig1.center_freq = in1.center_freq;
  sig1.pol_mode = in1.pol_mode;
  sig1.meta = in1.meta;

  Signal sig2(out2_data, in1.fs, in1.t0);
  sig2.center_freq = in1.center_freq;
  sig2.pol_mode = in1.pol_mode;
  sig2.meta = in1.meta;

  return {{"opt_out1", std::move(sig1)}, {"opt_out2", std::move(sig2)}};
}

std::optional<std::string> Coupler::port_type(const std::string &port) const {
  if (port == "opt_in1" || port == "opt_in2" || port == "opt_out1" ||
      port == "opt_out2") {
    return "optical";
  }
  return std::nullopt;
}

json Coupler::describe() const {
  return {{"ports",
           {{"opt_in1", "optical"},
            {"opt_in2", "optical"},
            {"opt_out1", "optical"},
            {"opt_out2", "optical"}}},
          {"spec",
           {{"params",
             {{"split_ratio",
               {{"type", "float"}, {"default", 0.5}, {"unit", ""}}}}},
            {"nonideal",
             {{"enable", {{"type", "bool"}, {"default", false}}},
              {"split_ratio_error",
               {{"type", "float"}, {"default", 0.0}, {"unit", ""}}},
              {"phase_error",
               {{"type", "float"}, {"default", 0.0}, {"unit", "rad"}}},
              {"loss_db",
               {{"type", "float"}, {"default", 0.0}, {"unit", "dB"}}}}}}}};
}

REGISTER_BLOCK(Coupler, "Coupler");

} // namespace photonflow
