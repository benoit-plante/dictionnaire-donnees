"""Read SPSS system files (.sav, .zsav) with their labels and declared missing values."""

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
    path = Path(path)
    try:
        table, meta = pyreadstat.read_sav(path, user_missing=True, encoding=encoding)
    except (
        pyreadstat.ReadstatError,
        pyreadstat.PyreadstatError,
        OSError,
        UnicodeError,
    ) as error:
        raise ReadError(f"Cannot read {path.name} as an SPSS file: {error}") from error

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
        format="sav",
        sha256=file_sha256(path),
        n_rows=len(table),
        n_columns=len(table.columns),
        label=meta.file_label or None,
        encoding=meta.file_encoding or None,
    )
    return LoadedData(source=source, variables=tuple(variables), table=table)
