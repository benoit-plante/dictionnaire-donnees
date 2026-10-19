"""The names of an earlier wave, taken again for a new one (v0.7, D-052).

The earlier wave is given by its project file (`.dd.json`, the richest), its documented copy
(`.sav`, already renamed) or a table of names (`.csv`: original name, new name). Each
variable of the new wave is matched, by computation, with a variable of the earlier one,
from reasons a person can read: the same platform variable, the same label, the same value
labels, the same question as its matched neighbours, the same type. A match is proposed
only when it is clear (the rule of the anchors) and the earlier variable has no better
match; otherwise the candidates are kept for a person. A table holds names only: it
matches by identical original names, which is fragile when the platform's numbering moved,
and the report says so.

The name proposed is the earlier one, without its own wave mark, with the new wave's mark.
The prefixes of the earlier groups are proposed for the groups whose items match theirs.
The report of differences (variables added, removed, value labels changed) is a result in
itself for the team; it holds metadata only.
"""

from __future__ import annotations

import csv
import io
import re
from collections import Counter
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

from ddict import naming, platforms
from ddict.export.wording import code_text, dataset_title
from ddict.i18n import N_, Texts, _, colon, quoted
from ddict.io.csv_reader import decode
from ddict.io.model import Code
from ddict.io.sav import normalize_code
from ddict.project.decisions import is_accepted
from ddict.project.model import Project, TrackedValue, VariableEntry
from ddict.project.store import PROJECT_SUFFIX, load_project
from ddict.questionnaire import link

# Weights of the reasons of a match.
WEIGHTS = {
    "same_platform_variable": 5.0,
    "same_label": 3.0,
    "same_question_text": 2.0,
    "same_value_labels": 2.0,
    "same_question": 2.0,
    "same_rank": 1.0,
    "same_type": 0.5,
    "same_original_name": 1.0,
    "similar_label": 1.5,  # a reworded item, perhaps: a candidate, never a match alone
}
# Reasons that may make a match; "similar_label" alone only offers a candidate.
STRONG_REASONS = frozenset(
    {"same_platform_variable", "same_label", "same_question_text", "same_question",
     "same_original_name"}
)  # fmt: skip
SIMILAR_LABEL = 0.7  # of SequenceMatcher's ratio, on normalized labels
MIN_SCORE = 3.0  # below, not a match
MARGIN = 1.25  # the best must be this many times the second (the rule of the anchors)
MAX_CANDIDATES = 3
# A wave mark: "_t1" at the end, "t1_" at the start, on most names.
_SUFFIX_MARK = re.compile(r"_(t\d{1,2})$")
_PREFIX_MARK = re.compile(r"^(t\d{1,2})_")
MARK_SHARE = 0.8
_RANKED = re.compile(r"(?P<stem>.+?)_(?P<rank>\d+)$")
HEADERS = (("nom_origine", "nouveau_nom"), ("original_name", "new_name"))


class ReferenceError(ValueError):
    """The earlier wave cannot be read."""


@dataclass(frozen=True)
class Earlier:
    """A variable of the earlier wave, as its source tells it."""

    name: str  # its name in that wave, mark included
    original: str | None = None  # its original name, when the source says
    label: str | None = None
    value_labels: tuple[tuple[Code, str], ...] = ()
    question_text: str | None = None
    numeric: bool | None = None
    question_key: str | None = None  # its question: the platform's, or its name's stem
    rank: int | None = None  # its rank in its question or group
    other: bool = False  # the text of an "other" option
    group_prefix: str | None = None  # the accepted prefix of its group


@dataclass
class EarlierWave:
    source: str  # "project", "documented_copy" or "table"
    file_name: str
    variables: list[Earlier]
    mark: str | None = None  # "t1"
    position: str = "suffix"


@dataclass(frozen=True)
class Match:
    variable: str
    earlier: str
    score: float
    reasons: tuple[str, ...]


@dataclass
class WaveReport:
    """What matching found: the matches, the variables left with candidates, and the
    differences between the waves."""

    source: str
    file_name: str
    matches: list[Match] = field(default_factory=list)
    candidates: dict[str, list[Match]] = field(default_factory=dict)
    added: list[str] = field(default_factory=list)  # no earlier variable at all
    removed: list[str] = field(default_factory=list)  # earlier names matched by none
    value_labels_changed: list[str] = field(default_factory=list)
    # For the report: what the earlier wave said, label of a removed variable, and each
    # changed value label (code, before, after; None where a code has no label).
    removed_labels: dict[str, str] = field(default_factory=dict)
    label_changes: dict[str, list[tuple[Code, str | None, str | None]]] = field(
        default_factory=dict
    )
    fragile: int = 0  # matches by the original name alone
    prefixes: dict[str, str] = field(default_factory=dict)  # group_id -> earlier prefix


# --- Reading the earlier wave. ---


def _mark(names: list[str]) -> tuple[str | None, str]:
    """The wave mark most names share, and its position."""
    for pattern, position in ((_SUFFIX_MARK, "suffix"), (_PREFIX_MARK, "prefix")):
        found = Counter(m.group(1) for n in names if (m := pattern.search(n)))
        if found:
            mark, count = found.most_common(1)[0]
            if count >= MARK_SHARE * len(names):
                return mark, position
    return None, "suffix"


def without_mark(name: str, mark: str | None, position: str) -> str:
    if not mark:
        return name
    if position == "suffix" and name.endswith(f"_{mark}"):
        return name[: -len(mark) - 1]
    if position == "prefix" and name.startswith(f"{mark}_"):
        return name[len(mark) + 1 :]
    return name


def _from_name(name: str, mark: str | None, position: str) -> tuple[str | None, int | None, bool]:
    """Question key, rank and "other" from a renamed name: `taches_2_t1`, `taches_autre_txt`."""
    bare = without_mark(name, mark, position)
    for ending in naming.OTHER_TEXT.values():
        if bare.endswith(f"_{ending}"):
            return bare[: -len(ending) - 1], None, True
    ranked = _RANKED.fullmatch(bare)
    if ranked:
        return ranked.group("stem"), int(ranked.group("rank")), False
    return bare, None, False


def _from_project(project: Project, file_name: str) -> EarlierWave:
    platform = platforms.of(project)
    groups = {m: g for g in project.groups for m in (g.members.value or [])}
    variables = []
    for entry in project.variables:
        place = platform.place(entry.name) if platform else None
        group = groups.get(entry.name)
        prefix = group.name_prefix.value if group and is_accepted(group.name_prefix) else None
        if place is not None:
            key, rank, other = platform.question_key(place.question), place.item, place.other
        else:
            rank = (group.members.value.index(entry.name) + 1) if group else None
            key, other = (group.group_id if group else None), False
        found = (
            link.target(project.questionnaire, entry.question.value)
            if is_accepted(entry.question) and entry.question.value
            else None
        )
        variables.append(
            Earlier(
                name=naming.final_name(entry),
                original=entry.name,
                label=entry.file.label,
                value_labels=tuple((v.code, v.label) for v in entry.file.value_labels),
                question_text=found.question.text if found else None,
                numeric=entry.file.storage_type == "numeric",
                question_key=key,
                rank=rank,
                other=other,
                group_prefix=prefix,
            )
        )
    settings = project.settings.naming
    mark, position = settings.wave, settings.position
    if not mark:
        mark, position = _mark([v.name for v in variables])
    return EarlierWave("project", file_name, variables, mark, position)


def _from_sav(path: Path) -> EarlierWave:
    import pyreadstat

    try:
        _table, meta = pyreadstat.read_sav(path, metadataonly=True)
    except Exception as error:  # pyreadstat raises its own errors
        raise ReferenceError(f"Cannot read {path.name}: {error}") from error
    names = list(meta.column_names)
    mark, position = _mark(names)
    variables = []
    for name in names:
        key, rank, other = _from_name(name, mark, position)
        labels = meta.variable_value_labels.get(name, {})
        variables.append(
            Earlier(
                name=name,
                label=meta.column_names_to_labels.get(name),
                value_labels=tuple((normalize_code(c), str(t)) for c, t in labels.items()),
                numeric=not meta.original_variable_types.get(name, "F").startswith("A"),
                question_key=key,
                rank=rank,
                other=other,
            )
        )
    return EarlierWave("documented_copy", path.name, variables, mark, position)


def read_name_table(path: Path) -> list[tuple[str, str]]:
    """The rows of a table of names (D-052): UTF-8, "," or ";", a header."""
    try:
        text, _encoding = decode(path.read_bytes())
    except (OSError, UnicodeError) as error:
        raise ReferenceError(f"Cannot read {path.name}: {error}") from error
    first = text.splitlines()[0] if text.strip() else ""
    delimiter = ";" if first.count(";") > first.count(",") else ","
    rows = [r for r in csv.reader(io.StringIO(text), delimiter=delimiter) if any(r)]
    if not rows or tuple(c.strip().lower() for c in rows[0][:2]) not in HEADERS:
        raise ReferenceError(f"{path.name}: the first row must be nom_origine,nouveau_nom")
    found = [(r[0].strip(), r[1].strip()) for r in rows[1:] if len(r) >= 2 and r[0].strip()]
    if not found:
        raise ReferenceError(f"{path.name}: no names")
    return found


def _from_table(path: Path) -> EarlierWave:
    rows = read_name_table(path)
    mark, position = _mark([new for _old, new in rows if new])
    variables = [Earlier(name=new or old, original=old) for old, new in rows]
    return EarlierWave("table", path.name, variables, mark, position)


def read_earlier_wave(path: Path | str) -> EarlierWave:
    """The earlier wave, from its project file, documented copy or table of names."""
    path = Path(path)
    lowered = path.name.lower()
    if lowered.endswith(PROJECT_SUFFIX):
        return _from_project(load_project(path), path.name)
    if lowered.endswith((".sav", ".zsav")):
        return _from_sav(path)
    if lowered.endswith(".csv"):
        return _from_table(path)
    raise ReferenceError(f"{path.name}: give a project (.dd.json), a .sav or a .csv file")


# --- Matching. ---


def _value_labels(entry: VariableEntry) -> tuple[tuple[Code, str], ...]:
    return tuple((v.code, v.label) for v in entry.file.value_labels)


def _same_labels(a: tuple, b: tuple) -> bool:
    if not a or not b or len(a) != len(b):
        return False
    first = {normalize_code(c): link.normalized_text(t) for c, t in a}
    second = {normalize_code(c): link.normalized_text(t) for c, t in b}
    return first == second


def _platform_role(name: str | None, mark: str | None, position: str) -> str | None:
    if not name:
        return None
    for platform in platforms.PLATFORMS:
        found = platform.platform_variable(name)
        if found is not None:
            return found.role
        bare = without_mark(name, mark, position)
        for variable in platform.variables:
            if bare in variable.new_name.values():
                return variable.role
    return None


def _question_text(project: Project, entry: VariableEntry, sure: dict[str, str]) -> str | None:
    target_id = entry.question.value if is_accepted(entry.question) else sure.get(entry.name)
    found = link.target(project.questionnaire, target_id) if target_id else None
    return found.question.text if found else None


def _reasons(
    project: Project,
    entry: VariableEntry,
    earlier: Earlier,
    wave: EarlierWave,
    question_text: str | None,
) -> list[str]:
    reasons = []
    role = _platform_role(entry.name, None, "suffix")
    if role is not None:
        earlier_role = _platform_role(earlier.original, None, "suffix") or _platform_role(
            earlier.name, wave.mark, wave.position
        )
        return ["same_platform_variable"] if role == earlier_role else []
    if wave.source == "table":
        return ["same_original_name"] if earlier.original == entry.name else []
    if entry.file.label and link.texts_agree(entry.file.label, earlier.label):
        reasons.append("same_label")
    elif question_text and link.texts_agree(question_text, earlier.question_text):
        reasons.append("same_question_text")
    elif _similar(entry.file.label, earlier.label):
        reasons.append("similar_label")
    if _same_labels(_value_labels(entry), earlier.value_labels):
        reasons.append("same_value_labels")
    if earlier.numeric is not None and earlier.numeric == (entry.file.storage_type == "numeric"):
        reasons.append("same_type")
    return reasons


def _similar(first: str | None, second: str | None) -> bool:
    a, b = link.normalized_text(first or ""), link.normalized_text(second or "")
    return bool(a and b) and SequenceMatcher(None, a, b).ratio() >= SIMILAR_LABEL


def _score(reasons: list[str]) -> float:
    return sum(WEIGHTS[r] for r in reasons)


def match(project: Project, wave: EarlierWave) -> WaveReport:
    """Match each variable of the project with one of the earlier wave."""
    report = WaveReport(source=wave.source, file_name=wave.file_name)
    sure = link.sure_choices(project) if project.questionnaire else {}
    scored: dict[str, list[Match]] = {}
    for entry in project.variables:
        text = _question_text(project, entry, sure)
        found = []
        for earlier in wave.variables:
            reasons = _reasons(project, entry, earlier, wave, text)
            score = _score(reasons)
            enough = WEIGHTS["same_original_name"] if wave.source == "table" else MIN_SCORE
            if score >= enough or "similar_label" in reasons:
                found.append(Match(entry.name, earlier.name, score, tuple(reasons)))
        scored[entry.name] = sorted(found, key=lambda m: -m.score)
    _with_questions(project, wave, scored)
    _same_shapes_only(project, wave, scored)

    # Clear matches, best first; an earlier variable goes to one variable only.
    clear = []
    for found in scored.values():
        if not found or not STRONG_REASONS & set(found[0].reasons):
            continue  # nothing, or a similar label only: a person decides
        if len(found) == 1 or found[0].score >= MARGIN * found[1].score:
            clear.append(found[0])
    # Two variables as good for the same earlier one: neither gets it, a person chooses.
    best: dict[str, list[Match]] = {}
    for chosen in clear:
        best.setdefault(chosen.earlier, []).append(chosen)
    tied = set()
    for earlier, found in best.items():
        scores = sorted((m.score for m in found), reverse=True)
        if len(scores) > 1 and scores[0] == scores[1]:
            tied.add(earlier)
    taken: set[str] = set()
    for chosen in sorted(clear, key=lambda m: -m.score):
        if chosen.earlier in taken or chosen.earlier in tied:
            continue
        taken.add(chosen.earlier)
        report.matches.append(chosen)
    matched = {m.variable for m in report.matches}
    order = {e.name: k for k, e in enumerate(project.variables)}
    report.matches.sort(key=lambda m: order[m.variable])
    for entry in project.variables:
        if entry.name in matched:
            continue
        options = [m for m in scored[entry.name] if m.earlier not in taken][:MAX_CANDIDATES]
        if options:
            report.candidates[entry.name] = options
        else:
            report.added.append(entry.name)
    report.removed = [v.name for v in wave.variables if v.name not in taken]
    by_name = {v.name: v for v in wave.variables}
    report.removed_labels = {n: by_name[n].label for n in report.removed if by_name[n].label}
    for found in report.matches:
        entry = project.variable(found.variable)
        before = by_name[found.earlier].value_labels
        if before and entry.file.value_labels and not _same_labels(_value_labels(entry), before):
            report.value_labels_changed.append(found.variable)
            report.label_changes[found.variable] = _changes(before, _value_labels(entry))
    report.fragile = sum(1 for m in report.matches if m.reasons == ("same_original_name",))
    report.prefixes = _prefixes(project, wave, report)
    return report


def _changes(before: tuple, after: tuple) -> list[tuple[Code, str | None, str | None]]:
    old = {normalize_code(c): t for c, t in before}
    new = {normalize_code(c): t for c, t in after}
    codes = sorted(set(old) | set(new), key=lambda c: (isinstance(c, str), c))
    return [
        (c, old.get(c), new.get(c))
        for c in codes
        if link.normalized_text(old.get(c) or "") != link.normalized_text(new.get(c) or "")
    ]


def _with_questions(project: Project, wave: EarlierWave, scored: dict[str, list[Match]]) -> None:
    """A variable of a question whose other variables match those of one earlier question
    (the text of "other", sharing its label with every "other"): the variable of that
    earlier question in the same place gains the reason "same_question"."""
    platform = platforms.of(project)
    if platform is None or wave.source == "table":
        return
    by_name = {v.name: v for v in wave.variables}
    for question in link.project_questions(project):
        for name in question.variables:
            # The other variables of the question, matched by a strong reason: a variable
            # never reinforces itself.
            clear = [
                scored[n][0]
                for n in question.variables
                if n != name and scored.get(n) and STRONG_REASONS & set(scored[n][0].reasons)
            ]
            keys = Counter(by_name[m.earlier].question_key for m in clear)
            if not keys:
                continue
            key, count = keys.most_common(1)[0]
            if key is None or count * 2 <= len(clear):
                continue
            place = platform.place(name)
            for earlier in wave.variables:
                if earlier.question_key != key or earlier.other != place.other:
                    continue
                if not place.other and earlier.rank != place.item:
                    continue
                reasons = ("same_question",)
                old = next((m for m in scored[name] if m.earlier == earlier.name), None)
                if old is not None:
                    reasons = (*old.reasons, "same_question")
                    scored[name].remove(old)
                scored[name].append(Match(name, earlier.name, _score(list(reasons)), reasons))
            scored[name].sort(key=lambda m: -m.score)


def _same_shapes_only(project: Project, wave: EarlierWave, scored: dict[str, list[Match]]) -> None:
    """With a table of names, the questions of the export matched by their original names
    only up to the first one whose earlier question of the same number has another shape
    (other items, an "other" or not): a question added there shifts the numbering of all
    those after it."""
    platform = platforms.of(project)
    if platform is None or wave.source != "table":
        return
    earlier: dict[int | str, set] = {}
    for variable in wave.variables:
        place = platform.place(variable.original or "")
        if place is not None:
            earlier.setdefault(place.question, set()).add((place.item, place.other))
    # From the first question whose shape differs, the numbering may have moved: the
    # original names of every later question are not trusted either.
    moved = False
    for question in sorted(link.project_questions(project), key=lambda q: q.rank):
        shape = {(p.item, p.other) for n in question.variables if (p := platform.place(n))}
        moved = moved or earlier.get(question.key) != shape
        if moved:
            for name in question.variables:
                scored[name] = []


def _prefixes(project: Project, wave: EarlierWave, report: WaveReport) -> dict[str, str]:
    """For each group most of whose items match items of one earlier group with a prefix:
    that prefix (from the earlier project, or from the earlier names)."""
    by_name = {v.name: v for v in wave.variables}
    matched = {m.variable: by_name[m.earlier] for m in report.matches}
    found = {}
    for group in project.groups:
        if group.kind != "scale":
            continue  # a set of checkboxes takes the stem of its question
        members = group.members.value or []
        prefixes = Counter(
            matched[m].group_prefix
            or (matched[m].question_key if wave.source == "documented_copy" else None)
            for m in members
            if m in matched
        )
        if not prefixes:
            continue
        prefix, count = prefixes.most_common(1)[0]
        if prefix and count * 2 > len(members):
            found[group.group_id] = prefix
    return found


# --- Proposals. ---


def apply(project: Project, wave: EarlierWave, report: WaveReport) -> int:
    """Propose the earlier names (origin "reference") where nothing is decided, then the
    rules for the rest; returns how many names were proposed from the earlier wave."""
    proposed = 0
    for found in report.matches:
        entry = project.variable(found.variable)
        if not _open(entry.new_name):
            continue
        bare = without_mark(found.earlier, wave.mark, wave.position)
        name = naming.with_wave(bare, project)
        entry.new_name = TrackedValue[str](origin="human")  # its own clash aside
        if not naming.problems(project, entry.name, name):
            entry.new_name = TrackedValue[str](value=name, origin="reference", status="proposed")
            proposed += 1
    for group_id, prefix in report.prefixes.items():
        group = next(g for g in project.groups if g.group_id == group_id)
        if _open(group.name_prefix):
            group.name_prefix = TrackedValue[str](
                value=prefix, origin="reference", status="proposed"
            )
    naming.propose(project)
    return proposed


def _open(tracked: TrackedValue[str]) -> bool:
    """Nothing decided: empty, or a pending proposal of the rules or an earlier wave."""
    if tracked.origin == "human":
        return tracked.value is None
    return tracked.origin in ("rule", "reference") and tracked.status == "proposed"


# --- The table of names and the report. ---


def write_name_table(project: Project, path: Path) -> None:
    """The table of names (D-052): each variable, its final name; the input of the next
    wave."""
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(HEADERS[0])
        writer.writerows((e.name, naming.final_name(e)) for e in project.variables)


REASONS = Texts(
    {
        "same_platform_variable": N_("variable de la plateforme"),
        "same_label": N_("même étiquette"),
        "same_question_text": N_("même question"),
        "same_value_labels": N_("mêmes étiquettes de valeurs"),
        "same_question": N_("même question que ses voisines"),
        "same_rank": N_("même rang"),
        "same_type": N_("même type"),
        "same_original_name": N_("même nom d'origine (seulement)"),
        "similar_label": N_("étiquette semblable"),
    }
)


def reason_text(reasons: tuple[str, ...]) -> str:
    return ", ".join(REASONS.get(r, r) for r in reasons)


def report_markdown(project: Project, report: WaveReport) -> str:
    """The report of differences between the waves, for the team."""
    lines = [
        _("# Écarts entre les vagues"),
        "",
        _("Vague précédente : {name} ; base : {base}.").format(
            name=report.file_name, base=dataset_title(project)
        ),
        "",
        _("- Variables appariées : {n}").format(n=len(report.matches)),
        _("- Variables ajoutées (sans équivalent) : {n}").format(n=len(report.added)),
        _("- Variables à apparier par une personne (plusieurs candidates) : {n}").format(
            n=len(report.candidates)
        ),
        _("- Variables retirées (absentes de la nouvelle vague) : {n}").format(
            n=len(report.removed)
        ),
        _("- Étiquettes de valeurs changées : {n}").format(n=len(report.value_labels_changed)),
    ]
    if report.fragile:
        lines += [
            "",
            _(
                "{n} appariements reposent sur le seul nom d'origine : à vérifier, la "
                "numérotation de la plateforme a pu changer d'une vague à l'autre."
            ).format(n=report.fragile),
        ]
    if report.added:
        lines += ["", _("## Variables ajoutées"), ""]
        lines += [f"- `{n}`{_label(project, n)}" for n in report.added]
    if report.removed:
        lines += ["", _("## Variables retirées"), ""]
        lines += [
            f"- `{n}`"
            + (f" {quoted(report.removed_labels[n])}" if n in report.removed_labels else "")
            for n in report.removed
        ]
    if report.value_labels_changed:
        lines += ["", _("## Étiquettes de valeurs changées"), ""]
        for name in report.value_labels_changed:
            lines.append(f"- `{name}`{_label(project, name)}")
            for code, before, after in report.label_changes.get(name, []):
                lines.append(
                    f"  - {code_text(code)}{colon()}{_value_text(before)} → {_value_text(after)}"
                )
    if report.candidates:
        lines += ["", _("## Plusieurs candidates"), ""]
        for name, options in report.candidates.items():
            found = ", ".join(f"`{m.earlier}` ({reason_text(m.reasons)})" for m in options)
            lines.append(f"- `{name}`{_label(project, name)}{colon()}{found}")
    if report.matches:
        lines += ["", _("## Appariements"), ""]
        lines += [
            f"- `{m.variable}` → `{m.earlier}` ({reason_text(m.reasons)})" for m in report.matches
        ]
    return "\n".join(lines) + "\n"


def _value_text(label: str | None) -> str:
    return quoted(label) if label is not None else _("(aucune étiquette)")


def _label(project: Project, name: str) -> str:
    try:
        label = project.variable(name).file.label
    except KeyError:
        return ""
    return f" {quoted(label)}" if label else ""
