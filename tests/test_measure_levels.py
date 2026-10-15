"""v0.8, step 3: the measure level, proposed by rules and decided by a person (D-063)."""

import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.export import render_markdown
from ddict.export.documented import _metadata
from ddict.export.syntax import spss
from ddict.export.wording import entry_anomalies
from ddict.io import read_database
from ddict.llm.messages import variable_payload
from ddict.project import build_project, fingerprint, load_project, measure
from ddict.project.model import TrackedValue, ValueLabel
from ddict.review import levels
from ddict.review.logic import ReviewError
from ddict.workflow import profile_database, tasks

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")
NOW = "2026-10-15T12:00:00"


def _proposed(project) -> dict[str, str]:
    return {
        e.name: e.measure_level.value
        for e in project.variables
        if e.measure_level.status == "proposed"
    }


@pytest.fixture(scope="module")
def csv_project():
    return build_project(read_database(EXAMPLES / "etude-sommeil.csv"))


def test_rules_where_the_file_has_no_level(csv_project):
    proposed = _proposed(csv_project)
    # Items of a probable scale: ordinal, even without labels in a CSV.
    assert all(proposed[f"sommeil_q{i}"] == "ordinal" for i in range(1, 9))
    assert proposed["anx3"] == "ordinal"
    # Ticked or not: nominal. A quantity: scale. Categories written as text: nominal.
    assert proposed["aide_tcc"] == "nominal"
    assert proposed["age"] == proposed["heures_sommeil"] == "scale"
    assert proposed["langue_maison"] == "nominal"
    # A few unlabelled codes (1, 2, 3, 9): only the team knows. No level for an identifier,
    # a free text, a birth date, a date, an empty variable or one of mixed types.
    for name in ("genre", "id_participant", "commentaire", "date_naissance", "date_passation",
                 "q_retiree", "taille_cm"):  # fmt: skip
        assert name not in proposed, name
    # Nothing is in force before a person accepts.
    assert measure.level(csv_project.variable("age")) is None


def test_a_doubtful_level_of_the_file():
    project = build_project(read_database(EXAMPLES / "travail-t2_surveymonkey.sav"))
    entry = project.variable("q0003_0001")
    assert entry.file.measure_level == "scale"
    assert entry.measure_level.value == "ordinal" and entry.measure_level.origin == "rule"
    assert measure.level(entry) == "scale"  # the file's stands until a person decides
    assert any("douteux" in a for a in entry_anomalies(entry))
    levels.apply_table(project, {}, {"q0003_0001": "accept"}, now=NOW)
    assert measure.level(entry) == "ordinal"
    assert not any("douteux" in a for a in entry_anomalies(entry))
    # The sav's other levels stand: no proposal where the file is sure.
    assert set(_proposed(project)) == {f"q0003_{i:04d}" for i in range(2, 13)}


def test_decisions_in_the_table():
    project = build_project(read_database(EXAMPLES / "etude-sommeil.csv"))
    done = levels.apply_table(
        project,
        {"genre": "nominal", "age": "scale"},  # age: as proposed, so not a change
        {"sommeil_q1": "accept", "aide_tcc": "reject", "age": "accept"},
        now=NOW,
    )
    assert done == 4
    assert measure.level(project.variable("genre")) == "nominal"  # chosen: decided
    assert project.variable("genre").measure_level.origin == "human"
    assert measure.level(project.variable("sommeil_q1")) == "ordinal"
    assert measure.level(project.variable("aide_tcc")) is None  # rejected
    assert measure.level(project.variable("age")) == "scale"
    # A proposal changed by a person: corrected, the proposal kept.
    levels.apply_table(project, {"sommeil_q2": "scale"}, {}, now=NOW)
    assert project.variable("sommeil_q2").measure_level.status == "corrected"
    assert project.variable("sommeil_q2").measure_level.proposed_value == "ordinal"
    with pytest.raises(ReviewError, match="n'attendent plus de décision : sommeil_q1"):
        levels.apply_table(project, {}, {"sommeil_q1": "accept"}, now=NOW)
    with pytest.raises(ReviewError, match="niveau modifié et « Rejeter »"):
        levels.apply_table(project, {"sommeil_q3": "scale"}, {"sommeil_q3": "reject"}, now=NOW)
    with pytest.raises(ReviewError, match="niveau de mesure inconnu"):
        levels.apply_table(project, {"sommeil_q3": "continu"}, {}, now=NOW)
    # Nothing changed by the refused calls.
    assert project.variable("sommeil_q3").measure_level.status == "proposed"


def test_rules_never_replace_a_decision_and_follow_new_labels():
    project = build_project(read_database(EXAMPLES / "etude-sommeil.csv"))
    levels.apply_table(project, {}, {"aide_tcc": "reject", "age": "accept"}, now=NOW)
    measure.propose(project)
    assert project.variable("aide_tcc").measure_level.status == "rejected"
    assert project.variable("age").measure_level.status == "validated"
    # Labels accepted later: the waiting proposal follows the rules again.
    entry = project.variable("nb_reveils")  # a few unlabelled codes: no proposal
    assert entry.measure_level.value is None
    entry.value_labels = TrackedValue[list[ValueLabel]](
        value=[ValueLabel(code=0, label="Aucun")], origin="questionnaire", status="validated"
    )
    measure.propose(project)
    assert entry.measure_level.value == "nominal"


def test_the_level_in_force_everywhere():
    project = build_project(read_database(EXAMPLES / "travail-t2_surveymonkey.sav"))
    before = fingerprint.fingerprint(project)
    assert "VARIABLE LEVEL q0003_0001 (SCALE)." in spss(project, "2026-10-15")
    levels.apply_table(project, {}, {"q0003_0001": "accept"}, now=NOW)
    assert "VARIABLE LEVEL q0003_0001 (ORDINAL)." in spss(project, "2026-10-15")
    metadata, _refused = _metadata(project, [e.name for e in project.variables])
    assert metadata["variable_measure"]["q0003_0001"] == "ordinal"
    assert variable_payload(project.variable("q0003_0001"), [], {})["measure_level"] == "ordinal"
    assert "Niveau de mesure : ordinal" in render_markdown(project)
    assert fingerprint.fingerprint(project) != before


def test_the_work_export_shows_a_proposal(csv_project):
    assert "Niveau de mesure : ordinal [proposé]" in render_markdown(csv_project, kind="work")
    assert "Niveau de mesure : ordinal" not in render_markdown(csv_project)


def test_the_dashboard(csv_project):
    found = [t.text.format(n=t.count) for t in tasks(csv_project)]
    assert f"Niveaux de mesure proposés : {len(_proposed(csv_project))}" in found


# --- In the interface. ---


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_table_on_the_base_page(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.csv", tmp_path / "etude-sommeil.csv")
    _project, path = profile_database(tmp_path / "etude-sommeil.csv")
    app = AppTest.from_file(APP, default_timeout=30)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "base"
    app.run()
    assert not app.exception, app.exception
    waiting = len(_proposed(load_project(path)))
    app.button(key="levels-prefill").click().run()  # filled in, nothing saved yet
    assert not app.exception, app.exception
    assert len(_proposed(load_project(path))) == waiting
    app.button(key="levels-save").click().run()
    assert not app.exception, app.exception
    project = load_project(path)
    assert not _proposed(project)
    assert measure.level(project.variable("sommeil_q1")) == "ordinal"
    assert any(f"{waiting} niveaux enregistrés" in s.value for s in app.success)
