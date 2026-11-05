import math

import pytest

from em_units import UnitError, esd_energy, esd_voltage


def test_esd_energy():
    # 500 pF charged to 5 kV stores 6.25 mJ
    assert math.isclose(esd_energy(500, "pF", 5, "kV", to="mJ"), 6.25)
    assert math.isclose(esd_energy(1, "uF", 1, "kV"), 0.5)


def test_esd_voltage_inverts_energy():
    e = esd_energy(10, "nF", 12.5, "kV")
    assert math.isclose(esd_voltage(e, "J", 10, "nF"), 12.5)


def test_esd_rejects_wrong_dimensions():
    with pytest.raises(UnitError):
        esd_energy(1, "V", 1, "F")
    with pytest.raises(ValueError):
        esd_voltage(1, "J", 0, "nF")
