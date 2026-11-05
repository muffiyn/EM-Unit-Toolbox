"""EM Unit Toolbox: unit conversion for energetic-materials data."""

from .converter import (
    UnitError,
    convert,
    dimension_of,
    get_unit,
    list_units,
    molar_to_specific,
    specific_to_molar,
    specific_to_total,
    to_si,
    total_to_specific,
)
from .electrostatic import esd_energy, esd_voltage
from .impact import drop_height, drop_mass, force_to_mass, potential_energy, weight_force
from .units import STANDARD_GRAVITY, Unit

__version__ = "0.1.0"

__all__ = [
    "STANDARD_GRAVITY",
    "Unit",
    "UnitError",
    "convert",
    "dimension_of",
    "drop_height",
    "drop_mass",
    "esd_energy",
    "esd_voltage",
    "force_to_mass",
    "get_unit",
    "list_units",
    "molar_to_specific",
    "potential_energy",
    "specific_to_molar",
    "specific_to_total",
    "to_si",
    "total_to_specific",
    "weight_force",
]
