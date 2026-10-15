"""The scoring of a group (v0.8, step 4, D-060): checked against the project, its range
computed, never typed; written by a person only (principle 4)."""

from __future__ import annotations

from ddict import naming
from ddict.project.decisions import is_accepted
from ddict.project.model import Group, Project, Scoring, VariableEntry


class ScoringError(ValueError):
    """The scoring cannot be kept; `problems` says why ("items", "score_name"...)."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__(", ".join(problems))
        self.problems = problems


def structured(scoring: Scoring | None) -> bool:
    return scoring is not None and bool(scoring.items)


def score_range(scoring: Scoring) -> tuple[float, float] | None:
    """The range of the score: n items from min to max, summed or averaged."""
    if not structured(scoring):
        return None
    if scoring.aggregation == "mean":
        return scoring.scale_min, scoring.scale_max
    n = len(scoring.items)
    return n * scoring.scale_min, n * scoring.scale_max


def reversed_items(group: Group, scoring: Scoring) -> list[str]:
    """The confirmed reversed items of the group that the score uses."""
    return [name for name in group.reverse_items if name in scoring.items]


def scale_bounds(entry: VariableEntry) -> tuple[float, float] | None:
    """The smallest and largest labelled codes that are not missing codes: the scale's ends
    as the team's labels give them (1 "Never" to 5 "Always")."""
    labels = list(entry.file.value_labels)
    if not labels and is_accepted(entry.value_labels):
        labels = list(entry.value_labels.value or [])
    missing = {m.low for m in entry.file.declared_missing if m.low == m.high}
    missing |= {d.code for d in entry.sentinel_decisions if d.missing}
    codes = [
        lab.code for lab in labels if isinstance(lab.code, int | float) and lab.code not in missing
    ]
    return (min(codes), max(codes)) if len(codes) >= 2 else None


def check(project: Project, group: Group, scoring: Scoring) -> list[str]:
    """Why this scoring cannot be kept for this group; empty when it can."""
    problems: list[str] = []
    if group.kind != "scale":
        problems.append("kind")
    if not structured(scoring):
        return problems
    members = group.members.value or []
    if any(name not in members for name in scoring.items):
        problems.append("items")
    name = scoring.score_name or ""
    if naming.problems(project, "", name):
        problems.append("score_name")
    others = [
        g.scoring.score_name
        for g in project.groups
        if g.group_id != group.group_id and structured(g.scoring)
    ]
    if name.lower() in {o.lower() for o in others if o}:
        problems.append("score_name_taken")
    return problems


def set_scoring(project: Project, group_id: str, scoring: Scoring | None) -> None:
    """Keep the scoring of a group, or remove it (None)."""
    group = next(g for g in project.groups if g.group_id == group_id)
    if scoring is not None:
        problems = check(project, group, scoring)
        if problems:
            raise ScoringError(problems)
    group.scoring = scoring
