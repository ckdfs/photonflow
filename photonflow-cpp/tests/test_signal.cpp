/**
 * @file test_signal.cpp
 * @brief Unit tests for Signal class.
 */

#include "photonflow/core/signal.hpp"
#include <gtest/gtest.h>


using namespace photonflow;

TEST(SignalTest, Construction) {
  Eigen::VectorXcd data(100);
  data.setConstant(std::complex<double>(1.0, 0.0));

  Signal sig(data, 1e9, 0.0);

  EXPECT_EQ(sig.n_samples(), 100);
  EXPECT_DOUBLE_EQ(sig.fs, 1e9);
  EXPECT_DOUBLE_EQ(sig.t0, 0.0);
  EXPECT_EQ(sig.pol_mode, "scalar");
  EXPECT_FALSE(sig.is_optical());
  EXPECT_FALSE(sig.is_jones());
}

TEST(SignalTest, Clone) {
  Eigen::VectorXcd data(50);
  data.setConstant(std::complex<double>(2.0, 1.0));

  Signal original(data, 100e9, 1e-6);
  original.center_freq = 193.1e12;
  original.pol_mode = "scalar";
  original.meta["test"] = "value";

  Signal copy = original.clone();

  // Verify copy is independent
  EXPECT_EQ(copy.n_samples(), original.n_samples());
  EXPECT_DOUBLE_EQ(copy.fs, original.fs);
  EXPECT_DOUBLE_EQ(copy.t0, original.t0);
  EXPECT_TRUE(copy.is_optical());
  EXPECT_DOUBLE_EQ(*copy.center_freq, 193.1e12);
  EXPECT_EQ(copy.meta["test"], "value");

  // Modify original, verify copy unchanged
  original.data[0] = std::complex<double>(0.0, 0.0);
  EXPECT_NE(copy.data[0], original.data[0]);
}

TEST(SignalTest, TimeVector) {
  const int n = 100;
  Eigen::VectorXcd data = Eigen::VectorXcd::Zero(n);
  double fs = 1e9;  // 1 GHz
  double t0 = 1e-6; // 1 us offset

  Signal sig(data, fs, t0);
  Eigen::VectorXd t = sig.time();

  EXPECT_EQ(t.size(), n);
  EXPECT_DOUBLE_EQ(t[0], t0);
  EXPECT_DOUBLE_EQ(t[1], t0 + 1.0 / fs);
  EXPECT_NEAR(t[n - 1], t0 + (n - 1) / fs, 1e-15);
}

TEST(SignalTest, IsOptical) {
  Eigen::VectorXcd data = Eigen::VectorXcd::Zero(10);
  Signal sig(data, 1e9);

  EXPECT_FALSE(sig.is_optical());

  sig.center_freq = 193.1e12;
  EXPECT_TRUE(sig.is_optical());
}

TEST(SignalTest, IsJones) {
  Eigen::VectorXcd data = Eigen::VectorXcd::Zero(10);
  Signal sig(data, 1e9);

  EXPECT_FALSE(sig.is_jones());

  sig.pol_mode = "jones";
  EXPECT_TRUE(sig.is_jones());
}
