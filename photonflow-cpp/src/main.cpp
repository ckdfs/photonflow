/**
 * @file main.cpp
 * @brief PhotonFlow C++ server entry point.
 */

#include "photonflow/server/server.hpp"

#include <cstdlib>
#include <spdlog/spdlog.h>


int main(int argc, char *argv[]) {
  spdlog::set_level(spdlog::level::info);
  spdlog::info("PhotonFlow C++ Backend v0.1.0");

  // Parse port from args or env
  uint16_t port = 8000;

  if (argc > 1) {
    port = static_cast<uint16_t>(std::atoi(argv[1]));
  } else if (const char *env_port = std::getenv("PHOTONFLOW_PORT")) {
    port = static_cast<uint16_t>(std::atoi(env_port));
  }

  try {
    photonflow::Server server(port, 2);
    server.run();
  } catch (const std::exception &e) {
    spdlog::error("Server error: {}", e.what());
    return 1;
  }

  return 0;
}
