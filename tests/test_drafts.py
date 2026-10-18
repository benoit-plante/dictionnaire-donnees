"""v0.16, step C2 (findings 8 and 9, D-124): one "Enregistrer" per section, no form where
something typed may be lost; what was typed and not saved is kept as a draft when the person
goes elsewhere, said on the page where they arrive, with "Revenir" and "Abandonner"; quitting
asks first. One action proposes the names."""

import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.project import load_project, save_project
from ddict.review import shutdown
from ddict.review.navigation import PAGES
from ddict.review.ui import common as c
from ddict.review.ui import groups_view
from ddict.workflow import add_questionnaire, profile_database
from test_notebook_page import _build_by_command, _folder

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")


@pytest.fixture
def sleep(tmp_path):
    for name in ("etude-sommeil.sav", "questionnaire-sommeil.pdf"):
        shutil.copy(EXAMPLES / name, tmp_path / name)
    project, path = profile_database(tmp_path / "etude-sommeil.sav")
    add_questionnaire(project, tmp_path / "questionnaire-sommeil.pdf")
    save_project(project, path)
    return path


def _open(path: Path, mode: str) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = mode
    app.run()
    assert not app.exception, app.exception
    return app


def _go(app: AppTest, mode: str) -> None:
    app.session_state["mode"] = mode
    app.run()
    assert not app.exception, app.exception


def _drafts(app: AppTest) -> list:
    # AppTest's session state has no .get()
    return app.session_state[c.DRAFTS] if c.DRAFTS in app.session_state else []  # noqa: SIM401


# --- Nothing typed, no draft. ---


@pytest.mark.allow_hosts(["127.0.0.1"])
@pytest.mark.parametrize("study", ["sleep", "analyses"])
def test_going_through_every_page_leaves_no_draft(study, sleep, tmp_path, capsys):
    if study == "analyses":
        path = _folder(tmp_path)
        _build_by_command(path)
        capsys.readouterr()
    else:
        path = sleep
    app = _open(path, "base")
    for mode in [*PAGES, "variables", "groups", "glossary", "names", "base"]:
        _go(app, mode)
        assert not _drafts(app), (mode, [d.place.title for d in _drafts(app)])
    assert not [w for w in app.warning if "non enregistrée" in w.value]


# --- A draft, then back to it or dropped. ---


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_draft_left_on_a_group_and_taken_back(sleep):
    app = _open(sleep, "groups")
    app.text_input(key="scoring-name-G1").input("sommeil_total").run()
    assert any("Modifications non enregistrées" in m.value for m in app.caption)
    _go(app, "variables")
    notice = [w.value for w in app.warning if "non enregistrée" in w.value]
    assert notice == ["Saisie non enregistrée : Groupes, G1, Cotation."]
    app.button(key="draft-back-0").click().run()
    assert app.session_state["mode"] == "groups"
    assert app.text_input(key="scoring-name-G1").value == "sommeil_total"
    assert app.session_state[groups_view.TAB] == "Cotation"
    assert not _drafts(app)
    assert load_project(sleep).groups[0].scoring is None  # still not saved


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_draft_dropped(sleep):
    app = _open(sleep, "groups")
    app.text_input(key="instrument-G1").input("Questionnaire fictif du sommeil").run()
    _go(app, "base")
    assert _drafts(app)
    app.button(key="draft-drop").click().run()
    assert not _drafts(app)
    _go(app, "groups")
    assert app.text_input(key="instrument-G1").value == ""


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_draft_left_on_a_variable(sleep):
    app = _open(sleep, "variables")
    app.sidebar.radio(key="filter").set_value("all").run()
    app.sidebar.selectbox(key="variable").set_value("sommeil_q2").run()
    app.text_input(key="input-sommeil_q2-label").input("Sommeil réparateur").run()
    app.button(key="variable-next").click().run()
    assert [d.place.title for d in _drafts(app)] == ["Variables, sommeil_q2"]
    app.button(key="draft-back-0").click().run()
    assert app.sidebar.selectbox(key="variable").value == "sommeil_q2"
    assert app.text_input(key="input-sommeil_q2-label").value == "Sommeil réparateur"
    app.button(key="save-texts-sommeil_q2").click().run()
    assert load_project(sleep).variable("sommeil_q2").label.value == "Sommeil réparateur"
    _go(app, "base")
    assert not _drafts(app)  # saved: nothing left behind


# --- One "Enregistrer" per section. ---


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_one_save_per_tab_of_a_group(sleep):
    app = _open(sleep, "groups")
    saves = sorted(b.key for b in app.button if b.key and b.key.startswith("save-"))
    assert saves == ["save-instrument-G1", "save-items-G1", "save-scoring-G1"]
    app.text_input(key="prefix-G1").input("qfs")
    app.button(key="offer-reverse-G1").click().run()
    app.button(key="save-items-G1").click().run()
    group = load_project(sleep).groups[0]
    assert group.name_prefix.value == "qfs" and group.reverse_items == ["sommeil_q3", "sommeil_q6"]
    app.text_input(key="instrument-G1").input("Questionnaire fictif du sommeil")
    app.text_input(key="instrument-source-G1").input("Manuel fictif, p. 1")
    app.checkbox(key="omit-text-G1").check()
    app.button(key="save-instrument-G1").click().run()
    group = load_project(sleep).groups[0]
    assert group.instrument_name.value == "Questionnaire fictif du sommeil"
    assert group.omit_question_text is True


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_one_save_for_the_texts_of_a_variable(sleep):
    app = _open(sleep, "variables")
    app.sidebar.radio(key="filter").set_value("all").run()
    app.sidebar.selectbox(key="variable").set_value("heures_sommeil").run()
    keys = {b.key for b in app.button if b.key}
    assert "save-texts-heures_sommeil" in keys
    assert not [k for k in keys if k.startswith("save-heures_sommeil-")]  # no button per field
    app.text_input(key="input-heures_sommeil-unit").input("heures")
    app.text_input(key="input-heures_sommeil-description").input("Heures de sommeil par nuit.")
    app.button(key="save-texts-heures_sommeil").click().run()
    entry = load_project(sleep).variable("heures_sommeil")
    assert (entry.unit.value, entry.description.value) == ("heures", "Heures de sommeil par nuit.")


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_one_action_proposes_the_names(sleep):
    app = _open(sleep, "names")
    keys = {b.key for b in app.button if b.key}
    assert "names-settings-save" in keys and "names-propose" not in keys
    assert app.button(key="names-settings-save").label == "Proposer les noms"


# --- Quitting with something typed. ---


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_quitting_asks_first_when_something_is_typed(sleep, monkeypatch):
    stopped = []
    monkeypatch.setattr(shutdown, "stop_soon", lambda: stopped.append(True))
    app = _open(sleep, "groups")
    app.text_input(key="scoring-name-G1").input("sommeil_total").run()
    app.sidebar.button(key="quit").click().run()
    assert not stopped
    assert any("sera perdue" in w.value for w in app.sidebar.warning)
    app.sidebar.button(key="quit-cancel").click().run()
    assert app.text_input(key="scoring-name-G1").value == "sommeil_total"
    app.sidebar.button(key="quit").click().run()
    app.sidebar.button(key="quit-anyway").click().run()
    assert stopped
