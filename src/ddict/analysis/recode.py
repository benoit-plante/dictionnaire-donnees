"""The recodings applied to the data (v0.15, D-120): each new column computed in memory, after
the scores and before the exclusion rules, in the order of the project; and, before a
recoding is kept, what the data says of it: a source value without a group refuses it, an
empty class or a category under 5 people warns, and the count of each new category is
shown. Nothing of the data is written in the project.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ddict.export import wording as w
from ddict.i18n import _
from ddict.project.model import ClassesRecode, GroupsRecode, Project, Recode
from ddict.project.recodes import source_name

SMALL = 5  # below it, a category warns (D-006)


@dataclass
class Checked:
    """What the data says of a recoding: refusals, warnings, and (label, count) for each new
    category, in the order of their codes."""

    refusals: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    counts: list[tuple[str, int]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.refusals


def _typed(value, column: pd.Series):
    """A source value as the column holds it: a number for a numeric column."""
    if column.dtype != object:
        try:
            return float(value)
        except (TypeError, ValueError):
            return value
    return value if isinstance(value, str) else w.code_text(value)


def column(rule: Recode, source: pd.Series) -> pd.Series:
    """The new column, codes as numbers (1, 2…), missing where the source is missing, or for
    a value declared missing or left without a group."""
    if isinstance(rule, ClassesRecode):
        values = pd.to_numeric(source, errors="coerce")
        codes = np.searchsorted(np.asarray(rule.cuts, dtype=float), values, side="right") + 1
        return pd.Series(np.where(values.isna(), np.nan, codes), index=source.index, dtype=float)
    result = pd.Series(np.nan, index=source.index, dtype=float)
    for group in rule.groups:
        result[source.isin([_typed(v, source) for v in group.values])] = float(group.code)
    return result


def labels(rule: Recode) -> dict[float, str]:
    """The value labels of the new variable, by code."""
    if isinstance(rule, ClassesRecode):
        return {float(i + 1): label for i, label in enumerate(rule.labels)}
    return {float(g.code): g.label for g in rule.groups}


def apply(project: Project, data: pd.DataFrame) -> None:
    """Add the recoded columns to the data, in the order of the project. A recoding whose
    source leads nowhere any more is left out: what uses it then says so."""
    for rule in project.recodes.rules:
        name = source_name(project, rule.source)
        if name is not None and name in data:
            data[rule.name] = column(rule, data[name])


def check(project: Project, rule: Recode, data: pd.DataFrame, book_labels: dict) -> Checked:
    """A recoding on the data before the exclusion rules: every observed value has a place,
    the counts of the new categories. `book_labels`: the value labels of the source."""
    found = Checked()
    name = source_name(project, rule.source)
    if name is None or name not in data:
        found.refusals.append(_("{name} : variable absente de la base.").format(name=name))
        return found
    source = data[name]
    if isinstance(rule, GroupsRecode):
        placed = {_typed(v, source) for g in rule.groups for v in g.values}
        placed |= {_typed(v, source) for v in rule.missing_values}
        observed = source.dropna()
        left = observed[~observed.isin(list(placed))]
        if len(left):
            counts = left.value_counts(sort=False).sort_index()
            shown = [
                _("{value} ({label}, {n} personnes)").format(
                    value=w.code_text(code), label=book_labels[code], n=int(n)
                )
                if code in book_labels
                else _("{value} ({n} personnes)").format(value=w.code_text(code), n=int(n))
                for code, n in counts.items()
            ]
            found.refusals.append(
                _(
                    "Valeurs sans groupe : {values}. Mettez-les dans un groupe, ou déclarez-les "
                    "manquantes."
                ).format(values=", ".join(shown))
            )
    new = column(rule, source)
    for code, label in labels(rule).items():
        n = int((new == code).sum())
        found.counts.append((label, n))
        if n == 0:
            found.warnings.append(_("Classe vide : {label}.").format(label=label))
        elif n < SMALL:
            found.warnings.append(
                _("Moins de {small} personnes : {label} ({n}).").format(
                    small=SMALL, label=label, n=n
                )
            )
    return found
