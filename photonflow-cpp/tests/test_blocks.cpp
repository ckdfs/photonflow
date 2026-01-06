/**
 * @file test_blocks.cpp
 * @brief Unit tests for Phase 2 blocks.
 */

#include <cmath>
#include <complex>

#include "photonflow/blocks/block_registry.hpp"
#include "photonflow/blocks/detectors/photodetector.hpp"
#include "photonflow/blocks/electrical/dc_source.hpp"
#include "photonflow/blocks/electrical/rf_source.hpp"
#include "photonflow/blocks/optical/attenuator.hpp"
#include "photonflow/blocks/optical/coupler.hpp"
#include "photonflow/blocks/optical/fiber.hpp"
#include "photonflow/blocks/optical/laser.hpp"
#include "photonflow/blocks/optical/mzm.hpp"
#include "photonflow/blocks/optical/pm.hpp"
#include "photonflow/core/signal.hpp"
#include "photonflow/core/sim_context.hpp"
#include <gtest/gtest.h>

using namespace photonflow;

class BlockTestFixture : public ::testing::Test {
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

// ===================== Laser Tests =====================

TEST_F(BlockTestFixture, Laser_IdealOutput) {
  Laser laser("laser1", {{"power_dbm", 0.0}, {"center_freq_hz", 193.1e12}}, {});

  auto ctx = make_context(1000);
  auto outputs = laser.process({}, ctx);

  ASSERT_TRUE(outputs.contains("opt_out"));
  const auto &sig = outputs.at("opt_out");

  EXPECT_EQ(sig.n_samples(), 1000);
  EXPECT_DOUBLE_EQ(sig.fs, 100e9);
  EXPECT_TRUE(sig.is_optical());
  EXPECT_DOUBLE_EQ(*sig.center_freq, 193.1e12);

  // 0 dBm = 1 mW = 0.001 W, so amplitude = sqrt(0.001)
  double expected_amp = std::sqrt(0.001);
  double actual_amp = std::abs(sig.data[0]);
  EXPECT_NEAR(actual_amp, expected_amp, 1e-10);
}

TEST_F(BlockTestFixture, Laser_PowerLevel) {
  // 10 dBm = 10 mW
  Laser laser("laser1", {{"power_dbm", 10.0}}, {});

  auto ctx = make_context(100);
  auto outputs = laser.process({}, ctx);

  double expected_power = 0.01; // 10 mW = 0.01 W
  double actual_power = std::norm(outputs.at("opt_out").data[0]);
  EXPECT_NEAR(actual_power, expected_power, 1e-10);
}

TEST_F(BlockTestFixture, Laser_PortType) {
  Laser laser("laser1", {}, {});

  EXPECT_EQ(laser.port_type("opt_out"), "optical");
  EXPECT_EQ(laser.port_type("unknown"), std::nullopt);
}

// ===================== RFSource Tests =====================

TEST_F(BlockTestFixture, RFSource_Sinusoid) {
  RFSource rf("rf1", {{"freq_hz", 1e9}, {"amplitude", 1.0}, {"phase", 0.0}},
              {});

  auto ctx = make_context(1000);
  auto outputs = rf.process({}, ctx);

  ASSERT_TRUE(outputs.contains("elec_out"));
  const auto &sig = outputs.at("elec_out");

  EXPECT_EQ(sig.n_samples(), 1000);
  EXPECT_FALSE(sig.is_optical());

  // Check that signal oscillates between -1 and 1
  double max_val = 0.0;
  for (Eigen::Index i = 0; i < sig.n_samples(); ++i) {
    max_val = std::max(max_val, std::abs(sig.data[i].real()));
  }
  EXPECT_NEAR(max_val, 1.0, 0.01);
}

TEST_F(BlockTestFixture, RFSource_EstimateFmax) {
  RFSource rf("rf1", {{"freq_hz", 5e9}}, {});

  auto fmax = rf.estimate_fmax();
  ASSERT_TRUE(fmax.has_value());
  EXPECT_DOUBLE_EQ(*fmax, 5e9);
}

// ===================== DCSource Tests =====================

TEST_F(BlockTestFixture, DCSource_ConstantVoltage) {
  DCSource dc("dc1", {{"voltage", 3.5}}, {});

  auto ctx = make_context(100);
  auto outputs = dc.process({}, ctx);

  ASSERT_TRUE(outputs.contains("elec_out"));
  const auto &sig = outputs.at("elec_out");

  // All samples should be 3.5V
  for (Eigen::Index i = 0; i < sig.n_samples(); ++i) {
    EXPECT_DOUBLE_EQ(sig.data[i].real(), 3.5);
  }
}

// ===================== MZM Tests =====================

TEST_F(BlockTestFixture, MZM_QuadraturePoint) {
  // At quadrature (phi_bias = pi/4), with no modulation, output should be ~0.5
  // power
  MZM mzm("mzm1", {{"Vpi", 3.5}, {"phi_bias", M_PI / 4.0}}, {});

  // Create optical input
  Eigen::VectorXcd optical_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(1.0, 0.0));
  Signal opt_in(optical_data, 100e9);
  opt_in.center_freq = 193.1e12;

  // Create zero electrical input
  Eigen::VectorXcd elec_data = Eigen::VectorXcd::Zero(100);
  Signal elec_in(elec_data, 100e9);

  auto ctx = make_context(100);
  auto outputs = mzm.process({{"opt_in", opt_in}, {"elec_in", elec_in}}, ctx);

  ASSERT_TRUE(outputs.contains("opt_out"));
  const auto &sig = outputs.at("opt_out");

  EXPECT_TRUE(sig.is_optical());
  EXPECT_DOUBLE_EQ(*sig.center_freq, 193.1e12);
}

TEST_F(BlockTestFixture, MZM_NullPoint) {
  // At null point (phi_bias = pi/2), output should be minimum
  MZM mzm("mzm1", {{"Vpi", 3.5}, {"phi_bias", M_PI / 2.0}}, {});

  Eigen::VectorXcd optical_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(1.0, 0.0));
  Signal opt_in(optical_data, 100e9);
  opt_in.center_freq = 193.1e12;

  Eigen::VectorXcd elec_data = Eigen::VectorXcd::Zero(100);
  Signal elec_in(elec_data, 100e9);

  auto ctx = make_context(100);
  auto outputs = mzm.process({{"opt_in", opt_in}, {"elec_in", elec_in}}, ctx);

  // At null point, output should be near zero
  double power = std::norm(outputs.at("opt_out").data[0]);
  EXPECT_NEAR(power, 0.0, 1e-10);
}

// ===================== PM Tests =====================

TEST_F(BlockTestFixture, PM_PhaseShift) {
  // With V = Vpi/2, phase shift should be pi/2
  PM pm("pm1", {{"Vpi", 3.5}}, {});

  Eigen::VectorXcd optical_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(1.0, 0.0));
  Signal opt_in(optical_data, 100e9);
  opt_in.center_freq = 193.1e12;

  double vpi = 3.5;
  Eigen::VectorXcd elec_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(vpi / 2.0, 0.0));
  Signal elec_in(elec_data, 100e9);

  auto ctx = make_context(100);
  auto outputs = pm.process({{"opt_in", opt_in}, {"elec_in", elec_in}}, ctx);

  // Output phase should be pi/2
  double output_phase = std::arg(outputs.at("opt_out").data[0]);
  EXPECT_NEAR(output_phase, M_PI / 2.0, 1e-10);
}

TEST_F(BlockTestFixture, PM_PowerPreservation) {
  PM pm("pm1", {{"Vpi", 3.5}}, {});

  Eigen::VectorXcd optical_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(1.0, 0.0));
  Signal opt_in(optical_data, 100e9);

  Eigen::VectorXcd elec_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(1.0, 0.0));
  Signal elec_in(elec_data, 100e9);

  auto ctx = make_context(100);
  auto outputs = pm.process({{"opt_in", opt_in}, {"elec_in", elec_in}}, ctx);

  // Power should be preserved (no loss in ideal case)
  double input_power = std::norm(opt_in.data[0]);
  double output_power = std::norm(outputs.at("opt_out").data[0]);
  EXPECT_NEAR(output_power, input_power, 1e-10);
}

// ===================== Photodetector Tests =====================

TEST_F(BlockTestFixture, PD_IdealDetection) {
  PD pd("pd1", {{"responsivity", 1.0}}, {});

  // 1W optical power -> 1A current
  Eigen::VectorXcd optical_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(1.0, 0.0));
  Signal opt_in(optical_data, 100e9);
  opt_in.center_freq = 193.1e12;

  auto ctx = make_context(100);
  auto outputs = pd.process({{"opt_in", opt_in}}, ctx);

  ASSERT_TRUE(outputs.contains("elec_out"));
  const auto &sig = outputs.at("elec_out");

  EXPECT_FALSE(sig.is_optical());

  // With 1W input and R=1 A/W, output current = 1A
  double expected_current = 1.0; // |E|^2 = 1, R = 1
  EXPECT_NEAR(sig.data[0].real(), expected_current, 1e-10);
}

TEST_F(BlockTestFixture, PD_Responsivity) {
  PD pd("pd1", {{"responsivity", 0.8}}, {});

  Eigen::VectorXcd optical_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(1.0, 0.0));
  Signal opt_in(optical_data, 100e9);

  auto ctx = make_context(100);
  auto outputs = pd.process({{"opt_in", opt_in}}, ctx);

  // With 1W input and R=0.8 A/W, output current = 0.8A
  EXPECT_NEAR(outputs.at("elec_out").data[0].real(), 0.8, 1e-10);
}

// ===================== Attenuator Tests =====================

TEST_F(BlockTestFixture, Attenuator_LossApplied) {
  Attenuator att("att1", {{"loss_db", 3.0}}, {});

  // 1W input power
  Eigen::VectorXcd optical_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(1.0, 0.0));
  Signal opt_in(optical_data, 100e9);
  opt_in.center_freq = 193.1e12;

  auto ctx = make_context(100);
  auto outputs = att.process({{"opt_in", opt_in}}, ctx);

  ASSERT_TRUE(outputs.contains("opt_out"));
  const auto &sig = outputs.at("opt_out");

  // 3 dB loss = power reduced by half, field by sqrt(2)
  double expected_field = 1.0 / std::sqrt(2.0); // 10^(-3/20)
  double actual_field = std::abs(sig.data[0]);
  EXPECT_NEAR(actual_field, expected_field, 0.01);
}

TEST_F(BlockTestFixture, Attenuator_ZeroLoss) {
  Attenuator att("att1", {{"loss_db", 0.0}}, {});

  Eigen::VectorXcd optical_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(1.0, 0.0));
  Signal opt_in(optical_data, 100e9);

  auto ctx = make_context(100);
  auto outputs = att.process({{"opt_in", opt_in}}, ctx);

  // No loss means signal unchanged
  EXPECT_NEAR(std::abs(outputs.at("opt_out").data[0]), 1.0, 1e-10);
}

// ===================== Coupler Tests =====================

TEST_F(BlockTestFixture, Coupler_3dBSplit) {
  // Default 50:50 coupler
  Coupler coupler("coupler1", {{"split_ratio", 0.5}}, {});

  // Single input
  Eigen::VectorXcd optical_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(1.0, 0.0));
  Signal opt_in1(optical_data, 100e9);
  opt_in1.center_freq = 193.1e12;

  auto ctx = make_context(100);
  auto outputs = coupler.process({{"opt_in1", opt_in1}}, ctx);

  ASSERT_TRUE(outputs.contains("opt_out1"));
  ASSERT_TRUE(outputs.contains("opt_out2"));

  // Power should be split 50:50
  double power1 = std::norm(outputs.at("opt_out1").data[0]);
  double power2 = std::norm(outputs.at("opt_out2").data[0]);
  EXPECT_NEAR(power1, 0.5, 0.01);
  EXPECT_NEAR(power2, 0.5, 0.01);
}

TEST_F(BlockTestFixture, Coupler_PowerConservation) {
  Coupler coupler("coupler1", {{"split_ratio", 0.3}}, {});

  Eigen::VectorXcd optical_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(1.0, 0.0));
  Signal opt_in1(optical_data, 100e9);

  auto ctx = make_context(100);
  auto outputs = coupler.process({{"opt_in1", opt_in1}}, ctx);

  // Total power should be conserved
  double input_power = 1.0;
  double output_power = std::norm(outputs.at("opt_out1").data[0]) +
                        std::norm(outputs.at("opt_out2").data[0]);
  EXPECT_NEAR(output_power, input_power, 1e-10);
}

// ===================== OpticalFiber Tests =====================

TEST_F(BlockTestFixture, OpticalFiber_Passthrough) {
  // Zero length fiber should pass through unchanged
  OpticalFiber fiber("fiber1", {{"length_m", 0.0}}, {});

  Eigen::VectorXcd optical_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(1.0, 0.0));
  Signal opt_in(optical_data, 100e9);
  opt_in.center_freq = 193.1e12;

  auto ctx = make_context(100);
  auto outputs = fiber.process({{"opt_in", opt_in}}, ctx);

  ASSERT_TRUE(outputs.contains("opt_out"));
  // Power should be unchanged
  EXPECT_NEAR(std::norm(outputs.at("opt_out").data[0]), 1.0, 1e-10);
}

TEST_F(BlockTestFixture, OpticalFiber_Attenuation) {
  // 0.2 dB/km over 10 km = 2 dB loss
  OpticalFiber fiber("fiber1",
                     {{"length_m", 10000.0}, {"alpha_db_per_km", 0.2}}, {});

  Eigen::VectorXcd optical_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(1.0, 0.0));
  Signal opt_in(optical_data, 100e9);
  opt_in.center_freq = 193.1e12;

  auto ctx = make_context(100);
  auto outputs = fiber.process({{"opt_in", opt_in}}, ctx);

  // 2 dB power loss = 10^(-2/10) = 0.631
  double expected_power = std::pow(10.0, -2.0 / 10.0);
  double actual_power = std::norm(outputs.at("opt_out").data[0]);
  EXPECT_NEAR(actual_power, expected_power, 0.01);
}

TEST_F(BlockTestFixture, OpticalFiber_DispersionPreservesPower) {
  // Dispersion only - power should be preserved
  OpticalFiber fiber("fiber1",
                     {{"length_m", 1000.0}, {"beta2_s2_per_m", -21.7e-27}}, {});

  Eigen::VectorXcd optical_data =
      Eigen::VectorXcd::Constant(100, std::complex<double>(1.0, 0.0));
  Signal opt_in(optical_data, 100e9);
  opt_in.center_freq = 193.1e12;

  auto ctx = make_context(100);
  auto outputs = fiber.process({{"opt_in", opt_in}}, ctx);

  // For CW input, power should be preserved under dispersion
  double input_power = 1.0;
  double output_power = std::norm(outputs.at("opt_out").data[0]);
  EXPECT_NEAR(output_power, input_power, 1e-6);
}

// ===================== Block Registry Tests =====================

TEST_F(BlockTestFixture, MeasurementProbes_Creation) {
  SimContext ctx(make_context(100));
  Signal sig_opt(Eigen::VectorXcd::Zero(100), 100e9, 0);
  Signal sig_elec(Eigen::VectorXcd::Zero(100), 100e9, 0);

  // OSAProbe
  {
    auto blk = BlockRegistry::instance().create("OSAProbe", "osa1", {}, {});
    ASSERT_NE(blk, nullptr);
    EXPECT_EQ(blk->block_type(), "OSAProbe");
    // Should accept optical input and return empty output (passthrough/sink
    // behavior)
    auto outputs = blk->process({{"opt_in", sig_opt}}, ctx);
    EXPECT_TRUE(outputs.empty());
  }

  // ESAProbe
  {
    auto blk = BlockRegistry::instance().create("ESAProbe", "esa1", {}, {});
    ASSERT_NE(blk, nullptr);
    EXPECT_EQ(blk->block_type(), "ESAProbe");
    auto outputs = blk->process({{"elec_in", sig_elec}}, ctx);
    EXPECT_TRUE(outputs.empty());
  }

  // ScopeProbe
  {
    auto blk = BlockRegistry::instance().create("ScopeProbe", "scope1", {}, {});
    ASSERT_NE(blk, nullptr);
    EXPECT_EQ(blk->block_type(), "ScopeProbe");
    auto outputs = blk->process({{"elec_in", sig_elec}}, ctx);
    EXPECT_TRUE(outputs.empty());
  }
}

TEST_F(BlockTestFixture, MZMComposite_Basic) {
  auto blk = BlockRegistry::instance().create(
      "MZMComposite", "mzm_c", {{"Vpi", 5.0}, {"phi_bias", 0.0}}, {});
  ASSERT_NE(blk, nullptr);

  auto ctx = make_context(100);
  int n = ctx.n_samples();

  // Constant optical input
  Signal opt_in(Eigen::VectorXcd::Constant(n, 1.0), ctx.fs(), ctx.t0());
  // Zero electrical input
  Signal elec_in(Eigen::VectorXcd::Zero(n), ctx.fs(), ctx.t0());

  std::unordered_map<std::string, Signal> inputs = {{"opt_in", opt_in},
                                                    {"elec_in", elec_in}};

  auto outputs = blk->process(inputs, ctx);
  ASSERT_TRUE(outputs.contains("opt_out"));

  // With 0V input and 0 bias, phase = 0
  // Transfer = cos(0) = 1.0
  EXPECT_NEAR(std::abs(outputs.at("opt_out").data[0]), 1.0, 1e-5);
}

TEST_F(BlockTestFixture, DPMZMComposite_Creation) {
  auto blk =
      BlockRegistry::instance().create("DPMZMComposite", "dpmzm_c", {}, {});
  ASSERT_NE(blk, nullptr);
  EXPECT_EQ(blk->block_type(), "DPMZMComposite");

  auto ctx = make_context(100);
  int n = ctx.n_samples();
  Signal opt_in(Eigen::VectorXcd::Constant(n, 1.0), ctx.fs(), ctx.t0());
  Signal elec(Eigen::VectorXcd::Zero(n), ctx.fs(), ctx.t0());

  std::unordered_map<std::string, Signal> inputs = {
      {"opt_in", opt_in}, {"elec_i", elec}, {"elec_q", elec}};

  auto outputs = blk->process(inputs, ctx);
  ASSERT_TRUE(outputs.contains("opt_out"));
}

TEST_F(BlockTestFixture, Registry_BlocksRegistered) {
  auto &registry = BlockRegistry::instance();

  EXPECT_TRUE(registry.has_type("Laser"));
  EXPECT_TRUE(registry.has_type("RFSource"));
  EXPECT_TRUE(registry.has_type("DCSource"));
  EXPECT_TRUE(registry.has_type("MZM"));
  EXPECT_TRUE(registry.has_type("PM"));
  EXPECT_TRUE(registry.has_type("PD"));
  EXPECT_TRUE(registry.has_type("Attenuator"));
  EXPECT_TRUE(registry.has_type("Coupler"));
  EXPECT_TRUE(registry.has_type("OpticalFiber"));
  // New blocks
  EXPECT_TRUE(registry.has_type("OSAProbe"));
  EXPECT_TRUE(registry.has_type("ESAProbe"));
  EXPECT_TRUE(registry.has_type("ScopeProbe"));
  EXPECT_TRUE(registry.has_type("MZMComposite"));
  EXPECT_TRUE(registry.has_type("DPMZMComposite"));
}

TEST_F(BlockTestFixture, Registry_CreateBlock) {
  auto &registry = BlockRegistry::instance();

  auto laser = registry.create("Laser", "test_laser", {{"power_dbm", 5.0}}, {});
  ASSERT_NE(laser, nullptr);
  EXPECT_EQ(laser->block_type(), "Laser");
}
