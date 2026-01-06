cmake_minimum_required(VERSION 3.25)
project(photonflow VERSION 0.1.0 LANGUAGES CXX)

# C++20 标准
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# MSVC 编译选项
if(MSVC)
    add_compile_options(/W4 /utf-8)
    add_compile_definitions(_USE_MATH_DEFINES NOMINMAX)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 导出编译命令供 clangd 使用
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# 查找依赖包
find_package(Eigen3 CONFIG REQUIRED)
find_package(nlohmann_json CONFIG REQUIRED)
find_package(spdlog CONFIG REQUIRED)
find_package(fmt CONFIG REQUIRED)
find_package(GTest CONFIG REQUIRED)

# 包含目录
include_directories(${CMAKE_SOURCE_DIR}/include)

# ============== 核心库 ==============
add_library(photonflow_core STATIC
    # Core
    src/core/signal.cpp
    src/core/sim_context.cpp
    src/core/graph.cpp
    # Blocks infrastructure
    src/blocks/base_block.cpp
    src/blocks/block_registry.cpp
    # Optical blocks
    src/blocks/optical/laser.cpp
    src/blocks/optical/mzm.cpp
    src/blocks/optical/pm.cpp
    # Electrical blocks
    src/blocks/electrical/rf_source.cpp
    src/blocks/electrical/dc_source.cpp
    # Detectors
    src/blocks/detectors/photodetector.cpp
)

target_link_libraries(photonflow_core
    PUBLIC
        Eigen3::Eigen
        nlohmann_json::nlohmann_json
        spdlog::spdlog
        fmt::fmt
)

target_include_directories(photonflow_core PUBLIC
    $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# ============== 测试 ==============
enable_testing()

add_executable(photonflow_tests
    tests/test_signal.cpp
    tests/test_sim_context.cpp
    tests/test_graph.cpp
    tests/test_blocks.cpp
)

target_link_libraries(photonflow_tests
    PRIVATE
        photonflow_core
        GTest::gtest
        GTest::gtest_main
)

include(GoogleTest)
gtest_discover_tests(photonflow_tests)

# ============== 安装配置 ==============
install(TARGETS photonflow_core
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)

install(DIRECTORY include/photonflow
    DESTINATION include
)
