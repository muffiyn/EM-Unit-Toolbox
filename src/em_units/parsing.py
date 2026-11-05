"""Parse unit expressions written in any common notation.

All of these are equivalent::

    J/g   J g-1   J g^-1   J·g⁻¹   J*g**-1   J.g-1   joules per gram   J / (g)

Rules:

* Factors are separated by spaces, ``*``, ``·``, ``⋅``, ``.`` or ``-`` (between
  letters), or are written next to parentheses. Symbols run together, such as
  ``Wm-1/K``, are split when there is exactly one way to do it.
* Exponents may be written ``m^3``, ``m**3``, ``m3``, ``m³``, ``s^-1``, ``s-1``
  or ``s⁻¹``, and may be applied to a parenthesised group: ``(m/s)^2``.
* Numbers scale a unit: ``g/100 g``, ``cc/40 h``, ``10^6 J/mol``,
  ``x 10^6 J/mol``. ``10-5`` directly followed by a unit means 10⁻⁵.
* Everything after a ``/`` (or the word ``per``) is in the denominator, so
  ``J/g K`` and ``J/g/K`` both mean ``J/(g·K)``.
* Atoms take SI prefixes (``kJ``, ``µs``, ``GPa``) and may be written as names
  (``kilojoules``, ``grams``, ``metres``).
* On its own, ``°C``/``°F`` is an absolute temperature (with an offset);
  inside a compound unit (``J/(g·°C)``, ``°C/min``) it is a temperature
  interval. A lone ``°`` is an angle in degrees.
* Trailing substance labels and conditions are kept as the unit's
  ``qualifier``: ``% TNT``, ``g LA``, ``g/100 g solvent``, ``J/g, 25 °C``.
"""

from __future__ import annotations

import math
import re
from dataclasses import replace
from fractions import Fraction
from functools import lru_cache

from .units import (
    ALIASES,
    ATOMS,
    NAME_PREFIXES,
    NAMES,
    NDIMS,
    OFFSETS,
    PREFIXES,
    SUBSTANCE_LABELS,
    Dims,
    Unit,
    dimension_name,
)


class UnitError(ValueError):
    """Raised for unknown units or conversions between incompatible dimensions."""


_SUPERSCRIPTS = str.maketrans("⁻⁺⁰¹²³⁴⁵⁶⁷⁸⁹", "-+0123456789")
_SUPERSCRIPT_RUN = re.compile("[⁻⁺⁰¹²³⁴⁵⁶⁷⁸⁹]+")
_LETTER = r"[^\W\d]"  # any unicode letter or underscore
# "g TNT", "kg-TNT", "kgTNT", "kt TNT" -> TNT-equivalent energy. Only after a
# mass unit: "% TNT" is a percentage *of* TNT, handled as a label.
_TNT = re.compile(
    r"\b((?:[kMGTm]?g|[kMGT]?t|lbs?|tons?|tonnes?|kilotons?|kilotonnes?|megatons?|megatonnes?))"
    r"[\s_\-]*TNT\b"
)


def _tidy(text: str) -> str:
    s = " ".join(text.strip().split())
    s = s.rstrip(".").rstrip()  # "mols."
    return _TNT.sub(r"\1_TNT", s)


def normalize(text: str) -> str:
    """Rewrite a unit expression into a canonical spelling (no evaluation)."""
    s = _tidy(text)
    s = re.sub(r"^[x×*·]\s*(?=[\d(])", "", s)  # "x 10^6 J/mol"
    s = s.replace("μ", "µ").replace("Ω", "Ω")  # Greek mu -> micro sign; ohm sign -> omega
    s = s.replace("**", "^")
    for sep in ("*", "⋅", "×", "•"):
        s = s.replace(sep, "·")
    s = _SUPERSCRIPT_RUN.sub(lambda m: "^" + m.group().translate(_SUPERSCRIPTS), s)
    # Temperatures: "°C", "° C", "℃", "deg C", "degrees Celsius" -> "degC"
    s = s.replace("℃", "degC").replace("℉", "degF")
    s = re.sub(r"°\s*([CFR])\b", r"deg\1", s)
    s = re.sub(r"\bdeg(?:ree)?s?\s*([CFR])\b", r"deg\1", s)
    s = re.sub(r"\bdeg(?:ree)?s?\s+celsius\b", "degC", s, flags=re.IGNORECASE)
    s = re.sub(r"\bdeg(?:ree)?s?\s+fahrenheit\b", "degF", s, flags=re.IGNORECASE)
    s = s.replace("°", "deg")  # what remains is an angle
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
    rf"(?P<atom>{_LETTER}+|%|‰)|(?P<num>[+-]?\d+(?:\.\d+)?)|(?P<op>[·/^()])"
)


def _tokenize(s: str, original: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    pos = 0
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if not m:
            raise UnitError(f"Could not parse unit {original!r}: unexpected {s[pos]!r}")
        tokens.append((m.lastgroup, m.group()))
        pos = m.end()
    return tokens


def _strip_plural(word: str) -> list[str]:
    forms = [word]
    if word.endswith("es"):
        forms.append(word[:-2])
    if word.endswith("s"):
        forms.append(word[:-1])
    return forms


def _name_to_symbol(word: str) -> str | None:
    for form in _strip_plural(word.lower()):
        if form in NAMES:
            return NAMES[form]
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


def _strict_atom(word: str) -> tuple[Fraction, Dims] | None:
    """Exact symbol, or SI prefix + symbol. Case-sensitive."""
    if word in ATOMS:
        factor, dims, _ = ATOMS[word]
        return _exact(factor), dims
    for prefix, scale in PREFIXES.items():
        rest = word[len(prefix):]
        if word.startswith(prefix) and rest in ATOMS and ATOMS[rest][2]:
            factor, dims, _ = ATOMS[rest]
            return _exact(scale) * _exact(factor), dims
    return None


def _resolve_atom(word: str, original: str) -> tuple[Fraction, Dims]:
    # 1-2. Exact symbol or SI prefix + symbol (case-sensitive: mJ != MJ).
    hit = _strict_atom(word)
    if hit is not None:
        return hit
    # 3. Full names, optionally with a prefix name: "joules", "kilojoules".
    symbol = _name_to_symbol(word)
    if symbol is not None:
        factor, dims, _ = ATOMS[symbol]
        return _exact(factor), dims
    lower = word.lower()
    for prefix, scale in NAME_PREFIXES.items():
        if lower.startswith(prefix):
            symbol = _name_to_symbol(lower[len(prefix):])
            if symbol is not None and ATOMS[symbol][2]:
                factor, dims, _ = ATOMS[symbol]
                return _exact(scale) * _exact(factor), dims
    # 4. Case-insensitive symbol, only if unambiguous.
    options = _dedupe(_LOWER_INDEX.get(lower, []))
    if len(options) == 1:
        return _exact(options[0][0]), options[0][1]
    if len(options) > 1:
        matches = sorted(
            {s for s in ATOMS if s.lower() == lower}
            | {p + s for s, (_, _, ok) in ATOMS.items() if ok for p in PREFIXES if (p + s).lower() == lower}
        )
        raise UnitError(f"Ambiguous unit {original!r}: {word!r} could be any of {', '.join(matches)}")
    raise UnitError(f"Unknown unit {original!r}: cannot interpret {word!r}. Use list_units() to see supported units.")


def _split_glued(word: str) -> tuple[str, str] | None:
    """Split symbols written together ("Wm" -> "W", "m") if exactly one split works."""
    splits = [
        (word[:i], word[i:])
        for i in range(1, len(word))
        if _strict_atom(word[:i]) is not None and _strict_atom(word[i:]) is not None
    ]
    return splits[0] if len(splits) == 1 else None


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
        factor, dims = Fraction(1), [0] * NDIMS
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
        head_factor, head_dims = Fraction(1), [0] * NDIMS  # glued prefix, e.g. W in "Wm-1"
        if kind == "atom":
            try:
                f, d = _resolve_atom(text, self.original)
            except UnitError as err:
                split = _split_glued(text) if "Unknown" in str(err) else None
                if split is None:
                    raise
                head = _strict_atom(split[0])
                head_factor, head_dims = head[0], list(head[1])
                f, d = _strict_atom(split[1])
            factor, dims = f, list(d)
            exponent = self.exponent(allow_bare=True)
        elif kind == "num":
            factor, dims = Fraction(text), [0] * NDIMS
            nxt = self.peek()
            # "10-5" is 10^-5 (as in "10-5/°C"); other numbers take only "^".
            ten_power = text == "10" and nxt is not None and nxt[0] == "num" and nxt[1][0] in "+-"
            exponent = self.exponent(allow_bare=ten_power)
        elif text == "(":
            factor, dims = self.product()
            if self.peek() != ("op", ")"):
                raise self.fail("missing ')'")
            self.take()
            exponent = self.exponent(allow_bare=True)
        else:
            raise self.fail(f"unexpected {text!r}")
        if exponent is not None:
            factor, dims = factor**exponent, [x * exponent for x in dims]
        return head_factor * factor, [a + b for a, b in zip(head_dims, dims)]

    def exponent(self, allow_bare: bool) -> int | None:
        tok = self.peek()
        if tok == ("op", "^"):
            self.take()
            if self.peek() == ("op", "("):
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


def _offset(s: str) -> Fraction:
    """Offset for a lone absolute temperature atom ("degC", "celsius"), else 0."""
    if s in OFFSETS:
        return OFFSETS[s]
    symbol = _name_to_symbol(s)
    return OFFSETS.get(symbol, Fraction(0)) if symbol else Fraction(0)


def _parse_expression(text: str, original: str) -> Unit:
    s = normalize(text)
    s = ALIASES.get(s, s)
    parser = _Parser(_tokenize(s, original), original)
    factor, dims = parser.product()
    if parser.peek() is not None:
        raise parser.fail("unbalanced ')'")
    dims_t = tuple(dims)
    return Unit(
        symbol=s,
        dimension=dimension_name(dims_t),
        factor=float(factor),
        dims=dims_t,
        exact=factor,
        offset=_offset(s),
    )


def _is_label(word: str) -> bool:
    w = word.lower().strip("()[]")
    w = re.sub(r"^[αβγδεε]-", "", w)  # "ε-CL-20"
    return w in SUBSTANCE_LABELS


def _is_unit_word(word: str, original: str) -> bool:
    try:
        _parse_expression(word, original)
    except UnitError:
        return False
    return True


# A label looks like a name: "TNT", "ε-CL-20", "tetryl", "(l)". Not "$" or "?".
_LABEL_WORD = re.compile(r"[\w()\[\]\-+.]*[^\W\d_][\w()\[\]\-+.]*")

# "25 °C", "298 K": a reference condition, not a unit.
_CONDITION = re.compile(r"[-+]?\d+(?:\.\d+)?\s*(?:°\s*[CFR]|℃|℉|K|deg\s*[CF])")


def parse_unit(text: str) -> Unit:
    """Parse a unit expression into a :class:`Unit`."""
    if not isinstance(text, str):
        raise TypeError(f"Unit must be a string, got {type(text).__name__}")
    return _parse_cached(text)


@lru_cache(maxsize=4096)
def _parse_cached(text: str) -> Unit:
    tidy = _tidy(text)
    head, _, tail = tidy.partition(",")
    head, tail = head.strip(), tail.strip()

    if tail and _CONDITION.fullmatch(head):
        # "25 °C, H2O (l)": no unit, only a reference condition.
        return Unit(symbol="1", dimension=dimension_name((0,) * NDIMS), factor=1.0,
                    dims=(0,) * NDIMS, exact=Fraction(1), qualifier=tidy)

    words = head.split(" ")
    try:
        unit = _parse_expression(head, text)
        if not any(_is_label(w) for w in words[1:]):
            return replace(unit, qualifier=tail)
        error = None
    except UnitError as err:
        error = err

    # Peel trailing label words: "% TNT", "g MF", "g/100 g solvent".
    for k in range(1, len(words)):
        if not _LABEL_WORD.fullmatch(words[k]):
            continue
        if _is_label(words[k]) or not _is_unit_word(words[k], text):
            try:
                unit = _parse_expression(" ".join(words[:k]), text)
            except UnitError:
                continue
            label = " ".join(words[k:])
            return replace(unit, qualifier=f"{label}, {tail}" if tail else label)
    if error is None:  # a label word that also parsed as a unit, with no clean split
        error = UnitError(f"Could not parse unit {text!r}")
    raise error
