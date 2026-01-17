"""Electrical spectrum analyzer probe."""

from __future__ import annotations

from typing import Dict

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext


@register_block("ESAProbe")
class ESAProbe(BaseBlock):
    """Electrical Spectrum Analyzer (ESA) probe. Measures the power spectrum of an electrical signal, displaying power vs. frequency."""

    PORTS = {"elec_in": "electrical"}
    SPEC = {
        "params": {
            "window": {
                "type": "enum",
                "default": "hann",
                "options": ["hann", "hamming", "blackman", "rect", "kaiser"],
            },
            "ref": {"type": "float", "default": 1.0, "unit": ""},
            "include_power": {"type": "bool", "default": False},
        },
        "nonideal": {},
    }

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        _ = inputs.get("elec_in")
        return {}
