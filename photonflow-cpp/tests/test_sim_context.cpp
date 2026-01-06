/**
 * @file test_sim_context.cpp
 * @brief Unit tests for SimContext class.
 */

#include "photonflow/core/sim_context.hpp"
#include <gtest/gtest.h>


using namespace photonflow;

TEST(SimContextTest, Construction) {
  SimConfig config;
  config.seed = 42;

  SimContext ctx(config, 1e9, 1000, 0.0, 0);

  EXPECT_DOUBLE_EQ(ctx.fs(), 1e9);
  EXPECT_EQ(ctx.n_samples(), 1000);
  EXPECT_DOUBLE_EQ(ctx.t0(), 0.0);
}

TEST(SimContextTest, TimeVector) {
  SimConfig config;
  SimContext ctx(config, 1e9, 100, 1e-6);

  Eigen::VectorXd t = ctx.time();

  EXPECT_EQ(t.size(), 100);
  EXPECT_DOUBLE_EQ(t[0], 1e-6);
  EXPECT_DOUBLE_EQ(t[1], 1e-6 + 1e-9);
}

TEST(SimContextTest, TimeVectorWithOffset) {
  SimConfig config;
  SimContext ctx(config, 1e9, 100, 0.0);

  Eigen::VectorXd t = ctx.time(1e-6);

  EXPECT_DOUBLE_EQ(t[0], 1e-6);
}

TEST(SimContextTest, ZerosComplex) {
  SimConfig config;
  SimContext ctx(config, 1e9, 100);

  Eigen::VectorXcd zeros = ctx.zeros_complex(50);

  EXPECT_EQ(zeros.size(), 50);
  for (int i = 0; i < 50; ++i) {
    EXPECT_EQ(zeros[i], std::complex<double>(0.0, 0.0));
  }
}

TEST(SimContextTest, Randn) {
  SimConfig config;
  config.seed = 12345;
  SimContext ctx(config, 1e9, 1000);

  Eigen::VectorXd noise = ctx.randn(1000);

  EXPECT_EQ(noise.size(), 1000);

  // Check statistical properties (mean ~ 0, std ~ 1)
  double mean = noise.mean();
  double std = std::sqrt((noise.array() - mean).square().mean());

  EXPECT_NEAR(mean, 0.0, 0.1); // Mean should be close to 0
  EXPECT_NEAR(std, 1.0, 0.1);  // Std should be close to 1
}

TEST(SimContextTest, RandnReproducibility) {
  SimConfig config;
  config.seed = 42;

  SimContext ctx1(config, 1e9, 100);
  Eigen::VectorXd noise1 = ctx1.randn(10);

  SimContext ctx2(config, 1e9, 100);
  Eigen::VectorXd noise2 = ctx2.randn(10);

  // Same seed should produce same sequence
  for (int i = 0; i < 10; ++i) {
    EXPECT_DOUBLE_EQ(noise1[i], noise2[i]);
  }
}
