"""Simulation runner for graph jobs."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import torch

from photonflow.core import Graph, SimConfig
from photonflow.measurements.spectrum import esa, osa


def run_graph_job(
    graph_data: Dict[str, Any],
    validate: bool = True,
    sim_override: Dict[str, Any] | None = None,
    max_points: int = 4096,
) -> Dict[str, Any]:
    graph = Graph.from_dict(graph_data, validate=validate)
    sim_cfg = _build_sim_config(graph_data.get("sim", {}), sim_override or {})
    outputs = graph.run(sim_cfg)
    results: Dict[str, Any] = {}

    outputs_spec = graph_data.get("outputs", {})
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
    }
    return results


def _build_sim_config(sim_data: Dict[str, Any], override: Dict[str, Any]) -> SimConfig:
    data = dict(sim_data)
    data.update(override)
    return SimConfig(
        backend=data.get("backend", "torch"),
        device=data.get("device", "cpu"),
        fs=data.get("fs", "auto"),
        oversample=int(data.get("oversample", 4)),
        seed=int(data.get("seed", 0)),
        window=data.get("window", "hann"),
        duration_s=float(data.get("duration_s", 1e-6)),
        n_samples=data.get("n_samples"),
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
