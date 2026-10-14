"""Read CSV files, guessing the encoding, the delimiter and the decimal mark.

The usual sources are Excel in French (Windows-1252 or UTF-8 with a byte order mark, ";"
delimiter, decimal comma), survey platforms and statistics software (UTF-8, ","). A column
becomes numeric only when every non-empty value is a number; anything else stays text and
profiling decides what it is (dates, mixed types, ...).

Cells holding a usual missing-value token ("NA" from R, "#N/A" from Excel, ...) are read
as empty, and counted per column so that the codebook says so (D-010).
"""

from __future__ import annotations

import codecs
import csv
import io
import re
from pathlib import Path

import numpy as np
import pandas as pd

from ddict.io.model import LoadedData, ReadError, SourceFile, VariableMetadata
from ddict.io.sav import file_sha256

DELIMITERS = (";", ",", "\t", "|")
# Excel in French saves "CSV (séparateur : point-virgule)" in Windows-1252.
FALLBACK_ENCODING = "cp1252"

_NUMBER = {
    ".": re.compile(r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?"),
    ",": re.compile(r"[+-]?(\d+(,\d*)?|,\d+)([eE][+-]?\d+)?"),
}
_LEADING_ZERO = re.compile(r"[+-]?0\d")
# Written by R ("NA"), pandas ("NaN"), Excel ("#N/A") and SQL exports ("NULL"); exact match.
MISSING_TOKENS = ("NA", "N/A", "NaN", "#N/A", "NULL")


def decode(raw: bytes, encoding: str | None = None) -> tuple[str, str]:
    """Return the text and the encoding used: forced, UTF-8 (with or without BOM), or cp1252."""
    if encoding is not None:
        return raw.decode(encoding), encoding
    if raw.startswith(codecs.BOM_UTF8):
        return raw.decode("utf-8-sig"), "utf-8-sig"
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return raw.decode(FALLBACK_ENCODING), FALLBACK_ENCODING


def _parse(text: str, delimiter: str) -> list[list[str]]:
    rows = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)
    return [row for row in rows if row]


def detect_delimiter(text: str) -> str:
    """Pick the delimiter that splits every row into the same number (> 1) of fields.

    When several do, the one giving the most columns wins; a row count check rather than
    csv.Sniffer, which is easily fooled by quoted line breaks and decimal commas.
    """
    best, best_columns = None, 1
    for delimiter in DELIMITERS:
        try:
            rows = _parse(text, delimiter)
        except csv.Error:
            continue
        if not rows:
            continue
        width = len(rows[0])
        if width > best_columns and all(len(row) == width for row in rows):
            best, best_columns = delimiter, width
    if best is None:
        raise ReadError("Cannot find the delimiter: rows do not have the same number of fields")
    return best


def _is_number(value: str, decimal: str) -> bool:
    return bool(_NUMBER[decimal].fullmatch(value.strip()))


def detect_decimal(columns: list[list[str]], delimiter: str) -> str:
    """A decimal comma is possible only when "," is not the delimiter; vote on the values."""
    if delimiter == ",":
        return "."
    comma = dot = 0
    for values in columns:
        for value in values:
            text = value.strip()
            if "," in text and _is_number(text, ","):
                comma += 1
            elif "." in text and _is_number(text, "."):
                dot += 1
    return "," if comma > dot else "."


def _blank_tokens(values: list[str]) -> tuple[list[str], dict[str, int]]:
    """Replace missing-value tokens with empty cells; count them by token."""
    counts: dict[str, int] = {}
    kept = []
    for value in values:
        token = value.strip()
        if token in MISSING_TOKENS:
            counts[token] = counts.get(token, 0) + 1
            kept.append("")
        else:
            kept.append(value)
    return kept, {token: counts[token] for token in MISSING_TOKENS if token in counts}


def _to_column(values: list[str], decimal: str) -> pd.Series:
    """Numeric if every non-empty value is a number without a meaningful leading zero.

    An entirely empty column is numeric too: all its cells are then missing values.
    """
    filled = [value.strip() for value in values if value.strip()]
    numeric = all(_is_number(value, decimal) and not _LEADING_ZERO.match(value) for value in filled)
    if not numeric:
        return pd.Series(values, dtype=object)
    return pd.Series(
        [float(v.strip().replace(decimal, ".")) if v.strip() else np.nan for v in values],
        dtype="float64",
    )


def read_csv(
    path: Path | str,
    *,
    encoding: str | None = None,
    delimiter: str | None = None,
    decimal: str | None = None,
) -> LoadedData:
    """Read a CSV file whose first row holds the variable names.

    Each option can be forced when the guess is wrong. Empty cells of numeric columns
    become missing values; text columns keep the empty string, as in a .sav file.
    """
    path = Path(path)
    try:
        raw = path.read_bytes()
        text, encoding = decode(raw, encoding)
    except (OSError, UnicodeError, LookupError) as error:
        raise ReadError(f"Cannot read {path.name} as a CSV file: {error}") from error

    try:
        delimiter = delimiter or detect_delimiter(text)
        rows = _parse(text, delimiter)
    except (ReadError, csv.Error) as error:
        raise ReadError(f"Cannot read {path.name} as a CSV file: {error}") from error
    if len(rows) < 1:
        raise ReadError(f"{path.name} is empty")

    header, records = rows[0], rows[1:]
    for line, record in enumerate(records, start=2):
        if len(record) != len(header):
            raise ReadError(
                f"{path.name}, row {line}: {len(record)} fields instead of {len(header)}"
            )
    names = [name.strip() or f"colonne_{position}" for position, name in enumerate(header, 1)]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ReadError(f"{path.name}: duplicate column names: {', '.join(duplicates)}")

    blanked = [_blank_tokens([record[i] for record in records]) for i in range(len(names))]
    columns = [values for values, _counts in blanked]
    decimal = decimal or detect_decimal(columns, delimiter)
    table = pd.DataFrame(
        {name: _to_column(values, decimal) for name, values in zip(names, columns, strict=True)}
    )

    variables = tuple(
        VariableMetadata(
            name=name,
            position=position,
            storage_type="numeric" if table[name].dtype == "float64" else "string",
            missing_tokens=counts,
        )
        for position, (name, (_values, counts)) in enumerate(zip(names, blanked, strict=True), 1)
    )
    source = SourceFile(
        name=path.name,
        format="csv",
        sha256=file_sha256(path),
        n_rows=len(table),
        n_columns=len(names),
        encoding=encoding,
        delimiter=delimiter,
        decimal=decimal,
    )
    return LoadedData(source=source, variables=variables, table=table)
