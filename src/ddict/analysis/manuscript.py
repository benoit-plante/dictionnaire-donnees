"""The statistics written in a Word manuscript (v0.15, step 4, D-117; docs/verification-depot.md,
§ 2.1): the paragraphs cut into sentences, the tables into rows read with the header of their
columns; in each, the statistics written in the APA style, in French or in English, with their
value, their decimals, their degrees of freedom and their intervals. A number is read only
after a known symbol: a table number, a date, a range in a label are never statistics. An
"x = number" whose symbol is not known is listed as not read, never guessed.

The manuscript is read, never changed; nothing of it leaves the computer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pathlib import Path

from ddict.i18n import _

# A number as written: a sign, digits with a French thousands space ("1 106"), a decimal
# comma or point, or none before it (",25", ".25").
_NUMBER = r"[-−–]?\s?(?:\d{1,3}(?: \d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?|[.,]\d+)"
NUMBER = re.compile(_NUMBER)


@dataclass(frozen=True)
class Number:
    value: float
    decimals: int
    text: str


def number(text: str) -> Number | None:
    """ "−2,28" → −2.28 with 2 decimals; ",011" → 0.011 with 3; "1 106" → 1106."""
    written = text.strip()
    cleaned = written.replace("−", "-").replace("–", "-").replace(" ", "").replace("\u00a0", "")
    if not re.fullmatch(r"-?(?:\d+(?:[.,]\d+)?|[.,]\d+)", cleaned):
        return None
    decimals = len(re.split(r"[.,]", cleaned)[1]) if re.search(r"[.,]", cleaned) else 0
    return Number(float(cleaned.replace(",", ".")), decimals, written)


@dataclass(frozen=True)
class Value:
    """A statistic as written. `of`: for a bound of an interval, the statistic it belongs to;
    `threshold`: "p < ,05" said of a rule, alone in its sentence, not a result."""

    stat: str
    value: float
    decimals: int
    relation: str  # "=", "<", ">"
    text: str
    df: tuple[Number, ...] = ()
    of: str = ""
    qualifier: str = ""
    threshold: bool = False
    cell: int = -1  # in a table row: the column it was read in (0 is the row's label)


@dataclass(frozen=True)
class Block:
    """A sentence of a paragraph or a row of a table, with where it is."""

    where: str  # "§ 12, phrase 1", "Tableau 4, ligne 2"
    kind: str  # "sentence" or "row"
    text: str
    section: str  # the heading above it
    label: str = ""  # the first cell of a table row
    values: tuple[Value, ...] = ()
    unread: tuple[str, ...] = ()
    # Where to find it again in the document (step 5, the comments): the paragraph's rank
    # among the paragraphs with text, or the table's rank and the row's index in it.
    paragraph: int = 0
    table: int = 0
    row: int = 0


# --- The symbols. ---

# Each: the key of the statistic, then the ways it is written, in a regular expression
# matched just before "=", "<" or ">" (with or without degrees of freedom in parentheses).
# The longer forms come first: "η² partiel" before "η²", "d_z" before "d".
SYMBOLS: tuple[tuple[str, str], ...] = (
    ("dR2", r"ΔR²|ΔR2|Delta R2"),
    (
        "R2",
        r"R² de (?:McFadden|Nagelkerke|Cox et Snell)|(?:McFadden|Nagelkerke|Cox and Snell|"
        r"Cox & Snell) R²|R² ajusté|adjusted R²|R²|R2|de (?:McFadden|Nagelkerke)",
    ),
    ("eta2p", r"η²p|η²ₚ|η² partiel|partial η²|ηp²|η2p"),
    ("eta2", r"η²|η2"),
    ("epsilon2", r"ε²|ε2"),
    ("omega2", r"ω²|ω2"),
    ("chi2", r"χ²|χ2|X²|X2|chi2|khi²|khi2"),
    ("dz", r"d_z|dz|d<sub>z</sub>"),
    ("d", r"d"),
    ("g", r"g"),
    ("t", r"t"),
    ("F", r"F"),
    ("H", r"H"),
    ("U", r"U"),
    ("V", r"V"),
    ("W", r"W(?: de Mauchly)?|Mauchly's W"),
    ("z", r"z"),
    ("r", r"r"),
    ("rho", r"ρ"),
    ("p", r"p"),
    ("M", r"M|Mdn"),
    ("SD", r"ÉT|SD"),
    ("SE", r"ET|SE"),
    ("b", r"b|B"),
    ("beta", r"β"),
    ("OR", r"RC|OR"),
    ("N", r"N"),
    ("n", r"n"),
    ("eps", r"ε"),
)
_SYMBOL_GROUPS = "|".join(f"(?P<s{i}>{pattern})" for i, (_k, pattern) in enumerate(SYMBOLS))
_STAT = re.compile(
    r"(?<![\w²])(?:" + _SYMBOL_GROUPS + r")"
    r"(?:\s*\((?P<df>[^()]*)\))?"
    r"\s*(?P<rel>[=<>≤≥])\s*(?P<num>" + _NUMBER + r")"
)
# Any "symbol = number": what is not a known statistic is listed as not read.
_ANY = re.compile(
    r"(?<![\w²])(?P<sym>[A-Za-zÀ-ÿΑ-ωΔ][\wÀ-ÿ²ₚ'’]{0,24})\s*(?:\([^()]*\))?\s*[=<>≤≥]\s*"
    r"(?P<num>" + _NUMBER + r")"
)
# An interval: "IC 95 % [a ; b]", "95% CI [a, b]", or brackets alone (a table cell).
_INTERVAL = re.compile(
    r"(?:IC\s*95\s*%|95\s*%\s*CI)?\s*\[\s*(?P<low>"
    + _NUMBER
    + r")\s*[;,]\s*(?P<high>"
    + _NUMBER
    + r")\s*\]"
)
# A difference written without "=": "différence 3,00, IC 95 % [2,28 ; 3,72]".
_DIFFERENCE = re.compile(r"(?<!\w)(?:différence|difference)\s+(?P<num>" + _NUMBER + r")", re.I)
# Words never a statistic, even before "=": "Tableau 2", "H1 =", "n° 3"…
NOT_STATISTICS = re.compile(r"^(?:Tableau|Table|Figure|H\d+|A\d+|E\d+|R\d+|n°|p\.)$", re.I)


def _key(match: re.Match) -> str:
    for i, (key, _pattern) in enumerate(SYMBOLS):
        if match.group(f"s{i}") is not None:
            return key
    raise AssertionError(match.group(0))


def _degrees(text: str | None) -> tuple[Number, ...]:
    """ "818", "2, 404", "1,72 ; 346,74", "1.72, 346.74"."""
    if not text:
        return ()
    parts = text.split(";") if ";" in text else re.split(r",\s+", text)
    found = tuple(n for n in (number(p) for p in parts) if n is not None)
    return found if len(found) == len(parts) else ()


def _qualifier(written: str) -> str:
    for word in ("McFadden", "Nagelkerke", "Cox", "ajusté", "adjusted", "partiel", "partial"):
        if word in written:
            return word
    return ""


def statistics(text: str) -> tuple[list[Value], list[str]]:
    """The statistics of a text, in their order, and the "x = number" not read."""
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    values: list[Value] = []
    spans: list[tuple[int, int]] = []
    for match in _STAT.finditer(text):
        found = number(match.group("num"))
        if found is None:
            continue
        key = _key(match)
        df = _degrees(match.group("df"))
        if match.group("df") and not df and key not in ("R2",):
            continue  # "t (voir plus haut) = 2": not a statistic as APA writes it
        relation = {"≤": "<", "≥": ">"}.get(match.group("rel"), match.group("rel"))
        values.append(
            Value(
                key,
                found.value,
                found.decimals,
                relation,
                match.group(0).strip(),
                df,
                qualifier=_qualifier(match.group(0)),
            )
        )
        spans.append(match.span())
    for match in _DIFFERENCE.finditer(text):
        found = number(match.group("num"))
        if found is not None:
            at = sum(1 for start, _end in spans if start < match.start())
            values.insert(at, Value("diff", found.value, found.decimals, "=",
                                    match.group(0).strip()))  # fmt: skip
            spans.insert(at, match.span())
    for match in _INTERVAL.finditer(text):
        low, high = number(match.group("low")), number(match.group("high"))
        if low is None or high is None:
            continue
        before = [v for v, (start, _end) in zip(values, spans, strict=True)
                  if start < match.start()]  # fmt: skip
        owner = before[-1].stat if before else ""
        index = len(before)
        values.insert(index, Value("ci_low", low.value, low.decimals, "=", low.text, of=owner))
        values.insert(index + 1, Value("ci_high", high.value, high.decimals, "=", high.text,
                                       of=owner))  # fmt: skip
        spans.insert(index, match.span())
        spans.insert(index + 1, match.span())
    unread = []
    for match in _ANY.finditer(text):
        if any(start <= match.start("num") < end for start, end in spans):
            continue
        symbol = match.group("sym").strip()
        if NOT_STATISTICS.match(symbol) or not symbol:
            continue
        unread.append(match.group(0).strip())
    tested = [v for v in values if v.stat not in ("p", "ci_low", "ci_high")]
    if not tested:  # "p < ,05" said of a rule, not a result
        values = [
            Value(**{**v.__dict__, "threshold": True}) if v.stat == "p" and v.relation == "<" else v
            for v in values
        ]
    return values, unread


# --- The document. ---

# A sentence ends with ".", "!" or "?" then a space and a capital, or the end of the
# paragraph; a decimal point (".25", "2.28") never ends one.
_END = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Ý«“(\[])")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in _END.split(text) if s.strip()]


# The header of a table column, as the tool and APA write it.
COLUMNS: tuple[tuple[str, str], ...] = (
    ("ci", r"^(?:IC 95 %|95% CI|IC)"),
    ("t", r"^t(?:\s*\(.*\))?$"),
    ("F", r"^F(?:\s*\(.*\))?$"),
    ("chi2", r"^(?:χ²|χ2|X²)(?:\s*\(.*\))?$"),
    ("p", r"^p$"),
    ("M", r"^(?:M|Mdn)$"),
    ("SD", r"^(?:ÉT|SD)$"),
    ("SE", r"^(?:ET|SE)$"),
    ("dz", r"^(?:dz|d_z)$"),
    ("d", r"^d$"),
    ("b", r"^(?:b|B)$"),
    ("beta", r"^β$"),
    ("z", r"^z$"),
    ("r", r"^(?:r|\d+)$"),  # a correlation matrix numbers its columns
    ("OR", r"^(?:RC|OR)$"),
    ("n", r"^(?:n|N)$"),
    ("diff", r"^(?:Différence|Difference)$"),
    ("eta2p", r"^(?:η²p|η² partiel|partial η²)$"),
    ("U", r"^U$"),
    ("W", r"^W$"),
)


def column_stat(header: str) -> tuple[str, tuple[Number, ...]]:
    """The statistic of a column, and the degrees of freedom of its header ("t(227)")."""
    header = header.strip()
    for key, pattern in COLUMNS:
        if re.match(pattern, header):
            inside = re.search(r"\((.*)\)", header)
            return key, _degrees(inside.group(1) if inside else None)
    return "", ()


def _cell(text: str, stat: str, df: tuple[Number, ...], owner: str) -> list[Value]:
    """The values of a cell under its column's statistic: "21,56", "< ,001", "3,00 [2,28 ;
    3,72]", "−,38 [−,49 ; −,27]", "[0,40 ; 0,68]"."""
    text = text.replace("\u00a0", " ").replace("\u202f", " ").strip()
    found: list[Value] = []
    if stat == "ci":
        interval = _INTERVAL.search(text)
        if interval:
            low, high = number(interval.group("low")), number(interval.group("high"))
            if low and high:
                found += [Value("ci_low", low.value, low.decimals, "=", low.text, of=owner),
                          Value("ci_high", high.value, high.decimals, "=", high.text,
                                of=owner)]  # fmt: skip
        return found
    head = re.match(r"\s*(?P<rel>[<>≤≥])?\s*(?P<num>" + _NUMBER + r")", text)
    if head:
        value = number(head.group("num"))
        if value is not None:
            relation = {"≤": "<", "≥": ">"}.get(head.group("rel") or "=", head.group("rel") or "=")
            found.append(Value(stat, value.value, value.decimals, relation, head.group(0).strip(),
                               df))  # fmt: skip
    interval = _INTERVAL.search(text)
    if interval and found:
        low, high = number(interval.group("low")), number(interval.group("high"))
        if low and high:
            found += [
                Value("ci_low", low.value, low.decimals, "=", low.text, of=stat),
                Value("ci_high", high.value, high.decimals, "=", high.text, of=stat),
            ]
    return found


def _holds_value(cell: str) -> bool:
    return bool(cell) and (number(cell.split(" ")[0]) is not None or cell.startswith(("<", "[")))


def _table_blocks(table, number_: int, section: str) -> list[Block]:
    rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
    # The first row of values: the header is the row above it (the first row is always a
    # header, even with numbers: a correlation matrix numbers its columns "1", "2", "3").
    first = next(
        (i for i, row in enumerate(rows) if i > 0 and any(_holds_value(c) for c in row[1:])),
        None,
    )
    if first is None:
        return []
    header = rows[first - 1]
    blocks = []
    for i, row in enumerate(rows[first:], start=first):
        blocks.append(
            Block(
                _("Tableau {n}, ligne {row}").format(n=number_, row=i - first + 1),
                "row",
                " | ".join(row),
                section,
                row[0],
                tuple(row_values(header, row)),
                table=number_,
                row=i,
            )
        )
    return blocks


def row_values(header: list[str], row: list[str]) -> list[Value]:
    """The values of a table row read under the header of its columns; its label (the first
    cell) may hold a count ("n = 228")."""
    values: list[Value] = []
    owner = ""
    for j, text in enumerate(row[1:], start=1):
        stat, df = column_stat(header[j] if j < len(header) else "")
        if not stat or not text or text == "—":
            continue
        found = _cell(text, stat, df, owner)
        if stat == "r" and header[j].strip().isdigit():  # the pair of a matrix cell
            found = [replace(v, qualifier=header[j].strip()) for v in found]
        if found and found[0].stat not in ("ci_low", "ci_high"):
            owner = found[0].stat
        values += [replace(v, cell=j) for v in found]
    label_values, _unread = statistics(row[0])
    return [replace(v, cell=0) for v in label_values] + values


def read(path: Path | str) -> list[Block]:
    """The blocks of a manuscript, in the order of the document: the sentences of each
    paragraph, the rows of each table."""
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    document = Document(str(path))
    blocks: list[Block] = []
    section = ""
    paragraph_number = table_number = 0
    for child in document.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            paragraph = Paragraph(child, document)
            text = paragraph.text.strip()
            if not text:
                continue
            paragraph_number += 1
            style = paragraph.style.name if paragraph.style is not None else ""
            if style.startswith(("Heading", "Titre")):
                section = text
                continue
            for k, sentence in enumerate(sentences(text), start=1):
                values, unread = statistics(sentence)
                blocks.append(
                    Block(
                        _("§ {n}, phrase {k}").format(n=paragraph_number, k=k),
                        "sentence",
                        sentence,
                        section,
                        values=tuple(values),
                        unread=tuple(unread),
                        paragraph=paragraph_number,
                    )
                )
        elif tag == "tbl":
            table_number += 1
            blocks += _table_blocks(Table(child, document), table_number, section)
    return blocks
