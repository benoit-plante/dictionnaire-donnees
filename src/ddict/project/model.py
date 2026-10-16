"""The project file: the dictionary being written, with the provenance of every field.

Field order in these models is the key order of the JSON file (CONCEPTION.md, § 5).
The file holds metadata and aggregates that went through the privacy gate, never
individual values.
"""

from __future__ import annotations

from typing import Annotated, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

# 0.2.0 (v0.7, D-048): new fields only, all with a default; a 0.1.0 file reads as it is.
# 0.3.0 (v0.8, D-061): the measure level a person decides; older files are converted on
# opening (the rules propose their levels), and a 0.3.0 file no longer opens in v0.7.
# 0.4.0 (v0.12, D-093): the exclusion rules, with a default; a 0.3.0 file reads as it is.
SCHEMA_VERSION = "0.4.0"

Code = int | float | str
# "questionnaire": computed from the questionnaire under a strict rule, and like an AI value
# only a proposal until a person accepts it (value labels from the options, D-016).
# "rule" and "reference" (v0.7, D-048): a new name given by the naming rules, or taken from
# an earlier wave; proposals too, never a name without a person. Since v0.8 (D-067), "rule"
# is any deterministic rule of the tool that proposes (names, measure levels).
Origin = Literal["file", "computed", "ai", "questionnaire", "rule", "reference", "human"]
PROPOSING_ORIGINS = ("ai", "questionnaire", "rule", "reference")
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
            raise ValueError("only proposing origins (AI, questionnaire, rule, reference)")
        if self.origin in PROPOSING_ORIGINS and self.status == "none":
            raise ValueError("a proposed value needs a status")
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


class Scoring(Strict):
    """How the score of a group is computed (v0.8, D-060): written by a person, with its
    source, never proposed by the model. Structured (items, sum or mean, the scale's minimum
    and maximum for reversing, the score's name), or a note only, for a scoring that does not
    fit. The reversed items are the group's confirmed ones (`Group.reverse_items`); the
    range of the score is computed, never typed."""

    items: list[str] = []  # original names; empty: a note only
    aggregation: Literal["sum", "mean"] | None = None
    reverse_rule: Literal["max_plus_min_minus_x"] = "max_plus_min_minus_x"
    scale_min: float | None = None
    scale_max: float | None = None
    min_items_answered: int | None = Field(default=None, ge=1)
    # A sum with items missing (D-068): the mean of the items answered times their number
    # ("prorate", the range stays), or the sum of the items answered.
    missing_rule: Literal["prorate", "sum_answered"] = "prorate"
    score_name: str | None = None
    source: SourceText
    note: str | None = None

    @model_validator(mode="after")
    def _complete(self) -> Scoring:
        if not self.items:
            if not (self.note or "").strip():
                raise ValueError("a scoring without items needs a note")
            return self
        if self.aggregation is None or not self.score_name:
            raise ValueError("a structured scoring needs its aggregation and score name")
        if self.scale_min is None or self.scale_max is None or self.scale_min >= self.scale_max:
            raise ValueError("the scale's minimum must be below its maximum")
        if self.min_items_answered is not None and self.min_items_answered > len(self.items):
            raise ValueError("more items required than the score has")
        return self


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


class SentinelDecision(Strict):
    """A suspect missing code (999, -9) as the team decided it (D-028): a missing code, or a
    real value. Never proposed by the model; the profile is not computed again."""

    code: Code
    missing: bool
    updated_at: str | None = None


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
    # The exact sum of the items of this group, in every row where all are given (v0.6,
    # D-039): a computed score, asked by no question. Only the fact is kept.
    sum_of_group: str | None = None


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
    # Its new name (v0.7, D-048); `name` stays the key by which the database is read.
    new_name: TrackedValue[str] = TrackedValue[str](origin="human")
    # Value labels proposed from the options of the linked question (D-016), when the file
    # has none: "questionnaire" origin, to be accepted by a person.
    value_labels: TrackedValue[list[ValueLabel]] = TrackedValue[list[ValueLabel]](origin="human")
    # The measure level decided by the team (v0.8, D-063): empty while the file's stands; a
    # "rule" proposal where the file has none or a doubtful one; "nominal", "ordinal" or
    # "scale". The level in force is `ddict.project.measure.level`.
    measure_level: TrackedValue[str] = TrackedValue[str](origin="human")
    label: TrackedValue[str]
    description: TrackedValue[str]
    issues: list[TrackedValue[str]] = []
    unit: TrackedValue[str]
    group_id: TrackedValue[str]
    # The team's decisions on the suspect missing codes (D-028).
    sentinel_decisions: list[SentinelDecision] = []
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
    # v0.7 (D-044): a probable scale, or the options of a "tick all that apply" question,
    # whose "other" text is attached outside the members.
    kind: Literal["scale", "multiple_response"] = "scale"
    attached: list[str] = []
    # The prefix of its items' names ("k6"): given by a person, or taken from an earlier wave;
    # never proposed by the model, an instrument's acronym being a name (principle 4).
    name_prefix: TrackedValue[str] = TrackedValue[str](origin="human")
    descriptive_label: TrackedValue[str]
    ai_hypothesis: TrackedValue[str]
    # Human only, each with a documented source (principle 4).
    instrument_name: SourcedText | None = None
    reverse_items: list[str] = []
    scoring: Scoring | None = None  # v0.8 (D-060); was a sourced text (now its note)
    theoretical_range: TheoreticalRange | None = None
    thresholds: list[Threshold] = []
    # D-014: the team's choice not to reproduce the items of a copyrighted instrument; the
    # exports then give the question's reference, not its words.
    omit_question_text: bool = False
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
    format: Literal["sav", "csv", "dta", "sas7bdat", "xlsx"]
    sha256: str
    n_rows: int
    n_columns: int
    label: str | None = None
    encoding: str | None = None
    delimiter: str | None = None
    decimal: str | None = None
    # The survey platform whose export this is (v0.7, D-044): "surveymonkey", or None.
    platform: str | None = None


class DesignVariables(Strict):
    """The variables of the study's design, by their original names (v0.8, D-064)."""

    cluster_id: str | None = None  # the unit rows belong to (family, class, participant)
    time: str | None = None  # the time of each row, in a long format
    wave: str | None = None
    cluster: str | None = None  # a sampling cluster
    weight: str | None = None


class Dataset(Strict):
    """What a row of the database is, and how the study is organised (v0.8, D-064): written
    by a person; only the structure may be proposed by a rule."""

    unit_of_observation: (
        Literal["participant", "repeated_observation", "dyad", "family", "other"] | None
    ) = None
    unit_other: str | None = None
    # "cross_sectional", "one_wave_per_file", "wide", "long".
    structure: TrackedValue[str] = TrackedValue[str](origin="human")
    wave: str | None = None  # the wave of this file, for "one_wave_per_file"
    time_suffixes: list[str] = []  # "_t1", "_t2"..., for "wide"
    design: DesignVariables = DesignVariables()
    description: str | None = None


class NamingSettings(Strict):
    """How new names are written (v0.7): at most `max_length` characters (Stata's limit),
    with the mark of a wave ("t2") as a suffix (`k6_1_t2`, D-049) or a prefix (`t2_k6_1`)."""

    max_length: int = Field(default=32, ge=8, le=64)
    wave: str | None = None
    position: Literal["suffix", "prefix"] = "suffix"


class Settings(Strict):
    min_cell_count: int = Field(default=5, ge=1)
    max_observed_values: int = Field(default=20, ge=1)
    # The language of the study: its questionnaire and labels (v0.5, D-032).
    language: Literal["fr", "en"] = "fr"
    naming: NamingSettings = NamingSettings()


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
    format: Literal["pdf", "txt", "xlsx"]  # xlsx: a platform export's header (v0.7, D-045)
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


class QuestionStem(Strict):
    """The stem of the names of a question's variables (`taches` for `taches_1`...), one per
    question (v0.7): `key` is the platform's question ("q0005") or the questionnaire's
    ("Q5")."""

    key: str
    stem: TrackedValue[str]
    # What in a stem proposed by the model may be an invention: "stem:acronym" (D-051).
    ai_signals: list[str] = []


# --- Exclusion rules (v0.12, D-093, D-094). ---

Operator = Literal["eq", "ne", "lt", "le", "gt", "ge", "in", "missing"]


# A rule decided by the team, never a list of people: `id` (E1, E2...) is never given again
# after a removal, the rank is the order of the list. Each kind declares `id` and `kind`
# first, its own fields, then `reason` and `source`: the order of the JSON file.


class ConditionRule(Strict):
    """A condition on a variable (its original name) or on the score of a group's scoring;
    a missing value never meets it, except with `missing`."""

    id: str
    kind: Literal["condition"] = "condition"
    variable: str | None = None
    score: str | None = None
    operator: Operator
    value: Code | list[Code] | None = None
    reason: NonEmptyText
    source: str | None = None

    @model_validator(mode="after")
    def _complete(self) -> ConditionRule:
        if (self.variable is None) == (self.score is None):
            raise ValueError("a condition names a variable or a score, not both")
        if self.operator == "missing" and self.value is not None:
            raise ValueError("'missing' takes no value")
        if self.operator == "in" and not (isinstance(self.value, list) and self.value):
            raise ValueError("'in' takes a list of values")
        if self.operator not in ("missing", "in") and (
            self.value is None or isinstance(self.value, list)
        ):
            raise ValueError("this operator takes one value")
        return self


class CompletenessRule(Strict):
    """Fewer than `min_answered` items of a group answered."""

    id: str
    kind: Literal["completeness"] = "completeness"
    group: str
    min_answered: int = Field(ge=1)
    reason: NonEmptyText
    source: str | None = None


class DurationRule(Strict):
    """An administration shorter than `min_seconds`, between two date variables; the
    threshold is the team's choice and needs its source (principle 4)."""

    id: str
    kind: Literal["duration"] = "duration"
    start: str
    end: str
    min_seconds: float = Field(gt=0)
    reason: NonEmptyText
    source: SourceText


class StraightliningRule(Strict):
    """Every item of a grid answered, all with the same value."""

    id: str
    kind: Literal["straightlining"] = "straightlining"
    group: str
    reason: NonEmptyText
    source: str | None = None


class DuplicateRule(Strict):
    """A later answer repeating an earlier one on these variables (the first is kept); an
    answer with one of them missing is never a duplicate."""

    id: str
    kind: Literal["duplicate"] = "duplicate"
    variables: list[str] = Field(min_length=1)
    keep: Literal["first"] = "first"
    reason: NonEmptyText
    source: str | None = None


ExclusionRule = Annotated[
    ConditionRule | CompletenessRule | DurationRule | StraightliningRule | DuplicateRule,
    Field(discriminator="kind"),
]


class Exclusions(Strict):
    next_id: int = 1
    rules: list[ExclusionRule] = []


class Project(Strict):
    schema_version: str = SCHEMA_VERSION
    source: SourceInfo
    settings: Settings = Settings()
    variables: list[VariableEntry]
    groups: list[Group] = []
    ai_runs: list[AiRun] = []
    questionnaire: Questionnaire | None = None
    glossary: list[GlossaryEntry] = []
    stems: list[QuestionStem] = []
    dataset: Dataset = Dataset()  # v0.8 (D-064)
    exclusions: Exclusions = Exclusions()  # v0.12 (D-093)

    def variable(self, name: str) -> VariableEntry:
        for entry in self.variables:
            if entry.name == name:
                return entry
        raise KeyError(name)
