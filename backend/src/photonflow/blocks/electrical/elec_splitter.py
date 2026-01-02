"""Electrical splitter block."""

from __future__ import annotations

from typing import Dict

import torch

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext


@register_block("ElecSplitter")
class ElecSplitter(BaseBlock):
    PORTS = {"elec_in": "electrical", "elec_out1": "electrical", "elec_out2": "electrical"}
    SPEC = {
        "params": {},
        "nonideal": {
            "enable": {"type": "bool", "default": False},
            "imbalance_db": {"type": "float", "default": 0.0, "unit": "dB"},
            "noise_rms": {"type": "float", "default": 0.0, "unit": "V"},
        },
    }

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        elec_in = inputs["elec_in"]
        nonideal = self.nonideal if self.nonideal.get("enable", False) else {}
        imbalance_db = float(nonideal.get("imbalance_db", 0.0))
        ratio = 10 ** (imbalance_db / 20.0)
        noise_rms = float(nonideal.get("noise_rms", 0.0))

        sig1 = elec_in.clone()
        sig2 = elec_in.clone()
        sig2.data = sig2.data * ratio
        if noise_rms > 0.0:
            sig1.data = sig1.data + noise_rms * torch.randn_like(sig1.data)
            sig2.data = sig2.data + noise_rms * torch.randn_like(sig2.data)
        return {"elec_out1": sig1, "elec_out2": sig2}
