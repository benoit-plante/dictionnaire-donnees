"""LimeSurvey's relevance expressions read back as conditions (v0.21, D-169, § 5.7.2 of the
plan): a closed grammar, the forms the tool writes (`design_limesurvey.expression`) and
nothing else. Terms in brackets, joined all by `and` or all by `or`, one level; each term one
of:

    (V.NAOK == "Y")                                   ticked
    (V.NAOK != "")                                    answered
    (V.NAOK != "" and V.NAOK OP VALUE)                =, ≠, <, ≤, >, ≥
    (V.NAOK != "" and (V.NAOK == A or V.NAOK == B))   among
    (V.NAOK != "" and V.NAOK != A and V.NAOK != B)    not among

a choice's code between quotes, a number bare; V a code of the questionnaire. "1" and the
empty expression mean "always asked". Any other expression (a function, nested brackets, a
brace, an unknown code, a value of the wrong kind) is refused with its reason, never guessed.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from ddict.project.model import Condition, Term

# A target as the questionnaire names it: its id, the nature of `skip.OPERATORS`, the codes
# of its choices (a choice's).
Named = tuple[str, str, frozenset[str]]

_TOKEN = re.compile(
    r"\s*(?:(?P<name>[A-Za-z][A-Za-z0-9_]*)\.NAOK\b|(?P<word>and|or)\b|(?P<op>==|!=|<=|>=|<|>)"
    r'|(?P<text>"[^"\\]*")|(?P<number>-?\d+(?:\.\d+)?)(?![\w.])|(?P<open>\()|(?P<close>\)))'
)
_OPERATORS = {"==": "eq", "!=": "ne", "<": "lt", "<=": "le", ">": "gt", ">=": "ge"}


class Unread(ValueError):
    """An expression outside the grammar: the reason, for the person."""


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str


def _tokens(expression: str) -> list[_Token]:
    found, at = [], 0
    while at < len(expression):
        if expression[at:].strip() == "":
            break
        match = _TOKEN.match(expression, at)
        if match is None or match.end() == at:
            raise Unread(f"not read from: {expression[at:].strip()[:30]}")
        kind = match.lastgroup or ""
        found.append(_Token(kind, match.group(kind)))
        at = match.end()
    return found


def _groups(tokens: list[_Token]) -> tuple[list[list[_Token]], str | None]:
    """The terms in brackets at the top level, and the word joining them."""
    groups, joiner, at = [], None, 0
    while at < len(tokens):
        if tokens[at].kind != "open":
            raise Unread("a term must be in brackets")
        depth, end = 0, at
        while end < len(tokens):
            depth += {"open": 1, "close": -1}.get(tokens[end].kind, 0)
            if depth == 0:
                break
            end += 1
        if depth != 0:
            raise Unread("a bracket is not closed")
        groups.append(tokens[at + 1 : end])
        at = end + 1
        if at < len(tokens):
            word = tokens[at]
            if word.kind != "word" or (joiner is not None and word.value != joiner):
                raise Unread("terms joined both by and and by or")
            joiner = word.value
            at += 1
            if at == len(tokens):
                raise Unread("the expression ends with and or or")
    return groups, joiner


def _shape(tokens: list[_Token]) -> str:
    """The tokens as letters, to match the forms: n name, o operator, t text, d number, w
    word, ( and )."""
    letters = {"name": "n", "op": "o", "text": "t", "number": "d", "word": "w"}
    return "".join(letters.get(t.kind, t.value) for t in tokens)


def _value(token: _Token, nature: str, codes: frozenset[str], name: str):
    if nature == "choice":
        if token.kind != "text":
            raise Unread(f"{name}: a choice's code is written between quotes")
        code = token.value[1:-1]
        if code not in codes:
            raise Unread(f"{name}: {code} is not one of its codes")
        return code
    if nature == "number" and token.kind == "number":
        number = float(token.value)
        return int(number) if number.is_integer() else number
    raise Unread(f"{name}: a number is written without quotes")


def _term(tokens: list[_Token], names: Mapping[str, Named]) -> Term:
    shape = _shape(tokens)
    if not tokens or tokens[0].kind != "name":
        raise Unread("a term starts with a code")
    name = tokens[0].value
    found = names.get(name)
    if found is None:
        raise Unread(f"unknown code: {name}")
    target, nature, codes = found
    if any(t.kind == "name" and t.value != name for t in tokens):
        raise Unread(f"a term names one code only ({name})")
    empty = tokens[1].value == "!=" and tokens[2].value == '""' if len(tokens) > 2 else False
    if shape == "not" and tokens[1].value == "==" and tokens[2].value == '"Y"':
        if nature != "box":
            raise Unread(f"{name}: only an option is ticked")
        return Term(target=target, operator="checked")
    if shape == "not" and empty:
        if nature == "box":
            raise Unread(f"{name}: an option is ticked, not answered")
        return Term(target=target, operator="answered")
    if not empty or nature not in ("choice", "number"):
        raise Unread(f"{name}: not a form the tool writes")
    rest = tokens[4:]
    if tokens[3].kind != "word" or tokens[3].value != "and":
        raise Unread(f"{name}: not a form the tool writes")
    if _shape(rest) in ("not", "nod"):
        operator = _OPERATORS[rest[1].value]
        if nature == "choice" and operator not in ("eq", "ne"):
            raise Unread(f"{name}: a choice is not compared by order")
        return Term(target=target, operator=operator, value=_value(rest[2], nature, codes, name))
    inner = _shape(rest)
    if nature == "choice" and re.fullmatch(r"\(not(?:wnot)+\)", inner):
        alternatives = rest[1:-1]
        if any(w.value != "or" for w in alternatives[3::4]) or any(
            o.value != "==" for o in alternatives[1::4]
        ):
            raise Unread(f"{name}: not a form the tool writes")
        values = [_value(t, nature, codes, name) for t in alternatives[2::4]]
        return Term(target=target, operator="in", value=values)
    if nature == "choice" and re.fullmatch(r"not(?:wnot)+", inner):
        if any(w.value != "and" for w in rest[3::4]) or any(o.value != "!=" for o in rest[1::4]):
            raise Unread(f"{name}: not a form the tool writes")
        values = [_value(t, nature, codes, name) for t in rest[2::4]]
        return Term(target=target, operator="not_in", value=values)
    raise Unread(f"{name}: not a form the tool writes")


def parse(expression: str | None, names: Mapping[str, Named]) -> Condition | None:
    """The condition an expression says; None for "always" ("1", empty). Raises Unread."""
    text = (expression or "").strip()
    if text in ("", "1"):
        return None
    if "{" in text or "}" in text:
        raise Unread("a brace")
    groups, joiner = _groups(_tokens(text))
    if len(groups) > 10:
        raise Unread("more than 10 terms")
    terms = [_term(group, names) for group in groups]
    return Condition(combine="any" if joiner == "or" else "all", terms=terms)


def canonical(condition: Condition | None) -> tuple | None:
    """A condition as a comparison sees it: "among" one code is "=", "not among" one code is
    "≠" (the file writes them the same), the terms in their order."""
    if condition is None:
        return None
    terms = []
    for term in condition.terms:
        operator, value = term.operator, term.value
        if operator in ("in", "not_in") and isinstance(value, list) and len(value) == 1:
            operator, value = ("eq" if operator == "in" else "ne"), value[0]
        if isinstance(value, list):
            value = tuple(str(v) for v in value)
        elif value is not None:
            value = str(value)
        terms.append((term.target, operator, value))
    combine = condition.combine if len(terms) > 1 else "all"
    return (combine, tuple(terms))
