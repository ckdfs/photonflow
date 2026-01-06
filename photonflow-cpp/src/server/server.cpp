/**
 * @file server.cpp
 * @brief REST API server implementation.
 */

#include "photonflow/server/server.hpp"

#include "photonflow/blocks/block_registry.hpp"
#include "photonflow/core/graph.hpp"
#include "photonflow/core/sim_context.hpp"

#include <Eigen/Dense>
#include <spdlog/spdlog.h>

namespace photonflow {

Server::Server(uint16_t port, size_t job_workers)
    : job_manager_(job_workers), port_(port) {
  // Configure CORS
  auto &cors = app_.get_middleware<crow::CORSHandler>();
  cors.global()
      .origin("*")
      .headers("Content-Type, Authorization")
      .methods("GET"_method, "POST"_method, "PUT"_method, "DELETE"_method,
               "OPTIONS"_method);

  setup_routes();
}

void Server::setup_routes() {
  // Health check
  CROW_ROUTE(app_, "/health")
  ([this]() { return handle_health(); });

  // Block types
  CROW_ROUTE(app_, "/blocks")
  ([this]() { return handle_blocks(); });

  // Block specs
  CROW_ROUTE(app_, "/blocks/specs")
  ([this]() { return handle_block_specs(); });

  // Graph validation
  CROW_ROUTE(app_, "/graph/validate")
      .methods(crow::HTTPMethod::POST)([this](const crow::request &req) {
        return handle_graph_validate(req);
      });

  // Job submission
  CROW_ROUTE(app_, "/jobs/submit")
      .methods(crow::HTTPMethod::POST)(
          [this](const crow::request &req) { return handle_job_submit(req); });

  // Job status
  CROW_ROUTE(app_, "/jobs/<string>/status")
  ([this](const std::string &job_id) { return handle_job_status(job_id); });

  // Job result
  CROW_ROUTE(app_, "/jobs/<string>/result")
  ([this](const std::string &job_id) { return handle_job_result(job_id); });
}

void Server::run() {
  spdlog::info("Starting PhotonFlow server on port {}", port_);
  app_.port(port_).multithreaded().run();
}

void Server::stop() { app_.stop(); }

crow::response Server::handle_health() {
  json response = {{"status", "ok"}};
  return crow::response(200, response.dump());
}

crow::response Server::handle_blocks() {
  auto &registry = BlockRegistry::instance();
  json response = {{"types", registry.list_types()}};
  return crow::response(200, response.dump());
}

crow::response Server::handle_block_specs() {
  auto &registry = BlockRegistry::instance();
  json specs = registry.get_specs();
  return crow::response(200, specs.dump());
}

crow::response Server::handle_graph_validate(const crow::request &req) {
  try {
    json payload = json::parse(req.body);
    json graph_data = payload.value("graph", json::object());
    bool validate_schema = payload.value("validate", true);

    // Create and compile graph
    Graph graph = Graph::from_json(graph_data);
    graph.compile();

    json response = {{"status", "ok"}};
    return crow::response(200, response.dump());
  } catch (const std::exception &e) {
    json response = {{"status", "error"}, {"error", e.what()}};
    return crow::response(200, response.dump());
  }
}

crow::response Server::handle_job_submit(const crow::request &req) {
  try {
    json payload = json::parse(req.body);
    json graph_data = payload.value("graph", json::object());
    json sim_override = payload.value("sim_override", json::object());
    int max_points = payload.value("max_points", 4096);

    // Capture data for lambda
    auto graph_copy = graph_data;
    auto sim_copy = sim_override;

    std::string job_id =
        job_manager_.submit([this, graph_copy, sim_copy, max_points]() {
          return run_graph_job(graph_copy, sim_copy, max_points);
        });

    json response = {{"job_id", job_id}};
    return crow::response(200, response.dump());
  } catch (const std::exception &e) {
    json response = {{"error", e.what()}};
    return crow::response(400, response.dump());
  }
}

crow::response Server::handle_job_status(const std::string &job_id) {
  auto record = job_manager_.get(job_id);

  if (!record) {
    json response = {{"job_id", job_id}, {"status", "not_found"}};
    return crow::response(200, response.dump());
  }

  json response = {{"job_id", job_id}, {"status", record->status}};

  if (record->error) {
    response["error"] = *record->error;
  }

  return crow::response(200, response.dump());
}

crow::response Server::handle_job_result(const std::string &job_id) {
  auto record = job_manager_.get(job_id);

  if (!record) {
    json response = {{"job_id", job_id}, {"status", "not_found"}};
    return crow::response(200, response.dump());
  }

  json response = {{"job_id", job_id}, {"status", record->status}};

  if (record->result) {
    response["result"] = *record->result;
  }
  if (record->error) {
    response["error"] = *record->error;
  }

  return crow::response(200, response.dump());
}

json Server::run_graph_job(const json &graph_data, const json &sim_override,
                           int max_points) {
  // Parse and build graph
  Graph graph = Graph::from_json(graph_data);
  graph.compile();

  // Get simulation config from graph or use defaults
  json sim_config = graph_data.value("sim", json::object());

  // Apply overrides
  if (!sim_override.is_null() && sim_override.is_object()) {
    sim_config.update(sim_override);
  }

  // Create SimConfig
  SimConfig config;
  config.fs = sim_config.value("fs", 100e9);
  config.seed = sim_config.value("seed", 0);

  // Determine n_samples
  int n_samples = sim_config.value("n_samples", 0);
  if (n_samples <= 0) {
    double duration_s = sim_config.value("duration_s", 1e-6);
    n_samples = static_cast<int>(duration_s * config.fs);
  }
  n_samples = std::min(n_samples, max_points);
  config.n_samples = n_samples;

  // Run simulation
  auto outputs = graph.run(config);

  // Convert outputs to JSON
  json result = json::object();
  json signals = json::object();

  for (auto it = outputs.begin(); it != outputs.end(); ++it) {
    // Key is pair<node_id, port_name>
    std::string key = it->first.first + "." + it->first.second;
    const Signal &signal = it->second;

    json sig_json;
    sig_json["fs"] = signal.fs;
    sig_json["t0"] = signal.t0;
    sig_json["n_samples"] = signal.n_samples();
    sig_json["pol_mode"] = signal.pol_mode;

    if (signal.center_freq) {
      sig_json["center_freq"] = *signal.center_freq;
    }

    // Downsample if needed and convert to arrays
    int step = 1;
    int actual_samples = static_cast<int>(signal.n_samples());
    if (actual_samples > max_points) {
      step = (actual_samples + max_points - 1) / max_points;
      actual_samples = (static_cast<int>(signal.n_samples()) + step - 1) / step;
    }

    std::vector<double> data_real, data_imag;
    data_real.reserve(static_cast<size_t>(actual_samples));
    data_imag.reserve(static_cast<size_t>(actual_samples));

    for (Eigen::Index i = 0; i < signal.n_samples(); i += step) {
      data_real.push_back(signal.data[i].real());
      data_imag.push_back(signal.data[i].imag());
    }

    sig_json["data_real"] = data_real;
    sig_json["data_imag"] = data_imag;

    signals[key] = sig_json;
  }

  // Handle explicitly requested outputs (e.g. probes)
  if (graph_data.contains("outputs") &&
      graph_data["outputs"].contains("extra")) {
    const auto &extra = graph_data["outputs"]["extra"];
    if (extra.is_array()) {
      for (const auto &req : extra) {
        std::string node = req.value("node", "");
        std::string port = req.value("port", "");
        if (node.empty() || port.empty())
          continue;

        std::string target_key = node + "." + port;

        // If already in outputs (it was an output port)
        if (signals.contains(target_key))
          continue;

        // Otherwise, it might be an input port (probe), solve for source
        auto source = graph.resolve_source(node, port);
        if (source.first.empty())
          continue; // Not connected

        // Look up source signal
        auto output_it = outputs.find(source);
        if (output_it != outputs.end()) {
          const Signal &signal = output_it->second;

          // Copy-paste serialization logic (can be refactored)
          json sig_json;
          sig_json["fs"] = signal.fs;
          sig_json["t0"] = signal.t0;
          sig_json["n_samples"] = signal.n_samples();
          sig_json["pol_mode"] = signal.pol_mode;

          if (signal.center_freq) {
            sig_json["center_freq"] = *signal.center_freq;
          }

          // Downsample
          int step = 1;
          int actual_samples = static_cast<int>(signal.n_samples());
          if (actual_samples > max_points) {
            step = (actual_samples + max_points - 1) / max_points;
            actual_samples =
                (static_cast<int>(signal.n_samples()) + step - 1) / step;
          }

          std::vector<double> data_real, data_imag;
          data_real.reserve(static_cast<size_t>(actual_samples));
          data_imag.reserve(static_cast<size_t>(actual_samples));

          for (Eigen::Index i = 0; i < signal.n_samples(); i += step) {
            data_real.push_back(signal.data[i].real());
            data_imag.push_back(signal.data[i].imag());
          }

          sig_json["data_real"] = data_real;
          sig_json["data_imag"] = data_imag;

          signals[target_key] = sig_json;
        }
      }
    }
  }

  result["signals"] = signals;
  result["status"] = "ok";

  return result;
}

} // namespace photonflow
