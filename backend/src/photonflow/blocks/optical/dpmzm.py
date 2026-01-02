"""Dual-parallel MZM block."""

from __future__ import annotations

import math
from typing import Dict

import torch

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.filters import apply_lowpass
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext


def _mzm_arm(opt_data: torch.Tensor, v: torch.Tensor, vpi: float, phi_bias: float, drive_mode: str,
             arm_ratio: float, phase_err: float) -> torch.Tensor:
    if drive_mode == "push_pull":
        phi1 = phi_bias + 0.5 * math.pi * v / vpi
        phi2 = -phi_bias - 0.5 * math.pi * v / vpi + phase_err
    else:
        phi1 = phi_bias + math.pi * v / vpi
        phi2 = -phi_bias + phase_err

    e1 = torch.exp(1j * phi1)
    e2 = arm_ratio * torch.exp(1j * phi2)
    return 0.5 * opt_data * (e1 + e2)


@register_block("DPMZM")
class DPMZM(BaseBlock):
    PORTS = {
        "opt_in": "optical",
        "elec_i": "electrical",
        "elec_q": "electrical",
        "opt_out": "optical",
    }
    SPEC = {
        "params": {
            "Vpi": {"type": "float", "default": 3.5, "unit": "V"},
            "drive_mode": {
                "type": "enum",
                "default": "push_pull",
                "options": ["push_pull", "single_arm"],
            },
            "phi_bias_i": {"type": "float", "default": 0.0, "unit": "rad"},
            "phi_bias_q": {"type": "float", "default": 0.0, "unit": "rad"},
            "phi_q": {"type": "float", "default": 1.57079632679, "unit": "rad"},
            "bandwidth_hz": {"type": "float", "default": 0.0, "unit": "Hz"},
            "bandwidth_kind": {
                "type": "enum",
                "default": "rect",
                "options": ["rect", "rc"],
            },
        },
        "nonideal": {
            "enable": {"type": "bool", "default": False},
            "loss_db": {"type": "float", "default": 0.0, "unit": "dB"},
            "vpi_error_pct": {"type": "float", "default": 0.0, "unit": "%"},
            "arm_ratio_db": {"type": "float", "default": 0.0, "unit": "dB"},
            "phase_error": {"type": "float", "default": 0.0, "unit": "rad"},
            "iq_phase_error": {"type": "float", "default": 0.0, "unit": "rad"},
            "iq_imbalance_db": {"type": "float", "default": 0.0, "unit": "dB"},
            "drive_noise_rms": {"type": "float", "default": 0.0, "unit": "V"},
            "bias_error_i": {"type": "float", "default": 0.0, "unit": "rad"},
            "bias_error_q": {"type": "float", "default": 0.0, "unit": "rad"},
        },
    }

    def estimate_fmax(self) -> float | None:
        bw = self.params.get("bandwidth_hz")
        if bw is not None and float(bw) > 0.0:
            return float(bw)
        return None

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        opt_in = inputs["opt_in"]
        v_i = torch.real(inputs.get("elec_i", None).data) if "elec_i" in inputs else torch.zeros_like(opt_in.data.real)
        v_q = torch.real(inputs.get("elec_q", None).data) if "elec_q" in inputs else torch.zeros_like(opt_in.data.real)

        vpi = float(self.params.get("Vpi", 3.5))
        drive_mode = self.params.get("drive_mode", "push_pull")
        phi_bias_i = float(self.params.get("phi_bias_i", 0.0))
        phi_bias_q = float(self.params.get("phi_bias_q", 0.0))
        phi_q = float(self.params.get("phi_q", math.pi / 2.0))
        bw_kind = self.params.get("bandwidth_kind", "rect")

        nonideal = self.nonideal if self.nonideal.get("enable", False) else {}
        vpi_error = float(nonideal.get("vpi_error", nonideal.get("vpi_error_pct", 0.0)))
        vpi = vpi * (1.0 + vpi_error / 100.0)
        arm_ratio_db = float(nonideal.get("arm_ratio_db", 0.0))
        arm_ratio = 10 ** (-arm_ratio_db / 20.0)
        phase_err = float(nonideal.get("phase_error", 0.0))
        iq_phase_error = float(nonideal.get("iq_phase_error", 0.0))
        iq_imbalance_db = float(nonideal.get("iq_imbalance_db", 0.0))
        drive_noise_rms = float(nonideal.get("drive_noise_rms", 0.0))
        bias_error_i = float(nonideal.get("bias_error_i", 0.0))
        bias_error_q = float(nonideal.get("bias_error_q", 0.0))
        if drive_noise_rms > 0.0:
            v_i = v_i + drive_noise_rms * torch.randn_like(v_i)
            v_q = v_q + drive_noise_rms * torch.randn_like(v_q)
        bandwidth_raw = self.params.get("bandwidth_hz")
        if bandwidth_raw is not None:
            bandwidth = float(bandwidth_raw)
            if 0.0 < bandwidth < ctx.fs / 2.0:
                v_i = apply_lowpass(v_i, ctx.fs, bandwidth, kind=bw_kind)
                v_q = apply_lowpass(v_q, ctx.fs, bandwidth, kind=bw_kind)

        e_i = _mzm_arm(opt_in.data, v_i, vpi, phi_bias_i + bias_error_i, drive_mode, arm_ratio, phase_err)
        e_q = _mzm_arm(opt_in.data, v_q, vpi, phi_bias_q + bias_error_q, drive_mode, arm_ratio, phase_err)
        e_q = e_q * torch.exp(1j * (phi_q + iq_phase_error))

        if iq_imbalance_db > 0.0:
            e_q = e_q * (10 ** (-abs(iq_imbalance_db) / 20.0))
        elif iq_imbalance_db < 0.0:
            e_i = e_i * (10 ** (-abs(iq_imbalance_db) / 20.0))

        data = (e_i + 1j * e_q) / math.sqrt(2.0)

        loss_db = nonideal.get("loss_db")
        if loss_db is not None:
            data = data * (10 ** (-float(loss_db) / 20.0))

        signal = Signal(
            data=data,
            fs=opt_in.fs,
            t0=opt_in.t0,
            center_freq=opt_in.center_freq,
            pol_mode=opt_in.pol_mode,
            meta=dict(opt_in.meta),
        )
        return {"opt_out": signal}
