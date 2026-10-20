"""The title of a project (v0.20.2, D-161): what the team calls it ("Sommeil et anxiété,
cohorte 2026"), shown instead of the name of its file. Written by a person only, never
proposed nor sent to the AI, not in the codebook's fingerprint; no file is renamed.
"""

from __future__ import annotations

from pathlib import Path

from ddict.i18n import _
from ddict.project.model import Project

MAX_LENGTH = 120


class TitleError(ValueError):
    """A title the tool refuses; the message is for the person."""


def check(text: str) -> str | None:
    """The title as kept: trimmed; None when empty (the file's name comes back). Raises
    TitleError for a title of more than one line or too long."""
    found = text.strip()
    if not found:
        return None
    if "\n" in found or "\r" in found:
        raise TitleError(_("Le titre tient sur une seule ligne."))
    if len(found) > MAX_LENGTH:
        raise TitleError(
            _("Le titre a {n} caractères ; {m} au plus.").format(n=len(found), m=MAX_LENGTH)
        )
    return found


def set_title(project: Project, text: str) -> bool:
    """Give the project this title (an empty one takes it off); returns whether it changed.
    Not saved: the caller saves the project (D-129, D-130)."""
    found = check(text)
    if found == project.title:
        return False
    project.title = found
    return True


def name(project: Project, path: Path) -> str:
    """What the project is called: its title, else the name of its file."""
    from ddict.workflow import project_stem

    return project.title or project_stem(path)
