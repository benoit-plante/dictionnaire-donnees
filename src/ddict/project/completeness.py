"""How complete the codebook is (v0.8, step 5): for each element, the variables where it is
decided, out of those where it applies; and what is missing. Computed for each export and
page, never saved: a finding, not a decision (and not in the fingerprint).

Only accepted values count. What is not decided is said to be missing, so that no reader,
person or model, takes an absence for a fact.
"""

from __future__ import annotations

from dataclasses import dataclass

from ddict.project import measure
from ddict.project.decisions import is_accepted
from ddict.project.model import Project, VariableEntry
from ddict.questionnaire.labels import accepted_labels

PARTS = ("question", "label", "value_labels", "measure_level", "new_name", "scoring")


@dataclass(frozen=True)
class Part:
    key: str
    done: int
    applicable: int
    missing: list[str]  # final names of variables, or ids of groups


def _final(entry: VariableEntry) -> str:
    return entry.new_name.value if is_accepted(entry.new_name) else entry.name


def _sensitive(entry: VariableEntry) -> bool:
    return (entry.privacy.privacy_class.value or "ordinary") in measure.SENSITIVE


def _coded(entry: VariableEntry) -> bool:
    """A numeric variable whose codes stand for categories: its labels say what they mean.
    The level in force says so, else the one proposed (a CSV before any decision)."""
    level = measure.level(entry)
    if level is None and entry.measure_level.status == "proposed":
        level = entry.measure_level.value
    return (
        entry.file.storage_type == "numeric"
        and level in ("nominal", "ordinal")
        and not _sensitive(entry)
    )


def _levelled(entry: VariableEntry) -> bool:
    """A variable that a measure level applies to."""
    return not _sensitive(entry) and entry.data_type not in measure.NO_LEVEL_TYPES


def _part(key: str, entries: list[VariableEntry], decided) -> Part:
    missing = [_final(e) for e in entries if not decided(e)]
    return Part(key, len(entries) - len(missing), len(entries), missing)


def parts(project: Project) -> list[Part]:
    """The elements that apply to this project, in the order of the exports."""
    variables = project.variables
    found = []
    if project.questionnaire is not None:
        found.append(_part("question", variables, lambda e: is_accepted(e.question)))
    found.append(_part("label", variables, lambda e: bool(e.file.label) or is_accepted(e.label)))
    found.append(
        _part("value_labels", [e for e in variables if _coded(e)], lambda e: accepted_labels(e))
    )
    found.append(
        _part(
            "measure_level",
            [e for e in variables if _levelled(e)],
            lambda e: measure.level(e) is not None,
        )
    )
    if any(e.new_name.value for e in variables):  # once renaming has begun
        found.append(_part("new_name", variables, lambda e: is_accepted(e.new_name)))
    scales = [g for g in project.groups if g.kind == "scale"]
    if scales:
        missing = [g.group_id for g in scales if g.scoring is None]
        found.append(Part("scoring", len(scales) - len(missing), len(scales), missing))
    return [p for p in found if p.applicable]


def dataset_missing(project: Project) -> list[str]:
    """What the team has not said of the database: "unit", "structure"."""
    found = project.dataset
    missing = []
    if not found.unit_of_observation:
        missing.append("unit")
    if not is_accepted(found.structure):
        missing.append("structure")
    return missing
