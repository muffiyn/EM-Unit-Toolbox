"""Command-line interface: ``em-units``."""

from __future__ import annotations

import argparse
import sys

from .converter import UnitError, convert, list_units
from .impact import potential_energy


def _quantity(text: str) -> tuple[float, str]:
    value, _, unit = text.strip().partition(" ")
    try:
        return float(value), unit.strip()
    except ValueError:
        raise argparse.ArgumentTypeError(f"Expected '<number> <unit>', got {text!r}") from None


def main(argv: list[str] | None = None) -> int:
    # Unit symbols use characters like "·", "µ" and "⁻" that legacy Windows code
    # pages cannot encode; escape them rather than crash.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(prog="em-units", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_conv = sub.add_parser("convert", help="Convert a value between units")
    p_conv.add_argument("value", type=float)
    p_conv.add_argument("from_unit")
    p_conv.add_argument("to_unit")

    p_pe = sub.add_parser("impact", help="Potential energy of a dropped mass (E = m*g*h)")
    p_pe.add_argument("--mass", required=True, type=_quantity, help="e.g. '2 kg'")
    p_pe.add_argument("--height", required=True, type=_quantity, help="e.g. '50 cm'")
    p_pe.add_argument("--to", default="J", help="Energy unit for the result (default: J)")

    p_list = sub.add_parser("units", help="List supported units")
    p_list.add_argument("dimension", nargs="?", help="e.g. 'energy'")

    args = parser.parse_args(argv)
    try:
        if args.command == "convert":
            result = convert(args.value, args.from_unit, args.to_unit)
            print(f"{args.value:g} {args.from_unit} = {result:.6g} {args.to_unit}")
        elif args.command == "impact":
            (m, mu), (h, hu) = args.mass, args.height
            result = potential_energy(m, mu, h, hu, to=args.to)
            print(f"{m:g} {mu} dropped {h:g} {hu} = {result:.6g} {args.to}")
        else:
            for dim, symbols in list_units(args.dimension).items():
                print(f"{dim}: {', '.join(symbols)}")
    except (UnitError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0
