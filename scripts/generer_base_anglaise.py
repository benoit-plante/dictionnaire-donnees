"""Generate the English version of the fictional sleep study (v0.5, step 4).

The same 200 fictional participants as `generer_bases_fictives.py` (same seed, same values),
for a study run in English: English variable names, labels, value labels, free text and
questionnaire. The questionnaire has the structure of the French one, question for question,
so that both must give the same questions; its acronyms are defined in English (FSQ, FAS,
CBT). Everything is invented.

Usage (from the repository root):
    uv run python scripts/generer_base_anglaise.py [output_folder]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generer_bases_fictives as common

BASE_NAME = "sleep-study"
QUESTIONNAIRE_NAME = "questionnaire-sleep"
DEFAULT_OUT_DIR = common.DEFAULT_OUT_DIR

NAMES = {
    "id_participant": "participant_id",
    "courriel": "email",
    "date_passation": "date_completed",
    "date_naissance": "birth_date",
    "age": "age",
    "genre": "gender",
    "vague": "wave",
    **{f"sommeil_q{i}": f"sleep_q{i}" for i in range(1, 9)},
    **{f"anx{i}": f"anx{i}" for i in range(1, 8)},
    "heures_sommeil": "sleep_hours",
    "heures_sommeil_2": "sleep_hours_2",
    "nb_reveils": "n_awakenings",
    "aide_medicament": "aid_medication",
    "aide_naturel": "aid_natural",
    "aide_tcc": "aid_cbt",
    "aide_aucune": "aid_none",
    "satisfaction_globale": "overall_satisfaction",
    "taille_cm": "height_cm",
    "q_retiree": "q_removed",
    "langue_maison": "home_language",
    "commentaire": "comment",
}
COLUMN_LABELS = {
    "participant_id": "Participant identifier",
    "email": "Email",
    "date_completed": "Date completed",
    "birth_date": "DOB",
    "age": "Age",
    "gender": "Gender",
    "wave": "Wave",
    "sleep_q1": "Q1 falling asleep",
    "sleep_q2": "Q2 restful sleep",
    "sleep_q3": "Q3 night awakenings",
    "sleep_q4": "Q4 sleep satisf",
    "sleep_q5": "Q5 morning energy",
    "sleep_q6": "Q6 daytime sleepiness",
    "sleep_q7": None,
    "sleep_q8": "Q8 routine",
    "anx1": "ANX worried",
    "anx2": "ANX tense",
    "anx3": "ANX control worry",
    "anx4": "ANX restless",
    "sleep_hours": "Hours of sleep (mean)",
    "sleep_hours_2": "Hours of sleep (mean)",
    "n_awakenings": "N awakenings / night",
    "aid_medication": "Sleep aid: medication",
    "aid_natural": "Sleep aid: natural product",
    "aid_cbt": "Sleep aid: CBT",
    "aid_none": "Sleep aid: none",
    "anx5": "ANX irritable",
    "anx6": "ANX afraid",
    "anx7": "ANX hard to relax",
    "overall_satisfaction": "Overall satisfaction 0-10",
    "height_cm": "Height (cm)",
    "q_removed": "Question removed v2",
    "home_language": "Home language",
    "comment": "Comments",
}
LIKERT_5 = {1: "Not at all", 2: "A little", 3: "Moderately", 4: "A lot", 5: "Extremely"}
FREQ_4 = {0: "Never", 1: "Sometimes", 2: "Often", 3: "Almost always", -9: "Refused"}
VALUE_LABELS = {
    "gender": {1: "Woman", 2: "Man", 3: "Other identity", 9: "Prefer not to answer"},
    "wave": {1: "Wave 1"},
    "overall_satisfaction": {
        0: "Not at all satisfied",
        10: "Completely satisfied",
        99: "Don't know",
    },
}
# The same answers typed by hand, in English: the variants differ by case only.
HOME_LANGUAGE = {
    "Français": "French",
    "français": "french",
    "Francais": "FRENCH",
    "Anglais": "English",
    "anglais": "english",
    "Espagnol": "Spanish",
    "Créole": "Creole",
    "créole": "creole",
    "": "",
}
COMMENTS = {
    "Je dors très mal depuis le déménagement.": "I have slept very badly since the move.",
    "Rien à ajouter ; merci pour l'étude": "Nothing to add; thanks for the study",
    "Mon conjoint ronfle, c'est \"l'enfer\" la nuit": 'My partner snores, nights are "hell"',
    "Le questionnaire était long.\nJ'ai répondu au mieux.": (
        "The questionnaire was long.\nI answered as best I could."
    ),
    "Travail de nuit en alternance — horaires très variables": (
        "Rotating night shifts — very irregular hours"
    ),
}
CANARY_CONSENT = "ZQXQUESTEN"

LIKERT_OPTIONS = list(LIKERT_5.values())
FREQ_OPTIONS = [label for code, label in FREQ_4.items() if code >= 0]

QUESTIONNAIRE = [
    [
        ("title", "Fictional study of sleep and well-being"),
        ("heading", "Information and consent form"),
        (
            "text",
            "This study is entirely fictional: it is used to try out a data documentation "
            "tool. It includes the Fictional Sleep Questionnaire (FSQ) and the Fictional "
            "Anxiety Scale (FAS).",
        ),
        (
            "text",
            f"Research team: Dr Zoe {CANARY_CONSENT}-Example, Fictional Sleep Laboratory. "
            f"For any question: {CANARY_CONSENT.lower()}@example.org or 555-0199.",
        ),
        ("question", "Do you agree to take part in this study?", ["Yes", "No"], []),
    ],
    [
        ("heading", "General information"),
        ("question", "What is your date of birth? (DD/MM/YYYY)", [], ["birth_date"]),
        ("question", "How old are you?", [], ["age"]),
        (
            "question",
            "What is your gender?",
            ["Woman", "Man", "Other identity", "Prefer not to answer"],
            ["gender"],
        ),
        ("question", "Your email address (to send you a reminder):", [], ["email"]),
        ("question", "How tall are you, in centimetres?", [], ["height_cm"]),
    ],
    [
        ("heading", "Your sleep"),
        ("text", "The following statements make up the Fictional Sleep Questionnaire (FSQ)."),
        (
            "grid",
            "Over the past month, how much do the following statements apply to you?",
            LIKERT_OPTIONS,
            [
                ("I have difficulty falling asleep at night.", "sleep_q1"),
                ("My sleep is restful.", "sleep_q2"),
                (
                    "I wake up several times during the night without being able to fall "
                    "back asleep easily.",
                    "sleep_q3",
                ),
                ("I am satisfied with the quality of my sleep.", "sleep_q4"),
                ("I have energy as soon as I wake up.", "sleep_q5"),
                ("I feel drowsy during the day, even after a good night.", "sleep_q6"),
                ("I avoid screens in the hour before going to bed.", "sleep_q7"),
                ("I follow a regular routine before going to bed.", "sleep_q8"),
            ],
        ),
        (
            "question",
            "On average, how many hours do you sleep per night?",
            [],
            ["sleep_hours", "sleep_hours_2"],
        ),
        (
            "question",
            "How many times do you wake up during a typical night?",
            [],
            ["n_awakenings"],
        ),
        (
            "checkbox",
            "What do you use to help you sleep? (Check all that apply)",
            [
                ("A prescribed medication", "aid_medication"),
                ("A natural product (herbal tea, melatonin)", "aid_natural"),
                ("Cognitive behavioural therapy (CBT)", "aid_cbt"),
                ("None of these", "aid_none"),
            ],
        ),
        (
            "question",
            "Overall, how satisfied are you with your sleep? "
            "(0 = Not at all satisfied, 10 = Completely satisfied)",
            [str(i) for i in range(11)] + ["Don't know"],
            ["overall_satisfaction"],
        ),
    ],
    [
        ("heading", "Your mood"),
        ("text", "The following statements make up the Fictional Anxiety Scale (FAS)."),
        (
            "grid",
            "Over the past two weeks, how often have you felt the following?",
            FREQ_OPTIONS,
            [
                ("I felt worried.", "anx1"),
                ("I felt tense.", "anx2"),
                ("I had trouble controlling my worries.", "anx3"),
                ("I felt restless.", "anx4"),
                ("I felt irritable.", "anx5"),
                ("I was afraid that something terrible might happen.", "anx6"),
                ("I had difficulty relaxing.", "anx7"),
            ],
        ),
        ("question", "Do you have any other comments about your sleep?", [], ["comment"]),
        (
            "question",
            "Which language do you speak most often at home?",
            [],
            ["home_language"],
        ),
        ("text", "Thank you for taking part!"),
    ],
]

TRAPS = {
    "defined_acronyms": {
        "FSQ": "Fictional Sleep Questionnaire",
        "FAS": "Fictional Anxiety Scale",
        "CBT": "cognitive behavioural therapy",
    },
    "acronym_in_name": {"aid_cbt": "CBT"},
    "consent_page_canary": CANARY_CONSENT,
    "variables_without_question": ["participant_id", "date_completed", "wave", "q_removed"],
    "spelling_variants": {
        "home_language": [["French", "french", "FRENCH"], ["English", "english"]]
    },
}


def answer_key() -> dict[str, tuple[int, int, int | None]]:
    return common.questionnaire_key(QUESTIONNAIRE)


def _comment(text: object) -> object:
    if not isinstance(text, str) or not text:
        return text
    for french, english in COMMENTS.items():
        if text.startswith(french):
            return english + text[len(french) :]
    raise ValueError(f"No English comment for {text!r}")


def build_dataset():
    """The French dataset, renamed and with its text answers in English."""
    df, meta = common.build_dataset()
    df = df.rename(columns=NAMES)
    df["home_language"] = df["home_language"].map(HOME_LANGUAGE)
    df["comment"] = df["comment"].map(_comment)
    value_labels = {NAMES[name]: LIKERT_5 for name in common.SLEEP_ITEMS}
    value_labels.update({NAMES[name]: FREQ_4 for name in common.ANXIETY_ITEMS})
    value_labels.update(VALUE_LABELS)
    meta = {
        "file_label": "Sleep study (fictional)",
        "column_labels": COLUMN_LABELS,
        "variable_value_labels": value_labels,
        "missing_ranges": {NAMES[name]: codes for name, codes in meta["missing_ranges"].items()},
        "variable_measure": {NAMES[name]: m for name, m in meta["variable_measure"].items()},
        "variable_format": {NAMES[name]: f for name, f in meta["variable_format"].items()},
    }
    return df, meta


def write_all(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df, meta = build_dataset()
    paths = []
    sav = out_dir / f"{BASE_NAME}.sav"
    common.write_sav(df, meta, sav)
    paths.append(sav)
    csv = out_dir / f"{BASE_NAME}.csv"
    common.write_csv(df, csv, encoding="utf-8", delimiter=",", decimal=".", line_end="\n")
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
    parser = argparse.ArgumentParser(description="Generate the English fictional sleep study.")
    parser.add_argument("out_dir", nargs="?", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    for path in write_all(args.out_dir):
        print(path)


if __name__ == "__main__":
    main()
