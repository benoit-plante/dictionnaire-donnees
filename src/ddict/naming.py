"""New names for the variables (v0.7, D-048 to D-051), proposed by rules, decided by a person.

The original name stays the key of a variable: the database is read and recognized by it,
and the original file is never changed. A new name is a tracked value: proposed by the
naming rules ("rule") or taken from an earlier wave ("reference"), it is applied in the
exports only once a person accepts it.

The rules, in this order:
1. a variable of the survey platform: its fixed name (D-050);
2. an item of a group whose prefix a person gave: `<prefix>_<rank>` (`k6_1`), the rank of
   the item in the platform's structure, or in the group;
3. a variable of a question with a stem (one per question, shared by its variables): the
   stem for a question alone, `<stem>_<rank>` for a checkbox option, `<stem>_autre_txt` for
   the text of its "other" option;
4. otherwise none: the variable is "to name", and keeps its original name.

A stem is proposed from the words of the question (small words aside, at most three, at
most 20 characters); the model never proposes a group's prefix (principle 4).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from ddict import platforms
from ddict.project.decisions import DecisionError, correct, enter, is_accepted, reject, validate
from ddict.project.model import Project, QuestionStem, TrackedValue, VariableEntry
from ddict.questionnaire import link

# SPSS reserved words: never a variable name.
RESERVED = frozenset(
    {"all", "and", "by", "eq", "ge", "gt", "le", "lt", "ne", "not", "or", "to", "with"}
)
# Words that ask or instruct, not what the question is about: never in a stem.
STEM_STOP_WORDS = frozenset(
    {
        "quel", "quels", "quelle", "quelles", "combien", "comment", "pourquoi", "lequel",
        "lesquels", "lesquelles", "cochez", "coche", "cocher", "decrivez", "decris",
        "indiquez", "indique", "precisez", "precise", "selectionnez", "choisissez",
        "veuillez", "avez", "etes", "faites", "fait", "prenez", "utilisez", "utilises",
        "travaillez", "occupez", "recu", "recue", "autres", "autre", "dernier", "derniere", "cours",
        "votre", "vos", "dans", "pour", "chez", "tres", "plus", "moins", "depuis",
        "how", "many", "much", "which", "what", "please", "describe", "check", "select",
        "indicate", "other", "last", "during", "about",
    }
)  # fmt: skip
MAX_STEM = 20  # characters of a stem, before any rank or wave
STEM_WORDS = 3
OTHER_TEXT = {"fr": "autre_txt", "en": "other_txt"}
_STYLE = re.compile(r"[a-z][a-z0-9]*(_[a-z0-9]+)*")
_NOT_ALLOWED = re.compile(r"[^a-z0-9]+")

Problem = str  # "style", "length", "reserved", "duplicate", "original_name"


class NamingError(ValueError):
    """A name or a decision the rules refuse; `problems` says why."""

    def __init__(self, problems: list[Problem]) -> None:
        super().__init__(", ".join(problems))
        self.problems = problems


def slug(text: str) -> str:
    """Lower case, digits and "_", without accents: "Âge (années)" -> "age_annees"."""
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return _NOT_ALLOWED.sub("_", plain.lower()).strip("_")


def with_wave(name: str, project: Project) -> str:
    settings = project.settings.naming
    if not settings.wave:
        return name
    if settings.position == "prefix":
        return f"{settings.wave}_{name}"
    return f"{name}_{settings.wave}"


def current_name(entry: VariableEntry) -> str:
    """The name the variable has now: its new name, proposed or accepted, else its own."""
    tracked = entry.new_name
    if tracked.value and tracked.status != "rejected":
        return tracked.value
    return entry.name


def final_name(entry: VariableEntry) -> str:
    """The name in the final exports: the accepted new name, else the original name."""
    return entry.new_name.value if is_accepted(entry.new_name) else entry.name


def problems(project: Project, variable: str, name: str) -> list[Problem]:
    """Why a new name cannot be given to a variable; empty when it can."""
    found: list[Problem] = []
    if not _STYLE.fullmatch(name):
        found.append("style")
    if len(name) > project.settings.naming.max_length:
        found.append("length")
    if name.lower() in RESERVED:
        found.append("reserved")
    others = [e for e in project.variables if e.name != variable]
    if any(e.name.lower() == name.lower() for e in others):
        found.append("original_name")
    elif any(current_name(e).lower() == name.lower() for e in others):
        found.append("duplicate")
    return found


def conflicts(project: Project) -> list[str]:
    """The variables whose current name clashes with another's (case aside)."""
    names: dict[str, list[str]] = {}
    for entry in project.variables:
        names.setdefault(current_name(entry).lower(), []).append(entry.name)
    return [n for group in names.values() if len(group) > 1 for n in group]


# --- Stems of questions. ---


def stem_from_text(text: str) -> str | None:
    """A stem from the words of a question: its first meaningful words, at most three and
    MAX_STEM characters."""
    chosen: list[str] = []
    for word in link.words(text):
        part = slug(word)
        if len(part) < 3 or part in chosen or part in STEM_STOP_WORDS:
            continue
        candidate = "_".join([*chosen, part])
        if len(candidate) > MAX_STEM:
            break
        chosen.append(part)
        if len(chosen) == STEM_WORDS:
            break
    stem = "_".join(chosen)
    return stem if stem and _STYLE.fullmatch(stem) else None


def valid_stem(text: str) -> bool:
    """A stem the rules accept: the style of a name, at most MAX_STEM characters."""
    return bool(_STYLE.fullmatch(text)) and len(text) <= MAX_STEM


def set_stem_proposal(
    project: Project, key: str, tracked: TrackedValue[str], signals: list[str]
) -> None:
    """A stem proposed by the model (v0.7, D-051), with its signals."""
    found = stem(project, key)
    if found is None:
        project.stems.append(QuestionStem(key=key, stem=tracked, ai_signals=signals))
    else:
        found.stem = tracked
        found.ai_signals = signals


def stem(project: Project, key: str) -> QuestionStem | None:
    return next((s for s in project.stems if s.key == key), None)


def usable_stem(project: Project, key: str | None) -> str | None:
    found = stem(project, key) if key else None
    if found is None or not found.stem.value or found.stem.status == "rejected":
        return None
    return found.stem.value


@dataclass(frozen=True)
class StemQuestion:
    """A question whose variables share a stem."""

    key: str
    single: str | None  # the variable of the whole question
    options: tuple[tuple[str, int], ...]  # (variable, rank) of its checkbox options
    other: str | None  # the variable of its "other" text


def stem_questions(project: Project) -> list[StemQuestion]:
    """Questions needing a stem: from the platform's structure (not grids, which take a
    prefix), else from the accepted links to the questionnaire."""
    found: list[StemQuestion] = []
    if platforms.by_name(project.source.platform) is not None:
        for question in link.project_questions(project):
            if question.kind == "grid":
                continue
            options = tuple((name, k) for k, name in enumerate(question.items, start=1))
            key = f"q{question.rank:04d}"
            found.append(StemQuestion(key, question.single, options, question.other))
        return found
    by_key: dict[str, dict] = {}
    for entry in project.variables:
        target = entry.question.value
        if not is_accepted(entry.question) or not target or target == link.NO_QUESTION:
            continue
        key, _dot, part = target.partition(".")
        question = by_key.setdefault(key, {"single": None, "options": []})
        if part.startswith("o") and part[1:].isdigit():
            question["options"].append((entry.name, int(part[1:])))
        elif not part and question["single"] is None:
            question["single"] = entry.name
    for key, question in by_key.items():
        if question["single"] or question["options"]:
            found.append(StemQuestion(key, question["single"], tuple(question["options"]), None))
    return found


def sure_links(project: Project) -> dict[str, str]:
    """The computation's sure links, computed once for many questions."""
    return link.sure_choices(project) if project.questionnaire else {}


def question_text(
    project: Project, question: StemQuestion, sure: dict[str, str] | None = None
) -> str | None:
    """The text of a question: from the questionnaire, through a variable's link (accepted,
    or sure); else the file label of its variable, which a platform's .sav gives. `sure`:
    the sure links, when the caller computed them."""
    sure = sure_links(project) if sure is None else sure
    names = [n for n in (question.single, *(n for n, _r in question.options)) if n]
    for name in names:
        entry = project.variable(name)
        target_id = entry.question.value if is_accepted(entry.question) else sure.get(name)
        found = link.target(project.questionnaire, target_id) if target_id else None
        if found is not None:
            return found.question.text
    for name in names:
        label = project.variable(name).file.label
        if label:
            return label
    return None


def _propose_stems(project: Project, questions: list[StemQuestion]) -> None:
    sure = None  # computed at the first question that needs a text
    taken = {
        s.stem.value
        for s in project.stems
        if s.stem.value and s.stem.status != "rejected" and s.stem.origin != "rule"
    }
    for question in questions:
        current = stem(project, question.key)
        if current is not None and (
            current.stem.origin != "rule" or current.stem.status != "proposed"
        ):
            continue  # decided, or given by a person or an earlier wave
        if sure is None:
            sure = sure_links(project)
        text = question_text(project, question, sure)
        base = stem_from_text(text) if text else None
        if base is None:
            if current is not None:
                project.stems.remove(current)
            continue
        value, number = base, 2
        while value in taken:
            value, number = f"{base}_{number}", number + 1
        taken.add(value)
        tracked = TrackedValue[str](value=value, origin="rule", status="proposed")
        if current is None:
            project.stems.append(QuestionStem(key=question.key, stem=tracked))
        else:
            current.stem = tracked


# --- Proposals. ---


def _undecided(tracked: TrackedValue[str]) -> bool:
    """A new name the rules may (re)write: none yet, or their own pending proposal."""
    if tracked.origin == "human":
        return tracked.value is None
    return tracked.origin == "rule" and tracked.status == "proposed"


def _rule_names(project: Project) -> dict[str, str]:
    """What the rules would name each variable, before the wave mark and the checks."""
    language = project.settings.language
    platform = platforms.by_name(project.source.platform)
    found: dict[str, str] = {}
    if platform is not None:
        for entry in project.variables:
            variable = platform.platform_variable(entry.name)
            if variable is not None:
                found[entry.name] = variable.new_name[language]
    for group in project.groups:
        prefix = group.name_prefix.value if is_accepted(group.name_prefix) else None
        if not prefix:
            continue
        for rank, member in enumerate(group.members.value or [], start=1):
            place = platform.place(member) if platform else None
            found.setdefault(member, f"{prefix}_{place.item if place and place.item else rank}")
    for question in stem_questions(project):
        base = usable_stem(project, question.key)
        if not base:
            continue
        if question.single:
            found.setdefault(question.single, base)
        for name, rank in question.options:
            found.setdefault(name, f"{base}_{rank}")
        if question.other:
            found.setdefault(question.other, f"{base}_{OTHER_TEXT[language]}")
    return found


def propose(project: Project) -> None:
    """Propose stems and names by the rules, where nothing is decided; a proposal the rules
    no longer give, or that breaks a rule, is withdrawn."""
    _propose_stems(project, stem_questions(project))
    wanted = _rule_names(project)
    for entry in project.variables:
        if _undecided(entry.new_name):
            entry.new_name = TrackedValue[str](origin="human")
    for entry in project.variables:
        if not _undecided(entry.new_name) or entry.name not in wanted:
            continue
        name = with_wave(slug(wanted[entry.name]) or wanted[entry.name], project)
        if not problems(project, entry.name, name):
            entry.new_name = TrackedValue[str](value=name, origin="rule", status="proposed")


def to_name(project: Project) -> list[str]:
    """The variables without a new name, proposed or decided."""
    return [e.name for e in project.variables if not e.new_name.value]


def summary(project: Project) -> dict[str, int]:
    """Counts for a person: proposed, accepted, to name, in conflict."""
    return {
        "proposed": sum(1 for e in project.variables if e.new_name.status == "proposed"),
        "accepted": sum(1 for e in project.variables if is_accepted(e.new_name)),
        "to_name": len(to_name(project)),
        "conflicts": len(conflicts(project)),
    }


# --- Decisions. ---


def decide(project: Project, variable: str, action: str, *, now: str, value: str = "") -> None:
    """Accept, correct (with `value`) or reject a variable's new name; or, for a name a
    person writes where nothing was proposed, enter it ("correct" too)."""
    entry = project.variable(variable)
    tracked = entry.new_name
    try:
        if action == "accept":
            entry.new_name = validate(tracked, now=now)
        elif action == "reject":
            entry.new_name = reject(tracked, now=now)
        else:
            name = value.strip()
            found = problems(project, variable, name)
            if found:
                raise NamingError(found)
            if tracked.origin == "human":
                entry.new_name = enter(tracked, name, now=now)
            else:
                entry.new_name = correct(tracked, name, now=now)
    except DecisionError as error:
        raise NamingError([str(error)]) from error


def set_prefix(project: Project, group_id: str, prefix: str, *, now: str) -> None:
    """A person gives (or clears, with "") the prefix of a group's names."""
    group = next(g for g in project.groups if g.group_id == group_id)
    text = prefix.strip()
    if text and not _STYLE.fullmatch(text):
        raise NamingError(["style"])
    if text.lower() in RESERVED:
        raise NamingError(["reserved"])
    group.name_prefix = TrackedValue[str](value=text or None, origin="human", updated_at=now)


def decide_stem(project: Project, key: str, action: str, *, now: str, value: str = "") -> None:
    """Accept, correct or reject a question's stem, or write one where none was proposed."""
    found = stem(project, key)
    if action in ("accept", "reject") and found is None:
        raise NamingError(["no_stem"])
    if found is not None:
        found.ai_signals = []  # a person's decision settles the signals
    try:
        if action == "accept":
            found.stem = validate(found.stem, now=now)
        elif action == "reject":
            found.stem = reject(found.stem, now=now)
        else:
            text = value.strip()
            if not _STYLE.fullmatch(text) or len(text) > MAX_STEM:
                raise NamingError(["style" if not _STYLE.fullmatch(text) else "length"])
            if found is None:
                tracked = TrackedValue[str](value=text, origin="human", updated_at=now)
                project.stems.append(QuestionStem(key=key, stem=tracked))
            elif found.stem.origin == "human":
                found.stem = enter(found.stem, text, now=now)
            else:
                found.stem = correct(found.stem, text, now=now)
    except DecisionError as error:
        raise NamingError([str(error)]) from error


def set_wave(project: Project, wave: str | None, position: str = "suffix") -> None:
    """The mark of the wave added to every proposed name ("t2"), or none."""
    mark = slug(wave or "") or None
    if mark is not None and not _STYLE.fullmatch(mark):
        raise NamingError(["style"])
    project.settings.naming.wave = mark
    project.settings.naming.position = position
