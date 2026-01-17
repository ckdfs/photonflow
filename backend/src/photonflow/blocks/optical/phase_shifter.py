"""Fixed phase shifter."""

from __future__ import annotations

from typing import Dict

import torch

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext


@register_block("PhaseShifter")
class PhaseShifter(BaseBlock):
    """Fixed optical phase shifter. Applies a constant phase offset to the optical signal."""

    PORTS = {"opt_in": "optical", "opt_out": "optical"}
    SPEC = {
        "params": {"phi": {"type": "float", "default": 0.0, "unit": "rad"}},
        "nonideal": {"enable": {"type": "bool", "default": False}},
    }

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        opt_in = inputs["opt_in"]
        phi = float(self.params.get("phi", 0.0))
        dtype = torch.float32 if opt_in.data.dtype == torch.complex64 else torch.float64
        phi_t = torch.tensor(phi, device=opt_in.data.device, dtype=dtype)
        phase = torch.exp(1j * phi_t)
        data = opt_in.data * phase

        signal = Signal(
            data=data,
            fs=opt_in.fs,
            t0=opt_in.t0,
            center_freq=opt_in.center_freq,
            pol_mode=opt_in.pol_mode,
            meta=dict(opt_in.meta),
        )
        return {"opt_out": signal}
