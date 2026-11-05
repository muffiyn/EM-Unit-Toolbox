"""Every common way of writing a unit should parse to the same thing."""

import math

import pytest

from em_units import UnitError, convert, dimension_of, get_unit, list_units


def same(a, b):
    ua, ub = get_unit(a), get_unit(b)
    return ua.dims == ub.dims and math.isclose(ua.factor, ub.factor, rel_tol=1e-12)


@pytest.mark.parametrize(
    "canonical, spellings",
    [
        ("g/mol", ["g mol-1", "g mol^-1", "g·mol⁻¹", "g*mol**-1", "g.mol-1", "g⋅mol^(-1)",
                   "grams per mole", "g / mol", "g/(mol)", "gram/mole"]),
        ("J/g", ["J g-1", "J·g⁻¹", "J g^-1", "joules per gram", "Joules/gram", "J/gram"]),
        ("kJ/mol", ["kJ mol-1", "kJ·mol⁻¹", "kilojoules per mole", "kJ mol^-1", "kJ/mole"]),
        ("cal/g", ["cal g-1", "cal·g⁻¹", "calories per gram", "cal.g-1"]),
        ("kcal/mol", ["kcal mol-1", "kilocalories per mole", "kcal·mol⁻¹"]),
        ("MJ/kg", ["MJ kg-1", "MJ·kg⁻¹", "megajoules per kilogram"]),
        ("erg/g", ["erg g-1", "ergs per gram", "erg·g⁻¹"]),
        ("g/cm^3", ["g cm-3", "g·cm⁻³", "g/cm3", "g/cm³", "g/cc", "g cm^-3", "g/mL", "g ml-1",
                    "grams per cubic centimetre", "g/cubic cm", "kg/L", "g/(cm^3)"]),
        ("kg/m^3", ["kg m-3", "kg·m⁻³", "kg/m3", "kg.m-3", "kilograms per cubic metre", "g/L"]),
        ("m/s", ["m s-1", "m·s⁻¹", "metres per second", "meters/second", "m s^-1"]),
        ("km/s", ["km s-1", "mm/us", "mm µs-1", "mm/μs", "mm·µs⁻¹", "mm us^-1"]),
        ("m/s^2", ["m s-2", "m·s⁻²", "m/s²", "m/s/s", "m/(s s)", "(m/s)/s"]),
        ("J/(g·K)", ["J g-1 K-1", "J·g⁻¹·K⁻¹", "J/g/K", "J/(g K)", "J g^-1 K^-1", "J/g K"]),
        ("J/(mol·K)", ["J mol-1 K-1", "J·mol⁻¹·K⁻¹", "J/mol/K", "J K-1 mol-1"]),
        ("GPa", ["GPa", "gigapascal", "gigapascals", "kJ/cm^3", "kJ cm-3", "10 kbar"]),
        ("kbar", ["kbar", "kilobar", "kilobars", "1000 bar", "100 MPa"]),
        ("N·m", ["N m", "N*m", "Nm", "N-m", "newton metre", "J"]),
        ("ft·lbf", ["ft lbf", "ft-lbf", "ft-lb", "ft·lb", "foot-pound", "lbf ft"]),
        ("kgf·m", ["kg·m", "kg m", "kg-m", "kg*m", "kgf m", "kpm", "kp m"]),
        ("kWh", ["kW h", "kW·h", "kilowatt hour", "kilowatt-hour", "kilowatt hours"]),
        ("kg_TNT", ["kg TNT", "kgTNT", "kg-TNT", "1000 g_TNT"]),
        ("t_TNT", ["t TNT", "ton TNT", "tonne TNT", "Mg_TNT"]),
        ("kt_TNT", ["kt TNT", "kiloton TNT", "kilotonne TNT"]),
        ("m^2", ["m2", "m²", "square metre", "sq m", "m squared", "m·m"]),
        ("1/s", ["s-1", "s⁻¹", "s^-1", "s**-1"]),
        ("µm", ["um", "μm", "micrometre", "micrometers", "0.001 mm"]),
    ],
)
def test_equivalent_spellings(canonical, spellings):
    for spelling in spellings:
        assert same(spelling, canonical), f"{spelling!r} != {canonical!r}"


@pytest.mark.parametrize(
    "value, src, dst, expected",
    [
        (1, "kcal mol-1", "kJ mol-1", 4.184),
        (1, "cal g-1", "J g-1", 4.184),
        (1, "kJ kg-1", "J g-1", 1),
        (1, "g cm-3", "kg m-3", 1000),
        (1, "J cm-3", "MPa", 1),  # energy density is a pressure
        (1, "J g-1 K-1", "cal g-1 K-1", 1 / 4.184),
        (1, "eV molecule-1", "kJ mol-1", 96.48533212331002),
        (1, "g mol-1", "kg mol-1", 1e-3),
        (1, "cm3 g-1", "m3 kg-1", 1e-3),
        (60, "min", "h", 1),
        (1, "atm", "Torr", 760),
        (1, "kgf cm-2", "MPa", 0.0980665),
        (1, "lbf in-2", "psi", 1),
        (1, "MW", "J s-1", 1e6),
    ],
)
def test_compound_conversions(value, src, dst, expected):
    assert math.isclose(convert(value, src, dst), expected, rel_tol=1e-12)


@pytest.mark.parametrize(
    "unit, dimension",
    [
        ("g mol-1", "molar mass"),
        ("J g-1 K-1", "specific heat capacity"),
        ("kg m2 s-2", "energy"),
        ("J m-3", "pressure"),
        ("cm3 g-1", "specific volume"),
        ("kg m-1", "M L^-1"),  # unnamed dimension falls back to a formula
    ],
)
def test_dimension_names(unit, dimension):
    assert dimension_of(unit) == dimension


def test_listed_units_parse_to_their_dimension():
    for dimension, symbols in list_units().items():
        for symbol in symbols:
            assert dimension_of(symbol) == dimension, symbol


def test_prefixes_case_sensitive():
    assert get_unit("mJ").factor == pytest.approx(1e-3)
    assert get_unit("MJ").factor == pytest.approx(1e6)
    assert get_unit("mPa").factor == pytest.approx(1e-3)
    assert get_unit("MPa").factor == pytest.approx(1e6)


def test_unambiguous_case_insensitive_fallback():
    assert same("KJ/KG", "kJ/kg")
    assert same("gpa", "GPa")


@pytest.mark.parametrize("bad", ["mj", "MPA"])
def test_ambiguous_case(bad):
    with pytest.raises(UnitError, match="Ambiguous"):
        get_unit(bad)


@pytest.mark.parametrize(
    "bad, message",
    [
        ("J/furlong", "cannot interpret 'furlong'"),
        ("J//g", "Could not parse"),
        ("(J/g", "missing '\\)'"),
        ("J/g)", "unbalanced"),
        ("/s", "numerator"),
        ("m^x", "exponent"),
        ("m^0.5", "not an integer"),
        ("", "empty"),
        ("J $", "unexpected"),
    ],
)
def test_parse_errors(bad, message):
    with pytest.raises(UnitError, match=message):
        get_unit(bad)


@pytest.mark.parametrize(
    "spelling",
    ["cal/(g·°C)", "cal g-1 °C-1", "cal/g/°C", "cal/(g ℃)", "cal·g⁻¹·°C⁻¹", "cal/(g·degC)"],
)
def test_celsius_intervals_in_compound_units(spelling):
    assert math.isclose(convert(1, spelling, "J/(g·K)"), 4.184)


def test_fahrenheit_interval():
    assert math.isclose(convert(1, "BTU/(lb·°F)", "J/(kg·K)"), 4186.8, rel_tol=1e-9)


@pytest.mark.parametrize("bare", ["°C", "degF", "℃"])
def test_bare_celsius_is_rejected(bare):
    with pytest.raises(UnitError, match="offset"):
        get_unit(bare)


def test_per_atom_and_per_molecule():
    assert same("eV/atom", "eV/molecule")
    assert same("eV/atom", "eV per particle")


def test_conversions_are_exact_where_possible():
    # Exact rational arithmetic avoids float noise like 999.9999999999999.
    assert convert(1, "g cm-3", "kg m-3") == 1000
    assert convert(1500, "cal/g", "MJ/kg") == 6.276
    assert convert(1, "J cm-3", "MPa") == 1
    assert math.isnan(convert(float("nan"), "J", "kJ"))


def test_non_string_unit():
    with pytest.raises(TypeError):
        get_unit(5)
