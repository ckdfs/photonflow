"""DC bias source."""

from __future__ import annotations

from typing import Dict

import torch

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext


@register_block("DCSource")
class DCSource(BaseBlock):
    """DC voltage source. Outputs a constant voltage level with optional noise and offset error modeling."""

    PORTS = {"elec_out": "electrical"}
    SPEC = {
        "params": {"voltage": {"type": "float", "default": 0.0, "unit": "V"}},
        "nonideal": {
            "enable": {"type": "bool", "default": False},
            "offset_error": {"type": "float", "default": 0.0, "unit": "V"},
            "noise_rms": {"type": "float", "default": 0.0, "unit": "V"},
        },
    }

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        voltage = float(self.params.get("voltage", 0.0))
        nonideal = self.nonideal if self.nonideal.get("enable", False) else {}
        voltage = voltage + float(nonideal.get("offset_error", 0.0))
        data = torch.full((ctx.n_samples,), voltage, device=ctx.device)
        noise_rms = float(nonideal.get("noise_rms", 0.0))
        if noise_rms > 0.0:
            data = data + noise_rms * torch.randn_like(data)
        signal = Signal(data=data, fs=ctx.fs, t0=ctx.t0, pol_mode="scalar")
        return {"elec_out": signal}
