"""Survey platforms, described by their conventions (v0.7, D-044).

A platform is data, not code: the variables it adds (with the names they had over time),
how it names the variables of the questions, and how its Excel and CSV exports write their
two header rows. The rest of the tool reads only this description, so another platform
(LimeSurvey, Qualtrics, REDCap) is added by describing it, with its tests.

A database is recognized when it holds enough of the platform's own variables and when most
of its other names follow the platform's pattern.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ddict.project.model import Project

# A database is an export of the platform with at least this many of its own variables...
MIN_PLATFORM_VARIABLES = 3
# ... and this share of its other names following the platform's pattern.
MIN_PATTERN_SHARE = 0.5


@dataclass(frozen=True)
class PlatformVariable:
    """A variable the platform adds to every export."""

    role: str  # "respondent_id", "start_date", ...
    names: tuple[str, ...]  # in the .sav file, every variant seen: the old one first
    # Its title in the Excel and CSV exports of the old variant, if it is there; the exports
    # of the recent variant use the recent name itself as title.
    header: str | None
    new_name: dict[str, str]  # the fixed name proposed for it, by study language (D-050)


@dataclass(frozen=True)
class Place:
    """Where a variable sits in the structure of the survey."""

    # The question: its rank in the survey (SurveyMonkey), or its code (LimeSurvey, v0.20).
    question: int | str
    # The grid item or checkbox option: its rank, or its code ("SQ001").
    item: int | str | None = None
    other: bool = False  # the text of the "other" option


@dataclass(frozen=True)
class Platform:
    name: str
    title: str  # as shown to people: "SurveyMonkey"
    variables: tuple[PlatformVariable, ...]
    # The name of a question's variable: groups "question", "item" (digits) or "other".
    item_name: re.Pattern
    question_format: str  # "q{question:04d}"
    item_format: str  # "q{question:04d}_{item:04d}"
    other_format: str  # "q{question:04d}_other"
    # Second header row of the Excel and CSV exports: the cell under a question answered
    # in a single column, and the forms of the "other" option.
    response_cells: tuple[str, ...]
    other_cells: tuple[str, ...]
    # The start of the names of a question's items: the prefix of its group.
    prefix_format: str = "{question}_"
    # The codes of a ticked box's value labels, beyond the one label of SurveyMonkey's:
    # LimeSurvey's .sav labels "Y" and "0" (v0.20).
    checkbox_codes: tuple[str, ...] = ()
    # Its exports name an item "question[item]" in a CSV or Excel file, "question_item" in its
    # .sav file: the readers name the columns as the .sav does (LimeSurvey, v0.20).
    bracket_names: bool = False
    # The date its .sav file writes for an empty date and time (the zero of SPSS's dates):
    # read as an empty cell (LimeSurvey, v0.20).
    empty_datetime: str | None = None
    # The label its .sav file gives an item: "[La lecture] Qu'est-ce qui vous aide à dormir ?"
    # (LimeSurvey, v0.20), groups "item" and "question".
    item_label: re.Pattern | None = None

    def label_question(self, label: str | None) -> str | None:
        """The question's text in an item's label, when the platform writes both there."""
        if not label or self.item_label is None:
            return None
        found = self.item_label.fullmatch(label)
        return found.group("question") if found else None

    def question_key(self, question: int | str) -> str:
        """The key of a question's stem (D-048): "q0005", or a LimeSurvey code."""
        return self.question_format.format(question=question)

    def item_prefix(self, question: int | str) -> str:
        return self.prefix_format.format(question=question)

    def ticked(self, label_codes, n_distinct: int | None) -> bool:
        """Whether a variable looks like a ticked box: a single value label (or the
        platform's own pair of labels), and a single value observed at most."""
        if (n_distinct or 0) > 1:
            return False
        if len(label_codes) <= 1:
            return True
        codes = {str(c) for c in label_codes}
        return bool(self.checkbox_codes) and codes <= set(self.checkbox_codes)

    def column_name(self, header: str) -> str:
        """The name the .sav file gives a column of a CSV or Excel export."""
        if not self.bracket_names:
            return header
        return _BRACKET.sub(r"_\1", header)

    def platform_variable(self, name: str) -> PlatformVariable | None:
        lowered = name.lower()
        for variable in self.variables:
            if lowered in (n.lower() for n in variable.names):
                return variable
        return None

    def place(self, name: str) -> Place | None:
        """The place of a question's variable, from its name alone; None otherwise."""
        match = self.item_name.fullmatch(name)
        if match is None:
            return None
        item = match.group("item")
        question = match.group("question")
        return Place(
            question=int(question) if question.isdigit() else question,
            item=(int(item) if item.isdigit() else item) if item else None,
            other=match.group("other") is not None,
        )

    def recognizes(self, names: Sequence[str]) -> bool:
        own = [n for n in names if self.platform_variable(n) is not None]
        others = [n for n in names if self.platform_variable(n) is None]
        if len({self.platform_variable(n).role for n in own}) < MIN_PLATFORM_VARIABLES:
            return False
        following = sum(self.place(n) is not None for n in others)
        return bool(others) and following / len(others) >= MIN_PATTERN_SHARE

    def header_names(self, first: Sequence[object], second: Sequence[object]) -> list[str] | None:
        """The names of the columns of an export with two header rows, as the .sav file
        names them; None when the two rows are not such a header.

        The first row holds the title of each platform variable, and the text of each
        question once, above its first column; the second row holds, under each column of a
        question, its item, its option, or a response cell ("Response"), and nothing under
        the platform variables (a row of answers has the respondent's identifier there).
        """
        first = [_cell(c) for c in first]
        second = [_cell(c) for c in second]
        width = max(len(first), len(second))
        first += [""] * (width - len(first))
        second += [""] * (width - len(second))
        # The column title of a platform variable, and the name it has in the .sav file of
        # the same export: "Respondent ID" goes with RespondentID, respondent_id with itself.
        headers = {_plain(v.header): v.names[0] for v in self.variables if v.header}
        headers |= {_plain(n): n for v in self.variables if v.header for n in v.names}
        if not any(_plain(c) in headers for c in first):
            return None
        others = {_plain(c) for c in self.other_cells}
        names: list[str] = []
        question = 0
        item = 0
        in_question = False
        for top, below in zip(first, second, strict=True):
            platform_name = headers.get(_plain(top)) if top else None
            if platform_name is not None:
                if below:  # a respondent's answers, not a header row
                    return None
                names.append(platform_name)
                in_question = False
                continue
            if top:
                question += 1
                item = 0
                in_question = True
            elif not in_question or not below:
                return None  # a column without a title that continues nothing
            if below in self.response_cells:
                names.append(self.question_format.format(question=question))
            elif _plain(below) in others:
                names.append(self.other_format.format(question=question))
            else:
                item += 1
                names.append(self.item_format.format(question=question, item=item))
        if question == 0 or len(set(names)) != len(names):
            return None
        return names

    def header_labels(self, first: Sequence[object], second: Sequence[object]) -> list[str | None]:
        """The variable labels the platform's .sav file gives the same columns (v0.7, step 4):
        the question's text for a question in one column, the item's or option's text for
        the others, none for the platform's own variables. Header cells, never answers."""
        names = self.header_names(first, second) or []
        first = [_cell(c) for c in first] + [""] * len(names)
        second = [_cell(c) for c in second] + [""] * len(names)
        labels: list[str | None] = []
        question_text = ""
        for column, name in enumerate(names):
            place = self.place(name)
            if place is None:
                labels.append(None)
                continue
            question_text = first[column] or question_text
            whole = place.item is None and not place.other
            labels.append((question_text if whole else second[column]) or None)
        return labels


def _cell(value: object) -> str:
    return "" if value is None else str(value).strip()


def _plain(text: str) -> str:
    """Case, accents and spaces aside, for comparing header cells."""
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(plain.lower().split())


SURVEYMONKEY = Platform(
    name="surveymonkey",
    title="SurveyMonkey",
    variables=(
        PlatformVariable(
            "collector_name",
            ("CollectorNm",),
            None,
            {"fr": "nom_collecteur", "en": "collector_name"},
        ),
        PlatformVariable(
            "respondent_id",
            ("RespondentID", "respondent_id"),
            "Respondent ID",
            {"fr": "respondent_id", "en": "respondent_id"},
        ),
        PlatformVariable(
            "collector_id",
            ("CollectorID", "collector_id"),
            "Collector ID",
            {"fr": "collector_id", "en": "collector_id"},
        ),
        PlatformVariable(
            "start_date",
            ("StartDate", "date_created"),
            "Start Date",
            {"fr": "date_debut", "en": "start_date"},
        ),
        PlatformVariable(
            "end_date",
            ("EndDate", "date_modified"),
            "End Date",
            {"fr": "date_fin", "en": "end_date"},
        ),
        PlatformVariable(
            "ip_address",
            ("IPAddress", "ip_address"),
            "IP Address",
            {"fr": "adresse_ip", "en": "ip_address"},
        ),
        PlatformVariable(
            "email",
            ("EmailAddress", "email_address"),
            "Email Address",
            {"fr": "courriel", "en": "email"},
        ),
        PlatformVariable(
            "first_name",
            ("FirstName", "first_name"),
            "First Name",
            {"fr": "prenom", "en": "first_name"},
        ),
        PlatformVariable(
            "last_name",
            ("LastName", "last_name"),
            "Last Name",
            {"fr": "nom_famille", "en": "last_name"},
        ),
        PlatformVariable(
            "custom_1",
            ("CustomData1", "custom_1"),
            "Custom Data 1",
            {"fr": "donnees_personnalisees_1", "en": "custom_data_1"},
        ),
    ),
    item_name=re.compile(
        r"q(?P<question>\d{4})(?:_(?P<item>\d{4})|_(?P<other>other))?", re.IGNORECASE
    ),
    question_format="q{question:04d}",
    item_format="q{question:04d}_{item:04d}",
    other_format="q{question:04d}_other",
    response_cells=("Response", "Open-Ended Response"),
    other_cells=("Other (please specify)", "Autre (veuillez préciser)"),
    prefix_format="q{question:04d}_",
)

# LimeSurvey (v0.20, D-148): its conventions as LimeSurvey Cloud 7.6 exported a fictional
# survey on 2026-10-19 (docs/essais/2026-10-19-limesurvey-fictif.md), and only those: the
# variables it added to the CSV, Excel and .sav exports of that survey. A question's code has
# letters and digits only (D-156), so the first "_" ends it.
LIMESURVEY = Platform(
    name="limesurvey",
    title="LimeSurvey",
    variables=(
        PlatformVariable("response_id", ("id",), None, {"fr": "id_reponse", "en": "response_id"}),
        PlatformVariable(
            "submit_date", ("submitdate",), None, {"fr": "date_soumission", "en": "submit_date"}
        ),
        PlatformVariable(
            "last_page", ("lastpage",), None, {"fr": "derniere_page", "en": "last_page"}
        ),
        PlatformVariable(
            "start_language",
            ("startlanguage",),
            None,
            {"fr": "langue_depart", "en": "start_language"},
        ),
        PlatformVariable("seed", ("seed",), None, {"fr": "graine", "en": "seed"}),
        PlatformVariable(
            "start_date", ("startdate",), None, {"fr": "date_debut", "en": "start_date"}
        ),
        PlatformVariable(
            "last_action_date",
            ("datestamp",),
            None,
            {"fr": "date_derniere_action", "en": "last_action_date"},
        ),
        PlatformVariable(
            "quota_exit", ("quota_exit",), None, {"fr": "sortie_quota", "en": "quota_exit"}
        ),
    ),
    item_name=re.compile(
        r"(?P<question>[A-Za-z][A-Za-z0-9]*)(?:_(?P<other>other)|_(?P<item>[A-Za-z0-9]+))?"
    ),
    question_format="{question}",
    item_format="{question}_{item}",
    other_format="{question}_other",
    response_cells=(),
    other_cells=(),
    checkbox_codes=("Y", "0"),
    bracket_names=True,
    empty_datetime="1582-10-14",
    item_label=re.compile(r"\[(?P<item>[^\]]*)\] (?P<question>.+)"),
)

PLATFORMS = (SURVEYMONKEY, LIMESURVEY)
_BRACKET = re.compile(r"\[([A-Za-z0-9]+)\]")


@dataclass(frozen=True)
class PlatformQuestion:
    """A question of the survey, as its variables show it (v0.7, step 4)."""

    rank: int  # its rank in the survey
    kind: str  # "grid", "checkbox", or "single" (one variable: a choice or an open answer)
    items: tuple[str, ...]  # the variables of its items or options, by rank
    other: str | None = None  # the variable of its "other" text
    single: str | None = None  # the variable of a whole question
    key: int | str | None = None  # its place's question: the rank, or a code (v0.20)

    @property
    def variables(self) -> tuple[str, ...]:
        found = (self.single,) if self.single else ()
        return (*found, *self.items, *((self.other,) if self.other else ()))


def survey_questions(
    platform: Platform, names: Sequence[str], ticked: set[str]
) -> list[PlatformQuestion]:
    """The questions of an export, in survey order, from the names of its variables.

    `ticked`: the variables that look like a checkbox (a single value label, or a single
    value observed): a question whose items all do is a set of checkboxes, otherwise a grid.
    """
    by_key: dict[int | str, list[tuple[str, Place]]] = {}
    for name in names:
        if platform.platform_variable(name) is not None:
            continue
        place = platform.place(name)
        if place is not None:
            by_key.setdefault(place.question, []).append((name, place))
    # Ranks in their order; codes (LimeSurvey) in the order of the export's columns.
    keys = sorted(by_key) if all(isinstance(k, int) for k in by_key) else list(by_key)
    found = []
    for rank, key in enumerate(keys, start=1):
        members = by_key[key]
        ranked = all(isinstance(p.item, int) for _n, p in members if p.item)
        ordered = sorted(members, key=lambda m: m[1].item or 0) if ranked else members
        items = tuple(n for n, p in ordered if p.item)
        other = next((n for n, p in members if p.other), None)
        single = next((n for n, p in members if p.item is None and not p.other), None)
        if not items:
            kind = "single"
        elif all(n in ticked for n in items):
            kind = "checkbox"
        else:
            kind = "grid"
        number = key if isinstance(key, int) else rank
        found.append(PlatformQuestion(number, kind, items, other, single, key))
    return found


def by_name(name: str | None) -> Platform | None:
    return next((p for p in PLATFORMS if p.name == name), None)


def of(project: Project) -> Platform | None:
    """The platform whose export the project's database is; None without a database yet
    (v0.20, D-145)."""
    return None if project.source is None else by_name(project.source.platform)


def recognize(names: Sequence[str]) -> Platform | None:
    """The platform whose export this is, from the names of its variables."""
    return next((p for p in PLATFORMS if p.recognizes(names)), None)


def split_header(rows: list[list[object]]) -> tuple[Platform, list[str]] | None:
    """For a table read with its first two rows as data: the platform and the names of the
    columns, when the first two rows are a platform's header; None otherwise."""
    if len(rows) < 2:
        return None
    for platform in PLATFORMS:
        names = platform.header_names(rows[0], rows[1])
        if names is not None:
            return platform, names
    return None
