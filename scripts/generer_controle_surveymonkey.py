"""Generate the control export of v0.7: a second fictional SurveyMonkey export, in English.

Written after the fixes of v0.7 were tuned on two real exports and on
`generer_base_surveymonkey.py`, and measured once with the code as it stands (D-042, the
same guard as in v0.6). It holds kinds of questions the two real exports did not have:
contact information (several text fields), a single choice with "other", a ranking, a
slider, several numeric text boxes, a grid with a comment column, a matrix of drop-down
menus, a study in English.

Caution: for these kinds, the names, labels and header cells are assumed, not observed
in a real export. The control export checks that the tool fails cleanly where it does not
know: no false group, no false link, no false identifier.

Everything is invented. The answer key (`corrige-controle-surveymonkey.json`) gives what
the tool should find.

Usage (from the repository root):
    uv run python scripts/generer_controle_surveymonkey.py [output_folder]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generer_base_surveymonkey as base
import generer_bases_fictives as common

SEED = 20261017
N_ROWS = 95
STEM = "trajets"
DEFAULT_OUT_DIR = common.DEFAULT_OUT_DIR
CANARY = "ZQXCTRL"
AGREEMENT = ("Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree")
FREQUENCY = ("Never", "Sometimes", "Often", "Always")
OTHER = "Other (please specify)"


@dataclass(frozen=True)
class Column:
    name: str
    label: str  # the variable label of the .sav
    header: str  # its cell in the second header row of the Excel export
    kind: str  # "code", "text", "number", "tick"
    value_labels: tuple[str, ...] = ()
    measure: str = "nominal"


@dataclass(frozen=True)
class Question:
    rank: int
    text: str
    kind: str  # what it is, for the answer key
    columns: tuple[Column, ...]
    options: tuple[str, ...] = ()  # printed options (questionnaire)
    rows: tuple[str, ...] = ()  # printed rows (questionnaire)
    expected_group: str | None = None  # "scale", "multiple_response" or None
    stem: str = ""  # the stem or prefix a team would give
    extra: dict = field(default_factory=dict)


def _q(rank: int, part: str = "") -> str:
    return f"q{rank:04d}{part}"


def questions() -> list[Question]:
    found = [
        Question(
            1,
            "What is your age group?",
            "single",
            (
                Column(
                    _q(1),
                    "What is your age group?",
                    "Response",
                    "code",
                    ("18-24", "25-34", "35-49", "50-64", "65 or older"),
                ),
            ),
            options=("18-24", "25-34", "35-49", "50-64", "65 or older"),
            stem="age_group",
        ),
        Question(
            2,
            "What is your main way of getting to work?",
            "single_with_other",
            (
                Column(
                    _q(2),
                    "What is your main way of getting to work?",
                    "Response",
                    "code",
                    ("Car", "Bus or train", "Bicycle", "On foot"),
                ),
                Column(_q(2, "_other"), OTHER, OTHER, "text"),
            ),
            options=("Car", "Bus or train", "Bicycle", "On foot", OTHER),
            stem="commute_mode",
        ),
        Question(
            3,
            "Please give your contact information.",
            "contact",
            tuple(
                Column(_q(3, f"_{k:04d}"), "Please give your contact information.", field_, "text")
                for k, field_ in enumerate(
                    ("Name", "City/Town", "Email Address", "Phone Number"), 1
                )
            ),
            rows=("Name", "City/Town", "Email Address", "Phone Number"),
            stem="contact",
        ),
        Question(
            4,
            "How much do you agree with the following statements about your commute?",
            "grid",
            tuple(
                Column(_q(4, f"_{k:04d}"), item, item, "code", AGREEMENT, "scale")
                for k, item in enumerate(
                    (
                        "My commute is stressful.",
                        "I use my commute time well.",
                        "My commute makes me tired.",
                        "I would like a shorter commute.",
                        "My commute is a pleasant part of my day.",
                    ),
                    1,
                )
            ),
            options=AGREEMENT,
            expected_group="scale",
            stem="cs",
        ),
        Question(
            5,
            "Rank the following in order of importance when choosing how to commute.",
            "ranking",
            tuple(
                Column(_q(5, f"_{k:04d}"), item, item, "number")
                for k, item in enumerate(("Cost", "Speed", "Comfort", "Environment"), 1)
            ),
            rows=("Cost", "Speed", "Comfort", "Environment"),
            stem="rank",
        ),
        Question(
            6,
            "How satisfied are you with your commute, from 0 to 100?",
            "slider",
            (
                Column(
                    _q(6),
                    "How satisfied are you with your commute, from 0 to 100?",
                    "Response",
                    "number",
                ),
            ),
            stem="commute_satisfaction",
        ),
        Question(
            7,
            "On a usual day, how many minutes do you spend commuting:",
            "textboxes",
            tuple(
                Column(_q(7, f"_{k:04d}"), item, item, "number")
                for k, item in enumerate(("In the morning", "In the evening"), 1)
            ),
            rows=("In the morning", "In the evening"),
            stem="minutes",
        ),
        Question(
            8,
            "Which of these do you do while commuting? (Select all that apply)",
            "checkbox",
            (
                *(
                    Column(
                        _q(8, f"_{k:04d}"),
                        "Which of these do you do while commuting? (Select all that apply)",
                        option,
                        "tick",
                        (option,),
                    )
                    for k, option in enumerate(
                        ("Read", "Listen to music", "Work", "Sleep", "Talk on the phone", OTHER),
                        1,
                    )
                ),
                Column(_q(8, "_other"), OTHER, OTHER, "text"),
            ),
            options=("Read", "Listen to music", "Work", "Sleep", "Talk on the phone", OTHER),
            expected_group="multiple_response",
            stem="activities",
        ),
        Question(
            9,
            "How often do the following happen on your commute?",
            "grid_with_comment",
            (
                *(
                    Column(_q(9, f"_{k:04d}"), item, item, "code", FREQUENCY, "scale")
                    for k, item in enumerate(
                        ("Delays", "Crowding", "Unsafe situations", "Bad weather"), 1
                    )
                ),
                Column(_q(9, "_other"), "Comments", "Comments", "text"),
            ),
            options=FREQUENCY,
            expected_group="scale",
            stem="events",
        ),
        Question(
            10,
            "For each trip, choose your usual departure time and mode.",
            "dropdowns",
            tuple(
                Column(
                    _q(10, f"_{r:04d}_{c:04d}"), f"{row} - {col}", f"{row} - {col}", "code", values
                )
                for r, row in enumerate(("Morning trip", "Evening trip"), 1)
                for c, (col, values) in enumerate(
                    (
                        ("Departure", ("Before 7", "7 to 9", "After 9")),
                        ("Mode", ("Car", "Transit", "Active")),
                    ),
                    1,
                )
            ),
            rows=("Morning trip", "Evening trip"),
            stem="trip",
        ),
        Question(
            11,
            "Is there anything else you would like to tell us?",
            "open",
            (
                Column(
                    _q(11),
                    "Is there anything else you would like to tell us?",
                    "Open-Ended Response",
                    "text",
                ),
            ),
            stem="comments",
        ),
    ]
    return found


PLATFORM = (
    ("CollectorNm", None, "nominal"),
    ("respondent_id", "respondent_id", "id"),
    ("collector_id", "collector_id", "id"),
    ("date_created", "date_created", "date"),
    ("date_modified", "date_modified", "date"),
    ("ip_address", "ip_address", "ip"),
    ("email_address", "email_address", "empty"),
    ("first_name", "first_name", "empty"),
    ("last_name", "last_name", "empty"),
    ("custom_1", "custom_1", "empty"),
)


def build() -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(SEED)
    n = N_ROWS
    data: dict[str, object] = {}
    starts, ends = base._survey_dates(rng, n, 2)
    for name, _header, _kind in PLATFORM:
        if name == "CollectorNm":
            data[name] = ["Web Link 1"] * n
        elif name == "respondent_id":
            data[name] = (118_000_000_000 + np.arange(n) * 41).astype(float)
        elif name == "collector_id":
            data[name] = np.full(n, 500_000_001.0)
        elif name == "date_created":
            data[name] = starts
        elif name == "date_modified":
            data[name] = ends
        elif name == "ip_address":
            data[name] = [f"198.51.100.{int(k)}" for k in rng.integers(1, 255, size=n)]
        else:
            data[name] = [""] * n
    stress = rng.normal(size=n)
    labels, value_labels, measure, formats = {}, {}, {}, {}
    for name, _header, _kind in PLATFORM:
        labels[name] = name
        measure[name] = "nominal"
        numeric = isinstance(data[name], np.ndarray)
        formats[name] = "F15.0" if numeric else ("A22" if "date" in name else "A100")
    for question in questions():
        for column in question.columns:
            name = column.name
            labels[name] = column.label
            measure[name] = column.measure
            if column.kind == "code":
                count = len(column.value_labels)
                if question.kind in ("grid", "grid_with_comment"):
                    sign = -1 if column.name == _q(4, "_0005") else 1
                    middle = (count + 1) / 2
                    values = np.round(middle + sign * stress + rng.normal(scale=0.8, size=n))
                    values = np.clip(values, 1, count)
                else:
                    values = rng.integers(1, count + 1, size=n).astype(float)
                data[name] = values.astype(float)
                value_labels[name] = {float(k): t for k, t in enumerate(column.value_labels, 1)}
                formats[name] = "F8.2"
            elif column.kind == "tick":
                share = 0.2 + 0.1 * (int(name[-1]) % 4)
                data[name] = np.where(rng.random(n) < share, 1.0, np.nan)
                value_labels[name] = {1.0: column.value_labels[0]}
                formats[name] = "F8.2"
            elif column.kind == "number":
                if question.kind == "ranking":
                    data[name] = np.nan  # set below: a permutation per row
                elif question.kind == "slider":
                    data[name] = np.clip(
                        np.round(60 - 12 * stress + rng.normal(size=n) * 10), 0, 100
                    )
                else:
                    data[name] = np.round(rng.gamma(3, 12, size=n))
                formats[name] = "F8.2"
            else:  # text
                data[name] = [""] * n
                formats[name] = "A100"
        if question.kind == "ranking":
            ranks = np.array([rng.permutation(len(question.columns)) + 1 for _ in range(n)])
            for k, column in enumerate(question.columns):
                data[column.name] = ranks[:, k].astype(float)
    # Text answers, invented, with canaries where a person could be named.
    contact = [c.name for c in questions()[2].columns]
    for i in range(n):
        if i % 4:
            continue
        data[contact[0]][i] = f"{CANARY}Name{i:03d}"
        data[contact[1]][i] = ("Laval", "Sherbrooke", "Gatineau")[i % 3]
        data[contact[2]][i] = f"{CANARY.lower()}{i:03d}@example.org"
        data[contact[3]][i] = f"514-555-{i:04d}"
    for name in (_q(2, "_other"), _q(8, "_other"), _q(9, "_other"), _q(11)):
        for i in np.sort(rng.choice(n, size=8, replace=False)):
            data[name][i] = f"Invented note {CANARY}{i:03d}"
    for i, text in enumerate(data[_q(8, "_other")]):
        data[_q(8, "_0006")][i] = 1.0 if text else np.nan
    names = [name for name, _h, _k in PLATFORM] + [c.name for q in questions() for c in q.columns]
    df = pd.DataFrame({name: data[name] for name in names})
    meta = {
        "column_labels": labels,
        "variable_value_labels": value_labels,
        "variable_measure": measure,
        "variable_format": formats,
    }
    return df, meta


def export_rows() -> list[list[object]]:
    """The Excel export: two header rows, then the answers as text."""
    df, meta = build()
    first, second, kept = [], [], []
    for name, header, _kind in PLATFORM:
        if header is not None:
            first.append(header)
            second.append(None)
            kept.append(name)
    for question in questions():
        for k, column in enumerate(question.columns):
            if (
                question.kind == "checkbox"
                and column.kind == "tick"
                and column.value_labels[0] == OTHER
            ):
                continue  # the "other" option ticked: only its text in this export
            first.append(question.text if k == 0 else None)
            second.append(column.header)
            kept.append(column.name)
    rows: list[list[object]] = [first, second]
    labels = meta["variable_value_labels"]
    for record in df[kept].itertuples(index=False):
        row = []
        for name, value in zip(kept, record, strict=True):
            if value is None or (isinstance(value, float) and np.isnan(value)) or value == "":
                row.append(None)
            elif name in labels:
                row.append(labels[name][float(value)])
            elif isinstance(value, float):
                row.append(int(value))
            else:
                row.append(value)
        rows.append(row)
    return rows


def write_xlsx(path: Path) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    for row in export_rows():
        sheet.append(row)
    workbook.properties.created = common.XLSX_FIXED_TIME
    workbook.properties.modified = common.XLSX_FIXED_TIME
    workbook.save(path)
    base._fix_zip_times(path)


INTRO = (
    "This study is entirely fictional: it serves to check a data documentation tool. "
    f"Contact: Dr. Sam {CANARY}-Example, Fictional Mobility Lab."
)


def write_questionnaire_txt(path: Path) -> None:
    lines = ["Fictional study on commuting and wellbeing", "", INTRO, ""]
    for question in questions():
        lines.append(f"{question.rank}. {question.text}")
        if question.options and question.kind in ("grid", "grid_with_comment"):
            lines.append("\t" + "\t".join(question.options))
            lines += [
                c.label + "\t" * len(question.options) for c in question.columns if c.kind == "code"
            ]
            if question.kind == "grid_with_comment":
                lines.append("Comments")
        else:
            lines += list(question.options or question.rows)
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def answer_key() -> dict:
    groups, links, stems = [], {}, {}
    for name, _header, _kind in PLATFORM:
        links[name] = "none"
    for number, question in enumerate(questions(), start=1):
        qid = f"Q{number}"
        if question.expected_group == "scale":
            groups.append(
                {"kind": "scale", "members": [c.name for c in question.columns if c.kind == "code"]}
            )
        elif question.expected_group == "multiple_response":
            groups.append(
                {
                    "kind": "multiple_response",
                    "members": [c.name for c in question.columns if c.kind == "tick"],
                    "attached": [c.name for c in question.columns if c.name.endswith("_other")],
                }
            )
        stems[_q(question.rank)] = question.stem
        for k, column in enumerate(question.columns, 1):
            if question.kind in ("single", "slider", "open"):
                links[column.name] = qid
            elif question.kind == "single_with_other":
                links[column.name] = qid if k == 1 else f"{qid}.o5"
            elif question.kind == "checkbox":
                links[column.name] = f"{qid}.o{min(k, 6)}"
            elif question.kind in ("grid", "grid_with_comment") and column.kind == "code":
                links[column.name] = f"{qid}.r{k}"
            else:
                links[column.name] = None  # no rule: a person decides
    identifiers = [c.name for c in questions()[2].columns if c.header != "City/Town"]
    return {
        "version": 1,
        "description": (
            "Base de contrôle de la v0.7 : export SurveyMonkey fictif en anglais, avec des types "
            "de questions supposés (coordonnées, classement, curseur, zones de texte, menus "
            "déroulants). Tout est inventé."
        ),
        "sav": f"{STEM}_surveymonkey.sav",
        "xlsx": f"{STEM}_surveymonkey.xlsx",
        "questionnaire_txt": f"questionnaire-{STEM}.txt",
        "n_rows": N_ROWS,
        "groups": groups,
        "links": links,
        "stems": stems,
        "likely_identifiers": identifiers,
        "kinds": {_q(q.rank): q.kind for q in questions()},
        "canary": CANARY,
    }


def write_all(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df, meta = build()
    paths = []
    sav = out_dir / f"{STEM}_surveymonkey.sav"
    common.write_sav(df, meta, sav)
    paths.append(sav)
    xlsx = out_dir / f"{STEM}_surveymonkey.xlsx"
    write_xlsx(xlsx)
    paths.append(xlsx)
    txt = out_dir / f"questionnaire-{STEM}.txt"
    write_questionnaire_txt(txt)
    paths.append(txt)
    key = out_dir / "corrige-controle-surveymonkey.json"
    key.write_text(
        json.dumps(answer_key(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    paths.append(key)
    return paths


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Génère la base de contrôle SurveyMonkey (v0.7).")
    parser.add_argument("out_dir", nargs="?", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    for path in write_all(args.out_dir):
        print(path)


if __name__ == "__main__":
    main()
