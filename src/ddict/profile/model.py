"""The deterministic profile of a variable (origin: computed)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ddict.io.model import Code

InferredType = Literal[
    "empty",
    "boolean",
    "integer",
    "decimal",
    "date",
    "datetime",
    "text",
    "mixed",
]
Flag = Literal["all_missing", "constant", "checkbox", "mixed_types", "duplicate"]


@dataclass(frozen=True)
class ObservedValue:
    """One distinct value and how many rows hold it."""

    code: Code
    count: int
    declared_missing: bool = False


@dataclass(frozen=True)
class VariableProfile:
    """Exact statistics of one variable.

    The profile can hold observed values of any variable, free text included: it stays in
    memory. What may leave it (towards the model, the project file or an export) is decided
    by the privacy module, which also masks small counts.
    """

    name: str
    inferred_type: InferredType
    n_rows: int
    n_valid: int
    n_system_missing: int  # empty cells
    n_declared_missing: int  # values declared missing in the file
    n_distinct: int  # distinct valid values
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    sd: float | None = None
    median: float | None = None
    q1: float | None = None
    q3: float | None = None
    date_min: str | None = None  # ISO 8601
    date_max: str | None = None
    length_min: int | None = None  # text only: lengths, never content
    length_max: int | None = None
    n_non_numeric: int | None = None  # mixed only: values that are not numbers
    # Distinct values (declared missing included) when there are few enough; else None.
    observed_values: tuple[ObservedValue, ...] | None = None
    unlabeled_codes: tuple[Code, ...] = ()
    unused_labels: tuple[Code, ...] = ()
    suspect_missing_codes: tuple[Code, ...] = ()
    flags: tuple[Flag, ...] = ()
    duplicate_of: str | None = None

    @property
    def n_missing(self) -> int:
        return self.n_system_missing + self.n_declared_missing

    @property
    def pct_missing(self) -> float:
        return 100 * self.n_missing / self.n_rows if self.n_rows else 0.0
