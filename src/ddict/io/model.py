"""What a reader returns: the table, and the metadata found in the file itself."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

# A code as written in a file: integral numbers are kept as int (1, not 1.0).
Code = int | float | str

StorageType = Literal["numeric", "string"]
MeasureLevel = Literal["nominal", "ordinal", "scale"]


class ReadError(Exception):
    """The file cannot be read as a database."""


@dataclass(frozen=True)
class MissingRange:
    """Values declared missing in the file: a single code when low == high."""

    low: Code
    high: Code


@dataclass(frozen=True)
class VariableMetadata:
    """Everything the file says about one variable (origin: file)."""

    name: str
    position: int  # 1-based rank in the file
    storage_type: StorageType
    storage_width: int | None = None
    display_format: str | None = None  # SPSS format, e.g. "F8.2", "A50", "DATE11"
    measure_level: MeasureLevel | None = None
    label: str | None = None
    value_labels: dict[Code, str] = field(default_factory=dict)
    declared_missing: tuple[MissingRange, ...] = ()
    # CSV only: cells written as a missing-value token ("NA", ...), read as empty (D-010).
    missing_tokens: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceFile:
    """Identity of the file that was read; never its content."""

    name: str
    format: Literal["sav", "csv"]
    sha256: str
    n_rows: int
    n_columns: int
    label: str | None = None
    encoding: str | None = None
    delimiter: str | None = None  # CSV only
    decimal: str | None = None  # CSV only


@dataclass(frozen=True)
class LoadedData:
    """A database as read: the table stays in memory and never goes past profiling."""

    source: SourceFile
    variables: tuple[VariableMetadata, ...]
    table: pd.DataFrame

    def variable(self, name: str) -> VariableMetadata:
        for variable in self.variables:
            if variable.name == name:
                return variable
        raise KeyError(name)
