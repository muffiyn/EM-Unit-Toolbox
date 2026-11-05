# EM-Unit-Toolbox
Unit normalizer for energetic materials data.

`em_units` is a small, dependency-free Python library for converting the units
that show up in energetic-materials work: ergs, calories, joules, cal/g, kJ/mol,
kgf·m drop-weight energies, detonation pressures and velocities, and so on. It
also combines two measurements into one, for example a striker mass and a drop
height into an impact energy.

## Install

```bash
pip install git+https://github.com/muffiyn/EM-Unit-Toolbox.git
```

Requires Python 3.10+.
## Usage
### Single-unit conversions

```python
from em_units import convert

convert(1, "cal/g", "J/g")        # 4.184
convert(1e7, "erg", "J")          # 1.0
convert(1500, "cal/g", "MJ/kg")   # 6.276
convert(5.4, "kJ", "kcal")        # 1.2906...
convert(1, "kgf*m", "J")          # 9.80665
convert(34.7, "GPa", "kbar")      # 347.0
convert(8.75, "mm/us", "m/s")     # 8750.0
```

Converting between dimensions (e.g. `J` to `J/g`) raises `UnitError`.

### Two-measurement conversions

#### Gravitational potential energy (drop-weight impact)

E = m·g·h, with standard gravity g = 9.80665 m/s² by default.

```python
from em_units import potential_energy, drop_height, drop_mass

potential_energy(2, "kg", 50, "cm")               # 9.80665 J
potential_energy(10, "lb", 2, "ft", to="ft*lbf")  # 20.0
potential_energy(5, "kg", 20, "cm", to="kgf*m")   # 1.0
potential_energy(1, "kg", 1, "m", g=1.62)         # custom gravity, m/s^2

# Inverse: what height (or mass) gives a target energy?
drop_height(7.5, "J", 2.5, "kg", to="cm")         # 30.59 cm
drop_mass(7.5, "J", 30, "cm", to="kg")            # 2.549 kg
```

#### Weight of a mass (friction sensitivity loads)

```python
from em_units import weight_force, force_to_mass

weight_force(36, "kg")              # 353.04 N (BAM friction 36 kg load)
weight_force(10, "lb", to="lbf")    # ≈ 10.0
force_to_mass(353.04, "N", to="kg") # ≈ 36.0
```

#### ESD spark energy (E = ½·C·V²)

```python
from em_units import esd_energy, esd_voltage

esd_energy(500, "pF", 5, "kV", to="mJ")  # 6.25
esd_voltage(6.25, "mJ", 500, "pF")       # 5.0 kV
```

#### Specific energy × mass

```python
from em_units import specific_to_total, total_to_specific

specific_to_total(1000, "cal/g", 10, "g", to="kJ")  # 41.84
total_to_specific(41.84, "kJ", 10, "g", to="cal/g") # 1000.0
```

#### Molar ↔ specific energy (needs the molar mass)

```python
from em_units import molar_to_specific, specific_to_molar

molar_to_specific(70.3, "kJ mol-1", 222.12, to="cal g-1")  # RDX heat of formation
specific_to_molar(-70.5, "cal/g", 227.13, to="kJ/mol")
molar_to_specific(70.3, "kJ/mol", 0.22212, molar_mass_unit="kg mol-1")
```

## Unit notation

Units can be written however the source paper or instrument writes them. All of
these are the same unit:

```
J/g    J g-1    J g^-1    J·g⁻¹    J*g**-1    J.g-1    joules per gram
```

- **Products:** separate factors with a space, `*`, `·`, `.` or `-` (e.g.
  `N m`, `ft-lbf`, `kg.m-3`).
- **Exponents:** `m^3`, `m**3`, `m3`, `m³`, `s^-1`, `s-1`, `s⁻¹`, and also on
  groups: `(m/s)^2`.
- **Division:** `/`, `per`, or negative exponents. Everything after a `/` is
  in the denominator, so `J/g K`, `J/g/K` and `J/(g·K)` are the same.
- **Prefixes:** any SI prefix on any metric unit (`kJ`, `µs`, `us`, `GPa`,
  `kt TNT`), plus spelled-out names (`kilojoules`, `grams`, `cubic centimetre`).
- **Numbers:** `g/100 g`, `cc/40 h`, `10^6 J/mol` and `x 10^6 J/mol` scale
  the unit; `10-5/°C` means 10⁻⁵ per °C.
- **Run-together symbols:** `Wm-1/K` is read as `W·m⁻¹/K` when there is
  exactly one way to split it.
- **Temperature:** on its own, `°C`/`°F` is an absolute temperature
  (`convert(25, "°C", "K")` is 298.15). Inside compound units it is a
  temperature interval: `cal/(g·°C)`, `°C/min`.
- **Labels:** words naming a substance or condition are kept as the unit's
  `qualifier`, not parsed as units: `% TNT`, `% ε-CL-20`, `g LA`, `g MF`,
  `g/100 g solvent`, `J/g, 25 °C`. A labelled unit converts to the same label
  or to an unlabelled unit, but `g LA` → `g MF` raises `UnitError`.
  `g TNT`/`kg TNT` (a mass unit directly before TNT) is TNT-equivalent energy.
- **Case:** symbols are case-sensitive first, so `mJ` and `MJ` stay distinct.
  An unambiguous case-insensitive match (`KJ/KG`, `Joules`) is accepted, and
  an ambiguous one (`MPA`: mPa or MPa?) raises an error.

Any combination works, and two units convert whenever their dimensions match:

```python
convert(1, "kcal mol-1", "kJ·mol⁻¹")      # 4.184
convert(1, "g cm-3", "kg/m3")             # 1000.0
convert(1, "J cm-3", "MPa")               # 1.0  (energy density = pressure)
convert(1, "cal/(g·°C)", "J g-1 K-1")     # 4.184
convert(1, "eV/atom", "kJ/mol")           # 96.485...
```

## Supported units

The building blocks are:

| Kind | Units |
|---|---|
| Energy | J, erg, cal, cal_IT, Cal (= kcal), eV, Wh, BTU, g_TNT, t_TNT |
| Mass | g, t, lb, oz, gr (grain) |
| Length | m, Å, in, ft, yd, mil, micron |
| Time | s, min, h, d (day), wk, yr |
| Amount | mol, molecule / atom / particle |
| Temperature | K, °C, °F, °R |
| Angle | rad, ° (deg) |
| Ratios | %, ‰, ppm, ppb |
| Electrical | A, C, V, Ω, F, D (debye) |
| Force | N, dyn, lbf, kgf (kp) |
| Pressure | Pa, bar, atm, psi, ksi, Torr, mmHg, barye |
| Power | W |
| Volume | L, cc |
| Acceleration | gn (standard gravity) |

`em_units.list_units()` (or `em-units units`) lists common combinations for
each dimension: energy, specific energy, molar energy, molar mass, pressure,
velocity, density, heat capacities, and more.

## Conventions

- **`cal` is the thermochemical calorie, exactly 4.184 J**, the usual
  convention for heats of formation, explosion and combustion. The
  International Table calorie (4.1868 J) is available as `cal_IT`.
- **TNT equivalent** uses the conventional 4184 J/g (1 kcal/g).
- **`kg*m` / `kg·m` / `kg m`** are treated as kilogram-force metres
  (9.80665 J), as in drop-weight impact sensitivity reports. Likewise `ft-lb`
  means foot-pound force.
