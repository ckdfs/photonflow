"""Electrical gain block."""

from __future__ import annotations

from typing import Dict

import torch

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext


@register_block("ElecGain")
class ElecGain(BaseBlock):
    """Electrical amplifier/attenuator. Scales an electrical signal by a configurable gain factor with optional noise."""

    PORTS = {"elec_in": "electrical", "elec_out": "electrical"}
    SPEC = {
        "params": {"gain": {"type": "float", "default": 1.0, "unit": ""}},
        "nonideal": {
            "enable": {"type": "bool", "default": False},
            "gain_error_pct": {"type": "float", "default": 0.0, "unit": "%"},
            "noise_rms": {"type": "float", "default": 0.0, "unit": "V"},
        },
    }

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        elec_in = inputs["elec_in"]
        gain = float(self.params.get("gain", 1.0))
        nonideal = self.nonideal if self.nonideal.get("enable", False) else {}
        gain_error = float(nonideal.get("gain_error_pct", 0.0))
        gain = gain * (1.0 + gain_error / 100.0)
        data = elec_in.data * gain
        noise_rms = float(nonideal.get("noise_rms", 0.0))
        if noise_rms > 0.0:
            data = data + noise_rms * torch.randn_like(data)
        signal = Signal(data=data, fs=elec_in.fs, t0=elec_in.t0, pol_mode="scalar")
        return {"elec_out": signal}
