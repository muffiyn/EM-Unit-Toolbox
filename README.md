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

Requires Python 3.9+.
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

#### Specific energy × mass

```python
from em_units import specific_to_total, total_to_specific

specific_to_total(1000, "cal/g", 10, "g", to="kJ")  # 41.84
total_to_specific(41.84, "kJ", 10, "g", to="cal/g") # 1000.0
```

#### Molar ↔ specific energy (needs molar mass in g/mol)

```python
from em_units import molar_to_specific, specific_to_molar

molar_to_specific(70.3, "kJ/mol", 222.12, to="cal/g")  # RDX heat of formation
specific_to_molar(-70.5, "cal/g", 227.13, to="kJ/mol")
```

## Supported units

Run `em_units.list_units()` for the full list. Highlights:

| Dimension | Units |
|---|---|
| Energy | J, mJ, kJ, MJ, GJ, erg, cal, kcal, cal_IT, eV, Wh, kWh, BTU, ft·lbf, in·lbf, kgf·m, kgf·cm, g/kg/t TNT |
| Specific energy | J/kg, J/g, kJ/kg, kJ/g, MJ/kg, cal/g, kcal/kg, kcal/g, erg/g, BTU/lb |
| Molar energy | J/mol, kJ/mol, cal/mol, kcal/mol, eV/molecule |
| Mass | kg, g, mg, t, lb, oz, gr (grain) |
| Length | m, cm, mm, µm, km, in, ft |
| Pressure | Pa, kPa, MPa, GPa, bar, kbar, Mbar, atm, psi, dyn/cm² |
| Velocity | m/s, km/s, mm/µs, cm/µs, ft/s |
| Density | kg/m³, g/cm³ (g/cc), lb/in³, lb/ft³ |

Common spellings are accepted (`ergs`, `joules`, `g/cc`, `kg·m`, `J / g`).
Lookups are case-sensitive first, so `mJ` and `MJ` stay distinct; an
unambiguous case-insensitive match (`Joules`) is accepted as a fallback.

## Conventions

- **`cal` is the thermochemical calorie, exactly 4.184 J**, the usual
  convention for heats of formation, explosion and combustion. The
  International Table calorie (4.1868 J) is available as `cal_IT`.
- **TNT equivalent** uses the conventional 4184 J/g (1 kcal/g).
- **`kg*m` / `kg·m`** are treated as kilogram-force metres (9.80665 J), as in
  drop-weight impact sensitivity reports.
