"""Optical attenuator."""

from __future__ import annotations

from typing import Dict

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext


@register_block("Attenuator")
class Attenuator(BaseBlock):
    PORTS = {"opt_in": "optical", "opt_out": "optical"}
    SPEC = {
        "params": {"loss_db": {"type": "float", "default": 0.0, "unit": "dB"}},
        "nonideal": {"enable": {"type": "bool", "default": False}},
    }

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        opt_in = inputs["opt_in"]
        loss_db = float(self.params.get("loss_db", 0.0))
        data = opt_in.data * (10 ** (-loss_db / 20.0))

        signal = Signal(
            data=data,
            fs=opt_in.fs,
            t0=opt_in.t0,
            center_freq=opt_in.center_freq,
            pol_mode=opt_in.pol_mode,
            meta=dict(opt_in.meta),
        )
        return {"opt_out": signal}
