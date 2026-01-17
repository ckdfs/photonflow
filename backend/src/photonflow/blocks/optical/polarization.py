"""Polarization manipulation blocks."""

from __future__ import annotations

import math
from typing import Dict, Tuple

import torch

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext


def _to_jones(opt_in: Signal) -> Tuple[torch.Tensor, str]:
    data = opt_in.data
    if opt_in.is_jones() and data.ndim == 2:
        return data, "jones"
    ex = data
    ey = torch.zeros_like(ex)
    return torch.stack([ex, ey], dim=0), "jones"


def _apply_waveplate(data: torch.Tensor, retardance: float, axis_angle: float) -> torch.Tensor:
    ex = data[0]
    ey = data[1]

    half = 0.5 * retardance
    e1 = torch.exp(-1j * ex.real.new_tensor(half))
    e2 = torch.exp(1j * ex.real.new_tensor(half))

    c = math.cos(axis_angle)
    s = math.sin(axis_angle)
    c = ex.real.new_tensor(c)
    s = ex.real.new_tensor(s)

    j11 = (c * c) * e1 + (s * s) * e2
    j22 = (s * s) * e1 + (c * c) * e2
    j12 = (c * s) * (e1 - e2)

    out0 = j11 * ex + j12 * ey
    out1 = j12 * ex + j22 * ey
    return torch.stack([out0, out1], dim=0)


def _ou_sequence(
    base: float,
    std: float,
    blocks: int,
    dt: float,
    corr_s: float,
    device: torch.device,
    dtype: torch.dtype,
) -> torch.Tensor:
    if std <= 0.0:
        return torch.full((blocks,), base, device=device, dtype=dtype)
    if corr_s <= 0.0:
        return base + std * torch.randn(blocks, device=device, dtype=dtype)
    a = math.exp(-dt / corr_s)
    b = std * math.sqrt(max(1.0 - a * a, 0.0))
    seq = torch.zeros(blocks, device=device, dtype=dtype)
    x = base + std * torch.randn((), device=device, dtype=dtype)
    for i in range(blocks):
        if i > 0:
            x = base + a * (x - base) + b * torch.randn((), device=device, dtype=dtype)
        seq[i] = x
    return seq

@register_block("PolarizationRotator")
class PolarizationRotator(BaseBlock):
    """Polarization rotator. Rotates the polarization state by a specified angle."""

    PORTS = {"opt_in": "optical", "opt_out": "optical"}
    SPEC = {
        "params": {"angle_rad": {"type": "float", "default": 0.0, "unit": "rad"}},
        "nonideal": {
            "enable": {"type": "bool", "default": False},
            "angle_noise_std_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "time_vary": {"type": "bool", "default": False},
            "angle_drift_std_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "drift_corr_s": {"type": "float", "default": 0.0, "unit": "s"},
            "drift_update_samples": {"type": "int", "default": 0},
        },
    }

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        opt_in = inputs["opt_in"]
        angle = float(self.params.get("angle_rad", 0.0))

        data, pol_mode = _to_jones(opt_in)
        nonideal = self.nonideal if self.nonideal.get("enable", False) else {}
        angle_noise = float(nonideal.get("angle_noise_std_rad", 0.0))
        if angle_noise > 0.0:
            angle += float(torch.randn((), device=data.device, dtype=data.real.dtype) * angle_noise)

        time_vary = bool(nonideal.get("time_vary", False))
        if time_vary and data.shape[-1] > 1:
            block_len = int(nonideal.get("drift_update_samples", 0))
            if block_len <= 0:
                corr_s = float(nonideal.get("drift_corr_s", 0.0))
                block_len = max(1, int(round(corr_s * opt_in.fs))) if corr_s > 0.0 else data.shape[-1]
            block_len = max(1, block_len)
            blocks = int(math.ceil(data.shape[-1] / block_len))
            dt = block_len / opt_in.fs

            angle_std = float(nonideal.get("angle_drift_std_rad", 0.0))
            angle_seq = _ou_sequence(
                angle, angle_std, blocks, dt, float(nonideal.get("drift_corr_s", 0.0)), data.device, data.real.dtype
            )

            segments = []
            for i in range(blocks):
                start = i * block_len
                end = min(start + block_len, data.shape[-1])
                seg = data[:, start:end]
                c = math.cos(float(angle_seq[i].item()))
                s = math.sin(float(angle_seq[i].item()))
                c = seg.real.new_tensor(c)
                s = seg.real.new_tensor(s)
                out0 = c * seg[0] - s * seg[1]
                out1 = s * seg[0] + c * seg[1]
                segments.append(torch.stack([out0, out1], dim=0))
            data_out = torch.cat(segments, dim=-1)
        else:
            ex = data[0]
            ey = data[1]
            c = math.cos(angle)
            s = math.sin(angle)
            c = ex.real.new_tensor(c)
            s = ex.real.new_tensor(s)
            out0 = c * ex - s * ey
            out1 = s * ex + c * ey
            data_out = torch.stack([out0, out1], dim=0)

        signal = Signal(
            data=data_out,
            fs=opt_in.fs,
            t0=opt_in.t0,
            center_freq=opt_in.center_freq,
            pol_mode=pol_mode,
            meta=dict(opt_in.meta),
        )
        return {"opt_out": signal}


@register_block("PolarizationPDL")
class PolarizationPDL(BaseBlock):
    """Polarization-dependent loss (PDL) element. Applies different attenuation to orthogonal polarization states."""

    PORTS = {"opt_in": "optical", "opt_out": "optical"}
    SPEC = {
        "params": {
            "pdl_db": {"type": "float", "default": 0.0, "unit": "dB"},
            "axis_angle_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "loss_db": {"type": "float", "default": 0.0, "unit": "dB"},
        },
        "nonideal": {
            "enable": {"type": "bool", "default": False},
            "pdl_noise_std_db": {"type": "float", "default": 0.0, "unit": "dB"},
            "axis_noise_std_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "time_vary": {"type": "bool", "default": False},
            "pdl_drift_std_db": {"type": "float", "default": 0.0, "unit": "dB"},
            "axis_drift_std_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "drift_corr_s": {"type": "float", "default": 0.0, "unit": "s"},
            "drift_update_samples": {"type": "int", "default": 0},
        },
    }

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        opt_in = inputs["opt_in"]
        pdl_db = float(self.params.get("pdl_db", 0.0))
        axis_angle = float(self.params.get("axis_angle_rad", 0.0))
        loss_db = float(self.params.get("loss_db", 0.0))

        data, pol_mode = _to_jones(opt_in)
        nonideal = self.nonideal if self.nonideal.get("enable", False) else {}
        pdl_noise = float(nonideal.get("pdl_noise_std_db", 0.0))
        axis_noise = float(nonideal.get("axis_noise_std_rad", 0.0))
        if pdl_noise > 0.0:
            pdl_db += float(torch.randn((), device=data.device, dtype=data.real.dtype) * pdl_noise)
        if axis_noise > 0.0:
            axis_angle += float(torch.randn((), device=data.device, dtype=data.real.dtype) * axis_noise)

        time_vary = bool(nonideal.get("time_vary", False))
        if time_vary and data.shape[-1] > 1:
            block_len = int(nonideal.get("drift_update_samples", 0))
            if block_len <= 0:
                corr_s = float(nonideal.get("drift_corr_s", 0.0))
                block_len = max(1, int(round(corr_s * opt_in.fs))) if corr_s > 0.0 else data.shape[-1]
            block_len = max(1, block_len)
            blocks = int(math.ceil(data.shape[-1] / block_len))
            dt = block_len / opt_in.fs

            pdl_std = float(nonideal.get("pdl_drift_std_db", 0.0))
            axis_std = float(nonideal.get("axis_drift_std_rad", 0.0))
            pdl_seq = _ou_sequence(
                pdl_db, pdl_std, blocks, dt, float(nonideal.get("drift_corr_s", 0.0)), data.device, data.real.dtype
            )
            axis_seq = _ou_sequence(
                axis_angle, axis_std, blocks, dt, float(nonideal.get("drift_corr_s", 0.0)), data.device, data.real.dtype
            )

            segments = []
            for i in range(blocks):
                start = i * block_len
                end = min(start + block_len, data.shape[-1])
                seg = data[:, start:end]
                a = 10 ** (-float(pdl_seq[i].item()) / 20.0)
                c = math.cos(float(axis_seq[i].item()))
                s = math.sin(float(axis_seq[i].item()))
                a = seg.real.new_tensor(a)
                c = seg.real.new_tensor(c)
                s = seg.real.new_tensor(s)
                j11 = (c * c) * a + (s * s)
                j22 = (s * s) * a + (c * c)
                j12 = (c * s) * (a - 1.0)
                out0 = j11 * seg[0] + j12 * seg[1]
                out1 = j12 * seg[0] + j22 * seg[1]
                if loss_db != 0.0:
                    loss = 10 ** (-loss_db / 20.0)
                    loss = seg.real.new_tensor(loss)
                    out0 = out0 * loss
                    out1 = out1 * loss
                segments.append(torch.stack([out0, out1], dim=0))
            data_out = torch.cat(segments, dim=-1)
        else:
            ex = data[0]
            ey = data[1]
            a = 10 ** (-pdl_db / 20.0)
            c = math.cos(axis_angle)
            s = math.sin(axis_angle)
            c = ex.real.new_tensor(c)
            s = ex.real.new_tensor(s)
            a = ex.real.new_tensor(a)

            j11 = (c * c) * a + (s * s)
            j22 = (s * s) * a + (c * c)
            j12 = (c * s) * (a - 1.0)

            out0 = j11 * ex + j12 * ey
            out1 = j12 * ex + j22 * ey

            if loss_db != 0.0:
                loss = 10 ** (-loss_db / 20.0)
                loss = ex.real.new_tensor(loss)
                out0 = out0 * loss
                out1 = out1 * loss

            data_out = torch.stack([out0, out1], dim=0)

        signal = Signal(
            data=data_out,
            fs=opt_in.fs,
            t0=opt_in.t0,
            center_freq=opt_in.center_freq,
            pol_mode=pol_mode,
            meta=dict(opt_in.meta),
        )
        return {"opt_out": signal}


@register_block("PolarizationWaveplate")
class PolarizationWaveplate(BaseBlock):
    """General waveplate. Introduces a phase delay (retardance) between polarization components. Use for quarter-wave (λ/4) or half-wave (λ/2) plates."""

    PORTS = {"opt_in": "optical", "opt_out": "optical"}
    SPEC = {
        "params": {
            "retardance_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "axis_angle_rad": {"type": "float", "default": 0.0, "unit": "rad"},
        },
        "nonideal": {
            "enable": {"type": "bool", "default": False},
            "axis_noise_std_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "retardance_noise_std_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "time_vary": {"type": "bool", "default": False},
            "axis_drift_std_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "retardance_drift_std_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "drift_corr_s": {"type": "float", "default": 0.0, "unit": "s"},
            "drift_update_samples": {"type": "int", "default": 0},
        },
    }

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        opt_in = inputs["opt_in"]
        retardance = float(self.params.get("retardance_rad", 0.0))
        axis_angle = float(self.params.get("axis_angle_rad", 0.0))

        data, pol_mode = _to_jones(opt_in)
        nonideal = self.nonideal if self.nonideal.get("enable", False) else {}
        axis_noise = float(nonideal.get("axis_noise_std_rad", 0.0))
        retardance_noise = float(nonideal.get("retardance_noise_std_rad", 0.0))
        if axis_noise > 0.0:
            axis_angle += float(torch.randn((), device=data.device, dtype=data.real.dtype) * axis_noise)
        if retardance_noise > 0.0:
            retardance += float(torch.randn((), device=data.device, dtype=data.real.dtype) * retardance_noise)

        time_vary = bool(nonideal.get("time_vary", False))
        if time_vary and data.shape[-1] > 1:
            block_len = int(nonideal.get("drift_update_samples", 0))
            if block_len <= 0:
                corr_s = float(nonideal.get("drift_corr_s", 0.0))
                block_len = max(1, int(round(corr_s * opt_in.fs))) if corr_s > 0.0 else data.shape[-1]
            block_len = max(1, block_len)
            blocks = int(math.ceil(data.shape[-1] / block_len))
            dt = block_len / opt_in.fs

            axis_std = float(nonideal.get("axis_drift_std_rad", 0.0))
            retardance_std = float(nonideal.get("retardance_drift_std_rad", 0.0))
            axis_seq = _ou_sequence(
                axis_angle, axis_std, blocks, dt, float(nonideal.get("drift_corr_s", 0.0)), data.device, data.real.dtype
            )
            ret_seq = _ou_sequence(
                retardance,
                retardance_std,
                blocks,
                dt,
                float(nonideal.get("drift_corr_s", 0.0)),
                data.device,
                data.real.dtype,
            )
            segments = []
            for i in range(blocks):
                start = i * block_len
                end = min(start + block_len, data.shape[-1])
                seg = data[:, start:end]
                segments.append(_apply_waveplate(seg, float(ret_seq[i].item()), float(axis_seq[i].item())))
            data_out = torch.cat(segments, dim=-1)
        else:
            data_out = _apply_waveplate(data, retardance, axis_angle)

        signal = Signal(
            data=data_out,
            fs=opt_in.fs,
            t0=opt_in.t0,
            center_freq=opt_in.center_freq,
            pol_mode=pol_mode,
            meta=dict(opt_in.meta),
        )
        return {"opt_out": signal}


@register_block("PolarizationController")
class PolarizationController(BaseBlock):
    """Polarization controller. Cascaded waveplate configuration for arbitrary polarization state transformation. Supports presets like QHQ (quarter-half-quarter)."""

    PORTS = {"opt_in": "optical", "opt_out": "optical"}
    SPEC = {
        "params": {
            "preset": {
                "type": "enum",
                "default": "custom",
                "options": ["custom", "QHQ", "H", "Q", "HWP", "QWP"],
            },
            "angle1_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "angle2_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "angle3_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "retardance1_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "retardance2_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "retardance3_rad": {"type": "float", "default": 0.0, "unit": "rad"},
        },
        "nonideal": {
            "enable": {"type": "bool", "default": False},
            "angle_noise_std_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "retardance_noise_std_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "time_vary": {"type": "bool", "default": False},
            "angle_drift_std_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "retardance_drift_std_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "drift_corr_s": {"type": "float", "default": 0.0, "unit": "s"},
            "drift_update_samples": {"type": "int", "default": 0},
        },
    }

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        opt_in = inputs["opt_in"]
        preset = str(self.params.get("preset", "custom")).upper()
        angle1 = float(self.params.get("angle1_rad", 0.0))
        angle2 = float(self.params.get("angle2_rad", 0.0))
        angle3 = float(self.params.get("angle3_rad", 0.0))
        ret1 = float(self.params.get("retardance1_rad", 0.0))
        ret2 = float(self.params.get("retardance2_rad", 0.0))
        ret3 = float(self.params.get("retardance3_rad", 0.0))

        if preset == "QWP":
            preset = "Q"
        elif preset == "HWP":
            preset = "H"

        if preset == "Q":
            ret1, ret2, ret3 = math.pi / 2.0, 0.0, 0.0
        elif preset == "H":
            ret1, ret2, ret3 = math.pi, 0.0, 0.0
        elif preset == "QHQ":
            ret1, ret2, ret3 = math.pi / 2.0, math.pi, math.pi / 2.0

        data, pol_mode = _to_jones(opt_in)
        nonideal = self.nonideal if self.nonideal.get("enable", False) else {}
        angle_noise = float(nonideal.get("angle_noise_std_rad", 0.0))
        retardance_noise = float(nonideal.get("retardance_noise_std_rad", 0.0))
        if angle_noise > 0.0:
            angle1 += float(torch.randn((), device=data.device, dtype=data.real.dtype) * angle_noise)
            angle2 += float(torch.randn((), device=data.device, dtype=data.real.dtype) * angle_noise)
            angle3 += float(torch.randn((), device=data.device, dtype=data.real.dtype) * angle_noise)
        if retardance_noise > 0.0:
            ret1 += float(torch.randn((), device=data.device, dtype=data.real.dtype) * retardance_noise)
            ret2 += float(torch.randn((), device=data.device, dtype=data.real.dtype) * retardance_noise)
            ret3 += float(torch.randn((), device=data.device, dtype=data.real.dtype) * retardance_noise)

        time_vary = bool(nonideal.get("time_vary", False))
        if time_vary and data.shape[-1] > 1:
            block_len = int(nonideal.get("drift_update_samples", 0))
            if block_len <= 0:
                corr_s = float(nonideal.get("drift_corr_s", 0.0))
                block_len = max(1, int(round(corr_s * opt_in.fs))) if corr_s > 0.0 else data.shape[-1]
            block_len = max(1, block_len)
            blocks = int(math.ceil(data.shape[-1] / block_len))
            dt = block_len / opt_in.fs

            angle_std = float(nonideal.get("angle_drift_std_rad", 0.0))
            retardance_std = float(nonideal.get("retardance_drift_std_rad", 0.0))
            angle1_seq = _ou_sequence(
                angle1, angle_std, blocks, dt, float(nonideal.get("drift_corr_s", 0.0)), data.device, data.real.dtype
            )
            angle2_seq = _ou_sequence(
                angle2, angle_std, blocks, dt, float(nonideal.get("drift_corr_s", 0.0)), data.device, data.real.dtype
            )
            angle3_seq = _ou_sequence(
                angle3, angle_std, blocks, dt, float(nonideal.get("drift_corr_s", 0.0)), data.device, data.real.dtype
            )
            ret1_seq = _ou_sequence(
                ret1, retardance_std, blocks, dt, float(nonideal.get("drift_corr_s", 0.0)), data.device, data.real.dtype
            )
            ret2_seq = _ou_sequence(
                ret2, retardance_std, blocks, dt, float(nonideal.get("drift_corr_s", 0.0)), data.device, data.real.dtype
            )
            ret3_seq = _ou_sequence(
                ret3, retardance_std, blocks, dt, float(nonideal.get("drift_corr_s", 0.0)), data.device, data.real.dtype
            )

            segments = []
            for i in range(blocks):
                start = i * block_len
                end = min(start + block_len, data.shape[-1])
                seg = data[:, start:end]
                seg_out = seg
                stages = [
                    (float(ret1_seq[i].item()), float(angle1_seq[i].item())),
                    (float(ret2_seq[i].item()), float(angle2_seq[i].item())),
                    (float(ret3_seq[i].item()), float(angle3_seq[i].item())),
                ]
                for retardance, axis_angle in stages:
                    if retardance == 0.0:
                        continue
                    seg_out = _apply_waveplate(seg_out, retardance, axis_angle)
                segments.append(seg_out)
            data_out = torch.cat(segments, dim=-1)
        else:
            stages = [
                (ret1, angle1),
                (ret2, angle2),
                (ret3, angle3),
            ]
            data_out = data
            for retardance, axis_angle in stages:
                if retardance == 0.0:
                    continue
                data_out = _apply_waveplate(data_out, retardance, axis_angle)

        signal = Signal(
            data=data_out,
            fs=opt_in.fs,
            t0=opt_in.t0,
            center_freq=opt_in.center_freq,
            pol_mode=pol_mode,
            meta=dict(opt_in.meta),
        )
        return {"opt_out": signal}
