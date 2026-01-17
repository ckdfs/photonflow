"""RF sine source."""

from __future__ import annotations

import math
from typing import Dict

import torch

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext


@register_block("RFSource")
class RFSource(BaseBlock):
    """Radio-frequency (RF) sinusoidal signal generator. Outputs a sine wave with configurable frequency, amplitude, phase, and DC offset."""

    PORTS = {"elec_out": "electrical"}
    SPEC = {
        "params": {
            "freq_hz": {"type": "float", "default": 1e9, "unit": "Hz"},
            "amplitude": {"type": "float", "default": 1.0, "unit": "V"},
            "phase": {"type": "float", "default": 0.0, "unit": "rad"},
            "offset": {"type": "float", "default": 0.0, "unit": "V"},
        },
        "nonideal": {
            "enable": {"type": "bool", "default": False},
            "freq_offset_hz": {"type": "float", "default": 0.0, "unit": "Hz"},
            "amplitude_error_pct": {"type": "float", "default": 0.0, "unit": "%"},
            "amplitude_noise_rms": {"type": "float", "default": 0.0, "unit": "V"},
            "phase_noise_rms": {"type": "float", "default": 0.0, "unit": "rad"},
            "offset_error": {"type": "float", "default": 0.0, "unit": "V"},
        },
    }

    def estimate_fmax(self) -> float | None:
        freq = self.params.get("freq_hz")
        if freq is not None:
            return float(freq)
        return None

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        freq = float(self.params.get("freq_hz", 1e9))
        amplitude = float(self.params.get("amplitude", 1.0))
        phase = float(self.params.get("phase", 0.0))
        offset = float(self.params.get("offset", 0.0))

        nonideal = self.nonideal if self.nonideal.get("enable", False) else {}
        freq += float(nonideal.get("freq_offset_hz", 0.0))
        amplitude = amplitude * (1.0 + float(nonideal.get("amplitude_error_pct", 0.0)) / 100.0)
        offset = offset + float(nonideal.get("offset_error", 0.0))
        phase_noise_rms = float(nonideal.get("phase_noise_rms", 0.0))
        amp_noise_rms = float(nonideal.get("amplitude_noise_rms", 0.0))

        t = ctx.time()
        phi = 2.0 * math.pi * freq * t + phase
        if phase_noise_rms > 0.0:
            phi = phi + phase_noise_rms * torch.randn_like(t)
        data = amplitude * torch.sin(phi) + offset
        if amp_noise_rms > 0.0:
            data = data + amp_noise_rms * torch.randn_like(data)
        signal = Signal(data=data, fs=ctx.fs, t0=ctx.t0, pol_mode="scalar")
        return {"elec_out": signal}
