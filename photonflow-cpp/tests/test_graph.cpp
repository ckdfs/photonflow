/**
 * @file test_graph.cpp
 * @brief Unit tests for Graph execution engine.
 */

#include "photonflow/blocks/block_registry.hpp"
#include "photonflow/core/graph.hpp"
#include <gtest/gtest.h>


using namespace photonflow;

// Simple test block for unit testing
class TestSource : public BaseBlock {
public:
  TestSource(const std::string &id, const json &params, const json &nonideal)
      : BaseBlock(id, params, nonideal) {}

  std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> & /*inputs*/,
          SimContext &ctx) override {
    Eigen::VectorXcd data = Eigen::VectorXcd::Ones(ctx.n_samples());
    Signal out(data, ctx.fs(), ctx.t0());
    return {{"out", out}};
  }

  std::optional<std::string> port_type(const std::string &port) const override {
    if (port == "out")
      return "electrical";
    return std::nullopt;
  }

  std::string block_type() const override { return "TestSource"; }
  json describe() const override {
    return {{"ports", {{"out", "electrical"}}}};
  }
};

class TestPassthrough : public BaseBlock {
public:
  TestPassthrough(const std::string &id, const json &params,
                  const json &nonideal)
      : BaseBlock(id, params, nonideal) {}

  std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> &inputs,
          SimContext & /*ctx*/) override {
    std::unordered_map<std::string, Signal> outputs;
    if (inputs.contains("in")) {
      outputs["out"] = inputs.at("in").clone();
    }
    return outputs;
  }

  std::optional<std::string> port_type(const std::string &port) const override {
    if (port == "in" || port == "out")
      return "electrical";
    return std::nullopt;
  }

  std::string block_type() const override { return "TestPassthrough"; }
  json describe() const override {
    return {{"ports", {{"in", "electrical"}, {"out", "electrical"}}}};
  }
};

class GraphTestFixture : public ::testing::Test {
protected:
  void SetUp() override {
    auto &registry = BlockRegistry::instance();
    registry.register_block<TestSource>("TestSource");
    registry.register_block<TestPassthrough>("TestPassthrough");
  }
};

TEST_F(GraphTestFixture, AddNode) {
  Graph graph;
  graph.add_node(
      std::make_unique<TestSource>("src1", json::object(), json::object()));

  EXPECT_EQ(graph.node_count(), 1);
  EXPECT_NE(graph.get_node("src1"), nullptr);
  EXPECT_EQ(graph.get_node("nonexistent"), nullptr);
}

TEST_F(GraphTestFixture, AddEdge) {
  Graph graph;
  graph.add_node(
      std::make_unique<TestSource>("src1", json::object(), json::object()));
  graph.add_node(std::make_unique<TestPassthrough>("pass1", json::object(),
                                                   json::object()));
  graph.add_edge({"src1", "out", "pass1", "in"});

  EXPECT_EQ(graph.edge_count(), 1);
}

TEST_F(GraphTestFixture, FromJson) {
  json graph_json = {{"nodes",
                      {{{"id", "src"}, {"type", "TestSource"}},
                       {{"id", "pass"},
                        {"type", "TestPassthrough"},
                        {"params", json::object()}}}},
                     {"edges",
                      {{{"src", "src"},
                        {"src_port", "out"},
                        {"dst", "pass"},
                        {"dst_port", "in"}}}}};

  auto graph = Graph::from_json(graph_json);
  EXPECT_EQ(graph.node_count(), 2);
  EXPECT_EQ(graph.edge_count(), 1);
}

TEST_F(GraphTestFixture, Compile) {
  Graph graph;
  graph.add_node(
      std::make_unique<TestSource>("src", json::object(), json::object()));
  graph.add_node(std::make_unique<TestPassthrough>("pass", json::object(),
                                                   json::object()));
  graph.add_edge({"src", "out", "pass", "in"});

  EXPECT_NO_THROW(graph.compile());

  auto order = graph.execution_order();
  EXPECT_EQ(order.size(), 2);
  // Source should come before passthrough
  EXPECT_EQ(order[0], "src");
  EXPECT_EQ(order[1], "pass");
}

TEST_F(GraphTestFixture, Run) {
  Graph graph;
  graph.add_node(
      std::make_unique<TestSource>("src", json::object(), json::object()));
  graph.add_node(std::make_unique<TestPassthrough>("pass", json::object(),
                                                   json::object()));
  graph.add_edge({"src", "out", "pass", "in"});

  SimConfig config;
  config.fs = 1e9;
  config.n_samples = 100;

  auto results = graph.run(config);

  // Check outputs exist
  EXPECT_TRUE(results.contains({"src", "out"}));
  EXPECT_TRUE(results.contains({"pass", "out"}));

  // Check signal properties
  const auto &out_signal = results.at({"pass", "out"});
  EXPECT_EQ(out_signal.n_samples(), 100);
  EXPECT_DOUBLE_EQ(out_signal.fs, 1e9);
}

TEST_F(GraphTestFixture, CycleDetection) {
  Graph graph;
  graph.add_node(
      std::make_unique<TestPassthrough>("a", json::object(), json::object()));
  graph.add_node(
      std::make_unique<TestPassthrough>("b", json::object(), json::object()));

  // Create a cycle: a -> b -> a
  graph.add_edge({"a", "out", "b", "in"});
  graph.add_edge({"b", "out", "a", "in"});

  EXPECT_THROW(graph.compile(), std::runtime_error);
}
