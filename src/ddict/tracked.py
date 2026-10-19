"""The projects followed, for the home page's table (v0.17, D-131).

Kept on this computer, next to the recent projects (`recents.config_dir`): paths of project
files only, never a name, a phase or a number. Unlike the recents, the list has no limit and
keeps a project that is no longer found. Paths are kept as given, made absolute but never
resolved: a network drive `Z:\\` stays `Z:\\`. A failure to write is not an error: the list
is a convenience, and the caller says it.
"""

from __future__ import annotations

import json
from pathlib import Path

from ddict import recents
from ddict.i18n import _
from ddict.project import ondisk

FILE_NAME = "projets-suivis.json"
FORMAT = 1


def not_written() -> str:
    return _(
        "La liste des projets suivis n'a pas pu être enregistrée sur cet ordinateur ; "
        "le projet, lui, n'est pas touché."
    )


def _file() -> Path:
    return recents.config_dir() / FILE_NAME


def _read() -> list[Path] | None:
    """The list as written; empty when there is none yet; None when the file cannot be read
    (then it is never overwritten)."""
    target = _file()
    if not target.exists():
        return []
    try:
        content = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    paths = content.get("projets") if isinstance(content, dict) else None
    if not isinstance(paths, list):
        return None
    return [Path(p) for p in paths if isinstance(p, str) and p]


def _sorted(paths: list[Path]) -> list[Path]:
    """One line per project, sorted without regard to case: the same list, the same bytes."""
    unique = {ondisk.key(p): Path(p).absolute() for p in paths}
    return sorted(unique.values(), key=lambda p: (str(p).casefold(), str(p)))


def _save(paths: list[Path]) -> bool:
    content = {"format": FORMAT, "projets": [str(p) for p in _sorted(paths)]}
    text = json.dumps(content, ensure_ascii=False, indent=2) + "\n"
    try:
        target = _file()
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    except OSError:
        return False
    return True


def load() -> list[Path]:
    """The projects followed, found or not, sorted."""
    return _sorted(_read() or [])


def is_followed(path: Path | str) -> bool:
    wanted = ondisk.key(path)
    return any(ondisk.key(p) == wanted for p in load())


def follow(path: Path | str) -> bool:
    """Add a project file to the list; True when the list is written (or already holds it)."""
    paths = _read()
    if paths is None:
        return False
    wanted = ondisk.key(path)
    if any(ondisk.key(p) == wanted for p in paths):
        return True
    return _save([*paths, Path(path)])


def unfollow(path: Path | str) -> bool:
    """Take a project off the list, found or not. No project file is touched."""
    paths = _read()
    if paths is None:
        return False
    wanted = ondisk.key(path)
    return _save([p for p in paths if ondisk.key(p) != wanted])
