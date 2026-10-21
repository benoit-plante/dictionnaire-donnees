"""Close the loop (v0.20, step E3, D-150): compare the questionnaire of the project with a
structure re-exported from LimeSurvey, and with each version marked as sent.

The re-export is read by the tool's own reader (step A1) and matched by the codes of its
questions, without case, as LimeSurvey compares them; a question of the same text under
another code is "probably the same". Nothing changes by itself: each question that differs
is settled by a decision, "Reprendre dans le projet" (`take`, the project then says what
LimeSurvey says) or "Garder le projet" (LimeSurvey is then to be corrected).

Two versions of the designed questionnaire (a version sent, the current one) are matched by
the ids of their questions, which are never given again.

Since v0.21 (D-169), three more kinds of difference: a condition changed (said in words on
both sides), a condition LimeSurvey has that the tool could not read (it cannot be taken: to
correct in LimeSurvey or in the tool), a random order changed; for a question, and for a
section, matched by its rank. Conditions are compared by the codes they name, as LimeSurvey
names them, "among" one code being "=".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from difflib import SequenceMatcher

from ddict import design
from ddict.design import DesignError, Draft, Item
from ddict.i18n import N_, Texts, _
from ddict.project import skip
from ddict.project.model import (
    Condition,
    Project,
    Provenance,
    Publication,
    Question,
    Questionnaire,
    Section,
    Term,
)
from ddict.questionnaire import relevance
from ddict.questionnaire.read import normalize

KINDS = Texts(
    {
        "added": N_("Question ajoutée"),
        "removed": N_("Question retirée"),
        "renamed": N_("Probablement la même : même texte, autre code"),
        "changed": N_("Question changée"),
        "section": N_("Section changée"),
    }
)
FIELDS = Texts(
    {
        "text": N_("texte"),
        "kind": N_("nature"),
        "answer": N_("réponse attendue"),
        "layout": N_("présentation"),
        "required": N_("obligatoire"),
        "instruction": N_("consigne"),
        "other": N_("option « autre »"),
        "condition": N_("condition"),
        "condition_unread": N_("condition que l'outil ne lit pas"),
        "shuffle": N_("ordre aléatoire"),
    }
)
SENT = Texts(
    {"ethics": N_("Envoyé au comité d'éthique"), "limesurvey": N_("Publié dans LimeSurvey")}
)


def _words(text: str | None) -> str:
    """A text as the reader of a file gives it: its spaces and its compatibility characters
    normalized ("…" is "...")."""
    return normalize(" ".join((text or "").split()))


@dataclass(frozen=True)
class ItemChange:
    """A choice or an item that differs: added, removed, recoded or reworded."""

    kind: str  # "added", "removed", "recoded", "reworded"
    what: str  # "row" or "option"
    code: str | None
    text: str
    before: str | None = None  # the code or text it had


@dataclass
class Difference:
    """A question that differs between the project (`mine`) and the other side (`theirs`)."""

    kind: str  # "added", "removed", "renamed", "changed"
    mine: Question | None
    theirs: Question | None
    code: str  # the code (or id) it is known by
    fields: list[str] = field(default_factory=list)  # for "changed"
    items: list[ItemChange] = field(default_factory=list)
    # v0.21: a condition in words, the project's then the other side's; LimeSurvey's on the
    # ids of the project, to take it (None, with `refused`, when it cannot be).
    conditions: tuple[str, str] | None = None
    theirs_condition: Condition | None = None
    refused: str | None = None
    sections: tuple[Section, Section] | None = None  # kind "section"

    @property
    def title(self) -> str:
        return _(KINDS[self.kind])

    def words(self) -> list[tuple[str, str]]:
        """The text, word by word: ("=", "…") kept, ("-", "…") theirs lacks, ("+", "…") new."""
        if self.mine is None or self.theirs is None:
            return []
        before, after = _words(self.mine.text).split(), _words(self.theirs.text).split()
        found = []
        for tag, i1, i2, j1, j2 in SequenceMatcher(None, before, after).get_opcodes():
            if tag == "equal":
                found.append(("=", " ".join(before[i1:i2])))
                continue
            if i2 > i1:
                found.append(("-", " ".join(before[i1:i2])))
            if j2 > j1:
                found.append(("+", " ".join(after[j1:j2])))
        return found


def _items(question: Question) -> list[tuple[str, str | None, str]]:
    """What, code and text of the choices and items a platform keeps ("other" apart)."""
    found = [("row", r.code, _words(r.text)) for r in question.rows]
    found += [("option", o.code, _words(o.text)) for o in question.options if not o.other]
    return found


def _item_changes(mine: Question, theirs: Question) -> list[ItemChange]:
    found: list[ItemChange] = []
    for what in ("row", "option"):
        left = [(c, t) for w, c, t in _items(mine) if w == what]
        right = [(c, t) for w, c, t in _items(theirs) if w == what]
        right_codes = {c: t for c, t in right if c}
        left_codes = {c: t for c, t in left if c}
        used: set[tuple] = set()
        for code, text in left:
            if code in right_codes:
                used.add((code, right_codes[code]))
                if right_codes[code] != text:
                    found.append(ItemChange("reworded", what, code, right_codes[code], text))
                continue
            same = next(
                (
                    (c, t)
                    for c, t in right
                    if t == text and c not in left_codes and (c, t) not in used
                ),
                None,
            )
            if same is not None:
                used.add(same)
                found.append(ItemChange("recoded", what, same[0], text, code))
            else:
                found.append(ItemChange("removed", what, code, text))
        for code, text in right:
            if (code, text) not in used and code not in left_codes:
                found.append(ItemChange("added", what, code, text))
    return found


# --- Conditions, compared by the codes they name (v0.21). ---


@dataclass(frozen=True)
class _Names:
    """How each side names its targets: the project's ids and the re-export's, each to the
    name LimeSurvey gives it ("enfants", "climat_SQ002"), and back for the project."""

    mine: dict[str, str]
    theirs: dict[str, str]
    targets: dict[str, str]  # a name -> the project's id


def _project_names(project: Project) -> dict[str, str]:
    from ddict import design_limesurvey  # it imports the Word, which imports design

    found = design.questionnaire(project)
    ids = []
    for question in found.questions:
        ids.append(question.question_id)
        ids += [r.row_id for r in question.rows] + [o.option_id for o in question.options]
    named = {i: design_limesurvey.variable_name(project, i) for i in ids}
    return {i: n.lower() for i, n in named.items() if n}


def _names(project: Project, read: Questionnaire) -> _Names:
    from ddict.questionnaire.lss import names

    mine = _project_names(project)
    theirs = {target: name.lower() for name, (target, _n, _c) in names(read).items()}
    return _Names(mine, theirs, {n: i for i, n in mine.items()})


def _key(condition: Condition | None, names: dict[str, str] | None) -> tuple | None:
    found = relevance.canonical(condition)
    if found is None or names is None:
        return found
    combine, terms = found
    return (combine, tuple((names.get(t, t), o, v) for t, o, v in terms))


def _on_project(condition: Condition | None, names: _Names) -> Condition | None:
    """LimeSurvey's condition on the ids of the project; DesignError when it names what the
    project does not have."""
    if condition is None:
        return None
    terms = []
    for term in condition.terms:
        name = names.theirs.get(term.target)
        target = names.targets.get(name or "")
        if target is None:
            raise DesignError(
                [_("La condition de LimeSurvey vise {name}, que le projet n'a pas.").format(
                    name=name or term.target)]
            )  # fmt: skip
        terms.append(Term(target=target, operator=term.operator, value=term.value))
    return Condition(combine=condition.combine, terms=terms)


def _condition_fields(mine, theirs, names: _Names | None) -> list[str]:
    found = []
    if theirs.condition_unread:
        found.append("condition_unread")
    elif _key(mine.condition, names.mine if names else None) != _key(
        theirs.condition, names.theirs if names else None
    ):
        found.append("condition")
    if mine.shuffle != theirs.shuffle:
        found.append("shuffle")
    return found


def _said(project: Project, condition: Condition | None) -> str:
    return skip.team_text(project, condition) if condition else _("Toujours posée")


def _with_conditions(project: Project, difference: Difference, names: _Names | None) -> None:
    """The conditions in words, and LimeSurvey's on the project's ids, to take it."""
    mine = difference.mine if difference.sections is None else difference.sections[0]
    theirs = difference.theirs if difference.sections is None else difference.sections[1]
    if theirs is None or names is None:
        return
    if theirs.condition_unread:
        difference.refused = _(
            "La condition de LimeSurvey n'est pas de la forme que l'outil écrit : corrigez-la "
            "dans LimeSurvey, ou dans l'outil puis réimportez."
        )
        said = theirs.condition_unread
    else:
        try:
            difference.theirs_condition = _on_project(theirs.condition, names)
            said = _said(project, difference.theirs_condition)
        except DesignError as error:
            difference.refused = error.reasons[0]
            said = difference.refused
    if {"condition", "condition_unread"} & set(difference.fields):
        difference.conditions = (_said(project, mine.condition if mine else None), said)


def _fields(mine: Question, theirs: Question) -> list[str]:
    found = []
    if _words(mine.text) != _words(theirs.text):
        found.append("text")
    for name in ("kind", "answer", "layout", "required"):
        if getattr(mine, name) != getattr(theirs, name):
            found.append(name)
    if _words(mine.instruction) != _words(theirs.instruction):
        found.append("instruction")
    if any(o.other for o in mine.options) != any(o.other for o in theirs.options):
        found.append("other")
    return found


def _compare(
    mine: Question, theirs: Question, code: str, names: _Names | None = None
) -> Difference | None:
    fields = _fields(mine, theirs) + _condition_fields(mine, theirs, names)
    items = _item_changes(mine, theirs)
    if not fields and not items:
        return None
    return Difference("changed", mine, theirs, code, fields, items)


def _sections(project: Project, read: Questionnaire, names: _Names) -> list[Difference]:
    """The sections that differ by their condition or their random order, matched by rank."""
    found = []
    for mine, theirs in zip(design.questionnaire(project).sections, read.sections, strict=False):
        fields = _condition_fields(mine, theirs, names)
        if fields:
            difference = Difference(
                "section", None, None, mine.title or mine.section_id, fields,
                sections=(mine, theirs),
            )  # fmt: skip
            _with_conditions(project, difference, names)
            found.append(difference)
    return found


def with_limesurvey(project: Project, read: Questionnaire) -> list[Difference]:
    """The questions that differ between the project and a structure re-exported from
    LimeSurvey, in the order of the project, then those added in LimeSurvey."""
    questions = design.questionnaire(project).questions
    theirs = {(q.code or "").lower(): q for q in read.questions}
    names = _names(project, read)
    found: list[Difference] = _sections(project, read, names)
    unmatched_mine: list[Question] = []
    for question in questions:
        code = design.code(project, question)
        other = theirs.pop(code.lower(), None)
        if other is None:
            unmatched_mine.append(question)
            continue
        difference = _compare(question, other, code, names)
        if difference is not None:
            _with_conditions(project, difference, names)
            found.append(difference)
    for question in unmatched_mine:
        code = design.code(project, question)
        same = next((q for q in theirs.values() if _words(q.text) == _words(question.text)), None)
        if same is not None:
            theirs.pop((same.code or "").lower())
            found.append(Difference("renamed", question, same, code))
        else:
            found.append(Difference("removed", question, None, code))
    for question in theirs.values():
        difference = Difference("added", None, question, question.code or question.question_id)
        _with_conditions(project, difference, names)
        found.append(difference)
    return found


def since(publication: Publication, project: Project) -> list[Difference]:
    """What changed in the questionnaire since a version sent, matched by the ids."""
    before = {q.question_id: q for q in publication.questionnaire.questions}
    found: list[Difference] = []
    for question in design.questionnaire(project).questions:
        old = before.pop(question.question_id, None)
        if old is None:
            found.append(Difference("added", None, question, question.question_id))
            continue
        difference = _compare(old, question, question.question_id)
        if difference is not None:
            found.append(difference)
    for old in before.values():
        found.append(Difference("removed", old, None, old.question_id))
    return found


# --- Settling a difference. ---


def _draft(theirs: Question, mine: Question | None, section: str) -> Draft:
    """LimeSurvey's version of a question, keeping the ids of the project's items of the
    same code (their variables keep their decisions) and the provenance of the project."""
    rows = {r.code: r for r in (mine.rows if mine else []) if r.code}
    options = {o.code: o for o in (mine.options if mine else []) if o.code and not o.other}
    other = next((o for o in (mine.options if mine else []) if o.other), None)

    def kept(found, mine_item, text: str, code: str | None, is_other: bool = False) -> Item:
        return Item(
            text,
            code,
            other=is_other,
            provenance=mine_item.provenance if mine_item is not None else None,
            item_id=getattr(mine_item, found) if mine_item is not None else None,
        )

    return Draft(
        kind=theirs.kind,
        text=theirs.text,
        section=section,
        instruction=theirs.instruction,
        required=theirs.required,
        answer=theirs.answer,
        layout=theirs.layout,
        provenance=mine.provenance if mine is not None else Provenance(kind="team"),
        options=tuple(
            kept("option_id", other, o.text, None, True)
            if o.other
            else kept("option_id", options.get(o.code), o.text, o.code)
            for o in theirs.options
        ),
        rows=tuple(kept("row_id", rows.get(r.code), r.text, r.code) for r in theirs.rows),
    )


def _other_text(mine: Question | None, theirs: Question) -> Question:
    """LimeSurvey's export does not say the text of an "other" option: the project's is
    kept."""
    if mine is None:
        return theirs
    text = next((o.text for o in mine.options if o.other), None)
    if text is None:
        return theirs
    options = [o.model_copy(update={"text": text}) if o.other else o for o in theirs.options]
    return theirs.model_copy(update={"options": options})


def _take_conditions(project: Project, owner: str, difference: Difference, theirs) -> None:
    """LimeSurvey's condition and random order, once the rest is taken (v0.21)."""
    if difference.kind == "added" or "condition" in difference.fields:
        design.set_condition(project, owner, difference.theirs_condition)
    if difference.kind == "added" or "shuffle" in difference.fields:
        if theirs.shuffle:
            design.set_shuffle(project, owner, True)
        elif "shuffle" in difference.fields:
            design.set_shuffle(project, owner, False)


def take(project: Project, difference: Difference, *, now: str) -> None:
    """ "Reprendre dans le projet": the project says what LimeSurvey says. Raises
    DesignError, the project unchanged, when the change is refused (a condition LimeSurvey
    has that the tool cannot read, or that names what the project does not have)."""
    found = design.questionnaire(project)
    if difference.refused and (  # refused before anything changes
        difference.kind == "added" or {"condition", "condition_unread"} & set(difference.fields)
    ):
        raise DesignError([difference.refused])
    if difference.kind == "section":
        mine, theirs = difference.sections
        _take_conditions(project, mine.section_id, difference, theirs)
        return
    if difference.kind == "removed":
        design.remove_question(project, difference.mine.question_id)
        return
    if difference.kind == "added":
        theirs = difference.theirs
        section = _section_of(project, difference)
        question_id = design.add_question(project, _draft(theirs, None, section))
        if theirs.code:
            design.decide_code(project, question_id, "write", now=now, value=theirs.code.lower())
        _take_conditions(project, question_id, difference, theirs)
        return
    mine = difference.mine
    if difference.kind == "renamed":
        code = (difference.theirs.code or "").lower()
        design.decide_code(project, mine.question_id, "write", now=now, value=code)
        return
    theirs = _other_text(mine, difference.theirs)
    section = mine.section or found.sections[0].section_id
    design.modify_question(project, mine.question_id, _draft(theirs, mine, section))
    _take_conditions(project, mine.question_id, difference, theirs)


def _section_of(project: Project, difference: Difference) -> str:
    """The section of a question added in LimeSurvey: the one of the same rank as its group,
    else the last."""
    sections = design.questionnaire(project).sections
    rank = None
    if difference.theirs is not None and difference.theirs.section:
        rank = int(difference.theirs.section.lstrip("S") or 0) - 1
    if rank is not None and 0 <= rank < len(sections):
        return sections[rank].section_id
    return sections[-1].section_id


# --- Marking as sent (D-150). ---


def mark_sent(project: Project, kind: str, day: str | None = None, note: str | None = None):
    """Keep a copy of the questionnaire as sent to the ethics committee or published in
    LimeSurvey, with its fingerprint. A reason is never required."""
    found = design.questionnaire(project)
    project.design.publications.append(
        Publication(
            kind=kind,  # type: ignore[arg-type]
            date=day or date.today().isoformat(),
            fingerprint=found.sha256,
            questionnaire=found.model_copy(deep=True),
            note=(note or "").strip() or None,
        )
    )


def warnings(project: Project) -> list[str]:
    """What a change made after a version was sent asks for: one line per place."""
    found = design.questionnaire(project)
    last: dict[str, Publication] = {}
    for publication in project.design.publications:
        last[publication.kind] = publication
    texts = {
        "limesurvey": N_(
            "Ce questionnaire a été publié dans LimeSurvey le {date} et a changé depuis : "
            "LimeSurvey doit être mis à jour (un nouveau fichier est proposé ci-dessous)."
        ),
        "ethics": N_(
            "Ce questionnaire a été envoyé au comité d'éthique le {date} et a changé depuis : "
            "le comité devra peut-être recevoir une modification."
        ),
    }
    return [
        _(texts[kind]).format(date=publication.date)
        for kind, publication in sorted(last.items())
        if publication.fingerprint != found.sha256
    ]
