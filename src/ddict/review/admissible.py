"""Which variables fit a role of an analysis, first, and why the others do not (v0.16,
finding 22). Without Streamlit.

Only the order of a list and a reason beside each name: the check before the computation
(`conditions.check`) is the same as before, so no analysis becomes possible that was not.
The variables a role never takes (an identifier, a free text, a date: D-093) stay out.
"""

from __future__ import annotations

from dataclasses import dataclass

from ddict.analysis import conditions
from ddict.analysis.catalogue import CATALOGUE
from ddict.analysis.data import PreparedData
from ddict.export import wording as w
from ddict.i18n import _
from ddict.project.model import Project

# From the most to the least fitting; the last ones are refused by the check, as before.
FITS, WITH_A_CHOICE, LESS_SUITED, DOES_NOT_FIT = 0, 1, 2, 3
ORDINAL = "ordinal"


@dataclass(frozen=True)
class Fit:
    name: str  # the final name, as the analyses take it
    rank: int  # FITS, WITH_A_CHOICE, LESS_SUITED or DOES_NOT_FIT
    reason: str = ""  # empty when it fits


def _modalities(prepared: PreparedData | None, name: str) -> int | None:
    if prepared is None or name not in prepared.table.columns:
        return None
    return int(prepared.table[name].dropna().nunique())


def _fit(analysis_key: str, role, level: str | None, n: int | None, name: str) -> Fit:
    if level is None:
        return Fit(name, DOES_NOT_FIT, _("niveau de mesure non décidé"))
    if level not in role.levels:
        return Fit(name, DOES_NOT_FIT, _("niveau {level}").format(level=w.MEASURES[level]))
    if role.modalities is None:
        return Fit(name, FITS)
    found = _groups(analysis_key, role, n, name)
    if level == ORDINAL and found.rank != DOES_NOT_FIT:
        # Groups made of an ordered scale (a Likert item): allowed, rarely what is meant.
        reasons = [_("niveau ordinal"), *([found.reason] if found.reason else [])]
        return Fit(name, LESS_SUITED, " ; ".join(reasons))
    return found


def _groups(analysis_key: str, role, n: int | None, name: str) -> Fit:
    """A variable whose values make the groups: how many modalities it has."""
    if n is None:
        return Fit(name, FITS)
    low, high = role.modalities
    if analysis_key == "t_test":  # two groups compared: more may be narrowed to two
        if n == 2:
            return Fit(name, FITS)
        if n > 2:
            return Fit(name, WITH_A_CHOICE,
                       _("{n} modalités : choisir les deux comparées").format(n=n))  # fmt: skip
        return Fit(name, DOES_NOT_FIT, _("il faut deux modalités"))
    if n < low:
        return Fit(name, DOES_NOT_FIT,
                   _("{n} modalités ; il en faut au moins {low}").format(n=n, low=low))  # fmt: skip
    if n > high:
        return Fit(name, DOES_NOT_FIT,
                   _("{n} modalités ; au plus {high}").format(n=n, high=high))  # fmt: skip
    return Fit(name, FITS)


def ranked(
    project: Project, analysis_key: str, role_key: str, prepared: PreparedData | None
) -> list[Fit]:
    """The variables of a role: those that fit first, then those that fit with a choice,
    then the others; in the order of the codebook within each."""
    role = CATALOGUE[analysis_key].role(role_key)
    excluded = conditions.excluded(project)
    found = [
        _fit(analysis_key, role, level, _modalities(prepared, name), name)
        for name, level in conditions.levels(project).items()
        if name not in excluded
    ]
    return sorted(found, key=lambda fit: fit.rank)  # sorted() keeps the codebook's order
