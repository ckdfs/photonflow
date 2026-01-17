"""PhotonFlow core package."""

__version__ = "0.2.0"

from photonflow.core.graph import Graph
from photonflow.core.sim import SimConfig
from photonflow.core.signal import Signal
import photonflow.blocks  # Register default blocks.
import photonflow.core.composites  # Register composite templates.

__all__ = ["Graph", "SimConfig", "Signal"]
