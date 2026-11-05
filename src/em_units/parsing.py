"""Parse unit expressions written in any common notation.

All of these are equivalent::

    J/g   J g-1   J g^-1   J·g⁻¹   J*g**-1   J.g-1   joules per gram   J / (g)

Rules:

* Factors are separated by spaces, ``*``, ``·``, ``⋅``, ``.`` or ``-`` (between
  letters), or are written next to parentheses.
* Exponents may be written ``m^3``, ``m**3``, ``m3``, ``m³``, ``s^-1``, ``s-1``
  or ``s⁻¹``, and may be applied to a parenthesised group: ``(m/s)^2``.
* Everything after a ``/`` (or the word ``per``) is in the denominator, so
  ``J/g K`` and ``J/g/K`` both mean ``J/(g·K)``.
* Atoms take SI prefixes (``kJ``, ``µs``, ``GPa``) and may be written as names
  (``kilojoules``, ``grams``, ``metres``).
"""

from __future__ import annotations

import math
import re
from fractions import Fraction
from functools import lru_cache

from .units import (
    ALIASES,
    ATOMS,
    NAME_PREFIXES,
    NAMES,
    PREFIXES,
    Dims,
    Unit,
    dimension_name,
)


class UnitError(ValueError):
    """Raised for unknown units or conversions between incompatible dimensions."""


_SUPERSCRIPTS = str.maketrans("⁻⁺⁰¹²³⁴⁵⁶⁷⁸⁹", "-+0123456789")
_SUPERSCRIPT_RUN = re.compile("[⁻⁺⁰¹²³⁴⁵⁶⁷⁸⁹]+")
_LETTER = r"[^\W\d]"  # any unicode letter or underscore


def normalize(text: str) -> str:
    """Rewrite a unit expression into a canonical spelling (no evaluation)."""
    s = " ".join(text.strip().split())
    s = s.replace("μ", "µ")  # Greek mu -> micro sign
    s = s.replace("**", "^")
    for sep in ("*", "⋅", "×", "•"):
        s = s.replace(sep, "·")
    s = _SUPERSCRIPT_RUN.sub(lambda m: "^" + m.group().translate(_SUPERSCRIPTS), s)
    # "°C", "° C", "℃" -> "degC" (likewise °F)
    s = s.replace("℃", "degC").replace("℉", "degF")
    s = re.sub(r"°\s*([CF])\b", r"deg\1", s)
    # "g TNT", "kg-TNT", "gTNT" -> "g_TNT"
    s = re.sub(r"[\s_\-]*TNT\b", "_TNT", s)
    # Words
    s = re.sub(r"\s+per\s+", "/", s, flags=re.IGNORECASE)
    s = re.sub(rf"\b(?:square|sq)\s+({_LETTER}+)", r"\1^2", s, flags=re.IGNORECASE)
    s = re.sub(rf"\b(?:cubic|cu)\s+({_LETTER}+)", r"\1^3", s, flags=re.IGNORECASE)
    s = re.sub(rf"({_LETTER}+)\s+squared\b", r"\1^2", s, flags=re.IGNORECASE)
    s = re.sub(rf"({_LETTER}+)\s+cubed\b", r"\1^3", s, flags=re.IGNORECASE)
    # "." and "-" between letters are multiplication: "kg.m-3", "ft-lbf"
    s = re.sub(rf"(?<=[^\W\d)])\.(?={_LETTER}|\()", "·", s)
    s = re.sub(rf"(?<=[^\W\d)])-(?={_LETTER}|\()", "·", s)
    # Spaces around operators carry no meaning; other spaces multiply.
    s = re.sub(r"\s*([/^·()])\s*", r"\1", s)
    s = s.replace(" ", "·")
    return s


_TOKEN = re.compile(
    rf"(?P<atom>{_LETTER}+)|(?P<num>[+-]?\d+(?:\.\d+)?)|(?P<op>[·/^()])"
)


def _tokenize(s: str, original: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    pos = 0
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if not m:
            raise UnitError(f"Could not parse unit {original!r}: unexpected {s[pos]!r}")
        kind = m.lastgroup
        tokens.append((kind, m.group()))
        pos = m.end()
    return tokens


def _strip_plural(word: str) -> list[str]:
    forms = [word]
    if word.endswith("es"):
        forms.append(word[:-2])
    if word.endswith("s"):
        forms.append(word[:-1])
    return forms


def _lookup_name(word: str) -> tuple[float, Dims, bool] | None:
    for form in _strip_plural(word.lower()):
        if form in NAMES:
            return ATOMS[NAMES[form]]
    return None


def _all_prefixed_atoms() -> dict[str, list[tuple[float, Dims]]]:
    """Lowercased symbol -> every (factor, dims) it could mean, for case-insensitive fallback."""
    index: dict[str, list[tuple[float, Dims]]] = {}
    for symbol, (factor, dims, prefixable) in ATOMS.items():
        index.setdefault(symbol.lower(), []).append((factor, dims))
        if prefixable:
            for prefix, scale in PREFIXES.items():
                index.setdefault((prefix + symbol).lower(), []).append((scale * factor, dims))
    return index


_LOWER_INDEX = _all_prefixed_atoms()


def _dedupe(options: list[tuple[float, Dims]]) -> list[tuple[float, Dims]]:
    unique: list[tuple[float, Dims]] = []
    for factor, dims in options:
        if not any(d == dims and math.isclose(f, factor, rel_tol=1e-12) for f, d in unique):
            unique.append((factor, dims))
    return unique


def _exact(x: float) -> Fraction:
    """Exact rational for a float's shortest decimal repr (0.01 -> 1/100, not 0.01000...0002)."""
    return Fraction(repr(x))


def _resolve_atom(word: str, original: str) -> tuple[Fraction, Dims]:
    # 1. Exact symbol (case-sensitive, so mJ and MJ stay distinct).
    if word in ATOMS:
        factor, dims, _ = ATOMS[word]
        return _exact(factor), dims
    # 2. SI prefix + symbol.
    for prefix, scale in PREFIXES.items():
        rest = word[len(prefix):]
        if word.startswith(prefix) and rest in ATOMS and ATOMS[rest][2]:
            factor, dims, _ = ATOMS[rest]
            return _exact(scale) * _exact(factor), dims
    # 3. Full names, optionally with a prefix name: "joules", "kilojoules".
    hit = _lookup_name(word)
    if hit is not None:
        return _exact(hit[0]), hit[1]
    lower = word.lower()
    for prefix, scale in NAME_PREFIXES.items():
        if lower.startswith(prefix):
            hit = _lookup_name(lower[len(prefix):])
            if hit is not None and hit[2]:
                return _exact(scale) * _exact(hit[0]), hit[1]
    # 4. Case-insensitive symbol, only if unambiguous.
    options = _dedupe(_LOWER_INDEX.get(lower, []))
    if len(options) == 1:
        return _exact(options[0][0]), options[0][1]
    if len(options) > 1:
        matches = sorted(
            {s for s, (f, d, p) in ATOMS.items() if s.lower() == lower}
            | {
                p + s
                for s, (f, d, ok) in ATOMS.items()
                if ok
                for p in PREFIXES
                if (p + s).lower() == lower
            }
        )
        raise UnitError(f"Ambiguous unit {original!r}: {word!r} could be any of {', '.join(matches)}")
    raise UnitError(f"Unknown unit {original!r}: cannot interpret {word!r}. Use list_units() to see supported units.")


class _Parser:
    def __init__(self, tokens: list[tuple[str, str]], original: str):
        self.tokens = tokens
        self.pos = 0
        self.original = original

    def peek(self) -> tuple[str, str] | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def take(self) -> tuple[str, str]:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def fail(self, why: str) -> UnitError:
        return UnitError(f"Could not parse unit {self.original!r}: {why}")

    def product(self) -> tuple[Fraction, list[int]]:
        """product := item (('·' | '/' | adjacency) item)*"""
        factor, dims = Fraction(1), [0] * 5
        sign = 1
        expect_item = True
        while True:
            tok = self.peek()
            if tok is None or tok == ("op", ")"):
                break
            if tok == ("op", "·"):
                if expect_item:
                    raise self.fail("unexpected '·'")
                self.take()
                expect_item = True
                continue
            if tok == ("op", "/"):
                if expect_item:
                    raise self.fail("'/' needs a numerator (write '1/s', not '/s')")
                self.take()
                sign = -1
                expect_item = True
                continue
            f, d = self.item()
            factor *= f**sign
            dims = [a + sign * b for a, b in zip(dims, d)]
            expect_item = False
        if expect_item:
            raise self.fail("expression ends with an operator" if self.tokens else "empty unit")
        return factor, dims

    def item(self) -> tuple[Fraction, list[int]]:
        """item := primary exponent?"""
        kind, text = self.take()
        if kind == "atom":
            f, d = _resolve_atom(text, self.original)
            factor, dims = f, list(d)
        elif kind == "num":
            factor, dims = Fraction(text), [0] * 5
        elif text == "(":
            factor, dims = self.product()
            if self.peek() != ("op", ")"):
                raise self.fail("missing ')'")
            self.take()
        else:
            raise self.fail(f"unexpected {text!r}")
        exponent = self.exponent(allow_bare=kind != "num")
        if exponent is not None:
            factor, dims = factor**exponent, [x * exponent for x in dims]
        return factor, dims

    def exponent(self, allow_bare: bool) -> int | None:
        tok = self.peek()
        if tok == ("op", "^"):
            self.take()
            nxt = self.peek()
            if nxt == ("op", "("):
                self.take()
                value = self._integer()
                if self.peek() != ("op", ")"):
                    raise self.fail("missing ')' after exponent")
                self.take()
                return value
            return self._integer()
        if allow_bare and tok is not None and tok[0] == "num":
            return self._integer()  # "m3", "s-1"
        return None

    def _integer(self) -> int:
        tok = self.peek()
        if tok is None or tok[0] != "num":
            raise self.fail("expected an exponent")
        self.take()
        value = float(tok[1])
        if not value.is_integer():
            raise self.fail(f"exponent {tok[1]} is not an integer")
        return int(value)


def parse_unit(text: str) -> Unit:
    """Parse a unit expression into a :class:`Unit`."""
    if not isinstance(text, str):
        raise TypeError(f"Unit must be a string, got {type(text).__name__}")
    return _parse_cached(text)


@lru_cache(maxsize=1024)
def _parse_cached(text: str) -> Unit:
    s = normalize(text)
    s = ALIASES.get(s, s)
    tokens = _tokenize(s, text)
    parser = _Parser(tokens, text)
    factor, dims = parser.product()
    if parser.peek() is not None:
        raise parser.fail("unbalanced ')'")
    dims_t = tuple(dims)
    if dims_t == (0, 0, 0, 0, 1) and re.search(r"deg[CF]", s):
        raise UnitError(
            f"{text!r} is an absolute temperature scale with an offset, which is not "
            "supported; °C and °F are accepted inside compound units such as J/(g·°C)"
        )
    return Unit(
        symbol=s, dimension=dimension_name(dims_t), factor=float(factor), dims=dims_t, exact=factor
    )
