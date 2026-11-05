"""Unit definitions for quantities common in energetic-materials work.

Units are built from *atoms* (g, m, s, mol, J, cal, erg, Pa, lb, ...). Each atom
has a factor to SI and a dimension vector over (mass, length, time, amount,
temperature). Compound units such as ``kJ kg-1`` or ``J/(mol·K)`` are parsed
into products of atoms (see :mod:`em_units.parsing`), so any combination is
supported and two units are convertible whenever their dimension vectors match.

Calorie convention
------------------
``cal`` is the *thermochemical* calorie (exactly 4.184 J), which is the
convention used for heats of formation, explosion and combustion in the
energetic-materials literature. The International Table calorie (4.1868 J) is
available as ``cal_IT``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from fractions import Fraction

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
ATMOSPHERE = 101325.0  # Pa

# --- Dimensions ---------------------------------------------------------------

Dims = tuple  # (mass, length, time, amount, temperature, current, angle) exponents
DIM_SYMBOLS = ("M", "L", "T", "N", "Θ", "I", "∠")
SI_SYMBOLS = ("kg", "m", "s", "mol", "K", "A", "rad")
NDIMS = len(DIM_SYMBOLS)


def _d(M: int = 0, L: int = 0, T: int = 0, N: int = 0, K: int = 0, I: int = 0, A: int = 0) -> Dims:  # noqa: E741
    return (M, L, T, N, K, I, A)


ENERGY = "energy"
SPECIFIC_ENERGY = "specific energy"
MOLAR_ENERGY = "molar energy"
MOLAR_MASS = "molar mass"
MASS = "mass"
LENGTH = "length"
TIME = "time"
AMOUNT = "amount of substance"
TEMPERATURE = "temperature"
PRESSURE = "pressure"
VELOCITY = "velocity"
DENSITY = "density"
ACCELERATION = "acceleration"
FORCE = "force"
POWER = "power"
AREA = "area"
VOLUME = "volume"
SPECIFIC_VOLUME = "specific volume"
MOLAR_VOLUME = "molar volume"
HEAT_CAPACITY = "heat capacity"
SPECIFIC_HEAT_CAPACITY = "specific heat capacity"
MOLAR_HEAT_CAPACITY = "molar heat capacity"
FREQUENCY = "frequency"
DIMENSIONLESS = "dimensionless"
ANGLE = "angle"
CURRENT = "electric current"
CHARGE = "electric charge"
VOLTAGE = "voltage"
RESISTANCE = "electrical resistance"
CAPACITANCE = "capacitance"
DIPOLE_MOMENT = "electric dipole moment"
THERMAL_CONDUCTIVITY = "thermal conductivity"
HEATING_RATE = "heating rate"
THERMAL_EXPANSION = "thermal expansion coefficient"
SPECIFIC_SURFACE_AREA = "specific surface area"
AREAL_DENSITY = "areal density"
DIFFUSIVITY = "diffusivity"
VOLUME_FLOW = "volume flow rate"

# Named dimension -> (dimension vector, SI symbol). Energy density (J/m^3)
# shares the pressure vector, so it is reported (and converts) as pressure.
DIMENSIONS: dict[str, tuple[Dims, str]] = {
    ENERGY: (_d(M=1, L=2, T=-2), "J"),
    SPECIFIC_ENERGY: (_d(L=2, T=-2), "J/kg"),
    MOLAR_ENERGY: (_d(M=1, L=2, T=-2, N=-1), "J/mol"),
    MOLAR_MASS: (_d(M=1, N=-1), "kg/mol"),
    MASS: (_d(M=1), "kg"),
    LENGTH: (_d(L=1), "m"),
    TIME: (_d(T=1), "s"),
    AMOUNT: (_d(N=1), "mol"),
    TEMPERATURE: (_d(K=1), "K"),
    PRESSURE: (_d(M=1, L=-1, T=-2), "Pa"),
    VELOCITY: (_d(L=1, T=-1), "m/s"),
    DENSITY: (_d(M=1, L=-3), "kg/m^3"),
    ACCELERATION: (_d(L=1, T=-2), "m/s^2"),
    FORCE: (_d(M=1, L=1, T=-2), "N"),
    POWER: (_d(M=1, L=2, T=-3), "W"),
    AREA: (_d(L=2), "m^2"),
    VOLUME: (_d(L=3), "m^3"),
    SPECIFIC_VOLUME: (_d(M=-1, L=3), "m^3/kg"),
    MOLAR_VOLUME: (_d(L=3, N=-1), "m^3/mol"),
    HEAT_CAPACITY: (_d(M=1, L=2, T=-2, K=-1), "J/K"),
    SPECIFIC_HEAT_CAPACITY: (_d(L=2, T=-2, K=-1), "J/(kg·K)"),
    MOLAR_HEAT_CAPACITY: (_d(M=1, L=2, T=-2, N=-1, K=-1), "J/(mol·K)"),
    FREQUENCY: (_d(T=-1), "1/s"),
    DIMENSIONLESS: (_d(), "1"),
    ANGLE: (_d(A=1), "rad"),
    CURRENT: (_d(I=1), "A"),
    CHARGE: (_d(T=1, I=1), "C"),
    VOLTAGE: (_d(M=1, L=2, T=-3, I=-1), "V"),
    RESISTANCE: (_d(M=1, L=2, T=-3, I=-2), "Ω"),
    CAPACITANCE: (_d(M=-1, L=-2, T=4, I=2), "F"),
    DIPOLE_MOMENT: (_d(L=1, T=1, I=1), "C·m"),
    THERMAL_CONDUCTIVITY: (_d(M=1, L=1, T=-3, K=-1), "W/(m·K)"),
    HEATING_RATE: (_d(T=-1, K=1), "K/s"),
    THERMAL_EXPANSION: (_d(K=-1), "1/K"),
    SPECIFIC_SURFACE_AREA: (_d(M=-1, L=2), "m^2/kg"),
    AREAL_DENSITY: (_d(M=1, L=-2), "kg/m^2"),
    DIFFUSIVITY: (_d(L=2, T=-1), "m^2/s"),
    VOLUME_FLOW: (_d(L=3, T=-1), "m^3/s"),
}
_NAME_BY_DIMS = {dims: name for name, (dims, _) in DIMENSIONS.items()}

# Kept for backwards compatibility: dimension name -> SI symbol.
BASE_UNITS = {name: symbol for name, (_, symbol) in DIMENSIONS.items()}


def dimension_name(dims: Dims) -> str:
    """Name of a dimension vector, e.g. ``"energy"``, or a formula like ``"M L^-1"``."""
    if dims in _NAME_BY_DIMS:
        return _NAME_BY_DIMS[dims]
    return " ".join(
        sym if p == 1 else f"{sym}^{p}" for sym, p in zip(DIM_SYMBOLS, dims) if p
    )


def si_symbol(dims: Dims) -> str:
    """SI unit symbol for a dimension vector, e.g. ``"J"`` or ``"kg·m^-1"``."""
    name = _NAME_BY_DIMS.get(dims)
    if name is not None:
        return DIMENSIONS[name][1]
    return "·".join(
        sym if p == 1 else f"{sym}^{p}" for sym, p in zip(SI_SYMBOLS, dims) if p
    )


@dataclass(frozen=True, eq=False)
class Unit:
    """A (possibly compound) unit: its symbol, dimension and factor to SI.

    ``offset`` is non-zero only for absolute temperature scales (°C, °F):
    value_in_SI = value_in_unit * factor + offset. ``qualifier`` holds a
    substance or condition label such as ``"TNT"`` in ``"% TNT"`` or ``"LA"``
    in ``"g LA"``.
    """

    symbol: str
    dimension: str
    factor: float  # value_in_SI = value_in_unit * factor + offset
    dims: Dims = ()
    exact: Fraction | None = field(default=None, repr=False)  # exact factor, when known
    offset: Fraction = field(default=Fraction(0), repr=False)
    qualifier: str = ""

    def to_base(self, value: float) -> float:
        return value * self.factor + float(self.offset)

    def from_base(self, value: float) -> float:
        return (value - float(self.offset)) / self.factor

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Unit):
            return NotImplemented
        return (
            self.dims == other.dims
            and math.isclose(self.factor, other.factor, rel_tol=1e-12)
            and self.offset == other.offset
            and self.qualifier == other.qualifier
        )

    def __hash__(self) -> int:
        return hash(self.dims)


# --- Atoms ----------------------------------------------------------------------

# symbol -> (factor to SI, dims, accepts SI prefixes)
ATOMS: dict[str, tuple[float, Dims, bool]] = {}
# lowercase full name (singular) -> atom symbol; plurals are handled by the parser
NAMES: dict[str, str] = {}


def _atom(symbol: str, factor: float, dims: Dims, prefixable: bool = False, names: tuple[str, ...] = (), aliases: tuple[str, ...] = ()) -> None:
    for key in (symbol, *aliases):
        if key in ATOMS:
            raise ValueError(f"Duplicate atom {key!r}")
        ATOMS[key] = (factor, dims, prefixable)
    for name in names:
        if name in NAMES:
            raise ValueError(f"Duplicate unit name {name!r}")
        NAMES[name] = symbol


_E = DIMENSIONS[ENERGY][0]

# Mass
_atom("g", 1e-3, _d(M=1), True, ("gram", "gramme"))
_atom("t", 1e3, _d(M=1), True, ("tonne",))
_atom("lb", POUND, _d(M=1), False, ("pound",), ("lbm", "lbs"))
_atom("oz", POUND / 16, _d(M=1), False, ("ounce",))
_atom("gr", POUND / 7000, _d(M=1), False, ("grain",))
# Length
_atom("m", 1.0, _d(L=1), True, ("metre", "meter"))
_atom("in", INCH, _d(L=1), False, ("inch",))
_atom("ft", FOOT, _d(L=1), False, ("foot", "feet"))
_atom("yd", 3 * FOOT, _d(L=1), False, ("yard",))
_atom("mil", INCH / 1000, _d(L=1), False, ("mil", "thou"))
_atom("micron", 1e-6, _d(L=1), False, ("micron",))
_atom("Å", 1e-10, _d(L=1), False, ("angstrom", "ångström"))
# Time
_atom("s", 1.0, _d(T=1), True, ("second",), ("sec", "secs"))
_atom("min", 60.0, _d(T=1), False, ("minute",), ("mins",))
_atom("h", 3600.0, _d(T=1), False, ("hour",), ("hr", "hrs"))
_atom("d", 86400.0, _d(T=1), False, ("day",))
_atom("wk", 7 * 86400.0, _d(T=1), False, ("week",))
_atom("yr", 365.25 * 86400.0, _d(T=1), False, ("year",), ("yrs",))  # Julian year
# Amount of substance
_atom("mol", 1.0, _d(N=1), True, ("mole",), ("mols",))
_atom("molecule", float(1 / Fraction("6.02214076e23")), _d(N=1), False, ("molecule", "particle", "atom"))
# Temperature. On their own, °C and °F are absolute scales with an offset
# (25 °C -> 298.15 K); inside compound units such as J/(g·°C) or °C/min they
# are temperature intervals.
_atom("K", 1.0, _d(K=1), True, ("kelvin",))
_atom("degC", 1.0, _d(K=1), False, ("celsius", "degree_celsius"), ("deg_C",))
_atom("degF", 5 / 9, _d(K=1), False, ("fahrenheit", "degree_fahrenheit"), ("deg_F",))
_atom("degR", 5 / 9, _d(K=1), False, ("rankine", "degree_rankine"), ("deg_R",))
# Plane angle
_atom("rad", 1.0, _d(A=1), True, ("radian",))
_atom("deg", math.pi / 180, _d(A=1), False, ("degree",))
# Dimensionless ratios
_atom("%", 1e-2, _d(), False, ("percent",), ("pct",))
_atom("‰", 1e-3, _d(), False, ("permille",))
_atom("ppm", 1e-6, _d())
_atom("ppb", 1e-9, _d())
# Electrical (ESD sensitivity, dipole moments)
_atom("A", 1.0, _d(I=1), True, ("ampere",), ("amp", "amps"))
_atom("C", 1.0, _d(T=1, I=1), True, ("coulomb",))
_atom("V", 1.0, _d(M=1, L=2, T=-3, I=-1), True, ("volt",))
_atom("Ω", 1.0, _d(M=1, L=2, T=-3, I=-2), True, ("ohm",), ("ohm", "ohms"))
_atom("F", 1.0, _d(M=-1, L=-2, T=4, I=2), True, ("farad",))
_atom("D", float(Fraction("1e-21") / 299792458), _d(L=1, T=1, I=1), False, ("debye",))
# Energy
_atom("J", 1.0, _E, True, ("joule",))
_atom("erg", ERG, _E, True, ("erg",))
_atom("cal", CAL_TH, _E, True, ("calorie",), ("cal_th",))
_atom("Cal", 1e3 * CAL_TH, _E, False, (), ("kcal_th",))  # dietary "Calorie" = kcal
_atom("cal_IT", CAL_IT, _E, True)
_atom("eV", ELECTRON_VOLT, _E, True, ("electronvolt",))
_atom("Wh", 3600.0, _E, True)
_atom("BTU", BTU_IT, _E, False, (), ("Btu", "btu"))
_atom("g_TNT", TNT_EQUIVALENT_PER_GRAM, _E, True, ("gram_tnt",))
_atom("t_TNT", 1e6 * TNT_EQUIVALENT_PER_GRAM, _E, True, ("ton_tnt", "tonne_tnt"))
# Force
_atom("N", 1.0, _d(M=1, L=1, T=-2), True, ("newton",))
_atom("dyn", 1e-5, _d(M=1, L=1, T=-2), False, ("dyne",))
_atom("lbf", POUND_FORCE, _d(M=1, L=1, T=-2), False, ("pound_force",))
_atom("kgf", STANDARD_GRAVITY, _d(M=1, L=1, T=-2), False, ("kilogram_force",), ("kp",))
# Pressure
_atom("Pa", 1.0, _d(M=1, L=-1, T=-2), True, ("pascal",))
_atom("bar", 1e5, _d(M=1, L=-1, T=-2), True, ("bar",))
_atom("atm", ATMOSPHERE, _d(M=1, L=-1, T=-2), False, ("atmosphere",))
_atom("psi", POUND_FORCE / INCH**2, _d(M=1, L=-1, T=-2), True)
_atom("ksi", 1e3 * POUND_FORCE / INCH**2, _d(M=1, L=-1, T=-2))
_atom("Torr", ATMOSPHERE / 760, _d(M=1, L=-1, T=-2), False, ("torr",))
_atom("mmHg", 133.322387415, _d(M=1, L=-1, T=-2))
_atom("barye", 0.1, _d(M=1, L=-1, T=-2), False, ("barye",))
# Power
_atom("W", 1.0, _d(M=1, L=2, T=-3), True, ("watt",))
# Volume
_atom("L", 1e-3, _d(L=3), True, ("litre", "liter"), ("l",))
_atom("cc", 1e-6, _d(L=3))
# Acceleration
_atom("gn", STANDARD_GRAVITY, _d(L=1, T=-2), False, ("standard_gravity",), ("g_n",))

# Absolute-scale offsets, in kelvin, applied when the unit stands alone.
OFFSETS: dict[str, Fraction] = {
    "degC": Fraction("273.15"),
    "deg_C": Fraction("273.15"),
    "degF": Fraction("459.67") * Fraction(5, 9),
    "deg_F": Fraction("459.67") * Fraction(5, 9),
}

# SI prefixes. "da" must be tried before "d".
PREFIXES: dict[str, float] = {
    "da": 1e1, "Y": 1e24, "Z": 1e21, "E": 1e18, "P": 1e15, "T": 1e12, "G": 1e9,
    "M": 1e6, "k": 1e3, "h": 1e2, "d": 1e-1, "c": 1e-2, "m": 1e-3, "u": 1e-6,
    "µ": 1e-6, "n": 1e-9, "p": 1e-12, "f": 1e-15, "a": 1e-18,
}
NAME_PREFIXES: dict[str, float] = {
    "tera": 1e12, "giga": 1e9, "mega": 1e6, "kilo": 1e3, "hecto": 1e2, "deci": 1e-1,
    "centi": 1e-2, "milli": 1e-3, "micro": 1e-6, "nano": 1e-9, "pico": 1e-12,
}

# Whole-expression aliases, written in normalized form (see parsing.normalize).
# These cover spellings whose literal reading would be dimensionally wrong.
ALIASES: dict[str, str] = {
    # Drop-weight impact energies are reported as kg·m meaning kilogram-force metres.
    "kg·m": "kgf·m",
    "kg·cm": "kgf·cm",
    "kpm": "kgf·m",
    "Nm": "N·m",
    # "ft-lb" conventionally means foot-pound force.
    "ft·lb": "ft·lbf",
    "in·lb": "in·lbf",
    "foot·pound": "ft·lbf",
    "inch·pound": "in·lbf",
    # Loading/consolidation pressures are reported as kg/cm² meaning kgf/cm².
    "kg/cm2": "kgf/cm^2",
    "kg/cm^2": "kgf/cm^2",
    "kg·cm-2": "kgf·cm^-2",
    "kg·cm^-2": "kgf·cm^-2",
    "kg/mm2": "kgf/mm^2",
    "kg/mm^2": "kgf/mm^2",
    "g0": "gn",
    "fps": "ft/s",
}

# Words that label *what* is measured rather than a unit: "% TNT", "g LA",
# "g/100 g solvent". Matched case-insensitively against trailing words; any
# trailing word that is not a unit at all is also treated as a label.
SUBSTANCE_LABELS: frozenset[str] = frozenset(
    w.lower()
    for w in (
        # explosives and energetic materials
        "TNT", "RDX", "HMX", "PETN", "CL-20", "HNIW", "TATB", "HNS", "NTO", "FOX-7",
        "LLM-105", "TNAZ", "ADN", "AN", "AP", "NC", "NG", "NQ", "PA", "LA", "LS", "MF",
        "DDNP", "TACOT", "DNAN", "TEX", "BTF", "KDNBF", "tetryl", "picric", "azide",
        "styphnate", "fulminate", "HNAB", "DATB", "TATP", "HMTD", "EGDN", "ETN",
        # matrices and conditions
        "solvent", "water", "H2O", "air", "sample", "explosive", "propellant", "charge",
        "salt", "solution", "mixture", "binder", "composition",
    )
)

# Representative units per dimension, for list_units() and documentation.
COMMON_UNITS: dict[str, list[str]] = {
    ENERGY: ["J", "mJ", "kJ", "MJ", "GJ", "erg", "cal", "kcal", "cal_IT", "kcal_IT", "eV",
             "Wh", "kWh", "BTU", "ft·lbf", "in·lbf", "kgf·m", "kgf·cm", "g_TNT", "kg_TNT",
             "t_TNT", "kt_TNT"],
    SPECIFIC_ENERGY: ["J/kg", "J/g", "kJ/kg", "kJ/g", "MJ/kg", "cal/g", "cal/kg", "kcal/kg",
                      "kcal/g", "erg/g", "BTU/lb"],
    MOLAR_ENERGY: ["J/mol", "kJ/mol", "cal/mol", "kcal/mol", "eV/molecule"],
    MOLAR_MASS: ["g/mol", "kg/mol"],
    MASS: ["kg", "g", "mg", "ug", "t", "lb", "oz", "gr"],
    LENGTH: ["m", "cm", "mm", "um", "nm", "km", "Å", "in", "ft", "yd"],
    TIME: ["s", "ms", "us", "ns", "min", "h"],
    TEMPERATURE: ["K", "degC", "degF", "degR"],
    PRESSURE: ["Pa", "kPa", "MPa", "GPa", "bar", "kbar", "Mbar", "atm", "psi", "ksi", "Torr",
               "mmHg", "dyn/cm^2", "J/cm^3"],
    VELOCITY: ["m/s", "km/s", "mm/us", "cm/us", "ft/s"],
    DENSITY: ["kg/m^3", "g/cm^3", "g/cc", "g/L", "lb/in^3", "lb/ft^3"],
    ACCELERATION: ["m/s^2", "ft/s^2", "gn"],
    FORCE: ["N", "kN", "dyn", "lbf", "kgf"],
    POWER: ["W", "kW", "MW", "BTU/h"],
    VOLUME: ["m^3", "L", "mL", "cm^3", "cc", "in^3", "ft^3"],
    SPECIFIC_VOLUME: ["m^3/kg", "cm^3/g", "L/kg"],
    MOLAR_VOLUME: ["m^3/mol", "cm^3/mol", "L/mol"],
    SPECIFIC_HEAT_CAPACITY: ["J/(kg·K)", "J/(g·K)", "kJ/(kg·K)", "cal/(g·K)"],
    MOLAR_HEAT_CAPACITY: ["J/(mol·K)", "cal/(mol·K)"],
    THERMAL_CONDUCTIVITY: ["W/(m·K)", "W·m^-1·K^-1", "cal/(cm·s·K)"],
    HEATING_RATE: ["K/min", "°C/min", "K/s"],
    THERMAL_EXPANSION: ["1/K", "1/°C", "ppm/K"],
    DIMENSIONLESS: ["1", "%", "‰", "ppm", "ppb", "g/100 g"],
    ANGLE: ["rad", "mrad", "deg"],
    AREAL_DENSITY: ["kg/m^2", "g/cm^2", "mg/cm^2"],
    SPECIFIC_SURFACE_AREA: ["m^2/g", "m^2/kg", "cm^2/g"],
    DIFFUSIVITY: ["m^2/s", "cm^2/s", "mm^2/s"],
    VOLUME_FLOW: ["m^3/s", "L/min", "cc/h"],
    CURRENT: ["A", "mA", "uA"],
    CHARGE: ["C", "mC", "uC", "nC"],
    VOLTAGE: ["V", "mV", "kV"],
    RESISTANCE: ["Ω", "kΩ", "MΩ"],
    CAPACITANCE: ["F", "uF", "nF", "pF"],
    DIPOLE_MOMENT: ["C·m", "D"],
}
