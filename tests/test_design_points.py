"""v0.20, step D3: the review of a designed questionnaire (`ddict.design_points`, the page
"Relecture") — points all computed, each with its place to be settled; "Garder tel quel"
closes one while its question says the same; the code of a question decided in its form
(D-156). A fictional questionnaire only."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import design, design_points
from ddict.design import Draft, Item
from ddict.project import load_project, save_project
from ddict.project.model import TrackedValue
from projet_concu import project as designed

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
NOW = "2026-10-20T09:00:00"


def _codes(project, question=None):
    return [
        (p.question, p.code)
        for p in design_points.points(project)
        if question is None or p.question == question
    ]


def _add(project, **fields):
    defaults = {"kind": "single", "text": "Question ?", "section": "S1"}
    return design.add_question(project, Draft(**{**defaults, **fields}))


# --- Without Streamlit -------------------------------------------------------------------------


def test_the_points_of_the_fictional_questionnaire():
    project = designed()
    assert _codes(project) == [
        ("Q1", "code_undecided"), ("Q2", "code_undecided"), ("Q4", "code_undecided"),
        ("Q4", "instrument_without_name"), ("Q5", "code_undecided"),
    ]  # fmt: skip
    pages = {p.code: p.page for p in design_points.points(project)}
    assert pages == {"code_undecided": "design", "instrument_without_name": "groups"}


def test_codes_missing_or_twice():
    project = designed()
    qid = _add(project, options=(Item("Oui", "1"), Item("Non", "1"), Item("Ne sais pas")))
    assert ("missing_code") in [c for _q, c in _codes(project, qid)]
    twice = next(p for p in design_points.points(project) if p.code == "duplicate_code")
    assert twice.detail == {"codes": "1"} and twice.text == "Code en double : 1."


def test_categories_that_overlap_or_leave_a_gap():
    project = designed()
    qid = _add(
        project,
        text="Quel âge avez-vous ?",
        options=(Item("18-25 ans", "1"), Item("25 à 35 ans", "2"), Item("40-50 ans", "3")),
    )
    found = {p.code: p.text for p in design_points.points(project) if p.question == qid}
    assert found["overlap"] == "Catégories qui se chevauchent : « 18-25 ans » et « 25 à 35 ans »."
    assert found["gap"] == "Catégories qui laissent un trou : « 25 à 35 ans » et « 40-50 ans »."


def test_a_required_question_without_a_refusal():
    project = designed()
    without = _add(project, required=True, options=(Item("Oui", "1"), Item("Non", "2")))
    with_it = _add(
        project, required=True, options=(Item("Oui", "1"), Item("Préfère ne pas répondre", "9"))
    )
    assert ("required_without_refusal") in [c for _q, c in _codes(project, without)]
    assert "required_without_refusal" not in [c for _q, c in _codes(project, with_it)]


def test_a_grid_without_instruction():
    project = designed()
    qid = _add(
        project,
        kind="grid",
        text="À quel point ?",
        options=(Item("Peu", "1"), Item("Beaucoup", "2")),
        rows=(Item("a", "SQ001"),),
    )
    assert "grid_without_instruction" in [c for _q, c in _codes(project, qid)]


def test_two_codes_that_limesurvey_would_make_the_same():
    project = designed()
    design.decide_code(project, "Q1", "write", now=NOW, value="aides_s")
    design.decide_code(project, "Q2", "write", now=NOW, value="aide_ss")
    shared = [p for p in design_points.points(project) if p.code == "code_shared"]
    assert {p.question for p in shared} == {"Q1", "Q2"}
    assert shared[0].text.startswith("Même code LimeSurvey qu'une autre question")


def test_names_in_conflict():
    project = designed()
    project.variable("Q1").new_name = TrackedValue[str](value="age", origin="human")
    project.variable("Q2").new_name = TrackedValue[str](value="age", origin="human")
    conflicts = [p for p in design_points.points(project) if p.code == "name_conflict"]
    assert [(p.question, p.page) for p in conflicts] == [("Q1", "names"), ("Q2", "names")]


def test_kept_as_it_is_until_the_question_changes():
    project = designed()
    point = next(p for p in design_points.points(project) if p.code == "instrument_without_name")
    design_points.keep(project, point, NOW)
    assert ("Q4", "instrument_without_name") not in _codes(project)
    assert design_points.is_kept(project, point)
    question = design.find(project, "Q4")
    changed = Draft(
        kind="grid",
        text=question.text + " (révisé)",
        section="S2",
        instruction=question.instruction,
        provenance=question.provenance,
        options=tuple(Item(o.text, o.code, item_id=o.option_id) for o in question.options),
        rows=tuple(Item(r.text, r.code, item_id=r.row_id) for r in question.rows),
    )
    design.modify_question(project, "Q4", changed)
    assert ("Q4", "instrument_without_name") in _codes(project)  # back, the question changed


# --- The interface -----------------------------------------------------------------------------


@pytest.fixture
def path(tmp_path):
    found = tmp_path / "Étude conçue" / "conçue.dd.json"
    found.parent.mkdir()
    save_project(designed(), found)
    return found


def _open(path, mode) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = mode
    app.run()
    assert not app.exception, app.exception
    return app


def _run(app, element) -> None:
    element.run()
    assert not app.exception, app.exception


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_review_page(path):
    app = _open(path, "design_review")
    assert [h.value for h in app.header] == ["Relecture"]
    texts = [m.value for m in app.markdown]
    assert any("Grille tirée d'une source sans nom d'instrument" in t for t in texts)
    # Kept as it is: saved, and said apart.
    index = next(
        i for i, p in enumerate(design_points.points(load_project(path)))
        if p.code == "instrument_without_name"
    )  # fmt: skip
    _run(app, app.button(key=f"design-review-keep-{index}").click())
    assert design_points.is_kept(
        load_project(path),
        next(
            p
            for p in design_points.points(load_project(path), kept=True)
            if p.code == "instrument_without_name"
        ),
    )
    assert any("Points gardés tels quels (1)" in e.label for e in app.expander)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_point_leads_to_its_question_open(path):
    app = _open(path, "design_review")
    _run(app, app.button(key="design-review-go-0").click())  # Q1: its code to decide
    assert app.session_state["mode"] == "design"
    assert app.session_state["design-open"] == "Q1"
    assert app.text_area(key="design-q-Q1-1-text").value == "Quel est votre genre ?"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_code_decided_in_the_form(path):
    app = _open(path, "design")
    assert any(":material/warning:" in m.value for m in app.markdown)  # the lines' points
    _run(app, app.button(key="design-Q1-edit").click())
    prefix = "design-q-Q1-1-"
    assert app.text_input(key=prefix + "code").value == ""  # never filled by the tool (D-126)
    _run(app, app.button(key=prefix + "code-offer").click())
    assert app.text_input(key=prefix + "code").value == "genre"
    _run(app, app.button(key=prefix + "save").click())
    project = load_project(path)
    assert [e.name for e in project.variables][:1] == ["genre"]
    assert ("Q1", "code_undecided") not in _codes(project)
    # A code the rules refuse changes nothing.
    before = path.read_bytes()
    _run(app, app.button(key="design-Q2-edit").click())
    _run(app, app.text_input(key="design-q-Q2-1-code").set_value("Âge!"))
    _run(app, app.button(key="design-q-Q2-1-save").click())
    assert any("Code refusé" in e.value for e in app.error)
    assert path.read_bytes() == before
