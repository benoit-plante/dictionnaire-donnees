"""The database of a designed questionnaire arrives (v0.20, step E4, D-145).

The database is read and profiled as any other (`build_project`). Each of its variables
finds the planned variable of the same name, without case (a LimeSurvey CSV or Excel export
is already read with the names of its .sav, `Q4_SQ001`), and takes again what the team
decided about it: its question, its new name, its label, description, unit, measure level,
value labels, privacy class, group; what the file says comes from the file. The project then
documents a database, as any other ("Documenter").

The conformity report says what differs from the questionnaire, computed at any time from
the questionnaire and the variables: planned variables absent, variables not planned (the
platform's own aside), codes observed outside the planned ones (the codes only, never their
counts), value labels that differ, a type other than the planned one. Nothing in the
questionnaire is changed by it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ddict import design, naming, platforms
from ddict.i18n import _
from ddict.io.load import read_database
from ddict.privacy import MIN_CELL_COUNT
from ddict.project import dataset, measure
from ddict.project.build import build_project
from ddict.project.decisions import PROPOSING_ORIGINS
from ddict.project.model import Project, TrackedValue, VariableEntry
from ddict.questionnaire.link import texts_agree

# The decisions a variable keeps from its planned self, when a person made them.
DECIDED = (
    "new_name", "value_labels", "measure_level", "label", "description", "unit",
)  # fmt: skip
KEPT_LISTS = ("issues", "thresholds", "references", "ai_signals")
NUMBERS = {"integer", "decimal", "boolean"}
DATES = {"date", "datetime"}
# A text column holding codes of digits and others ("1", "-oth-"), as LimeSurvey's .sav
# writes a single choice with "other" (the real export of 2026-10-19).
TEXTS = {"text", "mixed"}


class AlreadyThere(ValueError):
    """The project has its database already."""


def _decided(tracked: TrackedValue) -> bool:
    """A value a person gave or settled, which the file must not replace."""
    if tracked.value is None:
        return False
    if tracked.origin in PROPOSING_ORIGINS:
        return tracked.status in ("validated", "corrected")
    return tracked.origin == "human"


def _merged(planned: VariableEntry, found: VariableEntry) -> VariableEntry:
    """The variable of the database, with the decisions of the planned one."""
    entry = found.model_copy(deep=True)
    entry.question = planned.question.model_copy(deep=True)  # the link is a fact
    entry.group_id = planned.group_id.model_copy(deep=True)  # the project's groups
    entry.planned = planned.planned
    for name in DECIDED:
        if _decided(getattr(planned, name)):
            setattr(entry, name, getattr(planned, name).model_copy(deep=True))
    if _decided(planned.privacy.privacy_class):
        entry.privacy = planned.privacy.model_copy(deep=True)
    for name in KEPT_LISTS:
        if getattr(planned, name):
            setattr(entry, name, list(getattr(planned, name)))
    entry.theoretical_range = planned.theoretical_range or entry.theoretical_range
    entry.notes = planned.notes or entry.notes
    return entry


def receive(
    project: Project, database: Path | str, *, min_cell_count: int = MIN_CELL_COUNT
) -> Conformity:
    """Read the database into the designed project; the conformity report after it."""
    if project.source is not None:
        raise AlreadyThere(project.source.name)
    found = build_project(read_database(database), min_cell_count=min_cell_count)
    planned = {e.name.lower(): e for e in project.variables if e.planned is not None}
    variables = []
    for position, entry in enumerate(found.variables, start=1):
        before = planned.pop(entry.name.lower(), None)
        merged = entry if before is None else _merged(before, entry)
        merged.position = position
        if before is not None and merged.name != before.name:
            _rename_members(project, before.name, merged.name)
        variables.append(merged)
    project.source = found.source
    project.settings.min_cell_count = found.settings.min_cell_count
    project.settings.max_observed_values = found.settings.max_observed_values
    project.variables = variables
    known = {e.name for e in variables}
    for group in project.groups:  # a planned item absent from the base leaves its group
        if group.members.value:
            group.members.value = [m for m in group.members.value if m in known]
    measure.propose(project)
    naming.propose(project)
    dataset.propose_structure(project)
    return conformity(project)


def _rename_members(project: Project, old: str, new: str) -> None:
    for group in project.groups:
        if group.members.value and old in group.members.value:
            group.members.value = [new if m == old else m for m in group.members.value]


# --- The conformity report. ---


@dataclass
class Conformity:
    absent: list[str] = field(default_factory=list)  # planned, not in the base
    extra: list[str] = field(default_factory=list)  # in the base, not planned
    codes: dict[str, list[str]] = field(default_factory=dict)  # codes observed, not planned
    labels: dict[str, list[tuple[str, str, str]]] = field(default_factory=dict)
    types: dict[str, tuple[str, str]] = field(default_factory=dict)  # planned, observed

    @property
    def empty(self) -> bool:
        return not (self.absent or self.extra or self.codes or self.labels or self.types)


def _family(kind: str) -> str:
    if kind in NUMBERS:
        return "number"
    if kind in DATES:
        return "date"
    if kind in TEXTS:
        return "text"
    return kind


def _platform_names(project: Project) -> set[str]:
    platform = platforms.of(project)
    if platform is None:
        return set()
    return {n.lower() for v in platform.variables for n in v.names}


def conformity(project: Project) -> Conformity:
    """What the database says otherwise than the questionnaire planned."""
    found = Conformity()
    if project.source is None or project.design is None:
        return found
    wanted = {w.name.lower(): w for w in design.wanted(project)}
    names = {e.name.lower(): e for e in project.variables}
    found.absent = [w.name for key, w in wanted.items() if key not in names]
    platform = _platform_names(project)
    for entry in project.variables:
        key = entry.name.lower()
        plan = wanted.get(key)
        if plan is None:
            if key not in platform:
                found.extra.append(entry.name)
            continue
        observed = entry.profile.inferred_type if entry.profile is not None else plan.type
        if _family(observed) != _family(plan.type) and observed != "empty":
            found.types[entry.name] = (plan.type, observed)
        planned_codes = {str(c): t for c, t in plan.labels}
        if planned_codes and entry.profile is not None:
            seen = [
                str(v.code)
                for v in entry.profile.observed_values or []
                if not v.declared_missing and _code(v.code) not in planned_codes
            ]
            if seen:
                found.codes[entry.name] = seen
        differ = []
        for label in entry.file.value_labels:
            code = _code(label.code)
            text = planned_codes.get(code)
            # LimeSurvey's .sav labels the "other" answer "Other", in English, whatever the
            # language of the survey: not a difference the team made.
            if code == design.OTHER_ANSWER:
                continue
            if text is not None and not texts_agree(text, label.label):
                differ.append((code, text, label.label))
        if differ:
            found.labels[entry.name] = differ
    return found


def _code(code) -> str:
    """A code as a text: 1.0 is "1"."""
    if isinstance(code, float) and code.is_integer():
        return str(int(code))
    return str(code)


def report_markdown(project: Project, found: Conformity) -> str:
    """The conformity report, metadata only: names, codes and labels, never a count."""
    title = design.questionnaire(project).file_name
    lines = [
        "# " + _("Conformité de la base au questionnaire"),
        "",
        _("Questionnaire « {title} », base {base}.").format(title=title, base=project.source.name),
        "",
    ]
    if found.empty:
        lines += [_("La base dit ce que le questionnaire prévoyait."), ""]
        return "\n".join(lines)
    sections = [
        (_("Variables prévues absentes de la base"), [f"- `{n}`" for n in found.absent]),
        (_("Variables de la base que le questionnaire ne prévoyait pas"),
         [f"- `{n}`" for n in found.extra]),
        (_("Codes observés hors des codes prévus"),
         [f"- `{n}` : {', '.join(f'`{c}`' for c in codes)}" for n, codes in found.codes.items()]),
        (_("Étiquettes de valeurs différentes"),
         [f"- `{n}`, `{c}` : « {a} » → « {b} »" for n, rows in found.labels.items()
          for c, a, b in rows]),
        (_("Types différents"),
         [f"- `{n}` : " + _("prévu {planned}, observé {observed}").format(
             planned=a, observed=b) for n, (a, b) in found.types.items()]),
    ]  # fmt: skip
    for heading, items in sections:
        if items:
            lines += [f"## {heading}", "", *items, ""]
    return "\n".join(lines)


def report_path(project_path: Path) -> Path:
    """ "Étude conçue-conformite.md", next to the project."""
    stem = project_path.name.removesuffix(".dd.json")
    return project_path.with_name(f"{stem}-conformite.md")


def summary_text(found: Conformity) -> str:
    """One line for the command line and the page."""
    if found.empty:
        return _("Base lue : elle dit ce que le questionnaire prévoyait.")
    return _(
        "Base lue. Conformité au questionnaire — variables prévues absentes : {absent} ; "
        "non prévues : {extra} ; avec des codes hors des codes prévus : {codes} ; aux "
        "étiquettes différentes : {labels} ; d'un autre type : {types}."
    ).format(
        absent=len(found.absent),
        extra=len(found.extra),
        codes=len(found.codes),
        labels=len(found.labels),
        types=len(found.types),
    )
