/**
 * @file graph.hpp
 * @brief Graph execution engine for block-based simulations.
 *
 * Corresponds to: backend/src/photonflow/core/graph.py
 */

#pragma once

#include "photonflow/blocks/base_block.hpp"
#include "photonflow/blocks/block_registry.hpp"
#include "photonflow/core/signal.hpp"
#include "photonflow/core/sim_context.hpp"

#include <memory>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace photonflow {

/**
 * @struct Edge
 * @brief Represents a connection between two block ports.
 */
struct Edge {
  std::string src;      ///< Source block ID
  std::string src_port; ///< Source port name
  std::string dst;      ///< Destination block ID
  std::string dst_port; ///< Destination port name
};

/**
 * @struct PairHash
 * @brief Hash function for (string, string) tuples used as map keys.
 */
struct PairHash {
  size_t operator()(const std::pair<std::string, std::string> &p) const {
    auto h1 = std::hash<std::string>{}(p.first);
    auto h2 = std::hash<std::string>{}(p.second);
    return h1 ^ (h2 << 1);
  }
};

/// Type alias for signal results map: (node_id, port_name) -> Signal
using SignalMap =
    std::unordered_map<std::pair<std::string, std::string>, Signal, PairHash>;

class Graph {
public:
  // ... (constructors)
  /**
   * @brief Construct an empty graph.
   */
  Graph() = default;

  /**
   * @brief Move constructor.
   */
  Graph(Graph &&) = default;
  Graph &operator=(Graph &&) = default;

  // Prevent copying
  Graph(const Graph &) = delete;
  Graph &operator=(const Graph &) = delete;

  /**
   * @brief Add a block to the graph.
   * @param block Unique pointer to the block
   */
  void add_node(std::unique_ptr<BaseBlock> block);

  /**
   * @brief Add an edge (connection) to the graph.
   * @param edge Edge specifying the connection
   */
  void add_edge(const Edge &edge);

  /**
   * @brief Parse a graph from JSON data.
   * @param graph_json JSON object with "nodes" and "edges" arrays
   * @param registry Block registry to use (default: global instance)
   * @return Constructed Graph object
   */
  static Graph
  from_json(const json &graph_json,
            const BlockRegistry &registry = BlockRegistry::instance());

  /**
   * @brief Compile the graph (validate and sort).
   *
   * Performs topological sorting and validates all connections.
   * Must be called before run().
   */
  void compile();

  /**
   * @brief Resolve the source of an input port.
   * @param node_id Destination node ID
   * @param port_name Destination port name
   * @return Pair of {source_node_id, source_port_name}, or empty strings if not
   * connected
   */
  std::pair<std::string, std::string>
  resolve_source(const std::string &node_id,
                 const std::string &port_name) const;

  /**
   * @brief Estimate the required sampling rate.
   * @param oversample Oversampling factor
   * @return Estimated sampling rate in Hz
   */
  [[nodiscard]] double estimate_fs(int oversample = 4) const;

  /**
   * @brief Run the simulation.
   * @param config Simulation configuration
   * @return Map of (node_id, port_name) to output signals
   */
  [[nodiscard]] SignalMap run(const SimConfig &config);

  /**
   * @brief Get a node by ID.
   * @param id Node ID
   * @return Pointer to block, or nullptr if not found
   */
  [[nodiscard]] BaseBlock *get_node(const std::string &id);
  [[nodiscard]] const BaseBlock *get_node(const std::string &id) const;

  /**
   * @brief Get the number of nodes.
   */
  [[nodiscard]] size_t node_count() const { return nodes_.size(); }

  /**
   * @brief Get the number of edges.
   */
  [[nodiscard]] size_t edge_count() const { return edges_.size(); }

  /**
   * @brief Get the execution order (after compile).
   */
  [[nodiscard]] const std::vector<std::string> &execution_order() const {
    return execution_order_;
  }

private:
  std::unordered_map<std::string, std::unique_ptr<BaseBlock>> nodes_;
  std::vector<Edge> edges_;
  std::vector<std::string> execution_order_;
  bool compiled_ = false;

  /**
   * @brief Perform topological sort using Kahn's algorithm.
   */
  void topological_sort();

  /**
   * @brief Resolve simulation parameters (sampling rate, n_samples).
   * @param config Input configuration
   * @param fs Output: resolved sampling rate
   * @param n_samples Output: resolved sample count
   */
  void resolve_sim_params(const SimConfig &config, double &fs,
                          int &n_samples) const;

  /**
   * @brief Execute the graph once with given context.
   * @param ctx Simulation context
   * @return Signal outputs
   */
  SignalMap run_once(SimContext &ctx);
};

} // namespace photonflow
