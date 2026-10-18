"""v0.16, step A1 (D-126): a decision field never starts from a computed value. What the tool
computes is named on a button that puts it into the field, without saving anything."""

import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.project import load_project, save_project
from ddict.review import logic, study
from ddict.workflow import add_questionnaire, profile_database

EXAMPLES = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"
APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
SOURCE = "Manuel fictif, p. 4"
ITEMS = [f"sommeil_q{i}" for i in range(1, 9)]


@pytest.fixture
def project_path(tmp_path):
    for name in ("etude-sommeil.sav", "questionnaire-sommeil.pdf"):
        shutil.copy(EXAMPLES / name, tmp_path / name)
    project, path = profile_database(tmp_path / "etude-sommeil.sav")
    add_questionnaire(project, tmp_path / "questionnaire-sommeil.pdf")
    save_project(project, path)
    return path


def _app(path: Path, mode: str) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=30)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = mode
    app.run()
    assert not app.exception, app.exception
    return app


def _variable(app: AppTest, name: str) -> None:
    app.sidebar.radio(key="filter").set_value("all").run()
    app.sidebar.selectbox(key="variable").select(name).run()
    assert not app.exception, app.exception


def _errors(app: AppTest) -> list[str]:
    return [e.value for e in app.error]


# --- Groups: reversed items and the scoring. ---


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_likely_reversed_items_are_offered_not_confirmed(project_path):
    app = _app(project_path, "groups")
    assert app.multiselect(key="reverse-G1").value == []
    offer = app.button(key="offer-reverse-G1")
    assert offer.label == "Reprendre les items probables (sommeil_q3, sommeil_q6)"
    offer.click().run()
    assert app.multiselect(key="reverse-G1").value == ["sommeil_q3", "sommeil_q6"]
    assert load_project(project_path).groups[0].reverse_items == []  # nothing saved
    app.button(key="save-reverse-G1").click().run()
    assert load_project(project_path).groups[0].reverse_items == ["sommeil_q3", "sommeil_q6"]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_scoring_starts_empty(project_path):
    app = _app(project_path, "groups")
    assert app.multiselect(key="scoring-items-G1").value == []
    assert app.radio(key="scoring-how-G1").value is None
    assert app.radio(key="scoring-rule-G1").value is None
    for part in ("min", "max", "least"):
        assert app.number_input(key=f"scoring-{part}-G1").value is None
    assert app.button(key="offer-scoring-items-G1").label == "Prendre les 8 items du groupe"
    offer = app.button(key="offer-bounds-G1")
    assert offer.label == "Reprendre les bornes des étiquettes (1 à 5)"
    offer.click().run()
    assert app.number_input(key="scoring-min-G1").value == 1
    assert app.number_input(key="scoring-max-G1").value == 5
    assert load_project(project_path).groups[0].scoring is None  # nothing saved


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_scoring_without_its_calculation_is_refused(project_path):
    app = _app(project_path, "groups")
    app.button(key="offer-scoring-items-G1").click().run()
    app.button(key="offer-bounds-G1").click().run()
    app.text_input(key="scoring-name-G1").input("sommeil_total")
    app.text_input(key="scoring-source-G1").input(SOURCE)
    app.button(key="save-scoring-G1").click().run()
    assert any("Choisissez le calcul du score" in e for e in _errors(app)), _errors(app)
    assert load_project(project_path).groups[0].scoring is None
    # The fields keep what was typed after a refusal.
    assert app.multiselect(key="scoring-items-G1").value == ITEMS


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_saved_scoring_comes_back_as_saved(project_path):
    app = _app(project_path, "groups")
    app.button(key="offer-scoring-items-G1").click().run()
    app.button(key="offer-bounds-G1").click().run()
    app.radio(key="scoring-how-G1").set_value("mean")
    app.number_input(key="scoring-least-G1").set_value(0)
    app.text_input(key="scoring-name-G1").input("sommeil_moyen")
    app.text_input(key="scoring-source-G1").input(SOURCE)
    app.button(key="save-scoring-G1").click().run()
    assert not _errors(app), _errors(app)
    again = _app(project_path, "groups")
    assert again.radio(key="scoring-how-G1").value == "mean"
    assert again.number_input(key="scoring-least-G1").value == 0  # every item required
    assert again.multiselect(key="scoring-items-G1").value == ITEMS


def test_the_choices_a_structured_scoring_needs(project_path):
    project = load_project(project_path)

    def chosen(how, least, rule):
        study.set_scoring_chosen(
            project, "G1", ITEMS, how, 1.0, 5.0, least, "sommeil_total", SOURCE, "", rule
        )

    with pytest.raises(logic.ReviewError, match="calcul du score"):
        chosen(None, 0, None)
    with pytest.raises(logic.ReviewError, match="répondus, au minimum"):
        chosen("sum", None, None)
    with pytest.raises(logic.ReviewError, match="items manquants"):
        chosen("sum", 6, None)  # a sum that accepts missing items says its rule
    chosen("mean", 6, None)  # a mean has no such rule
    assert project.groups[0].scoring.min_items_answered == 6
    chosen("sum", 0, None)  # every item required: no rule needed
    assert project.groups[0].scoring.min_items_answered is None
    chosen("sum", 6, "sum_answered")
    assert project.groups[0].scoring.missing_rule == "sum_answered"
    # A scoring written as a note needs no calculation (D-060).
    note = "Voir le manuel."
    study.set_scoring_chosen(project, "G1", [], None, None, None, None, "", SOURCE, note, None)
    assert project.groups[0].scoring.note == "Voir le manuel."


# --- Variables: the sourced fields and the question to link. ---


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_range_and_threshold_start_empty(project_path):
    app = _app(project_path, "variables")
    _variable(app, "sommeil_q1")
    for key in ("range-min", "range-max", "threshold-value"):
        assert app.number_input(key=f"{key}-sommeil_q1").value is None
    app.text_input(key="range-source-sommeil_q1").input(SOURCE)
    app.button(key="save-range-sommeil_q1").click().run()
    assert any("Tapez le minimum et le maximum" in e for e in _errors(app)), _errors(app)
    assert load_project(project_path).variable("sommeil_q1").theoretical_range is None


def test_empty_numbers_are_said_with_the_other_problems(project_path):
    project = load_project(project_path)
    with pytest.raises(logic.ReviewError) as error:
        logic.add_threshold(project, "sommeil_q1", None, "", "")
    assert str(error.value).startswith("Tapez la valeur du seuil.")
    assert "signification" in str(error.value)
    with pytest.raises(logic.ReviewError, match="Tapez le minimum"):
        logic.set_theoretical_range(project, "sommeil_q1", 1.0, None, SOURCE)
    logic.set_theoretical_range(project, "sommeil_q1", 1.0, 5.0, SOURCE)
    logic.add_threshold(project, "sommeil_q1", 0.0, "Aucun réveil", SOURCE)  # 0 is a value
    assert project.variable("sommeil_q1").thresholds[0].value == 0


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_computed_question_is_offered_not_chosen(project_path):
    app = _app(project_path, "variables")
    _variable(app, "age")
    choice = app.selectbox(key="question-age")
    assert choice.value is None
    first = choice.options[0]
    assert first.startswith("Q")
    offer = app.button(key="offer-question-age")
    assert offer.label == f"Reprendre la proposition du calcul : {first.split(' — ')[0]}"
    app.button(key="save-question-age").click().run()
    assert any("Choisissez une question" in e for e in _errors(app)), _errors(app)
    assert load_project(project_path).variable("age").question.value is None
    offer.click().run()
    app.button(key="save-question-age").click().run()
    assert load_project(project_path).variable("age").question.value == first.split(" — ")[0]
