"""The exclusion rules applied to the data (v0.12, D-094): in their rank, after the missing
codes, the names, the reversed items and the scores; a person is counted by the first rule
that excludes them only. The preparation scripts of SPSS and R do the same
(`ddict.export.preparation`).

Since v0.21 (D-167), with the mask of what was not asked: a question not asked never meets a
condition, not even "missing", which means "asked and left empty"; the completeness of a
group counts the items answered among those asked, and a person not asked the group is not
excluded by it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ddict.export import wording as w
from ddict.project.exclusions import members
from ddict.project.model import (
    AttentionRule,
    CompletenessRule,
    ConditionRule,
    DuplicateRule,
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


def blank(column: pd.Series) -> pd.Series:
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
        return blank(column)
    if rule.operator == "in":
        return column.isin([_same_type(column, v) for v in rule.value])
    value = _same_type(column, rule.value)
    present = ~blank(column)
    compare = {
        "eq": lambda c: c == value,
        "ne": lambda c: c != value,
        "lt": lambda c: c < value,
        "le": lambda c: c <= value,
        "gt": lambda c: c > value,
        "ge": lambda c: c >= value,
    }[rule.operator]
    return present & compare(column).fillna(False).astype(bool)


def moments(column: pd.Series, text_format: str | None) -> pd.Series:
    """A date variable as dates: as it is, or read from its text ("iso" or a format of the
    slashes); a text that does not fit is missing."""
    if text_format is None:
        return column
    texts = column.astype("string").str.strip()
    if text_format == "iso":
        return pd.to_datetime(texts, format="ISO8601", errors="coerce")
    return pd.to_datetime(texts, format=text_format, errors="coerce")


def seconds(data: pd.DataFrame, start: str, end: str, text_format: str | None) -> pd.Series:
    """The duration of each administration, in seconds (final names)."""
    return (moments(data[end], text_format) - moments(data[start], text_format)).dt.total_seconds()


def _asked(not_applicable: pd.DataFrame | None, name: str, index) -> pd.Series:
    """Whether each person was asked the variable (always, without a condition)."""
    if not_applicable is None or name not in not_applicable.columns:
        return pd.Series(True, index=index)
    return pd.Series(~not_applicable[name].to_numpy(), index=index)


def hits(
    project: Project,
    data: pd.DataFrame,
    rule: ExclusionRule,
    not_applicable: pd.DataFrame | None = None,
) -> pd.Series:
    """The rows a rule excludes on its own, on the table with the decisions applied; with
    the mask of what was not asked (v0.21)."""
    names = w.names_of(project)
    if isinstance(rule, ConditionRule):
        if rule.recode is not None:  # v0.15
            name = next(r.name for r in project.recodes.rules if r.id == rule.recode)
        else:
            name = _score_names(project)[rule.score] if rule.score else names[rule.variable]
        found = _condition(data[name], rule) & _asked(not_applicable, name, data.index)
    elif isinstance(rule, CompletenessRule):
        items = [names[n] for n in members(_group(project, rule.group))]
        asked = pd.concat([_asked(not_applicable, i, data.index) for i in items], axis=1)
        answered = (data[items].notna() & asked.to_numpy()).sum(axis=1)
        found = asked.any(axis=1) & (answered < rule.min_answered)
    elif isinstance(rule, DurationRule):
        span = seconds(data, names[rule.start], names[rule.end], rule.text_format)
        found = (span >= 0) & (span < rule.min_seconds)
    elif isinstance(rule, StraightliningRule):
        items = data[[names[n] for n in members(_group(project, rule.group))]]
        found = items.notna().all(axis=1) & (items.nunique(axis=1) == 1)
    elif isinstance(rule, DuplicateRule):
        columns = [names[n] for n in rule.variables]
        complete = ~pd.concat([blank(data[c]) for c in columns], axis=1).any(axis=1)
        repeated = data.loc[complete, columns].duplicated(keep="first")
        found = repeated.reindex(data.index, fill_value=False)
    elif isinstance(rule, AttentionRule):  # v0.21 (D-170)
        found = failures(project, data, rule, not_applicable) >= rule.min_failed
    else:
        raise ValueError(f"exclusion rule not computed: {rule.kind}")
    return pd.Series(np.asarray(found, dtype=bool), index=data.index)


def failures(
    project: Project,
    data: pd.DataFrame,
    rule: AttentionRule,
    not_applicable: pd.DataFrame | None = None,
) -> pd.Series:
    """How many attention checks each person failed (v0.21, D-170): asked, and answered
    otherwise than right; or left empty, when the rule counts the empty as a failure. A check
    not asked is never failed."""
    names = w.names_of(project)
    count = pd.Series(0, index=data.index, dtype=int)
    for check in rule.checks:
        name = names[check.variable]
        column = data[name]
        answered = ~blank(column)
        right = column.isin([_same_type(column, c) for c in check.correct])
        failed = answered & ~right
        if rule.empty == "failed":
            failed |= ~answered
        count += (failed & _asked(not_applicable, name, data.index)).astype(int)
    return count


def _group(project: Project, group_id: str):
    return next(g for g in project.groups if g.group_id == group_id)


def ranks(
    project: Project, data: pd.DataFrame, not_applicable: pd.DataFrame | None = None
) -> pd.Series:
    """For each row, 0 when kept, otherwise the rank (1, 2...) of the first rule that
    excludes it: `ddict_exclusion` in the scripts."""
    rank = pd.Series(0, index=data.index, dtype=int)
    for number, rule in enumerate(project.exclusions.rules, start=1):
        rank = rank.mask((rank == 0) & hits(project, data, rule, not_applicable), number)
    return rank


def flow(project: Project, rank: pd.Series) -> Flow:
    rules = project.exclusions.rules
    excluded = tuple((r.id, int((rank == n).sum())) for n, r in enumerate(rules, start=1))
    return Flow(len(rank), excluded, int((rank == 0).sum()))
