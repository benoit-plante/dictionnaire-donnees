"""Whether a project may send its metadata to the AI (v0.18, D-138).

Not by default, and a 0.7.0 project reads as not allowed. Allowing or forbidding is a
decision of the team, saved like any other (the page through `c.save()`, the command line
through `save_project`, both under the check of D-129). Whatever the answer, previews of
the messages stay allowed: they send nothing.
"""

from __future__ import annotations

from ddict.project.model import AiPermission, Project


def is_allowed(project: Project) -> bool:
    return project.settings.ai.allowed


def allow(project: Project, today: str) -> bool:
    """Allow, from `today` ("2026-10-19"); False when it was already, its day kept."""
    if is_allowed(project):
        return False
    project.settings.ai = AiPermission(allowed=True, since=today)
    return True


def forbid(project: Project) -> bool:
    """Forbid; False when it was already."""
    if not is_allowed(project):
        return False
    project.settings.ai = AiPermission()
    return True
