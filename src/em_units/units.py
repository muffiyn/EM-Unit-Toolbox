"""Unit registry for quantities common in energetic-materials work.

Every unit belongs to exactly one *dimension* (energy, specific energy, mass, ...)
and carries a multiplicative factor that converts a value in that unit to the
dimension's SI base unit. Conversions are only allowed within a dimension.

Calorie convention
------------------
``cal`` is the *thermochemical* calorie (exactly 4.184 J), which is the
convention used for heats of formation, explosion and combustion in the
energetic-materials literature. The International Steam Table calorie
(4.1868 J) is available as ``cal_IT``.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Exact physical constants -------------------------------------------------

STANDARD_GRAVITY = 9.80665  # m/s^2, exact by definition (CGPM 1901)
CAL_TH = 4.184  # J, thermochemical calorie (exact)
CAL_IT = 4.1868  # J, International Table calorie (exact)
ERG = 1e-7  # J
ELECTRON_VOLT = 1.602176634e-19  # J, exact since the 2019 SI redefinition
AVOGADRO = 6.02214076e23  # 1/mol, exact
POUND = 0.45359237  # kg, exact
INCH = 0.0254  # m, exact
FOOT = 0.3048  # m, exact
BTU_IT = 1055.05585262  # J, International Table BTU
TNT_EQUIVALENT_PER_GRAM = 4184.0  # J/g, conventional TNT equivalence (1 kcal/g)
POUND_FORCE = POUND * STANDARD_GRAVITY  # N

# --- Dimensions ---------------------------------------------------------------

ENERGY = "energy"
SPECIFIC_ENERGY = "specific energy"
MOLAR_ENERGY = "molar energy"
MASS = "mass"
LENGTH = "length"
PRESSURE = "pressure"
VELOCITY = "velocity"
DENSITY = "density"
ACCELERATION = "acceleration"

BASE_UNITS = {
    ENERGY: "J",
    SPECIFIC_ENERGY: "J/kg",
    MOLAR_ENERGY: "J/mol",
    MASS: "kg",
    LENGTH: "m",
    PRESSURE: "Pa",
    VELOCITY: "m/s",
    DENSITY: "kg/m^3",
    ACCELERATION: "m/s^2",
}


@dataclass(frozen=True)
class Unit:
    """A unit of measure: its canonical symbol, dimension and SI factor."""

    symbol: str
    dimension: str
    factor: float  # value_in_base = value_in_unit * factor
    name: str = ""

    def to_base(self, value: float) -> float:
        return value * self.factor

    def from_base(self, value: float) -> float:
        return value / self.factor


# Each entry: (canonical symbol, dimension, factor to SI base, name, aliases)
_DEFINITIONS: list[tuple[str, str, float, str, tuple[str, ...]]] = [
    # Energy ------------------------------------------------------------------
    ("J", ENERGY, 1.0, "joule", ("joule", "joules", "N*m", "N·m", "Nm", "N m")),
    ("mJ", ENERGY, 1e-3, "millijoule", ("millijoule", "millijoules")),
    ("kJ", ENERGY, 1e3, "kilojoule", ("kilojoule", "kilojoules")),
    ("MJ", ENERGY, 1e6, "megajoule", ("megajoule", "megajoules")),
    ("GJ", ENERGY, 1e9, "gigajoule", ("gigajoule", "gigajoules")),
    ("erg", ENERGY, ERG, "erg", ("ergs",)),
    ("cal", ENERGY, CAL_TH, "thermochemical calorie", ("calorie", "calories", "cal_th")),
    ("kcal", ENERGY, 1e3 * CAL_TH, "thermochemical kilocalorie", ("kilocalorie", "kilocalories", "Cal", "kcal_th")),
    ("cal_IT", ENERGY, CAL_IT, "International Table calorie", ()),
    ("kcal_IT", ENERGY, 1e3 * CAL_IT, "International Table kilocalorie", ()),
    ("eV", ENERGY, ELECTRON_VOLT, "electronvolt", ("electronvolt", "electronvolts")),
    ("Wh", ENERGY, 3600.0, "watt-hour", ("watt-hour", "watt hour")),
    ("kWh", ENERGY, 3.6e6, "kilowatt-hour", ("kilowatt-hour", "kilowatt hour")),
    ("BTU", ENERGY, BTU_IT, "British thermal unit", ("Btu", "btu")),
    ("ft*lbf", ENERGY, FOOT * POUND_FORCE, "foot-pound force", ("ft·lbf", "ft-lbf", "ft lbf", "ft-lb", "ft*lb", "foot-pound")),
    ("in*lbf", ENERGY, INCH * POUND_FORCE, "inch-pound force", ("in·lbf", "in-lbf", "in lbf", "in-lb", "in*lb")),
    # Drop-weight impact sensitivity is often reported in kilogram-force metres.
    ("kgf*m", ENERGY, STANDARD_GRAVITY, "kilogram-force metre", ("kgf·m", "kgf-m", "kg*m", "kg·m", "kg-m", "kpm")),
    ("kgf*cm", ENERGY, STANDARD_GRAVITY / 100, "kilogram-force centimetre", ("kgf·cm", "kgf-cm", "kg*cm", "kg·cm", "kg-cm")),
    ("g_TNT", ENERGY, TNT_EQUIVALENT_PER_GRAM, "gram of TNT equivalent", ("g TNT", "gTNT")),
    ("kg_TNT", ENERGY, 1e3 * TNT_EQUIVALENT_PER_GRAM, "kilogram of TNT equivalent", ("kg TNT", "kgTNT")),
    ("t_TNT", ENERGY, 1e6 * TNT_EQUIVALENT_PER_GRAM, "tonne of TNT equivalent", ("t TNT", "tTNT", "ton TNT")),
    # Specific energy (energy per mass) ---------------------------------------
    ("J/kg", SPECIFIC_ENERGY, 1.0, "joule per kilogram", ()),
    ("J/g", SPECIFIC_ENERGY, 1e3, "joule per gram", ()),
    ("kJ/kg", SPECIFIC_ENERGY, 1e3, "kilojoule per kilogram", ()),
    ("kJ/g", SPECIFIC_ENERGY, 1e6, "kilojoule per gram", ()),
    ("MJ/kg", SPECIFIC_ENERGY, 1e6, "megajoule per kilogram", ()),
    ("cal/g", SPECIFIC_ENERGY, CAL_TH * 1e3, "calorie per gram", ()),
    ("cal/kg", SPECIFIC_ENERGY, CAL_TH, "calorie per kilogram", ()),
    ("kcal/kg", SPECIFIC_ENERGY, CAL_TH * 1e3, "kilocalorie per kilogram", ()),
    ("kcal/g", SPECIFIC_ENERGY, CAL_TH * 1e6, "kilocalorie per gram", ()),
    ("cal_IT/g", SPECIFIC_ENERGY, CAL_IT * 1e3, "IT calorie per gram", ()),
    ("erg/g", SPECIFIC_ENERGY, ERG * 1e3, "erg per gram", ("ergs/g",)),
    ("BTU/lb", SPECIFIC_ENERGY, BTU_IT / POUND, "BTU per pound", ("Btu/lb", "btu/lb")),
    # Molar energy (heats of formation, etc.) ---------------------------------
    ("J/mol", MOLAR_ENERGY, 1.0, "joule per mole", ()),
    ("kJ/mol", MOLAR_ENERGY, 1e3, "kilojoule per mole", ()),
    ("cal/mol", MOLAR_ENERGY, CAL_TH, "calorie per mole", ()),
    ("kcal/mol", MOLAR_ENERGY, CAL_TH * 1e3, "kilocalorie per mole", ()),
    ("eV/molecule", MOLAR_ENERGY, ELECTRON_VOLT * AVOGADRO, "electronvolt per molecule", ("eV/particle",)),
    # Mass ---------------------------------------------------------------------
    ("kg", MASS, 1.0, "kilogram", ("kilogram", "kilograms")),
    ("g", MASS, 1e-3, "gram", ("gram", "grams")),
    ("mg", MASS, 1e-6, "milligram", ("milligram", "milligrams")),
    ("t", MASS, 1e3, "tonne", ("tonne", "tonnes", "metric ton")),
    ("lb", MASS, POUND, "pound", ("lbs", "lbm", "pound", "pounds")),
    ("oz", MASS, POUND / 16, "ounce", ("ounce", "ounces")),
    ("gr", MASS, POUND / 7000, "grain", ("grain", "grains")),
    # Length -------------------------------------------------------------------
    ("m", LENGTH, 1.0, "metre", ("meter", "meters", "metre", "metres")),
    ("cm", LENGTH, 1e-2, "centimetre", ("centimeter", "centimeters", "centimetre", "centimetres")),
    ("mm", LENGTH, 1e-3, "millimetre", ("millimeter", "millimeters", "millimetre", "millimetres")),
    ("um", LENGTH, 1e-6, "micrometre", ("µm", "μm", "micron", "microns")),
    ("km", LENGTH, 1e3, "kilometre", ("kilometer", "kilometers", "kilometre", "kilometres")),
    ("in", LENGTH, INCH, "inch", ("inch", "inches")),
    ("ft", LENGTH, FOOT, "foot", ("foot", "feet")),
    # Pressure (detonation / CJ pressure) --------------------------------------
    ("Pa", PRESSURE, 1.0, "pascal", ("pascal", "pascals")),
    ("kPa", PRESSURE, 1e3, "kilopascal", ()),
    ("MPa", PRESSURE, 1e6, "megapascal", ()),
    ("GPa", PRESSURE, 1e9, "gigapascal", ()),
    ("bar", PRESSURE, 1e5, "bar", ("bars",)),
    ("kbar", PRESSURE, 1e8, "kilobar", ("kilobar", "kilobars")),
    ("Mbar", PRESSURE, 1e11, "megabar", ("megabar", "megabars")),
    ("atm", PRESSURE, 101325.0, "standard atmosphere", ()),
    ("psi", PRESSURE, POUND_FORCE / INCH**2, "pound-force per square inch", ()),
    ("dyn/cm^2", PRESSURE, 0.1, "dyne per square centimetre", ("dyn/cm2", "dyne/cm^2", "dyne/cm2", "barye")),
    # Velocity (detonation velocity) -------------------------------------------
    ("m/s", VELOCITY, 1.0, "metre per second", ()),
    ("km/s", VELOCITY, 1e3, "kilometre per second", ()),
    ("mm/us", VELOCITY, 1e3, "millimetre per microsecond", ("mm/µs", "mm/μs")),
    ("cm/us", VELOCITY, 1e4, "centimetre per microsecond", ("cm/µs", "cm/μs")),
    ("ft/s", VELOCITY, FOOT, "foot per second", ("fps",)),
    # Density ------------------------------------------------------------------
    ("kg/m^3", DENSITY, 1.0, "kilogram per cubic metre", ("kg/m3",)),
    ("g/cm^3", DENSITY, 1e3, "gram per cubic centimetre", ("g/cm3", "g/cc", "g/mL", "g/ml")),
    ("lb/in^3", DENSITY, POUND / INCH**3, "pound per cubic inch", ("lb/in3",)),
    ("lb/ft^3", DENSITY, POUND / FOOT**3, "pound per cubic foot", ("lb/ft3",)),
    # Acceleration (for non-standard gravity in potential-energy calculations)
    ("m/s^2", ACCELERATION, 1.0, "metre per second squared", ("m/s2",)),
    ("ft/s^2", ACCELERATION, FOOT, "foot per second squared", ("ft/s2",)),
    ("gn", ACCELERATION, STANDARD_GRAVITY, "standard gravity", ("g0", "g_n")),
]


def _build_registry() -> dict[str, Unit]:
    registry: dict[str, Unit] = {}
    for symbol, dimension, factor, name, aliases in _DEFINITIONS:
        unit = Unit(symbol, dimension, factor, name)
        for key in (symbol, *aliases):
            if key in registry:
                raise ValueError(f"Duplicate unit alias {key!r}")
            registry[key] = unit
    return registry


UNITS: dict[str, Unit] = _build_registry()
