
/**
 * @file test_server.cpp
 * @brief Unit tests for Server class (testing internal logic via friend class).
 */

#include "photonflow/server/server.hpp"
#include <gtest/gtest.h>
#include <nlohmann/json.hpp>

using namespace photonflow;
using json = nlohmann::json;

namespace photonflow {

class ServerTest : public ::testing::Test {
protected:
  Server server{8000, 1};

  // Helper to access private logic
  json call_run_graph_job(const json &graph_data, const json &sim_override,
                          int max_points) {
    return server.run_graph_job(graph_data, sim_override, max_points);
  }

  crow::response call_handle_health() { return server.handle_health(); }
};

TEST_F(ServerTest, HealthCheck) {
  auto res = call_handle_health();
  EXPECT_EQ(res.code, 200);
  auto body = json::parse(res.body);
  EXPECT_EQ(body["status"], "ok");
}

TEST_F(ServerTest, RunGraphJob_SimpleLaser) {
  // Construct a minimal graph JSON
  json graph_data;

  // Explicitly use json::array to avoid initializer list ambiguity
  graph_data["nodes"] = json::array(
      {{{"id", "laser1"}, {"type", "Laser"}, {"params", {{"power_dbm", 0.0}}}},
       {{"id", "osa1"}, {"type", "OSAProbe"}, {"params", {}}}});

  graph_data["edges"] = json::array({{{"src", "laser1"},
                                      {"src_port", "opt_out"},
                                      {"dst", "osa1"},
                                      {"dst_port", "opt_in"}}});

  graph_data["outputs"] = {
      {"extra", json::array({{{"node", "osa1"}, {"port", "opt_in"}}})}};

  json sim_override = {{"fs", 100e9}, {"n_samples", 128}};

  json result = call_run_graph_job(graph_data, sim_override, 128);
  EXPECT_EQ(result["status"], "ok");

  // Verify signals are present
  ASSERT_TRUE(result.contains("signals"));
  auto signals = result["signals"];
  EXPECT_TRUE(signals.contains("osa1.opt_in"));

  auto sig = signals["osa1.opt_in"];
  EXPECT_EQ(sig["n_samples"], 128);
  EXPECT_TRUE(sig.contains("data_real"));
  EXPECT_TRUE(sig.contains("data_imag"));
}

} // namespace photonflow
