"""v0.7, step 2: survey platforms recognized, two header rows read (D-044)."""

import json
from pathlib import Path

import pyreadstat
import pytest

from ddict.io import read_database
from ddict.platforms import SURVEYMONKEY, Place, recognize, split_header
from ddict.project import build_project
from ddict.project.store import ProjectError, dumps, load_project
from ddict.workflow import platform_notes

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
REFERENCE = ROOT / "tests" / "reference"
# The .sav variables an Excel export does not have: the collector's name, and the "other"
# option of each checkbox question as a checkbox of its own (seen in a real export).
NOT_IN_EXCEL = {
    "CollectorNm", "q0004_0006", "q0007_0007", "q0009_0005",  # wave 1
    "q0005_0006", "q0008_0007", "q0010_0005",  # wave 2
}  # fmt: skip


def _names(file_name: str) -> list[str]:
    _df, meta = pyreadstat.read_sav(EXAMPLES / file_name, metadataonly=True)
    return meta.column_names


@pytest.mark.parametrize("wave", ["t1", "t2"])
def test_both_variants_of_surveymonkey_names_are_recognized(wave):
    assert recognize(_names(f"travail-{wave}_surveymonkey.sav")) is SURVEYMONKEY


def test_other_databases_are_not_recognized():
    assert recognize(_names("etude-sommeil.sav")) is None
    assert recognize(_names("sleep-study.sav")) is None
    # Renamed by the team: no longer a platform export.
    assert recognize(_names("travail-t1-documente.sav")) is None


def test_a_few_q_names_are_not_enough():
    assert recognize(["q0001", "q0002", "q0003"]) is None
    assert recognize(["respondent_id", "collector_id", "q0001", "age", "sexe", "ville"]) is None


def test_the_place_of_a_variable_comes_from_its_name():
    assert SURVEYMONKEY.place("q0003_0004") == Place(question=3, item=4)
    assert SURVEYMONKEY.place("q0008_other") == Place(question=8, other=True)
    assert SURVEYMONKEY.place("q0001") == Place(question=1)
    assert SURVEYMONKEY.place("q000") is None
    assert SURVEYMONKEY.place("RespondentID") is None
    assert SURVEYMONKEY.platform_variable("RespondentID").role == "respondent_id"
    assert SURVEYMONKEY.platform_variable("date_created").role == "start_date"


def test_two_header_rows_give_the_names_of_the_sav_file():
    first = ["Respondent ID", "Start Date", "Quelle couleur ?", "Une grille", None, None, "Q"]
    second = [None, None, "Response", "Énoncé 1", "Énoncé 2", "Other (please specify)", "Rien"]
    platform, names = split_header([first, second])
    assert platform is SURVEYMONKEY
    assert names == [
        "RespondentID",
        "StartDate",
        "q0001",
        "q0002_0001",
        "q0002_0002",
        "q0002_other",
        "q0003_0001",
    ]


def test_recent_exports_title_the_platform_columns_with_their_names():
    first = ["respondent_id", "date_created", "Une question à cocher ?", None, None]
    second = [None, None, "Option A", "Option B", "Autre (veuillez préciser)"]
    _platform, names = split_header([first, second])
    assert names == ["respondent_id", "date_created", "q0001_0001", "q0001_0002", "q0001_other"]


def test_a_single_choice_with_other_keeps_the_question_name():
    first = ["Respondent ID", "Votre secteur ?", None]
    second = [None, "Response", "Other (please specify)"]
    assert split_header([first, second])[1] == ["RespondentID", "q0001", "q0001_other"]


@pytest.mark.parametrize(
    "rows",
    [
        [["id", "age", "sexe"], ["P01", "34", "F"]],  # an ordinary table
        [["Respondent ID", "Q ?"], ["114", "Bleu"]],  # answers, not a header
        [["Respondent ID", "Start Date"], [None, None]],  # no question
        [["Respondent ID", None, "Q ?"], [None, "x", "Response"]],  # a column continues nothing
        [["Respondent ID"]],
    ],
)
def test_other_tables_are_left_alone(rows):
    assert split_header(rows) is None


@pytest.mark.parametrize(
    "file_name", ["travail-t1_surveymonkey.xlsx", "travail-t2_surveymonkey.xlsx"]
)
def test_the_excel_export_reads_like_its_sav_file(file_name):
    data = read_database(EXAMPLES / file_name)
    sav = read_database(EXAMPLES / file_name.replace(".xlsx", ".sav"))
    assert data.source.platform == "surveymonkey"
    assert data.source.n_rows == sav.source.n_rows
    names = [v.name for v in data.variables]
    # Every column of the .sav file but the collector's name and the "other" options ticked,
    # which this export does not have (it has their texts).
    assert names == [v.name for v in sav.variables if v.name not in NOT_IN_EXCEL]


def test_the_csv_export_reads_like_the_excel_one():
    csv = read_database(EXAMPLES / "travail-t2_surveymonkey.csv")
    xlsx = read_database(EXAMPLES / "travail-t2_surveymonkey.xlsx")
    assert csv.source.platform == "surveymonkey"
    assert [v.name for v in csv.variables] == [v.name for v in xlsx.variables]
    assert csv.source.n_rows == xlsx.source.n_rows
    for name in ("q0003_0001", "q0005_0001", "q0009"):
        assert csv.table[name].fillna("").tolist() == xlsx.table[name].fillna("").tolist()


def test_the_platform_is_kept_in_the_project():
    project = build_project(read_database(EXAMPLES / "travail-t2_surveymonkey.sav"))
    assert project.source.platform == "surveymonkey"
    assert platform_notes(project) == ["Export SurveyMonkey reconnu."]
    excel = build_project(read_database(EXAMPLES / "travail-t2_surveymonkey.xlsx"))
    notes = platform_notes(excel)
    assert len(notes) == 2 and ".sav" in notes[1] and "XLSX" in notes[1]
    assert platform_notes(build_project(read_database(EXAMPLES / "etude-sommeil.sav"))) == []


def test_a_project_of_format_0_1_0_reads_without_conversion():
    old = REFERENCE / "etude-sommeil-0.1.0.dd.json"
    project = load_project(old)
    assert project.source.platform is None
    # Saved again, it says 0.2.0, and keeps everything the old file said, as it said it.
    new = json.loads(dumps(project))
    previous = json.loads(old.read_text(encoding="utf-8"))
    assert new["schema_version"] == "0.2.0" and new["source"]["platform"] is None
    del new["schema_version"], previous["schema_version"]
    assert _contains(new, previous)


def _contains(new, old) -> bool:
    """Whether `new` has every key of `old` with the same value; new keys aside."""
    if isinstance(old, dict):
        return isinstance(new, dict) and all(
            k in new and _contains(new[k], v) for k, v in old.items()
        )
    if isinstance(old, list):
        return isinstance(new, list) and len(new) == len(old) and all(map(_contains, new, old))
    return new == old


def test_a_project_of_a_more_recent_version_is_refused_clearly(tmp_path):
    text = (REFERENCE / "etude-sommeil.dd.json").read_text(encoding="utf-8")
    path = tmp_path / "futur.dd.json"
    path.write_text(text.replace('"0.2.0"', '"0.9.0"', 1), encoding="utf-8")
    with pytest.raises(ProjectError, match="more recent version"):
        load_project(path)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_base_page_says_which_export_it_is(tmp_path):
    from streamlit.testing.v1 import AppTest

    from ddict.workflow import profile_database

    database = tmp_path / "travail-t2_surveymonkey.xlsx"
    database.write_bytes((EXAMPLES / database.name).read_bytes())
    _project, path = profile_database(database)
    app = AppTest.from_file(str(ROOT / "src" / "ddict" / "review" / "app.py"), default_timeout=30)
    app.session_state["project_path"] = str(path)
    app.run()
    assert not app.exception, app.exception
    infos = [i.value for i in app.info]
    assert "Export SurveyMonkey reconnu." in infos
    assert any("préférez-le" in i for i in infos)
    assert [m.value for m in app.metric][:2] == ["51", "110"]
