"""Laser source block."""

from __future__ import annotations

import math
from typing import Dict

import torch

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext


@register_block("Laser")
class Laser(BaseBlock):
    """Continuous-wave (CW) laser source. Generates an optical carrier signal with configurable power, frequency, and phase. Supports linewidth, RIN, and other non-ideal effects."""

    PORTS = {"opt_out": "optical"}
    SPEC = {
        "params": {
            "power_dbm": {"type": "float", "default": 0.0, "unit": "dBm"},
            "center_freq_hz": {"type": "float", "default": 193.1e12, "unit": "Hz"},
            "phase0": {"type": "float", "default": 0.0, "unit": "rad"},
        },
        "nonideal": {
            "enable": {"type": "bool", "default": False},
            "linewidth_hz": {"type": "float", "default": 0.0, "unit": "Hz"},
            "rin_db_per_hz": {"type": "float", "default": -150.0, "unit": "dB/Hz"},
            "power_error_db": {"type": "float", "default": 0.0, "unit": "dB"},
            "freq_offset_hz": {"type": "float", "default": 0.0, "unit": "Hz"},
            "phase_noise_rms": {"type": "float", "default": 0.0, "unit": "rad"},
        },
    }

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        power_dbm = float(self.params.get("power_dbm", 0.0))
        center_freq = float(self.params.get("center_freq_hz", 193.1e12))
        phase0 = float(self.params.get("phase0", 0.0))

        power_w = 1e-3 * (10 ** (power_dbm / 10.0))
        amp = math.sqrt(power_w)

        t = ctx.time()
        dtype = torch.complex64
        phase = phase0 + torch.zeros_like(t)

        nonideal = self.nonideal if self.nonideal.get("enable", False) else {}
        power_error_db = float(nonideal.get("power_error_db", 0.0))
        if power_error_db != 0.0:
            amp = amp * (10 ** (power_error_db / 20.0))
        freq_offset = float(nonideal.get("freq_offset_hz", 0.0))
        if freq_offset != 0.0:
            center_freq = center_freq + freq_offset
        phase_noise_rms = float(nonideal.get("phase_noise_rms", 0.0))
        if phase_noise_rms > 0.0:
            phase = phase + phase_noise_rms * torch.randn_like(t)
        linewidth = float(nonideal.get("linewidth_hz", 0.0))
        if linewidth > 0.0:
            sigma = math.sqrt(2.0 * math.pi * linewidth / ctx.fs)
            dphi = sigma * torch.randn_like(t)
            phase = phase + torch.cumsum(dphi, dim=0)

        rin_db = nonideal.get("rin_db_per_hz")
        if rin_db is not None:
            rin_linear = 10 ** (float(rin_db) / 10.0)
            sigma_i = math.sqrt(rin_linear * ctx.fs / 2.0)
            intensity = power_w * (1.0 + sigma_i * torch.randn_like(t))
            intensity = torch.clamp(intensity, min=0.0)
            amp = torch.sqrt(intensity)

        field = amp * torch.exp(1j * phase.to(dtype=dtype))
        signal = Signal(data=field, fs=ctx.fs, t0=ctx.t0, center_freq=center_freq)
        return {"opt_out": signal}
