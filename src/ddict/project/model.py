"""The project file: the dictionary being written, with the provenance of every field.

Field order in these models is the key order of the JSON file (CONCEPTION.md, § 5).
The file holds metadata and aggregates that went through the privacy gate, never
individual values.
"""

from __future__ import annotations

from typing import Annotated, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

SCHEMA_VERSION = "0.1.0"

Code = int | float | str
Origin = Literal["file", "computed", "ai", "human"]
Status = Literal["none", "proposed", "validated", "corrected", "rejected"]
# A documented source is mandatory for thresholds, theoretical ranges and instrument names
# (CONCEPTION.md, principle 4): an empty or blank source is refused.
SourceText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

T = TypeVar("T")


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class TrackedValue(Strict, Generic[T]):
    """A value with its origin and the decision taken about it.

    `proposed_value` keeps what the file or the model said when a person corrects it.
    """

    value: T | None = None
    origin: Origin
    status: Status = "none"
    proposed_value: T | None = None
    ai_run: str | None = None
    updated_at: str | None = None

    @model_validator(mode="after")
    def _consistent(self) -> TrackedValue:
        if (self.origin == "ai") != (self.ai_run is not None):
            raise ValueError("ai_run is required for, and only for, values proposed by AI")
        if self.status == "proposed" and self.origin != "ai":
            raise ValueError("only AI values can be 'proposed'")
        if self.origin == "ai" and self.status == "none":
            raise ValueError("an AI value needs a status")
        if self.status == "corrected" and self.proposed_value is None:
            raise ValueError("a corrected value keeps the value it replaces")
        return self


class SourcedText(Strict):
    value: NonEmptyText
    source: SourceText


class TheoreticalRange(Strict):
    min: float
    max: float
    source: SourceText

    @model_validator(mode="after")
    def _ordered(self) -> TheoreticalRange:
        if self.min >= self.max:
            raise ValueError("min must be below max")
        return self


class Threshold(Strict):
    value: float
    meaning: NonEmptyText
    source: SourceText


class ValueLabel(Strict):
    code: Code
    label: str


class MissingRange(Strict):
    low: Code
    high: Code


class FileMetadata(Strict):
    """What the data file says about the variable (origin: file)."""

    storage_type: Literal["numeric", "string"]
    storage_width: int | None = None
    display_format: str | None = None
    measure_level: Literal["nominal", "ordinal", "scale"] | None = None
    label: str | None = None
    value_labels: list[ValueLabel] = []
    declared_missing: list[MissingRange] = []


class ObservedCount(Strict):
    code: Code
    count: int | None  # None: fewer than the threshold (D-006, D-007)
    declared_missing: bool = False


class Profile(Strict):
    """Computed statistics, as let through by the privacy gate (origin: computed)."""

    inferred_type: str
    n_rows: int
    n_valid: int
    n_system_missing: int
    n_declared_missing: int
    n_distinct: int | None = None
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    sd: float | None = None
    median: float | None = None
    q1: float | None = None
    q3: float | None = None
    date_min: str | None = None
    date_max: str | None = None
    n_non_numeric: int | None = None
    observed_values: list[ObservedCount] | None = None
    n_rare_values_hidden: int = 0
    unlabeled_codes: list[Code] = []
    unused_labels: list[Code] = []
    suspect_missing_codes: list[Code] = []
    flags: list[str] = []
    duplicate_of: str | None = None
    # Within its probable scale: correlation with the sum of the other items.
    item_rest_r: float | None = None
    reverse_suspect: bool = False


class Privacy(Strict):
    privacy_class: TrackedValue[str]
    reasons: list[str] = []


class VariableEntry(Strict):
    name: str
    position: int
    file: FileMetadata
    profile: Profile
    privacy: Privacy
    label: TrackedValue[str]
    description: TrackedValue[str]
    issues: list[TrackedValue[str]] = []
    unit: TrackedValue[str]
    group_id: TrackedValue[str]
    # Human only, each with a documented source (principle 4).
    theoretical_range: TheoreticalRange | None = None
    thresholds: list[Threshold] = []
    references: list[NonEmptyText] = []
    notes: str | None = None
    # What in the AI proposals looks like an invention, e.g. "description:threshold".
    ai_signals: list[str] = []


class Group(Strict):
    group_id: str
    members: TrackedValue[list[str]]
    basis: list[str] = []
    descriptive_label: TrackedValue[str]
    ai_hypothesis: TrackedValue[str]
    # Human only, each with a documented source (principle 4).
    instrument_name: SourcedText | None = None
    reverse_items: list[str] = []
    scoring: SourcedText | None = None
    theoretical_range: TheoreticalRange | None = None
    thresholds: list[Threshold] = []
    n_complete_rows: int | None = None
    cronbach_alpha: float | None = None  # as observed, for information
    cronbach_alpha_reversed: float | None = None  # with the suspect items reversed


class AiRun(Strict):
    """One call to the model for one block. Never holds the content of the exchange."""

    run_id: str
    block: str
    endpoint: str
    model: str
    parameters: dict[str, float | int | str] = {}
    prompt_version: str
    message_sha256: str
    started_at: str
    attempts: int = 1
    outcome: Literal["succeeded", "invalid_response", "refused", "failed"]
    detail: str | None = None  # a reason code when the call did not succeed


class SourceInfo(Strict):
    """Identity of the data file: its name, never its path nor its content."""

    name: str
    format: Literal["sav", "csv"]
    sha256: str
    n_rows: int
    n_columns: int
    label: str | None = None
    encoding: str | None = None
    delimiter: str | None = None
    decimal: str | None = None


class Settings(Strict):
    min_cell_count: int = Field(default=5, ge=1)
    max_observed_values: int = Field(default=20, ge=1)
    language: str = "fr"


class Project(Strict):
    schema_version: str = SCHEMA_VERSION
    source: SourceInfo
    settings: Settings = Settings()
    variables: list[VariableEntry]
    groups: list[Group] = []
    ai_runs: list[AiRun] = []

    def variable(self, name: str) -> VariableEntry:
        for entry in self.variables:
            if entry.name == name:
                return entry
        raise KeyError(name)
