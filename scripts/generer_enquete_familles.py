"""Generate the second fictional database: a survey of families (v0.4, step 1).

Everything here is invented. It differs on purpose from the sleep study, on which the tool
was tuned, so that the model bench (`ddict evaluer`) measures the tool on a questionnaire
it has never seen:

- a CSV exported by R: no labels at all, missing cells written "NA";
- questions repeated word for word, once per source of support;
- follow-up questions ("Si oui, ...") with options ticked one variable each;
- acronyms defined in the questionnaire (CPE, CLSC, EFSP) and found in the names;
- a grid coded 0..4, a 0..10 scale, a computed score without any question;
- a variable whose codes do not follow the order of the options (recoded by the team):
  the value labels proposed from the options are then wrong, and the key says so.

The answer key gives, for each variable, where it is asked (`answer_key`), and the true
value labels (`TRUE_VALUE_LABELS`).

Usage (from the repository root):
    uv run python scripts/generer_enquete_familles.py [output_folder]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generer_bases_fictives as common

SEED = 20261015
N_ROWS = 150
BASE_NAME = "enquete-familles"
QUESTIONNAIRE_NAME = "questionnaire-familles"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"
CANARY_ID = "ZQXFAMID"  # in the identifiers
CANARY_TEXT = "ZQXFAMTXT"  # in the free comments
CANARY_CONSENT = "ZQXFAMQUEST"  # in the consent page
CANARIES = (CANARY_ID, CANARY_TEXT)

SATISFACTION = [
    "Très insatisfait·e",
    "Plutôt insatisfait·e",
    "Ni l'un ni l'autre",
    "Plutôt satisfait·e",
    "Très satisfait·e",
]
FREQUENCY = [
    "Jamais",
    "Quelques fois par année",
    "Une fois par mois",
    "Chaque semaine",
    "Chaque jour",
]
STRESS_OPTIONS = ["Jamais", "Rarement", "Parfois", "Souvent", "Toujours"]
STRESS_ITEMS = [f"stress_{i}" for i in range(1, 7)]
SOURCES = [
    ("partenaire", "Votre partenaire"),
    ("grandsparents", "Les grands-parents de l'enfant"),
    ("voisins", "Vos voisins ou vos amis"),
]
REPEATED = "À quelle fréquence cette personne vous apporte-t-elle du soutien ?"

QUESTIONNAIRE = [
    [
        ("title", "Enquête fictive sur les familles et le soutien"),
        ("heading", "Information et consentement"),
        (
            "text",
            "Cette enquête est entièrement fictive : elle sert à essayer un outil de "
            "documentation des données. Elle comprend l'Échelle fictive de stress parental "
            "(EFSP).",
        ),
        (
            "text",
            f"Responsable : M. Alex {CANARY_CONSENT}-Exemple, Groupe fictif sur les familles. "
            f"Pour nous joindre : {CANARY_CONSENT.lower()}@exemple.org ou 555-0123.",
        ),
        ("question", "Acceptez-vous de répondre à cette enquête ?", ["Oui", "Non"], []),
    ],
    [
        ("heading", "Votre famille"),
        (
            "question",
            "Quel est votre lien avec l'enfant ?",
            ["Parent", "Grand-parent", "Tuteur ou tutrice", "Autre"],
            ["lien_enfant"],
        ),
        ("question", "Quel âge a l'enfant ? (en années)", [], ["age_enfant"]),
        ("question", "Combien de personnes vivent dans votre foyer ?", [], ["nb_personnes_foyer"]),
        (
            "question",
            "Quelle langue parlez-vous le plus souvent à la maison ?",
            ["Français", "Anglais", "Autre"],
            ["langue_maison"],
        ),
    ],
    [
        ("heading", "Le soutien que vous recevez"),
        (
            "text",
            "Pour chaque personne, dites votre satisfaction du soutien reçu, puis sa fréquence.",
        ),
        *[
            element
            for name, title in SOURCES
            for element in (
                ("question", title, SATISFACTION, [f"soutien_{name}"]),
                ("question", REPEATED, FREQUENCY, [f"soutien_{name}_freq"]),
            )
        ],
    ],
    [
        ("heading", "Les services"),
        (
            "question",
            "Votre enfant a-t-il fréquenté un service de garde au cours de la dernière année ?",
            ["Oui", "Non"],
            ["garde_utilise"],
        ),
        (
            "checkbox",
            "Si oui, lequel ou lesquels ? (Cochez toutes les réponses applicables)",
            [
                ("Un centre de la petite enfance (CPE)", "type_garde_cpe"),
                ("Une garderie privée", "type_garde_privee"),
                ("Un milieu familial", "type_garde_familial"),
                ("Autre", "type_garde_autre"),
            ],
        ),
        (
            "question",
            "Avez-vous consulté un centre local de services communautaires (CLSC) au cours de la "
            "dernière année ?",
            ["Oui", "Non"],
            ["clsc_consulte"],
        ),
        (
            "checkbox",
            "Si oui, quels professionnels avez-vous rencontrés ? (Cochez toutes les réponses "
            "applicables)",
            [
                ("Travailleur ou travailleuse sociale", "pro_clsc_ts"),
                ("Psychologue", "pro_clsc_psy"),
                ("Infirmière ou infirmier", "pro_clsc_inf"),
            ],
        ),
    ],
    [
        ("heading", "Votre bien-être"),
        ("text", "Les énoncés suivants forment l'Échelle fictive de stress parental (EFSP)."),
        (
            "grid",
            "Au cours des deux dernières semaines, à quelle fréquence avez-vous vécu ce qui suit ?",
            STRESS_OPTIONS,
            [
                ("Je me suis senti·e dépassé·e par mes responsabilités de parent.", "stress_1"),
                ("J'ai manqué de patience avec mon enfant.", "stress_2"),
                ("J'ai eu l'impression de ne pas avoir de temps pour moi.", "stress_3"),
                ("Je me suis inquiété·e pour l'avenir de mon enfant.", "stress_4"),
                ("Je me suis senti·e seul·e dans mon rôle de parent.", "stress_5"),
                ("J'ai eu de la difficulté à me reposer.", "stress_6"),
            ],
        ),
        (
            "question",
            "Dans l'ensemble, êtes-vous satisfait·e de votre vie familiale ? "
            "(0 = pas du tout, 10 = tout à fait)",
            [str(i) for i in range(11)],
            ["satisfaction_vie_familiale"],
        ),
        ("question", "Avez-vous d'autres commentaires ?", [], ["commentaire"]),
        ("text", "Merci de votre participation !"),
    ],
]

COLUMN_ORDER = [
    "id_famille",
    "date_reponse",
    "lien_enfant",
    "age_enfant",
    "nb_personnes_foyer",
    "langue_maison",
    *[c for name, _title in SOURCES for c in (f"soutien_{name}", f"soutien_{name}_freq")],
    "garde_utilise",
    "type_garde_cpe",
    "type_garde_privee",
    "type_garde_familial",
    "type_garde_autre",
    "clsc_consulte",
    "pro_clsc_ts",
    "pro_clsc_psy",
    "pro_clsc_inf",
    *STRESS_ITEMS,
    "stress_total",
    "satisfaction_vie_familiale",
    "commentaire",
]

# How the team coded the answers. langue_maison was recoded in alphabetical order: its
# codes do not follow the order of the options, so labels proposed from them are wrong.
TRUE_VALUE_LABELS = {
    "lien_enfant": {1: "Parent", 2: "Grand-parent", 3: "Tuteur ou tutrice", 4: "Autre"},
    "langue_maison": {1: "Anglais", 2: "Autre", 3: "Français"},
    **{f"soutien_{n}": dict(enumerate(SATISFACTION, start=1)) for n, _t in SOURCES},
    **{f"soutien_{n}_freq": dict(enumerate(FREQUENCY, start=1)) for n, _t in SOURCES},
    "garde_utilise": {1: "Oui", 2: "Non"},
    "clsc_consulte": {1: "Oui", 2: "Non"},
    **{item: dict(enumerate(STRESS_OPTIONS)) for item in STRESS_ITEMS},
    "satisfaction_vie_familiale": {i: str(i) for i in range(11)},
}

TRAPS = {
    "likely_identifier": ["id_famille"],
    "free_text": ["commentaire"],
    "missing_token": "NA",
    "repeated_question": {
        "text": REPEATED,
        "variables": [f"soutien_{n}_freq" for n, _t in SOURCES],
    },
    "follow_up_checkboxes": {
        "garde_utilise": [
            "type_garde_cpe",
            "type_garde_privee",
            "type_garde_familial",
            "type_garde_autre",
        ],
        "clsc_consulte": ["pro_clsc_ts", "pro_clsc_psy", "pro_clsc_inf"],
    },
    "defined_acronyms": {
        "CPE": "centre de la petite enfance",
        "CLSC": "centre local de services communautaires",
        "EFSP": "Échelle fictive de stress parental",
    },
    "acronyms_in_names": {"type_garde_cpe": "CPE", "clsc_consulte": "CLSC", "pro_clsc_ts": "TS"},
    "grid_coded_from_zero": STRESS_ITEMS,
    "codes_not_in_option_order": ["langue_maison"],
    "variables_without_question": ["id_famille", "date_reponse", "stress_total"],
    "consent_page_canary": CANARY_CONSENT,
}


def answer_key() -> dict[str, tuple[int, int, int | None]]:
    """Where each variable is asked: (page, question rank, option or row rank)."""
    return common.questionnaire_key(QUESTIONNAIRE)


def build_dataset() -> pd.DataFrame:
    """The fictional answers, always the same for SEED."""
    rng = np.random.default_rng(SEED)
    n = N_ROWS
    data: dict[str, object] = {}
    data["id_famille"] = [f"{CANARY_ID}-{i:03d}" for i in range(1, n + 1)]
    start = np.datetime64("2026-03-02")
    data["date_reponse"] = [str(start + int(d)) for d in rng.integers(0, 60, size=n)]
    data["lien_enfant"] = rng.choice([1, 2, 3, 4], size=n, p=[0.82, 0.1, 0.05, 0.03]).astype(float)
    data["age_enfant"] = rng.integers(0, 13, size=n).astype(float)
    data["nb_personnes_foyer"] = rng.integers(2, 8, size=n).astype(float)
    data["langue_maison"] = rng.choice([3, 1, 2], size=n, p=[0.78, 0.15, 0.07]).astype(float)

    wellbeing = rng.normal(size=n)
    for name, _title in SOURCES:
        satisfaction = np.clip(
            np.round(3.6 + 0.6 * wellbeing + rng.normal(scale=0.9, size=n)), 1, 5
        )
        frequency = np.clip(np.round(3 + 0.5 * wellbeing + rng.normal(scale=1.1, size=n)), 1, 5)
        missing = rng.random(n) < 0.06
        satisfaction[missing] = np.nan
        frequency[missing] = np.nan
        data[f"soutien_{name}"] = satisfaction
        data[f"soutien_{name}_freq"] = frequency

    garde = np.where(rng.random(n) < 0.7, 1.0, 2.0)
    data["garde_utilise"] = garde
    for name, share in (("cpe", 0.55), ("privee", 0.3), ("familial", 0.25), ("autre", 0.08)):
        ticked = (garde == 1) & (rng.random(n) < share)
        data[f"type_garde_{name}"] = np.where(ticked, 1.0, np.nan)
    clsc = np.where(rng.random(n) < 0.4, 1.0, 2.0)
    data["clsc_consulte"] = clsc
    for name, share in (("ts", 0.45), ("psy", 0.35), ("inf", 0.6)):
        ticked = (clsc == 1) & (rng.random(n) < share)
        data[f"pro_clsc_{name}"] = np.where(ticked, 1.0, np.nan)

    stress = -0.7 * wellbeing + rng.normal(scale=0.6, size=n)
    for item in STRESS_ITEMS:
        data[item] = np.clip(np.round(1.8 + stress + rng.normal(scale=0.7, size=n)), 0, 4)
    data["stress_total"] = sum(data[item] for item in STRESS_ITEMS)
    data["satisfaction_vie_familiale"] = np.clip(
        np.round(7 + 1.4 * wellbeing + rng.normal(scale=1.2, size=n)), 0, 10
    )

    comments = [""] * n
    for k, row in enumerate(np.sort(rng.choice(n, size=25, replace=False))):
        templates = (
            "Le service de garde a beaucoup aidé {c}",
            "Difficile de trouver une place en CPE ; on attend encore ({c}).",
            "Merci pour l'enquête. {c}",
        )
        comments[row] = templates[k % len(templates)].format(c=f"{CANARY_TEXT}-{row + 1:03d}")
    data["commentaire"] = comments
    return pd.DataFrame({name: data[name] for name in COLUMN_ORDER})


def write_csv(df: pd.DataFrame, path: Path) -> None:
    """As R's write.csv would: UTF-8, "," and ".", missing cells written NA."""
    filled = df.astype(object).where(df.notna(), "NA")
    filled["commentaire"] = df["commentaire"]  # an empty comment stays empty
    common.write_csv(filled, path, encoding="utf-8", delimiter=",", decimal=".", line_end="\n")


def write_all(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    csv = out_dir / f"{BASE_NAME}.csv"
    write_csv(build_dataset(), csv)
    paths.append(csv)
    for suffix, writer in (
        (".txt", common.write_questionnaire_txt),
        (".pdf", common.write_questionnaire_pdf),
    ):
        path = out_dir / f"{QUESTIONNAIRE_NAME}{suffix}"
        writer(path, QUESTIONNAIRE)
        paths.append(path)
    return paths


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Génère l'enquête fictive auprès de familles.")
    parser.add_argument("out_dir", nargs="?", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    for path in write_all(args.out_dir):
        print(path)


if __name__ == "__main__":
    main()
