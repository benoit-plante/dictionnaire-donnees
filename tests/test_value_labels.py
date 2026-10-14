"""v0.2, step 6: value labels proposed from the options of a question, under the strict
rule of D-016 — and only there."""

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.cli import main
from ddict.export import wording as w
from ddict.io import read_database
from ddict.llm.messages import build_blocks
from ddict.project import build_project, load_project, save_project
from ddict.project.model import ObservedCount, TrackedValue
from ddict.questionnaire import load_questionnaire
from ddict.questionnaire.labels import propose_value_labels
from ddict.review import logic

NOW = "2026-10-14T16:00:00"
APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
SLEEP = ["sommeil_q1", "sommeil_q2", "sommeil_q4", "sommeil_q5", "sommeil_q6", "sommeil_q7"]


def _linked(fictional_files, generator, data="etude-sommeil.csv", questionnaire="txt"):
    """The project with every link of the answer key accepted by a person."""
    project = build_project(read_database(fictional_files[data]))
    project.questionnaire = load_questionnaire(
        fictional_files[f"questionnaire-sommeil.{questionnaire}"]
    )
    for name, (_page, rank, row) in generator.questionnaire_key().items():
        question = project.questionnaire.questions[rank - 1]
        target = question.question_id
        if row is not None:
            target += f".{'r' if question.kind == 'grid' else 'o'}{row}"
        logic.link_question(project, name, target, now=NOW)
    return project


@pytest.fixture
def project(fictional_files, generator):
    return _linked(fictional_files, generator)


def _labels(project, name):
    tracked = project.variable(name).value_labels
    return {v.code: v.label for v in tracked.value} if tracked.value else None


def test_proposed_where_the_rule_holds(project, generator):
    waiting = [e.name for e in project.variables if e.value_labels.status == "proposed"]
    assert waiting == [*SLEEP, "sommeil_q8"]
    # The assumed order is right here: these are the labels of the .sav file.
    assert _labels(project, "sommeil_q1") == generator.LIKERT_5
    assert project.variable("sommeil_q1").value_labels.origin == "questionnaire"


@pytest.mark.parametrize(
    ("name", "why"),
    [
        ("sommeil_q3", "codes 1..5 and 9: not consecutive"),
        ("genre", "codes 1, 2, 3 and 9"),
        ("anx1", "codes -9 and 0..3 (no declared missing in a CSV)"),
        ("satisfaction_globale", "12 options, 11 codes"),
        ("aide_tcc", "linked to an option: the variable is a ticked box"),
        ("age", "an open question has no options"),
        ("vague", "no question"),
    ],
)
def test_nothing_proposed_otherwise(project, name, why):
    assert project.variable(name).value_labels.value is None, why


def test_codes_from_zero(project):
    entry = project.variable("anx1")
    entry.profile.observed_values = [o for o in entry.profile.observed_values if o.code != -9]
    propose_value_labels(project)
    assert _labels(project, "anx1") == {
        0: "Jamais",
        1: "Parfois",
        2: "Souvent",
        3: "Presque toujours",
    }


@pytest.mark.parametrize(
    "codes",
    [[2, 3, 4, 5, 6], [1, 2, 3, 4, 6], [1.0, 1.5, 2.0, 2.5, 3.0], ["a", "b", "c", "d", "e"]],
)
def test_codes_that_do_not_qualify(project, codes):
    entry = project.variable("sommeil_q1")
    entry.value_labels = TrackedValue(origin="human")
    entry.profile.observed_values = [ObservedCount(code=c, count=10) for c in codes]
    propose_value_labels(project)
    assert entry.value_labels.value is None


def test_declared_missing_codes_are_set_aside(fictional_files, generator):
    """In the .sav the -9 of anx1 is declared missing, but the file has labels: nothing."""
    project = _linked(fictional_files, generator, "etude-sommeil.sav")
    assert not any(e.value_labels.value for e in project.variables)


def test_columns_running_into_each_other_give_nothing(fictional_files, generator):
    """In the PDF, "MoyennementBeaucoup" is read as one column: flagged, nothing proposed."""
    project = _linked(fictional_files, generator, questionnaire="pdf")
    assert not any(e.name.startswith("sommeil") and e.value_labels.value for e in project.variables)


def test_only_an_accepted_link_counts(fictional_files):
    project = build_project(read_database(fictional_files["etude-sommeil.csv"]))
    project.questionnaire = load_questionnaire(fictional_files["questionnaire-sommeil.txt"])
    entry = project.variable("sommeil_q1")
    entry.question = TrackedValue[str](
        value="Q7.r1", origin="ai", status="proposed", ai_run="run-0001"
    )
    assert propose_value_labels(project) == []
    logic.decide(project, "sommeil_q1", "question", "accept", now=NOW)
    assert entry.value_labels.status == "proposed"
    logic.link_question(project, "sommeil_q1", "none", now=NOW)  # the person changes their mind
    assert entry.value_labels.value is None


def test_decisions_are_kept(project):
    logic.decide(project, "sommeil_q1", "value_labels", "accept", now=NOW)
    logic.decide(project, "sommeil_q2", "value_labels", "reject", now=NOW)
    propose_value_labels(project)
    assert project.variable("sommeil_q1").value_labels.status == "validated"
    assert project.variable("sommeil_q2").value_labels.status == "rejected"
    assert "value_labels" in logic.pending(project.variable("sommeil_q4"))
    assert "value_labels" not in logic.pending(project.variable("sommeil_q1"))


def test_accepted_labels_reach_the_codebook_and_the_model(project):
    logic.decide(project, "sommeil_q1", "value_labels", "accept", now=NOW)
    rows = {
        code: label
        for code, label, _count, _missing in w.value_rows(project.variable("sommeil_q1"))
    }
    assert rows["1"] == "Pas du tout" and rows["5"] == "Extrêmement"
    assert all(label == "" for _c, label, _n, _m in w.value_rows(project.variable("sommeil_q2")))
    sent = {
        v["name"]: v
        for b in build_blocks(project)
        for v in json.loads(b.messages[1]["content"])["variables"]
    }
    assert sent["sommeil_q1"]["value_labels"]["3"] == "Moyennement"
    assert "value_labels" not in sent["sommeil_q2"]  # proposed only: not sent


def test_link_command_reports_proposals(fictional_files, generator, tmp_path, capsys):
    path = tmp_path / "etude.dd.json"
    save_project(_linked(fictional_files, generator), path)
    project = load_project(path)
    for e in project.variables:
        e.value_labels = TrackedValue(origin="human")
    save_project(project, path)
    capsys.readouterr()
    assert main(["rattacher", str(path)]) == 0
    assert "à vérifier dans l'interface : sommeil_q1, sommeil_q2" in capsys.readouterr().out
    assert load_project(path).variable("sommeil_q1").value_labels.status == "proposed"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_accept_labels_in_the_interface(project, tmp_path):
    path = tmp_path / "etude.dd.json"
    save_project(project, path)
    test = AppTest.from_file(APP, default_timeout=30)
    test.session_state["project_path"] = str(path)
    test.session_state["mode"] = "variables"  # the page opens on "Base" (v0.3)
    test.run()
    test.sidebar.selectbox(key="variable").set_value("sommeil_q1").run()
    assert any("ordre supposé, à vérifier" in c.value for c in test.caption)
    test.button(key="accept-labels-sommeil_q1").click().run()
    assert not test.exception, test.exception
    assert load_project(path).variable("sommeil_q1").value_labels.status == "validated"
