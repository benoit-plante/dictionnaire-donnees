"""Link variables to the questions they come from (v0.2, D-013), without any model.

A variable comes from a question ("Q8"), a row of a grid ("Q7.r3") or an option ("Q10.o2"):
one variable per option of a "tick all that apply" question, and sometimes of a question
the questionnaire presents as a single choice. These are the targets. For each variable, the
tool computes a few candidate targets; the model may then choose among them by identifier
(`ddict.llm.link`), and a person decides. The text shown for a link always comes from the
questionnaire, looked up by identifier: nothing else can write it.

Candidates are scored from:
- words: the parts of the variable name and of its file label, the meaning of the accepted
  acronyms of the glossary, against the words of the row or option (full weight), of its
  question (half), of the question just before (0.4: a repeated question "À quelle
  fréquence…" is about the person named before it) and of the paragraphs of its page (a
  fifth: "Votre sommeil"). Words found in few questions count more than words found
  everywhere;
- series: variables numbered 1..n under a same stem (sommeil_q1..sommeil_q8, ethnie_0001..)
  are the rows of a grid or the options of a question, the k-th for number k;
- families: in variables sharing the start of their name (motifs_freq_ocf_repit,
  motifs_freq_ocf_activites, ...), the end of the name tells the option apart: its words
  count double in the option, and those of the shared start half. A variable outside any
  series or family rarely comes from a grid row, and never from the option of a
  single-choice question ("Oui"): those are not its candidates;
- order: variables mostly follow the questionnaire. Between two variables whose question is
  clear, the targets in between are preferred, and the one right after the previous.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass

from ddict import glossary
from ddict.i18n import _, colon
from ddict.project.model import Project, Question, Questionnaire, TrackedValue, VariableEntry

NO_QUESTION = "none"  # a decision: the variable comes from no question of the questionnaire
MAX_CANDIDATES = 5
MIN_SCORE = 1.0  # below, a target is not a candidate

PART_WEIGHT = 1.0
QUESTION_WEIGHT = 0.5
PAGE_WEIGHT = 0.2
PREVIOUS_WEIGHT = 0.4  # the question just before: what a repeated question is about
SERIES_BONUS = 3.0  # row or option k, of a question with enough of them, for the k-th of a series
SERIES_SIZE_BONUS = 1.0  # ... and exactly as many as the series has variables
SUFFIX_FACTOR = 2.0  # the end of a name in a family, found in the option
STEM_FACTOR = 0.5  # the start of a name in a family, shared by all its members
LONE_PART_FACTOR = 0.7  # a grid row outside series and families; a question in a family
WINDOW_BONUS = 0.5  # between the questions of the previous and the next clear variables
NEXT_BONUS = 1.5  # right after the previous clear variable's target
ANCHOR_SCORE = 3.0  # a variable whose best target scores this much, ...
ANCHOR_MARGIN = 1.25  # ... this many times more than the second, is clear
MIN_SERIES = 3
MIN_STEM_PARTS = 2  # motifs_freq_ocf_..., situation_professionnelle_...
MIN_PREFIX = 3  # "anx" for "anxiété", "aide" for "aider"
MIN_SHARED_PREFIX = 5  # "endormissement" and "endormir"

STOP_WORDS = glossary.STOP_WORDS | {
    "ce", "ces", "cette", "dans", "est", "il", "ils", "je", "j", "m", "me", "mon", "ma",
    "mes", "ne", "pas", "plus", "qu", "que", "quel", "quelle", "qui", "s", "se", "son",
    "un", "une", "vos", "votre", "vous", "avez", "etes", "y", "ou", "si", "ex", "q",
}  # fmt: skip

_WORD = re.compile(r"[a-z]+")
_SERIES = re.compile(r"(.*?[a-z])_?(\d{1,4})$")
# Parts of names written otherwise in questionnaires.
SYNONYMS = {"other": ("autre",), "genre": ("genre", "sexe")}


@dataclass(frozen=True)
class Target:
    target_id: str  # "Q8", "Q7.r3", "Q10.o2"
    question: Question
    part: str | None  # the text of the row or option, None for the question itself
    row: int | None  # the printed number of a row, or the rank of a row or option
    position: int  # in reading order


def _plain(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def words(text: str) -> list[str]:
    return [w for w in _WORD.findall(_plain(text)) if len(w) > 1 and w not in STOP_WORDS]


def _match(a: str, b: str) -> bool:
    if a == b:
        return True
    short, long = sorted((a, b), key=len)
    if len(short) >= MIN_PREFIX and long.startswith(short):
        return True
    shared = 0
    for x, y in zip(a, b, strict=False):
        if x != y:
            break
        shared += 1
    return shared >= MIN_SHARED_PREFIX


def targets(questionnaire: Questionnaire) -> list[Target]:
    """Every question, then its rows (grid) or options, in reading order."""
    found: list[Target] = []
    for question in questionnaire.questions:
        found.append(Target(question.question_id, question, None, None, len(found)))
        if question.kind == "grid":
            for rank, row in enumerate(question.rows, start=1):
                number = row.number if row.number is not None else rank
                found.append(Target(row.row_id, question, row.text, number, len(found)))
        else:
            for rank, option in enumerate(question.options, start=1):
                found.append(Target(option.option_id, question, option.text, rank, len(found)))
    return found


def previous_questions(questionnaire: Questionnaire) -> dict[str, Question]:
    """The question just before each one: what a repeated question is about ("Votre
    conjoint·e", then "À quelle fréquence cette personne vous apporte du soutien ?")."""
    questions = questionnaire.questions
    return {q.question_id: questions[i - 1] for i, q in enumerate(questions) if i > 0}


def target(questionnaire: Questionnaire | None, target_id: str) -> Target | None:
    if questionnaire is None:
        return None
    return next((t for t in targets(questionnaire) if t.target_id == target_id), None)


def target_text(found: Target) -> str:
    """The words of the questionnaire, exactly: the question, then the row or option."""
    if found.part is None:
        return found.question.text
    return f"{found.question.text} — {found.part}"


def describe(questionnaire: Questionnaire | None, target_id: str | None) -> str | None:
    """What a link points to, for a person: identifier, page and exact text."""
    if target_id is None:
        return None
    if target_id == NO_QUESTION:
        return _("Aucune question du questionnaire")
    found = target(questionnaire, target_id)
    if found is None:
        return None
    page = f", p. {found.question.page}" if found.question.page else ""
    return f"{target_id}{page}{colon()}{target_text(found)}"


def is_linked(entry: VariableEntry) -> bool:
    """Whether a decision was taken (a question, or none), and not rejected."""
    return entry.question.value is not None and entry.question.status != "rejected"


# --- Scoring. ---


def _variable_words(project: Project, entry: VariableEntry) -> list[str]:
    meanings = {e.term.casefold(): e.meaning for e in project.glossary if glossary.is_accepted(e)}
    found = []
    for part in glossary.name_parts(entry.name):
        for alternative in SYNONYMS.get(part, (part,)):
            found += words(meanings.get(alternative, alternative))
    found += words(entry.file.label or "")
    return list(dict.fromkeys(found))


def _target_words(
    questionnaire: Questionnaire, all_targets: list[Target]
) -> list[tuple[dict[str, float], set[str]]]:
    """For each target, its words and their weight (the strongest place they appear), with
    the words of the row or option itself."""
    page_words: dict[int | None, set[str]] = {}
    for text in questionnaire.texts:
        page_words.setdefault(text.page, set()).update(words(text.text))
    previous = previous_questions(questionnaire)
    weighted = []
    for found in all_targets:
        weights = dict.fromkeys(page_words.get(found.question.page, ()), PAGE_WEIGHT)
        before = previous.get(found.question.question_id)
        if before is not None:
            weights.update(dict.fromkeys(words(before.text), PREVIOUS_WEIGHT))
        question_weight = PART_WEIGHT if found.part is None else QUESTION_WEIGHT
        weights.update(dict.fromkeys(words(found.question.text), question_weight))
        part = set(words(found.part)) if found.part is not None else set()
        weights.update(dict.fromkeys(part, PART_WEIGHT))
        weighted.append((weights, part))
    return weighted


def _word_matches(
    variable_words: set[str], weighted: list[tuple[dict, set]]
) -> dict[str, tuple[list[float], list[bool], float]]:
    """For each word of the variables, computed once: its best weight in each target,
    whether it is in the row or option itself, and its rarity (a word found in few targets
    counts more: "tcc" more than "sommeil")."""
    vocabulary = {w for weights, _part in weighted for w in weights}
    found = {}
    for word in variable_words:
        matching = {w for w in vocabulary if _match(word, w)}
        best = [
            max((weights[w] for w in matching & weights.keys()), default=0.0)
            for weights, _part in weighted
        ]
        in_part = [bool(matching & part) for _weights, part in weighted]
        count = sum(1 for weight in best if weight >= QUESTION_WEIGHT)  # own words only
        rarity = math.log(1 + len(weighted) / count) if count else 0.0
        found[word] = (best, in_part, rarity)
    return found


def _series(project: Project) -> dict[str, tuple[int, int]]:
    """Variables numbered under a same stem: name -> (its number, size of the series)."""
    stems: dict[str, list[tuple[str, int]]] = {}
    for entry in project.variables:
        match = _SERIES.fullmatch(entry.name.lower())
        if match:
            stems.setdefault(match.group(1), []).append((entry.name, int(match.group(2))))
    found = {}
    for members in stems.values():
        numbers = {n for _name, n in members}
        if len(members) >= MIN_SERIES and len(numbers) == len(members):
            for name, number in members:
                found[name] = (number, len(members))
    return found


def _families(project: Project) -> dict[str, set[str]]:
    """Variables sharing the first parts of their name with two others or more: name -> the
    words of the end of its name, which tell it apart. One shared part is not enough:
    besoin_finance and besoin_repit are separate questions."""
    parts = {e.name: glossary.name_parts(e.name) for e in project.variables}
    found = {}
    for name, mine in parts.items():
        for length in range(len(mine) - 1, MIN_STEM_PARTS - 1, -1):
            stem = mine[:length]
            members = sum(1 for o in parts.values() if len(o) > length and o[:length] == stem)
            if members >= MIN_SERIES:
                ends = [a for part in mine[length:] for a in SYNONYMS.get(part, (part,))]
                found[name] = {w for end in ends for w in words(end)}
                break
    return found


def _sizes(all_targets: list[Target]) -> dict[str, int]:
    """Number of rows (grid) or options (checkbox) of each question."""
    return {t.question.question_id: t.row for t in all_targets if t.row is not None}


def scores(project: Project) -> dict[str, list[float]]:
    """Score of every target for every variable, in the order of `targets()`."""
    questionnaire = project.questionnaire
    if questionnaire is None:
        return {}
    all_targets = targets(questionnaire)
    weighted = _target_words(questionnaire, all_targets)
    variable_words = {e.name: _variable_words(project, e) for e in project.variables}
    matches = _word_matches({w for found in variable_words.values() for w in found}, weighted)
    series = _series(project)
    families = _families(project)
    sizes = _sizes(all_targets)

    result: dict[str, list[float]] = {}
    excluded: dict[str, set[int]] = {}
    for entry in project.variables:
        mine = variable_words[entry.name]
        ends = families.get(entry.name, set())
        lone = not ends and entry.name not in series
        excluded[entry.name] = {
            t.position
            for t in all_targets
            if lone and t.part is not None and t.question.kind == "single"
        }
        row = []
        for found in all_targets:
            score = 0.0
            for word in mine:
                weights, in_part, rarity = matches[word]
                best = weights[found.position]
                if word in ends:
                    best *= SUFFIX_FACTOR if in_part[found.position] else 1
                elif ends:
                    best *= STEM_FACTOR
                score += best * rarity
            if found.row is not None and entry.name in series:
                number, size = series[entry.name]
                available = sizes[found.question.question_id]
                if found.row == number and available >= size:
                    score += SERIES_BONUS + (SERIES_SIZE_BONUS if available == size else 0)
            elif lone and found.question.kind == "grid" and found.part is not None:
                score *= LONE_PART_FACTOR
            elif found.part is None and found.question.kind == "checkbox" and ends:
                score *= LONE_PART_FACTOR  # in a family, an option rather than its question
            row.append(score)
        result[entry.name] = row
    ordered = _with_order(project, result, len(all_targets))
    for name, positions in excluded.items():
        for position in positions:
            ordered[name][position] = 0.0
    return ordered


def _best(row: list[float]) -> tuple[int, float, float]:
    ranked = sorted(range(len(row)), key=lambda i: -row[i])
    first = ranked[0] if ranked else -1
    second = row[ranked[1]] if len(ranked) > 1 else 0.0
    return first, (row[first] if ranked else 0.0), second


def _with_order(project: Project, result: dict[str, list[float]], n: int) -> dict[str, list[float]]:
    anchors: dict[int, int] = {}  # variable index -> target position
    names = [e.name for e in project.variables]
    for index, name in enumerate(names):
        position, best, second = _best(result[name])
        if best >= ANCHOR_SCORE and best >= ANCHOR_MARGIN * second:
            anchors[index] = position
    ordered: dict[str, list[float]] = {}
    for index, name in enumerate(names):
        row = list(result[name])
        if index not in anchors and any(row):
            before = [i for i in anchors if i < index]
            after = [i for i in anchors if i > index]
            low = anchors[max(before)] if before else -1
            high = anchors[min(after)] if after else n
            for position in range(low + 1, high):
                row[position] += WINDOW_BONUS
            if before and low + 1 < n:
                row[low + 1] += NEXT_BONUS
        ordered[name] = row
    return ordered


def candidates(project: Project, *, limit: int = MAX_CANDIDATES) -> dict[str, list[str]]:
    """The best targets for each variable, best first; empty when nothing scores enough."""
    if project.questionnaire is None:
        return {}
    all_targets = targets(project.questionnaire)
    found = {}
    for name, row in scores(project).items():
        ranked = sorted(range(len(row)), key=lambda i: (-row[i], i))
        found[name] = [all_targets[i].target_id for i in ranked[:limit] if row[i] >= MIN_SCORE]
    return found


def best_guess(project: Project) -> dict[str, str]:
    """The first candidate, or "none": what the tool alone would choose (for the trials)."""
    return {name: (ids[0] if ids else NO_QUESTION) for name, ids in candidates(project).items()}


def drop_stale_links(project: Project, previous: Questionnaire | None) -> int:
    """After a new reading of the questionnaire, remove the links that may point elsewhere:
    all of them if the file changed, those whose target is gone otherwise. A decision that
    a variable comes from no question is kept. Returns how many were removed."""
    current = project.questionnaire
    changed = previous is None or current is None or previous.sha256 != current.sha256
    ids = {t.target_id for t in targets(current)} if current else set()
    removed = 0
    for entry in project.variables:
        value = entry.question.value
        if value is None or value == NO_QUESTION or (not changed and value in ids):
            continue
        entry.question = TrackedValue[str](origin="human")
        removed += 1
    return removed
