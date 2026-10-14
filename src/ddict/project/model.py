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
# "questionnaire": computed from the questionnaire under a strict rule, and like an AI value
# only a proposal until a person accepts it (value labels from the options, D-016).
Origin = Literal["file", "computed", "ai", "questionnaire", "human"]
PROPOSING_ORIGINS = ("ai", "questionnaire")
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
        if self.status == "proposed" and self.origin not in PROPOSING_ORIGINS:
            raise ValueError("only AI and questionnaire values can be 'proposed'")
        if self.origin in PROPOSING_ORIGINS and self.status == "none":
            raise ValueError("an AI or questionnaire value needs a status")
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


class MissingToken(Strict):
    """A missing-value token of a CSV file ("NA", ...) and the cells holding it (D-010)."""

    token: str
    count: int


class FileMetadata(Strict):
    """What the data file says about the variable (origin: file)."""

    storage_type: Literal["numeric", "string"]
    storage_width: int | None = None
    display_format: str | None = None
    measure_level: Literal["nominal", "ordinal", "scale"] | None = None
    label: str | None = None
    value_labels: list[ValueLabel] = []
    declared_missing: list[MissingRange] = []
    missing_tokens: list[MissingToken] = []


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
    # The question it comes from (D-013): "Q8", "Q7.r3", "Q10.o2", or "none"; the text is
    # looked up in the questionnaire, never stored here.
    question: TrackedValue[str] = TrackedValue[str](origin="human")
    # Value labels proposed from the options of the linked question (D-016), when the file
    # has none: "questionnaire" origin, to be accepted by a person.
    value_labels: TrackedValue[list[ValueLabel]] = TrackedValue[list[ValueLabel]](origin="human")
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


class QuestionOption(Strict):
    option_id: str  # "Q10.o3"
    text: str


class GridRow(Strict):
    row_id: str  # "Q7.r3"
    number: int | None = None  # as printed ("3."), when printed
    text: str


class Question(Strict):
    """A question as read in the questionnaire (D-012): its words, never rewritten."""

    question_id: str  # "Q7", in reading order
    page: int | None = None  # None for a text file without page breaks
    text: str
    kind: Literal["open", "single", "checkbox", "grid"]
    options: list[QuestionOption] = []  # for a grid: its columns
    rows: list[GridRow] = []
    to_check: list[str] = []  # codes: "grid_header_unclear", "grid_without_header"


class QuestionnaireText(Strict):
    """A paragraph that is not a question: instructions, definitions, consent page."""

    page: int | None = None
    text: str


class Questionnaire(Strict):
    """The study's questionnaire, a documented source given by the team (D-012)."""

    file_name: str
    sha256: str
    format: Literal["pdf", "txt"]
    n_pages: int | None = None
    questions: list[Question] = []
    texts: list[QuestionnaireText] = []


class GlossaryEntry(Strict):
    """An acronym and its meaning (D-015): found in the questionnaire, or written by a person.

    There is no "ai" origin: the model never defines an acronym. An entry found in the
    questionnaire is proposed until a person validates, corrects or rejects it.
    """

    term: NonEmptyText  # as written: "OCF"
    meaning: NonEmptyText
    origin: Literal["questionnaire", "human"]
    status: Literal["none", "proposed", "validated", "corrected", "rejected"] = "none"
    source: str | None = None  # where it was found: "questionnaire.pdf, p. 8"
    proposed_meaning: str | None = None  # the questionnaire's, when a person corrected it
    updated_at: str | None = None

    @model_validator(mode="after")
    def _consistent(self) -> GlossaryEntry:
        if (self.origin == "human") != (self.status == "none"):
            raise ValueError("only entries found in the questionnaire wait for a decision")
        if (self.status == "corrected") != (self.proposed_meaning is not None):
            raise ValueError("a corrected entry keeps the meaning it replaces, and only it")
        return self


class Project(Strict):
    schema_version: str = SCHEMA_VERSION
    source: SourceInfo
    settings: Settings = Settings()
    variables: list[VariableEntry]
    groups: list[Group] = []
    ai_runs: list[AiRun] = []
    questionnaire: Questionnaire | None = None
    glossary: list[GlossaryEntry] = []

    def variable(self, name: str) -> VariableEntry:
        for entry in self.variables:
            if entry.name == name:
                return entry
        raise KeyError(name)
