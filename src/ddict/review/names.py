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
# The decision column of the table (v0.7.1, D-056).
DECISIONS = Texts({"accept": N_("Accepter"), "reject": N_("Rejeter")})
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
    waiting: bool  # a proposed name without a problem: "Accept" can apply


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
                waiting=tracked.status == "proposed" and not problems,
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


def apply_table(
    project: Project, edits: dict[str, str], decisions: dict[str, str], *, now: str
) -> int:
    """What a person did in the table (v0.7.1, D-056): names written, and "accept" or
    "reject" chosen on rows. A written name is a decision already ("accept" with it changes
    nothing); "reject" with it is contradictory and refused. Everything is checked before
    anything changes. Returns how many names changed."""
    written = {
        name
        for name, value in edits.items()
        if (value or "").strip() != (project.variable(name).new_name.value or "")
    }
    chosen = {name: action for name, action in decisions.items() if action and name not in written}
    both = sorted(n for n in written if decisions.get(n) == "reject")
    if both:
        raise ReviewError(
            _("{names} : nom modifié et « Rejeter » choisi ; gardez l'un ou l'autre.").format(
                names=", ".join(both)
            )
        )
    done = sorted(n for n in chosen if project.variable(n).new_name.status != "proposed")
    if done:
        raise ReviewError(
            _("Ces noms n'attendent plus de décision : {names}.").format(names=", ".join(done))
        )
    changed = apply_edits(project, edits, now=now)
    for name, action in chosen.items():
        try:
            naming.decide(project, name, action, now=now)
        except naming.NamingError as error:
            raise ReviewError(
                _("{name} : nom refusé ({why}).").format(
                    name=name, why=problem_text(error.problems)
                )
            ) from error
    return changed + len(chosen)


def accept_shown(project: Project, name: str, shown: str, *, now: str) -> None:
    """Accept the new name shown on the variable's page (v0.16, D-121): the proposed one,
    validated; another, written as the team's, checked like any name."""
    if project.variable(name).new_name.status != "proposed":
        raise ReviewError(_("Ce nom n'attend plus de décision."))
    if not (shown or "").strip():
        raise ReviewError(_("La valeur affichée est vide ; utilisez « Rejeter »."))
    apply_table(project, {name: shown.strip()}, {name: "accept"}, now=now)


def reject(project: Project, name: str, *, now: str) -> None:
    """Reject the proposed new name, from the variable's page (v0.16)."""
    apply_table(project, {}, {name: "reject"}, now=now)


# --- Rules: prefixes, base names (stems), the wave mark. ---


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
    """The base names (stems) a person wrote in the table; then the rules propose again."""
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
                _("{key} : nom de base refusé ({why}).").format(
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
