"""The signals of the quality of administration (v0.12, step 5, D-095): durations, grids
answered in a straight line, duplicates. Computed by rules, among the people the exclusion
rules in force keep, and shown with their counts; never applied alone: a signal becomes an
exclusion when the team adds it as a rule. No threshold of duration is ever given by the
tool: the count under a threshold exists only for the threshold the team typed.

Only aggregates leave this module: counts, a median and two percentiles of the durations;
never a duration, a date or a value of a person.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ddict.analysis.data import PreparedData
from ddict.analysis.exclusions import blank, seconds
from ddict.export import wording as w
from ddict.platforms import by_name
from ddict.profile.compute import text_datetime_format
from ddict.project.exclusions import MIN_GRID, NAMING, members
from ddict.project.model import Project

DUPLICATE_ROLES = ("respondent_id", "email", "ip_address")


@dataclass(frozen=True)
class Durations:
    start: str  # original names
    end: str
    text_format: str | None  # None: dates in the file; else how their text is read
    n: int  # the people with both dates and a duration of zero or more
    invalid: int  # a date missing or unreadable, or the end before the start
    median: float | None  # seconds
    p5: float | None
    p10: float | None


@dataclass(frozen=True)
class Grid:
    group: str
    label: str
    items: int
    count: int  # every item answered, all with the same value


@dataclass(frozen=True)
class Duplicates:
    variables: tuple[str, ...]
    count: int  # later answers that repeat an earlier one


def date_variables(project: Project) -> list[str]:
    """The variables that hold a date and a time (original names)."""
    return [e.name for e in project.variables if e.profile.inferred_type == "datetime"]


def _roles(project: Project) -> dict[str, str]:
    """Role of a platform's variable -> its original name."""
    platform = by_name(project.source.platform)
    if platform is None:
        return {}
    found = {}
    for entry in project.variables:
        variable = platform.platform_variable(entry.name)
        if variable is not None:
            found.setdefault(variable.role, entry.name)
    return found


def proposed_dates(project: Project) -> tuple[str, str] | None:
    """The start and the end of an administration, as a platform names them."""
    roles = _roles(project)
    if "start_date" in roles and "end_date" in roles:
        return roles["start_date"], roles["end_date"]
    return None


def text_format(project: Project, prepared: PreparedData, start: str, end: str) -> str | None:
    """How to read two date variables: None for dates of the file, else the format of
    their text; ValueError when their texts are not dates of one format."""
    names = w.names_of(project)
    columns = [prepared.table[names[n]] for n in (start, end)]
    if all(pd.api.types.is_datetime64_any_dtype(c) for c in columns):
        return None
    texts = [str(v) for c in columns for v in c.dropna() if str(v).strip()]
    found = text_datetime_format(texts)
    if found is None:
        raise ValueError((start, end))
    return found


def durations(project: Project, prepared: PreparedData, start: str, end: str) -> Durations:
    names = w.names_of(project)
    found = text_format(project, prepared, start, end)
    span = seconds(prepared.table, names[start], names[end], found)
    valid = span[span >= 0]

    def quantile(q: float) -> float | None:
        return float(valid.quantile(q)) if len(valid) else None

    return Durations(
        start, end, found, len(valid), int(len(span) - len(valid)),
        quantile(0.5), quantile(0.05), quantile(0.10),
    )  # fmt: skip


def below(project: Project, prepared: PreparedData, found: Durations, threshold: float) -> int:
    """How many people took less than the team's threshold (seconds)."""
    names = w.names_of(project)
    span = seconds(prepared.table, names[found.start], names[found.end], found.text_format)
    return int(((span >= 0) & (span < threshold)).sum())


def grids(project: Project, prepared: PreparedData) -> list[Grid]:
    """For each grid of at least 4 items, who answered every item with the same value."""
    names = w.names_of(project)
    found = []
    for group in project.groups:
        items = members(group)
        if group.kind != "scale" or len(items) < MIN_GRID:
            continue
        table = prepared.table[[names[n] for n in items]]
        count = int((table.notna().all(axis=1) & (table.nunique(axis=1) == 1)).sum())
        label = group.descriptive_label.value or group.group_id
        found.append(Grid(group.group_id, label, len(items), count))
    return found


def duplicate_variables(project: Project) -> list[str]:
    """The variables that may say a person answered twice (original names): a platform's
    respondent, e-mail address and IP address; without a platform, the likely identifiers."""
    roles = _roles(project)
    if roles:
        return [roles[r] for r in DUPLICATE_ROLES if r in roles]
    return [e.name for e in project.variables if e.privacy.privacy_class.value == NAMING[0]]


def duplicates(project: Project, prepared: PreparedData, variables: list[str]) -> Duplicates:
    names = w.names_of(project)
    columns = [names[n] for n in variables]
    data = prepared.table
    complete = ~pd.concat([blank(data[c]) for c in columns], axis=1).any(axis=1)
    count = int(data.loc[complete, columns].duplicated(keep="first").sum())
    return Duplicates(tuple(variables), count)
