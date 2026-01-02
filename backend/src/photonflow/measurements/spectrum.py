"""OSA and ESA spectrum utilities."""

from __future__ import annotations

import torch

from photonflow.core.signal import Signal


def window_function(name: str, n: int, device: torch.device) -> torch.Tensor:
    name = name.lower()
    if name == "hann":
        return torch.hann_window(n, device=device)
    if name == "hamming":
        return torch.hamming_window(n, device=device)
    if name == "blackman":
        return torch.blackman_window(n, device=device)
    if name == "kaiser":
        return torch.kaiser_window(n, beta=14.0, device=device)
    return torch.ones(n, device=device)


def osa(signal: Signal, window: str = "hann", ref: float = 1.0) -> dict:
    data = signal.data
    if signal.pol_mode == "jones" and data.ndim == 2:
        n = data.shape[-1]
        w = window_function(window, n, data.device)
        data_w = data * w
        spec = torch.fft.fftshift(torch.fft.fft(data_w, dim=-1), dim=-1)
        power = torch.sum(torch.abs(spec) ** 2, dim=0) / n
    else:
        n = data.numel()
        w = window_function(window, n, data.device)
        data_w = data * w
        spec = torch.fft.fftshift(torch.fft.fft(data_w))
        power = torch.abs(spec) ** 2 / n
    freq_rel = torch.fft.fftshift(torch.fft.fftfreq(n, d=1.0 / signal.fs)).to(torch.float64)
    center_freq = float(signal.center_freq) if signal.center_freq is not None else 0.0
    freq = freq_rel + center_freq

    power_db = 10.0 * torch.log10(power / ref + 1e-30)
    return {
        "freq": freq,
        "freq_rel": freq_rel,
        "center_freq_hz": center_freq,
        "power": power,
        "power_db": power_db,
    }


def esa(signal: Signal, window: str = "hann", ref: float = 1.0) -> dict:
    data = signal.data
    n = data.numel()
    w = window_function(window, n, data.device)
    data_w = data * w

    spec = torch.fft.fftshift(torch.fft.fft(data_w))
    power = torch.abs(spec) ** 2 / n
    freq = torch.fft.fftshift(torch.fft.fftfreq(n, d=1.0 / signal.fs))

    power_db = 10.0 * torch.log10(power / ref + 1e-30)
    return {"freq": freq, "power": power, "power_db": power_db}
