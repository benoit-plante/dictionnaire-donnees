"""The projects followed, for the home page's table (v0.17, D-131).

Kept on this computer, next to the recent projects (`recents.config_dir`): paths of project
files only, never a name, a phase or a number. Unlike the recents, the list has no limit and
keeps a project that is no longer found. Paths are kept as given, made absolute but never
resolved: a network drive `Z:\\` stays `Z:\\`. A failure to write is not an error: the list
is a convenience, and the caller says it.
"""

from __future__ import annotations

import json
import os
import stat
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

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
    return follow_all([path])


def follow_all(new: list[Path] | list[str]) -> bool:
    """Add several project files at once (one writing of the list)."""
    paths = _read()
    if paths is None:
        return False
    known = {ondisk.key(p) for p in paths}
    added = [Path(p) for p in new if ondisk.key(p) not in known]
    if not added:
        return True
    return _save([*paths, *added])


def replace(old: Path | str, new: Path | str) -> bool:
    """A project found again elsewhere: its new path takes the old one's place (once, when
    the new one was followed already)."""
    paths = _read()
    if paths is None:
        return False
    gone = {ondisk.key(old), ondisk.key(new)}
    return _save([*(p for p in paths if ondisk.key(p) not in gone), Path(new)])


def unfollow(path: Path | str) -> bool:
    """Take a project off the list, found or not. No project file is touched."""
    paths = _read()
    if paths is None:
        return False
    wanted = ondisk.key(path)
    return _save([p for p in paths if ondisk.key(p) != wanted])


# --- Looking for projects in a folder (D-132). ---

DEPTH = 4  # levels of folders below the chosen one
MAX_PROJECTS = 500
MAX_FOLDERS = 20_000
SKIPPED = {"appdata", "node_modules"}
HIDDEN = stat.FILE_ATTRIBUTE_HIDDEN | stat.FILE_ATTRIBUTE_SYSTEM


@dataclass(frozen=True)
class Search:
    found: list[Path]  # sorted
    stopped: Literal["projects", "folders"] | None = None  # a limit was reached


def _skipped(entry: os.DirEntry) -> bool:
    """A folder not looked into: hidden or system, the tool's exchanges, those of programs;
    a link or a junction, never followed (those of "Documents" would loop)."""
    name = entry.name.casefold()
    if name.startswith((".", "$")) or name in SKIPPED or name.endswith(".dd-envois"):
        return True
    if entry.is_symlink():
        return True
    try:
        info = entry.stat(follow_symlinks=False)
    except OSError:
        return True
    if getattr(info, "st_file_attributes", 0) & HIDDEN:
        return True
    return getattr(info, "st_reparse_tag", 0) == stat.IO_REPARSE_TAG_MOUNT_POINT


def search(folder: Path | str) -> Search:
    """The project files (`*.dd.json`) in a folder and its subfolders, down to DEPTH levels.
    Only names are looked at: no file is opened, so a OneDrive file "online only" is not
    downloaded. A folder that cannot be read is passed over."""
    found: list[Path] = []
    waiting = deque([(Path(folder), 0)])
    looked = 0
    while waiting:
        if looked >= MAX_FOLDERS:
            return Search(sorted(found, key=_order), "folders")
        current, depth = waiting.popleft()
        looked += 1
        try:
            with os.scandir(current) as entries:
                listed = sorted(entries, key=lambda e: e.name.casefold())
        except OSError:
            continue
        for entry in listed:
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
            except OSError:
                continue
            if is_dir:
                if depth < DEPTH and not _skipped(entry):
                    waiting.append((Path(entry.path), depth + 1))
            elif entry.name.casefold().endswith(".dd.json"):
                if len(found) >= MAX_PROJECTS:
                    return Search(sorted(found, key=_order), "projects")
                found.append(Path(entry.path))
    return Search(sorted(found, key=_order))


def _order(path: Path) -> tuple[str, str]:
    return str(path).casefold(), str(path)
