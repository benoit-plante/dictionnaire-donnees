"""Generate a fictional SurveyMonkey export, in two waves (v0.7, step 1).

A fictional study of working conditions, exported as SurveyMonkey does it, with everything
the trial of two real exports showed (docs/plan-v0.7.md, § 1). All items are invented.

- Platform variables first: `CollectorNm`, then the old names (`RespondentID`, `StartDate`,
  ...) in wave 1 and the recent ones (`respondent_id`, `date_created`, ...) in wave 2.
- Questions named by their rank (`q0001`), grid items and checkbox options by the rank of
  the question and their own (`q0003_0004`), the "other" text by `q0005_other`.
- Numeric codes in `F8.2`, one value label set per variable; `scale` level for the items of
  the Likert grid, `nominal` elsewhere; dates of the survey as strings (`A22` or `A100`).
- A checkbox variable has a single value label (`1 = option`), unticked is empty, and the
  question text as its label; the "other" variable is labelled in English.
- "Ne sais pas" (6) and "Préfère ne pas répondre" (7) follow a 1-5 scale, not declared
  missing; an item of the Likert grid uses the verb "identifier"; a text variable labelled
  `id` comes last (a family code and invented initials).

Both waves also exist as an Excel workbook with the two header rows of SurveyMonkey (the
platform columns titled "Respondent ID" in the old exports, `respondent_id` in the recent
ones), and wave 2 as a CSV file too, with a numbered questionnaire (.txt) and a PDF laid
out like SurveyMonkey's (grid column titles stacked over several lines). Against wave 1,
wave 2 adds a question (which shifts the `qNNNN` numbering), removes an item of the Likert
grid and changes a value label. Wave 1 is also given renamed, as the team would have left
it: its documented copy (`_t1` names) and its table of names (D-052).

The answer key (`corrige-surveymonkey.json`) gives the groups, the links, the names and the
differences between the waves.

Usage (from the repository root):
    uv run python scripts/generer_base_surveymonkey.py [output_folder]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generer_bases_fictives as common

SEED = 20261015
N_ROWS = {1: 120, 2: 110}
STEM = "travail"
QUESTIONNAIRE_NAME = "questionnaire-travail"
ANSWER_KEY_NAME = "corrige-surveymonkey.json"
DEFAULT_OUT_DIR = common.DEFAULT_OUT_DIR
CANARY_ID = "ZQXSMID"  # in the identifying platform variables
CANARY_TEXT = "ZQXSMTXT"  # in the open answers
CANARY_CONSENT = "ZQXSMQUEST"  # in the information page of the questionnaire

# --- The questions, in the order of wave 2. -------------------------------------------------


@dataclass(frozen=True)
class Question:
    key: str  # stable across waves: what the question is about
    kind: str  # "single", "grid", "checkbox", "open", "hidden"
    text: str  # as the participant reads it; the label of a hidden variable
    options: tuple[str, ...] = ()  # answer options (single, grid) or ticked options (checkbox)
    items: tuple[str, ...] = ()  # grid items
    waves: tuple[int, ...] = (1, 2)
    measure: str = "nominal"
    # Expected names: the stem of the question, or the prefix of a grid given by a person.
    stem: str = ""
    # Wave 1 only: a different option text (the changed value label), by option rank.
    options_wave1: dict[int, str] = field(default_factory=dict)
    # Wave 1 only: an item removed in wave 2, and its rank in wave 1.
    removed_item: tuple[int, str] | None = None


FREQUENCY = ("Jamais", "Rarement", "Parfois", "Souvent", "Toujours")
SATISFACTION = (
    "Très insatisfait·e",
    "Plutôt insatisfait·e",
    "Ni l'un ni l'autre",
    "Plutôt satisfait·e",
    "Très satisfait·e",
    "Ne sais pas",
    "Préfère ne pas répondre",
)
TENSION_ITEMS = (
    "J'ai eu trop de tâches à accomplir en peu de temps.",
    "J'ai pu prendre mes pauses comme prévu.",
    "Je me suis senti·e soutenu·e par mes collègues.",
    "J'ai eu de la difficulté à décrocher après le travail.",
    "J'ai pu identifier les sources de tension dans mon équipe.",
    "J'ai reçu des consignes contradictoires.",
    "Je me suis senti·e reconnu·e pour mon travail.",
    "J'ai manqué d'information pour bien faire mon travail.",
    "J'ai eu le sentiment de bien faire mon travail.",
    "J'ai été interrompu·e souvent dans mes tâches.",
    "J'ai eu assez d'autonomie dans l'organisation de mon travail.",
    "J'ai pensé à quitter mon emploi.",
)
REMOVED_TENSION_ITEM = (10, "J'ai travaillé en dehors de mes heures habituelles.")
# Items of the Likert grid scored the other way: a satisfying situation.
TENSION_REVERSED = {2, 3, 5, 7, 9, 11}

QUESTIONS = (
    Question(
        "secteur",
        "single",
        "Dans quel secteur travaillez-vous ?",
        ("Santé et services sociaux", "Éducation", "Commerce", "Industrie", "Administration"),
        stem="secteur",
    ),
    Question(
        "anciennete",
        "single",
        "Depuis combien de temps occupez-vous votre emploi actuel ?",
        ("Moins d'un an", "De 1 à 5 ans", "De 6 à 10 ans", "Plus de 10 ans"),
        waves=(2,),
        stem="anciennete",
    ),
    Question(
        "tensions",
        "grid",
        "Au cours du dernier mois, à quelle fréquence avez-vous vécu les situations suivantes "
        "au travail ?",
        FREQUENCY,
        TENSION_ITEMS,
        measure="scale",
        stem="eft",
        removed_item=REMOVED_TENSION_ITEM,
    ),
    Question(
        "milieu",
        "grid",
        "Dans quelle mesure êtes-vous satisfait·e des aspects suivants de votre milieu de "
        "travail ?",
        SATISFACTION,
        (
            "Êtes-vous satisfait·e de l'éclairage ?",
            "Êtes-vous satisfait·e du niveau de bruit ?",
            "Êtes-vous satisfait·e de la température ?",
            "Êtes-vous satisfait·e de l'équipement fourni ?",
            "Êtes-vous satisfait·e de l'espace de rangement ?",
        ),
        stem="milieu",
    ),
    Question(
        "taches",
        "checkbox",
        "Quelles tâches faites-vous dans une semaine habituelle ? (Cochez toutes les réponses "
        "qui s'appliquent)",
        (
            "Accueil de la clientèle",
            "Travail à l'ordinateur",
            "Manutention",
            "Entretien ménager",
            "Supervision d'une équipe",
        ),
        stem="taches",
    ),
    Question(
        "formation",
        "single",
        "Avez-vous reçu une formation en santé et sécurité au travail au cours de la dernière "
        "année ?",
        ("Oui", "Non"),
        stem="formation_sst",
    ),
    Question(
        "pauses",
        "single",
        "Combien de pauses prenez-vous dans une journée de travail habituelle ?",
        ("Aucune", "Une", "Deux", "Trois ou plus"),
        stem="pauses",
        options_wave1={4: "Plus de deux"},
    ),
    Question(
        "consignes",
        "checkbox",
        "Cochez les consignes de sécurité que vous avez reçues à votre arrivée.",
        (
            "Plan d'évacuation",
            "Port de l'équipement de protection",
            "Utilisation des produits dangereux",
            "Premiers soins",
            "Signalement des accidents",
            "Ergonomie du poste de travail",
        ),
        stem="consignes_securite",
    ),
    Question(
        "situation",
        "open",
        "Décrivez une situation récente où vous vous êtes senti·e en danger au travail.",
        stem="situation_danger",
    ),
    Question(
        "transport",
        "checkbox",
        "Coche les moyens de transport que tu utilises pour te rendre au travail.",
        ("Voiture", "Transport en commun", "Vélo", "Marche"),
        stem="transport",
    ),
    Question("commentaires", "open", "Avez-vous d'autres commentaires ?", stem="commentaires"),
    Question("id", "hidden", "id", stem="id_participant"),
)
OTHER_OPTION = "Autre (veuillez préciser)"
OTHER_LABEL = "Other (please specify)"  # the label of the "other" variable in the .sav

# --- Platform variables: SurveyMonkey's names, old (wave 1) and recent (wave 2). -----------

# (role, old name, recent name, header in the Excel export, expected French name, width)
PLATFORM = (
    ("collector_name", "CollectorNm", "CollectorNm", None, "nom_collecteur"),
    ("respondent_id", "RespondentID", "respondent_id", "Respondent ID", "respondent_id"),
    ("collector_id", "CollectorID", "collector_id", "Collector ID", "collector_id"),
    ("start_date", "StartDate", "date_created", "Start Date", "date_debut"),
    ("end_date", "EndDate", "date_modified", "End Date", "date_fin"),
    ("ip_address", "IPAddress", "ip_address", "IP Address", "adresse_ip"),
    ("email", "EmailAddress", "email_address", "Email Address", "courriel"),
    ("first_name", "FirstName", "first_name", "First Name", "prenom"),
    ("last_name", "LastName", "last_name", "Last Name", "nom_famille"),
    ("custom_1", "CustomData1", "custom_1", "Custom Data 1", "donnees_personnalisees_1"),
)
DATE_WIDTH = {1: 22, 2: 100}
FAMILY_LETTERS = "ABCDEFGHJKLMNPRSTV"


@dataclass(frozen=True)
class Column:
    """One variable of a wave, as SurveyMonkey names it, and what it stands for."""

    name: str
    question: Question | None  # None for a platform variable
    rank: int | None = None  # rank of its question in the wave
    item: int | None = None  # rank of the item or option, None for a whole question
    other: bool = False
    role: str | None = None  # platform role
    item_key: int | None = None  # the item of the wave-2 list (grid), stable across waves


def wave_questions(wave: int) -> list[Question]:
    return [q for q in QUESTIONS if wave in q.waves]


def grid_items(question: Question, wave: int) -> list[tuple[int, str]]:
    """(item key, text) of a grid in a wave: the key is the rank in wave 2, or 0 for the
    item that wave 2 removed."""
    items = list(enumerate(question.items, start=1))
    if wave == 1 and question.removed_item:
        position, text = question.removed_item
        items.insert(position - 1, (0, text))
    return items


def options(question: Question, wave: int) -> list[str]:
    if wave == 1:
        return [
            question.options_wave1.get(rank, text)
            for rank, text in enumerate(question.options, start=1)
        ]
    return list(question.options)


def columns(wave: int) -> list[Column]:
    found = [
        Column(old if wave == 1 else recent, None, role=role)
        for role, old, recent, _header, _fr in PLATFORM
    ]
    for rank, question in enumerate(wave_questions(wave), start=1):
        base = f"q{rank:04d}"
        if question.kind == "grid":
            for item, (key, _text) in enumerate(grid_items(question, wave), start=1):
                found.append(Column(f"{base}_{item:04d}", question, rank, item, item_key=key))
        elif question.kind == "checkbox":
            for item in range(1, len(question.options) + 1):
                found.append(Column(f"{base}_{item:04d}", question, rank, item))
            found.append(Column(f"{base}_other", question, rank, other=True))
        else:
            found.append(Column(base, question, rank))
    return found


# --- Answers. ------------------------------------------------------------------------------


def _survey_dates(rng: np.random.Generator, n: int, wave: int) -> tuple[list[str], list[str]]:
    """Start and end of each answer, as SurveyMonkey writes them in a .sav: text."""
    start = np.datetime64("2026-03-02T07:00" if wave == 1 else "2026-09-07T07:00")
    starts = start + rng.integers(0, 21 * 24 * 60, size=n).astype("timedelta64[m]")
    starts = starts + rng.integers(0, 60, size=n).astype("timedelta64[s]")
    ends = starts + rng.integers(4 * 60, 25 * 60, size=n).astype("timedelta64[s]")

    def text(stamp: np.datetime64) -> str:
        return pd.Timestamp(stamp).strftime("%m/%d/%Y %I:%M:%S %p")

    return [text(s) for s in starts], [text(e) for e in ends]


def build_wave(wave: int) -> tuple[pd.DataFrame, dict]:
    """The answers of a wave and the metadata of its .sav file."""
    rng = np.random.default_rng(SEED + wave)
    n = N_ROWS[wave]
    strain = rng.normal(size=n)
    data: dict[str, object] = {}
    starts, ends = _survey_dates(rng, n, wave)
    for column in columns(wave):
        if column.role is None:
            continue
        name, role = column.name, column.role
        if role == "collector_name":
            data[name] = ["Lien Web 1"] * n
        elif role == "respondent_id":
            data[name] = (114_000_000_000 + wave * 10_000_000 + np.arange(n) * 37).astype(float)
        elif role == "collector_id":
            data[name] = np.full(n, 400_000_000.0 + wave)
        elif role == "start_date":
            data[name] = starts
        elif role == "end_date":
            data[name] = ends
        elif role == "ip_address":
            data[name] = [f"192.0.2.{int(k)}" for k in rng.integers(1, 255, size=n)]
        elif role == "email":
            # Most links are anonymous: only a few answers came through an email invitation.
            data[name] = [
                f"{CANARY_ID.lower()}-{i:03d}@exemple.org" if i % 9 == 0 else "" for i in range(n)
            ]
        elif role in ("first_name", "last_name"):
            data[name] = [
                f"{CANARY_ID}{role[0].upper()}{i:03d}" if i % 9 == 0 else "" for i in range(n)
            ]
        else:
            data[name] = [""] * n

    for column in columns(wave):
        question = column.question
        if question is None:
            continue
        name = column.name
        if question.kind == "single":
            count = len(question.options)
            weights = np.linspace(1.0, 0.5, count)
            data[name] = rng.choice(np.arange(1, count + 1), size=n, p=weights / weights.sum())
            data[name] = data[name].astype(float)
        elif question.kind == "grid" and question.key == "tensions":
            key = column.item_key or 0
            sign = -1 if key in TENSION_REVERSED else 1
            values = np.round(3 + sign * 0.9 * strain + rng.normal(scale=0.8, size=n))
            data[name] = np.clip(values, 1, 5)
        elif question.kind == "grid":
            values = np.clip(np.round(3.4 - 0.5 * strain + rng.normal(scale=0.9, size=n)), 1, 5)
            draw = rng.random(n)
            values = np.where(draw < 0.06, 6, np.where(draw < 0.10, 7, values))
            data[name] = values.astype(float)
        elif question.kind == "checkbox" and column.other:
            texts = [""] * n
            for k, row in enumerate(np.sort(rng.choice(n, size=9, replace=False))):
                texts[row] = ("Formation des stagiaires", "Inventaire", "Livraisons")[k % 3]
            data[name] = texts
        elif question.kind == "checkbox":
            share = 0.25 + 0.1 * ((column.item or 1) % 4)
            data[name] = np.where(rng.random(n) < share, 1.0, np.nan)
        elif question.kind == "open":
            texts = [""] * n
            for k, row in enumerate(np.sort(rng.choice(n, size=n // 4, replace=False))):
                text = (
                    "Un chariot a reculé sans signal près de moi",
                    "Le plancher était mouillé à l'entrée",
                    "Rien de particulier ce mois-ci",
                )[k % 3]
                texts[row] = f"{text} ({CANARY_TEXT}-{row + 1:03d})"
            data[name] = texts
        else:  # hidden: the participant's code, a family code and invented initials
            letters = rng.choice(list(FAMILY_LETTERS), size=(n, 2))
            data[name] = [
                f"F{100 + (i // 2):03d}-{a}{b}" for i, (a, b) in enumerate(letters.tolist())
            ]
    names = [c.name for c in columns(wave)]
    df = pd.DataFrame({name: data[name] for name in names})
    return df, _sav_metadata(wave, df)


def _sav_metadata(wave: int, df: pd.DataFrame) -> dict:
    labels, value_labels, measure, formats = {}, {}, {}, {}
    for column in columns(wave):
        name, question = column.name, column.question
        string = not pd.api.types.is_numeric_dtype(df[name])
        if question is None:
            labels[name] = name
            measure[name] = "nominal"
            if column.role in ("start_date", "end_date"):
                formats[name] = f"A{DATE_WIDTH[wave]}"
            elif string:
                formats[name] = "A100"
            else:
                formats[name] = "F15.0"
            continue
        measure[name] = question.measure if question.kind == "grid" else "nominal"
        formats[name] = "A100" if string else "F8.2"
        if question.kind == "grid":
            item_texts = dict(grid_items(question, wave))
            labels[name] = item_texts[column.item_key or 0]
            value_labels[name] = {
                float(code): text for code, text in enumerate(question.options, start=1)
            }
        elif question.kind == "checkbox" and column.other:
            labels[name] = OTHER_LABEL
        elif question.kind == "checkbox":
            labels[name] = question.text
            value_labels[name] = {1.0: question.options[(column.item or 1) - 1]}
        elif question.kind == "single":
            labels[name] = question.text
            value_labels[name] = {
                float(code): text for code, text in enumerate(options(question, wave), start=1)
            }
        else:
            labels[name] = question.text
    return {
        "column_labels": labels,
        "variable_value_labels": value_labels,
        "variable_measure": measure,
        "variable_format": formats,
    }


# --- Names: what the team gives, and the renamed wave 1. -----------------------------------


def expected_names(wave: int, suffix: str) -> dict[str, str]:
    """The names a person accepts (D-050 for the platform variables, prefixes and stems).

    In wave 2 the items of the Likert grid keep the name of the same item in wave 1, so the
    items after the removed one skip its number (`eft_11` is the tenth item of wave 2).
    """
    french = {old: fr for _role, old, _recent, _header, fr in PLATFORM}
    french |= {recent: fr for _role, _old, recent, _header, fr in PLATFORM}
    names = {}
    for column in columns(wave):
        question = column.question
        if question is None:
            names[column.name] = french[column.name] + suffix
        elif question.kind == "grid":
            # The item's rank in wave 1, the wave that set the names.
            ranks = {key: rank for rank, (key, _t) in enumerate(grid_items(question, 1), 1)}
            rank = ranks[column.item_key] if 1 in question.waves else column.item
            names[column.name] = f"{question.stem}_{rank}{suffix}"
        elif question.kind == "checkbox" and column.other:
            names[column.name] = f"{question.stem}_autre_txt{suffix}"
        elif question.kind == "checkbox":
            names[column.name] = f"{question.stem}_{column.item}{suffix}"
        else:
            names[column.name] = question.stem + suffix
    return names


def write_documented_copy(wave: int, path: Path) -> None:
    """Wave 1 as the team left it: renamed, with its "Ne sais pas" and "Préfère ne pas
    répondre" codes declared missing, its dates still text."""
    df, meta = build_wave(wave)
    names = expected_names(wave, "_t1")
    renamed = {
        "column_labels": {names[k]: v for k, v in meta["column_labels"].items()},
        "variable_value_labels": {names[k]: v for k, v in meta["variable_value_labels"].items()},
        "variable_measure": {names[k]: v for k, v in meta["variable_measure"].items()},
        "variable_format": {names[k]: v for k, v in meta["variable_format"].items()},
        "missing_ranges": {
            names[c.name]: [6.0, 7.0]
            for c in columns(wave)
            if c.question is not None and c.question.key == "milieu"
        },
    }
    common.write_sav(df.rename(columns=names), renamed, path)


def write_name_table(wave: int, path: Path) -> None:
    """The table of names of D-052: UTF-8, a header, one line per variable."""
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["nom_origine", "nouveau_nom"])
        writer.writerows(expected_names(wave, "_t1").items())


# --- The export with two header rows (.xlsx and .csv). -------------------------------------


def export_rows(wave: int) -> list[list[object]]:
    """The rows of SurveyMonkey's Excel or CSV export: the question once above its first
    column, the item, option or "Response" below, then answers as text, never codes."""
    df, meta = build_wave(wave)
    # The old exports title the platform columns ("Respondent ID"); the recent ones use the
    # recent names themselves (seen in the real exports).
    headers = {
        old if wave == 1 else recent: (header if wave == 1 else recent) if header else None
        for _r, old, recent, header, _f in PLATFORM
    }
    first, second, kept = [], [], []
    seen: set[int] = set()
    for column in columns(wave):
        if column.question is None:
            if headers[column.name] is None:  # the collector's name is not in this export
                continue
            first.append(headers[column.name])
            second.append(None)
        else:
            question = column.question
            first.append(None if column.rank in seen else question.text)
            seen.add(column.rank)
            if question.kind == "grid":
                second.append(dict(grid_items(question, wave))[column.item_key or 0])
            elif column.other:
                second.append(OTHER_LABEL)
            elif question.kind == "checkbox":
                second.append(question.options[(column.item or 1) - 1])
            elif question.kind == "single":
                second.append("Response")
            else:
                second.append("Open-Ended Response")
        kept.append(column.name)
    rows: list[list[object]] = [first, second]
    value_labels = meta["variable_value_labels"]
    for record in df[kept].itertuples(index=False):
        row = []
        for name, value in zip(kept, record, strict=True):
            if value is None or (isinstance(value, float) and np.isnan(value)) or value == "":
                row.append(None)
            elif name in value_labels:
                row.append(value_labels[name][float(value)])
            elif isinstance(value, float):
                row.append(int(value))
            else:
                row.append(value)
        rows.append(row)
    return rows


def write_export_xlsx(wave: int, path: Path) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet"
    for row in export_rows(wave):
        sheet.append(row)
    workbook.properties.created = common.XLSX_FIXED_TIME
    workbook.properties.modified = common.XLSX_FIXED_TIME
    workbook.save(path)
    _fix_zip_times(path)


def _fix_zip_times(path: Path) -> None:
    """As common.write_xlsx: fixed times in the zip entries, so that the bytes are stable."""
    with zipfile.ZipFile(path) as archive:
        entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for info, data in entries:
            if info.filename == "docProps/core.xml":
                data = re.sub(
                    rb"(<dcterms:modified[^>]*>)[^<]*", rb"\g<1>2026-01-01T00:00:00Z", data
                )
            fixed = zipfile.ZipInfo(info.filename, date_time=common.XLSX_FIXED_TIME.timetuple()[:6])
            fixed.compress_type = zipfile.ZIP_DEFLATED
            fixed.create_system = 0
            archive.writestr(fixed, data)


def write_export_csv(wave: int, path: Path) -> None:
    rows = [["" if cell is None else cell for cell in row] for row in export_rows(wave)]
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        csv.writer(stream, lineterminator="\r\n").writerows(rows)


# --- The questionnaire of wave 2. ----------------------------------------------------------

INTRODUCTION = (
    "Cette étude est entièrement fictive : elle sert à vérifier un outil de documentation des "
    "données. Elle comprend l'Échelle fictive des tensions au travail (EFT)."
)
CONTACT = (
    f"Responsable : Mme Alix {CANARY_CONSENT}-Exemple, Laboratoire fictif du travail. "
    f"Pour nous joindre : {CANARY_CONSENT.lower()}@exemple.org."
)


def write_questionnaire_txt(path: Path) -> None:
    """As copied from a word processor: numbered questions, options below, tab-separated
    column titles above the unnumbered items of a grid."""
    lines = ["Étude fictive sur la vie au travail", "", INTRODUCTION, "", CONTACT, ""]
    number = 0
    for question in wave_questions(2):
        if question.kind == "hidden":
            continue
        number += 1
        lines.append(f"{number}. {question.text}")
        if question.kind == "grid":
            lines.append("\t" + "\t".join(question.options))
            lines += [item + "\t" * len(question.options) for item in question.items]
        elif question.kind == "checkbox":
            lines += [*question.options, OTHER_OPTION]
        else:
            lines += list(question.options)
        lines.append("")
    lines.append("Merci de votre participation !")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


# The PDF, laid out as SurveyMonkey prints a survey: unnumbered questions in bold, options
# indented, grid column titles narrow and stacked over up to three lines, aligned on their
# last line just above the items.
_HEADER_WRAP = 10


def _pdf_pages() -> list[bytes]:
    page_height, margin = common._PAGE_HEIGHT, common._MARGIN
    pages, stream, y = [], b"", page_height - margin

    def new_page() -> None:
        nonlocal stream, y
        stream += common._show("F1", 8, common._PAGE_WIDTH / 2 - 10, 30, f"Page {len(pages) + 1}")
        pages.append(stream)
        stream, y = b"", page_height - margin

    def write(font: str, size: int, x: float, text: str, wrap: int, leading: int) -> None:
        nonlocal stream, y
        for part in common._wrap(text, wrap):
            stream += common._show(font, size, x, y, part)
            y -= leading

    write("F2", 16, margin, "Étude fictive sur la vie au travail", 60, 22)
    y -= 8
    write("F1", 10, margin, INTRODUCTION, 95, 13)
    y -= 8
    write("F1", 10, margin, CONTACT, 95, 13)
    new_page()
    for question in wave_questions(2):
        if question.kind == "hidden":
            continue
        if y < 260:
            new_page()
        write("F2", 10, margin, question.text, 85, 13)
        y -= 4
        if question.kind == "grid":
            x0 = 260
            step = (common._PAGE_WIDTH - margin - x0) / len(question.options)
            stacked = [common._wrap(option, _HEADER_WRAP) for option in question.options]
            height = max(len(parts) for parts in stacked)
            for column, parts in enumerate(stacked):
                top = height - len(parts)  # aligned on the last line
                for k, part in enumerate(parts):
                    stream += common._show("F1", 8, x0 + column * step, y - (top + k) * 9, part)
            y -= height * 9 + 6
            for item in question.items:
                write("F1", 9, margin, item, 40, 12)
                y -= 4
        else:
            listed = list(question.options)
            if question.kind == "checkbox":
                listed.append(OTHER_OPTION)
            for option in listed:
                write("F1", 10, margin + 15, option, 80, 13)
            if question.kind == "open":
                y -= 26  # the empty answer box
        y -= 10
    write("F1", 10, margin, "Merci de votre participation !", 95, 13)
    new_page()
    return pages


def write_questionnaire_pdf(path: Path) -> None:
    pages = _pdf_pages()
    first_page = 5
    kids = b" ".join(b"%d 0 R" % (first_page + 2 * i) for i in range(len(pages)))
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, len(pages)),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
    ]
    for i, content in enumerate(pages):
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %d %d] "
            b"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents %d 0 R >>"
            % (common._PAGE_WIDTH, common._PAGE_HEIGHT, first_page + 2 * i + 1)
        )
        objects.append(b"<< /Length %d >>\nstream\n%sendstream" % (len(content), content))
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n%s\nendobj\n" % (number, body)
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref,
    )
    path.write_bytes(bytes(out))


# --- The answer key. -----------------------------------------------------------------------


def answer_key() -> dict:
    """Groups, links, names and differences between waves, for the tests and the bench."""
    waves = {}
    for wave in (1, 2):
        groups, links, structure = [], {}, {}
        number = 0
        by_rank: dict[int, list[Column]] = {}
        for column in columns(wave):
            if column.question is not None:
                by_rank.setdefault(column.rank or 0, []).append(column)
        for rank, members in by_rank.items():
            question = members[0].question
            if question.kind != "hidden":
                number += 1
            for column in members:
                structure[column.name] = {
                    "question": rank,
                    "item": column.item,
                    "other": column.other,
                    "kind": question.kind,
                }
                if question.kind == "hidden":
                    links[column.name] = "none"
                elif question.kind == "grid":
                    links[column.name] = f"Q{number}.r{column.item}"
                elif question.kind == "checkbox":
                    option = len(question.options) + 1 if column.other else column.item
                    links[column.name] = f"Q{number}.o{option}"
                else:
                    links[column.name] = f"Q{number}"
            if question.kind == "grid":
                groups.append({"kind": "scale", "members": [c.name for c in members]})
            elif question.kind == "checkbox":
                groups.append(
                    {
                        "kind": "multiple_response",
                        "members": [c.name for c in members if not c.other],
                        "attached": [c.name for c in members if c.other],
                    }
                )
        for column in columns(wave):
            if column.question is None:
                links[column.name] = "none"
        prefixes = {
            f"q{c.rank:04d}": c.question.stem
            for c in columns(wave)
            if c.question is not None and c.question.kind == "grid"
        }
        stems = {
            f"q{c.rank:04d}": c.question.stem
            for c in columns(wave)
            if c.question is not None and c.question.kind != "grid"
        }
        waves[f"t{wave}"] = {
            "sav": f"{STEM}-t{wave}_surveymonkey.sav",
            "n_rows": N_ROWS[wave],
            "platform_variables": [c.name for c in columns(wave) if c.question is None],
            "structure": structure,
            "groups": groups,
            "links": links,
            "prefixes": prefixes,
            "stems": stems,
            "names": expected_names(wave, f"_t{wave}"),
        }
    waves["t1"]["xlsx"] = f"{STEM}-t1_surveymonkey.xlsx"
    t2 = waves["t2"]
    t2 |= {
        "xlsx": f"{STEM}-t2_surveymonkey.xlsx",
        "csv": f"{STEM}-t2_surveymonkey.csv",
        "questionnaire_txt": f"{QUESTIONNAIRE_NAME}.txt",
        "questionnaire_pdf": f"{QUESTIONNAIRE_NAME}.pdf",
        "questions": [
            {
                "id": f"Q{n}",
                "kind": q.kind,
                "n_rows": len(q.items),
                "n_options": len(q.options) + (1 if q.kind == "checkbox" else 0),
            }
            for n, q in enumerate([q for q in wave_questions(2) if q.kind != "hidden"], 1)
        ],
    }
    t1_names = {c.item_key: c.name for c in columns(1) if c.item_key is not None}
    old_rank = {q.key: r for r, q in enumerate(wave_questions(1), 1)}
    added = [c.name for c in columns(2) if c.question is not None and 1 not in c.question.waves]
    removed = [t1_names[0]]
    changed = [c.name for c in columns(2) if c.question is not None and c.question.options_wave1]
    pairs = {}
    for column in columns(2):
        question = column.question
        if question is None:
            index = [recent for _r, _o, recent, _h, _f in PLATFORM].index(column.name)
            pairs[column.name] = PLATFORM[index][1]
        elif 1 not in question.waves:
            continue
        elif question.kind == "grid":
            pairs[column.name] = t1_names[column.item_key]
        else:
            suffix = column.name[5:]  # "_0003", "_other" or ""
            pairs[column.name] = f"q{old_rank[question.key]:04d}{suffix}"
    return {
        "version": 1,
        "description": (
            "Base fictive au format SurveyMonkey (v0.7) : structure, groupes, rattachements, "
            "noms attendus et écarts entre les vagues. Tout est inventé."
        ),
        "waves": waves,
        "t1_renamed": {
            "documented_copy": f"{STEM}-t1-documente.sav",
            "name_table": f"{STEM}-t1-correspondance.csv",
        },
        "between_waves": {
            "pairs_t2_to_t1": pairs,
            "added": added,
            "removed": removed,
            "value_labels_changed": changed,
        },
        "canaries": [CANARY_ID, CANARY_TEXT, CANARY_CONSENT],
    }


def write_answer_key(path: Path) -> None:
    text = json.dumps(answer_key(), indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def write_all(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for wave in (1, 2):
        df, meta = build_wave(wave)
        path = out_dir / f"{STEM}-t{wave}_surveymonkey.sav"
        common.write_sav(df, meta, path)
        paths.append(path)
    writers = (
        (f"{STEM}-t1-documente.sav", lambda p: write_documented_copy(1, p)),
        (f"{STEM}-t1-correspondance.csv", lambda p: write_name_table(1, p)),
        (f"{STEM}-t1_surveymonkey.xlsx", lambda p: write_export_xlsx(1, p)),
        (f"{STEM}-t2_surveymonkey.xlsx", lambda p: write_export_xlsx(2, p)),
        (f"{STEM}-t2_surveymonkey.csv", lambda p: write_export_csv(2, p)),
        (f"{QUESTIONNAIRE_NAME}.txt", write_questionnaire_txt),
        (f"{QUESTIONNAIRE_NAME}.pdf", write_questionnaire_pdf),
        (ANSWER_KEY_NAME, write_answer_key),
    )
    for name, writer in writers:
        path = out_dir / name
        writer(path)
        paths.append(path)
    return paths


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Génère la base fictive au format SurveyMonkey (v0.7)."
    )
    parser.add_argument("out_dir", nargs="?", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    for path in write_all(args.out_dir):
        print(path)


if __name__ == "__main__":
    main()
