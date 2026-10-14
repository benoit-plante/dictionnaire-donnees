"""The projects opened lately, for the home page (v0.3, D-024).

Kept on this computer, in the user's folder (%APPDATA%\\ddict on Windows, ~/.config/ddict
elsewhere): paths of project files only, never data. The list can be emptied from the home
page. DDICT_CONFIG_DIR sets another folder (the tests use it).
"""

from __future__ import annotations

import contextlib
import json
import os
import sys
from pathlib import Path

MAX_RECENTS = 10
FILE_NAME = "projets-recents.json"


def config_dir() -> Path:
    override = os.environ.get("DDICT_CONFIG_DIR")
    if override:
        return Path(override)
    if sys.platform == "win32" and os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / "ddict"
    base = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(base) / "ddict"


def _file() -> Path:
    return config_dir() / FILE_NAME


def load() -> list[Path]:
    """The recent projects, latest first, that still exist."""
    try:
        paths = json.loads(_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(paths, list):
        return []
    return [Path(p) for p in paths if isinstance(p, str) and Path(p).is_file()]


def _save(paths: list[Path]) -> None:
    target = _file()
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps([str(p) for p in paths], ensure_ascii=False, indent=2) + "\n"
    with target.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def add(path: Path | str) -> None:
    """Put a project at the top of the list. A failure to write is not an error: the list is
    a convenience."""
    path = Path(path).resolve()
    paths = [path, *(p for p in load() if p.resolve() != path)][:MAX_RECENTS]
    with contextlib.suppress(OSError):
        _save(paths)


def clear() -> None:
    with contextlib.suppress(OSError):
        _file().unlink(missing_ok=True)
