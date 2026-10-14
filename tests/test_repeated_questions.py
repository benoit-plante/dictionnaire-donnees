"""v0.3, step 6: repeated questions told apart by the question before them, and the observed
range presented as the scale's."""

import json

import httpx
import pytest

from ddict.io import read_database
from ddict.llm.client import LocalModelClient
from ddict.llm.enrich import enrich
from ddict.llm.link import LINK_PROMPT_VERSION, build_link_blocks
from ddict.llm.validate import presents_observed_range
from ddict.project import build_project
from ddict.project.model import TheoreticalRange, ValueLabel
from ddict.questionnaire import link, load_questionnaire
from ddict.review import logic

# Invented: the same frequency question after each source of support, as in real surveys.
QUESTIONNAIRE = """Votre conjoint
Très satisfait
Insatisfait

À quelle fréquence cette personne vous apporte du soutien ?
Jamais
Souvent

Vos amis
Très satisfait
Insatisfait

À quelle fréquence cette personne vous apporte du soutien ?
Jamais
Souvent

Avez-vous reçu des services du CLSC ?
Oui
Non

Si oui, quels professionnels vous ont accompagné ? (Cochez toutes les réponses applicables)
Psychologue
Ergothérapeute

Avez-vous consulté en pratique privée ?
Oui
Non

Si oui, quels professionnels avez-vous consultés ? (Cochez toutes les réponses applicables)
Psychologue
Ergothérapeute
"""
COLUMNS = [
    "soutien_conjoint",
    "soutien_conjoint_freq",
    "soutien_amis",
    "soutien_amis_freq",
    "service_clsc",
    "type_clsc_psychologue",
    "type_clsc_ergo",
    "service_prive",
    "type_prive_psychologue",
    "type_prive_ergo",
]


@pytest.fixture
def project(tmp_path):
    (tmp_path / "q.txt").write_text(QUESTIONNAIRE, encoding="utf-8")
    rows = [",".join(COLUMNS)] + [
        ",".join(str(1 + (i + j) % 2) for j in range(10)) for i in range(20)
    ]
    (tmp_path / "base.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    project = build_project(read_database(tmp_path / "base.csv"))
    project.questionnaire = load_questionnaire(tmp_path / "q.txt")
    return project


def test_the_question_before_tells_repeated_questions_apart(project):
    ids = {q.text[:20]: q.question_id for q in project.questionnaire.questions}
    assert len(project.questionnaire.questions) == 8
    best = link.best_guess(project)
    assert best["soutien_conjoint_freq"] == "Q2"
    assert best["soutien_amis_freq"] == "Q4"
    assert best["type_clsc_ergo"] == "Q6.o2"  # after the CLSC question
    assert best["type_prive_ergo"] == "Q8.o2"  # after the private practice one
    assert ids["Votre conjoint"] == "Q1"


def test_the_model_sees_the_question_before_only_where_needed(project):
    assert LINK_PROMPT_VERSION == "link-v2"
    sent = [json.loads(b.messages[1]["content"]) for b in build_link_blocks(project, size=10)]
    candidates = {c["id"]: c for v in sent[0]["variables"] for c in v["candidates"]}
    assert candidates["Q4"]["after"] == "Vos amis"  # a repeated text
    assert candidates["Q6.o2"]["after"] == "Avez-vous reçu des services du CLSC ?"  # "Si oui"
    assert "after" not in candidates["Q3"]  # neither: no context needed
    assert "after" not in candidates["Q1"]


@pytest.mark.parametrize(
    ("text", "low", "high", "expected"),
    [
        ("Mesure le niveau de détresse sur une échelle de 0 à 21.", 0, 21, True),
        ("Évaluation du fonctionnement sur une échelle de 1,5 à 3,83.", 1.5, 3.83, True),
        ("Score total, entre 19 et 54.", 19, 54, True),
        ("Âge du participant, de 18 à 75 ans.", 18, 75, False),  # no scale is claimed
        ("Score sur une échelle de 0 à 24.", 0, 21, False),  # not the observed range
        ("Score sur une échelle de 0 à 21.", None, None, False),
    ],
)
def test_observed_range_as_a_scale(text, low, high, expected):
    assert presents_observed_range(text, low, high) is expected


def _enrich_with(project, description):
    def server(request):
        content = json.loads(json.loads(request.content)["messages"][1]["content"])
        answer = {
            "block": content["block"],
            "variables": [
                {"name": v["name"], "label": "Score", "description": description}
                for v in content["variables"]
            ],
        }
        text = json.dumps(answer, ensure_ascii=False)
        return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})

    client = LocalModelClient("m", transport=httpx.MockTransport(server))
    list(enrich(project, client, now=lambda: "2026-10-14T12:00:00", block_size=20, redo=True))


def test_flagged_unless_documented(project):
    _enrich_with(project, "Score sur une échelle de 1 à 2.")
    entry = project.variable("soutien_conjoint")
    assert "description:observed_range" in entry.ai_signals
    assert any("étendue observée" in text for text in logic.signal_texts(entry))

    entry.file.value_labels = [ValueLabel(code=1, label="Non"), ValueLabel(code=2, label="Oui")]
    project.variable("soutien_amis").theoretical_range = TheoreticalRange(
        min=1, max=2, source="Manuel fictif, p. 3"
    )
    _enrich_with(project, "Score sur une échelle de 1 à 2.")
    assert "description:observed_range" not in project.variable("soutien_conjoint").ai_signals
    assert "description:observed_range" not in project.variable("soutien_amis").ai_signals
