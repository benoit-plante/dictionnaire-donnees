"""Settings of this computer (v0.5): the language of the interface (D-032).

Kept next to the recent projects (see `recents.config_dir`), never in a project file:
another person on another computer may prefer the other language. DDICT_LANG overrides it.
"""

from __future__ import annotations

import contextlib
import json
import os

from ddict import i18n
from ddict.recents import config_dir

FILE_NAME = "reglages.json"


def _read() -> dict:
    try:
        found = json.loads((config_dir() / FILE_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return found if isinstance(found, dict) else {}


def interface_language() -> str:
    """DDICT_LANG, else the language chosen on the home page, else French."""
    chosen = os.environ.get("DDICT_LANG") or _read().get("interface_language")
    return chosen if chosen in i18n.LANGUAGES else i18n.DEFAULT_LANGUAGE


def save_interface_language(language: str) -> None:
    """Remember the choice. A failure to write is not an error: it is a convenience."""
    if language not in i18n.LANGUAGES:
        raise ValueError(language)
    values = {**_read(), "interface_language": language}
    target = config_dir() / FILE_NAME
    with contextlib.suppress(OSError):
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(values, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def apply() -> str:
    """Use the interface language of this computer; returns it."""
    return i18n.set_language(interface_language())
