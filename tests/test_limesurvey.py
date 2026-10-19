"""v0.20, step A2: LimeSurvey described in `ddict.platforms` (D-044, D-148) — its variables,
the names of its items, its "other" and its ticked boxes, as LimeSurvey Cloud 7.6 exported the
fictional survey of the trial in CSV, Excel and SPSS
(`docs/essais/2026-10-19-limesurvey-fictif.md`).
The responses of the tests come from `scripts/generer_limesurvey_fictif.py`, compared to the
author's own exports by the test marked `limesurvey`."""

import os
from pathlib import Path

import pandas as pd
import pytest

from ddict import design, naming, platforms
from ddict.design import Draft, Item
from ddict.io import load
from ddict.project import build_project
from ddict.questionnaire.link import project_questions
from test_lss import REAL, files, generator  # noqa: F401 (fixtures)

NAMES = [
    "id", "submitdate", "lastpage", "startlanguage", "seed", "startdate", "datestamp",
    "quota_exit", "genre", "genre_other", "age", "region", "journal", "profession", "intro",
    "sommeil_SQ001", "sommeil_SQ002", "sommeil_SQ003", "aides_SQ001", "aides_SQ002",
    "aides_other", "nuit",
]  # fmt: skip
NOW = "2026-10-20T09:00:00"


@pytest.fixture(scope="module")
def projects(files):  # noqa: F811
    return {kind: build_project(load.read_database(files[kind])) for kind in ("sav", "csv", "xlsx")}


def test_each_export_is_a_limesurvey_base_with_the_names_of_its_sav(projects):
    for kind, project in projects.items():
        assert project.source.platform == "limesurvey", kind
        assert [e.name for e in project.variables] == NAMES, kind


def test_the_variables_of_the_platform():
    lime = platforms.LIMESURVEY
    roles = [lime.platform_variable(n).role for n in NAMES[:8]]
    assert roles == [
        "response_id", "submit_date", "last_page", "start_language", "seed", "start_date",
        "last_action_date", "quota_exit",
    ]  # fmt: skip
    assert lime.place("sommeil_SQ001") == platforms.Place("sommeil", "SQ001")
    assert lime.place("genre_other") == platforms.Place("genre", None, True)
    assert lime.column_name("aides[SQ002]") == "aides_SQ002"
    assert lime.question_key("sommeil") == "sommeil" and lime.item_prefix("sommeil") == "sommeil_"
    # SurveyMonkey keeps its ranks.
    monkey = platforms.SURVEYMONKEY
    assert monkey.place("q0003_0004") == platforms.Place(3, 4)
    assert (monkey.question_key(3), monkey.item_prefix(3)) == ("q0003", "q0003_")


def test_a_csv_with_brackets_that_is_not_limesurvey_keeps_its_names(tmp_path):
    path = tmp_path / "autre.csv"
    path.write_text("id,score[1],score[2]\n1,3,4\n2,5,6\n", encoding="utf-8")
    data = load.read_database(path)
    assert [v.name for v in data.variables] == ["id", "score[1]", "score[2]"]
    assert data.source.platform is None


def test_the_empty_date_of_spss_is_an_empty_cell(files):  # noqa: F811
    table = load.read_database(files["sav"]).table
    assert table["submitdate"].isna().tolist() == [False, False, False, False, True]
    assert pd.Timestamp("1582-10-14") not in set(table["submitdate"].dropna())
    # A CSV keeps its cells as text, an empty one as "" (as every CSV, v0.1).
    assert load.read_database(files["csv"]).table["submitdate"].tolist()[-1] == ""


def test_the_structure_of_the_survey(projects):
    sav = projects["sav"]
    questions = {q.key: q for q in project_questions(sav)}
    assert list(questions) == [
        "genre", "age", "region", "journal", "profession", "intro", "sommeil", "aides", "nuit",
    ]  # fmt: skip
    assert questions["genre"].single == "genre" and questions["genre"].other == "genre_other"
    assert questions["sommeil"].kind == "grid"
    # A ticked box of LimeSurvey's .sav has two labels, "Y" (Oui) and "0" (Non sélectionné).
    assert questions["aides"].kind == "checkbox" and questions["aides"].other == "aides_other"
    groups = {g.kind: g for g in sav.groups}
    assert groups["scale"].members.value == ["sommeil_SQ001", "sommeil_SQ002", "sommeil_SQ003"]
    assert groups["multiple_response"].attached == ["aides_other"]
    assert all(g.basis == ["platform_structure"] for g in sav.groups)
    # Without labels, the grid of a CSV is no scale (as for SurveyMonkey, v0.7); its boxes are.
    assert [g.kind for g in projects["csv"].groups] == ["multiple_response"]
    assert [q.kind for q in project_questions(projects["csv"])] == [
        q.kind for q in project_questions(sav)
    ]


def test_names_for_a_limesurvey_base(projects):
    project = projects["sav"].model_copy(deep=True)
    naming.propose(project)
    names = {e.name: e.new_name.value for e in project.variables}
    assert names["submitdate"] == "date_soumission" and names["id"] == "id_reponse"
    assert names["genre_other"] == "genre_autre_txt"
    assert {s.key for s in project.stems} >= {"genre", "aides"}


def test_a_designed_question_is_named_as_limesurvey_will(tmp_path):
    """The code of a question is its stem without its "_" (D-156): the planned names are those
    of LimeSurvey's .sav."""
    project = design.new_project("Étude", "fr", "2026-10-20")
    design.add_question(
        project,
        Draft(
            kind="checkbox",
            text="Qu'est-ce qui vous aide à dormir ?",
            section="S1",
            options=(
                Item("La lecture", "SQ001"),
                Item("La musique", "SQ002"),
                Item("Autre", other=True),
            ),
        ),
    )
    design.decide_code(project, "Q1", "write", now=NOW, value="aides_sommeil")
    assert [e.name for e in project.variables] == [
        "aidessommeil_SQ001", "aidessommeil_SQ002", "aidessommeil_other",
    ]  # fmt: skip
    assert [e.new_name.value for e in project.variables] == [
        "aides_sommeil_1", "aides_sommeil_2", "aides_sommeil_autre_txt",
    ]  # fmt: skip


@pytest.mark.limesurvey
@pytest.mark.skipif(not (REAL and Path(REAL).is_dir()), reason="DDICT_LIMESURVEY non défini")
def test_the_fictional_responses_are_those_limesurvey_exported(files):  # noqa: F811
    real = Path(os.environ["DDICT_LIMESURVEY"])
    assert (real / "reponses-codes.csv").read_bytes() == files["csv"].read_bytes()
    for mine, theirs in (("sav", "reponses.sav"), ("xlsx", "reponses-codes.xlsx")):
        a = build_project(load.read_database(files[mine]))
        b = build_project(load.read_database(real / theirs))
        # pyreadstat cannot write LimeSurvey's storage width of a ticked box (32 for A28).
        for entry in (*a.variables, *b.variables):
            entry.file.storage_width = None
        assert [e.model_dump() for e in a.variables] == [e.model_dump() for e in b.variables]
        assert [g.model_dump() for g in a.groups] == [g.model_dump() for g in b.groups]
