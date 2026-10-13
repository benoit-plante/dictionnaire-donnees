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
    "anx5",
    "anx6",
    "anx7",
    "satisfaction_globale",
    "taille_cm",
    "q_retiree",
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
    "anx5": "ANX irritable",
    "anx6": "ANX peur",
    "anx7": "ANX difficulte relaxer",
    "satisfaction_globale": "Satisfaction globale 0-10",
    "taille_cm": "Taille (cm)",
    "q_retiree": "Question retiree v2",
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
    formats = {
        "age": "F3.0",
        "genre": "F1.0",
        "vague": "F1.0",
        **{item: "F1.0" for item in SLEEP_ITEMS},
        **{item: "F2.0" for item in ANXIETY_ITEMS},
        "heures_sommeil": "F4.1",
        "heures_sommeil_2": "F4.1",
        "nb_reveils": "F2.0",
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


def write_all(out_dir: Path) -> list[Path]:
    """Write the .sav file and its three CSV variants; return their paths."""
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
    return paths


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Génère les bases fictives d'exemple.")
    parser.add_argument("out_dir", nargs="?", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    for path in write_all(args.out_dir):
        print(path)


if __name__ == "__main__":
    main()
