"""Generate the fictional databases used by the examples and the tests.

Everything here is invented: a sleep study of 200 fictional participants, generated from a
fixed seed so that every run writes byte-identical files. The database contains deliberate
traps (reversed items, undeclared missing codes, identifiers, free text, ...) listed in TRAPS,
and canary strings (CANARIES) that must never reach the model, the project file or an export.

Usage (from the repository root):
    uv run python scripts/generer_bases_fictives.py [output_folder]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

SEED = 20261013
N_ROWS = 200
BASE_NAME = "etude-sommeil"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"

# Unique strings placed in identifiers and free text. A privacy test fails if any of them
# shows up in a message to the model, in a project file or in an export.
CANARY_ID = "ZQXID"
CANARY_MAIL = "zqxmail"
CANARY_TEXT = "ZQXTXT"
CANARIES = (CANARY_ID, CANARY_MAIL, CANARY_TEXT)

# Header bytes of a .sav file that hold its creation date and time (SPSS system file layout).
SAV_DATE_SLICE = slice(92, 101)
SAV_TIME_SLICE = slice(101, 109)
SAV_FIXED_DATE = b"01 Jan 26"
SAV_FIXED_TIME = b"00:00:00"

SLEEP_ITEMS = [f"sommeil_q{i}" for i in range(1, 9)]
ANXIETY_ITEMS = [f"anx{i}" for i in range(1, 8)]
# One variable per option of a "tick all that apply" question: 1 when ticked, empty if not.
AID_ITEMS = ["aide_medicament", "aide_naturel", "aide_tcc", "aide_aucune"]
# A language typed by hand (v0.2, step 7): the same answer written in several ways. The two
# rare spellings of "Créole" are fewer than 5 each: hidden, and never to be revealed.
HOME_LANGUAGE = {
    "Français": 110,
    "français": 25,
    "Francais": 12,
    "Anglais": 30,
    "anglais": 9,
    "Espagnol": 7,
    "Créole": 3,
    "créole": 2,
    "": 2,
}

COLUMN_ORDER = [
    "id_participant",
    "courriel",
    "date_passation",
    "date_naissance",
    "age",
    "genre",
    "vague",
    *SLEEP_ITEMS,
    "anx1",
    "anx2",
    "anx3",
    "anx4",
    "heures_sommeil",
    "heures_sommeil_2",
    "nb_reveils",
    *AID_ITEMS,
    "anx5",
    "anx6",
    "anx7",
    "satisfaction_globale",
    "taille_cm",
    "q_retiree",
    "langue_maison",
    "commentaire",
]

# What each trap is and where it is. Tests check that every trap is really in the files;
# later steps check that the tool detects them.
TRAPS = {
    "likely_identifier": ["id_participant", "courriel"],
    "quasi_identifier": ["date_naissance"],
    "free_text": ["commentaire"],
    "reversed_items": ["sommeil_q3", "sommeil_q6"],
    "unlabeled_code": {"sommeil_q3": 9},
    "undeclared_sentinel": {"age": 999, "nb_reveils": -9},
    "declared_missing": {**{item: -9 for item in ANXIETY_ITEMS}, "genre": 9},
    "unused_label": {"satisfaction_globale": 99},
    "small_count": {"genre": 3},
    "constant": ["vague"],
    "all_missing": ["q_retiree"],
    "duplicate_column": ["heures_sommeil", "heures_sommeil_2"],
    "mixed_types": ["taille_cm"],
    "no_file_label": ["sommeil_q7"],
    "non_contiguous_scale": ANXIETY_ITEMS,
    "decimal": ["heures_sommeil"],
    "checkbox": AID_ITEMS,
    "spelling_variants": {
        "langue_maison": [["Français", "français", "Francais"], ["Anglais", "anglais"]],
    },
    "hidden_variants": {"langue_maison": ["Créole", "créole"]},
}

LIKERT_5 = {1: "Pas du tout", 2: "Un peu", 3: "Moyennement", 4: "Beaucoup", 5: "Extrêmement"}
FREQ_4 = {0: "Jamais", 1: "Parfois", 2: "Souvent", 3: "Presque toujours", -9: "Refus"}

COLUMN_LABELS = {
    "id_participant": "Identifiant participant",
    "courriel": "Courriel",
    "date_passation": "Date passation",
    "date_naissance": "DDN",
    "age": "Age",
    "genre": "Genre",
    "vague": "Vague",
    "sommeil_q1": "Q1 endormissement",
    "sommeil_q2": "Q2 sommeil reparateur",
    "sommeil_q3": "Q3 reveils nocturnes",
    "sommeil_q4": "Q4 satisf sommeil",
    "sommeil_q5": "Q5 energie matin",
    "sommeil_q6": "Q6 somnolence jour",
    "sommeil_q7": None,
    "sommeil_q8": "Q8 routine",
    "anx1": "ANX inquiet",
    "anx2": "ANX tendu",
    "anx3": "ANX controle inquietude",
    "anx4": "ANX agite",
    "heures_sommeil": "Nb heures sommeil (moy)",
    "heures_sommeil_2": "Nb heures sommeil (moy)",
    "nb_reveils": "Nb reveils / nuit",
    "aide_medicament": "Aide sommeil: medicament",
    "aide_naturel": "Aide sommeil: produit naturel",
    "aide_tcc": "Aide sommeil: TCC",
    "aide_aucune": "Aide sommeil: aucune",
    "anx5": "ANX irritable",
    "anx6": "ANX peur",
    "anx7": "ANX difficulte relaxer",
    "satisfaction_globale": "Satisfaction globale 0-10",
    "taille_cm": "Taille (cm)",
    "q_retiree": "Question retiree v2",
    "langue_maison": "Langue maison",
    "commentaire": "Commentaires",
}

COMMENT_TEMPLATES = [
    "Je dors très mal depuis le déménagement. Réf {canary}",
    "Rien à ajouter ; merci pour l'étude ({canary}).",
    "Mon conjoint ronfle, c'est \"l'enfer\" la nuit {canary}",
    "Le questionnaire était long.\nJ'ai répondu au mieux. {canary}",
    "Travail de nuit en alternance — horaires très variables {canary}",
]


def build_dataset() -> tuple[pd.DataFrame, dict]:
    """Return the fictional database and its SPSS metadata, always the same for SEED."""
    rng = np.random.default_rng(SEED)
    n = N_ROWS
    sleep = rng.normal(size=n)
    anxiety = -0.5 * sleep + rng.normal(scale=0.85, size=n)

    data: dict[str, object] = {}
    data["id_participant"] = [f"{CANARY_ID}-{i:04d}" for i in range(1, n + 1)]
    data["courriel"] = [f"{CANARY_MAIL}{i:04d}@example.org" for i in range(1, n + 1)]

    start = dt.datetime(2026, 1, 5, 8, 0)
    offsets = rng.integers(0, 150 * 24 * 60, size=n)
    passation = [start + dt.timedelta(minutes=int(m)) for m in offsets]
    data["date_passation"] = passation

    age = rng.integers(18, 76, size=n).astype(float)
    birth = [
        (p - dt.timedelta(days=int(a * 365.25 + d))).date()
        for p, a, d in zip(passation, age, rng.integers(0, 365, size=n), strict=True)
    ]
    data["date_naissance"] = birth
    age[rng.choice(n, size=3, replace=False)] = 999
    data["age"] = age

    genre = rng.choice([1.0, 2.0], size=n, p=[0.55, 0.45])
    picked = rng.choice(n, size=6, replace=False)
    genre[picked[:2]] = 3
    genre[picked[2:]] = 9
    data["genre"] = genre
    data["vague"] = np.ones(n)

    reversed_items = set(TRAPS["reversed_items"])
    for item in SLEEP_ITEMS:
        sign = -1.0 if item in reversed_items else 1.0
        values = np.clip(np.round(3 + sign * sleep + rng.normal(scale=0.8, size=n)), 1, 5)
        values[rng.random(n) < 0.03] = np.nan
        data[item] = values
    data["sommeil_q3"][rng.choice(n, size=3, replace=False)] = 9

    for item in ANXIETY_ITEMS:
        values = np.clip(np.round(1.2 + 0.8 * anxiety + rng.normal(scale=0.6, size=n)), 0, 3)
        values[rng.random(n) < 0.02] = -9
        data[item] = values

    hours = np.clip(np.round(7 + 0.8 * sleep + rng.normal(scale=0.7, size=n), 1), 3.5, 11)
    data["heures_sommeil"] = hours
    data["heures_sommeil_2"] = hours.copy()

    wakeups = np.clip(rng.poisson(1.5, size=n), 0, 10).astype(float)
    wakeups[rng.choice(n, size=4, replace=False)] = -9
    data["nb_reveils"] = wakeups

    satisfaction = np.clip(np.round(6 + 1.5 * sleep + rng.normal(scale=1.5, size=n)), 0, 10)
    data["satisfaction_globale"] = satisfaction

    height = np.round(rng.normal(170, 9, size=n)).astype(int).astype(str).astype(object)
    height[rng.choice(n, size=7, replace=False)] = "NSP"
    data["taille_cm"] = list(height)
    data["q_retiree"] = np.full(n, np.nan)

    comments = [""] * n
    for k, row in enumerate(np.sort(rng.choice(n, size=60, replace=False))):
        template = COMMENT_TEMPLATES[k % len(COMMENT_TEMPLATES)]
        comments[row] = template.format(canary=f"{CANARY_TEXT}-{row + 1:04d}")
    data["commentaire"] = comments

    # Drawn last, so that the values of every other column stay as they were before.
    none_used = rng.random(n) < 0.45
    for item, share in zip(AID_ITEMS[:-1], (0.25, 0.35, 0.12), strict=True):
        data[item] = np.where(~none_used & (rng.random(n) < share), 1.0, np.nan)
    ticked = np.zeros(n, dtype=bool)
    for item in AID_ITEMS[:-1]:
        ticked |= data[item] == 1
    data["aide_aucune"] = np.where(~ticked, 1.0, np.nan)

    languages = [text for text, count in HOME_LANGUAGE.items() for _ in range(count)]
    data["langue_maison"] = list(rng.permutation(np.array(languages, dtype=object)))

    df = pd.DataFrame({name: data[name] for name in COLUMN_ORDER})

    value_labels = {item: LIKERT_5 for item in SLEEP_ITEMS}
    value_labels.update({item: FREQ_4 for item in ANXIETY_ITEMS})
    value_labels["genre"] = {
        1: "Femme",
        2: "Homme",
        3: "Autre identité",
        9: "Préfère ne pas répondre",
    }
    value_labels["vague"] = {1: "Vague 1"}
    value_labels["satisfaction_globale"] = {
        0: "Pas du tout satisfait",
        10: "Tout à fait satisfait",
        99: "Ne sait pas",
    }

    measure = {name: "scale" for name in COLUMN_ORDER}
    measure.update({item: "ordinal" for item in SLEEP_ITEMS + ANXIETY_ITEMS})
    measure.update(
        {
            name: "nominal"
            for name in ["id_participant", "courriel", "genre", "vague", "taille_cm", "commentaire"]
        }
    )
    measure.update({item: "nominal" for item in AID_ITEMS})
    formats = {
        "age": "F3.0",
        "genre": "F1.0",
        "vague": "F1.0",
        **{item: "F1.0" for item in SLEEP_ITEMS},
        **{item: "F2.0" for item in ANXIETY_ITEMS},
        "heures_sommeil": "F4.1",
        "heures_sommeil_2": "F4.1",
        "nb_reveils": "F2.0",
        **{item: "F1.0" for item in AID_ITEMS},
        "satisfaction_globale": "F2.0",
        "q_retiree": "F1.0",
    }
    meta = {
        "file_label": "Etude sommeil (fictive)",
        "column_labels": COLUMN_LABELS,
        "variable_value_labels": value_labels,
        "missing_ranges": {name: [code] for name, code in TRAPS["declared_missing"].items()},
        "variable_measure": measure,
        "variable_format": formats,
    }
    return df, meta


def write_sav(df: pd.DataFrame, meta: dict, path: Path) -> None:
    """Write the .sav file, then fix its creation timestamp so that the bytes are stable."""
    pyreadstat.write_sav(df, path, **meta)
    content = bytearray(path.read_bytes())
    if not re.fullmatch(rb"\d\d [A-Z][a-z]{2} \d\d", content[SAV_DATE_SLICE]):
        raise ValueError(f"Unexpected .sav header layout in {path}")
    content[SAV_DATE_SLICE] = SAV_FIXED_DATE
    content[SAV_TIME_SLICE] = SAV_FIXED_TIME
    path.write_bytes(bytes(content))


def _cell(value: object, decimal: str) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    if isinstance(value, dt.datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, float | np.floating):
        text = str(int(value)) if float(value).is_integer() else repr(float(value))
        return text.replace(".", decimal)
    return str(value)


DTA_FIXED_TIMESTAMP = b"<timestamp>\x1101 Jan 2026 00:00</timestamp>"
XLSX_FIXED_TIME = dt.datetime(2026, 1, 1)


def write_dta(df: pd.DataFrame, meta: dict, path: Path) -> None:
    """Write the Stata file (v0.2, step 8), then fix its timestamp so that the bytes are
    stable. Stata has no user-defined missing values like SPSS: -9 stays a value."""
    pyreadstat.write_dta(
        df,
        path,
        file_label=meta["file_label"],
        column_labels=meta["column_labels"],
        variable_value_labels=meta["variable_value_labels"],
        version=15,
    )
    content = path.read_bytes()
    stamp = re.search(rb"<timestamp>\x11[^<]{17}</timestamp>", content)
    if stamp is None:
        raise ValueError(f"Unexpected .dta header layout in {path}")
    path.write_bytes(content[: stamp.start()] + DTA_FIXED_TIMESTAMP + content[stamp.end() :])


def write_xlsx(df: pd.DataFrame, path: Path) -> None:
    """Write an Excel workbook as a team would type it: names in the first row, one sheet,
    no labels. Dates are real date cells; the workbook bytes are made stable."""
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "donnees"
    sheet.append(list(df.columns))
    for record in df.itertuples(index=False):
        row = []
        for value in record:
            if value is None or (isinstance(value, float) and np.isnan(value)) or value == "":
                row.append(None)
            elif isinstance(value, float | np.floating):
                row.append(int(value) if float(value).is_integer() else float(value))
            elif isinstance(value, pd.Timestamp):
                row.append(value.to_pydatetime())
            else:
                row.append(value)
        sheet.append(row)
    workbook.properties.created = XLSX_FIXED_TIME
    workbook.properties.modified = XLSX_FIXED_TIME
    workbook.save(path)
    # Zip entries carry the time of writing: rewrite them with a fixed one.
    with zipfile.ZipFile(path) as archive:
        entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for info, data in entries:
            if info.filename == "docProps/core.xml":  # openpyxl sets "modified" when saving
                data = re.sub(
                    rb"(<dcterms:modified[^>]*>)[^<]*", rb"\g<1>2026-01-01T00:00:00Z", data
                )
            if info.filename.startswith("xl/worksheets/"):
                # On Windows a line break in a cell is written CR LF; the data keeps LF,
                # the same on every computer.
                data = data.replace(b"\r\n", b"\n")
            fixed = zipfile.ZipInfo(info.filename, date_time=XLSX_FIXED_TIME.timetuple()[:6])
            fixed.compress_type = zipfile.ZIP_DEFLATED
            fixed.create_system = 0  # as on Windows: Python marks the system otherwise (v0.5)
            archive.writestr(fixed, data)


def write_csv(
    df: pd.DataFrame,
    path: Path,
    *,
    encoding: str,
    delimiter: str,
    decimal: str,
    line_end: str,
) -> None:
    """Write a CSV the way a given program would, without depending on pandas' formatting."""
    rows = [list(df.columns)]
    for record in df.itertuples(index=False):
        rows.append([_cell(value, decimal) for value in record])
    with path.open("w", encoding=encoding, newline="") as stream:
        writer = csv.writer(stream, delimiter=delimiter, lineterminator=line_end)
        writer.writerows(rows)


# --- The questionnaire of the fictional study (v0.2, step 1). ---
#
# Pages of paragraphs, questions and grids, in the order a participant reads them. Questions
# are not numbered, as in a SurveyMonkey export. Each question or grid row names the
# variables it gives; QUESTIONNAIRE_KEY lists them, and QUESTIONNAIRE_TRAPS what makes the
# questionnaire hard to read. Everything is invented.

QUESTIONNAIRE_NAME = "questionnaire-sommeil"
CANARY_CONSENT = "ZQXQUEST"  # in the consent page: must never reach an export (D-012)

LIKERT_OPTIONS = list(LIKERT_5.values())
FREQ_OPTIONS = [label for code, label in FREQ_4.items() if code >= 0]

QUESTIONNAIRE = [
    [
        ("title", "Étude fictive sur le sommeil et le bien-être"),
        ("heading", "Formulaire d'information et de consentement"),
        (
            "text",
            "Cette étude est entièrement fictive : elle sert à essayer un outil de "
            "documentation des données. Elle comprend le Questionnaire fictif du sommeil "
            "(QFS) et l'Échelle fictive d'anxiété (EFA).",
        ),
        (
            "text",
            f"Équipe de recherche : Dre Zoé {CANARY_CONSENT}-Exemple, Laboratoire fictif du "
            f"sommeil. Pour toute question : {CANARY_CONSENT.lower()}@exemple.org ou "
            "555-0199.",
        ),
        ("question", "Acceptez-vous de participer à cette étude ?", ["Oui", "Non"], []),
    ],
    [
        ("heading", "Renseignements généraux"),
        ("question", "Quelle est votre date de naissance ? (JJ/MM/AAAA)", [], ["date_naissance"]),
        ("question", "Quel âge avez-vous ?", [], ["age"]),
        (
            "question",
            "Quel est votre genre ?",
            ["Femme", "Homme", "Autre identité", "Préfère ne pas répondre"],
            ["genre"],
        ),
        (
            "question",
            "Votre adresse courriel (pour vous envoyer un rappel) :",
            [],
            ["courriel"],
        ),
        ("question", "Quelle est votre taille, en centimètres ?", [], ["taille_cm"]),
    ],
    [
        ("heading", "Votre sommeil"),
        ("text", "Les énoncés suivants forment le Questionnaire fictif du sommeil (QFS)."),
        (
            "grid",
            "Au cours du dernier mois, dans quelle mesure les énoncés suivants "
            "s'appliquent-ils à vous ?",
            LIKERT_OPTIONS,
            [
                ("J'ai de la difficulté à m'endormir le soir.", "sommeil_q1"),
                ("Mon sommeil est réparateur.", "sommeil_q2"),
                (
                    "Je me réveille plusieurs fois pendant la nuit sans pouvoir me "
                    "rendormir facilement.",
                    "sommeil_q3",
                ),
                ("Je suis satisfait.e de la qualité de mon sommeil.", "sommeil_q4"),
                ("J'ai de l'énergie dès le réveil.", "sommeil_q5"),
                ("Je somnole pendant la journée, même après une bonne nuit.", "sommeil_q6"),
                ("J'évite les écrans dans l'heure qui précède le coucher.", "sommeil_q7"),
                ("Je suis une routine régulière avant de me coucher.", "sommeil_q8"),
            ],
        ),
        (
            "question",
            "En moyenne, combien d'heures dormez-vous par nuit ?",
            [],
            ["heures_sommeil", "heures_sommeil_2"],
        ),
        (
            "question",
            "Combien de fois vous réveillez-vous au cours d'une nuit habituelle ?",
            [],
            ["nb_reveils"],
        ),
        (
            "checkbox",
            "Qu'utilisez-vous pour vous aider à dormir ? (Cochez toutes les réponses applicables)",
            [
                ("Un médicament prescrit", "aide_medicament"),
                ("Un produit naturel (tisane, mélatonine)", "aide_naturel"),
                ("Une thérapie cognitivo-comportementale (TCC)", "aide_tcc"),
                ("Rien de cela", "aide_aucune"),
            ],
        ),
        (
            "question",
            "Dans l'ensemble, quelle est votre satisfaction à l'égard de votre sommeil ? "
            "(0 = Pas du tout satisfait, 10 = Tout à fait satisfait)",
            [str(i) for i in range(11)] + ["Ne sait pas"],
            ["satisfaction_globale"],
        ),
    ],
    [
        ("heading", "Votre humeur"),
        ("text", "Les énoncés suivants forment l'Échelle fictive d'anxiété (EFA)."),
        (
            "grid",
            "Au cours des deux dernières semaines, à quelle fréquence avez-vous ressenti ce "
            "qui suit ?",
            FREQ_OPTIONS,
            [
                ("Je me suis senti.e inquiet.e.", "anx1"),
                ("Je me suis senti.e tendu.e.", "anx2"),
                ("J'ai eu du mal à contrôler mes inquiétudes.", "anx3"),
                ("Je me suis senti.e agité.e.", "anx4"),
                ("Je me suis senti.e irritable.", "anx5"),
                ("J'ai eu peur que quelque chose de terrible arrive.", "anx6"),
                ("J'ai eu de la difficulté à me détendre.", "anx7"),
            ],
        ),
        (
            "question",
            "Avez-vous d'autres commentaires sur votre sommeil ?",
            [],
            ["commentaire"],
        ),
        (
            "question",
            "Quelle langue parlez-vous le plus souvent à la maison ?",
            [],
            ["langue_maison"],
        ),
        ("text", "Merci de votre participation !"),
    ],
]


def questionnaire_key(questionnaire: list | None = None) -> dict[str, tuple[int, int, int | None]]:
    """Where each variable is asked: (page, question rank, option or row rank).

    Ranks start at 1; the question rank counts questions, grids and checkbox questions over
    the whole questionnaire. The third value is the grid row or the ticked option, or None
    for a plain question.
    """
    key: dict[str, tuple[int, int, int | None]] = {}
    rank = 0
    for page, elements in enumerate(questionnaire or QUESTIONNAIRE, start=1):
        for kind, *content in elements:
            if kind not in ("question", "grid", "checkbox"):
                continue
            rank += 1
            if kind == "question":
                for name in content[2]:
                    key[name] = (page, rank, None)
            else:
                rows = content[2] if kind == "grid" else content[1]
                for row, (_text, name) in enumerate(rows, start=1):
                    key[name] = (page, rank, row)
    return key


QUESTIONNAIRE_TRAPS = {
    "checkbox_question": AID_ITEMS,  # one variable per option
    "grid": SLEEP_ITEMS + ANXIETY_ITEMS,  # rows of a table, long rows wrapped in the PDF
    "defined_acronyms": {
        "QFS": "Questionnaire fictif du sommeil",
        "EFA": "Échelle fictive d'anxiété",
        "TCC": "thérapie cognitivo-comportementale",
    },
    "acronym_in_name": {"aide_tcc": "TCC"},
    "consent_page_canary": CANARY_CONSENT,
    "question_without_variable": ["Acceptez-vous de participer à cette étude ?"],
    "variables_without_question": ["id_participant", "date_passation", "vague", "q_retiree"],
    "one_question_two_variables": ["heures_sommeil", "heures_sommeil_2"],
    "order_differs_from_file": ["taille_cm"],
    "label_only_in_questionnaire": ["sommeil_q7"],
}


def _questionnaire_lines(elements: list) -> list[tuple[str, str]]:
    """The lines of a page as (style, text), as a word processor would show them."""
    lines: list[tuple[str, str]] = []
    for kind, *content in elements:
        if kind in ("title", "heading", "text"):
            lines += [(kind, content[0]), ("blank", "")]
        elif kind == "question":
            text, options, _names = content
            lines.append(("question", text))
            lines += [("option", option) for option in options]
            lines.append(("blank", ""))
        elif kind == "checkbox":
            text, options = content
            lines.append(("question", text))
            lines += [("option", option) for option, _name in options]
            lines.append(("blank", ""))
        else:  # grid
            text, options, rows = content
            lines.append(("question", text))
            lines.append(("grid_header", "\t" + "\t".join(options)))
            for number, (row, _name) in enumerate(rows, start=1):
                lines.append(("grid_row", f"{number}. {row}" + "\t" * len(options)))
            lines.append(("blank", ""))
    return lines


def write_questionnaire_txt(path: Path, questionnaire: list | None = None) -> None:
    """As copied from a word processor: one line per paragraph, tabs between table cells."""
    out = []
    for elements in questionnaire or QUESTIONNAIRE:
        out += [text for _style, text in _questionnaire_lines(elements)]
    path.write_text("\n".join(out).rstrip("\n") + "\n", encoding="utf-8", newline="\n")


# A minimal PDF written by hand: base fonts, Windows-1252 text, no date, so that every run
# writes the same bytes. Grids are laid out as tables, with long rows wrapped over several
# lines as survey platforms do: the hard case for text extraction.
_PAGE_WIDTH, _PAGE_HEIGHT, _MARGIN = 595, 842, 50
_STYLES = {
    "title": ("F2", 16, 22),
    "heading": ("F2", 13, 18),
    "text": ("F1", 10, 13),
    "question": ("F2", 10, 13),
    "option": ("F1", 10, 13),
    "grid_header": ("F1", 8, 11),
    "grid_row": ("F1", 9, 12),
}
_WRAP = {"title": 60, "heading": 70, "text": 95, "question": 85, "option": 85, "grid_row": 42}
_GRID_COLUMNS_X = 300  # options of a grid start here, one column each


def _wrap(text: str, width: int) -> list[str]:
    words, lines, current = text.split(), [], ""
    for word in words:
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    return [*lines, current] if current else lines


def _pdf_string(text: str) -> bytes:
    raw = text.encode("cp1252")
    return b"(" + raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)") + b")"


def _show(font: str, size: int, x: float, y: float, text: str) -> bytes:
    return b"BT /%s %d Tf %.1f %.1f Td %s Tj ET\n" % (
        font.encode(),
        size,
        x,
        y,
        _pdf_string(text),
    )


def _page_content(elements: list, page_number: int) -> bytes:
    stream = b""
    y = _PAGE_HEIGHT - _MARGIN
    for style, text in _questionnaire_lines(elements):
        if style == "blank":
            y -= 8
            continue
        font, size, leading = _STYLES[style]
        if style == "grid_header":
            options = text.strip("\t").split("\t")
            step = (_PAGE_WIDTH - _MARGIN - _GRID_COLUMNS_X) / len(options)
            for column, option in enumerate(options):
                for k, part in enumerate(_wrap(option, 12)):
                    stream += _show(font, size, _GRID_COLUMNS_X + column * step, y - k * 9, part)
            y -= leading + 9
            continue
        x = _MARGIN + (15 if style == "option" else 0)
        for part in _wrap(text.strip("\t"), _WRAP[style]):
            stream += _show(font, size, x, y, part)
            y -= leading
    stream += _show("F1", 8, _PAGE_WIDTH / 2 - 10, 30, f"Page {page_number}")
    return stream


def write_questionnaire_pdf(path: Path, questionnaire: list | None = None) -> None:
    pages = [
        _page_content(elements, n)
        for n, elements in enumerate(questionnaire or QUESTIONNAIRE, start=1)
    ]
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
            % (_PAGE_WIDTH, _PAGE_HEIGHT, first_page + 2 * i + 1)
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


def write_all(out_dir: Path) -> list[Path]:
    """Write the .sav file, its three CSV variants, the Stata and Excel versions and the
    questionnaire; return their paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    df, meta = build_dataset()
    paths = []

    sav = out_dir / f"{BASE_NAME}.sav"
    write_sav(df, meta, sav)
    paths.append(sav)

    # Plain UTF-8 CSV, as written by most programs.
    variants = {
        f"{BASE_NAME}.csv": dict(encoding="utf-8", delimiter=",", decimal=".", line_end="\n"),
        # Excel in French, "CSV (séparateur : point-virgule)": Windows-1252, decimal comma.
        f"{BASE_NAME}_excel-fr.csv": dict(
            encoding="cp1252", delimiter=";", decimal=",", line_end="\r\n"
        ),
        # Excel in French, "CSV UTF-8": same, with a byte order mark.
        f"{BASE_NAME}_excel-utf8.csv": dict(
            encoding="utf-8-sig", delimiter=";", decimal=",", line_end="\r\n"
        ),
    }
    for name, options in variants.items():
        path = out_dir / name
        write_csv(df, path, **options)
        paths.append(path)

    dta = out_dir / f"{BASE_NAME}.dta"
    write_dta(df, meta, dta)
    paths.append(dta)
    xlsx = out_dir / f"{BASE_NAME}.xlsx"
    write_xlsx(df, xlsx)
    paths.append(xlsx)
    # The SAS file is written from the Stata one by scripts/generer_sas.R (R and haven), which
    # Python cannot do; it is kept in the repository and checked by the tests.

    for suffix, writer in ((".txt", write_questionnaire_txt), (".pdf", write_questionnaire_pdf)):
        path = out_dir / f"{QUESTIONNAIRE_NAME}{suffix}"
        writer(path)
        paths.append(path)
    return paths


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Génère les bases fictives d'exemple.")
    parser.add_argument("out_dir", nargs="?", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    for path in write_all(args.out_dir):
        print(path)


if __name__ == "__main__":
    main()
