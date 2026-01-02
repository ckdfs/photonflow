"""Block registry and imports."""

from photonflow.blocks.base import registry, register_block

# Optical blocks
from photonflow.blocks.optical.laser import Laser
from photonflow.blocks.optical.pm import PM
from photonflow.blocks.optical.mzm import MZM
from photonflow.blocks.optical.dpmzm import DPMZM
from photonflow.blocks.optical.coupler import Coupler
from photonflow.blocks.optical.phase_shifter import PhaseShifter
from photonflow.blocks.optical.attenuator import Attenuator
from photonflow.blocks.optical.fiber import OpticalFiber
from photonflow.blocks.optical.optical_filter import OpticalFilter
from photonflow.blocks.optical.polarization import (
    PolarizationRotator,
    PolarizationPDL,
    PolarizationWaveplate,
    PolarizationController,
)

# Electrical blocks
from photonflow.blocks.electrical.rf_source import RFSource
from photonflow.blocks.electrical.dc_source import DCSource
from photonflow.blocks.electrical.elec_splitter import ElecSplitter
from photonflow.blocks.electrical.elec_gain import ElecGain

# Detectors
from photonflow.blocks.detectors.pd import PD

__all__ = [
    "registry",
    "register_block",
    "Laser",
    "PM",
    "MZM",
    "DPMZM",
    "Coupler",
    "PhaseShifter",
    "Attenuator",
    "OpticalFiber",
    "OpticalFilter",
    "PolarizationRotator",
    "PolarizationPDL",
    "PolarizationWaveplate",
    "PolarizationController",
    "RFSource",
    "DCSource",
    "ElecSplitter",
    "ElecGain",
    "PD",
]
