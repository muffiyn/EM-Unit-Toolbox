import math

import pytest

from em_units import (
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


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-12)


@pytest.mark.parametrize(
    "value, src, dst, expected",
    [
        (1, "erg", "J", 1e-7),
        (1, "J", "erg", 1e7),
        (1, "kJ", "J", 1000),
        (1, "cal", "J", 4.184),
        (1, "kcal", "kJ", 4.184),
        (1, "cal_IT", "J", 4.1868),
        (1, "g_TNT", "kJ", 4.184),
        (1, "kgf*m", "J", 9.80665),
        (1, "kWh", "MJ", 3.6),
        (1, "ft*lbf", "J", 1.3558179483314004),
        (1, "cal/g", "J/g", 4.184),
        (1, "cal/g", "kJ/kg", 4.184),
        (1, "kcal/kg", "cal/g", 1),
        (1000, "cal/g", "MJ/kg", 4.184),
        (1, "erg/g", "J/kg", 1e-4),
        (1, "kcal/mol", "kJ/mol", 4.184),
        (1, "lb", "g", 453.59237),
        (7000, "gr", "lb", 1),
        (1, "in", "cm", 2.54),
        (1, "GPa", "kbar", 10),
        (1, "mm/us", "km/s", 1),
        (1, "g/cm^3", "kg/m^3", 1000),
    ],
)
def test_convert(value, src, dst, expected):
    assert close(convert(value, src, dst), expected)


def test_round_trip_every_unit():
    for dim, symbols in list_units().items():
        for a in symbols:
            for b in symbols:
                assert close(convert(convert(3.7, a, b), b, a), 3.7), (dim, a, b)


def test_aliases_and_spacing():
    assert get_unit("ergs") is get_unit("erg")
    assert get_unit("Joules") is get_unit("J")  # unambiguous case-insensitive fallback
    assert get_unit("J / g") is get_unit("J/g")
    assert get_unit("kg·m") is get_unit("kgf*m")
    assert get_unit("g/cc") is get_unit("g/cm^3")


def test_case_sensitive_prefixes_are_distinct():
    assert convert(1, "MJ", "J") == 1e6
    assert convert(1, "mJ", "J") == 1e-3


def test_ambiguous_case_insensitive_lookup_raises():
    with pytest.raises(UnitError, match="Ambiguous"):
        get_unit("mj")


def test_unknown_unit():
    with pytest.raises(UnitError, match="Unknown unit"):
        convert(1, "furlong", "m")


def test_incompatible_dimensions():
    with pytest.raises(UnitError, match="Cannot convert"):
        convert(1, "J", "J/g")
    assert dimension_of("cal/g") == "specific energy"


def test_to_si():
    assert to_si(2, "kcal") == (8368.0, "J")


def test_specific_total_round_trip():
    total = specific_to_total(1000, "cal/g", 10, "g", to="kJ")
    assert close(total, 41.84)
    assert close(total_to_specific(total, "kJ", 10, "g", to="cal/g"), 1000)


def test_specific_to_total_rejects_wrong_dimensions():
    with pytest.raises(UnitError, match="Expected a mass unit"):
        specific_to_total(1, "cal/g", 1, "m")


def test_molar_specific_round_trip():
    # RDX: M = 222.12 g/mol
    cal_g = molar_to_specific(70.3, "kJ/mol", 222.12, to="cal/g")
    assert close(cal_g, 70.3e3 / 222.12 / 4.184)
    assert close(specific_to_molar(cal_g, "cal/g", 222.12, to="kJ/mol"), 70.3)


def test_molar_mass_must_be_positive():
    with pytest.raises(ValueError):
        molar_to_specific(1, "kJ/mol", 0)
