"""Oscilloscope probe."""

from __future__ import annotations

from typing import Dict

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext


@register_block("ScopeProbe")
class ScopeProbe(BaseBlock):
    """Oscilloscope probe. Captures time-domain waveforms of an electrical signal for visualization."""

    PORTS = {"elec_in": "electrical"}
    SPEC = {
        "params": {},
        "nonideal": {},
    }

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        _ = inputs.get("elec_in")
        return {}
