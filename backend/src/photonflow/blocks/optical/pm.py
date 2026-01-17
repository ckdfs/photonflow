"""Phase modulator block."""

from __future__ import annotations

import math
from typing import Dict

import torch

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.filters import apply_lowpass
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext


@register_block("PM")
class PM(BaseBlock):
    """Electro-optic phase modulator. Applies phase modulation to an optical signal based on an electrical drive voltage. Key parameter: Vπ (half-wave voltage)."""

    PORTS = {"opt_in": "optical", "elec_in": "electrical", "opt_out": "optical"}
    SPEC = {
        "params": {
            "Vpi": {"type": "float", "default": 3.5, "unit": "V"},
            "phi_bias": {"type": "float", "default": 0.0, "unit": "rad"},
            "bandwidth_hz": {"type": "float", "default": 0.0, "unit": "Hz"},
            "bandwidth_kind": {
                "type": "enum",
                "default": "rect",
                "options": ["rect", "rc"],
            },
        },
        "nonideal": {
            "enable": {"type": "bool", "default": False},
            "loss_db": {"type": "float", "default": 0.0, "unit": "dB"},
            "vpi_error_pct": {"type": "float", "default": 0.0, "unit": "%"},
            "drive_noise_rms": {"type": "float", "default": 0.0, "unit": "V"},
            "bias_error_rad": {"type": "float", "default": 0.0, "unit": "rad"},
        },
    }

    def estimate_fmax(self) -> float | None:
        bw = self.params.get("bandwidth_hz")
        if bw is not None and float(bw) > 0.0:
            return float(bw)
        return None

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        opt_in = inputs["opt_in"]
        elec_in = inputs.get("elec_in")

        v = elec_in.data if elec_in is not None else torch.zeros_like(opt_in.data.real)
        v = torch.real(v)

        vpi = float(self.params.get("Vpi", 3.5))
        phi_bias = float(self.params.get("phi_bias", 0.0))
        bw_kind = self.params.get("bandwidth_kind", "rect")

        nonideal = self.nonideal if self.nonideal.get("enable", False) else {}
        vpi_error = float(nonideal.get("vpi_error", nonideal.get("vpi_error_pct", 0.0)))
        vpi = vpi * (1.0 + vpi_error / 100.0)
        bias_error = float(nonideal.get("bias_error_rad", 0.0))
        drive_noise_rms = float(nonideal.get("drive_noise_rms", 0.0))
        if drive_noise_rms > 0.0:
            v = v + drive_noise_rms * torch.randn_like(v)
        bandwidth_raw = self.params.get("bandwidth_hz")
        if bandwidth_raw is not None:
            bandwidth = float(bandwidth_raw)
            if 0.0 < bandwidth < ctx.fs / 2.0:
                v = apply_lowpass(v, ctx.fs, bandwidth, kind=bw_kind)

        phi = (phi_bias + bias_error) + math.pi * v / vpi
        phase = torch.exp(1j * phi)

        data = opt_in.data * phase
        loss_db = nonideal.get("loss_db")
        if loss_db is not None:
            data = data * (10 ** (-float(loss_db) / 20.0))

        signal = Signal(
            data=data,
            fs=opt_in.fs,
            t0=opt_in.t0,
            center_freq=opt_in.center_freq,
            pol_mode=opt_in.pol_mode,
            meta=dict(opt_in.meta),
        )
        return {"opt_out": signal}
