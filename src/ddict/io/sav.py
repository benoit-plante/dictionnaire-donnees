"""Read SPSS (.sav, .zsav), Stata (.dta) and SAS (.sas7bdat) files with pyreadstat.

SPSS files bring labels, value labels, measure levels and declared missing values. Stata
files bring labels and value labels; their extended missing values (.a to .z) are read as
empty cells. SAS files bring variable labels only: value labels live in a separate format
catalog, which is not read.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyreadstat

from ddict.io.model import Code, LoadedData, MissingRange, ReadError, SourceFile, VariableMetadata

_MEASURE_LEVELS = {"nominal", "ordinal", "scale"}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_code(value: object) -> Code:
    """Return a code as the file means it: 1.0 becomes 1, strings stay strings."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, int | float | str):
        return value
    raise TypeError(f"Unexpected code type: {type(value).__name__}")


def _sorted_labels(labels: dict) -> dict[Code, str]:
    normalized = {normalize_code(code): text for code, text in labels.items()}
    return dict(sorted(normalized.items(), key=lambda item: (isinstance(item[0], str), item[0])))


def read_sav(path: Path | str, *, encoding: str | None = None) -> LoadedData:
    """Read a .sav file; declared missing values are kept as values in the table.

    Keeping them (instead of turning them into empty cells) lets profiling count declared
    missing values apart from empty cells. `encoding` overrides the encoding written in the
    file, for old files that declare it wrongly.
    """
    return _read(path, "sav", "SPSS", pyreadstat.read_sav, user_missing=True, encoding=encoding)


def read_dta(path: Path | str, *, encoding: str | None = None) -> LoadedData:
    """Read a Stata .dta file (v0.2)."""
    return _read(path, "dta", "Stata", pyreadstat.read_dta, encoding=encoding)


def read_sas7bdat(path: Path | str, *, encoding: str | None = None) -> LoadedData:
    """Read a SAS .sas7bdat file (v0.2)."""
    return _read(path, "sas7bdat", "SAS", pyreadstat.read_sas7bdat, encoding=encoding)


def _read(path: Path | str, file_format: str, program: str, reader, **options) -> LoadedData:
    path = Path(path)
    try:
        table, meta = reader(path, **options)
    except (
        pyreadstat.ReadstatError,
        pyreadstat.PyreadstatError,
        OSError,
        UnicodeError,
    ) as error:
        raise ReadError(f"Cannot read {path.name} as a {program} file: {error}") from error

    labels = dict(zip(meta.column_names, meta.column_labels, strict=True))
    variables = []
    for position, name in enumerate(meta.column_names, start=1):
        measure = meta.variable_measure.get(name)
        missing = tuple(
            MissingRange(normalize_code(item["lo"]), normalize_code(item["hi"]))
            for item in meta.missing_ranges.get(name, [])
        )
        variables.append(
            VariableMetadata(
                name=name,
                position=position,
                storage_type="string"
                if meta.readstat_variable_types[name] == "string"
                else "numeric",
                storage_width=meta.variable_storage_width.get(name),
                display_format=meta.original_variable_types.get(name) or None,
                measure_level=measure if measure in _MEASURE_LEVELS else None,
                label=labels[name] or None,
                value_labels=_sorted_labels(meta.variable_value_labels.get(name, {})),
                declared_missing=missing,
            )
        )

    source = SourceFile(
        name=path.name,
        format=file_format,
        sha256=file_sha256(path),
        n_rows=len(table),
        n_columns=len(table.columns),
        label=meta.file_label or None,
        encoding=meta.file_encoding or None,
    )
    return LoadedData(source=source, variables=tuple(variables), table=table)
