"""Gravitational potential energy (E = m·g·h) for drop-weight impact testing.

Drop-weight sensitivity results (e.g. H50, BAM fallhammer) are usually
reported as a drop height for a given striker mass. These helpers turn a mass
and a height into an energy and back again.
"""

from __future__ import annotations

from .converter import UnitError, get_unit
from .units import ACCELERATION, ENERGY, LENGTH, MASS, STANDARD_GRAVITY


def _base(value: float, unit: str, dimension: str) -> float:
    u = get_unit(unit)
    if u.dimension != dimension:
        raise UnitError(f"Expected a {dimension} unit, got {u.symbol} ({u.dimension})")
    return u.to_base(value)


def _gravity(g: float, g_unit: str) -> float:
    g_si = _base(g, g_unit, ACCELERATION)
    if g_si <= 0:
        raise ValueError("Gravitational acceleration must be positive")
    return g_si


def potential_energy(
    mass: float,
    mass_unit: str,
    height: float,
    height_unit: str,
    to: str = "J",
    g: float = STANDARD_GRAVITY,
    g_unit: str = "m/s^2",
) -> float:
    """Energy of a mass dropped from a height: E = m·g·h.

    >>> potential_energy(2, "kg", 50, "cm")  # 2 kg drop weight from 50 cm
    9.80665
    >>> round(potential_energy(5, "kg", 20, "cm", to="kgf*m"), 6)
    1.0
    """
    m = _base(mass, mass_unit, MASS)
    h = _base(height, height_unit, LENGTH)
    if m < 0:
        raise ValueError("Mass must be non-negative")
    energy_j = m * _gravity(g, g_unit) * h
    return _base_to(energy_j, to, ENERGY)


def drop_height(
    energy: float,
    energy_unit: str,
    mass: float,
    mass_unit: str,
    to: str = "cm",
    g: float = STANDARD_GRAVITY,
    g_unit: str = "m/s^2",
) -> float:
    """Height a mass must fall from to deliver a given energy: h = E / (m·g)."""
    m = _base(mass, mass_unit, MASS)
    if m <= 0:
        raise ValueError("Mass must be positive")
    e = _base(energy, energy_unit, ENERGY)
    return _base_to(e / (m * _gravity(g, g_unit)), to, LENGTH)


def drop_mass(
    energy: float,
    energy_unit: str,
    height: float,
    height_unit: str,
    to: str = "kg",
    g: float = STANDARD_GRAVITY,
    g_unit: str = "m/s^2",
) -> float:
    """Mass that delivers a given energy when dropped from a height: m = E / (g·h)."""
    h = _base(height, height_unit, LENGTH)
    if h <= 0:
        raise ValueError("Height must be positive")
    e = _base(energy, energy_unit, ENERGY)
    return _base_to(e / (_gravity(g, g_unit) * h), to, MASS)


def _base_to(value_si: float, unit: str, dimension: str) -> float:
    u = get_unit(unit)
    if u.dimension != dimension:
        raise UnitError(f"Expected a {dimension} unit, got {u.symbol} ({u.dimension})")
    return u.from_base(value_si)
