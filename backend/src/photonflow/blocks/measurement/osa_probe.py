"""Optical spectrum analyzer probe."""

from __future__ import annotations

from typing import Dict

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext


@register_block("OSAProbe")
class OSAProbe(BaseBlock):
    """Optical Spectrum Analyzer (OSA) probe. Measures the optical power spectrum of a signal, displaying power vs. wavelength/frequency."""

    PORTS = {"opt_in": "optical"}
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
        _ = inputs.get("opt_in")
        return {}
