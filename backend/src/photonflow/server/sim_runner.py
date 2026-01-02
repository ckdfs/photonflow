"""Simulation runner for graph jobs."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import torch

from photonflow.core import Graph, SimConfig
from photonflow.core.composites import composites, expand_graph_data
from photonflow.core.signal import Signal
from photonflow.measurements.spectrum import esa, osa


def run_graph_job(
    graph_data: Dict[str, Any],
    validate: bool = True,
    sim_override: Dict[str, Any] | None = None,
    max_points: int = 4096,
) -> Dict[str, Any]:
    graph = Graph.from_dict(graph_data, validate=validate)
    sim_cfg = _build_sim_config(graph_data.get("sim", {}), sim_override or {})
    expanded = expand_graph_data(graph_data, composites, annotate=False)
    outputs_spec = expanded.get("outputs", {})
    chunk = int(getattr(sim_cfg, "chunk", 0) or 0)
    if chunk > 0:
        outputs_chunks = graph.run_chunked(sim_cfg)
        results: Dict[str, Any] = {}
        for key, spec in outputs_spec.items():
            if key == "extra" and isinstance(spec, list):
                results[key] = [_build_measurement_chunked(outputs_chunks, item, sim_cfg, max_points) for item in spec]
            else:
                results[key] = _build_measurement_chunked(outputs_chunks, spec, sim_cfg, max_points)
    else:
        outputs = graph.run(sim_cfg)
        results = {}
        for key, spec in outputs_spec.items():
            if key == "extra" and isinstance(spec, list):
                results[key] = [_build_measurement(outputs, item, sim_cfg, max_points) for item in spec]
            else:
                results[key] = _build_measurement(outputs, spec, sim_cfg, max_points)

    results["meta"] = {
        "fs": sim_cfg.fs,
        "duration_s": sim_cfg.duration_s,
        "n_samples": sim_cfg.n_samples,
        "device": sim_cfg.device,
        "chunk": getattr(sim_cfg, "chunk", 0),
    }
    return results


def _build_sim_config(sim_data: Dict[str, Any], override: Dict[str, Any]) -> SimConfig:
    data = dict(sim_data)
    data.update(override)
    return SimConfig(
        backend=data.get("backend", "torch"),
        device=data.get("device", "cpu"),
        fs=data.get("fs", "auto"),
        fs_min=float(data.get("fs_min", 0.0)),
        fs_max=float(data.get("fs_max", 0.0)),
        oversample=int(data.get("oversample", 4)),
        seed=int(data.get("seed", 0)),
        window=data.get("window", "hann"),
        duration_s=float(data.get("duration_s", 1e-6)),
        n_samples=data.get("n_samples"),
        min_samples=int(data.get("min_samples", 0)),
        max_samples=int(data.get("max_samples", 0)),
        chunk=int(data.get("chunk", 0)),
    )


def _build_measurement(
    outputs: Dict[Tuple[str, str], "Signal"],
    spec: Dict[str, Any],
    sim_cfg: SimConfig,
    max_points: int,
) -> Dict[str, Any]:
    node = spec["node"]
    port = spec["port"]
    kind = spec.get("kind", "osa")
    params = spec.get("params", {})

    signal = outputs.get((node, port))
    if signal is None:
        raise ValueError(f"Missing output for {node}:{port}")

    window = params.get("window", sim_cfg.window)
    ref = float(params.get("ref", 1.0))

    include_power = bool(params.get("include_power", False))
    if kind == "esa":
        if signal.is_optical():
            raise ValueError(f"ESA expects electrical signal at {node}:{port}")
        data = esa(signal, window=window, ref=ref)
        return _format_spectrum("esa", data, max_points, include_power=include_power)
    if kind == "time":
        return _format_time(signal, max_points)

    if not signal.is_optical():
        raise ValueError(f"OSA expects optical signal at {node}:{port}")
    data = osa(signal, window=window, ref=ref)
    return _format_spectrum("osa", data, max_points, include_power=include_power)


def _build_measurement_chunked(
    outputs_chunks: list[Dict[Tuple[str, str], Signal]],
    spec: Dict[str, Any],
    sim_cfg: SimConfig,
    max_points: int,
) -> Dict[str, Any]:
    node = spec["node"]
    port = spec["port"]
    kind = spec.get("kind", "osa")
    params = spec.get("params", {})

    signals = []
    for outputs in outputs_chunks:
        signal = outputs.get((node, port))
        if signal is None:
            raise ValueError(f"Missing output for {node}:{port}")
        signals.append(signal)

    window = params.get("window", sim_cfg.window)
    ref = float(params.get("ref", 1.0))
    include_power = bool(params.get("include_power", False))

    if kind == "time":
        stitched = _stitch_signals(signals)
        return _format_time(stitched, max_points)

    if kind == "esa":
        if signals[0].is_optical():
            raise ValueError(f"ESA expects electrical signal at {node}:{port}")
        data = _accumulate_spectrum(signals, "esa", window, ref)
        return _format_spectrum("esa", data, max_points, include_power=include_power)

    if not signals[0].is_optical():
        raise ValueError(f"OSA expects optical signal at {node}:{port}")
    data = _accumulate_spectrum(signals, "osa", window, ref)
    return _format_spectrum("osa", data, max_points, include_power=include_power)


def _pad_signal(signal: Signal, n_samples: int) -> Signal:
    data = signal.data
    if data.shape[-1] == n_samples:
        return signal
    pad = n_samples - data.shape[-1]
    if pad <= 0:
        return Signal(
            data=data[..., :n_samples],
            fs=signal.fs,
            t0=signal.t0,
            center_freq=signal.center_freq,
            pol_mode=signal.pol_mode,
            meta=dict(signal.meta),
        )
    pad_shape = data.shape[:-1] + (pad,)
    pad_data = torch.zeros(pad_shape, device=data.device, dtype=data.dtype)
    return Signal(
        data=torch.cat([data, pad_data], dim=-1),
        fs=signal.fs,
        t0=signal.t0,
        center_freq=signal.center_freq,
        pol_mode=signal.pol_mode,
        meta=dict(signal.meta),
    )


def _stitch_signals(signals: list[Signal]) -> Signal:
    first = signals[0]
    data = torch.cat([sig.data for sig in signals], dim=-1)
    return Signal(
        data=data,
        fs=first.fs,
        t0=0.0,
        center_freq=first.center_freq,
        pol_mode=first.pol_mode,
        meta=dict(first.meta),
    )


def _accumulate_spectrum(
    signals: list[Signal],
    kind: str,
    window: str,
    ref: float,
) -> Dict[str, torch.Tensor]:
    chunk_len = max(sig.data.shape[-1] for sig in signals)
    power_sum = None
    freq = None
    freq_rel = None
    center_freq_hz = None
    total_weight = 0.0
    for sig in signals:
        actual_len = sig.data.shape[-1]
        padded = _pad_signal(sig, chunk_len)
        if kind == "esa":
            data = esa(padded, window=window, ref=ref)
        else:
            data = osa(padded, window=window, ref=ref)
        power = data["power"]
        if actual_len > 0 and actual_len != chunk_len:
            power = power * (chunk_len / actual_len)
        if power_sum is None:
            power_sum = power * actual_len
            freq = data["freq"]
            freq_rel = data.get("freq_rel")
            center_freq_hz = data.get("center_freq_hz")
        else:
            power_sum = power_sum + power * actual_len
        total_weight += actual_len
    power_avg = power_sum / max(total_weight, 1.0)
    power_db = 10.0 * torch.log10(power_avg / ref + 1e-30)
    payload = {"freq": freq, "power": power_avg, "power_db": power_db}
    if kind == "osa" and freq_rel is not None:
        payload["freq_rel"] = freq_rel
        payload["center_freq_hz"] = center_freq_hz if center_freq_hz is not None else 0.0
    return payload


def _format_spectrum(
    kind: str,
    data: Dict[str, torch.Tensor],
    max_points: int,
    include_power: bool = False,
) -> Dict[str, Any]:
    freq = data["freq"]
    power_db = data["power_db"]
    idx = _downsample_index(freq.numel(), max_points)
    freq = freq[idx].detach().cpu()
    power_db = power_db[idx].detach().cpu()
    payload = {
        "kind": kind,
        "freq": freq.tolist(),
        "power_db": power_db.tolist(),
    }
    if "freq_rel" in data:
        freq_rel = data["freq_rel"][idx].detach().cpu()
        payload["freq_rel"] = freq_rel.tolist()
    if "center_freq_hz" in data:
        payload["center_freq_hz"] = float(data["center_freq_hz"])
    if include_power:
        power = data["power"][idx].detach().cpu()
        payload["power"] = power.tolist()
    return payload


def _format_time(signal: "Signal", max_points: int) -> Dict[str, Any]:
    t = signal.time()
    data = signal.data
    if data.is_complex():
        real = torch.real(data)
        imag = torch.imag(data)
    else:
        real = data
        imag = None

    idx = _downsample_index(t.numel(), max_points)
    t = t[idx].detach().cpu()
    real = real[idx].detach().cpu()
    payload = {"kind": "time", "t": t.tolist(), "real": real.tolist()}
    if imag is not None:
        imag = imag[idx].detach().cpu()
        payload["imag"] = imag.tolist()
    return payload


def _downsample_pair(x: torch.Tensor, y: torch.Tensor, max_points: int) -> tuple[torch.Tensor, torch.Tensor]:
    n = x.numel()
    if n <= max_points:
        return x.detach().cpu(), y.detach().cpu()
    step = max(1, int(n // max_points))
    return x[::step].detach().cpu(), y[::step].detach().cpu()


def _downsample_index(n: int, max_points: int) -> slice:
    if n <= max_points:
        return slice(None)
    step = max(1, int(n // max_points))
    return slice(None, None, step)
