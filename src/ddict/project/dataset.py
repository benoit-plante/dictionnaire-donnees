"""The description of the database (v0.8, step 4, D-064): written by a person; a rule only
proposes its structure, never replacing a decision.

- "one_wave_per_file" when a wave mark is set on the Names page (v0.7): the team said this
  file is one wave;
- "wide" when time suffixes (`_t1`, `_t2`...) come back on at least three stems.
"""

from __future__ import annotations

import re
from collections import defaultdict

from ddict.project.model import Project, TrackedValue

STRUCTURES = ("cross_sectional", "one_wave_per_file", "wide", "long")
UNITS = ("participant", "repeated_observation", "dyad", "family", "other")
DESIGN = ("cluster_id", "time", "wave", "cluster", "weight")
MIN_WIDE_STEMS = 3
_SUFFIX = re.compile(r"^(?P<stem>.+?)_(?P<mark>t\d{1,2})$", re.IGNORECASE)


def time_suffixes(project: Project) -> list[str]:
    """The time suffixes shared by at least MIN_WIDE_STEMS stems, each with two or more."""
    marks_of: dict[str, set[str]] = defaultdict(set)
    for entry in project.variables:
        found = _SUFFIX.match(entry.name)
        if found:
            marks_of[found["stem"].lower()].add(found["mark"].lower())
    repeated = [marks for marks in marks_of.values() if len(marks) >= 2]
    if len(repeated) < MIN_WIDE_STEMS:
        return []
    return sorted({f"_{m}" for marks in repeated for m in marks}, key=lambda s: int(s[2:]))


def _rule(project: Project) -> tuple[str | None, dict]:
    if project.settings.naming.wave:
        return "one_wave_per_file", {"wave": project.settings.naming.wave}
    suffixes = time_suffixes(project)
    if suffixes:
        return "wide", {"time_suffixes": suffixes}
    return None, {}


def propose_structure(project: Project) -> None:
    """Propose the structure where nothing is decided; withdraw a proposal no rule makes."""
    dataset = project.dataset
    tracked = dataset.structure
    if tracked.value is not None and tracked.status != "proposed":
        return
    found, details = _rule(project)
    if found is None:
        dataset.structure = TrackedValue[str](origin="human")
        return
    dataset.structure = TrackedValue[str](value=found, origin="rule", status="proposed")
    if found == "one_wave_per_file" and not dataset.wave:
        dataset.wave = details["wave"]
    if found == "wide" and not dataset.time_suffixes:
        dataset.time_suffixes = details["time_suffixes"]
