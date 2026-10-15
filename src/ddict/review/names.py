"""The decisions of the "Names" page (v0.7), without Streamlit.

Each function takes the project and changes it; the page saves it. A refusal raises
ReviewError, with a message for a person. After any change of a rule (a prefix, a stem, the
wave mark), the rules propose again where nothing is decided.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ddict import naming, waves
from ddict.export import wording as w
from ddict.i18n import N_, Texts, _, colon
from ddict.io import ReadError
from ddict.project import ProjectError
from ddict.project.decisions import is_accepted
from ddict.project.model import Project, TrackedValue, VariableEntry
from ddict.questionnaire import link
from ddict.review.logic import ReviewError

MIN_LENGTH, MAX_LENGTH = 8, 64  # of the names, as the project's settings allow

NameFilter = Literal["all", "to_name", "proposed", "conflicts", "decided"]
FILTERS = Texts(
    {
        "all": N_("Toutes"),
        "to_name": N_("À nommer"),
        "proposed": N_("Proposés"),
        "conflicts": N_("En conflit"),
        "decided": N_("Décidés"),
    }
)
PROBLEMS = Texts(
    {
        "style": N_("minuscules, chiffres et « _ », en commençant par une lettre"),
        "length": N_("trop long"),
        "reserved": N_("mot réservé de SPSS"),
        "duplicate": N_("déjà le nom d'une autre variable"),
        "original_name": N_("nom d'origine d'une autre variable"),
    }
)


def problem_text(problems: list[str]) -> str:
    return ", ".join(PROBLEMS.get(p, p) for p in problems)


def _refused(error: naming.NamingError) -> ReviewError:
    return ReviewError(_("Nom refusé : {why}.").format(why=problem_text(error.problems)))


@dataclass(frozen=True)
class NameRow:
    """A line of the table of names."""

    name: str
    label: str
    question: str
    new_name: str
    origin: str
    status: str
    problem: str


def _question(project: Project, entry: VariableEntry, sure: dict[str, str]) -> str:
    target = entry.question.value if is_accepted(entry.question) else sure.get(entry.name)
    if not target or target == link.NO_QUESTION:
        return ""
    found = link.target(project.questionnaire, target)
    return f"{target}{colon()}{link.target_text(found)}" if found else target


def _selected(project: Project, entry: VariableEntry, which: NameFilter, clashes: set) -> bool:
    tracked = entry.new_name
    if which == "to_name":
        return not tracked.value
    if which == "proposed":
        return tracked.status == "proposed"
    if which == "conflicts":
        return entry.name in clashes
    if which == "decided":
        return bool(tracked.value) and tracked.status != "proposed"
    return True


def rows(project: Project, which: NameFilter = "all") -> list[NameRow]:
    """The table of names, filtered."""
    clashes = set(naming.conflicts(project))
    sure = link.sure_choices(project) if project.questionnaire else {}
    found = []
    for entry in project.variables:
        if not _selected(project, entry, which, clashes):
            continue
        tracked = entry.new_name
        problems = (
            naming.problems(project, entry.name, tracked.value)
            if tracked.value and tracked.status != "rejected"
            else []
        )
        found.append(
            NameRow(
                name=entry.name,
                label=w.label_text(entry, "final"),
                question=_question(project, entry, sure),
                new_name=tracked.value or "",
                origin=w.ORIGINS[tracked.origin] if tracked.value else "",
                status=w.status_text(tracked) if tracked.value else _("à nommer"),
                problem=problem_text(problems),
            )
        )
    return found


# --- One variable. ---


def decide(project: Project, name: str, action: str, *, now: str, value: str = "") -> None:
    """Accept, reject, or correct (write) a variable's new name."""
    try:
        naming.decide(project, name, action, now=now, value=value)
    except naming.NamingError as error:
        raise _refused(error) from error


def apply_edits(project: Project, edits: dict[str, str], *, now: str) -> int:
    """The names a person changed in the table: each a correction; an empty one withdraws
    the new name (the variable keeps its original name). Returns how many changed."""
    changed = 0
    for name, value in edits.items():
        entry = project.variable(name)
        text = (value or "").strip()
        if text == (entry.new_name.value or ""):
            continue
        if not text:
            entry.new_name = TrackedValue[str](origin="human", updated_at=now)
        else:
            try:
                naming.decide(project, name, "correct", now=now, value=text)
            except naming.NamingError as error:
                raise ReviewError(
                    _("{name} : nom refusé ({why}).").format(
                        name=name, why=problem_text(error.problems)
                    )
                ) from error
        changed += 1
    return changed


# --- Grouped decisions: the proposals of a group or of a question. ---


def scopes(project: Project) -> dict[str, list[str]]:
    """The groups and questions with names waiting for a decision: scope -> variables.
    A group is "G3"; a question, its key ("q0005", "Q5")."""
    found: dict[str, list[str]] = {}
    in_groups: set[str] = set()
    for group in project.groups:
        members = [
            n
            for n in group.members.value or []
            if project.variable(n).new_name.status == "proposed"
        ]
        members += [n for n in group.attached if project.variable(n).new_name.status == "proposed"]
        if members:
            found[group.group_id] = members
        in_groups.update(group.members.value or [])
        in_groups.update(group.attached)
    for question in naming.stem_questions(project):
        names = [
            n
            for n in (question.single, *(n for n, _r in question.options), question.other)
            if n and n not in in_groups and project.variable(n).new_name.status == "proposed"
        ]
        if names:
            found[question.key] = names
    others = [
        e.name
        for e in project.variables
        if e.new_name.status == "proposed"
        and e.name not in {n for names in found.values() for n in names}
    ]
    if others:
        found["*"] = others  # the rest: platform variables, variables alone
    return found


def scope_text(project: Project, scope: str) -> str:
    if scope == "*":
        return _("Autres variables")
    group = next((g for g in project.groups if g.group_id == scope), None)
    if group is not None:
        return f"{group.group_id} — {w.group_description(group, 'work')}"
    stem = naming.usable_stem(project, scope)
    return _("Question {key}").format(key=scope) + (f" ({stem})" if stem else "")


def accept_names(project: Project, names: list[str], *, now: str) -> None:
    """Accept the proposed names of these variables, one decision each."""
    if not names:
        raise ReviewError(_("Aucune variable cochée."))
    outside = [n for n in names if project.variable(n).new_name.status != "proposed"]
    if outside:
        raise ReviewError(
            _("Ces noms n'attendent plus de décision : {names}.").format(names=", ".join(outside))
        )
    for name in names:
        decide(project, name, "accept", now=now)


# --- Rules: prefixes, stems, the wave mark. ---


def set_group_prefix(project: Project, group_id: str, prefix: str, *, now: str) -> None:
    try:
        naming.set_prefix(project, group_id, prefix, now=now)
    except naming.NamingError as error:
        raise ReviewError(
            _("Préfixe refusé : {why}.").format(why=problem_text(error.problems))
        ) from error
    naming.propose(project)


def accept_group_prefix(project: Project, group_id: str, *, now: str) -> None:
    """Accept the prefix an earlier wave proposes for a group."""
    group = next(g for g in project.groups if g.group_id == group_id)
    if group.name_prefix.status != "proposed":
        raise ReviewError(_("Aucun préfixe proposé pour ce groupe."))
    group.name_prefix = group.name_prefix.model_copy(
        update={"status": "validated", "updated_at": now}
    )
    naming.propose(project)


def stem_rows(project: Project) -> list[tuple[str, str, str, str]]:
    """(question key, question text, stem, status) for each question with a stem."""
    found = []
    sure = naming.sure_links(project)
    for question in naming.stem_questions(project):
        current = naming.stem(project, question.key)
        text = naming.question_text(project, question, sure) or ""
        stem = current.stem.value if current and current.stem.value else ""
        status = w.status_text(current.stem) if current and current.stem.value else ""
        found.append((question.key, text, stem, status))
    return found


def apply_stems(project: Project, edits: dict[str, str], *, now: str) -> int:
    """The stems a person wrote in the table; then the rules propose again."""
    changed = 0
    for key, value in edits.items():
        text = (value or "").strip()
        current = naming.stem(project, key)
        if text == (current.stem.value if current else "") or not text:
            continue
        try:
            naming.decide_stem(project, key, "correct", now=now, value=text)
        except naming.NamingError as error:
            raise ReviewError(
                _("{key} : radical refusé ({why}).").format(
                    key=key, why=problem_text(error.problems)
                )
            ) from error
        changed += 1
    naming.propose(project)
    return changed


def set_settings(project: Project, wave: str, position: str, max_length: int) -> None:
    """The wave mark ("t2", empty for none), its place, the maximum length; then propose."""
    if not MIN_LENGTH <= max_length <= MAX_LENGTH:
        raise ReviewError(
            _("La longueur maximale doit être entre {low} et {high}.").format(
                low=MIN_LENGTH, high=MAX_LENGTH
            )
        )
    try:
        naming.set_wave(project, wave, position)
    except naming.NamingError as error:
        raise ReviewError(_("Marque de vague invalide : lettres et chiffres seulement.")) from error
    project.settings.naming.max_length = max_length
    naming.propose(project)


def propose(project: Project) -> None:
    naming.propose(project)


def take_earlier_wave(project: Project, path: Path) -> waves.WaveReport:
    """Take the names of an earlier wave (D-052); the report is written by the caller."""
    try:
        earlier = waves.read_earlier_wave(path)
    except (waves.ReferenceError, ProjectError, ReadError, OSError) as error:
        raise ReviewError(
            _("Impossible de lire la vague précédente : {detail}").format(detail=error)
        ) from error
    report = waves.match(project, earlier)
    waves.apply(project, earlier, report)
    return report
