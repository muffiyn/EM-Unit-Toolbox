"""Single-quantity conversions and conversions that combine two measurements."""

from __future__ import annotations

from .units import (
    BASE_UNITS,
    ENERGY,
    MASS,
    MOLAR_ENERGY,
    SPECIFIC_ENERGY,
    UNITS,
    Unit,
)


class UnitError(ValueError):
    """Raised for unknown units or conversions between incompatible dimensions."""


def _normalize(symbol: str) -> str:
    s = " ".join(symbol.strip().split())
    s = s.replace("**", "^").replace("⋅", "·")
    # Treat "J / g" the same as "J/g".
    s = s.replace(" / ", "/").replace(" /", "/").replace("/ ", "/")
    return s


def _lowercase_index() -> dict[str, set[Unit]]:
    index: dict[str, set[Unit]] = {}
    for key, unit in UNITS.items():
        index.setdefault(key.lower(), set()).add(unit)
    return index


_LOWER_INDEX = _lowercase_index()


def get_unit(symbol: str | Unit) -> Unit:
    """Look up a unit by symbol, name or alias.

    Lookup is case-sensitive first (so ``mJ`` and ``MJ`` stay distinct). If
    that fails, a case-insensitive match is accepted only when it is
    unambiguous.
    """
    if isinstance(symbol, Unit):
        return symbol
    if not isinstance(symbol, str):
        raise TypeError(f"Unit must be a string, got {type(symbol).__name__}")
    key = _normalize(symbol)
    if key in UNITS:
        return UNITS[key]
    candidates = _LOWER_INDEX.get(key.lower(), set())
    if len(candidates) == 1:
        return next(iter(candidates))
    if len(candidates) > 1:
        options = ", ".join(sorted(u.symbol for u in candidates))
        raise UnitError(f"Ambiguous unit {symbol!r}; did you mean one of: {options}?")
    raise UnitError(f"Unknown unit {symbol!r}. Use list_units() to see supported units.")


def dimension_of(symbol: str | Unit) -> str:
    """Return the dimension (e.g. ``"energy"``) of a unit."""
    return get_unit(symbol).dimension


def convert(value: float, from_unit: str | Unit, to_unit: str | Unit) -> float:
    """Convert ``value`` from one unit to another of the same dimension.

    >>> convert(1, "cal/g", "J/g")
    4.184
    >>> convert(1e7, "erg", "J")
    1.0
    """
    src, dst = get_unit(from_unit), get_unit(to_unit)
    if src.dimension != dst.dimension:
        raise UnitError(
            f"Cannot convert {src.symbol} ({src.dimension}) to {dst.symbol} ({dst.dimension})"
        )
    return dst.from_base(src.to_base(value))


def to_si(value: float, unit: str | Unit) -> tuple[float, str]:
    """Convert to the SI base unit of the unit's dimension; returns ``(value, symbol)``."""
    u = get_unit(unit)
    return u.to_base(value), BASE_UNITS[u.dimension]


def list_units(dimension: str | None = None) -> dict[str, list[str]]:
    """Return canonical unit symbols grouped by dimension.

    Pass ``dimension`` (e.g. ``"energy"``) to restrict the result.
    """
    grouped: dict[str, list[str]] = {}
    seen: set[str] = set()
    for unit in UNITS.values():
        if unit.symbol in seen:
            continue
        seen.add(unit.symbol)
        grouped.setdefault(unit.dimension, []).append(unit.symbol)
    if dimension is not None:
        if dimension not in grouped:
            raise UnitError(f"Unknown dimension {dimension!r}; choose from {sorted(grouped)}")
        return {dimension: grouped[dimension]}
    return grouped


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
) -> float:
    """Convert a molar energy (e.g. kJ/mol) to a specific energy.

    ``molar_mass`` is in g/mol.

    >>> round(molar_to_specific(-67.0, "kJ/mol", 227.13, to="cal/g"), 2)  # TNT ΔHf
    -70.5
    """
    if molar_mass <= 0:
        raise ValueError("Molar mass must be positive")
    j_per_mol = _require(molar_unit, MOLAR_ENERGY).to_base(value)
    j_per_kg = j_per_mol / (molar_mass * 1e-3)
    return _require(to, SPECIFIC_ENERGY).from_base(j_per_kg)


def specific_to_molar(
    value: float,
    specific_unit: str,
    molar_mass: float,
    to: str = "kJ/mol",
) -> float:
    """Convert a specific energy (e.g. cal/g) to a molar energy. ``molar_mass`` in g/mol."""
    if molar_mass <= 0:
        raise ValueError("Molar mass must be positive")
    j_per_kg = _require(specific_unit, SPECIFIC_ENERGY).to_base(value)
    j_per_mol = j_per_kg * molar_mass * 1e-3
    return _require(to, MOLAR_ENERGY).from_base(j_per_mol)
