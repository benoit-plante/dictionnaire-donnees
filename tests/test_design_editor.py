"""v0.20, step D2: the editor of the designed questionnaire (`design_view`) — the list on the
model of the page "Plan", one question open at a time in a form of its kind, its choices and
items in a table; one "Enregistrer" per question, drafts (D-124), the check at writing (D-129,
D-130); a filter by section; a questionnaire of 150 questions stays quick. Fictional only."""

import time
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import design
from ddict.design import Draft, Item
from ddict.project import load_project, save_project
from ddict.project.model import TrackedValue
from ddict.review.ui import common as c
from ddict.review.ui.design_view import merged
from projet_concu import project as designed

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
NEW = "design-q-new-1-"  # its first opening


@pytest.fixture
def path(tmp_path):
    found = tmp_path / "Étude conçue" / "conçue.dd.json"
    found.parent.mkdir()
    save_project(designed(), found)
    return found


def _open(path, mode="design") -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = mode
    app.run()
    assert not app.exception, app.exception
    return app


def _run(app, element) -> None:
    element.run()
    assert not app.exception, app.exception


def _questions(path) -> list:
    return load_project(path).questionnaire.questions


# --- Without Streamlit: the edits of a table ---------------------------------------------------


def test_the_edits_of_a_table_keep_the_ids():
    rows = [
        {"id": "Q1.o1", "code": "1", "text": "Femme", "other": False},
        {"id": "Q1.o2", "code": "2", "text": "Homme", "other": False},
    ]
    edits = {
        "edited_rows": {"1": {"text": "Homme ou garçon"}},
        "added_rows": [{"code": "9", "text": "Préfère ne pas répondre"}],
        "deleted_rows": [0],
    }
    assert merged(rows, edits, ["id", "code", "text", "other"]) == [
        {"id": "Q1.o2", "code": "2", "text": "Homme ou garçon", "other": False},
        {"id": None, "code": "9", "text": "Préfère ne pas répondre", "other": False},
    ]


# --- The editor --------------------------------------------------------------------------------


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_add_a_single_choice_in_a_section(path):
    app = _open(path)
    _run(app, app.button(key="design-S1-add").click())
    _run(app, app.text_area(key=NEW + "text").set_value("Avez-vous un animal ?"))
    app.session_state[NEW + "options"] = [
        {"id": None, "code": "1", "text": "Oui", "other": False},
        {"id": None, "code": "2", "text": "Non", "other": False},
    ]
    _run(app, app.button(key=NEW + "save").click())
    assert [s.value for s in app.success] == ["Enregistré."]
    project = load_project(path)
    added = project.questionnaire.questions[2]
    assert (added.question_id, added.section, added.text) == ("Q6", "S1", "Avez-vous un animal ?")
    assert [(o.code, o.text) for o in added.options] == [("1", "Oui"), ("2", "Non")]
    assert "Q6" in [e.name for e in project.variables]  # its variable, planned at once
    assert NEW + "save" not in [b.key for b in app.button]  # the form closed
    assert not (app.session_state[c.DRAFTS] if c.DRAFTS in app.session_state else [])  # noqa: SIM401


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_grid_with_its_columns_and_items(path):
    app = _open(path)
    _run(app, app.button(key="design-S2-add").click())
    _run(app, app.selectbox(key=NEW + "kind").set_value("grid"))
    _run(app, app.text_area(key=NEW + "text").set_value("À quel point êtes-vous d'accord ?"))
    app.session_state[NEW + "options"] = [
        {"id": None, "code": str(n), "text": t}
        for n, t in enumerate(["Pas du tout", "Tout à fait"], 1)
    ]
    app.session_state[NEW + "rows"] = [
        {"id": None, "code": "SQ001", "text": "Je dors bien."},
        {"id": None, "code": "SQ002", "text": "Je me réveille tôt."},
    ]
    _run(app, app.radio(key=NEW + "provenance").set_value("source"))
    _run(app, app.text_input(key=NEW + "source").set_value("Échelle fictive, manuel"))
    _run(app, app.number_input(key=NEW + "page").set_value(3))
    _run(app, app.button(key=NEW + "save").click())
    grid = _questions(path)[-1]
    assert grid.kind == "grid" and [r.code for r in grid.rows] == ["SQ001", "SQ002"]
    assert grid.provenance.source == "Échelle fictive, manuel" and grid.provenance.page == 3
    assert any(g.question == grid.question_id for g in load_project(path).groups)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_modify_keeps_the_decisions_of_its_variables(path):
    project = load_project(path)
    project.variable("Q4_SQ001").label = TrackedValue[str](value="Réveils", origin="human")
    save_project(project, path)
    app = _open(path)
    _run(app, app.button(key="design-Q4-edit").click())
    prefix = "design-q-Q4-1-"
    assert app.text_area(key=prefix + "text").value.startswith("Au cours du dernier mois")
    _run(app, app.text_area(key=prefix + "text").set_value("Au cours des deux dernières semaines…"))
    _run(app, app.button(key=prefix + "save").click())
    project = load_project(path)
    assert design.find(project, "Q4").text == "Au cours des deux dernières semaines…"
    assert project.variable("Q4_SQ001").label.value == "Réveils"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_what_a_question_needs_is_said_and_nothing_is_saved(path):
    before = path.read_bytes()
    app = _open(path)
    _run(app, app.button(key="design-S1-add").click())
    _run(app, app.button(key=NEW + "save").click())
    errors = [e.value for e in app.error]
    assert any("Le texte de la question est vide." in e for e in errors)
    assert any("Donnez au moins un choix de réponse." in e for e in errors)
    assert path.read_bytes() == before
    assert NEW + "save" in [b.key for b in app.button]  # the form stays open


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_move_and_remove(path):
    app = _open(path)
    _run(app, app.button(key="design-Q2-up").click())
    assert [q.question_id for q in _questions(path)][:2] == ["Q2", "Q1"]
    _run(app, app.button(key="design-Q2-remove").click())
    assert "Q2" not in [q.question_id for q in _questions(path)]
    assert "Q2" not in [e.name for e in load_project(path).variables]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_sections(path):
    app = _open(path)
    # In a form, what is typed is sent with its button, in the same run.
    app.text_input(key="design-new-section-title").set_value("Pour finir")
    _run(app, app.button(key="FormSubmitter:design-new-section-form-Ajouter la section").click())
    assert app.text_input(key="design-new-section-title").value == ""  # emptied once saved
    sections = load_project(path).questionnaire.sections
    assert [s.title for s in sections] == ["Vous", "Votre sommeil", "Pour finir"]
    _run(app, app.text_input(key="design-S3-title").set_value("Pour terminer"))
    _run(app, app.button(key="design-S3-save").click())
    _run(app, app.button(key="design-S3-up").click())
    titles = [s.title for s in load_project(path).questionnaire.sections]
    assert titles == ["Vous", "Pour terminer", "Votre sommeil"]
    _run(app, app.button(key="design-S1-remove").click())
    assert any("Retirez ou déplacez" in e.value for e in app.error)
    _run(app, app.button(key="design-S3-remove").click())
    assert len(load_project(path).questionnaire.sections) == 2


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_filter_by_section(path):
    app = _open(path)
    _run(app, app.selectbox(key="design-section-filter").set_value("S2"))
    keys = [b.key for b in app.button]
    assert "design-Q4-edit" in keys and "design-Q1-edit" not in keys
    numbers = [m.value for m in app.markdown if m.value.startswith("**")]
    assert numbers[0].startswith("**3.**")  # the numbering of the whole questionnaire


# --- Drafts and the check at writing ---------------------------------------------------------


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_question_typed_and_not_saved_is_a_draft(path):
    app = _open(path)
    _run(app, app.button(key="design-Q1-edit").click())
    _run(app, app.text_area(key="design-q-Q1-1-text").set_value("Votre genre ?"))
    app.session_state["mode"] = "glossary"
    app.run()
    notice = [w.value for w in app.warning if "non enregistrée" in w.value]
    assert notice == ["Saisie non enregistrée : Questionnaire, Q1."]
    _run(app, app.button(key="draft-back-0").click())
    assert app.session_state["mode"] == "design"
    assert app.text_area(key="design-q-Q1-1-text").value == "Votre genre ?"
    assert design.find(load_project(path), "Q1").text == "Quel est votre genre ?"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_question_opened_twice_and_saved_leaves_no_draft(path):
    # Seen in the author's trial (2026-10-20): the choices of the first opening stayed in the
    # session and, once the second saved others, read as a draft.
    app = _open(path)
    _run(app, app.button(key="design-Q1-edit").click())
    _run(app, app.button(key="design-q-Q1-1-cancel").click())
    _run(app, app.button(key="design-Q1-edit").click())
    rows = app.session_state["design-q-Q1-2-options"]
    app.session_state["design-q-Q1-2-options"] = [{**rows[0], "text": "Femme ou fille"}, *rows[1:]]
    _run(app, app.button(key="design-q-Q1-2-save").click())
    assert design.find(load_project(path), "Q1").options[0].text == "Femme ou fille"
    app.session_state["mode"] = "design_review"
    app.run()
    assert not [w.value for w in app.warning if "non enregistrée" in w.value]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_save_refused_when_the_file_changed_elsewhere(path):
    app = _open(path)
    _run(app, app.button(key="design-Q1-edit").click())
    other = load_project(path)
    design.modify_section(other, "S1", "Vous, ailleurs")
    save_project(other, path)
    _run(app, app.text_area(key="design-q-Q1-1-text").set_value("Votre genre ?"))
    _run(app, app.button(key="design-q-Q1-1-save").click())
    assert any("modifié ailleurs" in e.value for e in app.error)
    project = load_project(path)
    assert design.find(project, "Q1").text == "Quel est votre genre ?"
    assert project.questionnaire.sections[0].title == "Vous, ailleurs"  # the other's kept


# --- 150 questions ---------------------------------------------------------------------------


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_questionnaire_of_150_questions_stays_quick(tmp_path):
    project = design.new_project("Grand", "fr", "2026-10-20")
    for n in range(150):
        kind = ("single", "open", "grid", "checkbox")[n % 4]
        options = (Item("Oui", "1"), Item("Non", "2")) if kind != "open" else ()
        rows = (Item("a", "SQ001"), Item("b", "SQ002")) if kind == "grid" else ()
        design.add_question(
            project,
            Draft(kind=kind, text=f"Question {n} ?", section="S1", options=options, rows=rows),
        )
    path = tmp_path / "grand.dd.json"
    save_project(project, path)
    app = _open(path)
    started = time.perf_counter()
    _run(app, app.button(key="design-Q75-edit").click())
    _run(app, app.text_area(key="design-q-Q75-1-text").set_value("Question changée ?"))
    _run(app, app.button(key="design-q-Q75-1-save").click())
    assert time.perf_counter() - started < 6  # about 1 s measured; generous for a slow computer
    assert design.find(load_project(path), "Q75").text == "Question changée ?"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_question_reopened_after_a_save_shows_its_text(path):
    """Seen in the browser: reopened under the same keys, the text showed empty. Each opening
    gives the fields new keys."""
    app = _open(path)
    _run(app, app.button(key="design-Q1-edit").click())
    _run(app, app.button(key="design-q-Q1-1-save").click())
    _run(app, app.button(key="design-Q1-edit").click())
    assert app.text_area(key="design-q-Q1-2-text").value == "Quel est votre genre ?"
