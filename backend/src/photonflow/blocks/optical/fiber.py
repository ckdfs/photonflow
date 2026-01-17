"""Optical fiber propagation (linear dispersion + loss)."""

from __future__ import annotations

import math
from typing import Dict

import torch

from photonflow.blocks.base import BaseBlock, register_block
from photonflow.core.signal import Signal
from photonflow.core.sim import SimContext


@register_block("OpticalFiber")
class OpticalFiber(BaseBlock):
    """Optical fiber propagation model. Simulates chromatic dispersion (GVD), attenuation, PMD, and Kerr nonlinearity using split-step Fourier method."""

    PORTS = {"opt_in": "optical", "opt_out": "optical"}
    SPEC = {
        "params": {
            "length_m": {"type": "float", "default": 0.0, "unit": "m"},
            "alpha_db_per_km": {"type": "float", "default": 0.0, "unit": "dB/km"},
            "beta2_s2_per_m": {"type": "float", "default": 0.0, "unit": "s^2/m"},
            "beta3_s3_per_m": {"type": "float", "default": 0.0, "unit": "s^3/m"},
            "ssfm_steps": {"type": "int", "default": 1},
            "ssfm_auto": {"type": "bool", "default": False},
            "ssfm_max_phase_rad": {"type": "float", "default": 0.1, "unit": "rad"},
            "ssfm_length_frac": {"type": "float", "default": 0.1},
            "ssfm_auto_mode": {
                "type": "enum",
                "default": "fft",
                "options": ["fft", "fast"],
            },
            "ssfm_min_steps": {"type": "int", "default": 1},
            "ssfm_max_steps": {"type": "int", "default": 128},
        },
        "nonideal": {
            "enable": {"type": "bool", "default": False},
            "pmd_dgd_s": {"type": "float", "default": 0.0, "unit": "s"},
            "pmd_axis_angle_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "birefringence_phi_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "pmd_time_vary": {"type": "bool", "default": False},
            "pmd_dgd_std_s": {"type": "float", "default": 0.0, "unit": "s"},
            "pmd_axis_std_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "pmd_biref_std_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            "pmd_corr_s": {"type": "float", "default": 0.0, "unit": "s"},
            "pmd_update_samples": {"type": "int", "default": 0},
            "nonlin_gamma_w_inv_m": {"type": "float", "default": 0.0, "unit": "1/W/m"},
        },
    }

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        opt_in = inputs["opt_in"]
        length_m = float(self.params.get("length_m", 0.0))
        alpha_db_per_km = float(self.params.get("alpha_db_per_km", 0.0))
        beta2 = float(self.params.get("beta2_s2_per_m", 0.0))
        beta3 = float(self.params.get("beta3_s3_per_m", 0.0))
        ssfm_steps = max(1, int(self.params.get("ssfm_steps", 1)))
        ssfm_auto = bool(self.params.get("ssfm_auto", False))
        ssfm_max_phase = float(self.params.get("ssfm_max_phase_rad", 0.1))
        ssfm_length_frac = float(self.params.get("ssfm_length_frac", 0.1))
        ssfm_auto_mode = str(self.params.get("ssfm_auto_mode", "fft")).lower()
        ssfm_min_steps = max(1, int(self.params.get("ssfm_min_steps", 1)))
        ssfm_max_steps = max(ssfm_min_steps, int(self.params.get("ssfm_max_steps", 128)))

        nonideal = self.nonideal if self.nonideal.get("enable", False) else {}
        pmd_dgd_s = float(nonideal.get("pmd_dgd_s", 0.0))
        pmd_axis_angle = float(nonideal.get("pmd_axis_angle_rad", 0.0))
        biref_phi = float(nonideal.get("birefringence_phi_rad", 0.0))
        pmd_time_vary = bool(nonideal.get("pmd_time_vary", False))
        pmd_dgd_std = float(nonideal.get("pmd_dgd_std_s", 0.0))
        pmd_axis_std = float(nonideal.get("pmd_axis_std_rad", 0.0))
        pmd_biref_std = float(nonideal.get("pmd_biref_std_rad", 0.0))
        pmd_corr_s = float(nonideal.get("pmd_corr_s", 0.0))
        pmd_update_samples = int(nonideal.get("pmd_update_samples", 0))
        gamma = float(nonideal.get("nonlin_gamma_w_inv_m", 0.0))

        has_linear = alpha_db_per_km != 0.0 or beta2 != 0.0 or beta3 != 0.0
        has_polar = (pmd_dgd_s != 0.0 or biref_phi != 0.0) and opt_in.is_jones() and opt_in.data.ndim == 2
        has_polar_time = (
            pmd_time_vary
            and opt_in.is_jones()
            and opt_in.data.ndim == 2
            and (has_polar or pmd_dgd_std > 0.0 or pmd_axis_std > 0.0 or pmd_biref_std > 0.0)
        )
        has_nonlinear = gamma != 0.0

        if length_m <= 0.0 or not (has_linear or has_polar or has_nonlinear):
            return {"opt_out": opt_in.clone()}

        data = opt_in.data
        n = data.shape[-1]
        freq = torch.fft.fftfreq(n, d=1.0 / opt_in.fs, device=data.device)
        omega = 2.0 * math.pi * freq

        alpha_power = 0.0
        if alpha_db_per_km != 0.0:
            alpha_power = math.log(10.0) / 10.0 * (alpha_db_per_km / 1000.0)

        if ssfm_auto and (has_linear or has_nonlinear):
            if opt_in.is_jones() and data.ndim == 2:
                power = torch.sum(torch.abs(data) ** 2, dim=0)
            else:
                power = torch.abs(data) ** 2
            pmax = float(power.max().item()) if power.numel() else 0.0

            if ssfm_auto_mode == "fast":
                if opt_in.is_jones() and data.ndim == 2:
                    deriv = torch.diff(data, dim=-1) * opt_in.fs
                    deriv_power = torch.sum(torch.abs(deriv) ** 2, dim=0)
                else:
                    deriv = torch.diff(data, dim=-1) * opt_in.fs
                    deriv_power = torch.abs(deriv) ** 2
                sum_power = float(power.sum().item()) if power.numel() else 0.0
                sum_deriv = float(deriv_power.sum().item()) if deriv_power.numel() else 0.0
                w_rms = math.sqrt(sum_deriv / sum_power) if sum_power > 0.0 else 0.0
            else:
                spec = torch.fft.fft(data, dim=-1)
                if opt_in.is_jones() and data.ndim == 2:
                    spec_power = torch.sum(torch.abs(spec) ** 2, dim=0)
                else:
                    spec_power = torch.abs(spec) ** 2
                spec_power = spec_power.to(torch.float64)
                sum_power = float(spec_power.sum().item()) if spec_power.numel() else 0.0
                if sum_power > 0.0:
                    omega_f = omega.to(torch.float64)
                    mean_w = (omega_f * spec_power).sum() / sum_power
                    var_w = ((omega_f - mean_w) ** 2 * spec_power).sum() / sum_power
                    w_rms = math.sqrt(max(var_w.item(), 0.0))
                else:
                    w_rms = 0.0

            phi_disp = abs(0.5 * beta2 * w_rms ** 2 + (1.0 / 6.0) * beta3 * w_rms ** 3)
            dz_disp = length_m if phi_disp == 0.0 else ssfm_max_phase / max(phi_disp, 1e-12)

            phi_nl = gamma * pmax if pmax > 0.0 else 0.0
            dz_nl = length_m if phi_nl == 0.0 else ssfm_max_phase / max(phi_nl, 1e-12)

            ld2 = math.inf
            ld3 = math.inf
            if w_rms > 0.0:
                if beta2 != 0.0:
                    ld2 = 1.0 / (abs(beta2) * w_rms ** 2)
                if beta3 != 0.0:
                    ld3 = 1.0 / (abs(beta3) * w_rms ** 3)
            ld = min(ld2, ld3)

            lnl = math.inf
            if gamma != 0.0 and pmax > 0.0:
                lnl = 1.0 / (gamma * pmax)

            length_frac = max(ssfm_length_frac, 0.0)
            dz_len = length_m
            if math.isfinite(ld) or math.isfinite(lnl):
                dz_len = length_frac * min(ld, lnl)

            dz = min(dz_disp, dz_nl, dz_len, length_m)
            ssfm_steps = int(math.ceil(length_m / max(dz, 1e-12)))
            ssfm_steps = min(max(ssfm_steps, ssfm_min_steps), ssfm_max_steps)

        def apply_linear(data_in: torch.Tensor, seg_len: float) -> torch.Tensor:
            phase = torch.zeros_like(omega, dtype=torch.float64)
            if beta2 != 0.0:
                phase = phase + (-0.5 * beta2 * seg_len) * omega ** 2
            if beta3 != 0.0:
                phase = phase + (-(1.0 / 6.0) * beta3 * seg_len) * omega ** 3
            if phase.dtype != data_in.real.dtype:
                phase = phase.to(data_in.real.dtype)
            h = torch.exp(1j * phase)
            if alpha_power != 0.0:
                loss = math.exp(-alpha_power * seg_len / 2.0)
                h = h * loss

            if opt_in.is_jones() and data_in.ndim == 2:
                data_f = torch.fft.fft(data_in, dim=-1) * h
                if has_polar and not has_polar_time:
                    scale = seg_len / length_m
                    phi = (biref_phi * scale) + omega * (pmd_dgd_s * scale)
                    half_phi = 0.5 * phi
                    if half_phi.dtype != data_f.real.dtype:
                        half_phi = half_phi.to(data_f.real.dtype)
                    e1 = torch.exp(-1j * half_phi)
                    e2 = torch.exp(1j * half_phi)
                    c = math.cos(pmd_axis_angle)
                    s = math.sin(pmd_axis_angle)
                    j11 = (c * c) * e1 + (s * s) * e2
                    j22 = (s * s) * e1 + (c * c) * e2
                    j12 = (c * s) * (e1 - e2)
                    ex = data_f[0]
                    ey = data_f[1]
                    out0 = j11 * ex + j12 * ey
                    out1 = j12 * ex + j22 * ey
                    data_f = torch.stack([out0, out1], dim=0)
                return torch.fft.ifft(data_f, dim=-1)

            data_f = torch.fft.fft(data_in, dim=-1)
            return torch.fft.ifft(data_f * h, dim=-1)

        def apply_nonlinear(data_in: torch.Tensor, seg_len: float) -> torch.Tensor:
            if gamma == 0.0:
                return data_in
            if opt_in.is_jones() and data_in.ndim == 2:
                power = torch.sum(torch.abs(data_in) ** 2, dim=0)
            else:
                power = torch.abs(data_in) ** 2
            phi_nl = gamma * seg_len * power
            if phi_nl.dtype != data_in.real.dtype:
                phi_nl = phi_nl.to(data_in.real.dtype)
            return data_in * torch.exp(1j * phi_nl)

        if gamma != 0.0 and ssfm_steps > 1:
            dz = length_m / ssfm_steps
            data_out = data
            for _ in range(ssfm_steps):
                data_out = apply_linear(data_out, dz / 2.0)
                data_out = apply_nonlinear(data_out, dz)
                data_out = apply_linear(data_out, dz / 2.0)
        else:
            data_out = apply_linear(data, length_m)
            if gamma != 0.0:
                if alpha_power != 0.0:
                    l_eff = (1.0 - math.exp(-alpha_power * length_m)) / alpha_power
                else:
                    l_eff = length_m
                data_out = apply_nonlinear(data_out, l_eff)

        if has_polar_time:
            block_len = pmd_update_samples
            if block_len <= 0:
                if pmd_corr_s > 0.0:
                    block_len = max(1, int(round(pmd_corr_s * opt_in.fs)))
                else:
                    block_len = data_out.shape[-1]
            block_len = max(1, block_len)
            blocks = int(math.ceil(data_out.shape[-1] / block_len))
            dt = block_len / opt_in.fs

            dtype = data_out.real.dtype
            device = data_out.device

            def ou_sequence(base: float, std: float) -> torch.Tensor:
                if std <= 0.0:
                    return torch.full((blocks,), base, device=device, dtype=dtype)
                if pmd_corr_s <= 0.0:
                    return base + std * torch.randn(blocks, device=device, dtype=dtype)
                a = math.exp(-dt / pmd_corr_s)
                b = std * math.sqrt(max(1.0 - a * a, 0.0))
                seq = torch.zeros(blocks, device=device, dtype=dtype)
                x = base + std * torch.randn((), device=device, dtype=dtype)
                for i in range(blocks):
                    if i > 0:
                        x = base + a * (x - base) + b * torch.randn((), device=device, dtype=dtype)
                    seq[i] = x
                return seq

            dgd_seq = ou_sequence(pmd_dgd_s, pmd_dgd_std)
            axis_seq = ou_sequence(pmd_axis_angle, pmd_axis_std)
            biref_seq = ou_sequence(biref_phi, pmd_biref_std)

            def apply_pmd_segment(segment: torch.Tensor, dgd: torch.Tensor, axis: torch.Tensor, biref: torch.Tensor) -> torch.Tensor:
                seg_len = segment.shape[-1]
                freq_seg = torch.fft.fftfreq(seg_len, d=1.0 / opt_in.fs, device=segment.device)
                omega_seg = 2.0 * math.pi * freq_seg
                phi = biref + omega_seg * dgd
                half_phi = 0.5 * phi
                if half_phi.dtype != segment.real.dtype:
                    half_phi = half_phi.to(segment.real.dtype)
                e1 = torch.exp(-1j * half_phi)
                e2 = torch.exp(1j * half_phi)
                c = torch.cos(axis)
                s = torch.sin(axis)
                j11 = (c * c) * e1 + (s * s) * e2
                j22 = (s * s) * e1 + (c * c) * e2
                j12 = (c * s) * (e1 - e2)
                seg_f = torch.fft.fft(segment, dim=-1)
                ex = seg_f[0]
                ey = seg_f[1]
                out0 = j11 * ex + j12 * ey
                out1 = j12 * ex + j22 * ey
                out_f = torch.stack([out0, out1], dim=0)
                return torch.fft.ifft(out_f, dim=-1)

            data_segments = []
            for i in range(blocks):
                start = i * block_len
                end = min(start + block_len, data_out.shape[-1])
                segment = data_out[:, start:end]
                data_segments.append(apply_pmd_segment(segment, dgd_seq[i], axis_seq[i], biref_seq[i]))
            data_out = torch.cat(data_segments, dim=-1)

        signal = Signal(
            data=data_out,
            fs=opt_in.fs,
            t0=opt_in.t0,
            center_freq=opt_in.center_freq,
            pol_mode=opt_in.pol_mode,
            meta=dict(opt_in.meta),
        )
        return {"opt_out": signal}
