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
import re
from dataclasses import dataclass
from itertools import pairwise

from ddict import design, naming
from ddict.i18n import N_, Texts, _
from ddict.profile.compute import is_missing_label
from ddict.project.decisions import is_accepted
from ddict.project.model import KeptPoint, Project, Question

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
    }
)
# A range written in a choice: "18-25", "18 à 25", "de 18 à 25 ans", "18–25".
_RANGE = re.compile(r"(?:de\s+)?(\d+)\s*(?:-|–|à|to)\s*(\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class Point:
    code: str
    question: str  # the question's id: where the point is settled
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
    """What a point looked at: the whole question, as the project holds it."""
    text = json.dumps(question.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
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


def points(project: Project, *, kept: bool = False) -> list[Point]:
    """The points to look at, in the order of the questionnaire; `kept`: those closed by
    "Garder tel quel" too."""
    questionnaire = design.questionnaire(project)
    found: list[Point] = []
    for question in questionnaire.questions:
        found += _codes(question)
        found += _code_of(project, question)
        found += _ranges(question)
        found += _refusal(question)
        found += _grid(project, question)
    found += _names(project)
    order = {q.question_id: n for n, q in enumerate(questionnaire.questions)}
    found.sort(key=lambda p: order.get(p.question, len(order)))
    if kept:
        return found
    return [p for p in found if not is_kept(project, p)]


def is_kept(project: Project, point: Point) -> bool:
    if project.design is None:
        return False
    try:
        question = design.find(project, point.question)
    except design.DesignError:
        return False
    stamp = fingerprint(question)
    return any(
        k.code == point.code and k.target == point.question and k.fingerprint == stamp
        for k in project.design.kept
    )


def keep(project: Project, point: Point, now: str) -> None:
    """ "Garder tel quel": the point is closed while its question says the same."""
    assert project.design is not None
    question = design.find(project, point.question)
    others = [
        k for k in project.design.kept if not (k.code == point.code and k.target == point.question)
    ]
    others.append(
        KeptPoint(code=point.code, target=point.question, fingerprint=fingerprint(question),
                  date=now[:10])
    )  # fmt: skip
    project.design.kept = others


def by_question(project: Project) -> dict[str, list[Point]]:
    found: dict[str, list[Point]] = {}
    for point in points(project):
        found.setdefault(point.question, []).append(point)
    return found
