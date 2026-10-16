"""The result of an analysis (v0.9, step 4), the same shape for every analysis, and the
conventions of its numbers (D-077): a decimal comma in French, two decimals for statistics,
three for p, p without a leading zero (APA style), 95 % confidence intervals.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ddict.i18n import _, decimal

MINUS = "−"


@dataclass(frozen=True)
class Table:
    title: str
    columns: list[str]
    rows: list[list[str]]


@dataclass
class AnalysisResult:
    analysis: str
    chosen: dict[str, list[str]]
    options: dict[str, str]
    n_used: int
    n_excluded: int
    tables: list[Table] = field(default_factory=list)
    statistics: dict[str, float] = field(default_factory=dict)  # raw values, for tests and R
    sentence: str = ""  # the result, APA style; it describes, it does not judge
    warnings: list[str] = field(default_factory=list)


def number(value: float | None, digits: int = 2) -> str:
    """A statistic as the language writes it: 0,18 ; −0,27 ; 1 234,50 is not used."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = f"{abs(value):.{digits}f}"
    if float(text) == 0:
        value = 0.0
    return (MINUS if value < 0 else "") + decimal(text)


def p_value(p: float) -> str:
    """APA style: no leading zero, three decimals, "< ,001" below a thousandth."""
    if p < 0.001:
        return f"< {decimal('.001')}"
    text = f"{p:.3f}"
    return decimal(text[1:] if text.startswith("0") else text)


def bounded(value: float | None, digits: int = 2) -> str:
    """A statistic that cannot exceed 1 (r, ρ, V, η², ω², ε², R²), without its leading
    zero, as APA writes it: ",07", "−,13" (v0.12: the sentences, like the tables)."""
    text = number(value, digits)
    sign = MINUS if text.startswith(MINUS) else ""
    body = text[len(sign) :]
    if body.startswith("0") and len(body) > 1 and not body[1].isdigit():
        body = body[1:]
    return sign + body


def bounded_interval(low: float, high: float, digits: int = 2) -> str:
    """ "IC 95 % [−,13 ; ,15]": the interval of a correlation, without leading zeros."""
    return _("IC 95 % [{low} ; {high}]").format(
        low=bounded(low, digits), high=bounded(high, digits)
    )


def p_part(p: float) -> str:
    """ "p = ,861" or "p < ,001"."""
    shown = p_value(p)
    return f"p {shown}" if shown.startswith("<") else f"p = {shown}"


def interval(low: float, high: float, digits: int = 2) -> str:
    """ "IC 95 % [−0,27 ; 0,32]" in French, "95% CI [−0.27, 0.32]" in English."""
    return _("IC 95 % [{low} ; {high}]").format(low=number(low, digits), high=number(high, digits))


def count_percent(count: int, total: int) -> str:
    share = 100 * count / total if total else 0.0
    return f"{count} ({number(share, 1)} %)"
