"""v0.8, step 4: the scoring of a group (D-060) and the description of the database (D-064)."""

import json
import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import naming
from ddict.export import render_markdown
from ddict.export import wording as w
from ddict.io import read_database
from ddict.project import build_project, fingerprint, load_project, save_project
from ddict.project import scoring as sc
from ddict.project.model import Scoring
from ddict.review import study
from ddict.review.logic import ReviewError
from ddict.workflow import profile_database

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
REFERENCE = ROOT / "tests" / "reference"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")
NOW = "2026-10-15T12:00:00"
SOURCE = "Manuel fictif, p. 4"
ITEMS = [f"sommeil_q{i}" for i in range(1, 9)]


@pytest.fixture
def project():
    found = build_project(read_database(EXAMPLES / "etude-sommeil.sav"))
    found.groups[0].reverse_items = ["sommeil_q3", "sommeil_q6"]
    return found


def _score(project, **changes):
    values = dict(items=ITEMS, aggregation="sum", scale_min=1.0, scale_max=5.0, min_items=7,
                  score_name="sommeil_total", source=SOURCE, note="")  # fmt: skip
    values |= changes
    study.set_scoring(project, "G1", **values)
    return project.groups[0].scoring


# --- The scoring. ---


def test_a_structured_scoring(project):
    scoring = _score(project)
    assert sc.score_range(scoring) == (8, 40)
    assert sc.reversed_items(project.groups[0], scoring) == ["sommeil_q3", "sommeil_q6"]
    text = w.scoring_text(project, project.groups[0])
    assert text.startswith("sommeil_total = somme des 8 items, après inversion de ")
    assert "sommeil_q3, sommeil_q6 (6 - x)" in text
    assert "au moins 7 items répondus, sinon manquant" in text
    assert "étendue 8 – 40" in text and text.endswith(f"(source : {SOURCE})")
    assert sc.score_range(_score(project, aggregation="mean")) == (1, 5)
    # Items unticked: neither in the score nor among its reversed items.
    scoring = _score(project, items=ITEMS[:5], min_items=None)
    assert sc.score_range(scoring) == (5, 25)
    assert sc.reversed_items(project.groups[0], scoring) == ["sommeil_q3"]


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"source": " "}, "exige une source"),
        ({"items": [], "note": ""}, "en note"),
        ({"score_name": ""}, "Donnez un nom"),
        ({"scale_min": 5.0, "scale_max": 1.0}, "minimum de l'échelle"),
        ({"min_items": 9}, "dépasse le nombre d'items"),
        ({"score_name": "Sommeil total"}, "Nom de score invalide"),
        ({"score_name": "age"}, "Nom de score invalide"),  # a variable's name
    ],
)
def test_a_scoring_refused(project, changes, message):
    with pytest.raises(ReviewError, match=message):
        _score(project, **changes)
    assert project.groups[0].scoring is None


def test_rules_of_the_project(project):
    _score(project)
    with pytest.raises(ReviewError, match="déjà celui d'un autre groupe"):
        study.set_scoring(project, "G2", [f"anx{i}" for i in range(1, 8)], "sum", 0.0, 3.0,
                          None, "sommeil_total", SOURCE, "")  # fmt: skip
    with pytest.raises(sc.ScoringError) as error:  # an item from elsewhere, said directly
        other = Scoring(items=["age"], aggregation="sum", scale_min=0, scale_max=3,
                        score_name="anx_total", source=SOURCE)  # fmt: skip
        sc.set_scoring(project, "G2", other)
    assert error.value.problems == ["items"]
    survey = build_project(read_database(EXAMPLES / "travail-t2_surveymonkey.sav"))
    checkboxes = next(g for g in survey.groups if g.kind == "multiple_response")
    with pytest.raises(ReviewError, match="cases à cocher"):
        study.set_scoring(survey, checkboxes.group_id, [], "sum", None, None, None, "", SOURCE,
                          "Nombre de cases cochées")  # fmt: skip


def test_a_note_only_and_its_removal(project):
    scoring = _score(project, items=[], note="Voir le manuel : score T normalisé.")
    assert not sc.structured(scoring) and sc.score_range(scoring) is None
    assert w.scoring_text(project, project.groups[0]) == (
        f"Voir le manuel : score T normalisé. (source : {SOURCE})"
    )
    study.remove_scoring(project, "G1")
    assert project.groups[0].scoring is None


def test_scale_bounds_from_the_labels(project):
    assert sc.scale_bounds(project.variable("sommeil_q1")) == (1, 5)
    assert sc.scale_bounds(project.variable("anx1")) == (0, 3)  # -9 "Refus" is a missing code


def test_in_the_exports_and_the_fingerprint(project):
    before = fingerprint.fingerprint(project)
    _score(project)
    assert "- Cotation : sommeil_total = somme des 8 items" in render_markdown(project)
    assert fingerprint.fingerprint(project) != before


def test_an_old_scoring_text_becomes_a_note(tmp_path):
    data = json.loads((REFERENCE / "etude-sommeil-0.2.0.dd.json").read_text(encoding="utf-8"))
    data["groups"][0]["scoring"] = {"value": "Somme des 8 items", "source": SOURCE}
    path = tmp_path / "ancien.dd.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    scoring = load_project(path).groups[0].scoring
    assert scoring.note == "Somme des 8 items" and scoring.source == SOURCE
    assert not scoring.items


# --- The description of the database. ---


def test_one_wave_per_file_from_the_wave_mark():
    survey = build_project(read_database(EXAMPLES / "travail-t2_surveymonkey.sav"))
    assert survey.dataset.structure.value is None
    naming.set_wave(survey, "t2")
    assert survey.dataset.structure.value == "one_wave_per_file"
    assert survey.dataset.structure.status == "proposed" and survey.dataset.wave == "t2"
    assert not w.dataset_facts(survey)  # a proposal is not shown in the exports
    study.decide_structure(survey, "accept", now=NOW)
    assert ("Structure", "longitudinale, une vague par fichier ; vague t2") in w.dataset_facts(
        survey
    )
    with pytest.raises(ReviewError, match="Aucune structure proposée"):
        study.decide_structure(survey, "reject", now=NOW)
    naming.set_wave(survey, "t3")  # a decision stays
    assert survey.dataset.structure.status == "validated"


def test_wide_format_from_time_suffixes(tmp_path):
    lines = ["id,stress_t1,stress_t2,sommeil_t1,sommeil_t2,humeur_t1,humeur_t2,age"]
    lines += [f"{i},{i % 5},{(i + 1) % 5},{i % 4},{i % 3},{i % 2},{(i + 2) % 5},{20 + i}"
              for i in range(30)]  # fmt: skip
    path = tmp_path / "large.csv"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    project = build_project(read_database(path))
    assert project.dataset.structure.value == "wide"
    assert project.dataset.time_suffixes == ["_t1", "_t2"]
    study.decide_structure(project, "reject", now=NOW)
    assert not w.dataset_facts(project)


def test_what_a_person_writes(project):
    design = {"cluster_id": "id_participant", "weight": ""}
    study.set_dataset(
        project, "family", "", "cross_sectional", "", "", design, "Étude fictive.", now=NOW
    )
    facts = dict(w.dataset_facts(project))
    assert facts["Une ligne représente"] == "une famille"
    assert facts["Structure"] == "transversale"
    assert facts["Variables de plan"] == "identifiant de regroupement : id_participant"
    assert facts["Description de la base"] == "Étude fictive."
    assert project.dataset.structure.origin == "human"
    text = render_markdown(project)
    assert "- Une ligne représente : une famille" in text
    with pytest.raises(ReviewError, match="Variables inconnues : poids"):
        study.set_dataset(project, "", "", "", "", "", {"weight": "poids"}, "", now=NOW)
    study.set_dataset(project, "other", "Une classe", "", "", "", {}, "", now=NOW)
    assert dict(w.dataset_facts(project))["Une ligne représente"] == "Une classe"
    assert project.dataset.structure.value is None  # emptied: not said


def test_a_proposal_chosen_in_the_form_is_accepted():
    survey = build_project(read_database(EXAMPLES / "travail-t2_surveymonkey.sav"))
    naming.set_wave(survey, "t2")
    study.set_dataset(survey, "participant", "", "one_wave_per_file", "t2", "", {}, "", now=NOW)
    assert survey.dataset.structure.status == "validated"
    study.set_dataset(survey, "participant", "", "long", "", "", {"time": "date_created"}, "",
                      now=NOW)  # fmt: skip
    assert survey.dataset.structure.status == "corrected"
    assert survey.dataset.structure.proposed_value == "one_wave_per_file"


# --- In the interface. ---


@pytest.fixture
def project_path(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.sav", tmp_path / "etude-sommeil.sav")
    _project, path = profile_database(tmp_path / "etude-sommeil.sav")
    return path


def _app(path: Path, mode: str) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=30)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = mode
    app.run()
    assert not app.exception, app.exception
    return app


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_scoring_form(project_path):
    app = _app(project_path, "groups")
    # Nothing is chosen in advance (v0.16, D-126): the computed choices are taken up.
    app.button(key="offer-scoring-items-G1").click().run()
    app.button(key="offer-bounds-G1").click().run()
    app.radio(key="scoring-how-G1").set_value("sum")
    app.number_input(key="scoring-least-G1").set_value(0)
    app.text_input(key="scoring-name-G1").input("sommeil_total")
    app.text_input(key="scoring-source-G1").input(SOURCE)
    app.button(key="save-scoring-G1").click().run()
    assert not app.exception, app.exception
    scoring = load_project(project_path).groups[0].scoring
    assert scoring.items == ITEMS and (scoring.scale_min, scoring.scale_max) == (1, 5)
    assert scoring.aggregation == "sum" and scoring.min_items_answered is None


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_description_form(project_path):
    app = _app(project_path, "base")
    app.selectbox(key="dataset-unit_of_observation").select("participant")
    app.selectbox(key="dataset-structure").select("cross_sectional")
    app.text_area(key="dataset-description").input("Étude fictive.")
    app.button(key="dataset-save").click().run()
    assert not app.exception, app.exception
    found = load_project(project_path).dataset
    assert found.unit_of_observation == "participant"
    assert found.structure.value == "cross_sectional" and found.description == "Étude fictive."
    save_project(load_project(project_path), project_path)  # still a valid project
