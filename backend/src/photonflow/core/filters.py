"""Signal filtering utilities."""

from __future__ import annotations

import torch


def lowpass_rect(x: torch.Tensor, fs: float, cutoff_hz: float) -> torch.Tensor:
    """Apply an ideal rectangular low-pass filter to a 1-D signal."""
    if cutoff_hz <= 0 or cutoff_hz >= fs / 2.0:
        return x
    n = x.numel()
    freq = torch.fft.fftfreq(n, d=1.0 / fs, device=x.device)
    h = (torch.abs(freq) <= cutoff_hz).to(dtype=x.dtype)
    x_f = torch.fft.fft(x)
    h = h.to(dtype=x_f.dtype)
    y = torch.fft.ifft(x_f * h)
    if x.is_complex():
        return y
    return torch.real(y)


def lowpass_rc(x: torch.Tensor, fs: float, cutoff_hz: float) -> torch.Tensor:
    """Apply a first-order RC low-pass filter in frequency domain."""
    if cutoff_hz <= 0 or cutoff_hz >= fs / 2.0:
        return x
    n = x.numel()
    freq = torch.fft.fftfreq(n, d=1.0 / fs, device=x.device)
    h = 1.0 / (1.0 + 1j * (freq / cutoff_hz))
    x_f = torch.fft.fft(x)
    h = h.to(dtype=x_f.dtype)
    y = torch.fft.ifft(x_f * h)
    if x.is_complex():
        return y
    return torch.real(y)


def apply_lowpass(x: torch.Tensor, fs: float, cutoff_hz: float, kind: str = "rect") -> torch.Tensor:
    """Select and apply a low-pass filter by kind."""
    kind = (kind or "rect").lower()
    if kind == "rc":
        return lowpass_rc(x, fs, cutoff_hz)
    return lowpass_rect(x, fs, cutoff_hz)
