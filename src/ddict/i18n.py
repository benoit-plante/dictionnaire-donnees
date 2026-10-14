"""Translatable strings (gettext). Source strings are in French (D-004); the English
catalog is in locale/en (v0.5, D-032, D-033).

The language is read when a string is shown, never at import, so that it can change while
the tool runs: `_` translates now; `N_` only marks a string kept in a table, and `Texts` /
`TextList` translate a table's strings when they are read.
"""

from __future__ import annotations

import gettext
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from functools import cache, wraps
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


@contextmanager
def using(language: str | None) -> Iterator[str]:
    """Write in this language for a while (a codebook in English from a French interface,
    D-032), then come back to the language in use. None keeps the language in use."""
    previous = _current
    try:
        yield set_language(language) if language else previous
    finally:
        set_language(previous)


def in_language(function: Callable) -> Callable:
    """A writer that takes `language=`: its whole output is in that language."""

    @wraps(function)
    def wrapper(*args, language: str | None = None, **kwargs):
        with using(language):
            return function(*args, **kwargs)

    return wrapper


def decimal(text: str) -> str:
    """ "0,363" in French, "0.363" in English."""
    return text.replace(".", ",") if _current == "fr" else text


def _(text: str) -> str:
    return _catalog(_current).gettext(text)


def colon() -> str:
    """ " : " in French, ": " in English."""
    return " : " if _current == "fr" else ": "


def semicolon() -> str:
    """ " ; " in French, "; " in English."""
    return " ; " if _current == "fr" else "; "


def field_label(text: str) -> str:
    """ "Format : " in French, "Format: " in English: a translated label before a value."""
    return _(text) + colon()


def quoted(text: str) -> str:
    """« text » in French, "text" in English."""
    return f"« {text} »" if _current == "fr" else f'"{text}"'


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
