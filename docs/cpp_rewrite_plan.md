# PhotonFlow C++ 重写实施计划

## 项目概述

本文档提供了将 PhotonFlow 的 Python 后端（当前使用 PyTorch）重写为 C++ 的完整计划，以实现：

- **启动时间**：从 2-5 秒减少到 <100ms
- **安装包体积**：从 2.8GB 减少到 50-200MB  
- **运行时性能**：比 Python+PyTorch 快 2-10 倍
- **跨平台支持**：Windows、Linux、macOS

## 当前系统架构

### Python 后端（待替换）
```
backend/
├── src/photonflow/
│   ├── core/
│   │   ├── graph.py          # Graph execution engine
│   │   ├── signal.py         # Signal data structure
│   │   ├── sim.py            # Simulation context
│   │   └── filters.py        # Digital filters
│   ├── blocks/
│   │   ├── base.py           # BaseBlock + Registry
│   │   ├── optical/          # 10 optical blocks
│   │   ├── electrical/       # 4 electrical blocks
│   │   └── detectors/        # 1 detector
│   ├── measurements/
│   │   └── spectrum.py       # OSA/ESA measurements
│   └── server/
│       ├── app.py            # FastAPI REST server
│       ├── sim_runner.py     # Job execution
│       └── job_manager.py    # Async job queue
```

**关键 Python 依赖**：
- `torch`：张量运算、FFT、复数数学（2.5GB！）
- `fastapi`：REST API 框架
- `uvicorn`：ASGI 服务器
- `jsonschema`：图结构校验

### 前端（保持不变）
- React + TypeScript + Vite
- 通过 REST API 通信（HTTP/JSON）

### 桌面应用包装器（保持不变）
- Tauri (Rust) - 以 sidecar 进程方式启动后端

## 目标 C++ 架构

### 项目结构
```
photonflow-cpp/
├── CMakeLists.txt
├── vcpkg.json                    # Dependency manifest
├── README.md
├── include/
│   └── photonflow/
│       ├── core/
│       │   ├── signal.hpp
│       │   ├── graph.hpp
│       │   ├── sim_context.hpp
│       │   └── filters.hpp
│       ├── blocks/
│       │   ├── base_block.hpp
│       │   ├── block_registry.hpp
│       │   ├── optical/
│       │   │   ├── laser.hpp
│       │   │   ├── fiber.hpp
│       │   │   ├── mzm.hpp
│       │   │   ├── dpmzm.hpp
│       │   │   ├── pm.hpp
│       │   │   ├── phase_shifter.hpp
│       │   │   ├── attenuator.hpp
│       │   │   ├── coupler.hpp
│       │   │   ├── optical_filter.hpp
│       │   │   └── polarization.hpp
│       │   ├── electrical/
│       │   │   ├── rf_source.hpp
│       │   │   ├── dc_source.hpp
│       │   │   ├── elec_splitter.hpp
│       │   │   └── elec_gain.hpp
│       │   └── detectors/
│       │       └── photodetector.hpp
│       ├── measurements/
│       │   └── spectrum.hpp
│       └── server/
│           ├── api.hpp
│           └── job_manager.hpp
├── src/
│   ├── core/
│   │   ├── signal.cpp
│   │   ├── graph.cpp
│   │   ├── sim_context.cpp
│   │   └── filters.cpp
│   ├── blocks/
│   │   ├── base_block.cpp
│   │   ├── block_registry.cpp
│   │   ├── optical/           # 10 implementation files
│   │   ├── electrical/        # 4 implementation files
│   │   └── detectors/         # 1 implementation file
│   ├── measurements/
│   │   └── spectrum.cpp
│   ├── server/
│   │   ├── api.cpp
│   │   ├── job_manager.cpp
│   │   └── main.cpp
│   └── schema/
│       └── validator.cpp
├── tests/
│   ├── test_signal.cpp
│   ├── test_graph.cpp
│   ├── test_fiber.cpp
│   └── test_mzm.cpp
└── schema/
    └── graph_schema.json      # 从 Python 版本复制
```

## 技术栈

### 核心语言
- **C++20** 或 **C++23**
- 编译器：MSVC 2022 (Windows)、GCC 13+ (Linux)、AppleClang 15+ (macOS)
- 构建系统：CMake 3.25+
- 包管理器：**vcpkg**（推荐用于跨平台）

### 核心库

#### HTTP 服务器
```cpp
// Crow - 轻量级、类似 Flask 的 API
#include <crow.h>
```
**选择理由**：易于使用、性能足够、可选 header-only 模式。

**备选方案**：Drogon（性能更高但更复杂）

#### 数值计算
```cpp
// 线性代数和矩阵运算
#include <Eigen/Dense>
#include <Eigen/Core>

// FFT（二选一）：
#include <Eigen/FFT>           // 更简单，与 Eigen 集成
// 或
#include <fftw3.h>             // 大规模变换更快
```

**选择 Eigen 的理由**： 
- 纯头文件（部署简单）
- 自动向量化优化性能优秀（SSE/AVX）
- API 类似 NumPy/PyTorch

**选择 FFTW3 的理由**：
- FFT 业界标准
- 大数据量时比 Eigen FFT 快 2-3 倍
- 用于 OpticalFiber 的 SSFM 实现

#### JSON 处理
```cpp
#include <nlohmann/json.hpp>
using json = nlohmann::json;
```
**选择理由**：最流行的 C++ JSON 库，错误处理优秀。

#### 日志
```cpp
#include <spdlog/spdlog.h>
```
**选择理由**：高性能异步日志，类似 Python 的 logging。

#### 测试
```cpp
#include <gtest/gtest.h>
```
**选择理由**：业界标准，类似 Python 的 unittest。

#### 可选：GPU 支持
```cpp
#include <cuda_runtime.h>
#include <cufft.h>
```
**注意**：先实现 CPU 版本，GPU 作为第二阶段。

### vcpkg.json 依赖
```json
{
  "name": "photonflow",
  "version": "0.1.0",
  "dependencies": [
    "crow",
    "eigen3",
    "fftw3",
    "nlohmann-json",
    "spdlog",
    "gtest",
    "fmt"
  ]
}
```

## 实施路线图

### 阶段 1：核心基础设施（第 1-2 周）

**优先级**：必须首先完成，其他模块依赖于此。

#### 1.1 Signal 类
文件：`include/photonflow/core/signal.hpp`、`src/core/signal.cpp`

**参考**：`backend/src/photonflow/core/signal.py`

**核心特性**：
```cpp
class Signal {
public:
    // 复数时域数据
    Eigen::VectorXcd data;
    
    // 采样率 (Hz)
    double fs;
    
    // 时间偏移 (秒)
    double t0;
    
    // 可选：光信号的中心频率
    std::optional<double> center_freq;
    
    // 偏振模式："scalar" 或 "jones"
    std::string pol_mode;
    
    // 元数据字典
    std::unordered_map<std::string, std::string> meta;
    
    // 构造函数
    Signal(const Eigen::VectorXcd& data, double fs, double t0 = 0.0);
    
    // 方法
    Signal clone() const;
    Eigen::VectorXd time() const;
    bool is_optical() const;
    bool is_jones() const;
    
    // Jones 矢量：data 形状为 [2, n_samples]
    // 使用 Eigen::MatrixXcd，2 行
};
```

**关键细节**：
- 使用 `Eigen::VectorXcd` 表示复双精度
- 对于偏振（Jones 矢量），使用 `Eigen::MatrixXcd`，2 行
- 时间数组：`t0 + Eigen::VectorXd::LinSpaced(n, 0, (n-1)/fs)`

#### 1.2 SimContext 类
文件：`include/photonflow/core/sim_context.hpp`

**参考**：`backend/src/photonflow/core/sim.py`

```cpp
struct SimConfig {
    std::string backend = "cpp";
    std::string device = "cpu";
    double fs = 0.0;              // 0 时自动确定
    double duration_s = 1e-6;
    int n_samples = 0;
    int oversample = 4;
    int seed = 0;
};

class SimContext {
private:
    SimConfig config_;
    double fs_;
    int n_samples_;
    std::mt19937 rng_;           // 随机数生成器
    
public:
    SimContext(const SimConfig& config, double fs, int n_samples);
    
    Eigen::VectorXd time(double t0 = 0.0) const;
    Eigen::VectorXcd zeros_complex(int n) const;
    Eigen::VectorXd randn(int n);  // 高斯噪声
};
```

#### 1.3 BaseBlock 类
文件：`include/photonflow/blocks/base_block.hpp`

**参考**：`backend/src/photonflow/blocks/base.py`

```cpp
class BaseBlock {
protected:
    std::string id_;
    nlohmann::json params_;
    nlohmann::json nonideal_;
    
public:
    virtual ~BaseBlock() = default;
    
    // 纯虚函数：在派生类中实现
    virtual std::unordered_map<std::string, Signal> 
        process(const std::unordered_map<std::string, Signal>& inputs,
                const SimContext& ctx) = 0;
    
    // 端口类型验证
    virtual std::optional<std::string> port_type(const std::string& port) const = 0;
    
    // 元数据
    virtual std::string block_type() const = 0;
    virtual nlohmann::json describe() const = 0;
};
```

#### 1.4 Block 注册表
文件：`include/photonflow/blocks/block_registry.hpp`

**模式**：单例 + 工厂注册

```cpp
class BlockRegistry {
private:
    std::unordered_map<std::string, 
        std::function<std::unique_ptr<BaseBlock>(const std::string&, 
                                                  const nlohmann::json&,
                                                  const nlohmann::json&)>> factories_;
    
    BlockRegistry() = default;
    
public:
    static BlockRegistry& instance();
    
    template<typename T>
    void register_block(const std::string& name) {
        factories_[name] = [](const std::string& id, 
                             const nlohmann::json& params,
                             const nlohmann::json& nonideal) {
            return std::make_unique<T>(id, params, nonideal);
        };
    }
    
    std::unique_ptr<BaseBlock> create(const std::string& type, 
                                      const std::string& id,
                                      const nlohmann::json& params,
                                      const nlohmann::json& nonideal);
    
    std::vector<std::string> list_types() const;
};

// 自动注册宏
#define REGISTER_BLOCK(ClassName, BlockTypeName) \
    namespace { \
        struct ClassName##Registrar { \
            ClassName##Registrar() { \
                BlockRegistry::instance().register_block<ClassName>(BlockTypeName); \
            } \
        }; \
        static ClassName##Registrar ClassName##_registrar_; \
    }
```

#### 1.5 图执行引擎
文件：`include/photonflow/core/graph.hpp`、`src/core/graph.cpp`

**参考**：`backend/src/photonflow/core/graph.py`

```cpp
struct Edge {
    std::string src;
    std::string src_port;
    std::string dst;
    std::string dst_port;
};

class Graph {
private:
    std::unordered_map<std::string, std::unique_ptr<BaseBlock>> nodes_;
    std::vector<Edge> edges_;
    std::vector<std::string> execution_order_;
    
    // 拓扑排序用于执行顺序
    void topological_sort();
    
public:
    // 从 JSON 加载
    static Graph from_json(const nlohmann::json& graph_json);
    
    // 编译图（验证、排序）
    void compile();
    
    // 运行仿真
    std::unordered_map<std::tuple<std::string, std::string>, Signal> 
        run(const SimConfig& config);
};
```

**关键算法**：使用 Kahn 算法的拓扑排序（与 Python 版本相同）。

### 阶段 2：基本 Blocks（第 3-4 周）

按此顺序实现（基于依赖关系的优先级）：

#### 2.1 信号源
1. **Laser**（`optical/laser.cpp`）- 生成光载波
2. **RFSource**（`electrical/rf_source.cpp`）- 生成射频信号
3. **DCSource**（`electrical/dc_source.cpp`）- 直流偏置

#### 2.2 调制器
4. **MZM**（`optical/mzm.cpp`）- 马赫-曾德尔调制器
   - **参考**：`backend/src/photonflow/blocks/optical/mzm.py`
   - **关键公式**：`E_out = 0.5 * E_in * (exp(i*phi1) + exp(i*phi2))`

5. **PM**（`optical/pm.cpp`）- 相位调制器

#### 2.3 传输
6. **OpticalFiber**（`optical/fiber.cpp`）- **最复杂**
   - **参考**：`backend/src/photonflow/blocks/optical/fiber.py`（299 行）
   - **算法**：分步傅里叶法（SSFM）
   - **库**：使用 FFTW3 进行 FFT
   
   **SSFM 核心循环**：
   ```cpp
   // 线性步骤（频域）
   Eigen::VectorXcd freq_response = calc_dispersion(omega, beta2, beta3, dz);
   signal_fft = fft.forward(signal);
   signal_fft = signal_fft.cwiseProduct(freq_response);
   signal = fft.inverse(signal_fft);
   
   // 非线性步骤（时域）
   if (gamma != 0) {
       Eigen::VectorXd power = signal.cwiseAbs2();
       signal = signal.cwiseProduct((1j * gamma * dz * power).exp());
   }
   ```

#### 2.4 检测
7. **Photodetector**（`detectors/photodetector.cpp`）
   - 光信号 → 电信号转换

#### 2.5 工具模块
8. **Attenuator**、**Coupler**、**Splitter** - 简单线性操作

### 阶段 3：服务器 & API（第 5 周）

#### 3.1 REST API 服务器
文件：`src/server/api.cpp`、`src/server/main.cpp`

**参考**：`backend/src/photonflow/server/app.py`

```cpp
#include <crow.h>
#include "photonflow/core/graph.hpp"
#include "photonflow/server/job_manager.hpp"

int main() {
    crow::SimpleApp app;
    JobManager job_manager;
    
    // 端点：POST /graph/run
    CROW_ROUTE(app, "/graph/run")
        .methods("POST"_method)
        ([&](const crow::request& req) {
            try {
                auto graph_json = json::parse(req.body);
                auto job_id = job_manager.submit(graph_json);
                
                json response = {{"job_id", job_id}};
                return crow::response(200, response.dump());
            } catch (const std::exception& e) {
                json error = {{"error", e.what()}};
                return crow::response(400, error.dump());
            }
        });
    
    // 端点：GET /graph/status/<job_id>
    CROW_ROUTE(app, "/graph/status/<string>")
        ([&](const std::string& job_id) {
            auto status = job_manager.get_status(job_id);
            return crow::response(status.dump());
        });
    
    // 端点：GET /blocks/list
    CROW_ROUTE(app, "/blocks/list")
        ([]() {
            auto types = BlockRegistry::instance().list_types();
            json response = {{"blocks", types}};
            return crow::response(response.dump());
        });
    
    // 为前端设置 CORS 头
    app.bindaddr("0.0.0.0").port(8000).multithreaded().run();
}
```

#### 3.2 任务管理器
文件：`src/server/job_manager.cpp`

**参考**：`backend/src/photonflow/server/job_manager.py`

```cpp
class JobManager {
private:
    std::unordered_map<std::string, JobStatus> jobs_;
    std::mutex mutex_;
    std::thread worker_thread_;
    
public:
    std::string submit(const nlohmann::json& graph_json);
    nlohmann::json get_status(const std::string& job_id);
    nlohmann::json get_result(const std::string& job_id);
    
private:
    void process_job(const std::string& job_id);
};
```

**使用** `std::async` 或线程池进行异步执行。

### 阶段 4：测量（第 6 周）

#### 4.1 频谱分析
文件：`src/measurements/spectrum.cpp`

**参考**：`backend/src/photonflow/measurements/spectrum.py`

**函数**：
- `osa()` - 光谱分析仪
- `esa()` - 电频谱分析仪

**关键算法**：
```cpp
Eigen::VectorXcd fft_result = fft.forward(signal.data);
Eigen::VectorXd power_spectral_density = fft_result.cwiseAbs2();
Eigen::VectorXd freq = fftfreq(n, 1.0/signal.fs);

// 转换为 dBm/Hz
Eigen::VectorXd psd_dbm = 10.0 * power_spectral_density.array().log10() + 30.0;
```

### 阶段 5：测试与验证（第 7 周）

**目标**：确保 C++ 结果与 Python 结果误差 <0.1%。

#### 测试用例（从 Python 移植）
1. **test_signal.cpp**：Signal 创建、克隆、时间数组
2. **test_graph.cpp**：图解析、拓扑排序、执行
3. **test_mzm.cpp**：MZM 传递函数 vs. 解析解
4. **test_fiber.cpp**：光纤色散 vs. 解析解
5. **集成测试**：在 Python 和 C++ 中运行相同的图，比较输出

**示例**：
```cpp
TEST(FiberTest, ChromaticDispersion) {
    // Python 参考：backend/tests/test_graph_runs.py
    SimConfig config;
    config.fs = 100e9;  // 100 GHz
    config.n_samples = 1024;
    
    Fiber fiber("fiber1", {{"length_m", 80000}, {"beta2_s2_per_m", -21e-27}}, {});
    
    Signal input = create_gaussian_pulse(1e-12);  // 1 ps 脉冲
    SimContext ctx(config, config.fs, config.n_samples);
    auto outputs = fiber.process({{"opt_in", input}}, ctx);
    
    Signal output = outputs["opt_out"];
    double output_width = measure_pulse_width(output);
    double expected_width = 1.5e-12;  // 色散公式的预期值
    
    EXPECT_NEAR(output_width, expected_width, 0.1e-12);
}
```

### 阶段 6：集成 Tauri（第 8 周）

#### 6.1 构建脚本更新

**CMake 安装目标**：
```cmake
install(TARGETS photonflow-server
    RUNTIME DESTINATION bin
)
```

**Windows**（`scripts/build_windows.ps1`）：
```powershell
# 构建 C++ 后端
cd backend-cpp
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
cmake --install build --prefix dist

# 复制到 Tauri binaries
Copy-Item dist/bin/photonflow-server.exe src-tauri/binaries/server-x86_64-pc-windows-msvc.exe
```

**Linux/macOS**（`scripts/build_all.sh`）：
```bash
cd backend-cpp
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release
cmake --build build
cmake --install build --prefix dist

cp dist/bin/photonflow-server ../src-tauri/binaries/server-$TARGET
```

#### 6.2 Tauri 配置
无需更改 - 已在 `main.rs` 中使用 `Command` API。

## 关键实现要点

### 1. 复数处理
**Python**：`torch.complex128`  
**C++**：`std::complex<double>` 或 `Eigen::VectorXcd`

```cpp
// 逐元素操作
Eigen::VectorXcd result = a.cwiseProduct(b);  // a * b（逐元素）

// 相位计算
Eigen::VectorXcd phase_term = (1i * phi).array().exp();

// 绝对值
Eigen::VectorXd magnitude = signal.cwiseAbs();
```

### 2. FFT 使用

**Eigen FFT**（更简单）：
```cpp
#include <Eigen/FFT>

Eigen::FFT<double> fft;
Eigen::VectorXcd freq_domain = fft.fwd(time_domain);
Eigen::VectorXcd time_domain_back = fft.inv(freq_domain);
```

**FFTW3**（更快，用于大型 FFT）：
```cpp
#include <fftw3.h>

fftw_complex *in = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * n);
fftw_complex *out = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * n);

fftw_plan plan = fftw_plan_dft_1d(n, in, out, FFTW_FORWARD, FFTW_ESTIMATE);
fftw_execute(plan);

fftw_destroy_plan(plan);
fftw_free(in);
fftw_free(out);
```

### 3. JSON Schema 验证
使用 Python 版本现有的 `graph_schema.json`。

**库**：`nlohmann/json-schema-validator`（或手动实现）

```cpp
#include <nlohmann/json-schema.hpp>

nlohmann::json_schema::json_validator validator;
validator.set_root_schema(schema_json);

try {
    validator.validate(graph_json);
} catch (const std::exception& e) {
    // 验证失败
}
```

### 4. 随机数生成
```cpp
#include <random>

std::mt19937 rng(seed);
std::normal_distribution<double> dist(0.0, 1.0);

Eigen::VectorXd noise(n);
for (int i = 0; i < n; ++i) {
    noise[i] = dist(rng);
}
```

### 5. 从 JSON 提取参数
```cpp
double length = params.value("length_m", 1000.0);  // 默认 1000.0
bool enable_nonideal = nonideal.value("enable", false);

// 嵌套参数
if (nonideal.contains("pmd_dgd_s")) {
    double pmd = nonideal["pmd_dgd_s"].get<double>();
}
```

## 构建指南（给 LLM）

### 初始设置
```bash
# 安装 vcpkg
git clone https://github.com/microsoft/vcpkg.git
./vcpkg/bootstrap-vcpkg.sh  # Windows 上用 .bat

# 安装依赖
vcpkg install crow eigen3 fftw3 nlohmann-json spdlog gtest

# 配置 CMake
cmake -B build -S . -DCMAKE_TOOLCHAIN_FILE=path/to/vcpkg/scripts/buildsystems/vcpkg.cmake
cmake --build build
```

### 开发工作流
```bash
# 构建
cmake --build build

# 运行测试
cd build && ctest

# 运行服务器
./build/src/server/photonflow-server
```

## 成功标准

### 功能要求
- [ ] 所有 16 个 blocks 实现并测试
- [ ] 图执行结果与 Python 版本匹配（误差 < 0.1%）
- [ ] REST API 与现有前端兼容
- [ ] 启动时间 < 500ms
- [ ] 安装包体积 < 100MB（不含 CUDA）

### 性能要求
- [ ] Fiber SSFM：比 Python 快 > 2 倍
- [ ] FFT 操作：比 PyTorch CPU 快 > 3 倍
- [ ] 完整图执行：总体快 > 5 倍

### 质量要求
- [ ] 单元测试覆盖率 > 80%
- [ ] 无内存泄漏（valgrind 检查通过）
- [ ] 跨平台构建（Windows/Linux/macOS）
- [ ] 所有公共 API 有文档

## 参考资料

### 需要研究的关键 Python 文件
1. `backend/src/photonflow/core/graph.py` - 图执行引擎
2. `backend/src/photonflow/core/signal.py` - 信号结构
3. `backend/src/photonflow/blocks/optical/fiber.py` - SSFM 实现
4. `backend/src/photonflow/blocks/optical/mzm.py` - 调制器数学
5. `backend/src/photonflow/server/app.py` - REST API 端点
6. `backend/tests/test_graph_runs.py` - 集成测试

### 外部资源
- **Eigen 教程**：https://eigen.tuxfamily.org/dox/GettingStarted.html
- **FFTW 手册**：https://www.fftw.org/fftw3_doc/
- **Crow 框架**：https://crowcpp.org/
- **nlohmann/json**：https://json.nlohmann.me/

## LLM Agent 注意事项

1. **从阶段 1 开始 - 核心基础设施**。不要跳到 blocks。
2. **始终使用 Eigen** - 避免混用原始数组。
3. **测试每个模块** 后再进入下一阶段。
4. **完全匹配 Python 行为** - 以 Python 版本为参考。
5. **稍后优化** - 正确性第一，性能第二。
6. **遇到不清楚的 Python 代码要询问**。
7. **保持 JSON schema 兼容性** - 前端依赖于此。
8. **使用现代 C++ 特性**：智能指针、std::optional、结构化绑定。

## 示例代码片段

### Laser Block 完整实现
```cpp
// include/photonflow/blocks/optical/laser.hpp
#pragma once
#include "photonflow/blocks/base_block.hpp"

namespace photonflow {

class Laser : public BaseBlock {
public:
    Laser(const std::string& id, const nlohmann::json& params, const nlohmann::json& nonideal);
    
    std::unordered_map<std::string, Signal> 
        process(const std::unordered_map<std::string, Signal>& inputs,
                const SimContext& ctx) override;
    
    std::optional<std::string> port_type(const std::string& port) const override;
    std::string block_type() const override { return "Laser"; }
    nlohmann::json describe() const override;
};

} // namespace photonflow

// src/blocks/optical/laser.cpp
#include "photonflow/blocks/optical/laser.hpp"
#include <cmath>

namespace photonflow {

Laser::Laser(const std::string& id, const nlohmann::json& params, const nlohmann::json& nonideal)
    : BaseBlock(id, params, nonideal) {}

std::unordered_map<std::string, Signal> 
Laser::process(const std::unordered_map<std::string, Signal>& inputs, const SimContext& ctx) {
    // 提取参数
    double power_dbm = params_.value("power_dbm", 0.0);
    double linewidth_hz = params_.value("linewidth_hz", 0.0);
    double frequency_hz = params_.value("frequency_hz", 193.1e12);
    
    // 功率转换为线性标度
    double power_mw = std::pow(10.0, power_dbm / 10.0);
    double power_w = power_mw / 1000.0;
    
    // 生成载波
    int n = ctx.n_samples();
    Eigen::VectorXcd data(n);
    
    if (linewidth_hz > 0) {
        // 相位噪声模型
        double phase = 0.0;
        double phase_std = std::sqrt(2.0 * M_PI * linewidth_hz / ctx.fs());
        
        for (int i = 0; i < n; ++i) {
            phase += ctx.randn() * phase_std;
            data[i] = std::sqrt(power_w) * std::exp(std::complex<double>(0, phase));
        }
    } else {
        // 纯 CW
        data.setConstant(std::sqrt(power_w));
    }
    
    Signal output(data, ctx.fs(), ctx.t0());
    output.center_freq = frequency_hz;
    output.pol_mode = "scalar";
    
    return {{"opt_out", output}};
}

std::optional<std::string> Laser::port_type(const std::string& port) const {
    if (port == "opt_out") return "optical";
    return std::nullopt;
}

nlohmann::json Laser::describe() const {
    return {
        {"ports", {{"opt_out", "optical"}}},
        {"spec", {
            {"params", {
                {"power_dbm", {{"type", "float"}, {"default", 0.0}, {"unit", "dBm"}}},
                {"linewidth_hz", {{"type", "float"}, {"default", 0.0}, {"unit", "Hz"}}},
                {"frequency_hz", {{"type", "float"}, {"default", 193.1e12}, {"unit", "Hz"}}}
            }}
        }}
    };
}

// 自动注册
REGISTER_BLOCK(Laser, "Laser");

} // namespace photonflow
```

此示例展示了：
- 带默认值的参数提取
- Eigen 向量操作
- 复指数运算
- 随机数生成
- Signal 构造
- 自动注册模式

---

**实施计划完**

祝 C++ 实现顺利！按阶段顺序进行，每一步都要彻底测试。
