"""The database of a designed questionnaire arrives (v0.20, step E4, D-145).

The database is read and profiled as any other (`build_project`). Each of its variables
finds the planned variable of the same name, without case (a LimeSurvey CSV or Excel export
is already read with the names of its .sav, `Q4_SQ001`), and takes again what the team
decided about it: its question, its new name, its label, description, unit, measure level,
value labels, privacy class, group; what the file says comes from the file. A question
whose code changed in LimeSurvey (`nuit` became `nuisance`) is found by its texts, when they
leave no doubt: the same question text, found once in the questionnaire, and each item's
text found once among its variables (seen in the author's trial, 2026-10-20). The project
then documents a database, as any other ("Documenter").

The conformity report says what differs from the questionnaire, computed at any time from
the questionnaire and the variables: planned variables absent, variables not planned (the
platform's own aside), codes observed outside the planned ones (the codes only, never their
counts), value labels that differ, a type other than the planned one, the variables found
under another name, the texts of the base that differ from the questionnaire's (a question
reworded in LimeSurvey). Nothing in the questionnaire is changed by it.

Since v0.21 (D-167), with the database at hand: for each variable with a condition, how many
were asked it, how many not (not applicable), how many were asked and left it empty, and how
many answered under a false condition (anomalies). Counts only, a count under the threshold
said "< 5" (D-006): never a person, a line or a value. A variable keeps the condition it had
when the database arrived.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from ddict import design, naming, platforms
from ddict.design_limesurvey import OTHER_WORDS
from ddict.i18n import _
from ddict.io.load import read_database
from ddict.privacy import MIN_CELL_COUNT
from ddict.project import dataset, measure, skip
from ddict.project.build import build_project
from ddict.project.decisions import PROPOSING_ORIGINS
from ddict.project.model import Project, Question, TrackedValue, VariableEntry
from ddict.questionnaire.link import MIN_TRUNCATED, normalized_text, texts_agree

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
# "[Le bruit] Qu'est-ce qui nuit à votre sommeil ?": how LimeSurvey's .sav labels the
# variable of an item, a choice to tick or a grid's line.
ITEM_LABEL = re.compile(r"\s*\[(?P<item>[^\]]*)\]\s*(?P<question>.*)", re.DOTALL)


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
    if planned.asked_if is not None:  # v0.21: the condition it had when the base arrived
        entry.asked_if = planned.asked_if.model_copy(deep=True)
    return entry


def receive(
    project: Project, database: Path | str, *, min_cell_count: int = MIN_CELL_COUNT
) -> Conformity:
    """Read the database into the designed project; the conformity report after it."""
    if project.source is not None:
        raise AlreadyThere(project.source.name)
    data = read_database(database)
    found = build_project(data, min_cell_count=min_cell_count)
    planned = {e.name.lower(): e for e in project.variables if e.planned is not None}
    variables = []
    for position, entry in enumerate(found.variables, start=1):
        before = planned.pop(entry.name.lower(), None)
        merged = entry if before is None else _merged(before, entry)
        merged.position = position
        if before is not None and merged.name != before.name:
            _rename_members(project, before.name, merged.name)
        variables.append(merged)
    _by_texts(project, planned, variables)
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
    return conformity(project, data.table)


def _parts(label: str) -> tuple[str | None, str]:
    """The item and the question a variable's label names."""
    found = ITEM_LABEL.fullmatch(label)
    return (found["item"], found["question"]) if found else (None, label)


def _same(first: str | None, second: str | None) -> bool:
    """The same text, punctuation, case and accents aside, or the start of it (a label cut
    short): stricter than `texts_agree`, which takes a word changed for the same."""
    a, b = normalized_text(first or ""), normalized_text(second or "")
    if not a or not b:
        return False
    short, long = sorted((a, b), key=len)
    return a == b or (len(short) >= MIN_TRUNCATED and long.startswith(short))


def _item(question: Question, target: str | None):
    """The choice or the grid's line a variable stands for; None for the question itself."""
    for item in [*question.options, *question.rows]:
        if target in (getattr(item, "option_id", None), getattr(item, "row_id", None)):
            return item
    return None


def _item_agrees(item, text: str | None) -> bool:
    if text is None:
        return False
    if getattr(item, "other", False) and text.strip().lower() in OTHER_WORDS:
        return True  # LimeSurvey's own word for the "other" option
    return _same(item.text, text)


def _by_texts(
    project: Project, planned: dict[str, VariableEntry], variables: list[VariableEntry]
) -> None:
    """The planned variables not found by their name, found by their texts when they leave
    no doubt; found, they take again the decisions of the planned ones, as by their name."""
    questions = design.questionnaire(project).questions
    left: dict[str, list[VariableEntry]] = {}
    for entry in planned.values():
        left.setdefault((entry.question.value or "").partition(".")[0], []).append(entry)
    free = {
        n: _parts(e.file.label or "")
        for n, e in enumerate(variables)
        if e.planned is None and e.file.label
    }
    for question in questions:
        entries = left.get(question.question_id)
        if not entries or sum(_same(q.text, question.text) for q in questions) != 1:
            continue
        candidates = [n for n, (_i, text) in free.items() if _same(text, question.text)]
        if len(candidates) != len(entries):
            continue
        pairs = {}
        for entry in entries:
            item = _item(question, entry.question.value)
            hits = (
                candidates
                if item is None
                else [n for n in candidates if _item_agrees(item, free[n][0])]
            )
            if len(hits) != 1:
                break
            pairs[entry.name] = hits[0]
        else:
            if len(set(pairs.values())) != len(entries):
                continue
            for entry in entries:
                n = pairs[entry.name]
                merged = _merged(entry, variables[n])
                merged.position = variables[n].position
                _rename_members(project, entry.name, merged.name)
                variables[n] = merged
                planned.pop(entry.name.lower())
                del free[n]


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
    renamed: dict[str, str] = field(default_factory=dict)  # planned name -> name in the base
    texts: list[tuple[str, str, str]] = field(default_factory=list)  # name, planned, in base
    # v0.21: the variables with a condition, and their counts, when the base was at hand.
    filtered: dict[str, skip.Counts] = field(default_factory=dict)
    threshold: int = MIN_CELL_COUNT

    @property
    def anomalies(self) -> dict[str, int]:
        return {n: c.anomalies for n, c in self.filtered.items() if c.anomalies}

    @property
    def empty(self) -> bool:
        return not (
            self.absent or self.extra or self.codes or self.labels or self.types
            or self.renamed or self.texts or self.anomalies
        )  # fmt: skip


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


def conformity(project: Project, table: pd.DataFrame | None = None) -> Conformity:
    """What the database says otherwise than the questionnaire planned; with its table, the
    counts of the variables with a condition (v0.21)."""
    found = Conformity(threshold=project.settings.min_cell_count)
    if project.source is None or project.design is None:
        return found
    if table is not None:
        found.filtered = skip.counts(project, table)
    wanted = {w.name.lower(): w for w in design.wanted(project)}
    targets = {w.target: w for w in wanted.values()}
    questions = {q.question_id: q for q in design.questionnaire(project).questions}
    matched = set()
    platform = _platform_names(project)
    for entry in project.variables:
        key = entry.name.lower()
        plan = wanted.get(key)
        if plan is None and entry.question.value in targets:  # found by its texts
            plan = targets[entry.question.value]
            found.renamed[plan.name] = entry.name
        if plan is None:
            if key not in platform:
                found.extra.append(entry.name)
            continue
        matched.add(plan.name.lower())
        _texts(found, entry, questions.get(plan.target.partition(".")[0]), plan.target)
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
    found.absent = [w.name for key, w in wanted.items() if key not in matched]
    return found


def _texts(found: Conformity, entry: VariableEntry, question, target: str) -> None:
    """The question's text, and its item's, as the base's label says them, when they differ
    from the questionnaire's: each text once."""
    label = entry.file.label
    if question is None or not label or label == entry.name:
        return
    said, text = _parts(label)
    seen = {planned for _n, planned, _b in found.texts}
    if question.text not in seen and not _same(question.text, text):
        found.texts.append((entry.name, question.text, text.strip()))
    item = _item(question, target)
    if item is None or said is None or item.text in seen:
        return
    if not _item_agrees(item, said):
        found.texts.append((entry.name, item.text, said.strip()))


def _code(code) -> str:
    """A code as a text: 1.0 is "1"."""
    if isinstance(code, float) and code.is_integer():
        return str(int(code))
    return str(code)


def count_text(n: int, threshold: int) -> str:
    """A count as an export says it: under the threshold, "< 5" (D-006); none is 0."""
    return f"< {threshold}" if 0 < n < threshold else str(n)


def _filtered_lines(found: Conformity) -> list[str]:
    """The sections of the variables with a condition (v0.21): counts only."""
    if not found.filtered:
        return []
    n = found.threshold
    lines = [
        "## " + _("Questions filtrées"),
        "",
        "| " + " | ".join([_("Variable"), _("Posée à"), _("Non applicable"), _("Manquant")]) + " |",
        "|---|---|---|---|",
    ]
    for name, counts in found.filtered.items():
        cells = [
            f"`{name}`",
            *(count_text(c, n) for c in (counts.asked, counts.not_applicable, counts.missing)),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    if found.anomalies:
        lines += [
            "## " + _("Réponses sous une condition fausse"),
            "",
            _(
                "Des réponses à une question qui n'aurait pas dû être posée. La cause est "
                "d'ordinaire connue de l'équipe : une condition changée en cours de collecte "
                "(les versions marquées envoyées le disent), une base fusionnée à la main, une "
                "condition mal recopiée. Rien n'est corrigé par l'outil."
            ),
            "",
            *(f"- `{name}` : {count_text(c, n)}" for name, c in found.anomalies.items()),
            "",
        ]
    return lines


def report_markdown(project: Project, found: Conformity) -> str:
    """The conformity report, metadata only: names, codes and labels; since v0.21, the counts
    of the variables with a condition, a small count masked (D-006)."""
    title = design.questionnaire(project).file_name
    lines = [
        "# " + _("Conformité de la base au questionnaire"),
        "",
        _("Questionnaire « {title} », base {base}.").format(title=title, base=project.source.name),
        "",
    ]
    if found.empty:
        lines += [_("La base dit ce que le questionnaire prévoyait."), ""]
        return "\n".join(lines + _filtered_lines(found))
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
        (_("Variables retrouvées sous un autre nom (même texte, autre code)"),
         [f"- `{a}` → `{b}`" for a, b in found.renamed.items()]),
        (_("Textes différents du questionnaire"),
         [f"- `{n}` : « {a} » → « {b} »" for n, a, b in found.texts]),
    ]  # fmt: skip
    for heading, items in sections:
        if items:
            lines += [f"## {heading}", "", *items, ""]
    return "\n".join(lines + _filtered_lines(found))


def report_path(project_path: Path) -> Path:
    """ "Étude conçue-conformite.md", next to the project."""
    stem = project_path.name.removesuffix(".dd.json")
    return project_path.with_name(f"{stem}-conformite.md")


def summary_text(found: Conformity) -> str:
    """One line for the command line and the page."""
    if found.empty:
        return _("Base lue : elle dit ce que le questionnaire prévoyait.")
    if found.anomalies and not (
        found.absent or found.extra or found.codes or found.labels or found.types
        or found.renamed or found.texts
    ):  # fmt: skip
        return _(
            "Base lue. Conformité au questionnaire — variables avec des réponses sous une "
            "condition fausse : {n}."
        ).format(n=len(found.anomalies))
    return _(
        "Base lue. Conformité au questionnaire — variables prévues absentes : {absent} ; "
        "non prévues : {extra} ; avec des codes hors des codes prévus : {codes} ; aux "
        "étiquettes différentes : {labels} ; d'un autre type : {types} ; retrouvées sous un "
        "autre nom : {renamed} ; textes différents : {texts}."
    ).format(
        absent=len(found.absent),
        extra=len(found.extra),
        codes=len(found.codes),
        labels=len(found.labels),
        types=len(found.types),
        renamed=len(found.renamed),
        texts=len(found.texts),
    )
