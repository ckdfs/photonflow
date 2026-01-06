
/**
 * @file test_probes.cpp
 * @brief Unit tests for measurement probes (OSA, ESA, Scope).
 */

#include "photonflow/blocks/measurement/esa_probe.hpp"
#include "photonflow/blocks/measurement/osa_probe.hpp"
#include "photonflow/blocks/measurement/scope_probe.hpp"
#include "photonflow/core/signal.hpp"
#include "photonflow/core/sim_context.hpp"
#include <gtest/gtest.h>

using namespace photonflow;

class ProbeTestFixture : public ::testing::Test {
protected:
  SimConfig config;

  void SetUp() override {
    config.fs = 100e9; // 100 GHz
    config.seed = 42;
  }

  SimContext make_context(int n_samples = 1000) {
    return SimContext(config, config.fs, n_samples);
  }
};

// ===================== OSAProbe Tests =====================

TEST_F(ProbeTestFixture, OSAProbe_Connectivity) {
  OSAProbe osa("osa1", {}, {});

  // OSA expects "opt_in"
  Eigen::VectorXcd optical_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(1.0, 0.0));
  Signal opt_in(optical_data, 100e9);
  opt_in.center_freq = 193.1e12;

  auto ctx = make_context(100);
  auto outputs = osa.process({{"opt_in", opt_in}}, ctx);

  // Probes are sinks.
  EXPECT_TRUE(outputs.empty());
}

TEST_F(ProbeTestFixture, OSAProbe_PortType) {
  OSAProbe osa("osa1", {}, {});
  auto type = osa.port_type("opt_in");
  ASSERT_TRUE(type.has_value());
  EXPECT_EQ(*type, "optical");
  EXPECT_FALSE(osa.port_type("out").has_value());
}

// ===================== ESAProbe Tests =====================

TEST_F(ProbeTestFixture, ESAProbe_Connectivity) {
  ESAProbe esa("esa1", {}, {});

  // ESA expects "elec_in"
  Eigen::VectorXcd elec_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(0.5, 0.0));
  Signal elec_in(elec_data, 100e9);

  auto ctx = make_context(100);
  auto outputs = esa.process({{"elec_in", elec_in}}, ctx);

  EXPECT_TRUE(outputs.empty());
}

TEST_F(ProbeTestFixture, ESAProbe_PortType) {
  ESAProbe esa("esa1", {}, {});
  auto type = esa.port_type("elec_in");
  ASSERT_TRUE(type.has_value());
  EXPECT_EQ(*type, "electrical");
  EXPECT_FALSE(esa.port_type("out").has_value());
}

// ===================== ScopeProbe Tests =====================

TEST_F(ProbeTestFixture, ScopeProbe_Connectivity) {
  ScopeProbe scope("scope1", {}, {});

  // Scope expects "elec_in"
  Signal elec_in(Eigen::VectorXcd::Zero(100), 100e9);

  auto ctx = make_context(100);
  auto outputs = scope.process({{"elec_in", elec_in}}, ctx);

  EXPECT_TRUE(outputs.empty());
}

TEST_F(ProbeTestFixture, ScopeProbe_PortType) {
  ScopeProbe scope("scope1", {}, {});
  auto type = scope.port_type("elec_in");
  ASSERT_TRUE(type.has_value());
  EXPECT_EQ(*type, "electrical");
}
