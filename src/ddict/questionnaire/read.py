"""Read a questionnaire (PDF or text) into lines that keep their layout cues.

What matters for finding questions is not only the words but where they sit: options are
indented under their question in a PDF, and the columns of a grid are far apart. A PDF is
read in pypdf's layout mode, which keeps horizontal spacing; a text file copied from a word
processor keeps its tabs between table cells and its blank lines between paragraphs.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from ddict.io.csv_reader import decode
from ddict.io.model import ReadError
from ddict.io.sav import file_sha256

FORMATS = {".pdf": "pdf", ".txt": "txt"}

_FOOTER = re.compile(r"Page \d+( (de|sur|of) \d+)?", re.IGNORECASE)
# In layout mode, words of a phrase are one space apart and table columns several.
_PDF_CELL = re.compile(r"\S+(?: \S+)*")


@dataclass(frozen=True)
class Line:
    page: int | None
    indent: int  # leading spaces (PDF) or tabs (text): options sit deeper than questions
    cells: tuple[tuple[int, str], ...]  # (position, text): several for a table row
    after_blank: bool = False  # a blank line came before (text files only)

    @property
    def text(self) -> str:
        return " ".join(cell for _position, cell in self.cells)


@dataclass(frozen=True)
class QuestionnaireFile:
    name: str
    sha256: str
    format: str
    n_pages: int | None
    lines: tuple[Line, ...]


def normalize(text: str) -> str:
    """Ligatures, non-breaking and repeated spaces, composed accents (NFC)."""
    text = unicodedata.normalize("NFKC", text).replace("\N{SOFT HYPHEN}", "")
    spaces = "[ \N{NO-BREAK SPACE}\N{NARROW NO-BREAK SPACE}]+"
    return unicodedata.normalize("NFC", re.sub(spaces, " ", text).strip())


def _pdf_lines(path: Path) -> tuple[int, list[Line]]:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(path)
        pages = [page.extract_text(extraction_mode="layout") for page in reader.pages]
    except (PdfReadError, OSError, ValueError) as error:
        raise ReadError(f"Cannot read {path.name} as a PDF file: {error}") from error
    lines = []
    for number, page in enumerate(pages, start=1):
        for raw in page.splitlines():
            raw = unicodedata.normalize("NFKC", raw).replace("\t", " ").rstrip()
            if not raw.strip() or _FOOTER.fullmatch(raw.strip()):
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            cells = tuple((m.start(), normalize(m.group())) for m in _PDF_CELL.finditer(raw))
            lines.append(Line(page=number, indent=indent, cells=cells))
    return len(pages), lines


def _text_lines(path: Path) -> tuple[int | None, list[Line]]:
    try:
        text, _encoding = decode(path.read_bytes())
    except (OSError, UnicodeError) as error:
        raise ReadError(f"Cannot read {path.name} as a text file: {error}") from error
    pages = text.replace("\r\n", "\n").replace("\r", "\n").split("\f")
    lines = []
    for number, page in enumerate(pages, start=1):
        blank = False
        for raw in page.split("\n"):
            if not raw.strip():
                blank = True
                continue
            indent = len(raw) - len(raw.lstrip("\t"))
            cells = tuple(
                (column, normalize(cell))
                for column, cell in enumerate(raw.split("\t"))
                if cell.strip()
            )
            page_number = number if len(pages) > 1 else None
            lines.append(Line(page=page_number, indent=indent, cells=cells, after_blank=blank))
            blank = False
    return (len(pages) if len(pages) > 1 else None), lines


def read_questionnaire(path: Path | str) -> QuestionnaireFile:
    path = Path(path)
    kind = FORMATS.get(path.suffix.lower())
    if kind is None:
        raise ReadError(
            f"Unsupported questionnaire format: {path.suffix or '(none)'} "
            f"(supported: {', '.join(FORMATS)})"
        )
    n_pages, lines = _pdf_lines(path) if kind == "pdf" else _text_lines(path)
    return QuestionnaireFile(
        name=path.name,
        sha256=file_sha256(path),
        format=kind,
        n_pages=n_pages,
        lines=tuple(lines),
    )
