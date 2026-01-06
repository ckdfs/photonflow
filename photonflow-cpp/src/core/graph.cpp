/**
 * @file graph.cpp
 * @brief Graph execution engine implementation.
 */

#include "photonflow/core/graph.hpp"

#include <queue>
#include <spdlog/spdlog.h>
#include <stdexcept>

namespace photonflow {

void Graph::add_node(std::unique_ptr<BaseBlock> block) {
  if (!block) {
    throw std::invalid_argument("Cannot add null block to graph");
  }
  const std::string &id = block->id();
  if (nodes_.contains(id)) {
    throw std::invalid_argument("Duplicate node ID: " + id);
  }
  nodes_[id] = std::move(block);
  compiled_ = false;
}

void Graph::add_edge(const Edge &edge) {
  edges_.push_back(edge);
  compiled_ = false;
}

Graph Graph::from_json(const json &graph_json, const BlockRegistry &registry) {
  Graph graph;

  // Parse nodes
  if (graph_json.contains("nodes") && graph_json["nodes"].is_array()) {
    for (const auto &node_json : graph_json["nodes"]) {
      std::string id = node_json.at("id").get<std::string>();
      std::string type = node_json.at("type").get<std::string>();

      json params = node_json.value("params", json::object());
      json nonideal = node_json.value("nonideal", json::object());

      auto block = registry.create(type, id, params, nonideal);
      if (!block) {
        throw std::runtime_error("Unknown block type: " + type);
      }
      graph.add_node(std::move(block));
    }
  }

  // Parse edges
  if (graph_json.contains("edges") && graph_json["edges"].is_array()) {
    for (const auto &edge_json : graph_json["edges"]) {
      Edge edge;
      edge.src = edge_json.at("src").get<std::string>();
      edge.src_port = edge_json.at("src_port").get<std::string>();
      edge.dst = edge_json.at("dst").get<std::string>();
      edge.dst_port = edge_json.at("dst_port").get<std::string>();
      graph.add_edge(edge);
    }
  }

  return graph;
}

std::pair<std::string, std::string>
Graph::resolve_source(const std::string &node_id,
                      const std::string &port_name) const {
  for (const auto &edge : edges_) {
    if (edge.dst == node_id && edge.dst_port == port_name) {
      return {edge.src, edge.src_port};
    }
  }
  return {};
}

void Graph::compile() {
  topological_sort();
  compiled_ = true;
  spdlog::debug("Graph compiled with {} nodes, {} edges", nodes_.size(),
                edges_.size());
}

void Graph::topological_sort() {
  // Build adjacency list and in-degree map
  std::unordered_map<std::string, int> in_degree;
  std::unordered_map<std::string, std::vector<std::string>> adjacency;

  // Initialize all nodes with in-degree 0
  for (const auto &[id, _] : nodes_) {
    in_degree[id] = 0;
    adjacency[id] = {};
  }

  // Build graph from edges
  for (const auto &edge : edges_) {
    adjacency[edge.src].push_back(edge.dst);
    in_degree[edge.dst]++;
  }

  // Kahn's algorithm
  std::queue<std::string> queue;
  for (const auto &[id, degree] : in_degree) {
    if (degree == 0) {
      queue.push(id);
    }
  }

  execution_order_.clear();
  execution_order_.reserve(nodes_.size());

  while (!queue.empty()) {
    std::string node = queue.front();
    queue.pop();
    execution_order_.push_back(node);

    for (const auto &neighbor : adjacency[node]) {
      in_degree[neighbor]--;
      if (in_degree[neighbor] == 0) {
        queue.push(neighbor);
      }
    }
  }

  if (execution_order_.size() != nodes_.size()) {
    throw std::runtime_error(
        "Graph contains a cycle - cannot determine execution order");
  }
}

double Graph::estimate_fs(int oversample) const {
  double max_fmax = 0.0;
  for (const auto &[_, node] : nodes_) {
    auto fmax = node->estimate_fmax();
    if (fmax.has_value() && *fmax > max_fmax) {
      max_fmax = *fmax;
    }
  }
  return max_fmax * 2.0 * oversample; // Nyquist * oversample
}

void Graph::resolve_sim_params(const SimConfig &config, double &fs,
                               int &n_samples) const {
  // Resolve sampling rate
  if (config.fs > 0) {
    fs = config.fs;
  } else {
    fs = estimate_fs(config.oversample);
    if (fs <= 0) {
      fs = 100e9; // Default: 100 GHz
    }
  }

  // Apply limits
  if (config.fs_min > 0 && fs < config.fs_min) {
    fs = config.fs_min;
  }
  if (config.fs_max > 0 && fs > config.fs_max) {
    fs = config.fs_max;
  }

  // Resolve sample count
  if (config.n_samples.has_value()) {
    n_samples = *config.n_samples;
  } else {
    n_samples = static_cast<int>(config.duration_s * fs);
  }

  // Apply limits
  if (config.min_samples > 0 && n_samples < config.min_samples) {
    n_samples = config.min_samples;
  }
  if (config.max_samples > 0 && n_samples > config.max_samples) {
    n_samples = config.max_samples;
  }
}

SignalMap Graph::run(const SimConfig &config) {
  if (!compiled_) {
    compile();
  }

  double fs;
  int n_samples;
  resolve_sim_params(config, fs, n_samples);

  spdlog::info("Running graph: fs={:.2e} Hz, n_samples={}", fs, n_samples);

  SimContext ctx(config, fs, n_samples);
  return run_once(ctx);
}

SignalMap Graph::run_once(SimContext &ctx) {
  // Storage for all signals: (node_id, port_name) -> Signal
  SignalMap all_signals;

  // Build reverse edge lookup: (dst, dst_port) -> (src, src_port)
  std::unordered_map<std::pair<std::string, std::string>,
                     std::pair<std::string, std::string>, PairHash>
      input_sources;
  for (const auto &edge : edges_) {
    input_sources[{edge.dst, edge.dst_port}] = {edge.src, edge.src_port};
  }

  // Execute nodes in topological order
  for (const auto &node_id : execution_order_) {
    auto *node = nodes_.at(node_id).get();

    // Gather inputs for this node
    std::unordered_map<std::string, Signal> inputs;
    for (const auto &edge : edges_) {
      if (edge.dst == node_id) {
        auto source_key = std::make_pair(edge.src, edge.src_port);
        if (all_signals.contains(source_key)) {
          inputs[edge.dst_port] = all_signals[source_key];
        }
      }
    }

    // Process the node
    auto outputs = node->process(inputs, ctx);

    // Store outputs
    for (auto &[port_name, signal] : outputs) {
      all_signals[{node_id, port_name}] = std::move(signal);
    }
  }

  return all_signals;
}

BaseBlock *Graph::get_node(const std::string &id) {
  auto it = nodes_.find(id);
  return it != nodes_.end() ? it->second.get() : nullptr;
}

const BaseBlock *Graph::get_node(const std::string &id) const {
  auto it = nodes_.find(id);
  return it != nodes_.end() ? it->second.get() : nullptr;
}

} // namespace photonflow
