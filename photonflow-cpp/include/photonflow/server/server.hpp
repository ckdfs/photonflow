/**
 * @file server.hpp
 * @brief REST API server using Crow framework.
 *
 * Corresponds to: backend/src/photonflow/server/app.py
 */

#pragma once

#include "photonflow/server/job_manager.hpp"

#include <crow.h>
#include <crow/middlewares/cors.h>

namespace photonflow {

/**
 * @class Server
 * @brief REST API server for PhotonFlow.
 */
class Server {
public:
  friend class ServerTest;
  explicit Server(uint16_t port = 8000, size_t job_workers = 2);

  /// Start the server (blocking)
  void run();

  /// Stop the server
  void stop();

private:
  void setup_routes();

  // Route handlers
  crow::response handle_health();
  crow::response handle_blocks();
  crow::response handle_block_specs();
  crow::response handle_graph_validate(const crow::request &req);
  crow::response handle_job_submit(const crow::request &req);
  crow::response handle_job_status(const std::string &job_id);
  crow::response handle_job_result(const std::string &job_id);

  // Execute simulation job
  json run_graph_job(const json &graph_data, const json &sim_override,
                     int max_points);

  crow::App<crow::CORSHandler> app_;
  JobManager job_manager_;
  uint16_t port_;
};

} // namespace photonflow
