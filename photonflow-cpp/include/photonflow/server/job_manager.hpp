/**
 * @file job_manager.hpp
 * @brief Asynchronous job manager for simulation tasks.
 *
 * Corresponds to: backend/src/photonflow/server/job_manager.py
 */

#pragma once

#include <nlohmann/json.hpp>

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <functional>
#include <memory>
#include <mutex>
#include <optional>
#include <queue>
#include <string>
#include <thread>
#include <unordered_map>


namespace photonflow {

using json = nlohmann::json;

/**
 * @struct JobRecord
 * @brief Stores job status and result.
 */
struct JobRecord {
  std::string job_id;
  std::string status; // "queued", "running", "done", "error"
  std::optional<json> result;
  std::optional<std::string> error;
  std::chrono::system_clock::time_point created_at;
  std::chrono::system_clock::time_point updated_at;

  JobRecord(const std::string &id)
      : job_id(id), status("queued"),
        created_at(std::chrono::system_clock::now()),
        updated_at(std::chrono::system_clock::now()) {}
};

/**
 * @class JobManager
 * @brief Manages async simulation jobs with a thread pool.
 */
class JobManager {
public:
  using JobFunc = std::function<json()>;

  explicit JobManager(size_t max_workers = 2);
  ~JobManager();

  // Prevent copying
  JobManager(const JobManager &) = delete;
  JobManager &operator=(const JobManager &) = delete;

  /**
   * @brief Submit a job for execution.
   * @param func Function returning JSON result
   * @return Job ID
   */
  std::string submit(JobFunc func);

  /**
   * @brief Get job status and result.
   * @param job_id Job ID
   * @return JobRecord or nullptr if not found
   */
  std::shared_ptr<JobRecord> get(const std::string &job_id) const;

private:
  void worker_thread();
  std::string generate_id() const;

  std::vector<std::thread> workers_;
  std::queue<std::pair<std::string, JobFunc>> job_queue_;
  mutable std::mutex mutex_;
  std::condition_variable cv_;
  std::atomic<bool> stop_{false};

  std::unordered_map<std::string, std::shared_ptr<JobRecord>> jobs_;
};

} // namespace photonflow
