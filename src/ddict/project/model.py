"""The project file: the dictionary being written, with the provenance of every field.

Field order in these models is the key order of the JSON file (CONCEPTION.md, § 5).
The file holds metadata and aggregates that went through the privacy gate, never
individual values.
"""

from __future__ import annotations

from typing import Annotated, Generic, Literal, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    PrivateAttr,
    StringConstraints,
    model_serializer,
    model_validator,
)

# 0.2.0 (v0.7, D-048): new fields only, all with a default; a 0.1.0 file reads as it is.
# 0.3.0 (v0.8, D-061): the measure level a person decides; older files are converted on
# opening (the rules propose their levels), and a 0.3.0 file no longer opens in v0.7.
# 0.4.0 (v0.12, D-093): the exclusion rules, with a default; a 0.3.0 file reads as it is.
# 0.5.0 (v0.13, D-101): the analysis plan, with a default; a 0.4.0 file reads as it is.
# 0.8.0 (v0.18, D-138): whether the project may send its metadata to the AI, not by
# default; a 0.7.0 file reads as it is, not allowed.
# 0.9.0 (v0.20, D-145, D-146): a project may have no database yet (no `source`; planned
# variables without a profile) and a questionnaire designed in the tool (`design`, new
# question fields), all with a default; a 0.8.0 file reads as it is.
# 0.10.0 (v0.20.2, D-158): a variable set aside from the codebook by the team, with its
# reason, not by default; a 0.9.0 file reads as it is.
# 0.11.0 (v0.20.2, D-161): the project's title, given by a person, none by default; a
# 0.10.0 file reads as it is, without one.
# 0.12.0 (v0.21, D-165 to D-172): the conditions of the questions and sections, their random
# order, the attention checks, a variable's condition, the codes of the not applicable and
# of the missing, the "attention" exclusion rule; all with a default, a 0.11.0 file reads as
# it is.
SCHEMA_VERSION = "0.12.0"

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


# The types a designed questionnaire plans for a variable: those of `Profile.inferred_type`
# that a question can give (v0.20, D-145).
PlannedType = Literal["boolean", "integer", "decimal", "date", "datetime", "text"]


class Planned(Strict):
    """A variable the designed questionnaire plans, before the database exists (v0.20,
    D-145): never "empty", since nothing was observed."""

    type: PlannedType


class SetAside(Strict):
    """The team's decision to leave a variable out of the codebook (v0.20.2, D-158): a
    person's only, with its reason; the variable stays in the project and in the database."""

    reason: NonEmptyText
    date: str


# --- Skip logic (v0.21, D-165): when a question is asked. ---

# A term's target is a question ("Q3"), a grid's statement ("Q7.r2") or a checkbox's option
# ("Q10.o2"); in a variable's condition (D-168), a variable by its original name.
TermOperator = Literal["eq", "ne", "in", "not_in", "lt", "le", "gt", "ge", "checked", "answered"]
ONE_VALUE = ("eq", "ne", "lt", "le", "gt", "ge")
NO_VALUE = ("checked", "answered")


class Term(Strict):
    """A target, an operator its nature admits, a value chosen among its answers (or a
    number). A term on an empty answer, or on a question not asked, is false."""

    target: NonEmptyText
    operator: TermOperator
    value: Code | list[Code] | None = None

    @model_validator(mode="after")
    def _values(self) -> Term:
        if self.operator in NO_VALUE and self.value is not None:
            raise ValueError(f"'{self.operator}' takes no value")
        if self.operator in ("in", "not_in") and not (isinstance(self.value, list) and self.value):
            raise ValueError(f"'{self.operator}' takes a list of values")
        if self.operator in ONE_VALUE and (self.value is None or isinstance(self.value, list)):
            raise ValueError(f"'{self.operator}' takes one value")
        return self


class Condition(Strict):
    """Terms joined all by "and" or all by "or"; a section's and a question's are joined by
    "and" (the effective condition)."""

    combine: Literal["all", "any"] = "all"
    terms: list[Term] = Field(min_length=1, max_length=10)


class VariableEntry(Strict):
    name: str
    position: int
    # For a planned variable: what the questionnaire plans that the file will say.
    file: FileMetadata
    # None for a variable planned by a designed questionnaire, before the database arrives.
    profile: Profile | None = None
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
    # What the designed questionnaire planned (v0.20, D-145), kept once the database is there.
    planned: Planned | None = None
    # Left out of the codebook by the team (v0.20.2, D-158); `ddict.project.aside`.
    set_aside: SetAside | None = None
    # When it is asked (v0.21, D-168), on variables by their original names: typed by a
    # person ("human"), computed from the designed questionnaire ("computed"), or read in a
    # LimeSurvey file ("questionnaire", proposed until a person accepts it).
    asked_if: TrackedValue[Condition] | None = None

    @model_validator(mode="after")
    def _known(self) -> VariableEntry:
        if self.profile is None and self.planned is None:
            raise ValueError("a variable is profiled from the database, or planned")
        return self

    @property
    def data_type(self) -> str:
        """The type of the column: computed from the database, else planned."""
        if self.profile is not None:
            return self.profile.inferred_type
        assert self.planned is not None
        return self.planned.type

    @property
    def suspect_codes(self) -> list[Code]:
        """The probable undeclared missing codes found in the data; none for a planned
        variable."""
        return [] if self.profile is None else self.profile.suspect_missing_codes


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
    # v0.20 (D-146): the question of a designed questionnaire whose items it holds.
    question: str | None = None


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


class AiPermission(Strict):
    """Whether the metadata of this project may be sent to the AI (v0.18, D-138): not by
    default. A decision of the team, kept in the project so that colleagues see it, with
    the day it was given; never a person's name. Previews are always allowed."""

    allowed: bool = False
    since: str | None = None  # "2026-10-19"


class BlankCodes(Strict):
    """The codes the preparation scripts write in an empty cell (v0.21, D-167): one for a
    question not asked, one for a question asked and not answered. Chosen by the team, none
    by default; never written in the documented copy."""

    not_applicable: Code | None = None
    missing: Code | None = None

    @model_validator(mode="after")
    def _distinct(self) -> BlankCodes:
        if self.not_applicable is not None and self.not_applicable == self.missing:
            raise ValueError("the not applicable and the missing need two codes")
        return self


class Settings(Strict):
    min_cell_count: int = Field(default=5, ge=1)
    max_observed_values: int = Field(default=20, ge=1)
    # The language of the study: its questionnaire and labels (v0.5, D-032).
    language: Literal["fr", "en"] = "fr"
    naming: NamingSettings = NamingSettings()
    ai: AiPermission = AiPermission()
    blank_codes: BlankCodes = BlankCodes()  # v0.21 (D-167)


class Provenance(Strict):
    """Where a text of a designed questionnaire comes from (v0.20, D-146): typed by the team,
    taken from a source, or written by the AI (v0.21)."""

    kind: Literal["team", "source", "ai"]
    # A source as the team writes it ("Manuel, p. 4"); a deposited source in v0.21.
    source: str | None = None
    page: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _sourced(self) -> Provenance:
        if self.kind == "source" and not (self.source or "").strip():
            raise ValueError("a text taken from a source names it")
        if self.kind != "source" and (self.source is not None or self.page is not None):
            raise ValueError("only a text taken from a source has one")
        return self


class QuestionOption(Strict):
    option_id: str  # "Q10.o3"
    text: str
    # v0.20 (D-146), in a designed or LimeSurvey questionnaire: the answer code, decided
    # before the collection; whether it is the "other" option.
    code: str | None = None
    other: bool = False
    provenance: Provenance | None = None


class GridRow(Strict):
    row_id: str  # "Q7.r3"
    number: int | None = None  # as printed ("3."), when printed
    text: str
    code: str | None = None  # the subquestion's code (v0.20)
    provenance: Provenance | None = None
    # v0.21 (D-170): an attention check, with the codes of its right answers.
    attention: list[str] | None = Field(default=None, min_length=1)


# "display": a text shown to the participant, with no answer and no variable; only in a
# designed or LimeSurvey questionnaire (v0.20, D-146).
QuestionKind = Literal["open", "single", "checkbox", "grid", "display"]


class Question(Strict):
    """A question as read in the questionnaire (D-012): its words, never rewritten; or as
    designed in the tool (v0.20, D-146), where an id is never given again."""

    question_id: str  # "Q7", in reading order (designed: in order of creation)
    page: int | None = None  # None for a text file without page breaks
    text: str
    kind: QuestionKind
    options: list[QuestionOption] = []  # for a grid: its columns
    rows: list[GridRow] = []
    to_check: list[str] = []  # codes: "grid_header_unclear", "grid_without_header"
    # v0.20 (D-146), in a designed or LimeSurvey questionnaire.
    code: str | None = None  # as read in a platform's file (D-156); designed: from its stem
    section: str | None = None  # "S2"
    instruction: str | None = None
    required: bool = False
    answer: Literal["short", "long", "number", "date"] | None = None  # an open question's
    layout: Literal["radio", "dropdown"] | None = None  # a single choice's
    provenance: Provenance | None = None
    # v0.21, in a designed or LimeSurvey questionnaire: when it is asked (D-165); its
    # statements (grid), choices (single) or options (checkbox) in random order (D-166);
    # a single choice that is an attention check, with the codes of its right answers (D-170).
    condition: Condition | None = None
    shuffle: bool = False
    attention: list[str] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _shaped(self) -> Question:
        if self.answer is not None and self.kind != "open":
            raise ValueError("only an open question has an answer type")
        if self.layout is not None and self.kind != "single":
            raise ValueError("only a single choice is shown as a list or buttons")
        if self.kind == "display" and (self.options or self.rows or self.required):
            raise ValueError("a displayed text has no answer")
        if self.shuffle and self.kind not in ("single", "checkbox", "grid"):
            raise ValueError("only statements, choices or options are shown in random order")
        if self.attention is not None and self.kind != "single":
            raise ValueError("only a single choice is an attention check (or a grid's statement)")
        if any(row.attention for row in self.rows) and self.kind != "grid":
            raise ValueError("only a grid's statement is an attention check")
        return self


class Section(Strict):
    """A section of a designed questionnaire (v0.20): its id is never given again."""

    section_id: str  # "S2"
    title: str = ""
    instruction: str | None = None
    condition: Condition | None = None  # v0.21 (D-165), for each of its questions
    shuffle: bool = False  # v0.21 (D-166): its questions in random order


class QuestionnaireText(Strict):
    """A paragraph that is not a question: instructions, definitions, consent page."""

    page: int | None = None
    text: str


class Questionnaire(Strict):
    """The study's questionnaire, a documented source given by the team (D-012)."""

    file_name: str
    sha256: str
    # xlsx: a platform export's header (v0.7, D-045); lss: a LimeSurvey structure, .lss or
    # .txt (v0.20, D-148); designed: built in the tool, `sha256` that of its content (D-146).
    format: Literal["pdf", "txt", "xlsx", "lss", "designed"]
    n_pages: int | None = None
    questions: list[Question] = []
    texts: list[QuestionnaireText] = []
    sections: list[Section] = []  # v0.20, in the order shown


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
    """A condition on a variable (its original name), on the score of a group's scoring or,
    since v0.15, on a recoded variable (the id of its rule); a missing value never meets it,
    except with `missing`."""

    id: str
    kind: Literal["condition"] = "condition"
    variable: str | None = None
    score: str | None = None
    recode: str | None = None
    operator: Operator
    value: Code | list[Code] | None = None
    reason: NonEmptyText
    source: str | None = None

    @model_validator(mode="after")
    def _complete(self) -> ConditionRule:
        if sum(v is not None for v in (self.variable, self.score, self.recode)) != 1:
            raise ValueError("a condition names one variable, score or recoded variable")
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
    threshold is the team's choice and needs its source (principle 4). Dates in text (a
    platform's export) are read with `text_format`, "iso" or a format of the slashes
    (`ddict.profile.compute.TEXT_DATETIME_FORMATS`), found in the data when the rule is
    made."""

    id: str
    kind: Literal["duration"] = "duration"
    start: str
    end: str
    min_seconds: float = Field(gt=0)
    text_format: str | None = None
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


class AttentionCheck(Strict):
    """An attention check by its variable (original name) and its right answers."""

    variable: str
    correct: list[Code] = Field(min_length=1)


class AttentionRule(Strict):
    """v0.21 (D-170): failed at least `min_failed` of the attention checks; an item left
    empty is a failure or ignored, as the team chooses (no default); an item not asked is
    never a failure."""

    id: str
    kind: Literal["attention"] = "attention"
    checks: list[AttentionCheck] = Field(min_length=1)
    min_failed: int = Field(default=1, ge=1)
    empty: Literal["failed", "ignored"]
    reason: NonEmptyText
    source: str | None = None

    @model_validator(mode="after")
    def _counted(self) -> AttentionRule:
        names = [c.variable for c in self.checks]
        if len(set(names)) != len(names):
            raise ValueError("each attention check once")
        if self.min_failed > len(self.checks):
            raise ValueError("more failures required than there are checks")
        return self


ExclusionRule = Annotated[
    ConditionRule
    | CompletenessRule
    | DurationRule
    | StraightliningRule
    | DuplicateRule
    | AttentionRule,
    Field(discriminator="kind"),
]


class Exclusions(Strict):
    next_id: int = 1
    rules: list[ExclusionRule] = []


# --- The analysis plan (v0.13, D-101 to D-104, D-109): decisions of the team, never a value
# of the data nor a result. The sheet is docs/plan-analyse-article.md (validated). ---


class VariableRef(Strict):
    """A variable by its key in the project, which survives a renaming: a variable of the
    file (its original name), the score of a group's scoring, a reversed item or, since
    v0.15, a recoded variable (the id of its rule). Shared by the plan and the analysis
    notebook (v0.11)."""

    variable: str | None = None
    score: str | None = None
    reversed: str | None = None
    recode: str | None = None

    @model_validator(mode="after")
    def _one(self) -> VariableRef:
        if sum(v is not None for v in (self.variable, self.score, self.reversed, self.recode)) != 1:
            raise ValueError(
                "a variable reference names exactly one of variable, score, reversed, recode"
            )
        return self

    @model_serializer
    def _only_the_one(self) -> dict[str, str]:
        return {
            k: v
            for k, v in (
                ("variable", self.variable),
                ("score", self.score),
                ("reversed", self.reversed),
                ("recode", self.recode),
            )
            if v is not None
        }


# --- Recoding (v0.15, D-120): a derived variable as a decision of the team, never the
# column itself, computed in memory after the scores and before the exclusion rules. The
# sheet is docs/verification-depot.md, section 1 (validated). ---


class RecodeGroup(Strict):
    """A category of a regrouping: its code, its label and the source values it gathers."""

    code: int
    label: NonEmptyText
    values: list[Code] = Field(min_length=1)


class _Recode(Strict):
    @model_validator(mode="after")
    def _source(self):
        if self.source.recode is not None:  # type: ignore[attr-defined]
            raise ValueError("a recoded variable is recoded from its own source")
        if self.source.reversed is not None:  # type: ignore[attr-defined]
            raise ValueError("a reversed item is not recoded")
        return self


class GroupsRecode(_Recode):
    """Categories gathered into new ones; `missing_values`: source values that become
    missing. Every observed source value must have a place (checked on the data)."""

    id: str
    kind: Literal["groups"] = "groups"
    source: VariableRef
    name: NonEmptyText
    label: NonEmptyText
    level: Literal["nominal", "ordinal"] = "nominal"
    groups: list[RecodeGroup] = Field(min_length=2)
    missing_values: list[Code] = []
    reason: NonEmptyText

    @model_validator(mode="after")
    def _groups(self) -> GroupsRecode:
        codes = [g.code for g in self.groups]
        if len(set(codes)) != len(codes):
            raise ValueError("two groups have the same code")
        values = [_same(v) for g in self.groups for v in g.values]
        values += [_same(v) for v in self.missing_values]
        if len(set(values)) != len(values):
            raise ValueError("a source value is in two groups")
        return self


class ClassesRecode(_Recode):
    """A number cut into classes: each class from its cut included to the next one
    excluded; the first from −∞, the last to +∞. Codes 1, 2… in order."""

    id: str
    kind: Literal["classes"] = "classes"
    source: VariableRef
    name: NonEmptyText
    label: NonEmptyText
    level: Literal["ordinal"] = "ordinal"
    cuts: list[float] = Field(min_length=1)
    labels: list[NonEmptyText]
    reason: NonEmptyText

    @model_validator(mode="after")
    def _cuts(self) -> ClassesRecode:
        if any(b <= a for a, b in zip(self.cuts, self.cuts[1:], strict=False)):
            raise ValueError("the cuts must increase")
        if len(self.labels) != len(self.cuts) + 1:
            raise ValueError("one label per class: one more than the cuts")
        return self


def _same(value: Code) -> Code:
    """1 and 1.0 are the same source value; a text stays a text."""
    return float(value) if isinstance(value, int | float) else value


Recode = Annotated[GroupsRecode | ClassesRecode, Field(discriminator="kind")]


class Recodes(Strict):
    next_id: int = 1
    rules: list[Recode] = []


# The tested effect: the one p-value a hypothesis is about (D-103).
class DifferenceEffect(Strict):
    kind: Literal["difference"] = "difference"  # t test, Mann-Whitney


class GroupEffect(Strict):
    kind: Literal["group"] = "group"  # ANOVA, Kruskal-Wallis: the overall test


class AssociationEffect(Strict):
    kind: Literal["association"] = "association"  # chi-square, Fisher


class ModelEffect(Strict):
    kind: Literal["model"] = "model"  # a regression's overall F


class PartialEffect(Strict):
    kind: Literal["partial"] = "partial"  # v0.14: a partial correlation, of its two variables


class InteractionEffect(Strict):
    kind: Literal["interaction"] = "interaction"  # v0.14: a moderation's interaction


class PairEffect(Strict):
    """A pair of a correlation, by its two variables, never by its position."""

    kind: Literal["pair"] = "pair"
    variables: list[VariableRef] = Field(min_length=2, max_length=2)


class PredictorEffect(Strict):
    """A predictor of a regression, by its variable: its one coefficient."""

    kind: Literal["predictor"] = "predictor"
    variable: VariableRef


Effect = Annotated[
    DifferenceEffect
    | GroupEffect
    | AssociationEffect
    | ModelEffect
    | PairEffect
    | PredictorEffect
    | PartialEffect
    | InteractionEffect,
    Field(discriminator="kind"),
]
Direction = Literal["first_higher", "second_higher", "positive", "negative"]
DataOrigin = Literal["primary", "secondary"]
# The five answers of the OSF Prereg form on existing data (D-109).
DataStatus = Literal[
    "before_creation", "before_observation", "before_access", "before_analysis", "after_analysis"
]
Statement = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
FamilyName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]


SubgroupOperator = Literal["eq", "ne", "lt", "le", "gt", "ge", "in"]


class Subgroup(Strict):
    """v0.14 (D-113): the people an analysis or an hypothesis is about, by a condition on a
    variable (by its key, as the roles); never an identifier nor a free text, never a list
    of people."""

    variable: VariableRef
    operator: SubgroupOperator
    value: Code | list[Code]

    @model_validator(mode="after")
    def _values(self) -> Subgroup:
        if (self.operator == "in") != isinstance(self.value, list):
            raise ValueError("'in' takes a list of values, the other operators one value")
        if self.operator == "in" and not self.value:
            raise ValueError("'in' takes at least one value")
        return self


class Hypothesis(Strict):
    """An hypothesis written by the team: `id` (H1, H2...) is never given again after a
    removal; the order of the list is the order of the article."""

    id: str
    statement: Statement
    analysis: str
    roles: dict[str, list[VariableRef]]
    options: dict[str, str] = {}
    effect: Effect
    direction: Direction | None = None
    kind: Literal["confirmatory", "exploratory"] = "confirmatory"
    family: FamilyName | None = None
    subgroup: Subgroup | None = None  # v0.14 (D-113)


class PriorAnalysis(Strict):
    """A planned analysis the notebook already held the day the plan was frozen."""

    hypothesis: str
    entry: str
    added: str


class Frozen(Strict):
    date: str
    fingerprint: str  # the plan's, the day it was frozen
    prior: list[PriorAnalysis] = []


class Amendment(Strict):
    """A change after the plan was frozen: dated, with its reason, never removed. `before`
    and `after` keep only the fields that changed (a whole hypothesis when one is added or
    removed)."""

    date: str
    target: str  # an hypothesis (H2) or "rules"
    change: Literal["modified", "added", "removed"]
    reason: NonEmptyText
    before: dict[str, JsonValue] = {}
    after: dict[str, JsonValue] = {}


class Plan(Strict):
    alpha: float | None = Field(default=None, gt=0, lt=1)  # typed by the team
    correction: Literal["none", "holm", "bonferroni"] = "holm"
    missing: Literal["listwise_by_analysis"] = "listwise_by_analysis"
    sample_size: str = Field(default="", max_length=2000)
    data_origin: DataOrigin | None = None  # declared by the team (D-109)
    data_status: DataStatus | None = None
    next_id: int = 1
    hypotheses: list[Hypothesis] = []
    frozen: Frozen | None = None
    amendments: list[Amendment] = []


class Publication(Strict):
    """A version of the designed questionnaire sent to the ethics committee or published in
    LimeSurvey (v0.20, D-150): a copy of it at that moment, and its fingerprint."""

    kind: Literal["ethics", "limesurvey"]
    date: str
    fingerprint: str
    questionnaire: Questionnaire
    note: str | None = None  # a reason, never required


class KeptPoint(Strict):
    """A review point closed by "Garder tel quel" (v0.20): it comes back when the text it
    was about changes."""

    code: str
    target: str  # "Q7", "Q7.r3", "Q10.o2"
    fingerprint: str  # of the texts the point looked at
    date: str


class Design(Strict):
    """What a project created by "Concevoir un questionnaire" keeps (v0.20, D-145), even
    once its database has arrived."""

    created: str
    # The day its content last changed (v0.20, D-152): the date the Word gives, never the
    # day of its production.
    changed: str | None = None
    # The last number given to each kind of id ("Q", "S", "Q7.r", "Q7.o"): an id is never
    # given again. Keys in sorted order.
    counters: dict[str, int] = {}
    publications: list[Publication] = []
    kept: list[KeptPoint] = []


class NoDatabase(ValueError):
    """Asked of a project whose database has not arrived yet (v0.20, D-145): `what` names
    what needs it ("context", "syntax", "preparation")."""

    def __init__(self, what: str) -> None:
        super().__init__(what)
        self.what = what


class Project(Strict):
    schema_version: str = SCHEMA_VERSION
    # v0.20.2 (D-161): what the team calls the project, shown instead of its file's name;
    # written by a person only, never sent to the AI, not in the codebook's fingerprint.
    # No file is renamed. Set through `ddict.project.title`.
    title: str | None = None
    # None until the database of a designed questionnaire arrives (v0.20, D-145).
    source: SourceInfo | None = None
    settings: Settings = Settings()
    variables: list[VariableEntry]
    groups: list[Group] = []
    ai_runs: list[AiRun] = []
    questionnaire: Questionnaire | None = None
    glossary: list[GlossaryEntry] = []
    stems: list[QuestionStem] = []
    dataset: Dataset = Dataset()  # v0.8 (D-064)
    exclusions: Exclusions = Exclusions()  # v0.12 (D-093)
    plan: Plan = Plan()  # v0.13 (D-101)
    recodes: Recodes = Recodes()  # v0.15 (D-120)
    design: Design | None = None  # v0.20 (D-145)
    # v0.17 (D-129): what the file held when read, in memory only (`ondisk`).
    _disk: object = PrivateAttr(default=None)

    @model_validator(mode="after")
    def _profiled_from_its_database(self) -> Project:
        if self.source is None and any(e.profile is not None for e in self.variables):
            raise ValueError("without a database, no variable has a profile")
        return self

    def variable(self, name: str) -> VariableEntry:
        for entry in self.variables:
            if entry.name == name:
                return entry
        raise KeyError(name)
