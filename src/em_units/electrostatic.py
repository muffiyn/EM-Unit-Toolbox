"""Electrostatic discharge (ESD) spark energy: E = ½·C·V².

ESD sensitivity tests discharge a capacitor charged to a voltage through the
sample; the spark energy follows from the capacitance and voltage.
"""

from __future__ import annotations

import math

from .converter import _require
from .units import CAPACITANCE, ENERGY, VOLTAGE


def esd_energy(
    capacitance: float,
    capacitance_unit: str,
    voltage: float,
    voltage_unit: str,
    to: str = "J",
) -> float:
    """Spark energy stored in a capacitor: E = ½·C·V².

    >>> round(esd_energy(500, "pF", 5, "kV", to="mJ"), 12)
    6.25
    """
    c = _require(capacitance_unit, CAPACITANCE).to_base(capacitance)
    v = _require(voltage_unit, VOLTAGE).to_base(voltage)
    if c < 0:
        raise ValueError("Capacitance must be non-negative")
    return _require(to, ENERGY).from_base(0.5 * c * v * v)


def esd_voltage(
    energy: float,
    energy_unit: str,
    capacitance: float,
    capacitance_unit: str,
    to: str = "kV",
) -> float:
    """Charging voltage that stores a given energy: V = √(2E / C)."""
    e = _require(energy_unit, ENERGY).to_base(energy)
    c = _require(capacitance_unit, CAPACITANCE).to_base(capacitance)
    if c <= 0:
        raise ValueError("Capacitance must be positive")
    if e < 0:
        raise ValueError("Energy must be non-negative")
    return _require(to, VOLTAGE).from_base(math.sqrt(2 * e / c))
