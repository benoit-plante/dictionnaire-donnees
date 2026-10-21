"""v0.21, step 4: the block "Posée si" of the editor, on a question and on a section; the
boxes of random order and of attention check; the review's new points and the estimated
duration; every save through `c.save`, with drafts (D-124) and the check at writing (D-129).
Nothing real: the questionnaire of `test_skip`."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import design, design_points
from ddict.design import DesignError
from ddict.project import load_project, save_project
from ddict.review.ui import common as c
from ddict.review.ui.design_view import condition_from, condition_rows, target_labels
from test_skip import famille, term, when

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
CHILDREN = "3. Avez-vous des enfants ?"


@pytest.fixture
def path(tmp_path):
    found = tmp_path / "Familles" / "familles.dd.json"
    found.parent.mkdir()
    save_project(famille(), found)
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


def _set(app, key, value) -> None:
    app.session_state[key] = value


# --- Without Streamlit: a condition as a table. ---


def test_the_targets_of_a_condition():
    labels = target_labels(famille())
    assert labels[CHILDREN] == "Q3"
    assert labels["2. Votre âge ?"] == "Q2"
    assert labels["7. Votre quartier… — est sûr."] == "Q7.r2"
    assert labels["10. Vos transports ? — Vélo"] == "Q10.o2"
    assert "10. Vos transports ? — Autre" not in labels  # the "other" option
    assert not any(t == "Q7" or t == "Q10" for t in labels.values())  # whole questions


def test_a_condition_to_its_rows_and_back():
    project = famille()
    found = when(term("Q3", "in", ["1", "2"]), term("Q10.o2", "checked"), combine="any")
    rows = condition_rows(project, found)
    assert rows == [
        {"target": CHILDREN, "operator": "parmi", "value": "1, 2"},
        {"target": "10. Vos transports ? — Vélo", "operator": "est cochée", "value": ""},
    ]
    assert condition_from(project, rows, "any") == found
    assert condition_from(project, [{"target": "", "operator": "", "value": ""}], "all") is None


@pytest.mark.parametrize(
    ("row", "reason"),
    [
        ({"target": "", "operator": "=", "value": "1"}, "choisissez la question ou la variable"),
        ({"target": CHILDREN, "operator": "", "value": "1"}, "choisissez un opérateur"),
        ({"target": CHILDREN, "operator": "=", "value": ""}, "donnez une valeur"),
        ({"target": CHILDREN, "operator": "parmi", "value": " , "}, "au moins un code"),
    ],
)
def test_a_line_that_cannot_be_a_term(row, reason):
    with pytest.raises(DesignError, match=reason):
        condition_from(famille(), [row], "all")


# --- The editor. ---


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_condition_set_changed_and_removed_on_a_question(path):
    app = _open(path)
    _run(app, app.button(key="design-Q4-edit").click())
    prefix = "design-q-Q4-1-"
    _set(app, prefix + "terms", [{"target": CHILDREN, "operator": "=", "value": "1"}])
    _run(app, app.button(key=prefix + "save").click())
    assert [s.value for s in app.success] == ["Enregistré."]
    project = load_project(path)
    assert design.find(project, "Q4").condition == when(term("Q3", "eq", "1"))
    assert project.variable("nbenfants").asked_if.value == [when(term("enfants", "eq", 1))]
    assert "Posée si Q3 (enfants) = 1 (Oui)" in [x.value for x in app.caption]
    # Changed: "or", two lines.
    _run(app, app.button(key="design-Q4-edit").click())
    prefix = "design-q-Q4-2-"
    assert app.session_state[prefix + "terms"] == [
        {"target": CHILDREN, "operator": "=", "value": "1"}
    ]
    _set(
        app,
        prefix + "terms",
        [
            {"target": CHILDREN, "operator": "≠", "value": "2"},
            {"target": "2. Votre âge ?", "operator": "≥", "value": "18"},
        ],
    )
    _run(app, app.radio(key=prefix + "combine").set_value("any"))
    _run(app, app.button(key=prefix + "save").click())
    assert design.find(load_project(path), "Q4").condition == when(
        term("Q3", "ne", "2"), term("Q2", "ge", 18), combine="any"
    )
    # Removed: no line.
    _run(app, app.button(key="design-Q4-edit").click())
    _set(app, "design-q-Q4-3-terms", [])
    _run(app, app.button(key="design-q-Q4-3-save").click())
    assert design.find(load_project(path), "Q4").condition is None
    assert load_project(path).variable("nbenfants").asked_if is None


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_condition_refused_is_said_and_nothing_is_saved(path):
    before = path.read_bytes()
    app = _open(path)
    _run(app, app.button(key="design-Q4-edit").click())
    prefix = "design-q-Q4-1-"
    _set(app, prefix + "terms", [{"target": "4. Combien ?", "operator": "≥", "value": "1"}])
    _run(app, app.button(key=prefix + "save").click())
    assert any("elle-même" in e.value for e in app.error)
    _set(app, prefix + "terms", [{"target": CHILDREN, "operator": "=", "value": "7"}])
    _run(app, app.button(key=prefix + "save").click())
    assert any("7 n'est pas un choix" in e.value for e in app.error)
    assert path.read_bytes() == before
    assert prefix + "save" in [b.key for b in app.button]  # the form stays open


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_condition_typed_and_not_saved_is_a_draft(path):
    app = _open(path)
    _run(app, app.button(key="design-Q4-edit").click())
    _set(app, "design-q-Q4-1-terms", [{"target": CHILDREN, "operator": "=", "value": "1"}])
    app.session_state["mode"] = "glossary"
    app.run()
    notice = [w.value for w in app.warning if "non enregistrée" in w.value]
    assert notice == ["Saisie non enregistrée : Questionnaire, Q4."]
    assert design.find(load_project(path), "Q4").condition is None


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_condition_refused_when_the_file_changed_elsewhere(path):
    app = _open(path)
    _run(app, app.button(key="design-Q4-edit").click())
    other = load_project(path)
    design.modify_section(other, "S1", "Vous, ailleurs")
    save_project(other, path)
    _set(app, "design-q-Q4-1-terms", [{"target": CHILDREN, "operator": "=", "value": "1"}])
    _run(app, app.button(key="design-q-Q4-1-save").click())
    assert any("modifié ailleurs" in e.value for e in app.error)
    project = load_project(path)
    assert design.find(project, "Q4").condition is None
    assert project.questionnaire.sections[0].title == "Vous, ailleurs"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_condition_and_a_random_order_on_a_section(path):
    app = _open(path)
    _set(app, "design-S2-terms", [{"target": CHILDREN, "operator": "=", "value": "1"}])
    _run(app, app.checkbox(key="design-S2-shuffle").check())
    _run(app, app.button(key="design-S2-save").click())
    section = load_project(path).questionnaire.sections[1]
    assert section.condition == when(term("Q3", "eq", "1")) and section.shuffle
    assert section.title == "Votre quartier"  # its title kept
    captions = [x.value for x in app.caption]
    assert "Posée si Q3 (enfants) = 1 (Oui)" in captions
    assert "Questions de la section en ordre aléatoire." in captions
    _set(app, "design-S2-terms", [])
    _run(app, app.checkbox(key="design-S2-shuffle").uncheck())
    _run(app, app.button(key="design-S2-save").click())
    section = load_project(path).questionnaire.sections[1]
    assert section.condition is None and not section.shuffle


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_random_order_and_attention_checks_in_the_form(path):
    app = _open(path)
    _run(app, app.button(key="design-Q7-edit").click())
    prefix = "design-q-Q7-1-"
    _run(app, app.checkbox(key=prefix + "shuffle").check())
    rows = app.session_state[prefix + "rows"]
    assert rows[1]["attention"] == ""
    _set(app, prefix + "rows", [rows[0], {**rows[1], "attention": "4"}])
    _run(app, app.button(key=prefix + "save").click())
    project = load_project(path)
    grid = design.find(project, "Q7")
    assert grid.shuffle and grid.rows[1].attention == ["4"]
    assert next(g for g in project.groups if g.question == "Q7").attached == ["climat_SQ002"]
    assert "Item de contrôle « est sûr. » : bonnes réponses 4." in [x.value for x in app.caption]
    _run(app, app.button(key="design-Q5-edit").click())
    _run(app, app.text_input(key="design-q-Q5-1-attention").set_value("1, 2"))
    _run(app, app.button(key="design-q-Q5-1-save").click())
    assert design.find(load_project(path), "Q5").attention == ["1", "2"]


# --- The review. ---


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_review_shows_the_duration_and_a_section_point(path):
    project = load_project(path)
    design.set_condition(project, "S2", when(term("Q3", "eq", "1")))
    save_project(project, path)
    app = _open(path, "design_review")
    texts = [m.value for m in app.markdown]
    assert any(t.startswith("**Durée estimée** : environ") for t in texts)
    assert "**Section** Votre quartier" in texts
    index = next(n for n, b in enumerate(app.button) if b.label == "Aller à la section")
    _run(app, app.button[index].click())
    assert app.session_state["mode"] == "design"
    assert app.session_state["design-section-filter"] == "S2"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_section_point_kept(path):
    project = load_project(path)
    design.set_condition(project, "S2", when(term("Q3", "eq", "1")))
    save_project(project, path)
    app = _open(path, "design_review")
    found = design_points.points(load_project(path))
    index = next(n for n, p in enumerate(found) if p.code == "section_without_display")
    _run(app, app.button(key=f"design-review-keep-{index}").click())
    kept = load_project(path).design.kept
    assert [(k.code, k.target) for k in kept] == [("section_without_display", "S2")]
    assert not (app.session_state[c.DRAFTS] if c.DRAFTS in app.session_state else [])  # noqa: SIM401
