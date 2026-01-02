"""Signal data structure."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import torch


@dataclass
class Signal:
    data: torch.Tensor
    fs: float
    t0: float = 0.0
    center_freq: Optional[float] = None
    pol_mode: str = "scalar"
    meta: Dict[str, Any] = field(default_factory=dict)

    def clone(self) -> "Signal":
        return Signal(
            data=self.data.clone(),
            fs=self.fs,
            t0=self.t0,
            center_freq=self.center_freq,
            pol_mode=self.pol_mode,
            meta=dict(self.meta),
        )

    def time(self) -> torch.Tensor:
        n = self.data.shape[-1]
        device = self.data.device
        if self.data.dtype in (torch.complex64, torch.complex128):
            dtype = torch.float32 if self.data.dtype == torch.complex64 else torch.float64
        else:
            dtype = self.data.dtype
        return self.t0 + torch.arange(n, device=device, dtype=dtype) / self.fs

    def is_optical(self) -> bool:
        return self.center_freq is not None

    def is_jones(self) -> bool:
        return self.pol_mode == "jones"
