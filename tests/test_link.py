"""v0.2, step 4: variables linked to questions — computed candidates, the model's choice by
identifier, a person's decision (D-013)."""

import json
import re
from pathlib import Path

import httpx
import pytest
from streamlit.testing.v1 import AppTest

from ddict import glossary
from ddict.cli import main
from ddict.io import read_database
from ddict.llm.client import LocalModelClient
from ddict.llm.link import build_link_blocks, propose_links
from ddict.project import build_project, load_project, save_project
from ddict.project.model import TrackedValue
from ddict.questionnaire import link, load_questionnaire
from ddict.review import logic

NOW = "2026-10-14T10:00:00"
APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
LINK_VALUE = re.compile(r"Q\d+(\.[ro]\d+)?|none")


def _project(fictional_files, data="etude-sommeil.sav", questionnaire="questionnaire-sommeil.pdf"):
    project = build_project(read_database(fictional_files[data]))
    project.questionnaire = load_questionnaire(fictional_files[questionnaire])
    glossary.propose_from_questionnaire(project)
    return project


def expected_links(project, generator) -> dict[str, str]:
    """The answer key of the fictional questionnaire, as identifiers."""
    found = {}
    for name, (_page, rank, row) in generator.questionnaire_key().items():
        question = project.questionnaire.questions[rank - 1]
        if row is None:
            found[name] = question.question_id
        else:
            found[name] = f"{question.question_id}.{'r' if question.kind == 'grid' else 'o'}{row}"
    return found


@pytest.fixture
def project(fictional_files):
    return _project(fictional_files)


# --- Computed candidates, without any model. ---


def test_targets_hold_the_exact_words_of_the_questionnaire(project, fictional_files):
    text = fictional_files["questionnaire-sommeil.txt"].read_text(encoding="utf-8")
    found = {t.target_id: t for t in link.targets(project.questionnaire)}
    assert found["Q7.r3"].part.startswith("Je me réveille plusieurs fois")
    assert found["Q10.o3"].part == "Une thérapie cognitivo-comportementale (TCC)"
    assert link.describe(project.questionnaire, "Q8") == (
        "Q8, p. 3 : En moyenne, combien d'heures dormez-vous par nuit ?"
    )
    for target in found.values():
        assert target.question.text in text
        assert target.part is None or target.part in text


@pytest.mark.parametrize("data", ["etude-sommeil.sav", "etude-sommeil.csv"])
@pytest.mark.parametrize(
    "questionnaire", ["questionnaire-sommeil.pdf", "questionnaire-sommeil.txt"]
)
def test_computed_links_are_right_on_the_fictional_base(
    fictional_files, generator, data, questionnaire
):
    """Every variable asked in the questionnaire gets its question first, with or without
    file labels: grid rows by series, ticked options, the order differing from the file."""
    project = _project(fictional_files, data, questionnaire)
    best = link.best_guess(project)
    expected = expected_links(project, generator)
    assert {name: best[name] for name in expected} == expected


def test_variables_not_asked_are_left_to_the_model_or_a_person(project, generator):
    found = link.candidates(project)
    assert found["vague"] == []  # nothing comes close
    for name in generator.QUESTIONNAIRE_TRAPS["variables_without_question"]:
        assert len(found[name]) <= link.MAX_CANDIDATES


def test_single_choice_options_are_not_candidates_of_a_lone_variable(project):
    assert not any(".o" in target for target in link.candidates(project)["genre"])


def test_accepted_glossary_meanings_help(project):
    """An accepted acronym is read as its meaning: "tcc", then "thérapie cognitivo-..."."""
    row = link.target(project.questionnaire, "Q10.o3").position
    before = link.scores(project)["aide_tcc"][row]
    glossary.decide(project, "TCC", "accept", now=NOW)
    assert link.scores(project)["aide_tcc"][row] > before


def test_stale_links_are_dropped_when_the_questionnaire_changes(project, fictional_files):
    project.variable("age").question = TrackedValue[str](value="Q3", origin="human")
    project.variable("vague").question = TrackedValue[str](value="none", origin="human")
    same = project.questionnaire
    assert link.drop_stale_links(project, same) == 0
    other = same.model_copy(update={"sha256": "0" * 64})
    assert link.drop_stale_links(project, other) == 1
    assert project.variable("age").question.value is None
    assert project.variable("vague").question.value == "none"  # still no question


# --- The model chooses by identifier. ---


class Server:
    """A fake local model: `choose(name, candidate ids)` gives the answer for a variable."""

    def __init__(self, choose, extra=None):
        self.choose = choose
        self.extra = extra or {}
        self.messages = []

    def __call__(self, request):
        body = json.loads(request.content)
        self.messages.append(body["messages"])
        content = json.loads(body["messages"][1]["content"])
        answer = {
            "block": content["block"],
            "variables": [
                {
                    "name": v["name"],
                    "question": self.choose(v["name"], [c["id"] for c in v["candidates"]]),
                    **self.extra,
                }
                for v in content["variables"]
            ],
        }
        text = json.dumps(answer, ensure_ascii=False)
        return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


def _run(project, server, **kwargs):
    client = LocalModelClient("modele-test", transport=httpx.MockTransport(server))
    return list(propose_links(project, client, now=lambda: NOW, block_size=6, **kwargs))


def test_choices_enter_as_proposals(project):
    answers = {"id_participant": "aucune", "age": "incertain"}
    _run(project, Server(lambda name, ids: answers.get(name, ids[0])))
    q1 = project.variable("sommeil_q1").question
    assert (q1.value, q1.origin, q1.status) == ("Q7.r1", "ai", "proposed")
    assert project.variable("id_participant").question.value == "none"
    assert project.variable("age").question.value is None  # unsure: a person chooses
    assert {run.prompt_version for run in project.ai_runs} == {"link-v2"}
    assert all(run.outcome == "succeeded" for run in project.ai_runs)
    assert "question" in logic.pending(project.variable("sommeil_q1"))


def test_an_identifier_outside_the_candidates_refuses_the_block(project):
    _run(project, Server(lambda name, ids: "Q99" if name == "age" else ids[0]))
    refused = [run for run in project.ai_runs if run.detail == "unknown_target"]
    assert len(refused) == 1
    names = next(b.names for b in build_link_blocks(project, size=6) if "age" in b.names)
    assert all(project.variable(n).question.value is None for n in names)


def test_question_text_in_the_answer_is_refused(project):
    """No field for text: an answer that writes the question is refused as a whole."""
    _run(project, Server(lambda name, ids: ids[0], extra={"text": "Une question inventée ?"}))
    assert {run.detail for run in project.ai_runs} == {"schema"}
    assert all(e.question.value is None for e in project.variables)


def test_no_question_text_outside_the_questionnaire(project, fictional_files):
    """Whatever the model answers, a link holds an identifier, and its text is the
    questionnaire's own words."""
    _run(project, Server(lambda name, ids: ids[-1]))
    text = fictional_files["questionnaire-sommeil.txt"].read_text(encoding="utf-8")
    for entry in project.variables:
        value = entry.question.value
        if value is None:
            continue
        assert LINK_VALUE.fullmatch(value)
        if value != link.NO_QUESTION:
            found = link.target(project.questionnaire, value)
            assert found.question.text in text and (found.part is None or found.part in text)


def test_messages_hold_candidates_only(project, generator):
    server = Server(lambda name, ids: ids[0])
    _run(project, server)
    sent = json.dumps(server.messages, ensure_ascii=False)
    assert generator.CANARY_CONSENT not in sent  # the consent page is never sent
    assert "Merci de votre participation" not in sent  # nor any other paragraph
    for canary in generator.CANARIES:
        assert canary not in sent
    user = json.loads(server.messages[0][1]["content"])
    assert all(len(v["candidates"]) <= link.MAX_CANDIDATES for v in user["variables"])
    assert len(user["variables"]) <= 6


def test_a_persons_decision_is_neither_sent_nor_replaced(project):
    logic.link_question(project, "sommeil_q1", "Q7.r2", now=NOW)  # wrong on purpose
    server = Server(lambda name, ids: ids[0])
    _run(project, server)
    sent = [json.loads(m[1]["content"]) for m in server.messages]
    assert all(v["name"] != "sommeil_q1" for block in sent for v in block["variables"])
    assert project.variable("sommeil_q1").question.value == "Q7.r2"


def test_an_interrupted_run_resumes(project):
    _run(project, Server(lambda name, ids: ids[0]))
    runs = len(project.ai_runs)
    events = _run(project, Server(lambda name, ids: ids[0]))
    assert all(event.result is None for event in events)
    assert len(project.ai_runs) == runs


# --- A person decides. ---


def test_decisions(project):
    project.variable("genre").question = TrackedValue[str](
        value="Q4.o3", origin="ai", status="proposed", ai_run="run-0001"
    )
    logic.link_question(project, "genre", "Q4", now=NOW)
    genre = project.variable("genre").question
    assert (genre.value, genre.status, genre.proposed_value) == ("Q4", "corrected", "Q4.o3")

    project.variable("age").question = TrackedValue[str](
        value="Q3", origin="ai", status="proposed", ai_run="run-0001"
    )
    logic.link_question(project, "age", "Q3", now=NOW)
    assert project.variable("age").question.status == "validated"

    logic.link_question(project, "vague", link.NO_QUESTION, now=NOW)
    assert project.variable("vague").question.value == "none"
    with pytest.raises(logic.ReviewError):
        logic.link_question(project, "vague", "Q99", now=NOW)

    unlinked = [e.name for e in logic.select(project, "unlinked")]
    assert "genre" not in unlinked and "vague" not in unlinked and "sommeil_q1" in unlinked


def test_reject_a_proposed_link(project):
    project.variable("age").question = TrackedValue[str](
        value="Q2", origin="ai", status="proposed", ai_run="run-0001"
    )
    logic.decide(project, "age", "question", "reject", now=NOW)
    assert project.variable("age").question.status == "rejected"
    assert "age" in [e.name for e in logic.select(project, "unlinked")]


# --- Command line and interface. ---


def test_link_command_without_a_model(fictional_files, tmp_path, capsys):
    path = tmp_path / "etude.dd.json"
    main(["profiler", str(fictional_files["etude-sommeil.sav"]), "-o", str(path)])
    assert main(["rattacher", str(path)]) == 2  # no questionnaire yet
    assert "ddict questionnaire" in capsys.readouterr().err
    main(["questionnaire", str(path), str(fictional_files["questionnaire-sommeil.pdf"])])
    capsys.readouterr()
    assert main(["rattacher", str(path)]) == 0
    assert "32 variables sur 34 ont des questions candidates" in capsys.readouterr().out
    assert main(["rattacher", str(path), "--apercu"]) == 0
    folder = tmp_path / "etude.dd-envois" / "apercu"
    assert sorted(p.name for p in folder.iterdir())[:2] == ["l-001.json", "l-002.json"]
    record = json.loads((folder / "l-001.json").read_text(encoding="utf-8"))
    assert record["prompt_version"] == "link-v2"


def test_new_questionnaire_drops_links(fictional_files, tmp_path, capsys):
    path = tmp_path / "etude.dd.json"
    main(["profiler", str(fictional_files["etude-sommeil.sav"]), "-o", str(path)])
    main(["questionnaire", str(path), str(fictional_files["questionnaire-sommeil.pdf"])])
    project = load_project(path)
    logic.link_question(project, "age", "Q3", now=NOW)
    save_project(project, path)
    capsys.readouterr()
    txt = str(fictional_files["questionnaire-sommeil.txt"])
    assert main(["questionnaire", str(path), txt, "--remplacer"]) == 0
    assert "1 rattachements retirés" in capsys.readouterr().out
    assert load_project(path).variable("age").question.value is None


@pytest.fixture
def app(project, tmp_path):
    project.variable("age").question = TrackedValue[str](
        value="Q3", origin="ai", status="proposed", ai_run="run-0001"
    )
    path = tmp_path / "etude.dd.json"
    save_project(project, path)
    test = AppTest.from_file(APP, default_timeout=30)
    test.session_state["project_path"] = str(path)
    test.session_state["mode"] = "variables"  # the page opens on "Base" (v0.3)
    test.run()
    assert not test.exception, test.exception
    return test, path


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_link_in_the_interface(app):
    test, path = app
    assert test.selectbox(key="variable").value == "age"  # the proposal is to review
    assert any("Quel âge avez-vous ?" in m.value for m in test.markdown)
    test.button(key="accept-question-age").click().run()
    assert load_project(path).variable("age").question.status == "validated"

    test.sidebar.radio(key="filter").set_value("unlinked").run()
    name = test.selectbox(key="variable").value
    choice = test.selectbox(key=f"question-{name}")
    assert choice.options[0] != link.NO_QUESTION  # the best candidate first
    choice.set_value(link.NO_QUESTION)
    test.button(key=f"save-question-{name}").click().run()
    assert not test.exception, test.exception
    assert load_project(path).variable(name).question.value == link.NO_QUESTION
