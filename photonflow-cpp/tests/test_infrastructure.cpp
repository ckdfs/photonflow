/**
 * @file test_infrastructure.cpp
 * @brief Unit tests for BaseBlock, BlockRegistry, and JobManager.
 */

#include "photonflow/blocks/base_block.hpp"
#include "photonflow/blocks/block_registry.hpp"
#include "photonflow/server/job_manager.hpp"
#include <chrono>
#include <gtest/gtest.h>
#include <set>
#include <thread>

using namespace photonflow;

// ===================== Test Block for BaseBlock Tests =====================

class TestBlock : public BaseBlock {
public:
  TestBlock(const std::string &id, const json &params, const json &nonideal)
      : BaseBlock(id, params, nonideal) {}

  std::unordered_map<std::string, Signal>
  process(const std::unordered_map<std::string, Signal> & /*inputs*/,
          SimContext & /*ctx*/) override {
    return {};
  }

  std::optional<std::string>
  port_type(const std::string & /*port*/) const override {
    return std::nullopt;
  }

  std::string block_type() const override { return "TestBlock"; }
  json describe() const override { return {}; }

  // Expose protected methods for testing
  template <typename T>
  T test_get_param(const std::string &key, const T &default_value) const {
    return get_param(key, default_value);
  }

  template <typename T>
  T test_get_nonideal(const std::string &key, const T &default_value) const {
    return get_nonideal(key, default_value);
  }
};

// ===================== BaseBlock Tests =====================

class BaseBlockTest : public ::testing::Test {};

TEST_F(BaseBlockTest, GetParam_NumberAsNumber) {
  json params = {{"value", 3.14}};
  TestBlock block("test", params, {});

  double result = block.test_get_param("value", 0.0);
  EXPECT_DOUBLE_EQ(result, 3.14);
}

TEST_F(BaseBlockTest, GetParam_StringToDouble) {
  json params = {{"value", "2.718"}};
  TestBlock block("test", params, {});

  double result = block.test_get_param("value", 0.0);
  EXPECT_DOUBLE_EQ(result, 2.718);
}

TEST_F(BaseBlockTest, GetParam_StringToInt) {
  json params = {{"count", "42"}};
  TestBlock block("test", params, {});

  int result = block.test_get_param("count", 0);
  EXPECT_EQ(result, 42);
}

TEST_F(BaseBlockTest, GetParam_DefaultValue) {
  json params = {};
  TestBlock block("test", params, {});

  double result = block.test_get_param("missing", 99.9);
  EXPECT_DOUBLE_EQ(result, 99.9);
}

TEST_F(BaseBlockTest, GetParam_NegativeStringNumber) {
  json params = {{"value", "-123.456"}};
  TestBlock block("test", params, {});

  double result = block.test_get_param("value", 0.0);
  EXPECT_DOUBLE_EQ(result, -123.456);
}

TEST_F(BaseBlockTest, GetNonideal_StringToDouble) {
  json nonideal = {{"noise", "0.01"}};
  TestBlock block("test", {}, nonideal);

  double result = block.test_get_nonideal("noise", 0.0);
  EXPECT_DOUBLE_EQ(result, 0.01);
}

TEST_F(BaseBlockTest, GetNonideal_DefaultValue) {
  TestBlock block("test", {}, {});

  double result = block.test_get_nonideal("missing", 1.0);
  EXPECT_DOUBLE_EQ(result, 1.0);
}

// ===================== BlockRegistry Tests =====================

class BlockRegistryTest : public ::testing::Test {
protected:
  BlockRegistry &registry = BlockRegistry::instance();
};

TEST_F(BlockRegistryTest, CreateUnknownType_ReturnsNull) {
  auto block = registry.create("NonExistentBlockType", "test_id", {}, {});
  EXPECT_EQ(block, nullptr);
}

TEST_F(BlockRegistryTest, HasType_ExistingType) {
  EXPECT_TRUE(registry.has_type("Laser"));
  EXPECT_TRUE(registry.has_type("MZM"));
}

TEST_F(BlockRegistryTest, HasType_NonExistentType) {
  EXPECT_FALSE(registry.has_type("FakeBlock123"));
}

TEST_F(BlockRegistryTest, ListTypes_NotEmpty) {
  auto types = registry.list_types();
  EXPECT_FALSE(types.empty());
  EXPECT_GE(types.size(), 10u); // We have at least 10 block types
}

TEST_F(BlockRegistryTest, GetSpecs_ContainsAllTypes) {
  auto specs = registry.get_specs();
  auto types = registry.list_types();

  for (const auto &type : types) {
    EXPECT_TRUE(specs.contains(type)) << "Missing spec for: " << type;
  }
}

TEST_F(BlockRegistryTest, Create_WithParams) {
  json params = {{"power_dbm", 10.0}, {"wavelength_nm", 1550.0}};
  auto block = registry.create("Laser", "laser_test", params, {});

  ASSERT_NE(block, nullptr);
  EXPECT_EQ(block->id(), "laser_test");
  EXPECT_EQ(block->block_type(), "Laser");
}

// ===================== JobManager Tests =====================

class JobManagerTest : public ::testing::Test {};

TEST_F(JobManagerTest, SubmitAndGet_SimpleJob) {
  JobManager manager(1);

  std::string job_id =
      manager.submit([]() -> json { return {{"result", "success"}}; });

  EXPECT_FALSE(job_id.empty());

  // Wait for job to complete
  std::this_thread::sleep_for(std::chrono::milliseconds(100));

  auto record = manager.get(job_id);
  ASSERT_NE(record, nullptr);
  EXPECT_EQ(record->job_id, job_id);
}

TEST_F(JobManagerTest, Get_NonExistentJob) {
  JobManager manager(1);

  auto record = manager.get("non_existent_job_id");
  EXPECT_EQ(record, nullptr);
}

TEST_F(JobManagerTest, JobStatus_TransitionsToComplete) {
  JobManager manager(1);

  std::string job_id = manager.submit([]() -> json {
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    return {{"value", 42}};
  });

  // Initially should be queued or running
  auto record = manager.get(job_id);
  ASSERT_NE(record, nullptr);

  // Wait for completion
  std::this_thread::sleep_for(std::chrono::milliseconds(200));

  record = manager.get(job_id);
  EXPECT_EQ(record->status, "done");
  ASSERT_TRUE(record->result.has_value());
  EXPECT_EQ((*record->result)["value"], 42);
}

TEST_F(JobManagerTest, MultipleJobs_AllComplete) {
  JobManager manager(2);

  std::vector<std::string> job_ids;
  for (int i = 0; i < 5; ++i) {
    int val = i;
    job_ids.push_back(
        manager.submit([val]() -> json { return {{"index", val}}; }));
  }

  // Wait for all jobs
  std::this_thread::sleep_for(std::chrono::milliseconds(500));

  for (size_t i = 0; i < job_ids.size(); ++i) {
    auto record = manager.get(job_ids[i]);
    ASSERT_NE(record, nullptr);
    EXPECT_EQ(record->status, "done");
    ASSERT_TRUE(record->result.has_value());
    EXPECT_EQ((*record->result)["index"], static_cast<int>(i));
  }
}

TEST_F(JobManagerTest, JobWithError_CapturesError) {
  JobManager manager(1);

  std::string job_id = manager.submit([]() -> json {
    throw std::runtime_error("Test error");
    return {}; // Never reached
  });

  // Wait for job to complete
  std::this_thread::sleep_for(std::chrono::milliseconds(100));

  auto record = manager.get(job_id);
  ASSERT_NE(record, nullptr);
  EXPECT_EQ(record->status, "error");
  ASSERT_TRUE(record->error.has_value());
  EXPECT_NE(record->error->find("Test error"), std::string::npos);
}

TEST_F(JobManagerTest, UniqueJobIds) {
  JobManager manager(1);

  std::set<std::string> ids;
  for (int i = 0; i < 10; ++i) {
    ids.insert(manager.submit([]() -> json { return {}; }));
  }

  // All IDs should be unique
  EXPECT_EQ(ids.size(), 10u);
}
