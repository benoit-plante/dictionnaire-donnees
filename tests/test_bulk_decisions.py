"""v0.4, step 5: grouped decisions, with a preview where each can be unchecked (D-029)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.io import read_database
from ddict.project import build_project, load_project, save_project
from ddict.project.model import TrackedValue
from ddict.questionnaire import link, load_questionnaire
from ddict.review import logic

NOW = "2026-10-14T17:00:00"
APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")


def _key(project, generator):
    found = {}
    for name, (_page, rank, row) in generator.questionnaire_key().items():
        question = project.questionnaire.questions[rank - 1]
        target = question.question_id
        if row is not None:
            target += f".{'r' if question.kind == 'grid' else 'o'}{row}"
        found[name] = target
    return found


@pytest.fixture
def project(fictional_files, generator):
    """Every link proposed by a "model": the answer key, except two wrong ones."""
    project = build_project(read_database(fictional_files["etude-sommeil.csv"]))
    project.questionnaire = load_questionnaire(fictional_files["questionnaire-sommeil.txt"])
    key = _key(project, generator)
    key["age"] = key["sommeil_q1"]  # the model is wrong here
    key["sommeil_q2"] = key["sommeil_q3"]  # and here
    for name, target in key.items():
        project.variable(name).question = TrackedValue[str](
            value=target, origin="ai", status="proposed", ai_run="run-0001"
        )
    return project


def test_only_where_the_model_and_the_computation_agree(project):
    computed = link.best_guess(project)
    agreeing = logic.agreeing_links(project)
    assert agreeing
    assert all(project.variable(n).question.value == computed[n] for n in agreeing)
    assert "age" not in agreeing and "sommeil_q2" not in agreeing
    proposed = [e.name for e in project.variables if e.question.status == "proposed"]
    assert set(agreeing) < set(proposed)


def test_accepted_one_by_one(project):
    agreeing = logic.agreeing_links(project)
    chosen, left_out = agreeing[:-1], agreeing[-1]
    logic.accept_links(project, chosen, now=NOW)
    for name in chosen:
        question = project.variable(name).question
        assert (question.status, question.updated_at, question.origin) == (
            "validated",
            NOW,
            "ai",
        )
    assert project.variable(left_out).question.status == "proposed"  # unchecked
    assert project.variable("age").question.status == "proposed"
    with pytest.raises(logic.ReviewError, match="plus en accord"):
        logic.accept_links(project, ["age"], now=NOW)
    with pytest.raises(logic.ReviewError, match="Aucune variable"):
        logic.accept_links(project, [], now=NOW)


@pytest.fixture
def labelled(project):
    """The links accepted: the value labels from the options wait for a decision."""
    for entry in project.variables:
        if entry.question.status == "proposed":
            logic.decide(project, entry.name, "question", "accept", now=NOW)
    return project


def _group_of(project, name):
    return next(g.group_id for g in project.groups if name in (g.members.value or []))


def test_value_labels_of_a_group(labelled):
    group_id = _group_of(labelled, "sommeil_q1")
    names = logic.group_label_proposals(labelled, group_id)
    assert "sommeil_q1" in names and len(names) > 1
    members = logic.group(labelled, group_id).members.value
    assert set(names) <= set(members)
    logic.accept_group_labels(labelled, group_id, names[1:], now=NOW)
    assert labelled.variable(names[0]).value_labels.status == "proposed"
    assert {labelled.variable(n).value_labels.status for n in names[1:]} == {"validated"}
    with pytest.raises(logic.ReviewError, match="n'attendent plus"):
        logic.accept_group_labels(labelled, group_id, names[1:2], now=NOW)


def _open(path, **state):
    app = AppTest.from_file(APP, default_timeout=30)
    app.session_state["project_path"] = str(path)
    for key, value in state.items():
        app.session_state[key] = value
    app.run()
    assert not app.exception, app.exception
    return app


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_links_in_the_interface(project, tmp_path):
    path = tmp_path / "p.dd.json"
    save_project(project, path)
    agreeing = logic.agreeing_links(project)
    app = _open(path, mode="variables", filter="all")
    assert not [b for b in app.button if b.key == "bulk-links-accept"]  # not before the list
    app.button(key="bulk-links-open").click().run()
    shown = [b.key for b in app.checkbox if b.key.startswith("bulk-link-")]
    assert shown == [f"bulk-link-{n}" for n in agreeing]  # the exact list
    unchecked = agreeing[0]
    app.checkbox(key=f"bulk-link-{unchecked}").uncheck().run()
    accept = app.button(key="bulk-links-accept")
    assert accept.label == f"Accepter ces {len(agreeing) - 1} rattachements"
    accept.click().run()
    assert not app.exception, app.exception
    assert f"{len(agreeing) - 1} rattachements acceptés." in [s.value for s in app.success]
    saved = load_project(path)
    assert saved.variable(unchecked).question.status == "proposed"
    assert {saved.variable(n).question.status for n in agreeing[1:]} == {"validated"}
    assert not [b for b in app.checkbox if b.key.startswith("bulk-link-")]  # list closed


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_cancel(project, tmp_path):
    path = tmp_path / "p.dd.json"
    save_project(project, path)
    app = _open(path, mode="variables", filter="all")
    app.button(key="bulk-links-open").click().run()
    app.button(key="bulk-links-cancel").click().run()
    assert not [b for b in app.checkbox if b.key.startswith("bulk-link-")]
    assert load_project(path).model_dump() == project.model_dump()


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_labels_in_the_interface(labelled, tmp_path):
    path = tmp_path / "p.dd.json"
    save_project(labelled, path)
    group_id = _group_of(labelled, "sommeil_q1")
    names = logic.group_label_proposals(labelled, group_id)
    app = _open(path, mode="groups", group=group_id)
    app.button(key=f"bulk-labels-open-{group_id}").click().run()
    app.button(key=f"bulk-labels-accept-{group_id}").click().run()
    assert not app.exception, app.exception
    assert f"Étiquettes de {len(names)} variables acceptées." in [s.value for s in app.success]
    saved = load_project(path)
    assert {saved.variable(n).value_labels.status for n in names} == {"validated"}
