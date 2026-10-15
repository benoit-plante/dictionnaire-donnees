"""The measure level of a variable (v0.8, step 3, D-063): proposed by rules, decided by a
person, and the one in force everywhere (command files, documented copy, codebook, messages
to the model, fingerprint).

The level in force is the one a person accepted or wrote, else the file's. The rules propose
where the file has none (CSV, Excel), and next to the file's when it is doubtful (an item of
a grid declared "scale" whose every observed value has a label, flagged since v0.7; a text
of categories declared "scale"). They
never propose for an identifier, a free text, a date, an empty variable or one of mixed
types, and never replace a decision.
"""

from __future__ import annotations

from ddict.project.decisions import is_accepted
from ddict.project.model import Project, TrackedValue, VariableEntry

LEVELS = ("nominal", "ordinal", "scale")
SENSITIVE = ("likely_identifier", "quasi_identifier", "free_text")
NO_LEVEL_TYPES = ("empty", "mixed", "date", "datetime")
FEW_CODES = 10  # unlabelled integers with at most this many values: codes, not a quantity


def level(entry: VariableEntry) -> str | None:
    """The level in force: accepted or written by a person, else the file's."""
    if is_accepted(entry.measure_level):
        return entry.measure_level.value
    return entry.file.measure_level


def _labelled(entry: VariableEntry) -> bool:
    if entry.file.value_labels:
        return True
    return is_accepted(entry.value_labels) and bool(entry.value_labels.value)


def rule_level(entry: VariableEntry, group_kind: str | None) -> str | None:
    """What the rules would say of this variable, from its type, labels and group."""
    if (entry.privacy.privacy_class.value or "ordinary") in SENSITIVE:
        return None
    kind = entry.profile.inferred_type
    if kind in NO_LEVEL_TYPES:
        return None
    if kind == "text":
        return "nominal"
    distinct = entry.profile.n_distinct
    few = kind == "integer" and distinct is not None and distinct <= FEW_CODES
    if group_kind == "scale" and (_labelled(entry) or few):
        return "ordinal"
    if group_kind == "multiple_response" or _labelled(entry):
        return "nominal"
    if distinct is not None and distinct <= 2:
        return "nominal"  # yes or no, a box ticked or not
    if few:
        return None  # a few unlabelled codes (1, 2, 3, 9): only the team knows
    if kind in ("integer", "decimal"):
        return "scale"
    return None


def _doubtful(entry: VariableEntry) -> bool:
    return "measure_level_doubtful" in entry.profile.flags


def proposal(entry: VariableEntry, group_kind: str | None) -> str | None:
    """The level the rules propose for this variable, or None."""
    if entry.file.measure_level is None:
        return rule_level(entry, group_kind)
    if _doubtful(entry):
        return "ordinal"
    if (
        entry.file.measure_level == "scale"
        and entry.profile.inferred_type == "text"
        and rule_level(entry, group_kind) == "nominal"
    ):
        return "nominal"  # categories written as text, declared "scale" (SPSS's default)
    return None


def _undecided(tracked: TrackedValue[str]) -> bool:
    return tracked.value is None or tracked.status == "proposed"


def propose(project: Project) -> int:
    """Propose a level wherever nothing is decided; a proposal no rule makes any more is
    withdrawn. Returns the number of proposals waiting."""
    kinds = {}
    for group in project.groups:
        for name in [*(group.members.value or []), *group.attached]:
            kinds[name] = group.kind
    for entry in project.variables:
        if not _undecided(entry.measure_level):
            continue
        found = proposal(entry, kinds.get(entry.name))
        if found is None:
            entry.measure_level = TrackedValue[str](origin="human")
        elif entry.measure_level.value != found:
            entry.measure_level = TrackedValue[str](value=found, origin="rule", status="proposed")
    return sum(1 for e in project.variables if e.measure_level.status == "proposed")
