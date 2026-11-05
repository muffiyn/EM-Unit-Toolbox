import math

import pytest

from em_units import UnitError, drop_height, drop_mass, force_to_mass, potential_energy, weight_force


def test_potential_energy_si():
    assert math.isclose(potential_energy(2, "kg", 50, "cm"), 2 * 9.80665 * 0.5)


def test_potential_energy_mixed_units():
    # 10 lb from 2 ft
    expected = 10 * 0.45359237 * 9.80665 * 2 * 0.3048
    assert math.isclose(potential_energy(10, "lb", 2, "ft"), expected)
    assert math.isclose(potential_energy(10, "lb", 2, "ft", to="ft*lbf"), 20)


def test_potential_energy_output_units():
    assert math.isclose(potential_energy(5, "kg", 20, "cm", to="kgf*m"), 1.0)
    assert math.isclose(potential_energy(1, "kg", 1, "m", to="erg"), 9.80665e7)


def test_custom_gravity():
    assert math.isclose(potential_energy(1, "kg", 1, "m", g=1.62), 1.62)
    assert math.isclose(potential_energy(1, "kg", 1, "m", g=1, g_unit="gn"), 9.80665)


def test_inverse_functions():
    e = potential_energy(2.5, "kg", 37, "cm", to="J")
    assert math.isclose(drop_height(e, "J", 2.5, "kg", to="cm"), 37)
    assert math.isclose(drop_mass(e, "J", 37, "cm", to="kg"), 2.5)


@pytest.mark.parametrize(
    "args",
    [
        (1, "m", 1, "m"),  # mass given as length
        (1, "kg", 1, "kg"),  # height given as mass
    ],
)
def test_wrong_dimensions(args):
    with pytest.raises(UnitError):
        potential_energy(*args)


def test_wrong_output_dimension():
    with pytest.raises(UnitError):
        potential_energy(1, "kg", 1, "m", to="J/g")


def test_invalid_values():
    with pytest.raises(ValueError):
        potential_energy(-1, "kg", 1, "m")
    with pytest.raises(ValueError):
        drop_height(1, "J", 0, "kg")
    with pytest.raises(ValueError):
        potential_energy(1, "kg", 1, "m", g=0)


def test_weight_force():
    assert math.isclose(weight_force(36, "kg"), 36 * 9.80665)
    assert math.isclose(weight_force(1, "lb", to="lbf"), 1)
    assert math.isclose(weight_force(10, "lb"), 10 * 0.45359237 * 9.80665)
    assert math.isclose(force_to_mass(weight_force(2.5, "kg"), "N"), 2.5)


def test_weight_force_rejects_wrong_dimension():
    with pytest.raises(UnitError):
        weight_force(1, "N")
