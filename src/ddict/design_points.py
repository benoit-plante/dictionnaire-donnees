"""The review of a designed questionnaire (v0.20, step D3): the points to look at, all
computed, none proposed by a model. A point is settled by changing the question, or closed by
"Garder tel quel" (`keep`): kept, it stays closed while the question says the same, and comes
back when it changes.

What cannot be computed reliably (a scale unbalanced, a question asking two things, a leading
question) is left to the reading of the team, and to the AI in v0.21, as proposals.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from itertools import pairwise

from ddict import design, naming
from ddict.i18n import N_, Texts, _
from ddict.profile.compute import is_missing_label
from ddict.project import skip
from ddict.project.decisions import is_accepted
from ddict.project.model import Condition, KeptPoint, Project, Question, Questionnaire, Term

TEXTS = Texts(
    {
        "missing_code": N_(
            "{n} choix ou énoncés sans code : les codes se décident avant la collecte."
        ),
        "duplicate_code": N_("Code en double : {codes}."),
        "code_undecided": N_(
            "Le code de la question n'est pas décidé : ses variables portent son numéro ({id})."
        ),
        "code_shared": N_(
            "Même code LimeSurvey qu'une autre question ({other}) : LimeSurvey n'a pas de « _ »."
        ),
        "name_conflict": N_("Nom de variable en conflit : {names}."),
        "overlap": N_("Catégories qui se chevauchent : {pairs}."),
        "gap": N_("Catégories qui laissent un trou : {pairs}."),
        "required_without_refusal": N_(
            "Question obligatoire sans choix de non-réponse (« Préfère ne pas répondre ») : une "
            "personne doit pouvoir ne pas répondre."
        ),
        "grid_without_instruction": N_("Grille sans consigne."),
        "instrument_without_name": N_(
            "Grille tirée d'une source sans nom d'instrument : à donner, avec sa source, sur la "
            "page « Groupes »."
        ),
        "french_spacing": N_(
            "Espace manquante avant « ? », « ! », « : » ou « ; », comme l'écrit le français : "
            "{words}."
        ),
        # v0.21 (§ 5.5 of the plan): conditions, random order, attention checks.
        "condition_forward": N_(
            "La condition vise une question qui vient après ({targets}) : elle n'a pas encore "
            "de réponse à ce moment ; {then}."
        ),
        "condition_target_gone": N_(
            "La condition vise ce qui a été retiré depuis ({targets}) : corrigez-la."
        ),
        "condition_value_gone": N_(
            "La condition attend un code qui n'est plus un choix ({values}) : elle ne serait "
            "jamais vraie."
        ),
        "condition_never": N_("Condition jamais vraie : la question ne serait jamais posée."),
        "section_never": N_("Condition jamais vraie : la section ne serait jamais posée."),
        "condition_optional": N_(
            "Une condition vise une question facultative ({targets}) : une réponse laissée vide "
            "la rend fausse. C'est peut-être voulu."
        ),
        "conditions_optional": N_(
            "Des conditions visent des questions facultatives ({targets}) : une réponse laissée "
            "vide les rend fausses. C'est peut-être voulu."
        ),
        "section_without_display": N_(
            "Section filtrée sans texte d'affichage : un texte qui dit à qui elle s'adresse "
            "aide la personne à suivre."
        ),
        "shuffle_section_mixed": N_(
            "Questions en ordre aléatoire dans une section qui contient {what} : l'ordre "
            "aléatoire ne garderait pas {place}."
        ),
        "shuffle_refusal": N_(
            "Choix en ordre aléatoire avec un choix de non-réponse ({choice}) : il serait mêlé "
            "aux autres. Le « Sans réponse » de LimeSurvey, lui, reste à la fin."
        ),
        "attention_doubtful": N_(
            "Item de contrôle {why} : un vide ou une question non posée brouillent l'échec."
        ),
        "attention_gone": N_(
            "Item de contrôle dont une bonne réponse n'est plus un choix ({codes}) : il serait "
            "toujours échoué."
        ),
    }
)
WHAT = Texts(
    {
        "display": N_("un texte d'affichage"),
        "attention": N_("un item de contrôle"),
        "filter": N_("une question qui sert de condition à une autre de la section"),
        "optional": N_("facultatif"),
        "conditioned": N_("sous une condition"),
        "its_place": N_("sa place"),
        "their_place": N_("leur place"),
        "never_question": N_("la question ne serait jamais posée"),
        "never_section": N_("la section ne serait jamais posée"),
        "term_false": N_("cette partie de la condition serait toujours fausse"),
    }
)
# A range written in a choice: "18-25", "18 à 25", "de 18 à 25 ans", "18–25".
_RANGE = re.compile(r"(?:de\s+)?(\d+)\s*(?:-|–|à|to)\s*(\d+)", re.IGNORECASE)
# A word glued to "?", "!", ":" or ";" ("sommeil?"): letters only before it, so that an hour
# ("10:30") or an address ("https://") is no point.
_GLUED = re.compile(r"([^\W\d_][\w'’-]*)([?!:;])(?!//)")
SHOWN = 3  # glued words shown in the point


@dataclass(frozen=True)
class Point:
    code: str
    question: str  # the question's id, or its section's (v0.21): where the point is settled
    detail: dict

    @property
    def text(self) -> str:
        return _(TEXTS[self.code]).format(**self.detail)

    @property
    def page(self) -> str:
        """Where it is settled: the question's form (its code too, D-156), the page "Noms"
        for its names, the page "Groupes" for its instrument."""
        if self.code == "name_conflict":
            return "names"
        return "groups" if self.code == "instrument_without_name" else "design"


def fingerprint(question: Question) -> str:
    """What a point looked at: the whole question, as the project holds it (the fields added
    since 0.11.0 only when filled, D-172)."""
    text = json.dumps(design.question_content(question), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _items(question: Question):
    rows = list(question.rows)
    options = [o for o in question.options if not o.other]
    return rows, options


def _codes(question: Question) -> list[Point]:
    found = []
    rows, options = _items(question)
    items = [*options, *rows] if question.kind != "open" else []
    missing = sum(1 for i in items if not i.code)
    if missing:
        found.append(Point("missing_code", question.question_id, {"n": missing}))
    for group in (options, rows):
        seen: dict[str, int] = {}
        for item in group:
            if item.code:
                seen[item.code] = seen.get(item.code, 0) + 1
        twice = sorted(c for c, n in seen.items() if n > 1)
        if twice:
            found.append(Point("duplicate_code", question.question_id, {"codes": ", ".join(twice)}))
    return found


def _ranges(question: Question) -> list[Point]:
    """Numeric categories that overlap or leave a gap ("18-25", "25-35"), in their order."""
    if question.kind not in ("single", "checkbox"):
        return []
    ranges = []
    for option in question.options:
        found = _RANGE.search(option.text)
        if found:
            low, high = int(found.group(1)), int(found.group(2))
            ranges.append((min(low, high), max(low, high), option.text))
    if len(ranges) < 2:
        return []
    overlaps, gaps = [], []
    for (_low, high, text), (next_low, _next_high, next_text) in pairwise(ranges):
        if next_low <= high:
            overlaps.append(f"« {text} » et « {next_text} »")
        elif next_low > high + 1:
            gaps.append(f"« {text} » et « {next_text} »")
    found = []
    if overlaps:
        found.append(Point("overlap", question.question_id, {"pairs": " ; ".join(overlaps)}))
    if gaps:
        found.append(Point("gap", question.question_id, {"pairs": " ; ".join(gaps)}))
    return found


def _refusal(question: Question) -> list[Point]:
    if not question.required or question.kind not in ("single", "checkbox", "grid"):
        return []
    if any(is_missing_label(o.text) for o in question.options):
        return []
    return [Point("required_without_refusal", question.question_id, {})]


def _grid(project: Project, question: Question) -> list[Point]:
    if question.kind != "grid":
        return []
    found = []
    if not question.instruction:
        found.append(Point("grid_without_instruction", question.question_id, {}))
    provenance = question.provenance
    group = next((g for g in project.groups if g.question == question.question_id), None)
    if provenance and provenance.kind == "source" and group and group.instrument_name is None:
        found.append(Point("instrument_without_name", question.question_id, {}))
    return found


def _spacing(question: Question) -> list[Point]:
    """French puts a space before "?", "!", ":" and ";" (v0.20.1, the author's trial)."""
    texts = [question.text, question.instruction or ""]
    texts += [i.text for i in [*question.options, *question.rows]]
    glued = [f"« {m.group(0)} »" for text in texts for m in _GLUED.finditer(text)]
    if not glued:
        return []
    words = ", ".join(glued[:SHOWN]) + (" …" if len(glued) > SHOWN else "")
    return [Point("french_spacing", question.question_id, {"words": words})]


def _code_of(project: Project, question: Question) -> list[Point]:
    """The question's code: decided, and its own in LimeSurvey (D-156)."""
    if question.kind == "display":
        return []
    stem = naming.stem(project, question.question_id)
    if stem is None or not stem.stem.value or not is_accepted(stem.stem):
        return [Point("code_undecided", question.question_id, {"id": question.question_id})]
    mine = design.code(project, question)
    for other in design.questionnaire(project).questions:
        if (
            other is not question
            and other.kind != "display"
            and design.code(project, other) == mine
        ):
            return [Point("code_shared", question.question_id, {"other": other.question_id})]
    return []


def _names(project: Project) -> list[Point]:
    clashing = set(naming.conflicts(project))
    by_question: dict[str, list[str]] = {}
    for entry in project.variables:
        if entry.name in clashing:
            question = (entry.question.value or "").partition(".")[0]
            by_question.setdefault(question, []).append(naming.current_name(entry))
    return [
        Point("name_conflict", question, {"names": ", ".join(names)})
        for question, names in by_question.items()
        if question
    ]


# --- Conditions, random order, attention checks (v0.21). ---


def _said(found: Questionnaire, targets) -> str:
    """The targets as a person reads them: « question 3 », or the id of one gone."""
    numbers = skip.numbers(found)
    known, gone = [], []
    for target in dict.fromkeys(targets):
        number = numbers.get(target.partition(".")[0])
        if number is None:
            gone.append(target)
        elif number not in known:
            known.append(number)
    said = []
    if len(known) == 1:
        said.append(_("question {n}").format(n=known[0]))
    elif known:
        said.append(_("questions {list}").format(list=", ".join(str(n) for n in sorted(known))))
    return ", ".join(said + gone)


def _depends(found: Questionnaire, question: Question) -> set[str]:
    """The questions its effective condition names."""
    return {
        t.partition(".")[0] for condition in skip.effective(found, question)
        for t in skip.targets(condition)
    }  # fmt: skip


def _ahead(found: Questionnaire):
    """A function: whether a section's or a question's condition names a question not yet
    answered when it is read: the question itself or one after it, or for a section one of
    its own questions or after them. Such a term is always false; a condition "in a loop"
    always holds one."""
    order = {q.question_id: n for n, q in enumerate(found.questions)}
    first: dict[str, int] = {}
    for question in found.questions:
        first.setdefault(question.section or "", order[question.question_id])

    def ahead(owner: str, target: Question) -> bool:
        if owner in order:
            return order[target.question_id] >= order[owner]
        return order[target.question_id] >= first.get(owner, len(order))

    return ahead


def _term_never(found: Questionnaire, owner: str, term: Term, asked, ahead) -> bool:
    """A term that cannot hold whatever the answers: on a question not yet answered or never
    asked, or on codes none of which is a choice."""
    target = skip.target_of(found, term.target)
    if target is None:
        return False  # gone: its own point
    if ahead(owner, target.question) or not asked(target.question):
        return True
    if target.nature == "choice" and term.operator in ("eq", "in"):
        codes = skip.choices(target.question)
        return not any(skip.code_text(v) in codes for v in skip.values_of(term))
    if target.nature == "choice" and term.operator in ("ne", "not_in"):
        codes = set(skip.choices(target.question))
        return not codes - {skip.code_text(v) for v in skip.values_of(term)}
    return False


def _all_never(found: Questionnaire, condition: Condition) -> bool:
    """Terms joined by "and" that contradict each other on a same target: two codes, or
    bounds that leave no number ("≥ 18 and < 18")."""
    by_target: dict[str, list[Term]] = {}
    for term in condition.terms:
        by_target.setdefault(term.target, []).append(term)
    for target_id, terms in by_target.items():
        target = skip.target_of(found, target_id)
        if target is None:
            continue
        if target.nature == "choice":
            allowed = set(skip.choices(target.question))
            for term in terms:
                values = {skip.code_text(v) for v in skip.values_of(term)}
                if term.operator in ("eq", "in"):
                    allowed &= values
                elif term.operator in ("ne", "not_in"):
                    allowed -= values
            if not allowed:
                return True
        elif target.nature == "number":
            low, high = (-math.inf, False), (math.inf, False)  # (bound, strict)
            excluded = set()
            for term in terms:
                if term.value is None:
                    continue
                value = skip.as_number(term.value)
                if value is None:
                    continue
                if term.operator in ("ge", "gt", "eq"):
                    candidate = (value, term.operator == "gt")
                    if candidate[0] > low[0] or (candidate[0] == low[0] and candidate[1]):
                        low = candidate
                if term.operator in ("le", "lt", "eq"):
                    candidate = (value, term.operator == "lt")
                    if candidate[0] < high[0] or (candidate[0] == high[0] and candidate[1]):
                        high = candidate
                if term.operator == "ne":
                    excluded.add(value)
            if low[0] > high[0] or (low[0] == high[0] and (low[1] or high[1])):
                return True
            if low[0] == high[0] and low[0] in excluded:
                return True
    return False


def _never(found: Questionnaire, owner: str, condition: Condition, asked, ahead) -> bool:
    each = [_term_never(found, owner, t, asked, ahead) for t in condition.terms]
    if condition.combine == "all":
        return any(each) or _all_never(found, condition)
    return all(each)


class _Asked:
    """Whether a section or a question can ever be asked (its condition, and its section's,
    can hold), the questions it depends on looked at first. A term on a question not yet
    answered is false without looking further, so there is no loop to follow."""

    def __init__(self, found: Questionnaire) -> None:
        self.found = found
        self.ahead = _ahead(found)
        self.sections = {s.section_id: s for s in found.sections}
        self.memo: dict[str, bool] = {}

    def section(self, section_id: str) -> bool:
        section = self.sections.get(section_id)
        if section is None or section.condition is None:
            return True
        if section_id not in self.memo:
            self.memo[section_id] = True  # while looking
            never = _never(self.found, section_id, section.condition, self, self.ahead)
            self.memo[section_id] = not never
        return self.memo[section_id]

    def __call__(self, question: Question) -> bool:
        key = question.question_id
        if key not in self.memo:
            self.memo[key] = True  # while looking
            never = not self.section(question.section or "")
            if not never and question.condition is not None:
                never = _never(self.found, key, question.condition, self, self.ahead)
            self.memo[key] = not never
        return self.memo[key]


def _condition_points(
    found: Questionnaire, owner: str, condition: Condition, asked: _Asked, never: bool
) -> list[Point]:
    """The points of one section's or question's own condition. `never`: it is never asked,
    said with its terms on a question not yet answered when it has some, else in a point of
    its own. The optional targets are said once for the questionnaire (`_optional`)."""
    found_points = []
    gone, values, later = [], [], []
    for term in condition.terms:
        target = skip.target_of(found, term.target)
        if target is None:
            gone.append(term.target)
            continue
        if target.nature == "choice":
            codes = skip.choices(target.question)
            values += [
                skip.code_text(v) for v in skip.values_of(term) if skip.code_text(v) not in codes
            ]
        if asked.ahead(owner, target.question):
            later.append(term.target)
    section = owner in asked.sections
    if gone:
        found_points.append(Point("condition_target_gone", owner, {"targets": ", ".join(gone)}))
    if values:
        found_points.append(Point("condition_value_gone", owner, {"values": ", ".join(values)}))
    if later:
        then = "term_false"
        if never:
            then = "never_section" if section else "never_question"
        detail = {"targets": _said(found, later), "then": _(WHAT[then])}
        found_points.append(Point("condition_forward", owner, detail))
    elif never:
        found_points.append(Point("section_never" if section else "condition_never", owner, {}))
    return found_points


def _optional(found: Questionnaire) -> list[Point]:
    """The optional questions that conditions name, in one point on the first of them, where
    it is settled: made required, or kept as is."""
    conditions = [s.condition for s in found.sections] + [q.condition for q in found.questions]
    named = {t.target.partition(".")[0] for c in conditions if c is not None for t in c.terms}
    optional = [q.question_id for q in found.questions if q.question_id in named
                and not q.required]  # fmt: skip
    if not optional:
        return []
    code = "condition_optional" if len(optional) == 1 else "conditions_optional"
    return [Point(code, optional[0], {"targets": _said(found, optional)})]


def _conditions(project: Project) -> list[Point]:
    found = design.questionnaire(project)
    asked = _Asked(found)
    points_found: list[Point] = []
    for section in found.sections:
        mine = [q for q in found.questions if q.section == section.section_id]
        if section.condition is not None:
            never = not asked.section(section.section_id)
            points_found += _condition_points(
                found, section.section_id, section.condition, asked, never
            )
            if not any(q.kind == "display" for q in mine):
                points_found.append(Point("section_without_display", section.section_id, {}))
        if section.shuffle:
            what = []
            if any(q.kind == "display" for q in mine):
                what.append(_(WHAT["display"]))
            if any(q.attention or any(r.attention for r in q.rows) for q in mine):
                what.append(_(WHAT["attention"]))
            ids = {q.question_id for q in mine}
            if any(_depends(found, q) & (ids - {q.question_id}) for q in mine):
                what.append(_(WHAT["filter"]))
            if what:
                listed = ", ".join(what[:-1]) + _(" et ") + what[-1] if len(what) > 1 else what[0]
                place = _(WHAT["their_place" if len(what) > 1 else "its_place"])
                detail = {"what": listed, "place": place}
                points_found.append(Point("shuffle_section_mixed", section.section_id, detail))
    for question in found.questions:
        qid = question.question_id
        # In a section never asked, a question is never asked either: said once, on it.
        never = asked.section(question.section or "") and not asked(question)
        if question.condition is not None:
            points_found += _condition_points(found, qid, question.condition, asked, never)
        if question.shuffle and question.kind == "single":
            refusal = [o.text for o in question.options if is_missing_label(o.text)]
            if refusal:
                points_found.append(Point("shuffle_refusal", qid, {"choice": f"« {refusal[0]} »"}))
        checks = [question.attention] if question.attention else []
        checks += [r.attention for r in question.rows if r.attention]
        if checks:
            why = []
            if not question.required:
                why.append(_(WHAT["optional"]))
            if skip.effective(found, question):
                why.append(_(WHAT["conditioned"]))
            if why:
                points_found.append(Point("attention_doubtful", qid, {"why": _(" et ").join(why)}))
            codes = skip.choices(question)
            wrong = sorted({c for check in checks for c in check if c not in codes})
            if wrong:
                points_found.append(Point("attention_gone", qid, {"codes": ", ".join(wrong)}))
    return points_found + _optional(found)


def points(project: Project, *, kept: bool = False) -> list[Point]:
    """The points to look at, in the order of the questionnaire; `kept`: those closed by
    "Garder tel quel" too."""
    questionnaire = design.questionnaire(project)
    french = project.settings.language.startswith("fr")
    found: list[Point] = []
    for question in questionnaire.questions:
        if french:
            found += _spacing(question)
        found += _codes(question)
        found += _code_of(project, question)
        found += _ranges(question)
        found += _refusal(question)
        found += _grid(project, question)
    found += _names(project)
    found += _conditions(project)
    order: dict[str, float] = {q.question_id: n for n, q in enumerate(questionnaire.questions)}
    before = 0  # a section's points come before its first question
    for section in questionnaire.sections:
        order[section.section_id] = before - 0.5
        before += sum(1 for q in questionnaire.questions if q.section == section.section_id)
    found.sort(key=lambda p: order.get(p.question, len(order)))
    if kept:
        return found
    return [p for p in found if not is_kept(project, p)]


def _stamp(project: Project, target: str) -> str | None:
    """What a kept point looked at: its question, or its section with its questions (v0.21);
    None for one gone."""
    found = design.questionnaire(project)
    if target.startswith("S"):
        section = next((s for s in found.sections if s.section_id == target), None)
        if section is None:
            return None
        data = {
            "section": design.section_content(section),
            "questions": [design.question_content(q) for q in found.questions
                          if q.section == target],
        }  # fmt: skip
        text = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    try:
        return fingerprint(design.find(project, target))
    except design.DesignError:
        return None


def is_kept(project: Project, point: Point) -> bool:
    if project.design is None:
        return False
    stamp = _stamp(project, point.question)
    if stamp is None:
        return False
    return any(
        k.code == point.code and k.target == point.question and k.fingerprint == stamp
        for k in project.design.kept
    )


def keep(project: Project, point: Point, now: str) -> None:
    """ "Garder tel quel": the point is closed while its question (or its section) says the
    same. A point on a condition looks at the question that holds it, not at its target."""
    assert project.design is not None
    stamp = _stamp(project, point.question)
    assert stamp is not None
    others = [
        k for k in project.design.kept if not (k.code == point.code and k.target == point.question)
    ]
    others.append(
        KeptPoint(code=point.code, target=point.question, fingerprint=stamp, date=now[:10])
    )  # fmt: skip
    project.design.kept = others


def where(project: Project, point: Point) -> str:
    """Where a point is, as a person reads it: « question 7 », « section « Votre quartier » »."""
    found = design.questionnaire(project)
    for section in found.sections:
        if section.section_id == point.question:
            return _("section « {title} »").format(title=section.title or section.section_id)
    number = skip.numbers(found).get(point.question)
    return _("question {n}").format(n=number) if number else point.question


def by_question(project: Project) -> dict[str, list[Point]]:
    found: dict[str, list[Point]] = {}
    for point in points(project):
        found.setdefault(point.question, []).append(point)
    return found
