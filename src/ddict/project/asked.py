"""A variable's condition declared by the team (v0.21, D-168): for a database without a
designed questionnaire (a SurveyMonkey export, a .sav already there), "asked if" on the
variables, by their original names. The same functions for the page of a variable and the
command line (`ddict conditions`).

A condition typed by a person is a decision ("human"): never proposed by a computation nor
by the AI. One read in a LimeSurvey file is a proposal ("questionnaire") until a person
accepts it. Refused, as in the designed questionnaire (§ 5.1 of the plan): an unknown target,
the variable itself, an operator its nature does not admit, a code it does not have, a value
that is not a number for a number; and a term on the value of an identifier or a free text
(only "has an answer": a condition never names what a person wrote).
"""

from __future__ import annotations

from collections.abc import Sequence

from ddict.i18n import _
from ddict.project import aside, skip
from ddict.project.decisions import reject, validate
from ddict.project.model import Condition, Project, Term, TrackedValue, VariableEntry
from ddict.questionnaire.labels import accepted_labels

# Never a term on their value (D-006, D-168).
PRIVATE = ("likely_identifier", "free_text")
NUMBERS = ("integer", "decimal")


class AskedError(ValueError):
    """A condition refused, with the reasons in plain language; nothing changed."""

    def __init__(self, reasons: list[str]) -> None:
        super().__init__("; ".join(reasons))
        self.reasons = reasons


def nature(project: Project, entry: VariableEntry) -> str:
    """What a term on the variable may test (a key of `skip.OPERATORS`): an option to tick
    (a member of a multiple-response group), a choice (value labels), a number, a text."""
    if entry.name in skip.boxes_of(project):
        return "box"
    if accepted_labels(entry):
        return "choice"
    if entry.data_type in NUMBERS or (entry.planned is not None and entry.planned.type in NUMBERS):
        return "number"
    return "text"


def codes(entry: VariableEntry) -> set[str]:
    """The codes a choice may be compared with: its value labels, and the codes observed."""
    found = {skip.code_text(v.code) for v in accepted_labels(entry)}
    if entry.profile is not None:
        found |= {skip.code_text(v.code) for v in entry.profile.observed_values or []}
    return found


def _value(value):
    """A code as the variable holds it: 1, not "1"."""
    text = skip.code_text(value)
    return int(text) if text.lstrip("-").isdigit() else value


def normalized(project: Project, condition: Condition) -> Condition:
    entries = {e.name: e for e in project.variables}
    terms = []
    for term in condition.terms:
        value = term.value
        entry = entries.get(term.target)
        if entry is not None and value is not None and nature(project, entry) != "text":
            value = [_value(v) for v in value] if isinstance(value, list) else _value(value)
        terms.append(Term(target=term.target, operator=term.operator, value=value))
    return Condition(combine=condition.combine, terms=terms)


def problems(project: Project, owners: Sequence[str], conditions: Sequence[Condition]) -> list[str]:
    """Why these conditions cannot be declared on these variables."""
    entries = {e.name: e for e in aside.kept(project)}
    found = [
        _("Variable inconnue : {name}.").format(name=name) for name in owners if name not in entries
    ]
    for condition in conditions:
        for term in condition.terms:
            target = entries.get(term.target)
            if target is None:
                found.append(_("Variable inconnue : {name}.").format(name=term.target))
                continue
            if term.target in owners:
                found.append(_("{name} ne peut pas dépendre d'elle-même.").format(name=term.target))
                continue
            kind = nature(project, target)
            private = (target.privacy.privacy_class.value or "ordinary") in PRIVATE
            if private and term.operator != "answered":
                found.append(
                    _(
                        "{name} est un identifiant ou un texte libre : une condition ne nomme "
                        "jamais sa valeur, seulement « a une réponse »."
                    ).format(name=term.target)
                )
                continue
            if term.operator not in (*skip.OPERATORS[kind], "answered"):
                found.append(
                    _("Cet opérateur ne convient pas à {target}.").format(target=term.target)
                )
                continue
            if kind == "choice":
                known = codes(target)
                found += [
                    _("{value} n'est pas un choix de {target}.").format(
                        value=skip.code_text(v), target=term.target
                    )
                    for v in skip.values_of(term)
                    if skip.code_text(v) not in known
                ]
            elif kind == "number":
                found += [
                    _("{target} attend un nombre.").format(target=term.target)
                    for v in skip.values_of(term)
                    if skip.as_number(v) is None
                ]
    return found


def set_asked_if(
    project: Project, names: Sequence[str], conditions: Sequence[Condition] | None, *, now: str
) -> None:
    """Declare the same conditions on these variables (a grid's items at once); None: always
    asked. Raises AskedError, the project unchanged."""
    if conditions:
        conditions = [normalized(project, c) for c in conditions]
        found = problems(project, names, conditions)
        if found:
            raise AskedError(found)
    entries = {e.name: e for e in project.variables}
    unknown = [n for n in names if n not in entries]
    if unknown:
        raise AskedError([_("Variable inconnue : {name}.").format(name=n) for n in unknown])
    for name in names:
        entry = entries[name]
        entry.asked_if = (
            TrackedValue[list[Condition]](value=list(conditions), origin="human", updated_at=now)
            if conditions
            else None
        )


def decide(project: Project, name: str, action: str, *, now: str) -> None:
    """Accept or reject a condition read in a LimeSurvey file."""
    entry = next((e for e in project.variables if e.name == name), None)
    if entry is None or entry.asked_if is None or entry.asked_if.status != "proposed":
        raise AskedError([_("Aucune condition proposée pour {name}.").format(name=name)])
    entry.asked_if = (validate if action == "accept" else reject)(entry.asked_if, now=now)


def propose_from_lss(project: Project) -> list[str]:
    """The conditions of a LimeSurvey structure read for a database already there (v0.20, A3;
    D-168): each variable of a filtered question gets them, on the names of the variables its
    terms name, as a proposal to accept. Nothing for a term whose target is linked to no
    variable or to several, nor for a condition the tool could not read. Returns the names."""
    found = project.questionnaire
    if found is None or found.format != "lss":
        return []
    for entry in project.variables:  # a former reading's proposals go with it
        if (
            entry.asked_if is not None
            and entry.asked_if.origin == "questionnaire"
            and (entry.asked_if.status == "proposed")
        ):
            entry.asked_if = None
    from ddict.questionnaire import link

    # Each variable's question: its link, else the one its LimeSurvey code makes sure.
    sure = link.sure_choices(project)
    target_of = {e.name: e.question.value or sure.get(e.name) for e in project.variables}
    linked: dict[str, list[VariableEntry]] = {}
    for entry in project.variables:
        if target_of[entry.name]:
            linked.setdefault(target_of[entry.name], []).append(entry)
    questions = {q.question_id: q for q in found.questions}
    proposed = []
    for entry in aside.kept(project):
        question = questions.get((target_of[entry.name] or "").partition(".")[0])
        if entry.asked_if is not None or question is None:
            continue
        conditions = []
        for condition in skip.effective(found, question):
            targets = [linked.get(t.target, []) for t in condition.terms]
            if any(len(t) != 1 for t in targets):
                conditions = []
                break
            terms = [
                Term(target=t[0].name, operator=term.operator, value=term.value)
                for t, term in zip(targets, condition.terms, strict=True)
            ]
            conditions.append(
                normalized(project, Condition(combine=condition.combine, terms=terms))
            )
        if conditions:
            entry.asked_if = TrackedValue[list[Condition]](
                value=conditions, origin="questionnaire", status="proposed"
            )
            proposed.append(entry.name)
    return proposed
