"""The exclusion rules applied to the data (v0.12, D-094): in their rank, after the missing
codes, the names, the reversed items and the scores; a person is counted by the first rule
that excludes them only. The preparation scripts of SPSS and R do the same
(`ddict.export.preparation`).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ddict.export import wording as w
from ddict.project.exclusions import members
from ddict.project.model import (
    CompletenessRule,
    ConditionRule,
    DurationRule,
    ExclusionRule,
    Project,
    StraightliningRule,
)


@dataclass(frozen=True)
class Flow:
    """The people of the database, those each rule excluded in its rank, those analysed."""

    start: int
    excluded: tuple[tuple[str, int], ...]  # (rule id, count), in rank
    analysed: int


def _score_names(project: Project) -> dict[str, str]:
    from ddict.export.preparation import plan

    return {score.group: score.name for score in plan(project)[1]}


def _blank(column: pd.Series) -> pd.Series:
    """Missing, or an empty text."""
    missing = column.isna()
    if column.dtype == object or pd.api.types.is_string_dtype(column):
        missing |= column.astype("string").str.strip().fillna("") == ""
    return missing


def _same_type(column: pd.Series, value):
    if pd.api.types.is_numeric_dtype(column) and isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return value
    return value


def _condition(column: pd.Series, rule: ConditionRule) -> pd.Series:
    if rule.operator == "missing":
        return _blank(column)
    if rule.operator == "in":
        return column.isin([_same_type(column, v) for v in rule.value])
    value = _same_type(column, rule.value)
    present = ~_blank(column)
    compare = {
        "eq": lambda c: c == value,
        "ne": lambda c: c != value,
        "lt": lambda c: c < value,
        "le": lambda c: c <= value,
        "gt": lambda c: c > value,
        "ge": lambda c: c >= value,
    }[rule.operator]
    return present & compare(column).fillna(False).astype(bool)


def hits(project: Project, data: pd.DataFrame, rule: ExclusionRule) -> pd.Series:
    """The rows a rule excludes on its own, on the table with the decisions applied."""
    names = w.names_of(project)
    if isinstance(rule, ConditionRule):
        name = _score_names(project)[rule.score] if rule.score else names[rule.variable]
        found = _condition(data[name], rule)
    elif isinstance(rule, CompletenessRule):
        items = [names[n] for n in members(_group(project, rule.group))]
        found = data[items].notna().sum(axis=1) < rule.min_answered
    elif isinstance(rule, DurationRule):
        seconds = (data[names[rule.end]] - data[names[rule.start]]).dt.total_seconds()
        found = (seconds >= 0) & (seconds < rule.min_seconds)
    elif isinstance(rule, StraightliningRule):
        items = data[[names[n] for n in members(_group(project, rule.group))]]
        found = items.notna().all(axis=1) & (items.nunique(axis=1) == 1)
    else:  # DuplicateRule
        columns = [names[n] for n in rule.variables]
        complete = ~pd.concat([_blank(data[c]) for c in columns], axis=1).any(axis=1)
        repeated = data.loc[complete, columns].duplicated(keep="first")
        found = repeated.reindex(data.index, fill_value=False)
    return pd.Series(np.asarray(found, dtype=bool), index=data.index)


def _group(project: Project, group_id: str):
    return next(g for g in project.groups if g.group_id == group_id)


def ranks(project: Project, data: pd.DataFrame) -> pd.Series:
    """For each row, 0 when kept, otherwise the rank (1, 2...) of the first rule that
    excludes it: `ddict_exclusion` in the scripts."""
    rank = pd.Series(0, index=data.index, dtype=int)
    for number, rule in enumerate(project.exclusions.rules, start=1):
        rank = rank.mask((rank == 0) & hits(project, data, rule), number)
    return rank


def flow(project: Project, rank: pd.Series) -> Flow:
    rules = project.exclusions.rules
    excluded = tuple((r.id, int((rank == n).sum())) for n, r in enumerate(rules, start=1))
    return Flow(len(rank), excluded, int((rank == 0).sum()))
