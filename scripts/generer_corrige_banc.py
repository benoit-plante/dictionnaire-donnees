"""Write the answer key of the model bench (v0.4, step 6): corrige-banc.json.

For each fictional base, the question of every variable as the tool names it ("Q7.r3",
"Q10.o2", or "none"), resolved from the keys of the two generators.

Run: uv run python scripts/generer_corrige_banc.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import generer_base_anglaise as english  # noqa: E402
import generer_base_controle as control  # noqa: E402
import generer_bases_fictives as sleep  # noqa: E402
import generer_enquete_familles as families  # noqa: E402

from ddict.questionnaire import load_questionnaire  # noqa: E402
from ddict.questionnaire.link import NO_QUESTION  # noqa: E402

EXAMPLES = HERE.parent / "exemples" / "bases-fictives"
OUTPUT = EXAMPLES / "corrige-banc.json"

BASES = [
    (
        "etude-sommeil",
        "etude-sommeil.csv",
        "questionnaire-sommeil.pdf",
        sleep.questionnaire_key,
        sleep.QUESTIONNAIRE_TRAPS["variables_without_question"],
    ),
    (
        "enquete-familles",
        "enquete-familles.csv",
        "questionnaire-familles.pdf",
        families.answer_key,
        families.TRAPS["variables_without_question"],
    ),
    (
        "sleep-study",
        "sleep-study.csv",
        "questionnaire-sleep.pdf",
        english.answer_key,
        english.TRAPS["variables_without_question"],
    ),
    # The control base of v0.6 (D-042), in the bench once measured (step 6).
    (
        "etude-activite",
        "etude-activite.csv",
        "questionnaire-activite.pdf",
        control.answer_key,
        control.TRAPS["variables_without_question"],
    ),
]
# The control base of v0.6 (D-042): its own key, kept for the record of step 6.
CONTROL_OUTPUT = EXAMPLES / "corrige-controle.json"
CONTROL = [
    (
        "etude-activite",
        "etude-activite.csv",
        "questionnaire-activite.pdf",
        control.answer_key,
        control.TRAPS["variables_without_question"],
    ),
]


def resolve(questionnaire_path: Path, key: dict, not_asked: list[str]) -> dict[str, str]:
    questions = load_questionnaire(questionnaire_path).questions
    links = {}
    for name, (*_page, rank, row) in key.items():
        question = questions[rank - 1]
        target = question.question_id
        if row is not None:
            target += f".{'r' if question.kind == 'grid' else 'o'}{row}"
        links[name] = target
    for name in not_asked:
        links[name] = NO_QUESTION
    return dict(sorted(links.items()))


def build(folder: Path = EXAMPLES, bases: list = BASES) -> dict:
    return {
        "version": 1,
        "bases": [
            {
                "name": name,
                "data": data,
                "questionnaire": questionnaire,
                "links": resolve(folder / questionnaire, key(), not_asked),
            }
            for name, data, questionnaire, key, not_asked in bases
        ],
    }


def write(path: Path = OUTPUT, folder: Path = EXAMPLES, bases: list = BASES) -> Path:
    text = json.dumps(build(folder, bases), ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


if __name__ == "__main__":
    print(write())
    print(write(CONTROL_OUTPUT, bases=CONTROL))
