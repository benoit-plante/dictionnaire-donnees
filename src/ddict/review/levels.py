"""The measure levels on the "Base" page (v0.8, step 3, D-063), without Streamlit.

The rules propose (`ddict.project.measure`); a person decides in a table, as for the names
(D-056): "accept" or "reject" a proposal, or choose another level, which is then decided.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ddict.export import wording as w
from ddict.i18n import N_, Texts, _
from ddict.project import aside, measure
from ddict.project.decisions import correct, enter, reject, validate
from ddict.project.model import Project
from ddict.review.logic import ReviewError

LevelFilter = Literal["proposed", "all"]
FILTERS = Texts({"proposed": N_("Proposés"), "all": N_("Toutes")})
DECISIONS = Texts({"accept": N_("Accepter"), "reject": N_("Rejeter")})


@dataclass(frozen=True)
class LevelRow:
    """A line of the table of measure levels."""

    name: str
    label: str
    kind: str  # the type found by the profile
    file_level: str  # as the file says, shown
    level: str  # "nominal", "ordinal", "scale" or "": the proposal, or the level in force
    status: str
    waiting: bool  # a proposal: "Accept" can apply


def rows(project: Project, which: LevelFilter = "proposed") -> list[LevelRow]:
    found = []
    for entry in aside.kept(project):
        tracked = entry.measure_level
        waiting = tracked.status == "proposed"
        if which == "proposed" and not waiting:
            continue
        shown = tracked.value if waiting else measure.level(entry)
        found.append(
            LevelRow(
                name=w.final_name(entry),
                label=w.label_text(entry, "final"),
                kind=w.TYPES.get(entry.data_type, entry.data_type),
                file_level=w.MEASURES.get(entry.file.measure_level or "", ""),
                level=shown or "",
                status=w.status_text(tracked) if tracked.value else _("du fichier"),
                waiting=waiting,
            )
        )
    return found


def _entry_named(project: Project, shown_name: str):
    for entry in aside.kept(project):
        if w.final_name(entry) == shown_name:
            return entry
    raise KeyError(shown_name)


def apply_table(
    project: Project, levels: dict[str, str], decisions: dict[str, str], *, now: str
) -> int:
    """What a person did in the table: levels chosen (by the name shown), and "accept" or
    "reject" on proposals. A level chosen is a decision already; "reject" with it is
    contradictory. Everything is checked before anything changes. Returns the count."""
    chosen = {}
    for name, value in levels.items():
        entry = _entry_named(project, name)
        if value not in measure.LEVELS:
            raise ReviewError(_("{name} : niveau de mesure inconnu.").format(name=name))
        current = entry.measure_level.value if entry.measure_level.value else measure.level(entry)
        if value != current:
            chosen[name] = value
    both = sorted(n for n in chosen if decisions.get(n) == "reject")
    if both:
        raise ReviewError(
            _("{names} : niveau modifié et « Rejeter » choisi ; gardez l'un ou l'autre.").format(
                names=", ".join(both)
            )
        )
    actions = {n: a for n, a in decisions.items() if a and n not in chosen}
    done = sorted(n for n in actions if _entry_named(project, n).measure_level.status != "proposed")
    if done:
        raise ReviewError(
            _("Ces niveaux n'attendent plus de décision : {names}.").format(names=", ".join(done))
        )
    for name, value in chosen.items():
        entry = _entry_named(project, name)
        tracked = entry.measure_level
        if tracked.origin == "human":
            entry.measure_level = enter(tracked, value, now=now)
        else:
            entry.measure_level = correct(tracked, value, now=now)
    for name, action in actions.items():
        entry = _entry_named(project, name)
        decide = validate if action == "accept" else reject
        entry.measure_level = decide(entry.measure_level, now=now)
    return len(chosen) + len(actions)


def accept_shown(project: Project, name: str, shown: str, *, now: str) -> None:
    """Accept the level shown on the variable's page (v0.16, D-121), by its original name:
    the proposed one, validated; another, chosen as a correction."""
    entry = project.variable(name)
    if entry.measure_level.status != "proposed":
        raise ReviewError(_("Ce niveau n'attend plus de décision."))
    apply_table(project, {w.final_name(entry): shown}, {w.final_name(entry): "accept"}, now=now)


def waiting(project: Project) -> int:
    return sum(1 for e in aside.kept(project) if e.measure_level.status == "proposed")
