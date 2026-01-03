# 参数字典、Graph JSON 与 UI 交互流程

## 参数字典约定
Block 参数定义存在于 Block 库中，Graph 仅保存用户值。

每个 Block 有两类参数：
- params: 理想参数
- nonideal: 非理想参数（含 enable 开关）

默认值约定（重要）：
- 所有参数的默认值必须是数值 / 布尔 / 字符串，不能是 `null/None`。
- 对于“关闭效果”的参数，使用 0 或 false 作为默认值，例如 `bandwidth_hz=0` 表示不限制带宽，噪声/失配默认 0。
- 枚举类参数默认取 options 的第一个值（例如 `bandwidth_kind="rect"`）。

参数规格示例（定义在 Block 库中，不直接写入 Graph）：

```json
{
  "params": {
    "Vpi": {"type": "float", "default": 3.5, "unit": "V", "min": 0.1, "max": 20.0},
    "phi_bias": {"type": "float", "default": 0.0, "unit": "rad", "min": -3.14, "max": 3.14},
    "bandwidth_hz": {"type": "float", "default": 0.0, "unit": "Hz"},
    "bandwidth_kind": {"type": "enum", "default": "rect", "options": ["rect", "rc"]}
  },
  "nonideal": {
    "enable": {"type": "bool", "default": false},
    "loss_db": {"type": "float", "default": 0.0, "unit": "dB", "min": 0.0, "max": 20.0},
    "vpi_error_pct": {"type": "float", "default": 0.0, "unit": "%", "min": -20.0, "max": 20.0},
    "drive_noise_rms": {"type": "float", "default": 0.0, "unit": "V"},
    "bias_error_rad": {"type": "float", "default": 0.0, "unit": "rad"}
  }
}
```

Block 规格在后端以 `/blocks/specs` 返回，包含 `ports` 与 `spec`：

```json
{
  "PM": {
    "ports": {"opt_in": "optical", "elec_in": "electrical", "opt_out": "optical"},
    "spec": {"params": { ... }, "nonideal": { ... }},
    "composite": false
  }
}
```

Graph 中的参数值示例（项目 JSON 内保存）：

```json
{
  "params": {"Vpi": 4.0, "phi_bias": 0.2, "bandwidth_hz": 40e9, "bandwidth_kind": "rc"},
  "nonideal": {"enable": true, "loss_db": 2.5, "vpi_error_pct": -5.0, "drive_noise_rms": 0.02}
}
```

全局仿真设置位于顶层 sim：
- backend: "torch"
- device: "cpu" 或 "cuda"
- fs: 数值或 "auto"（当 fs 为 auto 时，按图中器件估算最高频率）
- oversample: 整数（默认 4）
- fs_min / fs_max: 采样率下限/上限（0 表示不限制）
- seed: 整数
- window: "hann"、"blackman" 等
- chunk: 可选整数（分块执行，按采样点，OSA/ESA 按块功率加权平均）
- duration_s: 仿真时长（秒）
- n_samples: 可选，直接指定采样点数
- min_samples / max_samples: 采样点数下限/上限（0 表示不限制）

仿真参数字典（默认值）：

| 参数 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| backend | string | "torch" | 后端类型 |
| device | string | "cpu" | 设备类型 |
| fs | number/string | "auto" | 采样率，auto 则自动估计 |
| fs_min | float | 0.0 | 采样率下限（0 表示不限制） |
| fs_max | float | 0.0 | 采样率上限（0 表示不限制） |
| oversample | int | 4 | 过采样倍率 |
| seed | int | 0 | 随机种子 |
| window | string | "hann" | 窗函数 |
| chunk | int | 0 | 分块长度（采样点，频谱按块加权平均） |
| duration_s | float | 1e-6 | 仿真时长 |
| n_samples | int | 不填写 | 由 duration_s 与 fs 自动推导 |
| min_samples | int | 0 | 采样点数下限（0 表示不限制） |
| max_samples | int | 0 | 采样点数上限（0 表示不限制） |

## Graph JSON 格式
顶层结构：

```json
{
  "version": "0.1",
  "sim": {
    "backend": "torch",
    "device": "cuda",
    "fs": "auto",
    "oversample": 4,
    "seed": 1234,
    "window": "hann"
  },
  "nodes": [
    {
      "id": "laser1",
      "type": "Laser",
      "params": {"power_dbm": 10.0, "linewidth_hz": 1e5},
      "nonideal": {"enable": true}
    },
    {
      "id": "pm1",
      "type": "PM",
      "params": {"Vpi": 4.0, "phi_bias": 0.0},
      "nonideal": {"enable": true, "loss_db": 2.0}
    },
    {
      "id": "osa1",
      "type": "OSAProbe",
      "params": {"window": "hann", "ref": 1.0, "include_power": true}
    },
    {
      "id": "pd1",
      "type": "PD",
      "params": {"responsivity": 0.8, "bandwidth_hz": 40e9},
      "nonideal": {"enable": true}
    },
    {
      "id": "esa1",
      "type": "ESAProbe",
      "params": {"window": "hann", "ref": 1.0}
    }
  ],
  "edges": [
    {"src": "laser1", "src_port": "opt_out", "dst": "pm1", "dst_port": "opt_in"},
    {"src": "pm1", "src_port": "opt_out", "dst": "pd1", "dst_port": "opt_in"},
    {"src": "pm1", "src_port": "opt_out", "dst": "osa1", "dst_port": "opt_in"},
    {"src": "pd1", "src_port": "elec_out", "dst": "esa1", "dst_port": "elec_in"}
  ],
  "outputs": {
    "extra": [
      {"node": "osa1", "port": "opt_in", "kind": "osa"},
      {"node": "esa1", "port": "elec_in", "kind": "esa"}
    ]
  }
}
```

说明：
- 复合节点（MZM、DPMZM）允许直接出现在 nodes 中，编译器会展开。
- 端口由 Block 类型固定，编译时做兼容性校验。
- 输出 `kind` 支持：`osa` / `esa` / `time`（时域预览）。
- 输出必须通过观测仪器节点（如 OSAProbe/ESAProbe/ScopeProbe）接入，并通过 `outputs.extra` 指定；`port` 使用观测仪器的输入端口（`opt_in` / `elec_in`）。
- 观测仪器只包含输入端口，可并联在链路中，不改变信号流向。
- 输出参数 `params` 可包含 `window` / `ref` / `include_power`。

输出参数 `params`（OSA/ESA）：

| 参数 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| window | string | sim.window | 窗函数（hann/hamming/blackman/rect/kaiser） |
| ref | float | 1.0 | 参考功率（线性） |
| include_power | bool | false | 是否返回线性功率数组 |

## 器件参数字典（自动生成）
以下表格由脚本从后端 `/blocks/specs` 自动生成，确保与实现一致。

生成命令：

```bash
conda run -n photonflow bash -lc "PYTHONPATH=backend/src python backend/scripts/generate_param_docs.py"
```

<!-- AUTO-GENERATED:PARAMS:START -->
### Attenuator
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| loss_db | float | 0.0 | dB | 插入损耗（幅度乘以 10^(-L/20)）；公式: [ATT-1](physics_models.md#formula_index)；参考: [光衰减器](physics_models.md#attenuator) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [光衰减器](physics_models.md#attenuator) |

### Coupler
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| split_ratio | float | 0.5 |  | 功率分配比 k；公式: [CPL-1](physics_models.md#formula_index)；参考: [耦合器](physics_models.md#coupler) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [耦合器](physics_models.md#coupler) |
| split_ratio_error | float | 0.0 |  | 分光比误差 Δk；公式: [CPL-1](physics_models.md#formula_index)；参考: [耦合器](physics_models.md#coupler) |
| phase_error | float | 0.0 | rad | 相位失配（rad）；参考: [耦合器](physics_models.md#coupler) |
| loss_db | float | 0.0 | dB | 插入损耗（幅度乘以 10^(-L/20)）；公式: [ATT-1](physics_models.md#formula_index)；参考: [耦合器](physics_models.md#coupler) |

### DCSource
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| voltage | float | 0.0 | V | 直流电压 V_dc；公式: [ELEC-2](physics_models.md#formula_index)；参考: [电信号源](physics_models.md#electrical) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [电信号源](physics_models.md#electrical) |
| offset_error | float | 0.0 | V | 直流误差；参考: [电信号源](physics_models.md#electrical) |
| noise_rms | float | 0.0 | V | 噪声 RMS；参考: [电信号源](physics_models.md#electrical) |

### DPMZM
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| Vpi | float | 3.5 | V | 半波电压，调制深度 m=πV/Vpi；公式: [DPMZM-1](physics_models.md#formula_index)；参考: [DPMZM](physics_models.md#dpmzm) |
| drive_mode | enum | push_pull |  | 驱动模式（push_pull:推挽，single_arm:单臂）；公式: [MZM-4](physics_models.md#formula_index)；options: push_pull/single_arm；参考: [DPMZM](physics_models.md#dpmzm) |
| phi_bias_i | float | 0.0 | rad | I 路偏置（rad）；公式: [DPMZM-1](physics_models.md#formula_index)；参考: [DPMZM](physics_models.md#dpmzm) |
| phi_bias_q | float | 0.0 | rad | Q 路偏置（rad）；公式: [DPMZM-1](physics_models.md#formula_index)；参考: [DPMZM](physics_models.md#dpmzm) |
| phi_q | float | 1.57079632679 | rad | I/Q 相位差（理想 π/2）；公式: [DPMZM-1](physics_models.md#formula_index)；参考: [DPMZM](physics_models.md#dpmzm) |
| bandwidth_hz | float | 0.0 | Hz | 截止频率 f_c，0 表示不限制带宽；公式: [LP-1](physics_models.md#formula_index)；参考: [DPMZM](physics_models.md#dpmzm) |
| bandwidth_kind | enum | rect |  | 低通模型（rect:矩形，rc:一阶RC）；公式: [LP-1](physics_models.md#formula_index)；options: rect/rc；参考: [DPMZM](physics_models.md#dpmzm) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [DPMZM](physics_models.md#dpmzm) |
| loss_db | float | 0.0 | dB | 插入损耗（幅度乘以 10^(-L/20)）；公式: [ATT-1](physics_models.md#formula_index)；参考: [DPMZM](physics_models.md#dpmzm) |
| vpi_error_pct | float | 0.0 | % | Vpi 误差百分比；参考: [DPMZM](physics_models.md#dpmzm) |
| arm_ratio_db | float | 0.0 | dB | 臂幅度不平衡（dB）；参考: [DPMZM](physics_models.md#dpmzm) |
| phase_error | float | 0.0 | rad | 相位失配（rad）；参考: [DPMZM](physics_models.md#dpmzm) |
| iq_phase_error | float | 0.0 | rad | I/Q 相位误差（rad）；参考: [DPMZM](physics_models.md#dpmzm) |
| iq_imbalance_db | float | 0.0 | dB | I/Q 幅度失衡（dB）；参考: [DPMZM](physics_models.md#dpmzm) |
| drive_noise_rms | float | 0.0 | V | 驱动电压噪声 RMS；参考: [DPMZM](physics_models.md#dpmzm) |
| bias_error_i | float | 0.0 | rad | I 路偏置误差；参考: [DPMZM](physics_models.md#dpmzm) |
| bias_error_q | float | 0.0 | rad | Q 路偏置误差；参考: [DPMZM](physics_models.md#dpmzm) |

### DPMZMComposite（复合器件）
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| Vpi | float | 3.5 | V | 半波电压，调制深度 m=πV/Vpi；公式: [DPMZM-1](physics_models.md#formula_index)；参考: [DPMZM](physics_models.md#dpmzm) |
| drive_mode | enum | push_pull |  | 驱动模式（push_pull:推挽，single_arm:单臂）；公式: [MZM-4](physics_models.md#formula_index)；options: push_pull/single_arm；参考: [DPMZM](physics_models.md#dpmzm) |
| phi_bias_i | float | 0.0 | rad | I 路偏置（rad）；公式: [DPMZM-1](physics_models.md#formula_index)；参考: [DPMZM](physics_models.md#dpmzm) |
| phi_bias_q | float | 0.0 | rad | Q 路偏置（rad）；公式: [DPMZM-1](physics_models.md#formula_index)；参考: [DPMZM](physics_models.md#dpmzm) |
| phi_q | float | 1.57079632679 | rad | I/Q 相位差（理想 π/2）；公式: [DPMZM-1](physics_models.md#formula_index)；参考: [DPMZM](physics_models.md#dpmzm) |
| bandwidth_hz | float | 0.0 | Hz | 截止频率 f_c，0 表示不限制带宽；公式: [LP-1](physics_models.md#formula_index)；参考: [DPMZM](physics_models.md#dpmzm) |
| bandwidth_kind | enum | rect |  | 低通模型（rect:矩形，rc:一阶RC）；公式: [LP-1](physics_models.md#formula_index)；options: rect/rc；参考: [DPMZM](physics_models.md#dpmzm) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [DPMZM](physics_models.md#dpmzm) |
| loss_db | float | 0.0 | dB | 插入损耗（幅度乘以 10^(-L/20)）；公式: [ATT-1](physics_models.md#formula_index)；参考: [DPMZM](physics_models.md#dpmzm) |
| iq_phase_error | float | 0.0 | rad | I/Q 相位误差（rad）；参考: [DPMZM](physics_models.md#dpmzm) |
| iq_imbalance_db | float | 0.0 | dB | I/Q 幅度失衡（dB）；参考: [DPMZM](physics_models.md#dpmzm) |
| vpi_error_pct | float | 0.0 | % | Vpi 误差百分比；参考: [DPMZM](physics_models.md#dpmzm) |
| arm_ratio_db | float | 0.0 | dB | 臂幅度不平衡（dB）；参考: [DPMZM](physics_models.md#dpmzm) |
| phase_error | float | 0.0 | rad | 相位失配（rad）；参考: [DPMZM](physics_models.md#dpmzm) |
| drive_noise_rms | float | 0.0 | V | 驱动电压噪声 RMS；参考: [DPMZM](physics_models.md#dpmzm) |
| bias_error_rad | float | 0.0 | rad | 偏置相位误差；参考: [DPMZM](physics_models.md#dpmzm) |

### ElecGain
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| gain | float | 1.0 |  | 增益 g；公式: [ELEC-3](physics_models.md#formula_index)；参考: [电信号源](physics_models.md#electrical) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [电信号源](physics_models.md#electrical) |
| gain_error_pct | float | 0.0 | % | 增益误差百分比；参考: [电信号源](physics_models.md#electrical) |
| noise_rms | float | 0.0 | V | 噪声 RMS；参考: [电信号源](physics_models.md#electrical) |

### ElecSplitter
params：无

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [电分路](physics_models.md#elec_splitter) |
| imbalance_db | float | 0.0 | dB | 分路不平衡（dB）；公式: [ELEC-4](physics_models.md#formula_index)；参考: [电分路](physics_models.md#elec_splitter) |
| noise_rms | float | 0.0 | V | 噪声 RMS；参考: [电分路](physics_models.md#elec_splitter) |

### Laser
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| power_dbm | float | 0.0 | dBm | 输出功率（dBm）；公式: [LASER-1](physics_models.md#formula_index)；参考: [激光器](physics_models.md#laser) |
| center_freq_hz | float | 1.931e+14 | Hz | 载波频率 f0；公式: [LASER-1](physics_models.md#formula_index)；参考: [激光器](physics_models.md#laser) |
| phase0 | float | 0.0 | rad | 初始相位；公式: [LASER-1](physics_models.md#formula_index)；参考: [激光器](physics_models.md#laser) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [激光器](physics_models.md#laser) |
| linewidth_hz | float | 0.0 | Hz | 线宽 Δf；公式: [LASER-2](physics_models.md#formula_index)；参考: [激光器](physics_models.md#laser) |
| rin_db_per_hz | float | -150.0 | dB/Hz | RIN 指标（dB/Hz）；公式: [LASER-3](physics_models.md#formula_index)；参考: [激光器](physics_models.md#laser) |
| power_error_db | float | 0.0 | dB | 功率误差（dB）；参考: [激光器](physics_models.md#laser) |
| freq_offset_hz | float | 0.0 | Hz | 频偏 Δf；参考: [激光器](physics_models.md#laser) |
| phase_noise_rms | float | 0.0 | rad | 额外相位抖动 RMS；参考: [激光器](physics_models.md#laser) |

### MZM
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| Vpi | float | 3.5 | V | 半波电压，调制深度 m=πV/Vpi；公式: [MZM-2](physics_models.md#formula_index)；参考: [MZM](physics_models.md#mzm) |
| phi_bias | float | 0.0 | rad | 偏置相位（工作点）；公式: [MZM-2](physics_models.md#formula_index)；参考: [MZM](physics_models.md#mzm) |
| drive_mode | enum | push_pull |  | 驱动模式（push_pull:推挽，single_arm:单臂）；公式: [MZM-4](physics_models.md#formula_index)；options: push_pull/single_arm；参考: [MZM](physics_models.md#mzm) |
| bandwidth_hz | float | 0.0 | Hz | 截止频率 f_c，0 表示不限制带宽；公式: [LP-1](physics_models.md#formula_index)；参考: [MZM](physics_models.md#mzm) |
| bandwidth_kind | enum | rect |  | 低通模型（rect:矩形，rc:一阶RC）；公式: [LP-1](physics_models.md#formula_index)；options: rect/rc；参考: [MZM](physics_models.md#mzm) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [MZM](physics_models.md#mzm) |
| loss_db | float | 0.0 | dB | 插入损耗（幅度乘以 10^(-L/20)）；公式: [ATT-1](physics_models.md#formula_index)；参考: [MZM](physics_models.md#mzm) |
| vpi_error_pct | float | 0.0 | % | Vpi 误差百分比；参考: [MZM](physics_models.md#mzm) |
| arm_ratio_db | float | 0.0 | dB | 臂幅度不平衡（dB）；参考: [MZM](physics_models.md#mzm) |
| phase_error | float | 0.0 | rad | 相位失配（rad）；参考: [MZM](physics_models.md#mzm) |
| drive_noise_rms | float | 0.0 | V | 驱动电压噪声 RMS；参考: [MZM](physics_models.md#mzm) |
| bias_error_rad | float | 0.0 | rad | 偏置相位误差；参考: [MZM](physics_models.md#mzm) |

### MZMComposite（复合器件）
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| Vpi | float | 3.5 | V | 半波电压，调制深度 m=πV/Vpi；公式: [PM-2](physics_models.md#formula_index)；参考: [MZM](physics_models.md#mzm) |
| phi_bias | float | 0.0 | rad | 偏置相位（工作点）；公式: [PM-2](physics_models.md#formula_index)；参考: [MZM](physics_models.md#mzm) |
| drive_mode | enum | push_pull |  | 驱动模式（push_pull:推挽，single_arm:单臂）；公式: [MZM-4](physics_models.md#formula_index)；options: push_pull/single_arm；参考: [MZM](physics_models.md#mzm) |
| bandwidth_hz | float | 0.0 | Hz | 截止频率 f_c，0 表示不限制带宽；公式: [LP-1](physics_models.md#formula_index)；参考: [MZM](physics_models.md#mzm) |
| bandwidth_kind | enum | rect |  | 低通模型（rect:矩形，rc:一阶RC）；公式: [LP-1](physics_models.md#formula_index)；options: rect/rc；参考: [MZM](physics_models.md#mzm) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [MZM](physics_models.md#mzm) |
| loss_db | float | 0.0 | dB | 插入损耗（幅度乘以 10^(-L/20)）；公式: [ATT-1](physics_models.md#formula_index)；参考: [MZM](physics_models.md#mzm) |
| vpi_error_pct | float | 0.0 | % | Vpi 误差百分比；参考: [MZM](physics_models.md#mzm) |
| arm_ratio_db | float | 0.0 | dB | 臂幅度不平衡（dB）；参考: [MZM](physics_models.md#mzm) |
| phase_error | float | 0.0 | rad | 相位失配（rad）；参考: [MZM](physics_models.md#mzm) |
| drive_noise_rms | float | 0.0 | V | 驱动电压噪声 RMS；参考: [MZM](physics_models.md#mzm) |
| bias_error_rad | float | 0.0 | rad | 偏置相位误差；参考: [MZM](physics_models.md#mzm) |

### OpticalFiber
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| length_m | float | 0.0 | m | 光纤长度 L；公式: [FIBER-1](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| alpha_db_per_km | float | 0.0 | dB/km | 衰减系数 α（dB/km）；公式: [FIBER-1](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| beta2_s2_per_m | float | 0.0 | s^2/m | 二阶色散 β2；公式: [FIBER-1](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| beta3_s3_per_m | float | 0.0 | s^3/m | 三阶色散 β3；公式: [FIBER-1](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| ssfm_steps | int | 1 |  | SSFM 分步数（>1 时启用分步传播）；公式: [FIBER-4](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| ssfm_auto | bool | false |  | 自动估计分步数（色散/非线性任一开启时生效）；公式: [FIBER-4](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| ssfm_max_phase_rad | float | 0.1 | rad | 自动分步时的最大相位阈值；公式: [FIBER-4](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| ssfm_length_frac | float | 0.1 |  | 按色散/非线性长度估计的分步比例；公式: [FIBER-4](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| ssfm_auto_mode | enum | fft |  | 自动分步频宽估算方式（fft/fast）；公式: [FIBER-4](physics_models.md#formula_index)；options: fft/fast；参考: [光纤](physics_models.md#fiber) |
| ssfm_min_steps | int | 1 |  | 自动分步的下限；公式: [FIBER-4](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| ssfm_max_steps | int | 128 |  | 自动分步的上限；公式: [FIBER-4](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [光纤](physics_models.md#fiber) |
| pmd_dgd_s | float | 0.0 | s | 偏振模色散 DGD；公式: [FIBER-2](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| pmd_axis_angle_rad | float | 0.0 | rad | PMD 主轴角度；公式: [FIBER-2](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| birefringence_phi_rad | float | 0.0 | rad | 双折射相位延迟；公式: [FIBER-2](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| pmd_time_vary | bool | false |  | PMD 时变开关（按块更新）；公式: [FIBER-2](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| pmd_dgd_std_s | float | 0.0 | s | DGD 漂移标准差；公式: [FIBER-2](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| pmd_axis_std_rad | float | 0.0 | rad | 主轴角漂移标准差；公式: [FIBER-2](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| pmd_biref_std_rad | float | 0.0 | rad | 双折射相位漂移标准差；公式: [FIBER-2](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| pmd_corr_s | float | 0.0 | s | 漂移相关时间（0 表示独立更新）；公式: [FIBER-2](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| pmd_update_samples | int | 0 |  | 更新时间窗长度（采样点）；公式: [FIBER-2](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |
| nonlin_gamma_w_inv_m | float | 0.0 | 1/W/m | Kerr 系数 γ；公式: [FIBER-3](physics_models.md#formula_index)；参考: [光纤](physics_models.md#fiber) |

### OpticalFilter
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| kind | enum | bandpass |  | 滤波器类型；公式: [FILTER-1](physics_models.md#formula_index)；options: lowpass/highpass/bandpass/bandstop；参考: [光学滤波器](physics_models.md#optical_filter) |
| shape | enum | gaussian |  | 滤波响应形状；公式: [FILTER-1](physics_models.md#formula_index)；options: rect/gaussian/butter；参考: [光学滤波器](physics_models.md#optical_filter) |
| phase_mode | enum | none |  | 相位响应模式；公式: [FILTER-2](physics_models.md#formula_index)；options: none/linear/quadratic/minimum；参考: [光学滤波器](physics_models.md#optical_filter) |
| bandwidth_hz | float | 0.0 | Hz | 带宽或截止频率 B，0 表示不启用滤波；公式: [FILTER-1](physics_models.md#formula_index)；参考: [光学滤波器](physics_models.md#optical_filter) |
| center_hz | float | 0.0 | Hz | 基带中心频率偏移；公式: [FILTER-1](physics_models.md#formula_index)；参考: [光学滤波器](physics_models.md#optical_filter) |
| order | int | 2 |  | 滤波阶数（Butterworth）；公式: [FILTER-1](physics_models.md#formula_index)；参考: [光学滤波器](physics_models.md#optical_filter) |
| group_delay_s | float | 0.0 | s | 群时延；公式: [FILTER-2](physics_models.md#formula_index)；参考: [光学滤波器](physics_models.md#optical_filter) |
| gdd_s2 | float | 0.0 | s^2 | 群时延色散；公式: [FILTER-2](physics_models.md#formula_index)；参考: [光学滤波器](physics_models.md#optical_filter) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [光学滤波器](physics_models.md#optical_filter) |

### PD
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| responsivity | float | 1.0 | A/W | 响应度 R（A/W）；公式: [PD-1](physics_models.md#formula_index)；参考: [PD](physics_models.md#pd) |
| bandwidth_hz | float | 0.0 | Hz | 截止频率 f_c，0 表示不限制带宽；公式: [LP-1](physics_models.md#formula_index)；参考: [PD](physics_models.md#pd) |
| bandwidth_kind | enum | rect |  | 低通模型（rect:矩形，rc:一阶RC）；公式: [LP-1](physics_models.md#formula_index)；options: rect/rc；参考: [PD](physics_models.md#pd) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [PD](physics_models.md#pd) |
| shot_noise | bool | true |  | 散粒噪声开关；公式: [PD-2](physics_models.md#formula_index)；参考: [PD](physics_models.md#pd) |
| thermal_noise | bool | true |  | 热噪声开关；公式: [PD-3](physics_models.md#formula_index)；参考: [PD](physics_models.md#pd) |
| load_resistance | float | 50.0 | Ohm | 负载电阻 R_L；公式: [PD-3](physics_models.md#formula_index)；参考: [PD](physics_models.md#pd) |
| temperature_k | float | 300.0 | K | 温度 T；公式: [PD-3](physics_models.md#formula_index)；参考: [PD](physics_models.md#pd) |
| dark_current | float | 0.0 | A | 暗电流 I_dark；参考: [PD](physics_models.md#pd) |
| responsivity_error_pct | float | 0.0 | % | 响应度误差百分比；参考: [PD](physics_models.md#pd) |
| saturation_current | float | 0.0 | A | 饱和电流上限 I_sat；参考: [PD](physics_models.md#pd) |
| noise_current_rms | float | 0.0 | A | 附加白噪声电流 RMS；参考: [PD](physics_models.md#pd) |

### PhaseShifter
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| phi | float | 0.0 | rad | 固定相移（rad）；参考: [相移器](physics_models.md#phase_shifter) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [相移器](physics_models.md#phase_shifter) |

### PM
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| Vpi | float | 3.5 | V | 半波电压，调制深度 m=πV/Vpi；公式: [PM-2](physics_models.md#formula_index)；参考: [PM](physics_models.md#pm) |
| phi_bias | float | 0.0 | rad | 偏置相位（工作点）；公式: [PM-2](physics_models.md#formula_index)；参考: [PM](physics_models.md#pm) |
| bandwidth_hz | float | 0.0 | Hz | 截止频率 f_c，0 表示不限制带宽；公式: [LP-1](physics_models.md#formula_index)；参考: [PM](physics_models.md#pm) |
| bandwidth_kind | enum | rect |  | 低通模型（rect:矩形，rc:一阶RC）；公式: [LP-1](physics_models.md#formula_index)；options: rect/rc；参考: [PM](physics_models.md#pm) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [PM](physics_models.md#pm) |
| loss_db | float | 0.0 | dB | 插入损耗（幅度乘以 10^(-L/20)）；公式: [ATT-1](physics_models.md#formula_index)；参考: [PM](physics_models.md#pm) |
| vpi_error_pct | float | 0.0 | % | Vpi 误差百分比；参考: [PM](physics_models.md#pm) |
| drive_noise_rms | float | 0.0 | V | 驱动电压噪声 RMS；参考: [PM](physics_models.md#pm) |
| bias_error_rad | float | 0.0 | rad | 偏置相位误差；参考: [PM](physics_models.md#pm) |

### PolarizationController
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| preset | enum | custom |  | 波片组合预设（QHQ/H/Q/custom）；公式: [POL-3](physics_models.md#formula_index)；options: custom/QHQ/H/Q/HWP/QWP；参考: [偏振模型](physics_models.md#polarization) |
| angle1_rad | float | 0.0 | rad | 第 1 片波片轴角；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| angle2_rad | float | 0.0 | rad | 第 2 片波片轴角；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| angle3_rad | float | 0.0 | rad | 第 3 片波片轴角；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| retardance1_rad | float | 0.0 | rad | 第 1 片相位延迟；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| retardance2_rad | float | 0.0 | rad | 第 2 片相位延迟；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| retardance3_rad | float | 0.0 | rad | 第 3 片相位延迟；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [偏振模型](physics_models.md#polarization) |
| angle_noise_std_rad | float | 0.0 | rad | 角度扰动标准差；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| retardance_noise_std_rad | float | 0.0 | rad | 相位延迟扰动标准差；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| time_vary | bool | false |  | 时变漂移开关；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| angle_drift_std_rad | float | 0.0 | rad | 角度漂移标准差；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| retardance_drift_std_rad | float | 0.0 | rad | 相位延迟漂移标准差；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| drift_corr_s | float | 0.0 | s | 漂移相关时间；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| drift_update_samples | int | 0 |  | 漂移更新时间窗；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |

### PolarizationPDL
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| pdl_db | float | 0.0 | dB | 偏振相关损耗；公式: [POL-2](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| axis_angle_rad | float | 0.0 | rad | PDL 主轴角度；公式: [POL-2](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| loss_db | float | 0.0 | dB | 插入损耗（幅度乘以 10^(-L/20)）；公式: [ATT-1](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [偏振模型](physics_models.md#polarization) |
| pdl_noise_std_db | float | 0.0 | dB | PDL 随机扰动标准差；公式: [POL-2](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| axis_noise_std_rad | float | 0.0 | rad | 主轴角随机扰动标准差；公式: [POL-2](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| time_vary | bool | false |  | 时变漂移开关；公式: [POL-2](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| pdl_drift_std_db | float | 0.0 | dB | PDL 漂移标准差；公式: [POL-2](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| axis_drift_std_rad | float | 0.0 | rad | 主轴角漂移标准差；公式: [POL-2](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| drift_corr_s | float | 0.0 | s | 漂移相关时间；公式: [POL-2](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| drift_update_samples | int | 0 |  | 漂移更新时间窗；公式: [POL-2](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |

### PolarizationRotator
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| angle_rad | float | 0.0 | rad | 偏振旋转角；公式: [POL-1](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [偏振模型](physics_models.md#polarization) |
| angle_noise_std_rad | float | 0.0 | rad | 角度随机扰动标准差；公式: [POL-1](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| time_vary | bool | false |  | 时变漂移开关；公式: [POL-1](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| angle_drift_std_rad | float | 0.0 | rad | 角度漂移标准差；公式: [POL-1](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| drift_corr_s | float | 0.0 | s | 漂移相关时间；公式: [POL-1](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| drift_update_samples | int | 0 |  | 漂移更新时间窗；公式: [POL-1](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |

### PolarizationWaveplate
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| retardance_rad | float | 0.0 | rad | 相位延迟（波片）；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| axis_angle_rad | float | 0.0 | rad | 波片主轴角；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [偏振模型](physics_models.md#polarization) |
| axis_noise_std_rad | float | 0.0 | rad | 波片主轴角随机扰动标准差；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| retardance_noise_std_rad | float | 0.0 | rad | 相位延迟随机扰动标准差；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| time_vary | bool | false |  | 时变漂移开关；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| axis_drift_std_rad | float | 0.0 | rad | 主轴角漂移标准差；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| retardance_drift_std_rad | float | 0.0 | rad | 相位延迟漂移标准差；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| drift_corr_s | float | 0.0 | s | 漂移相关时间；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |
| drift_update_samples | int | 0 |  | 漂移更新时间窗；公式: [POL-3](physics_models.md#formula_index)；参考: [偏振模型](physics_models.md#polarization) |

### RFSource
params：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| freq_hz | float | 1e+09 | Hz | 频率 f；公式: [ELEC-1](physics_models.md#formula_index)；参考: [电信号源](physics_models.md#electrical) |
| amplitude | float | 1.0 | V | 幅值 A；公式: [ELEC-1](physics_models.md#formula_index)；参考: [电信号源](physics_models.md#electrical) |
| phase | float | 0.0 | rad | 初相 φ；公式: [ELEC-1](physics_models.md#formula_index)；参考: [电信号源](physics_models.md#electrical) |
| offset | float | 0.0 | V | 直流偏置；公式: [ELEC-1](physics_models.md#formula_index)；参考: [电信号源](physics_models.md#electrical) |

nonideal：
| 参数 | 类型 | 默认 | 单位 | 说明 |
| --- | --- | --- | --- | --- |
| enable | bool | false |  | 非理想总开关；参考: [电信号源](physics_models.md#electrical) |
| freq_offset_hz | float | 0.0 | Hz | 频偏 Δf；参考: [电信号源](physics_models.md#electrical) |
| amplitude_error_pct | float | 0.0 | % | 幅度误差百分比；参考: [电信号源](physics_models.md#electrical) |
| amplitude_noise_rms | float | 0.0 | V | 幅度噪声 RMS；参考: [电信号源](physics_models.md#electrical) |
| phase_noise_rms | float | 0.0 | rad | 相位噪声 RMS；参考: [电信号源](physics_models.md#electrical) |
| offset_error | float | 0.0 | V | 直流误差；参考: [电信号源](physics_models.md#electrical) |
<!-- AUTO-GENERATED:PARAMS:END -->

## UI 交互流程（React + React Flow）
1) 创建工程
   - 选择后端（torch）、设备（cpu/cuda）与全局设置。
   - 设置采样率（auto/custom）与采样点数（可选）。
2) 搭建图
   - 从器件库拖拽到画布。
   - 用连线连接兼容端口。
3) 配置参数
   - 选中节点打开参数面板。
   - 编辑 params 和 nonideal，启用/禁用非理想开关。
4) 校验
   - 运行图校验，提示端口不匹配或必需参数缺失。
   - 可调用 `/graph/expand` 预览复合器件展开后的子图。

Graph 展开接口示例：

```json
POST /graph/expand
{
  "graph": { ... },
  "validate": true,
  "annotate": true
}
```

展开返回会包含 `expansion_map`（当 annotate=true）：

```json
{
  "expansion_map": {
    "mzm1": {
      "template": "MZMComposite",
      "children": ["mzm1__cpl_in", "mzm1__pm1", "..."],
      "port_map": {"opt_in": ["mzm1__cpl_in", "opt_in1"], "opt_out": ["mzm1__cpl_out", "opt_out1"]},
      "params": { ... },
      "nonideal": { ... }
    }
  }
}
```
5) 异步运行
   - 提交图到后端，得到 job_id。
   - WebSocket 推送状态（queued/running/done/error）。
6) 查看结果
   - 在 OSA/ESA 视图中显示频谱。
   - 可切换 ESA 为时域预览或手动指定输出端口。
7) 保存/导出
   - 保存项目 JSON。
   - 导出图像或数据（CSV/HDF5/Zarr）。
