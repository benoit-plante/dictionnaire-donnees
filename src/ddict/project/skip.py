"""When a question is asked (v0.21, D-165, D-167, D-168).

A condition is a list of terms joined all by "and" or all by "or"; a section's condition and
its question's are joined by "and" (the effective condition). In a designed questionnaire the
terms name ids ("Q3", "Q7.r2", "Q10.o2"), which are never given again, so that a changed code
does not break them; on a variable (`asked_if`) they name the original names of variables.

One rule gives the meaning: a term on an empty answer, or on a question not asked, is false,
whatever its operator. It is the rule written for LimeSurvey and the one applied to the
database when it arrives, so both say the same thing.

The database is read as it was recorded, before the missing codes are taken out: "Prefers not
to answer" (9) is a choice, and "Q3 ≠ 1" holds for it, as in LimeSurvey.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import pandas as pd

from ddict import i18n
from ddict.i18n import _
from ddict.project.model import Condition, Project, Question, Questionnaire, Term

# What a term may test, for each nature of target (D-165).
OPERATORS = {
    "choice": ("eq", "ne", "in", "not_in", "answered"),  # a single choice, a grid's statement
    "box": ("checked",),  # an option of a checkbox question
    "number": ("eq", "ne", "lt", "le", "gt", "ge", "answered"),
    "text": ("answered",),  # a short or long text, a date
}
SYMBOLS = {"eq": "=", "ne": "≠", "lt": "<", "le": "≤", "gt": ">", "ge": "≥"}
# What an unticked box holds, in an export that writes one ("N", 0); LimeSurvey leaves it empty.
UNTICKED = ("N", "0")


@dataclass(frozen=True)
class Target:
    """What a term of a designed questionnaire aims at."""

    nature: str  # a key of OPERATORS
    question: Question
    item: str | None = None  # the text of the statement or of the option


def target_of(found: Questionnaire, target: str) -> Target | None:
    """The question, statement or option a term names; None for one that cannot be tested:
    unknown, a whole grid or checkbox question, a displayed text, an "other" option."""
    question_id = target.partition(".")[0]
    question = next((q for q in found.questions if q.question_id == question_id), None)
    if question is None:
        return None
    if target == question_id:
        if question.kind == "single":
            return Target("choice", question)
        if question.kind == "open":
            return Target("number" if question.answer == "number" else "text", question)
        return None
    if question.kind == "grid":
        row = next((r for r in question.rows if r.row_id == target), None)
        return Target("choice", question, row.text) if row else None
    if question.kind == "checkbox":
        option = next((o for o in question.options if o.option_id == target), None)
        return Target("box", question, option.text) if option and not option.other else None
    return None


def choices(question: Question) -> dict[str, str]:
    """The codes of a question's choices (a grid's columns) and their texts; the "other"
    option is not one."""
    return {o.code: o.text for o in question.options if o.code and not o.other}


def code_text(value) -> str:
    """A code as written in the questionnaire: 1, 1.0 and "1" are "1"."""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def as_number(value) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    try:
        return float(str(value).strip().replace(",", "."))
    except ValueError:
        return None


def values_of(term: Term) -> list:
    if term.value is None:
        return []
    return term.value if isinstance(term.value, list) else [term.value]


def owner_of(found: Questionnaire, owner: str) -> list[str]:
    """The ids a condition on this section or question may not name: the question itself and
    its items (a section's own questions are a review point, a cycle, not a refusal)."""
    return [owner] if owner.startswith("S") else [owner, f"{owner}."]


def normalized(found: Questionnaire, condition: Condition) -> Condition:
    """The values as the questionnaire writes them: a choice's code as a text ("1"), a number
    as a number (18, 2.5); what cannot be read is left as it is, for `problems` to say."""
    terms = []
    for term in condition.terms:
        target = target_of(found, term.target)
        value = term.value
        if target is not None and target.nature == "choice" and value is not None:
            value = [code_text(v) for v in value] if isinstance(value, list) else code_text(value)
        elif target is not None and target.nature == "number" and value is not None:
            number = as_number(value)
            if number is not None:
                value = int(number) if number.is_integer() else number
        terms.append(Term(target=term.target, operator=term.operator, value=value))
    return Condition(combine=condition.combine, terms=terms)


def problems(found: Questionnaire, owner: str, condition: Condition) -> list[str]:
    """Why a condition cannot be saved on this section or question (D-165): what is allowed
    but doubtful is the review's (`design_points`), not a refusal."""
    found_problems = []
    own = owner_of(found, owner)
    for term in condition.terms:
        if term.target == own[0] or (len(own) > 1 and term.target.startswith(own[1])):
            found_problems.append(_("Une question ne peut pas dépendre d'elle-même."))
            continue
        target = target_of(found, term.target)
        if target is None:
            found_problems.append(
                _(
                    "{target} ne peut pas servir de condition : visez une question à choix, un "
                    "énoncé de grille, une option à cocher, un nombre ou un texte."
                ).format(target=term.target)
            )
            continue
        if term.operator not in OPERATORS[target.nature]:
            found_problems.append(
                _("Cet opérateur ne convient pas à {target}.").format(target=term.target)
            )
            continue
        if target.nature == "choice":
            codes = choices(target.question)
            for value in values_of(term):
                if code_text(value) not in codes:
                    found_problems.append(
                        _("{value} n'est pas un choix de {target}.").format(
                            value=code_text(value), target=term.target
                        )
                    )
        elif target.nature == "number":
            for value in values_of(term):
                if as_number(value) is None:
                    found_problems.append(
                        _("{target} attend un nombre.").format(target=term.target)
                    )
    return found_problems


def effective(found: Questionnaire, question: Question) -> list[Condition]:
    """The conditions that must all hold for the question to be asked: its section's, then
    its own."""
    section = next((s for s in found.sections if s.section_id == question.section), None)
    return [c for c in (section.condition if section else None, question.condition) if c]


def targets(condition: Condition) -> list[str]:
    return [term.target for term in condition.terms]


def citing(found: Questionnaire, question_id: str) -> list[str]:
    """The sections and questions whose condition names this question or one of its items."""
    prefix = f"{question_id}."
    owners = [(s.section_id, s.condition) for s in found.sections]
    owners += [(q.question_id, q.condition) for q in found.questions]
    return [
        owner
        for owner, condition in owners
        if condition is not None
        and owner != question_id
        and any(t == question_id or t.startswith(prefix) for t in targets(condition))
    ]


# --- In plain words (one function for the editor, the review, the Word, the codebook). ---


def numbers(found: Questionnaire) -> dict[str, int]:
    """The questions' numbers as a person answering sees them (a displayed text has none)."""
    found_numbers = {}
    for question in found.questions:
        if question.kind != "display":
            found_numbers[question.question_id] = len(found_numbers) + 1
    return found_numbers


def _quoted(text: str) -> str:
    return _("« {text} »").format(text=text)


def _number_text(value) -> str:
    number = as_number(value)
    if number is None:
        return str(value)
    return i18n.decimal(str(int(number) if number.is_integer() else number))


def _either(texts: list[str]) -> str:
    """« A », « B » ou « C »."""
    if len(texts) <= 1:
        return "".join(texts)
    return _("{first} ou {last}").format(first=", ".join(texts[:-1]), last=texts[-1])


def _committee_term(found: Questionnaire, term: Term, section: bool) -> str:
    """One term, for the committee: in the language of the study, with the question's number
    and its words, never a code nor a name."""
    target = target_of(found, term.target)
    if target is None:
        return term.target  # gone since; the review says it
    number = numbers(found).get(target.question.question_id)
    where = (
        _("à l'énoncé {row} de la question {n}").format(row=_quoted(target.item), n=number)
        if target.nature == "choice" and target.item is not None
        else _("à la question {n}").format(n=number)
    )
    codes = choices(target.question)
    said = _either([_quoted(codes.get(code_text(v), code_text(v))) for v in values_of(term)])
    if term.operator == "answered":
        return (_("qui ont répondu {where}") if section else _("vous avez répondu {where}")).format(
            where=where
        )
    if term.operator == "checked":
        text = (
            _("qui ont coché {option} à la question {n}")
            if section
            else _("vous avez coché {option} à la question {n}")
        )
        return text.format(option=_quoted(target.item), n=number)
    if target.nature == "choice":
        if term.operator in ("eq", "in"):
            text = (
                _("qui ont répondu {said} {where}")
                if section
                else _("vous avez répondu {said} {where}")
            )
        else:
            text = (
                _("qui ont répondu autre chose que {said} {where}")
                if section
                else _("vous avez répondu autre chose que {said} {where}")
            )
        return text.format(said=said, where=where)
    value = _number_text(values_of(term)[0])
    answer = {
        "eq": _("est {value}"),
        "ne": _("n'est pas {value}"),
        "lt": _("est inférieure à {value}"),
        "le": _("est {value} ou moins"),
        "gt": _("est supérieure à {value}"),
        "ge": _("est {value} ou plus"),
    }[term.operator].format(value=value)
    text = (
        _("dont la réponse à la question {n} {answer}")
        if section
        else _("votre réponse à la question {n} {answer}")
    )
    return text.format(n=number, answer=answer)


def committee_text(project: Project, condition: Condition, *, section: bool = False) -> str:
    """A section's or a question's condition as the committee and a person answering read it:
    « Si vous avez répondu « Oui » à la question 3 » ; « Cette section s'adresse aux
    personnes qui ont répondu … ». In the language in use (the Word sets the study's)."""
    found = project.questionnaire
    clauses = [_committee_term(found, t, section) for t in condition.terms]
    if section:
        joined = (_(" et ") if condition.combine == "all" else _(" ou ")).join(clauses)
        return _("Cette section s'adresse aux personnes {clauses}").format(clauses=joined)
    joined = (_(" et si ") if condition.combine == "all" else _(" ou si ")).join(clauses)
    return _("Si {clauses}").format(clauses=joined)


def _team_target(project: Project, target: Target, term: Term, names: Mapping[str, str]) -> str:
    """« Q3 (enfants) » : the question's number and its code once decided; for a statement,
    the name of its variable (« Q7 (climat_SQ002) »), or its own code until then."""
    from ddict import design  # design imports this module

    question = target.question
    number = numbers(project.questionnaire).get(question.question_id)
    decided = design.code(project, question) != question.question_id
    if target.nature == "choice" and target.item is not None:
        row = next(r for r in question.rows if r.row_id == term.target)
        said = names.get(term.target) if decided else row.code
        return f"Q{number} ({said})" if said else f"Q{number}"
    return f"Q{number} ({design.code(project, question)})" if decided else f"Q{number}"


def _labelled(value, labels: Mapping[str, str]) -> str:
    code = code_text(value)
    return f"{code} ({labels[code]})" if code in labels else code


def _team_term(term: Term, subject: str, labels: Mapping[str, str], item: str | None) -> str:
    values = [_labelled(v, labels) for v in values_of(term)]
    if term.operator == "answered":
        return _("{subject} a une réponse").format(subject=subject)
    if term.operator == "checked":
        if item is None:  # a variable: the option is its own
            return _("{subject} coché").format(subject=subject)
        return _("{subject} : {option} coché").format(subject=subject, option=item)
    if term.operator in ("in", "not_in"):
        symbol = "∈" if term.operator == "in" else "∉"
        return f"{subject} {symbol} {{{', '.join(values)}}}"
    value = values[0] if labels else _number_text(values_of(term)[0])
    return f"{subject} {SYMBOLS[term.operator]} {value}"


def _joined(texts: list[list[str]], combines: list[str]) -> str:
    """Terms joined by "and" or "or"; with two conditions, an "or" of several terms between
    brackets: « (A ou B) et C »."""
    parts = []
    for terms, combine in zip(texts, combines, strict=True):
        part = (_(" et ") if combine == "all" else _(" ou ")).join(terms)
        parts.append(
            f"({part})" if len(texts) > 1 and len(terms) > 1 and combine == "any" else part
        )
    return _(" et ").join(parts)


def team_text(project: Project, conditions: Condition | Sequence[Condition]) -> str:
    """A designed questionnaire's conditions for the team: « Posée si Q3 (enfants) = 1 (Oui) »."""
    from ddict import design  # the names of the planned variables; design imports this module

    if isinstance(conditions, Condition):
        conditions = [conditions]
    found = project.questionnaire
    names = {w.target: w.name for w in design.wanted(project)}
    texts = []
    for condition in conditions:
        terms = []
        for term in condition.terms:
            target = target_of(found, term.target)
            if target is None:
                terms.append(term.target)
                continue
            subject = _team_target(project, target, term, names)
            labels = choices(target.question) if target.nature == "choice" else {}
            terms.append(_team_term(term, subject, labels, target.item))
        texts.append(terms)
    return _("Posée si {condition}").format(
        condition=_joined(texts, [c.combine for c in conditions])
    )


def variable_condition(
    project: Project, conditions: Sequence[Condition], names: Mapping[str, str] | None = None
) -> str:
    """A variable's conditions (`asked_if`) for the codebook, with the value labels in force:
    "enfants = 1 (Oui)"; `names`: the names the export shows (a renamed variable's)."""
    from ddict.questionnaire.labels import accepted_labels

    entries = {e.name: e for e in project.variables}
    texts = []
    for condition in conditions:
        terms = []
        for term in condition.terms:
            entry = entries.get(term.target)
            labels = {code_text(v.code): v.label for v in accepted_labels(entry)} if entry else {}
            if term.operator in ("lt", "le", "gt", "ge"):
                labels = {}
            subject = (names or {}).get(term.target, term.target)
            terms.append(_team_term(term, subject, labels, None))
        texts.append(terms)
    return _joined(texts, [c.combine for c in conditions])


def variable_text(
    project: Project, conditions: Sequence[Condition], names: Mapping[str, str] | None = None
) -> str:
    """ "Posée si enfants = 1 (Oui)"."""
    return _("Posée si {condition}").format(
        condition=variable_condition(project, conditions, names)
    )


def attention_text(question: Question, correct: Sequence[str]) -> str:
    """The right answers of an attention check, with their texts: "bonne réponse 4 (Plutôt
    d'accord)", "bonnes réponses 1 (Oui), 2 (Non)"."""
    codes = choices(question)
    said = ", ".join(_labelled(c, codes) for c in correct)
    if len(correct) == 1:
        return _("bonne réponse {codes}").format(codes=said)
    return _("bonnes réponses {codes}").format(codes=said)


# --- On a table: who was asked (D-167). ---


def _blank(column: pd.Series) -> pd.Series:
    missing = column.isna()
    if column.dtype == object or pd.api.types.is_string_dtype(column):
        missing |= column.astype("string").str.strip().fillna("") == ""
    return missing


def _texts(column: pd.Series) -> pd.Series:
    return column.map(lambda v: "" if pd.isna(v) else code_text(v))


def _holds(data: pd.DataFrame, term: Term) -> pd.Series:
    """Whether the term holds for each person: never on an empty cell."""
    if term.target not in data.columns:
        raise ValueError(f"no column for the condition: {term.target}")
    column = data[term.target]
    answered = ~_blank(column)
    if term.operator == "answered":
        return answered
    texts = _texts(column)
    if term.operator == "checked":
        return answered & ~texts.isin(UNTICKED)
    numbers_ = pd.to_numeric(column, errors="coerce")
    if term.operator in ("eq", "ne", "in", "not_in"):
        hit = pd.Series(False, index=data.index)
        for value in values_of(term):
            hit |= texts == code_text(value)
            number = as_number(value)
            if number is not None:
                hit |= numbers_ == number
        return answered & (hit if term.operator in ("eq", "in") else ~hit)
    number = as_number(values_of(term)[0])
    compare = {"lt": numbers_.lt, "le": numbers_.le, "gt": numbers_.gt, "ge": numbers_.ge}
    return answered & compare[term.operator](number).fillna(False).astype(bool)


def holds(data: pd.DataFrame, conditions: Sequence[Condition]) -> pd.Series:
    """Whether all the conditions hold, for each person."""
    found = pd.Series(True, index=data.index)
    for condition in conditions:
        each = [_holds(data, term) for term in condition.terms]
        joined = each[0]
        for other in each[1:]:
            joined = (joined & other) if condition.combine == "all" else (joined | other)
        found &= joined
    return found


def asked(data: pd.DataFrame, conditions: Mapping[str, Sequence[Condition]]) -> pd.DataFrame:
    """For each variable with conditions, whether each person was asked it, on the table as
    recorded (before the missing codes are taken out).

    The cascade of LimeSurvey comes by itself: a question not asked is empty, so a term on it
    is false; an answer recorded under a false condition (an anomaly) counts, for the
    conditions that name it, as the answer it holds, since it is what the database says."""
    return pd.DataFrame(
        {name: holds(data, found) for name, found in conditions.items()}, index=data.index
    )


ANSWER, MISSING, NOT_APPLICABLE, ANOMALY = "answer", "missing", "not_applicable", "anomaly"


def _ticked(column: pd.Series) -> pd.Series:
    return _holds(pd.DataFrame({"box": column}), Term(target="box", operator="checked"))


def natures(
    data: pd.DataFrame,
    conditions: Mapping[str, Sequence[Condition]],
    boxes: Mapping[str, Sequence[str]] | None = None,
) -> pd.DataFrame:
    """For each variable with conditions and each person: an answer, a missing answer (asked,
    left empty), not applicable (not asked, empty) or an anomaly (an answer, not asked).

    `boxes`: for an option to tick, the options of its question. An option left unticked is
    an answer ("not ticked") when another box of the question is ticked; missing only when
    none is, as the codebook says it."""
    was_asked = asked(data, conditions)
    found = {}
    for name in conditions:
        others = (boxes or {}).get(name)
        if others:
            present = _ticked(data[name])
            answered = pd.concat([_ticked(data[o]) for o in others], axis=1).any(axis=1)
        else:
            present = answered = ~_blank(data[name])
        yes = was_asked[name]
        found[name] = pd.Series(
            [
                (ANSWER if q else MISSING) if a else (ANOMALY if p else NOT_APPLICABLE)
                for a, p, q in zip(yes, present, answered, strict=True)
            ],
            index=data.index,
        )
    return pd.DataFrame(found, index=data.index)


# --- On a project (v0.21, step 8). ---


@dataclass(frozen=True)
class Counts:
    """For a variable with conditions: how many were asked it, how many not (not applicable),
    how many were asked and did not answer, how many answered without being asked."""

    asked: int
    not_applicable: int
    missing: int
    anomalies: int


def conditions_of(project: Project) -> dict[str, list[Condition]]:
    """The accepted conditions of the variables the codebook keeps, by original name."""
    from ddict.project import aside
    from ddict.project.decisions import is_accepted

    return {
        e.name: list(e.asked_if.value)
        for e in aside.kept(project)
        if e.asked_if is not None and is_accepted(e.asked_if) and e.asked_if.value
    }


def boxes_of(project: Project) -> dict[str, list[str]]:
    """Each option to tick (a member of a multiple-response group), with all its group's."""
    found = {}
    for group in project.groups:
        if group.kind == "multiple_response" and group.members.value:
            for name in group.members.value:
                found[name] = list(group.members.value)
    return found


def counts(project: Project, table: pd.DataFrame) -> dict[str, Counts]:
    """The four numbers of each variable with conditions, on the database as recorded."""
    conditions = conditions_of(project)
    known = set(table.columns)
    conditions = {
        n: c for n, c in conditions.items()
        if n in known and all(t.target in known for cond in c for t in cond.terms)
    }  # fmt: skip
    if not conditions:
        return {}
    boxes = {n: [o for o in b if o in known] for n, b in boxes_of(project).items() if n in known}
    found = natures(table, conditions, boxes)
    return {
        name: Counts(
            asked=int(found[name].isin([ANSWER, MISSING]).sum()),
            not_applicable=int((found[name] == NOT_APPLICABLE).sum()),
            missing=int((found[name] == MISSING).sum()),
            anomalies=int((found[name] == ANOMALY).sum()),
        )
        for name in conditions
    }
