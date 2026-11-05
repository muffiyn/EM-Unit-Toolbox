"""Single-quantity conversions and conversions that combine two measurements."""

from __future__ import annotations

from fractions import Fraction

from .parsing import UnitError, parse_unit
from .units import (
    COMMON_UNITS,
    DIMENSIONS,
    ENERGY,
    MASS,
    MOLAR_ENERGY,
    MOLAR_MASS,
    SPECIFIC_ENERGY,
    Unit,
    si_symbol,
)

def get_unit(symbol: str | Unit) -> Unit:
    """Parse a unit written in any common notation.

    ``"J/g"``, ``"J g-1"``, ``"J·g⁻¹"``, ``"J g^-1"`` and ``"joules per gram"``
    all give the same unit. Symbols are case-sensitive first (so ``mJ`` and
    ``MJ`` stay distinct); a case-insensitive match is accepted only when it is
    unambiguous.

    >>> get_unit("g mol-1") == get_unit("g/mol")
    True
    """
    if isinstance(symbol, Unit):
        return symbol
    return parse_unit(symbol)


def dimension_of(symbol: str | Unit) -> str:
    """Return the dimension (e.g. ``"energy"``) of a unit."""
    return get_unit(symbol).dimension


def convert(value: float, from_unit: str | Unit, to_unit: str | Unit) -> float:
    """Convert ``value`` between two units of the same dimension.

    >>> convert(1, "cal/g", "J/g")
    4.184
    >>> convert(1e7, "erg", "J")
    1.0
    >>> convert(1, "kcal mol-1", "kJ·mol⁻¹")
    4.184
    """
    src, dst = get_unit(from_unit), get_unit(to_unit)
    if src.dims != dst.dims:
        raise UnitError(
            f"Cannot convert {src.symbol} ({src.dimension}) to {dst.symbol} ({dst.dimension})"
        )
    if src.exact is not None and dst.exact is not None:
        ratio = src.exact / dst.exact
        try:
            return float(Fraction(value) * ratio)  # one rounding: 1500 cal/g -> 6.276 MJ/kg
        except (TypeError, ValueError, OverflowError):  # nan, inf, non-float types
            return value * float(ratio)
    return dst.from_base(src.to_base(value))


def to_si(value: float, unit: str | Unit) -> tuple[float, str]:
    """Convert to SI; returns ``(value, si_symbol)``, e.g. ``(8368.0, "J")``."""
    u = get_unit(unit)
    return u.to_base(value), si_symbol(u.dims)


def list_units(dimension: str | None = None) -> dict[str, list[str]]:
    """Return representative unit symbols grouped by dimension.

    These are examples, not a limit: any prefix, product, quotient or power of
    supported units is accepted. Pass ``dimension`` (e.g. ``"energy"``) to
    restrict the result.
    """
    if dimension is not None:
        if dimension not in COMMON_UNITS:
            known = sorted(set(COMMON_UNITS) | set(DIMENSIONS))
            raise UnitError(f"Unknown dimension {dimension!r}; choose from {known}")
        return {dimension: list(COMMON_UNITS[dimension])}
    return {dim: list(symbols) for dim, symbols in COMMON_UNITS.items()}


def _require(unit: str | Unit, dimension: str) -> Unit:
    u = get_unit(unit)
    if u.dimension != dimension:
        raise UnitError(f"Expected a {dimension} unit, got {u.symbol} ({u.dimension})")
    return u


def specific_to_total(
    specific_value: float,
    specific_unit: str,
    mass: float,
    mass_unit: str,
    to: str = "J",
) -> float:
    """Total energy released by ``mass`` of material with a given specific energy.

    >>> specific_to_total(1000, "cal/g", 10, "g", to="kJ")
    41.84
    """
    se = _require(specific_unit, SPECIFIC_ENERGY).to_base(specific_value)  # J/kg
    m = _require(mass_unit, MASS).to_base(mass)  # kg
    return _require(to, ENERGY).from_base(se * m)


def total_to_specific(
    energy: float,
    energy_unit: str,
    mass: float,
    mass_unit: str,
    to: str = "J/g",
) -> float:
    """Specific energy from a total energy and the mass that produced it."""
    m = _require(mass_unit, MASS).to_base(mass)
    if m <= 0:
        raise ValueError("Mass must be positive")
    e = _require(energy_unit, ENERGY).to_base(energy)
    return _require(to, SPECIFIC_ENERGY).from_base(e / m)


def molar_to_specific(
    value: float,
    molar_unit: str,
    molar_mass: float,
    to: str = "J/g",
    molar_mass_unit: str = "g/mol",
) -> float:
    """Convert a molar energy (e.g. kJ/mol) to a specific energy.

    ``molar_mass`` is in ``molar_mass_unit`` (default g/mol).

    >>> round(molar_to_specific(-67.0, "kJ mol-1", 227.13, to="cal g-1"), 2)  # TNT ΔHf
    -70.5
    """
    kg_per_mol = _molar_mass_si(molar_mass, molar_mass_unit)
    j_per_mol = _require(molar_unit, MOLAR_ENERGY).to_base(value)
    return _require(to, SPECIFIC_ENERGY).from_base(j_per_mol / kg_per_mol)


def specific_to_molar(
    value: float,
    specific_unit: str,
    molar_mass: float,
    to: str = "kJ/mol",
    molar_mass_unit: str = "g/mol",
) -> float:
    """Convert a specific energy (e.g. cal/g) to a molar energy.

    ``molar_mass`` is in ``molar_mass_unit`` (default g/mol).
    """
    kg_per_mol = _molar_mass_si(molar_mass, molar_mass_unit)
    j_per_kg = _require(specific_unit, SPECIFIC_ENERGY).to_base(value)
    return _require(to, MOLAR_ENERGY).from_base(j_per_kg * kg_per_mol)


def _molar_mass_si(molar_mass: float, unit: str) -> float:
    kg_per_mol = _require(unit, MOLAR_MASS).to_base(molar_mass)
    if kg_per_mol <= 0:
        raise ValueError("Molar mass must be positive")
    return kg_per_mol
