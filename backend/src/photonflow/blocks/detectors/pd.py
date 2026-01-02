"""Photodiode detector."""

from __future__ import annotations

import math
from typing import Dict

import torch

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext
from photonflow.core.filters import apply_lowpass


@register_block("PD")
class PD(BaseBlock):
    PORTS = {"opt_in": "optical", "elec_out": "electrical"}
    SPEC = {
        "params": {
            "responsivity": {"type": "float", "default": 1.0, "unit": "A/W"},
            "bandwidth_hz": {"type": "float", "default": 0.0, "unit": "Hz"},
            "bandwidth_kind": {
                "type": "enum",
                "default": "rect",
                "options": ["rect", "rc"],
            },
        },
        "nonideal": {
            "enable": {"type": "bool", "default": False},
            "shot_noise": {"type": "bool", "default": True},
            "thermal_noise": {"type": "bool", "default": True},
            "load_resistance": {"type": "float", "default": 50.0, "unit": "Ohm"},
            "temperature_k": {"type": "float", "default": 300.0, "unit": "K"},
            "dark_current": {"type": "float", "default": 0.0, "unit": "A"},
            "responsivity_error_pct": {"type": "float", "default": 0.0, "unit": "%"},
            "saturation_current": {"type": "float", "default": 0.0, "unit": "A"},
            "noise_current_rms": {"type": "float", "default": 0.0, "unit": "A"},
        },
    }

    def estimate_fmax(self) -> float | None:
        bw = self.params.get("bandwidth_hz")
        if bw is not None and float(bw) > 0.0:
            return float(bw)
        return None

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        opt_in = inputs["opt_in"]
        responsivity = float(self.params.get("responsivity", 1.0))

        if opt_in.pol_mode == "jones" and opt_in.data.ndim == 2:
            power = torch.sum(torch.abs(opt_in.data) ** 2, dim=0)
        else:
            power = torch.abs(opt_in.data) ** 2

        nonideal = self.nonideal if self.nonideal.get("enable", False) else {}
        resp_error = float(nonideal.get("responsivity_error_pct", 0.0))
        responsivity = responsivity * (1.0 + resp_error / 100.0)
        current = responsivity * power
        dark_current = float(nonideal.get("dark_current", 0.0))
        if dark_current != 0.0:
            current = current + dark_current
        bandwidth_raw = self.params.get("bandwidth_hz")
        bandwidth_val = float(bandwidth_raw) if bandwidth_raw is not None else 0.0
        bandwidth = ctx.fs / 2.0 if bandwidth_val <= 0.0 else bandwidth_val
        bw_kind = self.params.get("bandwidth_kind", "rect")
        if bandwidth > 0 and bandwidth < ctx.fs / 2.0:
            current = apply_lowpass(current, ctx.fs, bandwidth, kind=bw_kind)

        saturation = float(nonideal.get("saturation_current", 0.0))
        if saturation > 0.0:
            current = torch.clamp(current, max=saturation)

        if nonideal.get("shot_noise", True) or nonideal.get("thermal_noise", True):
            noise = _pd_noise(current, bandwidth, nonideal)
            current = current + noise
        extra_noise = float(nonideal.get("noise_current_rms", 0.0))
        if extra_noise > 0.0:
            current = current + extra_noise * torch.randn_like(current)

        signal = Signal(data=current, fs=opt_in.fs, t0=opt_in.t0, pol_mode="scalar")
        return {"elec_out": signal}


def _pd_noise(current: torch.Tensor, bandwidth: float, nonideal: dict) -> torch.Tensor:
    q = 1.602176634e-19
    k_b = 1.380649e-23
    r_load = float(nonideal.get("load_resistance", 50.0))
    temp_k = float(nonideal.get("temperature_k", 300.0))

    mean_i = torch.mean(current).item()
    sigma_shot = math.sqrt(2.0 * q * mean_i * bandwidth)
    sigma_therm = math.sqrt(4.0 * k_b * temp_k * bandwidth / r_load)
    sigma_sq = 0.0
    if nonideal.get("shot_noise", True):
        sigma_sq += sigma_shot ** 2
    if nonideal.get("thermal_noise", True):
        sigma_sq += sigma_therm ** 2

    if sigma_sq == 0.0:
        return torch.zeros_like(current)
    return math.sqrt(sigma_sq) * torch.randn_like(current)
