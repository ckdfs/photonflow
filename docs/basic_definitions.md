# PhotonFlow 基本定义与架构

## 目标
- 通过可复用的积木式模块搭建光/电链路（激光器、耦合器、PM、MZM、PD 等）。
- 使用复包络时域模型进行调制仿真，避免直接采样光载波。
- 在任意节点提供 OSA（光谱）与 ESA（电谱）视图。
- 从一开始就支持双偏振模型。
- 支持 CPU-only 与 GPU（torch 后端）。

## 建模思路
- 光学信号用复包络 $E(t)$ 表示，并显式声明中心频率 $f_0$。
- 电信号用实数或复数基带信号表示。
- 非理想因素通过可选参数开启或关闭。
- 仿真以有向图执行：器件是节点，端口连线为边，按拓扑顺序计算。
- 带宽参数（如 `bandwidth_hz`）为 0 表示不限制。

## Signal 定义
Signal 是仿真的统一数据对象。

最小字段：
- data: torch 张量
  - 光学标量：形状 [N]
  - 光学双偏振：形状 [2, N]（Jones 向量）
  - 电信号：形状 [N]（可实可复）
- fs: 采样率 (Hz)
- t0: 起始时间 (s)
- center_freq: 载频 (Hz，仅光学信号)
- pol_mode: "scalar" 或 "jones"
- meta: dict（单位、标签、来源等）

## Block（器件）定义
Block 是可复用器件单元，包含固定类型的端口。

通用接口：
- id: 唯一字符串
- type: 器件类型字符串
- params: 理想参数 dict
- nonideal: 非理想参数 dict（含 enable 开关）
- ports: 端口定义（optical / electrical / control）
- process(inputs, backend) -> outputs

Block 库提供参数默认值与范围，Graph 只保存用户覆盖值。

## Graph（图）定义
Graph 由节点和连线构成。

关键规则：
- 端口类型必须匹配（optical 对 optical，electrical 对 electrical）。
- Graph 会被编译为执行计划（拓扑排序）。
- 复合器件在编译时展开为子图。
- 在相同随机种子下仿真结果可复现。

## Composite（复合器件）
复合器件是图模板，在编译时展开。

示例：
- MZMComposite: Coupler -> 两臂 PM -> Coupler（含电学分路与推挽增益）
- DPMZMComposite: 两个 MZMComposite + 相位器 + 合束器

复合展开后所有子块仍可见，便于调试与优化。

## 非理想因素
每个 Block 可启用非理想行为。

默认（核心）项：
- 激光器：线宽、RIN、功率漂移
- PM/MZM：Vpi 误差、臂不平衡、插入损耗、偏置漂移
- 耦合器：分光比误差、相位误差、损耗
- PD：响应度、带宽、散粒噪声、热噪声

其他非理想项可在不改变 Graph 格式的情况下扩展。

## 后端
- 主后端：torch
- 支持 CPU 与 GPU；设备选择由全局设置决定。
- FFT 使用 torch.fft。

## 测量
- OSA：对 $E(t)$ 施加窗函数后 FFT 得到光谱。
- ESA：对 $i(t)$ 施加窗函数后 FFT 得到电谱。
- Scope（示波器）：对选定端口直接输出时域波形（用于电信号或光功率时域预览）。

测量仪器节点说明：
- **OSAProbe**：光谱分析仪探头，接受光学信号输入（`opt_in`），输出频谱数据。
- **ESAProbe**：电谱分析仪探头，接受电信号输入（`elec_in`），输出频谱数据。
- **ScopeProbe**：示波器探头，接受电信号输入（`elec_in`），输出时域波形数据。

观测仪器只包含输入端口，可并联在链路中进行无损测量，不改变信号流向。所有输出必须通过 `outputs.extra` 指定观测节点和端口。

## 结果与存储
- 小数据直接返回（JSON 友好或降采样）。
- 大时域结果可写入 HDF5/Zarr 并以路径引用。
