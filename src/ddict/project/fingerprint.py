"""The fingerprint of a codebook (v0.8, step 2): a hash of what the team decided.

Two projects that carry the same decisions have the same fingerprint, on any computer;
any accepted change gives another. In it: what the file says of each variable, the accepted
values, the team's decisions (suspect codes, sourced ranges and thresholds, notes), the
groups, the accepted glossary and the questionnaire the question texts come from. Not in it:
proposals waiting or rejected, dates, model calls, settings, statistics computed on the
data. Exports show its first 12 characters.
"""

from __future__ import annotations

import hashlib
import json

from ddict.project.decisions import is_accepted
from ddict.project.model import GlossaryEntry, Project, TrackedValue, VariableEntry

SHORT = 12


def _accepted(tracked: TrackedValue) -> object:
    return tracked.value if is_accepted(tracked) else None


def _dump(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, list):
        return [_dump(item) for item in value]
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else value


def _variable(entry: VariableEntry) -> dict:
    file = entry.file
    return {
        "name": entry.name,
        "file": {
            "label": file.label,
            "measure_level": file.measure_level,
            "value_labels": _dump(file.value_labels),
            "declared_missing": _dump(file.declared_missing),
        },
        "measure_level": _accepted(entry.measure_level),
        "privacy_class": _accepted(entry.privacy.privacy_class),
        "question": _accepted(entry.question),
        "new_name": _accepted(entry.new_name),
        "value_labels": _dump(_accepted(entry.value_labels)),
        "label": _accepted(entry.label),
        "description": _accepted(entry.description),
        "issues": [_accepted(t) for t in entry.issues if is_accepted(t)],
        "unit": _accepted(entry.unit),
        "group_id": _accepted(entry.group_id),
        "sentinel_decisions": [[d.code, d.missing] for d in entry.sentinel_decisions],
        "theoretical_range": _dump(entry.theoretical_range),
        "thresholds": _dump(entry.thresholds),
        "references": entry.references,
        "notes": entry.notes,
    }


def _glossary_accepted(entry: GlossaryEntry) -> bool:
    return entry.status in ("none", "validated", "corrected")


def decided_content(project: Project) -> dict:
    """What the fingerprint is computed from, in the project's own order."""
    return {
        "variables": [_variable(e) for e in project.variables],
        "groups": [
            {
                "group_id": g.group_id,
                "kind": g.kind,
                "members": _accepted(g.members),
                "attached": g.attached,
                "name_prefix": _accepted(g.name_prefix),
                "descriptive_label": _accepted(g.descriptive_label),
                "instrument_name": _dump(g.instrument_name),
                "reverse_items": g.reverse_items,
                "scoring": _dump(g.scoring),
                "theoretical_range": _dump(g.theoretical_range),
                "thresholds": _dump(g.thresholds),
                "omit_question_text": g.omit_question_text,
            }
            for g in project.groups
        ],
        "glossary": [[e.term, e.meaning] for e in project.glossary if _glossary_accepted(e)],
        "questionnaire": project.questionnaire.sha256 if project.questionnaire else None,
        "dataset": {
            **project.dataset.model_dump(mode="json", exclude={"structure"}),
            "structure": _accepted(project.dataset.structure),
        },
    }


def fingerprint(project: Project) -> str:
    """The SHA-256 of the decided content, as compact JSON with sorted keys."""
    text = json.dumps(
        decided_content(project), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def short(project: Project) -> str:
    """The fingerprint as exports show it: its first 12 characters."""
    return fingerprint(project)[:SHORT]
