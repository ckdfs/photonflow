"""Generate parameter dictionary tables from block specs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from photonflow.blocks import registry
from photonflow.core.composites import composites


START_MARKER = "<!-- AUTO-GENERATED:PARAMS:START -->"
END_MARKER = "<!-- AUTO-GENERATED:PARAMS:END -->"

NOTE_OVERRIDES = {
    "enable": "非理想总开关",
    "bandwidth_hz": "截止频率 f_c，0 表示不限制带宽",
    "bandwidth_kind": "低通模型（rect:矩形，rc:一阶RC）",
    "Vpi": "半波电压，调制深度 m=πV/Vpi",
    "phi_bias": "偏置相位（工作点）",
    "drive_mode": "驱动模式（push_pull:推挽，single_arm:单臂）",
    "loss_db": "插入损耗（幅度乘以 10^(-L/20)）",
    "vpi_error_pct": "Vpi 误差百分比",
    "arm_ratio_db": "臂幅度不平衡（dB）",
    "phase_error": "相位失配（rad）",
    "drive_noise_rms": "驱动电压噪声 RMS",
    "bias_error_rad": "偏置相位误差",
    "split_ratio": "功率分配比 k",
    "split_ratio_error": "分光比误差 Δk",
    "phi": "固定相移（rad）",
    "length_m": "光纤长度 L",
    "alpha_db_per_km": "衰减系数 α（dB/km）",
    "beta2_s2_per_m": "二阶色散 β2",
    "beta3_s3_per_m": "三阶色散 β3",
    "pmd_dgd_s": "偏振模色散 DGD",
    "pmd_axis_angle_rad": "PMD 主轴角度",
    "birefringence_phi_rad": "双折射相位延迟",
    "pmd_time_vary": "PMD 时变开关",
    "pmd_dgd_std_s": "PMD DGD 标准差",
    "pmd_axis_std_rad": "PMD 主轴角标准差",
    "pmd_biref_std_rad": "双折射相位标准差",
    "pmd_corr_s": "PMD 漂移相关时间",
    "pmd_update_samples": "PMD 更新采样步长",
    "nonlin_gamma_w_inv_m": "Kerr 系数 γ",
    "ssfm_auto": "自动估计分步数",
    "ssfm_max_phase_rad": "单步最大相位限制",
    "ssfm_length_frac": "长度尺度分步比例",
    "ssfm_auto_mode": "自动分步估算方式",
    "ssfm_min_steps": "最小分步数",
    "ssfm_max_steps": "最大分步数",
    "kind": "滤波器类型",
    "shape": "滤波响应形状",
    "center_hz": "滤波中心频率",
    "order": "滤波阶数（Butterworth）",
    "phase_mode": "相位响应模式",
    "group_delay_s": "群时延",
    "gdd_s2": "群时延色散",
    "angle_rad": "偏振旋转角",
    "pdl_db": "偏振相关损耗",
    "axis_angle_rad": "主轴角度",
    "angle_noise_std_rad": "角度随机扰动标准差",
    "time_vary": "时变漂移开关",
    "angle_drift_std_rad": "角度漂移标准差",
    "drift_corr_s": "漂移相关时间",
    "drift_update_samples": "漂移更新时间窗",
    "pdl_noise_std_db": "PDL 随机扰动标准差",
    "axis_noise_std_rad": "主轴角随机扰动标准差",
    "pdl_drift_std_db": "PDL 漂移标准差",
    "axis_drift_std_rad": "主轴角漂移标准差",
    "retardance_noise_std_rad": "相位延迟随机扰动标准差",
    "retardance_drift_std_rad": "相位延迟漂移标准差",
    "retardance_rad": "相位延迟（波片）",
    "preset": "波片组合模式",
    "angle1_rad": "第 1 片波片轴角",
    "angle2_rad": "第 2 片波片轴角",
    "angle3_rad": "第 3 片波片轴角",
    "retardance1_rad": "第 1 片相位延迟",
    "retardance2_rad": "第 2 片相位延迟",
    "retardance3_rad": "第 3 片相位延迟",
    "angle_noise_std_rad": "角度随机扰动（标准差）",
    "retardance_noise_std_rad": "相位延迟随机扰动（标准差）",
    "responsivity": "响应度 R（A/W）",
    "shot_noise": "散粒噪声开关",
    "thermal_noise": "热噪声开关",
    "load_resistance": "负载电阻 R_L",
    "temperature_k": "温度 T",
    "dark_current": "暗电流 I_dark",
    "responsivity_error_pct": "响应度误差百分比",
    "saturation_current": "饱和电流上限 I_sat",
    "noise_current_rms": "附加白噪声电流 RMS",
    "freq_hz": "频率 f",
    "amplitude": "幅值 A",
    "phase": "初相 φ",
    "offset": "直流偏置",
    "freq_offset_hz": "频偏 Δf",
    "amplitude_error_pct": "幅度误差百分比",
    "amplitude_noise_rms": "幅度噪声 RMS",
    "phase_noise_rms": "相位噪声 RMS",
    "offset_error": "直流误差",
    "voltage": "直流电压 V_dc",
    "noise_rms": "噪声 RMS",
    "gain": "增益 g",
    "gain_error_pct": "增益误差百分比",
    "imbalance_db": "分路不平衡（dB）",
    "power_dbm": "输出功率（dBm）",
    "center_freq_hz": "载波频率 f0",
    "phase0": "初始相位",
    "linewidth_hz": "线宽 Δf",
    "rin_db_per_hz": "RIN 指标（dB/Hz）",
    "power_error_db": "功率误差（dB）",
    "phi_bias_i": "I 路偏置（rad）",
    "phi_bias_q": "Q 路偏置（rad）",
    "phi_q": "I/Q 相位差（理想 π/2）",
    "iq_phase_error": "I/Q 相位误差（rad）",
    "iq_imbalance_db": "I/Q 幅度失衡（dB）",
    "bias_error_i": "I 路偏置误差",
    "bias_error_q": "Q 路偏置误差",
}

NOTE_BY_BLOCK = {
    "Laser": {
        "phase_noise_rms": "额外相位抖动 RMS",
    },
    "PolarizationRotator": {
        "angle_noise_std_rad": "角度随机扰动标准差",
        "time_vary": "时变漂移开关",
        "angle_drift_std_rad": "角度漂移标准差",
        "drift_corr_s": "漂移相关时间",
        "drift_update_samples": "漂移更新时间窗",
    },
    "PolarizationPDL": {
        "axis_angle_rad": "PDL 主轴角度",
        "pdl_noise_std_db": "PDL 随机扰动标准差",
        "axis_noise_std_rad": "主轴角随机扰动标准差",
        "time_vary": "时变漂移开关",
        "pdl_drift_std_db": "PDL 漂移标准差",
        "axis_drift_std_rad": "主轴角漂移标准差",
        "drift_corr_s": "漂移相关时间",
        "drift_update_samples": "漂移更新时间窗",
    },
    "PolarizationWaveplate": {
        "axis_angle_rad": "波片主轴角",
        "axis_noise_std_rad": "波片主轴角随机扰动标准差",
        "retardance_noise_std_rad": "相位延迟随机扰动标准差",
        "time_vary": "时变漂移开关",
        "axis_drift_std_rad": "主轴角漂移标准差",
        "retardance_drift_std_rad": "相位延迟漂移标准差",
        "drift_corr_s": "漂移相关时间",
        "drift_update_samples": "漂移更新时间窗",
    },
    "OpticalFilter": {
        "bandwidth_hz": "带宽或截止频率 B，0 表示不启用滤波",
        "center_hz": "基带中心频率偏移",
    },
    "OpticalFiber": {
        "ssfm_steps": "SSFM 分步数（>1 时启用分步传播）",
        "ssfm_auto": "自动估计分步数（色散/非线性任一开启时生效）",
        "ssfm_max_phase_rad": "自动分步时的最大相位阈值",
        "ssfm_length_frac": "按色散/非线性长度估计的分步比例",
        "ssfm_auto_mode": "自动分步频宽估算方式（fft/fast）",
        "ssfm_min_steps": "自动分步的下限",
        "ssfm_max_steps": "自动分步的上限",
        "pmd_time_vary": "PMD 时变开关（按块更新）",
        "pmd_dgd_std_s": "DGD 漂移标准差",
        "pmd_axis_std_rad": "主轴角漂移标准差",
        "pmd_biref_std_rad": "双折射相位漂移标准差",
        "pmd_corr_s": "漂移相关时间（0 表示独立更新）",
        "pmd_update_samples": "更新时间窗长度（采样点）",
    },
    "PolarizationController": {
        "preset": "波片组合预设（QHQ/H/Q/custom）",
        "angle_noise_std_rad": "角度扰动标准差",
        "retardance_noise_std_rad": "相位延迟扰动标准差",
    },
}

BLOCK_REF = {
    "Laser": ("激光器", "laser"),
    "PM": ("PM", "pm"),
    "MZM": ("MZM", "mzm"),
    "DPMZM": ("DPMZM", "dpmzm"),
    "MZMComposite": ("MZM", "mzm"),
    "DPMZMComposite": ("DPMZM", "dpmzm"),
    "Coupler": ("耦合器", "coupler"),
    "PhaseShifter": ("相移器", "phase_shifter"),
    "Attenuator": ("光衰减器", "attenuator"),
    "OpticalFiber": ("光纤", "fiber"),
    "OpticalFilter": ("光学滤波器", "optical_filter"),
    "PolarizationRotator": ("偏振模型", "polarization"),
    "PolarizationPDL": ("偏振模型", "polarization"),
    "PolarizationWaveplate": ("偏振模型", "polarization"),
    "PolarizationController": ("偏振模型", "polarization"),
    "PD": ("PD", "pd"),
    "RFSource": ("电信号源", "electrical"),
    "DCSource": ("电信号源", "electrical"),
    "ElecGain": ("电信号源", "electrical"),
    "ElecSplitter": ("电分路", "elec_splitter"),
}

FORMULA_OVERRIDES = {
    "power_dbm": "LASER-1",
    "center_freq_hz": "LASER-1",
    "phase0": "LASER-1",
    "linewidth_hz": "LASER-2",
    "rin_db_per_hz": "LASER-3",
    "Vpi": "PM-2",
    "phi_bias": "PM-2",
    "phi_bias_i": "DPMZM-1",
    "phi_bias_q": "DPMZM-1",
    "phi_q": "DPMZM-1",
    "drive_mode": "MZM-4",
    "bandwidth_hz": "LP-1",
    "bandwidth_kind": "LP-1",
    "loss_db": "ATT-1",
    "length_m": "FIBER-1",
    "alpha_db_per_km": "FIBER-1",
    "beta2_s2_per_m": "FIBER-1",
    "beta3_s3_per_m": "FIBER-1",
    "pmd_dgd_s": "FIBER-2",
    "pmd_axis_angle_rad": "FIBER-2",
    "birefringence_phi_rad": "FIBER-2",
    "pmd_time_vary": "FIBER-2",
    "pmd_dgd_std_s": "FIBER-2",
    "pmd_axis_std_rad": "FIBER-2",
    "pmd_biref_std_rad": "FIBER-2",
    "pmd_corr_s": "FIBER-2",
    "pmd_update_samples": "FIBER-2",
    "nonlin_gamma_w_inv_m": "FIBER-3",
    "ssfm_steps": "FIBER-4",
    "ssfm_auto": "FIBER-4",
    "ssfm_max_phase_rad": "FIBER-4",
    "ssfm_length_frac": "FIBER-4",
    "ssfm_auto_mode": "FIBER-4",
    "ssfm_min_steps": "FIBER-4",
    "ssfm_max_steps": "FIBER-4",
    "kind": "FILTER-1",
    "shape": "FILTER-1",
    "center_hz": "FILTER-1",
    "order": "FILTER-1",
    "phase_mode": "FILTER-2",
    "group_delay_s": "FILTER-2",
    "gdd_s2": "FILTER-2",
    "angle_rad": "POL-1",
    "pdl_db": "POL-2",
    "axis_angle_rad": "POL-2",
    "retardance_rad": "POL-3",
    "angle_noise_std_rad": "POL-1",
    "time_vary": "POL-1",
    "angle_drift_std_rad": "POL-1",
    "drift_corr_s": "POL-1",
    "drift_update_samples": "POL-1",
    "pdl_noise_std_db": "POL-2",
    "axis_noise_std_rad": "POL-2",
    "pdl_drift_std_db": "POL-2",
    "axis_drift_std_rad": "POL-2",
    "retardance_noise_std_rad": "POL-3",
    "retardance_drift_std_rad": "POL-3",
    "preset": "POL-3",
    "angle1_rad": "POL-3",
    "angle2_rad": "POL-3",
    "angle3_rad": "POL-3",
    "retardance1_rad": "POL-3",
    "retardance2_rad": "POL-3",
    "retardance3_rad": "POL-3",
    "angle_noise_std_rad": "POL-3",
    "retardance_noise_std_rad": "POL-3",
    "split_ratio": "CPL-1",
    "split_ratio_error": "CPL-1",
    "responsivity": "PD-1",
    "shot_noise": "PD-2",
    "thermal_noise": "PD-3",
    "load_resistance": "PD-3",
    "temperature_k": "PD-3",
    "freq_hz": "ELEC-1",
    "amplitude": "ELEC-1",
    "phase": "ELEC-1",
    "offset": "ELEC-1",
    "voltage": "ELEC-2",
    "gain": "ELEC-3",
    "imbalance_db": "ELEC-4",
}

FORMULA_BY_BLOCK = {
    "MZM": {
        "Vpi": "MZM-2",
        "phi_bias": "MZM-2",
        "drive_mode": "MZM-4",
    },
    "DPMZM": {
        "Vpi": "DPMZM-1",
        "phi_bias_i": "DPMZM-1",
        "phi_bias_q": "DPMZM-1",
        "phi_q": "DPMZM-1",
    },
    "DPMZMComposite": {
        "Vpi": "DPMZM-1",
        "phi_bias_i": "DPMZM-1",
        "phi_bias_q": "DPMZM-1",
        "phi_q": "DPMZM-1",
    },
    "OpticalFilter": {
        "bandwidth_hz": "FILTER-1",
        "phase_mode": "FILTER-2",
        "group_delay_s": "FILTER-2",
        "gdd_s2": "FILTER-2",
    },
    "PolarizationRotator": {
        "angle_noise_std_rad": "POL-1",
        "time_vary": "POL-1",
        "angle_drift_std_rad": "POL-1",
        "drift_corr_s": "POL-1",
        "drift_update_samples": "POL-1",
    },
    "PolarizationPDL": {
        "pdl_noise_std_db": "POL-2",
        "axis_noise_std_rad": "POL-2",
        "time_vary": "POL-2",
        "pdl_drift_std_db": "POL-2",
        "axis_drift_std_rad": "POL-2",
        "drift_corr_s": "POL-2",
        "drift_update_samples": "POL-2",
    },
    "PolarizationWaveplate": {
        "axis_angle_rad": "POL-3",
        "axis_noise_std_rad": "POL-3",
        "retardance_noise_std_rad": "POL-3",
        "time_vary": "POL-3",
        "axis_drift_std_rad": "POL-3",
        "retardance_drift_std_rad": "POL-3",
        "drift_corr_s": "POL-3",
        "drift_update_samples": "POL-3",
    },
    "PolarizationController": {
        "angle_noise_std_rad": "POL-3",
        "retardance_noise_std_rad": "POL-3",
        "time_vary": "POL-3",
        "angle_drift_std_rad": "POL-3",
        "retardance_drift_std_rad": "POL-3",
        "drift_corr_s": "POL-3",
        "drift_update_samples": "POL-3",
    },
}


def _format_default(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value == 0.0:
            return "0.0"
        abs_val = abs(value)
        if abs_val >= 1e6 or abs_val < 1e-3:
            return f"{value:.6g}"
        return f"{value}"
    if value is None:
        return ""
    return str(value)


def _render_table(entries: Dict[str, Dict[str, Any]], block_name: str) -> List[str]:
    lines: List[str] = []
    lines.append("| 参数 | 类型 | 默认 | 单位 | 说明 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for key, entry in entries.items():
        entry_type = str(entry.get("type", ""))
        default = _format_default(entry.get("default"))
        unit = str(entry.get("unit", ""))
        note_parts: List[str] = []
        override = NOTE_BY_BLOCK.get(block_name, {}).get(key) or NOTE_OVERRIDES.get(key)
        if override:
            note_parts.append(override)
        formula = FORMULA_BY_BLOCK.get(block_name, {}).get(key) or FORMULA_OVERRIDES.get(key)
        if formula:
            note_parts.append(f"公式: [{formula}](physics_models.md#formula_index)")
        options = entry.get("options")
        if isinstance(options, list) and options:
            note_parts.append("options: " + "/".join(str(opt) for opt in options))
        ref = BLOCK_REF.get(block_name)
        if ref:
            note_parts.append(f"参考: [{ref[0]}](physics_models.md#{ref[1]})")
        note = "；".join(note_parts)
        lines.append(f"| {key} | {entry_type} | {default} | {unit} | {note} |")
    return lines


def _render_block(name: str, spec: Dict[str, Any], composite: bool) -> List[str]:
    title = f"### {name}"
    if composite:
        title += "（复合器件）"
    lines: List[str] = [title]

    params = spec.get("params", {})
    if params:
        lines.append("params：")
        lines.extend(_render_table(params, name))
    else:
        lines.append("params：无")

    nonideal = spec.get("nonideal", {})
    if nonideal:
        lines.append("")
        lines.append("nonideal：")
        lines.extend(_render_table(nonideal, name))
    else:
        lines.append("")
        lines.append("nonideal：无")

    return lines


def _render_all(specs: Iterable[Tuple[str, Dict[str, Any]]]) -> str:
    lines: List[str] = []
    for name, info in specs:
        lines.extend(_render_block(name, info.get("spec", {}), bool(info.get("composite", False))))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _load_specs() -> List[Tuple[str, Dict[str, Any]]]:
    specs: Dict[str, Dict[str, Any]] = {}
    specs.update(registry.specs())
    specs.update(composites.specs())
    return sorted(specs.items(), key=lambda item: item[0].lower())


def _replace_section(text: str, new_block: str) -> str:
    start = text.find(START_MARKER)
    end = text.find(END_MARKER)
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError("Markers not found in docs.")
    before = text[: start + len(START_MARKER)]
    after = text[end:]
    return f"{before}\n{new_block}{after}"


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    docs_path = root / "docs" / "params_graph_ui.md"
    text = docs_path.read_text(encoding="utf-8")
    tables = _render_all(_load_specs())
    updated = _replace_section(text, tables)
    docs_path.write_text(updated, encoding="utf-8")
    print(f"Updated {docs_path}")


if __name__ == "__main__":
    main()
