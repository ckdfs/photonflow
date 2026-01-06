/**
 * @file job_manager.cpp
 * @brief JobManager implementation.
 */

#include "photonflow/server/job_manager.hpp"

#include <iomanip>
#include <random>
#include <sstream>


namespace photonflow {

JobManager::JobManager(size_t max_workers) {
  for (size_t i = 0; i < max_workers; ++i) {
    workers_.emplace_back(&JobManager::worker_thread, this);
  }
}

JobManager::~JobManager() {
  {
    std::lock_guard<std::mutex> lock(mutex_);
    stop_ = true;
  }
  cv_.notify_all();
  for (auto &worker : workers_) {
    if (worker.joinable()) {
      worker.join();
    }
  }
}

std::string JobManager::generate_id() const {
  static std::random_device rd;
  static std::mt19937 gen(rd());
  static std::uniform_int_distribution<uint64_t> dis;

  std::stringstream ss;
  ss << std::hex << std::setfill('0') << std::setw(16) << dis(gen);
  ss << std::setw(16) << dis(gen);
  return ss.str();
}

std::string JobManager::submit(JobFunc func) {
  std::string job_id = generate_id();
  auto record = std::make_shared<JobRecord>(job_id);

  {
    std::lock_guard<std::mutex> lock(mutex_);
    jobs_[job_id] = record;
    job_queue_.push({job_id, std::move(func)});
  }
  cv_.notify_one();

  return job_id;
}

std::shared_ptr<JobRecord> JobManager::get(const std::string &job_id) const {
  std::lock_guard<std::mutex> lock(mutex_);
  auto it = jobs_.find(job_id);
  if (it != jobs_.end()) {
    return it->second;
  }
  return nullptr;
}

void JobManager::worker_thread() {
  while (true) {
    std::pair<std::string, JobFunc> job;

    {
      std::unique_lock<std::mutex> lock(mutex_);
      cv_.wait(lock, [this] { return stop_ || !job_queue_.empty(); });

      if (stop_ && job_queue_.empty()) {
        return;
      }

      job = std::move(job_queue_.front());
      job_queue_.pop();

      // Update status to running
      if (auto it = jobs_.find(job.first); it != jobs_.end()) {
        it->second->status = "running";
        it->second->updated_at = std::chrono::system_clock::now();
      }
    }

    // Execute job outside of lock
    try {
      json result = job.second();

      std::lock_guard<std::mutex> lock(mutex_);
      if (auto it = jobs_.find(job.first); it != jobs_.end()) {
        it->second->result = std::move(result);
        it->second->status = "done";
        it->second->updated_at = std::chrono::system_clock::now();
      }
    } catch (const std::exception &e) {
      std::lock_guard<std::mutex> lock(mutex_);
      if (auto it = jobs_.find(job.first); it != jobs_.end()) {
        it->second->error = e.what();
        it->second->status = "error";
        it->second->updated_at = std::chrono::system_clock::now();
      }
    }
  }
}

} // namespace photonflow
