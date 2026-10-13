"""What the review interface does to a project, without any interface.

Each function changes the project in memory and returns nothing; the interface saves the
project after each call. Errors are ReviewError with a French message for the person.
"""

from __future__ import annotations

from typing import Literal

from pydantic import ValidationError

from ddict.export.wording import anomalies
from ddict.i18n import _
from ddict.project.decisions import DecisionError, correct, enter, reject, validate
from ddict.project.model import (
    Project,
    SourcedText,
    TheoreticalRange,
    Threshold,
    TrackedValue,
    VariableEntry,
)

Field = Literal["label", "description", "unit"]
Action = Literal["accept", "correct", "reject"]
Filter = Literal["all", "to_review", "flagged", "sensitive"]

PRIVACY_CLASSES = ("ordinary", "likely_identifier", "free_text", "quasi_identifier")

SIGNALS = {
    "citation": _("ressemble à une citation"),
    "threshold": _("ressemble à un seuil"),
    "instrument": _("ressemble à un nom d'instrument"),
    "no_file_label": _("deviné : la variable n'a pas d'étiquette dans le fichier"),
}
FIELD_NAMES = {"label": _("libellé"), "description": _("description"), "issues": _("signalement")}


class ReviewError(ValueError):
    """A decision that cannot be recorded; the message is for the person."""


def is_sensitive(entry: VariableEntry) -> bool:
    return (entry.privacy.privacy_class.value or "ordinary") != "ordinary"


def pending(entry: VariableEntry) -> list[str]:
    """Fields with an AI proposal waiting for a decision."""
    fields = [f for f in ("label", "description") if getattr(entry, f).status == "proposed"]
    fields += ["issues"] * sum(1 for i in entry.issues if i.status == "proposed")
    return fields


def is_flagged(entry: VariableEntry) -> bool:
    return bool(anomalies(entry.profile) or entry.ai_signals)


def select(project: Project, which: Filter) -> list[VariableEntry]:
    tests = {
        "all": lambda e: True,
        "to_review": lambda e: bool(pending(e)),
        "flagged": is_flagged,
        "sensitive": is_sensitive,
    }
    return [e for e in project.variables if tests[which](e)]


def progress(project: Project) -> tuple[int, int]:
    """Variables without pending proposal, out of all variables."""
    done = sum(1 for e in project.variables if not pending(e))
    return done, len(project.variables)


def signal_texts(entry: VariableEntry) -> list[str]:
    texts = []
    for signal in entry.ai_signals:
        field, _sep, code = signal.partition(":")
        texts.append(f"{FIELD_NAMES.get(field, field)} : {SIGNALS.get(code, code)}")
    return texts


def decide(
    project: Project,
    name: str,
    field: Field,
    action: Action,
    *,
    now: str,
    value: str | None = None,
) -> None:
    """Accept, correct or reject the value of a field of a variable."""
    entry = project.variable(name)
    tracked: TrackedValue[str] = getattr(entry, field)
    try:
        if action == "accept":
            new = validate(tracked, now=now)
        elif action == "reject":
            new = reject(tracked, now=now)
        else:
            text = (value or "").strip()
            if not text:
                raise ReviewError(_("La valeur corrigée est vide."))
            new = correct(tracked, text, now=now)
    except DecisionError as error:
        raise ReviewError(_("Décision impossible : {detail}").format(detail=error)) from error
    setattr(entry, field, new)
    if action in ("accept", "correct", "reject"):
        # A decision on the field settles its signals.
        entry.ai_signals = [s for s in entry.ai_signals if not s.startswith(f"{field}:")]


def write(project: Project, name: str, field: Field, value: str, *, now: str) -> None:
    """Enter or change a value by hand, whatever its origin."""
    entry = project.variable(name)
    tracked: TrackedValue[str] = getattr(entry, field)
    text = value.strip() or None
    if tracked.origin == "human":
        setattr(entry, field, enter(tracked, text, now=now))
    elif text is not None and text != tracked.value:
        decide(project, name, field, "correct", now=now, value=text)


def decide_issue(project: Project, name: str, index: int, action: Action, *, now: str) -> None:
    entry = project.variable(name)
    issue = entry.issues[index]
    entry.issues[index] = validate(issue, now=now) if action == "accept" else reject(issue, now=now)


def set_privacy(project: Project, name: str, privacy_class: str, *, now: str) -> None:
    """Confirm the computed class, or change it."""
    if privacy_class not in PRIVACY_CLASSES:
        raise ReviewError(_("Classe de confidentialité inconnue : {c}").format(c=privacy_class))
    privacy = project.variable(name).privacy
    tracked = privacy.privacy_class
    if privacy_class == tracked.value:
        privacy.privacy_class = validate(tracked, now=now)
    else:
        privacy.privacy_class = correct(tracked, privacy_class, now=now)


def _sourced(build):
    try:
        return build()
    except ValidationError as error:
        problems = {e["loc"][-1] if e["loc"] else "" for e in error.errors()}
        if "source" in problems:
            raise ReviewError(_("Une source documentée est obligatoire.")) from error
        raise ReviewError(_("Valeur invalide : {detail}").format(detail=error)) from error


def add_threshold(project: Project, name: str, value: float, meaning: str, source: str) -> None:
    threshold = _sourced(lambda: Threshold(value=value, meaning=meaning, source=source))
    project.variable(name).thresholds.append(threshold)


def remove_threshold(project: Project, name: str, index: int) -> None:
    del project.variable(name).thresholds[index]


def set_theoretical_range(
    project: Project, name: str, low: float, high: float, source: str
) -> None:
    value = _sourced(lambda: TheoreticalRange(min=low, max=high, source=source))
    project.variable(name).theoretical_range = value


def clear_theoretical_range(project: Project, name: str) -> None:
    project.variable(name).theoretical_range = None


def set_references(project: Project, name: str, text: str) -> None:
    project.variable(name).references = [line.strip() for line in text.splitlines() if line.strip()]


def set_notes(project: Project, name: str, text: str) -> None:
    project.variable(name).notes = text.strip() or None


def set_references_and_notes(project: Project, name: str, references: str, notes: str) -> None:
    set_references(project, name, references)
    set_notes(project, name, notes)


def _group(project: Project, group_id: str):
    for group in project.groups:
        if group.group_id == group_id:
            return group
    raise KeyError(group_id)


def set_instrument(project: Project, group_id: str, value: str, source: str) -> None:
    group = _group(project, group_id)
    if not value.strip():
        group.instrument_name = None
        return
    group.instrument_name = _sourced(lambda: SourcedText(value=value, source=source))


def set_reverse_items(project: Project, group_id: str, names: list[str]) -> None:
    group = _group(project, group_id)
    members = group.members.value or []
    unknown = [n for n in names if n not in members]
    if unknown:
        raise ReviewError(_("Pas dans le groupe : {names}").format(names=", ".join(unknown)))
    group.reverse_items = [n for n in members if n in names]
