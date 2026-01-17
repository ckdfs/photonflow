"""Optical filter (frequency-domain shaping)."""

from __future__ import annotations

import math
from typing import Dict

import torch

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext


def _gaussian_response(freq: torch.Tensor, bandwidth_hz: float) -> torch.Tensor:
    if bandwidth_hz <= 0.0:
        return torch.ones_like(freq)
    sigma = bandwidth_hz / (2.0 * math.sqrt(2.0 * math.log(2.0)))
    return torch.exp(-0.5 * (freq / sigma) ** 2)


def _butter_response(freq: torch.Tensor, bandwidth_hz: float, order: int) -> torch.Tensor:
    if bandwidth_hz <= 0.0:
        return torch.ones_like(freq)
    n = max(1, int(order))
    ratio = freq / bandwidth_hz
    return 1.0 / torch.sqrt(1.0 + ratio ** (2 * n))


def _phase_from_magnitude(magnitude: torch.Tensor, eps: float = 1e-12) -> torch.Tensor:
    log_mag = torch.log(torch.clamp(magnitude, min=eps))
    n = log_mag.numel()
    freqs = torch.fft.fftfreq(n, device=log_mag.device)
    hilbert = torch.zeros_like(log_mag, dtype=torch.complex64 if log_mag.dtype == torch.float32 else torch.complex128)
    hilbert[freqs > 0] = -1j
    hilbert[freqs < 0] = 1j
    analytic = torch.fft.ifft(torch.fft.fft(log_mag) * hilbert)
    return torch.real(analytic)


@register_block("OpticalFilter")
class OpticalFilter(BaseBlock):
    """Optical frequency-domain filter. Supports lowpass, highpass, bandpass, and bandstop configurations with various filter shapes (Gaussian, Butterworth)."""

    PORTS = {"opt_in": "optical", "opt_out": "optical"}
    SPEC = {
        "params": {
            "kind": {
                "type": "enum",
                "default": "bandpass",
                "options": ["lowpass", "highpass", "bandpass", "bandstop"],
            },
            "shape": {
                "type": "enum",
                "default": "gaussian",
                "options": ["rect", "gaussian", "butter"],
            },
            "phase_mode": {
                "type": "enum",
                "default": "none",
                "options": ["none", "linear", "quadratic", "minimum"],
            },
            "bandwidth_hz": {"type": "float", "default": 0.0, "unit": "Hz"},
            "center_hz": {"type": "float", "default": 0.0, "unit": "Hz"},
            "order": {"type": "int", "default": 2},
            "group_delay_s": {"type": "float", "default": 0.0, "unit": "s"},
            "gdd_s2": {"type": "float", "default": 0.0, "unit": "s^2"},
        },
        "nonideal": {"enable": {"type": "bool", "default": False}},
    }

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        opt_in = inputs["opt_in"]
        bandwidth = float(self.params.get("bandwidth_hz", 0.0))
        if bandwidth <= 0.0:
            return {"opt_out": opt_in.clone()}

        kind = str(self.params.get("kind", "bandpass")).lower()
        shape = str(self.params.get("shape", "gaussian")).lower()
        phase_mode = str(self.params.get("phase_mode", "none")).lower()
        center = float(self.params.get("center_hz", 0.0))
        order = int(self.params.get("order", 2))
        group_delay = float(self.params.get("group_delay_s", 0.0))
        gdd = float(self.params.get("gdd_s2", 0.0))

        data = opt_in.data
        n = data.shape[-1]
        freq = torch.fft.fftfreq(n, d=1.0 / opt_in.fs, device=data.device)

        if kind in ("bandpass", "bandstop"):
            freq_rel = torch.abs(freq - center)
            bw = bandwidth / 2.0
        else:
            freq_rel = torch.abs(freq)
            bw = bandwidth

        if shape == "rect":
            if kind in ("bandpass", "bandstop"):
                response = (freq_rel <= bw).to(freq_rel.dtype)
            elif kind == "highpass":
                response = (freq_rel >= bw).to(freq_rel.dtype)
            else:
                response = (freq_rel <= bw).to(freq_rel.dtype)
        elif shape == "butter":
            if kind == "highpass":
                eps = 1e-12
                response = 1.0 / torch.sqrt(1.0 + (bw / (freq_rel + eps)) ** (2 * max(1, order)))
            else:
                response = _butter_response(freq_rel, bw, order)
        else:
            response = _gaussian_response(freq_rel, bw)
            if kind == "highpass":
                response = 1.0 - response

        if kind == "bandstop":
            response = 1.0 - response

        response = response.to(data.real.dtype)

        phase = None
        if phase_mode != "none":
            omega = 2.0 * math.pi * freq
            if phase_mode == "minimum":
                phase = _phase_from_magnitude(response).to(data.real.dtype)
            else:
                phase = torch.zeros_like(response, dtype=data.real.dtype)
                if phase_mode in ("linear", "quadratic"):
                    phase = phase - group_delay * omega
                if phase_mode == "quadratic":
                    phase = phase - 0.5 * gdd * omega ** 2

        if phase is not None:
            response = response * torch.exp(1j * phase)
        response = response.to(torch.complex64 if data.is_complex() else torch.complex128)

        if opt_in.is_jones() and data.ndim == 2:
            data_f = torch.fft.fft(data, dim=-1)
            data_out = torch.fft.ifft(data_f * response, dim=-1)
        else:
            data_f = torch.fft.fft(data, dim=-1)
            data_out = torch.fft.ifft(data_f * response, dim=-1)

        signal = Signal(
            data=data_out,
            fs=opt_in.fs,
            t0=opt_in.t0,
            center_freq=opt_in.center_freq,
            pol_mode=opt_in.pol_mode,
            meta=dict(opt_in.meta),
        )
        return {"opt_out": signal}
