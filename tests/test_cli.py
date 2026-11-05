import pytest

from em_units.cli import main


def test_convert(capsys):
    assert main(["convert", "1", "cal/g", "J/g"]) == 0
    assert capsys.readouterr().out.strip() == "1 cal/g = 4.184 J/g"


def test_impact(capsys):
    assert main(["impact", "--mass", "2 kg", "--height", "50 cm"]) == 0
    assert capsys.readouterr().out.strip() == "2 kg dropped 50 cm = 9.80665 J"


def test_units(capsys):
    assert main(["units", "energy"]) == 0
    assert capsys.readouterr().out.startswith("energy: J, mJ, kJ")


def test_error_exit(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["convert", "1", "J", "kg"])
    assert exc.value.code == 2
    assert "Cannot convert" in capsys.readouterr().err
