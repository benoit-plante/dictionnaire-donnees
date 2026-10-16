"""Recompute the notebook's analyses and say what changed (v0.11, step 3, D-089; the sheet
`docs/carnet-analyses.md`, § 5 and 6).

Each entry is in one state: current (the same codebook fingerprint as its last confirmed
computation); unchanged (the fingerprint changed but every statistic is the same: the
fingerprint and the date are brought up to date, and the tool says so); changed (a
statistic or a count differs: the new computation waits in `pending` until a person
confirms it); impossible (a variable's key leads nowhere, or the conditions of the codebook
refuse the analysis: said with its reason, never removed); no database (the database is
missing or is another one: nothing is recomputed, the notebook stays readable).

A retained entry that changed and is not confirmed blocks the export: no number changes in
a document without a person having seen it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from ddict.analysis import notebook as nb
from ddict.analysis.apa import apa
from ddict.analysis.compute import AnalysisRefused, run
from ddict.analysis.data import PreparedData
from ddict.analysis.results import AnalysisResult
from ddict.i18n import _
from ddict.project import fingerprint
from ddict.project.model import Project

State = Literal["current", "unchanged", "changed", "impossible", "no_database"]
RELATIVE = 1e-9  # "nothing changed" below this relative difference (the sheet, § 8)
ABSOLUTE = 1e-12
MAX_DIGITS = 10


@dataclass(frozen=True)
class Difference:
    """A statistic before and after, as the APA shows it; with more decimals when the APA's
    would show the same number on both sides."""

    key: str
    before: float | None
    after: float | None
    shown_before: str
    shown_after: str


@dataclass(frozen=True)
class Status:
    entry_id: str
    state: State
    reason: str = ""
    differences: tuple[Difference, ...] = ()
    result: AnalysisResult | None = None  # the analysis recomputed, when it was


def _same(a: float, b: float) -> bool:
    return abs(a - b) <= max(ABSOLUTE, RELATIVE * max(abs(a), abs(b)))


def _digits(key: str) -> int:
    """Three decimals for a p, two for the rest, none for a count."""
    if key in ("n", "n_used", "n_excluded", "n1", "n2", "df1", "df2") or key.startswith("n_"):
        return 0
    if key == "p" or key.startswith(("p_", "tukey_p_", "fisher_p", "levene_p", "shapiro_p")):
        return 3
    return 2


NO_ZERO = {"r", "p", "V", "rb", "r2", "r2adj", "eta2", "omega2", "epsilon2", "ci_low", "ci_high"}
NO_ZERO_STARTS = ("p_", "r_", "beta_", "levene_p", "shapiro_p", "fisher_p", "tukey_p_")


def _zero(key: str) -> bool:
    """APA: no leading zero for what cannot exceed 1 (r, p, β, η², V… and the interval of
    a correlation, `low_2_1`); a leading zero for the rest (b and its interval, `low_1`)."""
    pair_bound = key.startswith(("low_", "high_")) and key.count("_") == 2
    return not (key in NO_ZERO or key.startswith(NO_ZERO_STARTS) or pair_bound)


def _shown(value: float | None, digits: int, zero: bool = True) -> str:
    return "—" if value is None else apa(value, digits, zero)


def _difference(key: str, before: float | None, after: float | None) -> Difference:
    digits, zero = _digits(key), _zero(key)
    while (
        before is not None
        and after is not None
        and _shown(before, digits, zero) == _shown(after, digits, zero)
        and digits < MAX_DIGITS
    ):
        digits += 1
    return Difference(key, before, after, _shown(before, digits, zero), _shown(after, digits, zero))


def differences(before: nb.Computed, after: nb.Computed) -> tuple[Difference, ...]:
    """What differs between two computations: the counts, then each statistic both have (a
    key only one side has, added by another version of the tool, is not a difference)."""
    found = []
    for key in ("n_used", "n_excluded"):
        a, b = float(getattr(before, key)), float(getattr(after, key))
        if not _same(a, b):
            found.append(_difference(key, a, b))
    for key in sorted(set(before.statistics) & set(after.statistics)):
        a, b = before.statistics[key], after.statistics[key]
        if not (math.isfinite(a) and math.isfinite(b) and _same(a, b)):
            found.append(_difference(key, a, b))
    return tuple(found)


def recompute(project: Project, prepared: PreparedData, entry: nb.Entry) -> AnalysisResult:
    """The entry's analysis on the database as it is now, with the decisions in force.
    Raises NotebookError (a key leads nowhere) or AnalysisRefused (the conditions refuse)."""
    chosen = nb.resolved(project, entry)
    return run(project, prepared, entry.analysis, chosen, dict(entry.options))


def check(
    project: Project,
    prepared: PreparedData | None,
    entry: nb.Entry,
    *,
    today: str,
    reason: str = "",
    always: bool = False,
) -> Status:
    """The state of an entry, and what to keep: an unchanged entry gets the new
    fingerprint and date; a changed one gets `pending`; a current one loses an old
    `pending` (a decision taken back). `always` recomputes a current entry too (an export
    never copies the notebook)."""
    if prepared is None:
        return Status(entry.id, "no_database", reason)
    current = fingerprint.fingerprint(project)
    if current == entry.computed.fingerprint and not always:
        entry.pending = None
        return Status(entry.id, "current")
    try:
        result = recompute(project, prepared, entry)
    except nb.NotebookError as error:
        return Status(entry.id, "impossible", nb.reason_text(error))
    except AnalysisRefused as error:
        return Status(entry.id, "impossible", " ".join(error.check.refusals))
    fresh = nb.computed(project, result, today)
    found = differences(entry.computed, fresh)
    if not found:
        entry.computed = entry.computed.model_copy(
            update={"fingerprint": fresh.fingerprint, "date": fresh.date}
        )
        entry.pending = None
        state: State = "current" if current == fresh.fingerprint and always else "unchanged"
        return Status(entry.id, state, result=result)
    entry.pending = fresh
    return Status(entry.id, "changed", differences=found, result=result)


def check_all(
    notebook: nb.Notebook,
    project: Project,
    prepared: PreparedData | None,
    *,
    today: str,
    reason: str = "",
    always: bool = False,
) -> list[Status]:
    """Every entry's state, in the notebook's order; the notebook is updated in memory,
    to be saved by the caller."""
    if prepared is not None and not nb.belongs(notebook, project):
        prepared, reason = None, _("Ce carnet a été fait avec une autre base que celle du projet.")
    return [
        check(project, prepared, entry, today=today, reason=reason, always=always)
        for entry in notebook.entries
    ]


def confirm(notebook: nb.Notebook, entry_id: str) -> None:
    """A person confirms the new computation: it replaces the statistics kept."""
    entry = nb.find(notebook, entry_id)
    if entry.pending is None:
        raise nb.NotebookError("nothing_pending", entry_id)
    entry.computed, entry.pending = entry.pending, None


def blocking(notebook: nb.Notebook, statuses: list[Status]) -> list[str]:
    """The retained entries whose change waits for a confirmation: they block the export."""
    retained = {e.id for e in notebook.entries if e.retained}
    return [s.entry_id for s in statuses if s.state == "changed" and s.entry_id in retained]
