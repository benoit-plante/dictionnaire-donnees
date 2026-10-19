"""The data ready for an analysis (v0.9, step 3, D-070): the database read in memory, with
the team's accepted decisions applied in the order of the command files and the
preparation script (D-062): missing codes removed (declared in the file or confirmed by the
team), final names, reversed items (`<item>_inv`), scores of the structured scorings,
since v0.15 the recodings (D-120), and since v0.12 the exclusion rules (D-094): only the
people they keep are analysed.

The original file is never changed, and nothing of the data is written in the project
(principle 2): the table lives in memory for the time of an analysis.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ddict.analysis import exclusions
from ddict.export import wording as w
from ddict.export.preparation import plan
from ddict.io import read_database
from ddict.io.sav import file_sha256
from ddict.project.model import Project, VariableEntry


class DataError(Exception):
    """The database cannot be prepared; `reason`: "not_found", "other_file", "no_base"."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(reason, detail)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class PreparedData:
    table: pd.DataFrame  # columns: final names, then new variables (`_inv`, scores, recodings)
    scores: dict[str, str]  # score name -> group id
    reversed: dict[str, str]  # new variable -> final name of the item
    flow: exclusions.Flow | None = None  # v0.12: who the exclusion rules kept


def code_key(code) -> str:
    """A code inside a statistic's key: "1", "2p5" for 2.5, "m9" for −9; a text code with
    "s" before it and "_" for each sign other than an ASCII letter or digit ("sin_service")."""
    if isinstance(code, str):
        return "s" + re.sub(r"[^0-9A-Za-z]", "_", code)
    value = float(code)
    text = str(int(value)) if value.is_integer() else repr(value)
    return text.replace("-", "m").replace(".", "p")


def level_codes(text: str) -> list:
    """The codes of a "levels" option without the data: a number where it reads as one,
    else the text code as it is."""
    found: list = []
    for part in str(text).split(","):
        try:
            found.append(float(part.strip()))
        except ValueError:
            found.append(part.strip())
    return found


def chosen_levels(text: str, column: pd.Series) -> list:
    """The codes of a t test's "levels" option ("1,3"; "non,oui" for a text variable), typed
    as the column holds them."""
    parts = [part.strip() for part in str(text).split(",")]
    if column.dtype == object:
        return parts
    return [float(part) for part in parts]


def subset_values(texts: list[str], column: pd.Series) -> list:
    """The values of a subgroup as typed ("1", "Femme"), typed as the column holds them.
    Raises ValueError for a word where the column holds numbers."""
    if column.dtype == object:
        return [t.strip() for t in texts]
    return [float(t.replace(",", ".")) for t in texts]


def subset_mask(table: pd.DataFrame, subset) -> pd.Series:
    """Who is in a subgroup (v0.14, D-113): as an exclusion condition, a missing value never
    meets it."""
    column = table[subset.name]
    present = ~exclusions.blank(column)
    if subset.operator == "in":
        return present & column.isin(list(subset.value))
    compare = {
        "eq": lambda c: c == subset.value,
        "ne": lambda c: c != subset.value,
        "lt": lambda c: c < subset.value,
        "le": lambda c: c <= subset.value,
        "gt": lambda c: c > subset.value,
        "ge": lambda c: c >= subset.value,
    }[subset.operator]
    return present & compare(column).fillna(False).astype(bool)


def apply_subset(prepared: PreparedData, subset) -> PreparedData:
    """The data of a subgroup only, after the exclusion rules; the flow does not change."""
    kept = prepared.table[subset_mask(prepared.table, subset)].reset_index(drop=True)
    return PreparedData(kept, prepared.scores, prepared.reversed, prepared.flow)


def find_database(project: Project, project_path: Path, given: Path | None = None) -> Path:
    """The database the project was made from: the given file, or the one of the same name
    next to the project; its fingerprint must be the project's. A project without a database
    yet (v0.20) has none to find."""
    if project.source is None:
        raise DataError("no_base")
    path = Path(given) if given else project_path.with_name(project.source.name)
    if not path.is_file():
        raise DataError("not_found", str(path))
    if file_sha256(path) != project.source.sha256:
        raise DataError("other_file", str(path))
    return path


def _missing_codes(entry: VariableEntry) -> tuple[set, list[tuple]]:
    singles = {m.low for m in entry.file.declared_missing if m.low == m.high}
    singles |= set(w.confirmed_missing(entry))
    ranges = [(m.low, m.high) for m in entry.file.declared_missing if m.low != m.high]
    return singles, ranges


def _without_missing(column: pd.Series, entry: VariableEntry) -> pd.Series:
    singles, ranges = _missing_codes(entry)
    if not singles and not ranges:
        return column
    missing = column.isin(singles)
    numeric = pd.to_numeric(column, errors="coerce")
    for low, high in ranges:
        missing |= (numeric >= low) & (numeric <= high)
    return column.mask(missing)


def decided(project: Project, table: pd.DataFrame) -> tuple[pd.DataFrame, list, dict]:
    """The decisions before the exclusion rules: the table with its final names, missing
    codes removed, reversed items, scores and recodings; the reversals and the scores."""
    from ddict.analysis import recode

    names = w.names_of(project)
    columns = {}
    for entry in project.variables:
        column = table[entry.name]
        # A date stays a date (the duration of an exclusion rule); it enters no analysis.
        if entry.file.storage_type == "numeric" and not pd.api.types.is_datetime64_any_dtype(
            column
        ):
            column = pd.to_numeric(column, errors="coerce")
        elif column.dtype == object:
            column = column.mask(exclusions.blank(column))  # an empty text is missing, as profiled
        columns[names[entry.name]] = _without_missing(column, entry).reset_index(drop=True)
    data = pd.DataFrame(columns)
    reversals, scores, _notes = plan(project)
    for item in reversals:
        data[item.new] = item.total - data[item.name]
    found_scores = {}
    for score in scores:
        items = data[score.items]
        answered = items.notna().sum(axis=1)
        if score.aggregation == "mean":
            value = items.mean(axis=1)
        elif score.prorate:
            value = items.mean(axis=1) * len(score.items)
        else:
            value = items.sum(axis=1, min_count=1)
        data[score.name] = value.where(answered >= score.least, np.nan)
        found_scores[score.name] = score.group
    recode.apply(project, data)
    return data, reversals, found_scores


def apply_decisions(project: Project, table: pd.DataFrame) -> PreparedData:
    """The accepted decisions applied to a table read from the database."""
    data, reversals, found_scores = decided(project, table)
    rank = exclusions.ranks(project, data)
    kept = data[rank == 0].reset_index(drop=True)
    return PreparedData(
        kept,
        found_scores,
        {r.new: r.name for r in reversals},
        exclusions.flow(project, rank) if project.exclusions.rules else None,
    )


def prepare(project: Project, project_path: Path, given: Path | None = None) -> PreparedData:
    """Read the database next to the project and apply the accepted decisions."""
    path = find_database(project, project_path, given)
    return apply_decisions(project, read_database(path).table)
