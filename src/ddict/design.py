"""A questionnaire designed in the tool, before its collection (v0.20, D-145, D-146).

The questionnaire is the project's source of truth: its sections and questions are changed
here, by the same functions for the interface and the command line, and each change makes
the planned variables again (`plan_variables`): their names, labels, codes and groups follow
the questions. An id ("Q7", "Q7.r3", "Q10.o2", "S2") is never given again, so a variable keeps
its place through every change; only the codes the team decides change its name.

A change the project cannot take (a renamed variable that the plan still cites, a question
left without options) raises DesignError and leaves the project as it was.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date

from ddict import naming
from ddict.i18n import N_, _
from ddict.privacy.classify import classify_planned
from ddict.project import measure, skip
from ddict.project.build import GROUP_PARTS
from ddict.project.decisions import is_accepted
from ddict.project.model import (
    Condition,
    Design,
    FileMetadata,
    GridRow,
    Group,
    Planned,
    Privacy,
    Project,
    Provenance,
    Question,
    Questionnaire,
    QuestionOption,
    Section,
    Settings,
    Term,
    TrackedValue,
    ValueLabel,
    VariableEntry,
)

# How LimeSurvey 7.6 names the columns of a question's items in its .sav export, as seen on
# the author's (docs/essais/2026-10-19-limesurvey-fictif.md): the question's code, then the
# item's ("sommeil_SQ001", "genre_other"); its CSV and Excel exports, read by the tool, are
# named the same way (`platforms.LIMESURVEY.column_name`).
SEPARATOR = "_"
OTHER_CODE = "other"
# A ticked box holds "Y", a text; the "other" answer of a single choice is coded "-oth-",
# which makes the whole question a text in the .sav.
CHECKBOX_TYPE = "text"
OTHER_ANSWER = "-oth-"
BASIS = "designed_questionnaire"


class DesignError(ValueError):
    """A change refused, with the reasons in plain language; the project is unchanged."""

    def __init__(self, reasons: list[str]) -> None:
        super().__init__("; ".join(reasons))
        self.reasons = reasons


@dataclass(frozen=True)
class Item:
    """A choice of answer, or a row of a grid, as the team gives it: `item_id` is the one it
    already has, None for a new one."""

    text: str
    code: str | None = None
    other: bool = False
    provenance: Provenance | None = None
    item_id: str | None = None


@dataclass(frozen=True)
class Draft:
    """A question as the team writes it, before it gets its ids."""

    kind: str
    text: str
    section: str
    instruction: str | None = None
    required: bool = False
    answer: str | None = None
    layout: str | None = None
    provenance: Provenance | None = None
    options: tuple[Item, ...] = ()
    rows: tuple[Item, ...] = ()


@dataclass
class Changes:
    """What making the planned variables again changed."""

    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    renamed: dict[str, str] = field(default_factory=dict)


# --- The project. ---


def new_project(title: str, language: str, today: str) -> Project:
    """A project designed before its collection: no database, one empty section."""
    if not title.strip():
        raise DesignError([_("Donnez un nom au questionnaire.")])
    project = Project(
        settings=Settings(language=language),
        variables=[],
        questionnaire=Questionnaire(
            file_name=title.strip(),
            sha256="",
            format="designed",
            sections=[Section(section_id="S1")],
        ),
        design=Design(created=today, counters={"S": 1}),
    )
    _seal(project, today)
    return project


def questionnaire(project: Project) -> Questionnaire:
    found = project.questionnaire
    if project.design is None or found is None or found.format != "designed":
        raise DesignError([_("Ce projet n'a pas de questionnaire conçu dans l'outil.")])
    return found


# The fields added since 0.11.0 (v0.21, D-172), with their empty value: what a fingerprint
# leaves out while they are empty, so that a questionnaire without any keeps its fingerprint,
# its publications and its kept review points.
_SINCE_0_12 = {"condition": None, "shuffle": False, "attention": None}


def _without_empty(data: dict) -> dict:
    return {k: v for k, v in data.items() if k not in _SINCE_0_12 or v != _SINCE_0_12[k]}


def section_content(section: Section) -> dict:
    return _without_empty(section.model_dump(mode="json"))


def question_content(question: Question) -> dict:
    """A question as its fingerprints see it: whole, the fields added since 0.11.0 only when
    filled (D-172)."""
    data = _without_empty(question.model_dump(mode="json"))
    data["rows"] = [_without_empty(row) for row in data["rows"]]
    return data


def content_fingerprint(found: Questionnaire) -> str:
    """The SHA-256 of what the questionnaire says (its sections and questions), whatever its
    name: what the codebook's fingerprint and a publication keep (D-150)."""
    data = {
        "sections": [section_content(s) for s in found.sections],
        "questions": [question_content(q) for q in found.questions],
    }
    text = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _next(project: Project, kind: str) -> int:
    """The next number of an id of this kind ("Q", "S", "G", "Q7.o", "Q7.r"), never one
    given before."""
    assert project.design is not None
    counters = dict(project.design.counters)
    counters[kind] = counters.get(kind, 0) + 1
    project.design.counters = dict(sorted(counters.items()))
    return counters[kind]


def _seal(project: Project, today: str | None = None) -> None:
    """The questionnaire's fingerprint, and the day its content changed (D-152)."""
    found = questionnaire(project)
    sealed = content_fingerprint(found)
    if sealed != found.sha256:
        found.sha256 = sealed
        project.design.changed = today or date.today().isoformat()


def _change(project: Project, change) -> Changes:
    """Apply a change, then make the variables again; refused, the project is as before."""
    before = project.model_copy(deep=True)
    try:
        change()
        _tidy(project)
        _seal(project)
        return plan_variables(project)
    except DesignError:
        for name in Project.model_fields:
            setattr(project, name, getattr(before, name))
        raise


def _tidy(project: Project) -> None:
    """The questions in the order of their sections, each keeping its place in its own."""
    found = questionnaire(project)
    rank = {s.section_id: n for n, s in enumerate(found.sections)}
    found.questions = sorted(found.questions, key=lambda q: rank.get(q.section, len(rank)))


# --- Sections. ---


def _section(project: Project, section_id: str) -> Section:
    for section in questionnaire(project).sections:
        if section.section_id == section_id:
            return section
    raise DesignError([_("Section inconnue : {id}.").format(id=section_id)])


def add_section(project: Project, title: str, instruction: str | None = None) -> str:
    found: list[str] = []

    def change() -> None:
        section_id = f"S{_next(project, 'S')}"
        questionnaire(project).sections.append(
            Section(section_id=section_id, title=title.strip(), instruction=_clean(instruction))
        )
        found.append(section_id)

    _change(project, change)
    return found[0]


def modify_section(
    project: Project, section_id: str, title: str, instruction: str | None = None
) -> None:
    def change() -> None:
        section = _section(project, section_id)
        section.title = title.strip()
        section.instruction = _clean(instruction)

    _change(project, change)


def remove_section(project: Project, section_id: str) -> None:
    """Only an empty section, and never the last one."""

    def change() -> None:
        found = questionnaire(project)
        _section(project, section_id)
        if len(found.sections) == 1:
            raise DesignError([_("Un questionnaire garde au moins une section.")])
        if any(q.section == section_id for q in found.questions):
            raise DesignError([_("Retirez ou déplacez d'abord les questions de cette section.")])
        found.sections = [s for s in found.sections if s.section_id != section_id]

    _change(project, change)


def move_section(project: Project, section_id: str, rank: int) -> None:
    """To its new rank, from 1."""

    def change() -> None:
        found = questionnaire(project)
        section = _section(project, section_id)
        others = [s for s in found.sections if s.section_id != section_id]
        others.insert(max(0, min(rank - 1, len(others))), section)
        found.sections = others

    _change(project, change)


# --- Questions. ---


def find(project: Project, question_id: str) -> Question:
    for question in questionnaire(project).questions:
        if question.question_id == question_id:
            return question
    raise DesignError([_("Question inconnue : {id}.").format(id=question_id)])


def _clean(text: str | None) -> str | None:
    return text.strip() if text and text.strip() else None


def draft_problems(project: Project, draft: Draft) -> list[str]:
    """Why a question cannot be saved: what is missing for its kind. What it would be better
    to change (codes, names) is the review's, not a refusal."""
    found = []
    if draft.kind not in ("open", "single", "checkbox", "grid", "display"):
        found.append(_("Nature de question inconnue."))
    if not draft.text.strip():
        found.append(_("Le texte de la question est vide."))
    if draft.section not in {s.section_id for s in questionnaire(project).sections}:
        found.append(_("Section inconnue : {id}.").format(id=draft.section))
    options = [i for i in draft.options if i.text.strip()]
    rows = [i for i in draft.rows if i.text.strip()]
    if draft.kind in ("single", "checkbox") and not [o for o in options if not o.other]:
        found.append(_("Donnez au moins un choix de réponse."))
    if draft.kind == "grid":
        if not rows:
            found.append(_("Donnez au moins un énoncé à la grille."))
        if len(options) < 2:
            found.append(_("Donnez au moins deux choix de réponse (les colonnes de la grille)."))
    if draft.kind in ("open", "display") and (options or rows):
        found.append(_("Une question ouverte ou un texte d'affichage n'a pas de choix."))
    if draft.kind != "grid" and rows:
        found.append(_("Seule une grille a des énoncés."))
    if sum(1 for o in options if o.other) > 1 or (
        draft.kind == "grid" and any(o.other for o in options)
    ):
        found.append(_("Une seule option « autre », et jamais dans une grille."))
    return found


def _items(project: Project, question_id: str, items, kind: str, make) -> list:
    """The items with their ids: those they had, new ones for the others."""
    found = []
    known = set()
    for item in items:
        if not item.text.strip():
            continue
        item_id = item.item_id
        if item_id is None or not item_id.startswith(f"{question_id}.{kind}") or item_id in known:
            item_id = f"{question_id}.{kind}{_next(project, f'{question_id}.{kind}')}"
        known.add(item_id)
        found.append(make(item, item_id))
    return found


def _question(project: Project, question_id: str, draft: Draft) -> Question:
    options = _items(
        project,
        question_id,
        draft.options,
        "o",
        lambda item, item_id: QuestionOption(
            option_id=item_id,
            text=item.text.strip(),
            code=_clean(item.code),
            other=item.other,
            provenance=item.provenance,
        ),
    )
    rows = _items(
        project,
        question_id,
        draft.rows,
        "r",
        lambda item, item_id: GridRow(
            row_id=item_id,
            text=item.text.strip(),
            code=_clean(item.code),
            provenance=item.provenance,
        ),
    )
    return Question(
        question_id=question_id,
        text=draft.text.strip(),
        kind=draft.kind,  # type: ignore[arg-type]
        options=options,
        rows=rows,
        section=draft.section,
        instruction=_clean(draft.instruction),
        required=draft.required and draft.kind != "display",
        answer=(draft.answer or "short") if draft.kind == "open" else None,  # type: ignore[arg-type]
        layout=(draft.layout or "radio") if draft.kind == "single" else None,  # type: ignore[arg-type]
        provenance=draft.provenance,
    )


def add_question(project: Project, draft: Draft, after: str | None = None) -> str:
    """At the end of its section, or after the question `after`. Returns its id."""
    found: list[str] = []

    def change() -> None:
        problems = draft_problems(project, draft)
        if problems:
            raise DesignError(problems)
        question_id = f"Q{_next(project, 'Q')}"
        question = _question(project, question_id, draft)
        questions = questionnaire(project).questions
        ids = [q.question_id for q in questions]
        if after in ids:
            questions.insert(ids.index(after) + 1, question)
        else:
            last = [n for n, q in enumerate(questions) if q.section == draft.section]
            questions.insert(last[-1] + 1 if last else len(questions), question)
        found.append(question_id)

    _change(project, change)
    return found[0]


def modify_question(project: Project, question_id: str, draft: Draft) -> Changes:
    """The question as the team rewrote it: items given with their id keep it, and so their
    variables. Moved to another section, it goes to the end of that one."""

    def change() -> None:
        old = find(project, question_id)
        problems = draft_problems(project, draft)
        if problems:
            raise DesignError(problems)
        questions = questionnaire(project).questions
        index = questions.index(old)
        new = _question(project, question_id, draft)
        _keep(old, new)
        if new.section == old.section:
            questions[index] = new
        else:
            del questions[index]
            last = [n for n, q in enumerate(questions) if q.section == new.section]
            questions.insert(last[-1] + 1 if last else len(questions), new)

    return _change(project, change)


def _keep(old: Question, new: Question) -> None:
    """What the editor's draft does not carry (v0.21): the question's condition, its random
    order and its attention checks, as long as its kind admits them."""
    new.condition = old.condition
    new.shuffle = old.shuffle and new.kind in SHUFFLED
    new.attention = old.attention if new.kind == "single" else None
    if new.kind == "grid":
        kept = {row.row_id: row.attention for row in old.rows}
        for row in new.rows:
            row.attention = kept.get(row.row_id)


def remove_question(project: Project, question_id: str) -> Changes:
    """With its variables and its group; refused while the plan, a recoding, an exclusion
    rule or the description of the database cites one of its variables (`citations`)."""

    def change() -> None:
        found = questionnaire(project)
        find(project, question_id)
        found.questions = [q for q in found.questions if q.question_id != question_id]
        project.stems = [s for s in project.stems if s.key != question_id]

    return _change(project, change)


def move_question(project: Project, question_id: str, rank: int) -> None:
    """To its new rank within its section, from 1."""

    def change() -> None:
        question = find(project, question_id)
        questions = questionnaire(project).questions
        same = [q for q in questions if q.section == question.section and q is not question]
        same.insert(max(0, min(rank - 1, len(same))), question)
        places = [n for n, q in enumerate(questions) if q.section == question.section]
        for place, moved in zip(places, same, strict=True):
            questions[place] = moved

    _change(project, change)


def decide_code(
    project: Project, question_id: str, action: str, *, now: str, value: str = ""
) -> Changes:
    """The question's code, decided as its stem (D-146, `naming.decide_stem`): its variables
    are renamed after it, and refused as any rename."""

    def change() -> None:
        find(project, question_id)
        try:
            naming.decide_stem(project, question_id, action, now=now, value=value)
        except naming.NamingError as error:
            from ddict.review.names import problem_text  # the texts of the page "Noms"

            raise DesignError(
                [_("Code refusé : {why}.").format(why=problem_text(error.problems))]
            ) from error

    return _change(project, change)


# --- Conditions, random order, attention checks (v0.21, D-165, D-166, D-170). ---

# The kinds of question whose statements, choices or options can be shown in random order.
SHUFFLED = ("single", "checkbox", "grid")


def _owner(project: Project, owner: str) -> Section | Question:
    if owner.startswith("S"):
        return _section(project, owner)
    return find(project, owner)


def set_condition(project: Project, owner: str, condition: Condition | None) -> Changes:
    """When a section ("S2") or a question ("Q4") is asked; None: always. Refused with the
    reasons of `skip.problems`; what is allowed but doubtful is the review's."""

    def change() -> None:
        found = questionnaire(project)
        target = _owner(project, owner)
        if condition is None:
            target.condition = None
            return
        ready = skip.normalized(found, condition)
        problems = skip.problems(found, owner, ready)
        if problems:
            raise DesignError(problems)
        target.condition = ready

    return _change(project, change)


def set_shuffle(project: Project, owner: str, shuffle: bool) -> Changes:
    """A section's questions, or a question's statements, choices or options, in random
    order, drawn for each person (D-166)."""

    def change() -> None:
        target = _owner(project, owner)
        if isinstance(target, Question) and shuffle and target.kind not in SHUFFLED:
            raise DesignError(
                [
                    _(
                        "Seuls les énoncés d'une grille, les choix d'une question et les options "
                        "à cocher se présentent dans un ordre aléatoire."
                    )
                ]
            )
        target.shuffle = shuffle

    return _change(project, change)


def set_attention(project: Project, item: str, correct: list[str] | None) -> Changes:
    """A single choice ("Q4") or a grid's statement ("Q7.r3") as an attention check, with the
    codes of its right answers (D-170); None: no longer one. A statement that is one leaves
    the members of its grid's group (it enters no score)."""

    def change() -> None:
        question = find(project, item.partition(".")[0])
        if item == question.question_id:
            if question.kind != "single":
                raise DesignError(
                    [
                        _(
                            "Seule une question à choix unique ou un énoncé de grille peut être "
                            "un item de contrôle."
                        )
                    ]
                )
            holder: Question | GridRow = question
        else:
            row = next((r for r in question.rows if r.row_id == item), None)
            if row is None:
                raise DesignError([_("Énoncé inconnu : {id}.").format(id=item)])
            holder = row
        if correct is None:
            holder.attention = None
            return
        codes = list(dict.fromkeys(skip.code_text(c) for c in correct))
        if not codes:
            raise DesignError([_("Donnez au moins une bonne réponse.")])
        known = skip.choices(question)
        wrong = [
            _("{value} n'est pas un choix de {target}.").format(value=c, target=item)
            for c in codes
            if c not in known
        ]
        if wrong:
            raise DesignError(wrong)
        holder.attention = codes

    return _change(project, change)


def citations(project: Project, question_id: str) -> list[str]:
    """What, beyond the questionnaire, holds a decision on the question's variables: what the
    page says before removing it."""
    names = [e.name for e in project.variables if _question_of(e) == question_id]
    found = [
        _("{place} cite {name}").format(place=p, name=n) for n in names for p in _cited(project, n)
    ]
    for group in project.groups:
        if group.question == question_id and (group.scoring or group.instrument_name):
            found.append(
                _("le groupe {id} a une cotation ou un nom d'instrument").format(id=group.group_id)
            )
    if project.questionnaire is not None:  # v0.21: the conditions left without their target
        for owner in skip.citing(project.questionnaire, question_id):
            found.append(_("la condition de {id} vise cette question").format(id=owner))
    return found


# --- The planned variables. ---


@dataclass(frozen=True)
class _Wanted:
    target: str  # "Q4.r1", "Q2", "Q5.o3" (the "other" text)
    name: str
    label: str
    type: str
    labels: tuple[tuple[int | str, str], ...] = ()
    long: bool = False
    choice: bool = False


def code(project: Project, question: Question) -> str:
    """The question's LimeSurvey code (D-156): its accepted stem (D-146) without its "_",
    since LimeSurvey takes letters and digits only; else its id until one is decided."""
    found = naming.stem(project, question.question_id)
    if found is not None and is_accepted(found.stem) and found.stem.value:
        return found.stem.value.replace("_", "")
    return question.question_id


# The LimeSurvey type of each kind of question (D-148), as LimeSurvey 7.6 names them.
LIMESURVEY_TYPES = {"checkbox": "M", "grid": "F", "display": "X"}
LIMESURVEY_ANSWERS = {"short": "S", "long": "T", "number": "N", "date": "D"}


def limesurvey_type(question: Question) -> str:
    if question.kind == "single":
        return "!" if question.layout == "dropdown" else "L"
    if question.kind == "open":
        return LIMESURVEY_ANSWERS[question.answer or "short"]
    return LIMESURVEY_TYPES[question.kind]


def _coded(options) -> list[tuple[str, str]]:
    """The codes of the choices and their texts; a single choice's "other" answer is coded
    "-oth-", as LimeSurvey exports it."""
    found = [(o.code, o.text) for o in options if o.code and not o.other]
    found += [(OTHER_ANSWER, o.text) for o in options if o.other]
    return found


def _numeric(coded) -> bool:
    return bool(coded) and all(c.lstrip("-").isdigit() for c, _t in coded)


def _labels(options) -> tuple[tuple[int | str, str], ...]:
    coded = _coded(options)
    numeric = _numeric(coded)
    return tuple((int(c) if numeric else c, t) for c, t in coded)


def _type(options) -> str:
    return "integer" if _numeric(_coded(options)) else "text"


def _wanted(project: Project) -> list[_Wanted]:
    found = []
    for question in questionnaire(project).questions:
        base = code(project, question)
        other = next((o for o in question.options if o.other), None)
        if question.kind == "display":  # an empty column in every export of LimeSurvey 7.6
            found.append(_Wanted(question.question_id, base, question.text, "text"))
        elif question.kind == "open":
            kind = {"number": "decimal", "date": "date"}.get(question.answer or "", "text")
            found.append(
                _Wanted(
                    question.question_id, base, question.text, kind, long=question.answer == "long"
                )
            )
        elif question.kind == "single":
            found.append(
                _Wanted(
                    question.question_id,
                    base,
                    question.text,
                    _type(question.options),
                    _labels(question.options),
                    choice=True,
                )
            )
        elif question.kind == "grid":
            kind, labels = _type(question.options), _labels(question.options)
            for row in question.rows:
                item = row.code or row.row_id.partition(".")[2]
                found.append(
                    _Wanted(
                        row.row_id, f"{base}{SEPARATOR}{item}", row.text, kind, labels, choice=True
                    )
                )
        elif question.kind == "checkbox":
            for option in question.options:
                if option.other:
                    continue
                item = option.code or option.option_id.partition(".")[2]
                found.append(
                    _Wanted(
                        option.option_id,
                        f"{base}{SEPARATOR}{item}",
                        option.text,
                        CHECKBOX_TYPE,
                        choice=True,
                    )
                )
        if other is not None and question.kind in ("single", "checkbox"):
            found.append(
                _Wanted(other.option_id, f"{base}{SEPARATOR}{OTHER_CODE}", other.text, "text")
            )
    # Two items with the same code would give one name to two columns: the second keeps the
    # name made of its ids, which are unique, until the review has the codes changed.
    taken: set[str] = set()
    unique = []
    for wanted in found:
        name = wanted.name
        if name.lower() in taken:
            name = wanted.target.replace(".", SEPARATOR)
        if name.lower() in taken:
            raise DesignError([_("Deux variables auraient le nom {name}.").format(name=name)])
        taken.add(name.lower())
        unique.append(wanted if name == wanted.name else _replace(wanted, name))
    return unique


def wanted(project: Project) -> list[_Wanted]:
    """The variables the questionnaire plans: target, name, label, type, value labels."""
    return _wanted(project)


def _replace(wanted: _Wanted, name: str) -> _Wanted:
    return _Wanted(
        wanted.target, name, wanted.label, wanted.type, wanted.labels, wanted.long, wanted.choice
    )


def _question_of(entry: VariableEntry) -> str | None:
    return (entry.question.value or "").partition(".")[0] or None


def _file(wanted: _Wanted) -> FileMetadata:
    return FileMetadata(
        storage_type="numeric" if wanted.type in ("integer", "decimal") else "string",
        label=wanted.label,
        value_labels=[ValueLabel(code=c, label=t) for c, t in wanted.labels],
    )


def _privacy(wanted: _Wanted) -> Privacy:
    found = classify_planned(
        wanted.name,
        wanted.label,
        text=wanted.type == "text",
        choice=wanted.choice,
        long=wanted.long,
    )
    return Privacy(
        privacy_class=TrackedValue[str](value=found.privacy_class, origin="computed"),
        reasons=list(found.reasons),
    )


def _entry(wanted: _Wanted, position: int) -> VariableEntry:
    return VariableEntry(
        name=wanted.name,
        position=position,
        file=_file(wanted),
        planned=Planned(type=wanted.type),  # type: ignore[arg-type]
        privacy=_privacy(wanted),
        question=TrackedValue[str](value=wanted.target, origin="computed"),
        label=TrackedValue[str](value=wanted.label, origin="file"),
        description=TrackedValue[str](origin="human"),
        unit=TrackedValue[str](origin="human"),
        group_id=TrackedValue[str](origin="human"),
    )


def _update(entry: VariableEntry, wanted: _Wanted, position: int) -> None:
    """The questionnaire's planned metadata; what a person decided stays."""
    entry.position = position
    entry.file = _file(wanted)
    entry.planned = Planned(type=wanted.type)  # type: ignore[arg-type]
    if (
        entry.privacy.privacy_class.origin == "computed"
        and entry.privacy.privacy_class.status == "none"
    ):
        entry.privacy = _privacy(wanted)
    if entry.label.origin == "file" and entry.label.status == "none":
        entry.label = TrackedValue[str](value=wanted.label, origin="file")


# Where, beyond the groups, a project names a variable: what a rename must not break.
_CITING = {
    "plan": N_("le plan"),
    "recodes": N_("un recodage"),
    "exclusions": N_("une règle d'exclusion"),
    "dataset": N_("la description de la base"),
}
# Texts written by the team, which may say any word.
_FREE = {"statement", "reason", "note", "label", "description", "source", "meaning", "title"}


def _strings(data, key: str | None = None):
    if isinstance(data, dict):
        for k, v in data.items():
            if k not in _FREE:
                yield from _strings(v, k)
    elif isinstance(data, list):
        for v in data:
            yield from _strings(v, key)
    elif isinstance(data, str):
        yield data


def _cited(project: Project, name: str) -> list[str]:
    return [
        _(text)
        for part, text in _CITING.items()
        if name in set(_strings(getattr(project, part).model_dump(mode="json")))
    ]


def _rename_in_groups(project: Project, renamed: dict[str, str]) -> None:
    def new(names):
        return [renamed.get(n, n) for n in names]

    for group in project.groups:
        if group.members.value:
            group.members = group.members.model_copy(update={"value": new(group.members.value)})
        group.attached = new(group.attached)
        group.reverse_items = new(group.reverse_items)
        if group.scoring is not None and group.scoring.items:
            group.scoring = group.scoring.model_copy(update={"items": new(group.scoring.items)})


def plan_variables(project: Project) -> Changes:
    """Make the planned variables again from the questionnaire, in its order: a variable
    keeps its decisions through every change of its question; renamed when its codes change
    (and in its group); removed with its item. Refused when a renamed or removed variable is
    still cited by the plan, a recoding, an exclusion rule or the description of the base.
    Once the database is there (E4), its variables are the file's: the questionnaire changes
    alone, and the conformity report says what differs."""
    if project.source is not None:
        return Changes()
    wanted = _wanted(project)
    by_target = {e.question.value: e for e in project.variables if e.planned is not None}
    changes = Changes()
    kept = []
    for position, item in enumerate(wanted, start=1):
        entry = by_target.pop(item.target, None)
        if entry is None:
            entry = _entry(item, position)
            changes.added.append(item.name)
        else:
            if entry.name != item.name:
                changes.renamed[entry.name] = item.name
            _update(entry, item, position)
        kept.append(entry)
    changes.removed = [e.name for e in by_target.values()]
    refused = [
        _("{place} cite {name}").format(place=place, name=name)
        for name in [*changes.renamed, *changes.removed]
        for place in _cited(project, name)
    ]
    if refused:
        raise DesignError([_("Changez d'abord ce qui cite ces variables :"), *refused])
    for entry in kept:
        if entry.name in changes.renamed:
            entry.name = changes.renamed[entry.name]
    # Not cited elsewhere: a name decided for a variable now gone is let go with it.
    project.variables = kept
    _rename_in_groups(project, changes.renamed)
    _plan_conditions(project)
    _plan_groups(project)
    measure.propose(project)
    naming.propose(project)  # after the groups: a grid's names take its prefix
    return changes


def _on_variables(
    conditions: list[Condition], entries: dict[str | None, VariableEntry]
) -> list[Condition] | None:
    """The conditions on the names of the variables tested, a choice's code as the variable
    holds it (1, not "1"). None when a target is gone: nothing is carried until the condition
    is corrected, which the review says."""
    found = []
    for condition in conditions:
        terms = []
        for term in condition.terms:
            entry = entries.get(term.target)
            if entry is None:
                return None
            value = term.value
            if entry.planned is not None and entry.planned.type == "integer":
                value = [_integer(v) for v in value] if isinstance(value, list) else _integer(value)
            terms.append(Term(target=entry.name, operator=term.operator, value=value))
        found.append(Condition(combine=condition.combine, terms=terms))
    return found


def _integer(value):
    text = skip.code_text(value) if value is not None else ""
    return int(text) if text.lstrip("-").isdigit() else value


def _plan_conditions(project: Project) -> None:
    """Each planned variable carries its question's effective condition (D-168, "computed",
    a fact like its question); one typed by a person or read in a file stays."""
    found = questionnaire(project)
    questions = {q.question_id: q for q in found.questions}
    entries = {e.question.value: e for e in project.variables}
    for entry in project.variables:
        if entry.asked_if is not None and entry.asked_if.origin != "computed":
            continue
        question = questions.get(_question_of(entry) or "")
        conditions = skip.effective(found, question) if question else []
        carried = _on_variables(conditions, entries) if conditions else None
        entry.asked_if = (
            TrackedValue[list[Condition]](value=carried, origin="computed") if carried else None
        )


def _plan_groups(project: Project) -> None:
    """A group for each grid (a probable scale) and each set of boxes (D-044), made from its
    question; a group whose question is gone goes with it."""
    names = {e.question.value: e.name for e in project.variables}
    groups = {g.question: g for g in project.groups if g.question is not None}
    found = [g for g in project.groups if g.question is None]
    for question in questionnaire(project).questions:
        if question.kind == "grid":  # an attention check is attached, never a member
            rows = [r for r in question.rows if r.row_id in names]
            members = [names[r.row_id] for r in rows if not r.attention]
            attached = [names[r.row_id] for r in rows if r.attention]
            kind, part = "scale", GROUP_PARTS[0]
        elif question.kind == "checkbox":
            members = [
                names[o.option_id] for o in question.options if not o.other and o.option_id in names
            ]
            attached = [
                names[o.option_id] for o in question.options if o.other and o.option_id in names
            ]
            kind, part = "multiple_response", GROUP_PARTS[1]
        else:
            continue
        group = groups.get(question.question_id)
        if group is None:
            group = Group(
                group_id=f"G{_next(project, 'G')}",
                members=TrackedValue[list[str]](value=members, origin="computed"),
                basis=[BASIS],
                ai_hypothesis=TrackedValue[str](origin="human"),
                descriptive_label=TrackedValue[str](
                    value=part.format(n=len(members)), origin="computed"
                ),
                question=question.question_id,
            )
        group.kind = kind  # type: ignore[assignment]
        group.attached = attached
        group.members = group.members.model_copy(update={"value": members})
        if group.descriptive_label.origin == "computed":
            group.descriptive_label = TrackedValue[str](
                value=part.format(n=len(members)), origin="computed"
            )
        group.reverse_items = [n for n in group.reverse_items if n in members]
        if group.scoring is not None and group.scoring.items:
            items = [n for n in group.scoring.items if n in members]
            group.scoring = group.scoring.model_copy(update={"items": items})
        found.append(group)
    project.groups = found
    member_of = {n: g.group_id for g in found for n in (g.members.value or [])}
    for entry in project.variables:
        if entry.group_id.origin == "computed" or entry.group_id.value is None:
            gid = member_of.get(entry.name)
            entry.group_id = (
                TrackedValue[str](value=gid, origin="computed")
                if gid
                else TrackedValue[str](origin="human")
            )
