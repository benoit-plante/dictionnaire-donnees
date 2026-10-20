"""A variable set aside from the codebook (v0.20.2, D-158).

The team leaves out a variable that is not relevant (a platform's technical column, a
question dropped from the study), with its reason. The variable stays in the project and
in the database, which is never changed: it leaves the codebook (listed apart, with its
reason), the analysis context, the to-do counters and the choices of the analyses. A person
decides, never the AI, and "Remettre dans le codebook" undoes it.

A variable in use is never set aside: a group, an exclusion rule, a recoding, a hypothesis
of the plan, the study's design or an analysis of the notebook names it; each use is said,
to be removed first. Nothing breaks without a word.
"""

from __future__ import annotations

from typing import Any

from ddict.i18n import _
from ddict.project.model import Project, SetAside, VariableEntry

# The fields that name a variable by its original name, in the rules, the recodes, the plan
# and the notebook ("variable", "reversed": a `VariableRef`; "start", "end": a duration).
NAMING_KEYS = {"variable", "variables", "reversed", "start", "end"}


class InUse(ValueError):
    """The variable is in use: `uses` says where, nothing was changed."""

    def __init__(self, name: str, uses: list[str]) -> None:
        super().__init__(name, uses)
        self.name = name
        self.uses = uses


def is_aside(entry: VariableEntry) -> bool:
    return entry.set_aside is not None


def kept(project: Project) -> list[VariableEntry]:
    """The variables of the codebook: those not set aside, in their order."""
    return [e for e in project.variables if e.set_aside is None]


def aside(project: Project) -> list[VariableEntry]:
    return [e for e in project.variables if e.set_aside is not None]


def kept_names(project: Project) -> set[str]:
    return {e.name for e in kept(project)}


def _names(data: Any, name: str) -> bool:
    """Whether a dumped rule, recode, hypothesis or analysis names the variable."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key in NAMING_KEYS and (
                value == name or (isinstance(value, list) and name in value)
            ):
                return True
            if _names(value, name):
                return True
        return False
    if isinstance(data, list):
        return any(_names(item, name) for item in data)
    return False


def uses(project: Project, name: str, notebook=None) -> list[str]:
    """Where the variable is in use, in words; empty when it may be set aside. `notebook`:
    the project's analysis notebook, when it has one."""
    found = []
    for group in project.groups:
        in_group = [*(group.members.value or []), *group.attached, *group.reverse_items]
        if name in in_group:
            found.append(_("le groupe {id}").format(id=group.group_id))
    for rule in project.exclusions.rules:
        if _names(rule.model_dump(mode="json"), name):
            found.append(_("la règle d'exclusion {id}").format(id=rule.id))
    for recode in project.recodes.rules:
        if _names(recode.model_dump(mode="json"), name):
            found.append(_("le recodage {id}").format(id=recode.id))
    for hypothesis in project.plan.hypotheses:
        if _names(hypothesis.model_dump(mode="json"), name):
            found.append(_("l'hypothèse {id} du plan").format(id=hypothesis.id))
    if name in project.dataset.design.model_dump().values():
        found.append(_("la structure de la base (page « Base »)"))
    if notebook is not None:
        for entry in notebook.entries:
            if _names(entry.model_dump(mode="json"), name):
                found.append(_("l'analyse {id} du carnet").format(id=entry.id))
        if _names(notebook.method.model_dump(mode="json"), name):
            found.append(_("la description de l'échantillon (page « Méthode »)"))
    return found


def set_aside(project: Project, name: str, reason: str, today: str, notebook=None) -> None:
    """Leave the variable out of the codebook, with its reason. Raises InUse, the project
    unchanged, when something names it; ValueError for an empty reason."""
    entry = project.variable(name)
    found = uses(project, name, notebook)
    if found:
        raise InUse(name, found)
    entry.set_aside = SetAside(reason=reason, date=today)


def restore(project: Project, name: str) -> bool:
    """Put the variable back in the codebook; False when it was not set aside."""
    entry = project.variable(name)
    if entry.set_aside is None:
        return False
    entry.set_aside = None
    return True
