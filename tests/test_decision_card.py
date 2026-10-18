"""v0.16, step C1 (D-121): one decision card on every page. The value, its origin and its
status, the field to change it, then "Accepter", which takes the value shown, and "Rejeter",
side by side; once decided, "Enregistrer". For a label, a description, a question, value
labels, an acronym, a measure level and a new name."""

import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.io import read_sav
from ddict.project import build_project, load_project, save_project
from ddict.project.model import TrackedValue
from ddict.review import levels, logic, names
from ddict.workflow import add_questionnaire, profile_database

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")
NOW = "2026-10-18T12:00:00"


def _ai(value):
    return TrackedValue[str](value=value, origin="ai", status="proposed", ai_run="run-0001")


@pytest.fixture
def project():
    found = build_project(read_sav(EXAMPLES / "etude-sommeil.sav"))
    found.variable("sommeil_q1").label = _ai("Difficulté d'endormissement")
    found.variable("sommeil_q1").description = _ai("Difficulté à s'endormir, de 1 à 5.")
    return found


# --- The rules, without Streamlit. ---


def test_accept_takes_the_value_shown(project):
    logic.accept_shown(project, "sommeil_q1", "label", "Difficulté d'endormissement", now=NOW)
    assert project.variable("sommeil_q1").label.status == "validated"
    logic.accept_shown(project, "sommeil_q1", "description", " Difficulté à s'endormir. ",
                       now=NOW)  # fmt: skip
    description = project.variable("sommeil_q1").description
    assert (description.value, description.status) == ("Difficulté à s'endormir.", "corrected")
    assert description.proposed_value == "Difficulté à s'endormir, de 1 à 5."
    with pytest.raises(logic.ReviewError, match="n'attend plus"):
        logic.accept_shown(project, "sommeil_q1", "label", "Autre", now=NOW)


def test_an_empty_value_is_rejected_not_accepted(project):
    with pytest.raises(logic.ReviewError, match="Rejeter"):
        logic.accept_shown(project, "sommeil_q1", "label", "  ", now=NOW)
    assert project.variable("sommeil_q1").label.status == "proposed"


def test_a_level_shown(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.csv", tmp_path / "etude-sommeil.csv")
    project, _path = profile_database(tmp_path / "etude-sommeil.csv")
    waiting = [e.name for e in project.variables if e.measure_level.status == "proposed"]
    first, second = waiting[:2]
    proposed = project.variable(first).measure_level.value
    levels.accept_shown(project, first, proposed, now=NOW)
    assert project.variable(first).measure_level.status == "validated"
    other = "nominal" if project.variable(second).measure_level.value != "nominal" else "ordinal"
    levels.accept_shown(project, second, other, now=NOW)
    level = project.variable(second).measure_level
    assert (level.value, level.status) == (other, "corrected")


def _rule(value):
    return TrackedValue[str](value=value, origin="rule", status="proposed")


def test_a_name_shown(project):
    first, second, third = "sommeil_q1", "sommeil_q2", "sommeil_q3"
    for name in (first, second, third):
        project.variable(name).new_name = _rule(f"qfs_{name[-1]}")
    names.accept_shown(project, first, project.variable(first).new_name.value, now=NOW)
    assert project.variable(first).new_name.status == "validated"
    names.accept_shown(project, second, "nom_choisi", now=NOW)
    assert project.variable(second).new_name.value == "nom_choisi"
    names.reject(project, third, now=NOW)
    assert project.variable(third).new_name.status == "rejected"


# --- The card, on the page of a variable and in the glossary. ---


def _open(path: Path, mode: str, variable: str | None = None) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = mode
    app.run()
    if variable:
        app.sidebar.radio(key="filter").set_value("all").run()
        app.sidebar.selectbox(key="variable").set_value(variable).run()
    assert not app.exception, app.exception
    return app


def _keys(app: AppTest) -> set[str]:
    return {b.key for b in app.button if b.key}


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_proposal_has_accept_and_reject_and_no_save(project, tmp_path):
    path = tmp_path / "etude.dd.json"
    save_project(project, path)
    app = _open(path, "variables", "sommeil_q1")
    keys = _keys(app)
    for field in ("label", "description"):
        assert {f"accept-sommeil_q1-{field}", f"reject-sommeil_q1-{field}"} <= keys
        assert f"save-sommeil_q1-{field}" not in keys  # no third button
    assert "save-texts-sommeil_q1" in keys  # the unit: the section's one "Enregistrer"
    app.text_input(key="input-sommeil_q1-label").input("Endormissement difficile").run()
    assert any("enregistrera votre correction" in m.value for m in app.markdown)
    app.button(key="accept-sommeil_q1-label").click().run()
    label = load_project(path).variable("sommeil_q1").label
    assert (label.value, label.status) == ("Endormissement difficile", "corrected")
    assert "accept-sommeil_q1-label" not in _keys(app)  # decided: the section's button


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_level_and_the_name_on_the_page_of_a_variable(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.csv", tmp_path / "etude-sommeil.csv")
    project, path = profile_database(tmp_path / "etude-sommeil.csv")
    name = next(e.name for e in project.variables if e.measure_level.status == "proposed")
    project.variable(name).new_name = _rule("nom_propose")
    save_project(project, path)
    app = _open(path, "variables", name)
    assert {f"accept-level-{name}", f"reject-level-{name}"} <= _keys(app)
    assert {f"accept-name-{name}", f"reject-name-{name}"} <= _keys(app)
    app.button(key=f"accept-level-{name}").click().run()
    app.button(key=f"reject-name-{name}").click().run()
    assert not app.exception, app.exception
    found = load_project(path).variable(name)
    assert found.measure_level.status == "validated"
    assert found.new_name.status == "rejected"


# The value labels, accepted or rejected as a whole on the same card: test_value_labels.py.


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_glossary_uses_the_same_card(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.sav", tmp_path / "etude-sommeil.sav")
    shutil.copy(EXAMPLES / "questionnaire-sommeil.pdf", tmp_path / "questionnaire-sommeil.pdf")
    project, path = profile_database(tmp_path / "etude-sommeil.sav")
    add_questionnaire(project, tmp_path / "questionnaire-sommeil.pdf")
    save_project(project, path)
    app = _open(path, "glossary")
    assert {"accept-glossary-TCC", "reject-glossary-TCC"} <= _keys(app)
    assert "save-glossary-TCC" not in _keys(app)
    assert "Questionnaire — à valider (questionnaire-sommeil.pdf, p. 3)" in [
        c.value for c in app.caption
    ]
