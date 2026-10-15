"""v0.7, step 10: stems proposed by the local model (D-051), against a fake server."""

import json
from pathlib import Path

import httpx
import pytest

import ddict.llm.client as client_module
from ddict import naming
from ddict.cli import main
from ddict.io import read_database
from ddict.llm.client import LocalModelClient
from ddict.llm.stems import (
    ACRONYM_SIGNAL,
    build_stem_blocks,
    parse_stem_response,
    propose_stems,
)
from ddict.llm.validate import InvalidResponse
from ddict.project import build_project, load_project, save_project
from ddict.workflow import add_questionnaire

EXAMPLES = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"
KEY = json.loads((EXAMPLES / "corrige-surveymonkey.json").read_text(encoding="utf-8"))
STEMS = KEY["waves"]["t2"]["stems"]
NOW = "2026-10-15T12:00:00"


@pytest.fixture
def project():
    found = build_project(read_database(EXAMPLES / "travail-t2_surveymonkey.sav"))
    add_questionnaire(found, EXAMPLES / "travail-t2_surveymonkey.xlsx")
    naming.propose(found)
    return found


class Server:
    """Answers each question with the key's stem; `answers` overrides some."""

    def __init__(self, answers: dict | None = None, raw: str | None = None):
        self.answers = answers or {}
        self.raw = raw
        self.calls = 0
        self.sent: list[str] = []

    def __call__(self, request):
        self.calls += 1
        body = json.loads(request.content)
        self.sent.append(body["messages"][1]["content"])
        content = json.loads(body["messages"][1]["content"])
        if self.raw is not None:
            text = self.raw.replace("BLOCK", content["block"])
        else:
            questions = [
                {"key": q["key"], "stem": self.answers.get(q["key"], STEMS.get(q["key"], ""))}
                for q in content["questions"]
            ]
            text = json.dumps({"block": content["block"], "questions": questions})
        return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


def _run(project, server):
    client = LocalModelClient("qwen-test", transport=httpx.MockTransport(server))
    with client:
        return list(propose_stems(project, client, now=lambda: NOW))


# --- What is sent. ---


def test_the_blocks_hold_the_open_questions_only(project):
    naming.decide_stem(project, "q0001", "correct", value="secteur", now=NOW)
    blocks = build_stem_blocks(project, size=4)
    keys = [k for b in blocks for k in b.names]
    assert "q0001" not in keys  # decided by a person
    assert keys[:3] == ["q0002", "q0005", "q0006"]
    assert [len(b.names) for b in blocks] == [4, 4, 1]
    assert blocks[0].prompt_version == "rename-v1"
    first = json.loads(blocks[0].messages[1]["content"])["questions"]
    tasks = next(q for q in first if q["key"] == "q0005")
    assert tasks["kind"] == "checkbox" and tasks["other"] is True
    assert tasks["options"][0] == "Accueil de la clientèle"
    assert tasks["question"].startswith("Quelles tâches faites-vous")


def test_no_participant_value_is_sent(project):
    text = "\n".join(b.messages[1]["content"] for b in build_stem_blocks(project, size=8))
    for canary in KEY["canaries"]:
        assert canary not in text
    identifier = next(
        q
        for b in build_stem_blocks(project, size=8)
        for q in json.loads(b.messages[1]["content"])["questions"]
        if q["key"] == "q0012"
    )
    assert identifier["note"] == "identifiant probable : aucune valeur transmise"
    assert "options" not in identifier


def test_english_instructions_for_a_study_in_english(project):
    project.settings.language = "en"
    block = build_stem_blocks(project, size=8)[0]
    assert block.prompt_version == "rename-v1.en"
    assert block.messages[0]["content"].startswith("You help a research team")


# --- What is accepted. ---


@pytest.mark.parametrize(
    ("answer", "code"),
    [
        ("", "empty_response"),
        ("pas du JSON", "not_json"),
        ('{"block": "BLOCK", "questions": [], "seuil": 3}', "schema"),
        ('{"block": "r-999", "questions": []}', "block_mismatch"),
        (
            '{"block": "BLOCK", "questions": [{"key": "q0001", "stem": "secteur"}]}',
            "names_mismatch",
        ),
    ],
)
def test_refused_answers(project, answer, code):
    block = build_stem_blocks(project, size=8)[0]
    with pytest.raises(InvalidResponse) as error:
        parse_stem_response(answer.replace("BLOCK", block.block_id), block)
    assert error.value.code == code


@pytest.mark.parametrize("stem", ["Secteur", "secteur_", "1secteur", "un secteur", "a" * 21])
def test_a_stem_the_rules_refuse_refuses_the_block(project, stem):
    block = build_stem_blocks(project, size=8)[0]
    questions = [{"key": k, "stem": "secteur" if k != "q0001" else stem} for k in block.names]
    with pytest.raises(InvalidResponse) as error:
        parse_stem_response(json.dumps({"block": block.block_id, "questions": questions}), block)
    assert error.value.code in ("invalid_stem", "schema")


# --- What is proposed. ---


def test_the_model_proposes_stems_and_the_names_follow(project):
    events = _run(project, Server())
    assert all(e.result.run.outcome == "succeeded" for e in events)
    found = naming.stem(project, "q0005")
    assert (found.stem.value, found.stem.origin, found.stem.status) == ("taches", "ai", "proposed")
    assert found.stem.ai_run is not None
    assert project.variable("q0005_0002").new_name.value == "taches_2"
    assert project.variable("q0009").new_name.value == "situation_danger"


def test_a_decided_stem_is_never_replaced(project):
    naming.decide_stem(project, "q0001", "correct", value="domaine", now=NOW)
    naming.decide_stem(project, "q0007", "accept", now=NOW)  # the rules' stem, accepted
    _run(project, Server({"q0001": "secteur", "q0007": "nb_pauses"}))
    assert naming.stem(project, "q0001").stem.value == "domaine"
    assert naming.stem(project, "q0007").stem.value == "pauses_journee"


def test_unsure_keeps_the_rules_stem(project):
    before = naming.stem(project, "q0002").stem.value
    _run(project, Server({"q0002": ""}))
    after = naming.stem(project, "q0002")
    assert (after.stem.value, after.stem.origin) == (before, "rule")


def test_an_acronym_the_question_does_not_hold_is_flagged(project):
    _run(project, Server({"q0007": "eft_pauses", "q0001": "secteur"}))
    assert ACRONYM_SIGNAL in naming.stem(project, "q0007").ai_signals
    assert naming.stem(project, "q0001").ai_signals == []
    # A person's decision settles the signal.
    naming.decide_stem(project, "q0007", "accept", now=NOW)
    assert naming.stem(project, "q0007").ai_signals == []


def test_two_questions_given_the_same_stem(project):
    _run(project, Server({"q0009": "remarques", "q0011": "remarques"}))
    assert {naming.stem(project, k).stem.value for k in ("q0009", "q0011")} == {
        "remarques",
        "remarques_2",
    }


def test_no_group_prefix_is_ever_proposed(project):
    _run(project, Server())
    assert all(not g.name_prefix.value for g in project.groups)


# --- The command. ---


@pytest.fixture
def fake_ollama(monkeypatch):
    server = Server()
    real = client_module.LocalModelClient.__init__

    def init(self, model, *, endpoint=client_module.DEFAULT_ENDPOINT, **kwargs):
        real(self, model, endpoint=endpoint, transport=httpx.MockTransport(server))

    monkeypatch.setattr(client_module.LocalModelClient, "__init__", init)
    return server


def test_rename_command_with_a_model(project, tmp_path, capsys, fake_ollama):
    path = tmp_path / "travail.dd.json"
    save_project(project, path)
    assert main(["renommer", str(path), "--modele", "qwen-test"]) == 0
    out = capsys.readouterr().out
    assert "Bloc r-001 (8 variables) : réussi." in out
    assert load_project(path).variable("q0005_0001").new_name.value == "taches_1"
    assert main(["renommer", str(path), "--apercu"]) == 0
    assert "rien n'a été envoyé" in capsys.readouterr().out
