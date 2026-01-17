"""2x2 optical coupler."""

from __future__ import annotations

import math
from typing import Dict

import torch

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext


@register_block("Coupler")
class Coupler(BaseBlock):
    """2×2 optical coupler/splitter. Combines or splits optical signals with configurable coupling ratio and phase."""

    PORTS = {
        "opt_in1": "optical",
        "opt_in2": "optical",
        "opt_out1": "optical",
        "opt_out2": "optical",
    }
    SPEC = {
        "params": {
            "split_ratio": {"type": "float", "default": 0.5, "unit": ""},
        },
        "nonideal": {
            "enable": {"type": "bool", "default": False},
            "split_ratio_error": {"type": "float", "default": 0.0, "unit": ""},
            "phase_error": {"type": "float", "default": 0.0, "unit": "rad"},
            "loss_db": {"type": "float", "default": 0.0, "unit": "dB"},
        },
    }

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        in1 = inputs["opt_in1"]
        in2 = inputs.get("opt_in2")
        if in2 is None:
            in2 = Signal(
                data=torch.zeros_like(in1.data),
                fs=in1.fs,
                t0=in1.t0,
                center_freq=in1.center_freq,
                pol_mode=in1.pol_mode,
            )

        k = float(self.params.get("split_ratio", 0.5))
        k = min(max(k, 0.0), 1.0)
        nonideal = self.nonideal if self.nonideal.get("enable", False) else {}
        delta_k = float(nonideal.get("split_ratio_error", 0.0))
        k = min(max(k + delta_k, 0.0), 1.0)
        phi_err = float(nonideal.get("phase_error", 0.0))

        a = math.sqrt(k)
        b = 1j * math.sqrt(1.0 - k) * complex(math.cos(phi_err), math.sin(phi_err))
        c = 1j * math.sqrt(1.0 - k)
        d = math.sqrt(k)

        out1 = a * in1.data + b * in2.data
        out2 = c * in1.data + d * in2.data

        loss_db = nonideal.get("loss_db")
        if loss_db is not None:
            loss = 10 ** (-float(loss_db) / 20.0)
            out1 = out1 * loss
            out2 = out2 * loss

        sig1 = Signal(
            data=out1,
            fs=in1.fs,
            t0=in1.t0,
            center_freq=in1.center_freq,
            pol_mode=in1.pol_mode,
            meta=dict(in1.meta),
        )
        sig2 = Signal(
            data=out2,
            fs=in1.fs,
            t0=in1.t0,
            center_freq=in1.center_freq,
            pol_mode=in1.pol_mode,
            meta=dict(in1.meta),
        )
        return {"opt_out1": sig1, "opt_out2": sig2}
