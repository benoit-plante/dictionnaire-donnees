"""Generate the control database of v0.6 (D-042): a fictional study of physical activity.

Generated before any tuning of v0.6 and set aside: it is measured once at the end, for 0.5
and 0.6, to check that the gains do not come from tuning on the three bases of the bench.
It has what the v0.6 is about, in new words:

- questions that share no word with the names of their variables ("Combien pesez-vous ?"
  for `poids_kg`);
- administrative variables without a question: identifier, time stamp, wave;
- a computed score (the sum of the items of a grid) without a question;
- a checkbox question, a follow-up question ("Si oui, ...") and a grid.

Everything is invented. The answer key is `answer_key()`.

Usage (from the repository root):
    uv run python scripts/generer_base_controle.py [output_folder]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generer_bases_fictives as common

SEED = 20261016
N_ROWS = 160
BASE_NAME = "etude-activite"
QUESTIONNAIRE_NAME = "questionnaire-activite"
DEFAULT_OUT_DIR = common.DEFAULT_OUT_DIR
CANARY_ID = "ZQXACTID"
CANARY_TEXT = "ZQXACTTXT"
CANARY_CONSENT = "ZQXACTQUEST"

MOTIVATION = [
    ("Je bouge parce que cela me fait du bien.", "motiv_1"),
    ("Je bouge pour rencontrer d'autres personnes.", "motiv_2"),
    ("Je bouge parce que mon médecin me l'a conseillé.", "motiv_3"),
    ("Je bouge pour avoir plus d'énergie au travail.", "motiv_4"),
    ("Je me sentirais coupable de ne pas bouger.", "motiv_5"),
]
AGREEMENT = [
    "Pas du tout d'accord",
    "Plutôt pas d'accord",
    "Neutre",
    "Plutôt d'accord",
    "Tout à fait d'accord",
]
ACTIVITIES = [
    ("La marche", "pratique_marche"),
    ("Le vélo", "pratique_velo"),
    ("La natation", "pratique_natation"),
    ("Le yoga ou l'étirement", "pratique_yoga"),
    ("Une autre activité", "pratique_autre"),
]

COLUMN_ORDER = [
    "id_repondant",
    "horodatage",
    "vague",
    "annee_naissance",
    "poids_kg",
    "taille_m",
    "jours_actifs",
    "minutes_assis",
    *[name for _text, name in ACTIVITIES],
    "membre_club",
    "club_seances",
    *[name for _text, name in MOTIVATION],
    "score_motivation",
    "forme_satisfaction",
    "remarques",
]

QUESTIONNAIRE = [
    [
        ("title", "Étude fictive sur l'activité physique au quotidien"),
        ("heading", "Information et consentement"),
        (
            "text",
            "Cette étude est entièrement fictive : elle sert à vérifier un outil de "
            "documentation des données. Elle comprend l'Échelle fictive de motivation (EFM).",
        ),
        (
            "text",
            f"Responsable : M. Léo {CANARY_CONSENT}-Exemple, Laboratoire fictif du mouvement. "
            f"Pour nous joindre : {CANARY_CONSENT.lower()}@exemple.org.",
        ),
        ("question", "Consentez-vous à répondre à ce questionnaire ?", ["Oui", "Non"], []),
    ],
    [
        ("heading", "Vous"),
        ("question", "En quelle année êtes-vous né·e ?", [], ["annee_naissance"]),
        ("question", "Combien pesez-vous, en kilogrammes ?", [], ["poids_kg"]),
        ("question", "Combien mesurez-vous, en mètres (par exemple 1,68) ?", [], ["taille_m"]),
    ],
    [
        ("heading", "Votre semaine"),
        (
            "question",
            "Au cours des sept derniers jours, combien de jours avez-vous bougé au moins "
            "30 minutes d'affilée ?",
            [],
            ["jours_actifs"],
        ),
        (
            "question",
            "Un jour de semaine habituel, combien de temps restez-vous sur une chaise ou un "
            "fauteuil, en minutes ?",
            [],
            ["minutes_assis"],
        ),
        (
            "checkbox",
            "Lesquelles de ces activités faites-vous au moins une fois par mois ? (Cochez "
            "toutes les réponses applicables)",
            ACTIVITIES,
        ),
        (
            "question",
            "Êtes-vous inscrit·e dans un club ou une association sportive ?",
            ["Oui", "Non"],
            ["membre_club"],
        ),
        (
            "question",
            "Si oui, combien de fois par semaine y allez-vous ?",
            [],
            ["club_seances"],
        ),
    ],
    [
        ("heading", "Pourquoi vous bougez"),
        ("text", "Les énoncés suivants forment l'Échelle fictive de motivation (EFM)."),
        (
            "grid",
            "Dans quelle mesure êtes-vous d'accord avec les énoncés suivants ?",
            AGREEMENT,
            MOTIVATION,
        ),
        (
            "question",
            "Sur une échelle de 0 à 10, à quel point êtes-vous content·e de votre forme physique ?",
            [str(i) for i in range(11)],
            ["forme_satisfaction"],
        ),
        ("question", "Voulez-vous ajouter quelque chose ?", [], ["remarques"]),
        ("text", "Merci !"),
    ],
]

TRAPS = {
    "variables_without_question": ["id_repondant", "horodatage", "vague", "score_motivation"],
    "computed_score": {"score_motivation": [name for _text, name in MOTIVATION]},
    "paraphrased": ["poids_kg", "taille_m", "jours_actifs", "minutes_assis", "forme_satisfaction"],
    "follow_up": {"membre_club": ["club_seances"]},
    "defined_acronyms": {"EFM": "Échelle fictive de motivation"},
    "consent_page_canary": CANARY_CONSENT,
}


def answer_key() -> dict[str, tuple[int, int, int | None]]:
    return common.questionnaire_key(QUESTIONNAIRE)


def build_dataset() -> pd.DataFrame:
    """The fictional answers, always the same for SEED."""
    rng = np.random.default_rng(SEED)
    n = N_ROWS
    data: dict[str, object] = {}
    data["id_repondant"] = [f"{CANARY_ID}-{i:03d}" for i in range(1, n + 1)]
    start = np.datetime64("2026-04-06T08:00")
    data["horodatage"] = [
        str(start + np.timedelta64(int(m), "m")).replace("T", " ")
        for m in rng.integers(0, 40 * 24 * 60, size=n)
    ]
    data["vague"] = np.ones(n)
    data["annee_naissance"] = rng.integers(1950, 2006, size=n).astype(float)
    data["poids_kg"] = np.round(rng.normal(72, 13, size=n), 1)
    data["taille_m"] = np.round(rng.normal(1.69, 0.09, size=n), 2)
    activity = rng.normal(size=n)
    data["jours_actifs"] = np.clip(np.round(3.2 + 1.6 * activity), 0, 7)
    data["minutes_assis"] = np.clip(
        np.round(rng.normal(420, 120, size=n) - 30 * activity, -1), 60, 900
    )
    for (_text, name), share in zip(ACTIVITIES, (0.7, 0.35, 0.2, 0.25, 0.15), strict=True):
        data[name] = np.where(rng.random(n) < share, 1.0, np.nan)
    member = rng.random(n) < 0.3
    data["membre_club"] = np.where(member, 1.0, 2.0)
    data["club_seances"] = np.where(member, rng.integers(1, 5, size=n).astype(float), np.nan)
    items = []
    for _text, name in MOTIVATION:
        values = np.clip(np.round(3 + 0.7 * activity + rng.normal(scale=0.9, size=n)), 1, 5)
        data[name] = values
        items.append(values)
    data["score_motivation"] = np.sum(items, axis=0)
    data["forme_satisfaction"] = np.clip(np.round(5.5 + 1.5 * activity + rng.normal(size=n)), 0, 10)
    remarks = [""] * n
    for k, row in enumerate(np.sort(rng.choice(n, size=25, replace=False))):
        text = ("J'aimerais marcher davantage", "Trop de travail cette année", "Rien à ajouter")[
            k % 3
        ]
        remarks[row] = f"{text} ({CANARY_TEXT}-{row + 1:03d})"
    data["remarques"] = remarks
    return pd.DataFrame({name: data[name] for name in COLUMN_ORDER})


def write_csv(df: pd.DataFrame, path: Path) -> None:
    """As R's write.csv would: UTF-8, "," and ".", missing cells written NA."""
    filled = df.astype(object).where(df.notna(), "NA")
    filled["remarques"] = df["remarques"]  # an empty remark stays empty
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
    parser = argparse.ArgumentParser(description="Génère la base de contrôle de la v0.6.")
    parser.add_argument("out_dir", nargs="?", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    for path in write_all(args.out_dir):
        print(path)


if __name__ == "__main__":
    main()
