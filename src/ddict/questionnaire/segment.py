"""Cut the lines of a questionnaire into questions, options, grids and paragraphs.

No model is involved: the rules follow what survey platforms and word processors produce.

- A question ends with "?" or ":" (possibly followed by an instruction in parentheses), or
  it is a short line followed by its options ("Langue maternelle" / "Français" / ...).
- Its options follow it: indented under it in a PDF, without a blank line in a text file.
- A grid is a question followed by rows, numbered ("1. ...") or starting with "..." as in
  SurveyMonkey; the line(s) in between, split into columns, are its answers. Answers laid
  out in columns without rows below are the options of a single question. Columns that
  run into each other ("MoyennementBeaucoup") are kept as read and flagged: the tool does
  not guess where to cut.
- Input fields of survey platforms ("Date", "JJ/MM/AAAA") are not questions.
- Everything else is a paragraph: instructions, definitions, the consent page.

When the rules are unsure, the result says so (`to_check`) for the person to verify.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ddict.project.model import (
    GridRow,
    Question,
    QuestionnaireText,
    QuestionOption,
)
from ddict.questionnaire.read import Line

MAX_OPTION_LENGTH = 100
MAX_QUESTION_LENGTH = 300
# Column titles sit far to the right of their question: this many characters at least, in
# layout mode ("Presque" / "toujours", "La plupart du" / "temps").
HEADER_INDENT = 10
# A line at least this long was probably cut by the page width (lines of about 90 characters
# in the PDF exports seen): what follows in lower case goes on with it, even after ":".
WRAPPED_LENGTH = 70

_TERMINAL = (".", "?", "!", ":", ";")
# "(ex." or "etc." at the end of a line does not end the sentence.
_ABBREVIATION = re.compile(r"\b(ex|p\. ?ex|etc|env|cf|no|art|vol|chap)\.$", re.IGNORECASE)
_ROW = re.compile(r"(\d{1,3})[.)]\s+(\S.*)")
_ELLIPSIS_ROW = re.compile(r"(?:\.\.\.|…)\s*\S.*")
_QUESTION_END = re.compile(r"[?:]\s*(\([^()]*\))?$")
_FIELD_HINT = re.compile(
    r"Date|Heure|Année/Mois|JJ/MM/AAAA|MM/AAAA|AAAA|HH:MM|DD/MM/YYYY|MM/DD/YYYY",
    re.IGNORECASE,
)
_CHECKBOX = re.compile(
    r"coch\w*\s+tout|toutes\s+les\s+r[ée]ponses\s+applicables|plusieurs\s+r[ée]ponses"
    r"|check\s+all|select\s+all",
    re.IGNORECASE,
)
_GLUED = re.compile(r"[a-zà-ÿ][A-ZÀ-Ý]")


def _is_row(line: Line) -> bool:
    return len(line.cells) == 1 and bool(
        _ROW.fullmatch(line.text) or _ELLIPSIS_ROW.fullmatch(line.text)
    )


def _ends_sentence(text: str) -> bool:
    if text.count("(") > text.count(")") or _ABBREVIATION.search(text):
        return False
    return text.endswith(_TERMINAL)


def _merge(first: Line, second: Line, separator: str = " ") -> Line:
    text = first.text + separator + second.text
    return Line(first.page, first.indent, ((first.cells[0][0], text),), first.after_blank)


def _cut_after_colon(before: str, text: str) -> bool:
    """A line cut by the page width just after a colon: "… Pour nous joindre :" then
    "adresse@exemple.org". A short line ending with a colon is a question with its options."""
    return before.endswith(":") and len(before) >= WRAPPED_LENGTH and text[0].islower()


def join_lines(lines: tuple[Line, ...] | list[Line]) -> list[Line]:
    """Put back together what the page width cut: a line that goes on in lower case."""
    out: list[Line] = []
    for line in lines:
        previous = out[-1] if out else None
        if previous is None or previous.page != line.page or line.after_blank:
            out.append(line)
            continue
        before, text = previous.text, line.text
        if before == "(" or text.startswith(")"):
            out[-1] = _merge(previous, line, separator="")
        elif len(previous.cells) == 1 and len(text) <= 2 and not text[0].isalnum():
            out[-1] = _merge(previous, line)  # a "?" left alone on its line
        elif (
            len(previous.cells) == 1
            and len(line.cells) == 1
            and (not _ends_sentence(before) or _cut_after_colon(before, text))
            # Lower case goes on; so does anything inside a parenthesis left open.
            and (text[0].islower() or text[0] == "(" or before.count("(") > before.count(")"))
            and not _is_row(line)
            and abs(line.indent - previous.indent) <= 2
        ):
            out[-1] = _merge(previous, line)
        else:
            out.append(line)
    return out


@dataclass
class _Draft:
    line: Line
    text: str
    state: str = "question"  # then "options", "header" or "rows"
    options: list[str] = field(default_factory=list)
    header: list[Line] = field(default_factory=list)
    rows: list[tuple[int | None, str]] = field(default_factory=list)


def _header_follows(lines: list[Line], index: int, use_indent: bool) -> bool:
    """Column titles come next: a matrix whose question is a paragraph of instructions
    ("Cochez la case qui correspond le mieux...") rather than a sentence ending in "?"."""
    line = lines[index]
    following = [nxt for nxt in lines[index + 1 : index + 3] if nxt.page == line.page]
    if not following or following[0].after_blank:
        return False
    first = following[0]
    if len(first.cells) >= 2 and "?" not in first.text:
        return first.indent > line.indent if use_indent else True
    return (
        use_indent
        and first.indent >= line.indent + HEADER_INDENT
        and len(following) == 2
        and len(following[1].cells) >= 2
    )


def _has_own_options(lines: list[Line], index: int, use_indent: bool) -> bool:
    """A short line without final punctuation followed by its options: indented short lines
    aligned with each other, or answers laid out in columns. In a text file, without
    indentation, only a line that starts a paragraph can be such a question."""
    line = lines[index]
    text = line.text
    if text.endswith(_TERMINAL[:3]) or len(text) > MAX_OPTION_LENGTH or _is_row(line):
        return False
    if not use_indent and index > 0 and not line.after_blank:
        return False
    following = lines[index + 1 : index + 3]
    if len(following) < 2 or any(
        nxt.page != line.page or nxt.after_blank or len(nxt.text) > MAX_OPTION_LENGTH
        for nxt in following
    ):
        return False
    if not use_indent:
        return not any(_QUESTION_END.search(nxt.text) for nxt in following)
    first, second = following
    if len(first.cells) >= 2 or len(second.cells) >= 2:  # answers in columns
        return first.indent > line.indent
    return first.indent == second.indent > line.indent


def _is_question(lines: list[Line], index: int, use_indent: bool) -> bool:
    line = lines[index]
    if _is_row(line):
        return False
    if _header_follows(lines, index, use_indent):  # instructions may be long
        return True
    if len(line.text) > MAX_QUESTION_LENGTH or _FIELD_HINT.fullmatch(line.text):
        return False
    following = lines[index + 1] if index + 1 < len(lines) else None
    field_follows = (  # "Année/Mois d'arrivée au Canada" then a date field
        following is not None
        and following.page == line.page
        and bool(_FIELD_HINT.fullmatch(following.text))
    )
    return (
        bool(_QUESTION_END.search(line.text))
        or field_follows
        or _has_own_options(lines, index, use_indent)
    )


def _is_instruction(text: str) -> bool:
    """A sentence or an arrow list ("→ cochez le 2 si..."), not a short label such as
    "L'autre parent" that heads its own scale."""
    return text.endswith((".", "...", "…")) or not text[0].isalnum()


def _is_header(line: Line, following: Line | None, draft: _Draft, use_indent: bool) -> bool:
    if len(line.cells) >= 2 and "?" not in line.text:
        return True
    if line.indent < draft.line.indent + (HEADER_INDENT if use_indent else 1):
        return False
    # Far to the right: the end of a column title, or its start above the other titles.
    return draft.state == "header" or (
        following is not None and following.page == line.page and len(following.cells) >= 2
    )


def _is_option(line: Line, draft: _Draft, use_indent: bool) -> bool:
    text = line.text
    if len(text) > MAX_OPTION_LENGTH or text.endswith("?"):
        return False
    return line.indent > draft.line.indent if use_indent else True


def _grid_columns(header: list[Line]) -> list[str]:
    """Column titles written over one or more lines.

    The line with the most cells gives the columns; each cell of the other lines goes to
    the column whose centre is nearest, before its text when written above ("Vraiment"
    over "insatisfait·e"), after it when written below ("Presque" over "toujours").
    """
    main = max(range(len(header)), key=lambda i: len(header[i].cells))
    columns = [(position + len(text) / 2, [], text, []) for position, text in header[main].cells]
    for index, line in enumerate(header):
        if index == main:
            continue
        for position, text in line.cells:
            centre = position + len(text) / 2
            nearest = min(columns, key=lambda column: abs(column[0] - centre))
            (nearest[1] if index < main else nearest[3]).append(text)
    return [" ".join([*above, text, *below]) for _centre, above, text, below in columns]


def _question(draft: _Draft, number: int) -> Question:
    qid = f"Q{number}"
    to_check: list[str] = []
    options = list(draft.options)
    rows = draft.rows
    if rows:
        kind = "grid"
        if any(number is None and not _ELLIPSIS_ROW.fullmatch(text) for number, text in rows):
            to_check.append("grid_rows_unnumbered")
        if draft.header:
            options = _grid_columns(draft.header)
            if any(_GLUED.search(option) for option in options):
                to_check.append("grid_header_unclear")
        else:
            to_check.append("grid_without_header")
    elif draft.header:  # answers laid out in columns, without rows
        options = options + _grid_columns(draft.header)
        kind = "single"
    else:
        kind = "single" if options else "open"
    if kind != "grid" and _CHECKBOX.search(draft.text):
        kind = "checkbox"
    return Question(
        question_id=qid,
        page=draft.line.page,
        text=draft.text,
        kind=kind,
        options=[
            QuestionOption(option_id=f"{qid}.o{k}", text=text)
            for k, text in enumerate(options, start=1)
        ],
        rows=[
            GridRow(row_id=f"{qid}.r{k}", number=row_number, text=text)
            for k, (row_number, text) in enumerate(rows, start=1)
        ],
        to_check=to_check,
    )


def segment(
    lines: tuple[Line, ...] | list[Line], *, use_indent: bool
) -> tuple[list[Question], list[QuestionnaireText]]:
    """Questions in reading order (Q1, Q2, ...) and the paragraphs between them.

    `use_indent` is true for a PDF, whose layout shows options indented under questions.
    """
    logical = join_lines(lines)
    questions: list[Question] = []
    texts: list[QuestionnaireText] = []
    draft: _Draft | None = None
    texts_since_question = 0

    def close() -> None:
        nonlocal draft
        if draft is not None:
            questions.append(_question(draft, len(questions) + 1))
            draft = None

    for index, line in enumerate(logical):
        text = line.text
        following = logical[index + 1] if index + 1 < len(logical) else None
        if draft is not None and line.page == draft.line.page and not line.after_blank:
            if _FIELD_HINT.fullmatch(text):
                continue
            if _is_row(line) and draft.state in ("question", "header", "rows"):
                numbered = _ROW.fullmatch(text)
                if numbered:
                    draft.rows.append((int(numbered.group(1)), numbered.group(2)))
                else:
                    draft.rows.append((None, text))
                draft.state = "rows"
                continue
            if draft.state in ("question", "header") and _is_header(
                line, following, draft, use_indent
            ):
                draft.header.append(line)
                draft.state = "header"
                continue
            if (
                draft.state in ("header", "rows")
                and draft.header
                and not _QUESTION_END.search(draft.text)
                and len(line.cells) == 1
                and not _is_question(logical, index, use_indent)
            ):
                # The statements of a matrix introduced by instructions, not numbered.
                draft.rows.append((None, text))
                draft.state = "rows"
                continue
            if draft.state == "question" and text.startswith("(") and text.endswith(")"):
                draft.text = f"{draft.text} {text}"
                continue
            if (
                draft.state in ("question", "options")
                and _is_option(line, draft, use_indent)
                and not _has_own_options(logical, index, use_indent)
            ):
                draft.options.append(text)
                draft.state = "options"
                continue
        if _is_question(logical, index, use_indent):
            close()
            if (
                not _QUESTION_END.search(text)
                and _is_instruction(text)
                and _header_follows(logical, index, use_indent)
            ):
                # Instructions over several paragraphs, since the last question and on the
                # same page: together they are the question of the matrix.
                while texts_since_question and texts[-1].page == line.page:
                    text = f"{texts.pop().text} {text}"
                    texts_since_question -= 1
            draft = _Draft(line=line, text=text)
            texts_since_question = 0
            continue
        close()
        if _FIELD_HINT.fullmatch(text):
            continue
        numbered = _ROW.fullmatch(text) if len(line.cells) == 1 else None
        last = questions[-1] if questions else None
        if (
            numbered
            and last is not None
            and last.kind == "grid"
            and last.rows
            and last.rows[-1].number is not None
            and int(numbered.group(1)) > last.rows[-1].number
            and texts_since_question == 0
        ):
            # A numbered grid going on over the next page, without its column titles.
            last.rows.append(
                GridRow(
                    row_id=f"{last.question_id}.r{len(last.rows) + 1}",
                    number=int(numbered.group(1)),
                    text=numbered.group(2),
                )
            )
            continue
        texts.append(QuestionnaireText(page=line.page, text=text))
        texts_since_question += 1
    close()
    return questions, texts
