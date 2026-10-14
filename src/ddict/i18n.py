"""Translatable strings (gettext). Source strings are in French (D-004); the English
catalog is in locale/en (v0.5, D-032, D-033).

The language is read when a string is shown, never at import, so that it can change while
the tool runs: `_` translates now; `N_` only marks a string kept in a table, and `Texts` /
`TextList` translate a table's strings when they are read.
"""

from __future__ import annotations

import gettext
from collections.abc import Iterator, Mapping, Sequence
from functools import cache
from pathlib import Path

LOCALE_DIR = Path(__file__).resolve().parent / "locale"
LANGUAGES = {"fr": "Français", "en": "English"}
DEFAULT_LANGUAGE = "fr"

_current = DEFAULT_LANGUAGE


@cache
def _catalog(language: str) -> gettext.NullTranslations:
    return gettext.translation("ddict", localedir=LOCALE_DIR, languages=[language], fallback=True)


def set_language(language: str | None) -> str:
    """Use this language from now on; an unknown one means French. Returns the one used."""
    global _current
    _current = language if language in LANGUAGES else DEFAULT_LANGUAGE
    return _current


def language() -> str:
    return _current


def _(text: str) -> str:
    return _catalog(_current).gettext(text)


def N_(text: str) -> str:
    """Mark a string for translation without translating it (it is kept in a table)."""
    return text


def _translated(value):
    if isinstance(value, str):
        return _(value)
    if isinstance(value, tuple):
        return tuple(_translated(v) for v in value)
    return value


class Texts(Mapping):
    """A table whose strings are translated each time they are read."""

    def __init__(self, items: Mapping) -> None:
        self._items = dict(items)

    def __getitem__(self, key):
        return _translated(self._items[key])

    def __iter__(self) -> Iterator:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)


class TextList(Sequence):
    """A list of strings translated each time they are read."""

    def __init__(self, items: Sequence) -> None:
        self._items = list(items)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [_translated(v) for v in self._items[index]]
        return _translated(self._items[index])

    def __len__(self) -> int:
        return len(self._items)
