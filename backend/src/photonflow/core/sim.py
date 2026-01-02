"""Simulation configuration and context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import torch


@dataclass
class SimConfig:
    backend: str = "torch"
    device: str = "cpu"
    fs: float | str = "auto"
    oversample: int = 4
    seed: int = 0
    window: str = "hann"
    duration_s: float = 1e-6
    n_samples: Optional[int] = None


class SimContext:
    def __init__(self, config: SimConfig, fs: float, n_samples: int):
        self.config = config
        self.fs = fs
        self.n_samples = n_samples
        self.device = torch.device(config.device)
        self.t0 = 0.0
        torch.manual_seed(config.seed)

    def time(self) -> torch.Tensor:
        return self.t0 + torch.arange(self.n_samples, device=self.device) / self.fs

    def zeros(self, shape: Sequence[int], dtype: torch.dtype) -> torch.Tensor:
        return torch.zeros(shape, device=self.device, dtype=dtype)
