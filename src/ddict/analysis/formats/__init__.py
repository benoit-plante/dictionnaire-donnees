"""The formats of the APA tables and figures (v0.10, D-083), each in its own module.

A format renders an `ApaDocument` (`ddict.analysis.apa`) to bytes and adds nothing to it. It
says what it renders (tables, figures or both) and how to read its own text back, for the
test every format must pass (tests/test_apa_formats.py): every number, title and note of
the description is found in the file. The page and `ddict analyser --format` list the
formats of FORMATS by themselves: a new format is a new module that calls `register`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ddict.analysis.apa import ApaDocument


@dataclass(frozen=True)
class Format:
    key: str  # what `ddict analyser --format` takes: "docx"
    label: str  # in French; translated where it is shown (N_)
    suffix: str  # added to the analysis's file name: ".docx", "-graphiques.xlsx"
    mime: str
    tables: bool  # renders the tables
    figures: bool  # renders the figures
    render: Callable[[ApaDocument], bytes]
    read_text: Callable[[bytes], str]  # its text back, for the common test


FORMATS: dict[str, Format] = {}


def register(found: Format) -> Format:
    FORMATS[found.key] = found
    return found


def available(document: ApaDocument) -> list[Format]:
    """The formats that have something to render for this document."""
    return [
        f
        for f in FORMATS.values()
        if (f.tables and document.tables) or (f.figures and document.figures)
    ]


# The formats of this version (D-085): importing them registers them.
from ddict.analysis.formats import docx  # noqa: E402, F401
