"""What the codebook says of a variable an analysis uses, by its final name (v0.9)."""

from __future__ import annotations

from ddict.analysis import conditions
from ddict.analysis.data import PreparedData
from ddict.export import wording as w
from ddict.i18n import _
from ddict.project.model import Project
from ddict.questionnaire.labels import accepted_labels


class Codebook:
    def __init__(self, project: Project, prepared: PreparedData) -> None:
        self.entries = {w.final_name(e): e for e in project.variables}
        self.levels = conditions.levels(project)
        self.prepared = prepared

    def label(self, name: str) -> str:
        entry = self.entries.get(name)
        if entry is None:
            group = self.prepared.scores.get(name)
            return _("{name} (score de {group})").format(name=name, group=group) if group else name
        return w.label_text(entry, "final") or name

    def value_labels(self, name: str) -> dict:
        entry = self.entries.get(name)
        return {lab.code: lab.label for lab in accepted_labels(entry)} if entry else {}

    def category(self, name: str, code) -> str:
        labels = self.value_labels(name)
        return labels.get(code, w.code_text(code))
