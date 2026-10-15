"""v0.8, step 5: how complete the codebook is, from accepted values only."""

import shutil
from pathlib import Path

import openpyxl
import pytest
from streamlit.testing.v1 import AppTest

from ddict import naming
from ddict.export import render_markdown, write_xlsx
from ddict.export import wording as w
from ddict.io import read_database
from ddict.project import build_project, completeness
from ddict.project.decisions import validate
from ddict.project.model import TrackedValue
from ddict.review import levels, study
from ddict.workflow import add_questionnaire, profile_database

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")
NOW = "2026-10-15T12:00:00"


def _counts(project) -> dict[str, tuple[int, int]]:
    return {p.key: (p.done, p.applicable) for p in completeness.parts(project)}


def test_a_database_as_read():
    project = build_project(read_database(EXAMPLES / "etude-sommeil.sav"))
    assert _counts(project) == {
        "label": (33, 34),  # sommeil_q7 has no label
        "value_labels": (17, 21),  # the four ticked boxes have none
        "measure_level": (27, 27),  # not for identifiers, free text, dates, empty, mixed
        "scoring": (0, 2),
    }
    assert completeness.dataset_missing(project) == ["unit", "structure"]
    # A CSV: nothing decided yet; the coded variables are those proposed nominal or ordinal.
    csv = build_project(read_database(EXAMPLES / "etude-sommeil.csv"))
    assert _counts(csv)["label"] == (0, 34)
    assert _counts(csv)["value_labels"] == (0, 20)
    assert _counts(csv)["measure_level"] == (0, 27)


def test_half_reviewed():
    project = build_project(read_database(EXAMPLES / "etude-sommeil.csv"))
    add_questionnaire(project, EXAMPLES / "questionnaire-sommeil.pdf")
    assert _counts(project)["question"] == (0, 34)
    project.variable("age").question = TrackedValue[str](value="Q3", origin="human")
    proposed = TrackedValue[str](value="Âge", origin="ai", status="proposed", ai_run="r1")
    project.variable("age").label = proposed
    assert _counts(project)["label"] == (0, 34)  # a proposal is not documented
    project.variable("age").label = validate(proposed, now=NOW)
    levels.apply_table(project, {}, {"sommeil_q1": "accept", "age": "accept"}, now=NOW)
    study.set_scoring(project, "G1", [f"sommeil_q{i}" for i in range(1, 9)], "sum", 1.0, 5.0,
                      None, "sommeil_total", "Manuel fictif, p. 4", "")  # fmt: skip
    study.set_dataset(project, "participant", "", "cross_sectional", "", "", {}, "", now=NOW)
    counts = _counts(project)
    assert counts["question"] == (1, 34)
    assert counts["label"] == (1, 34)
    assert counts["measure_level"] == (2, 27)
    assert counts["scoring"] == (1, 2)
    assert completeness.dataset_missing(project) == []
    rows = {name: (count, missing) for name, count, missing in w.completeness_rows(project)}
    assert rows["Description de la base"] == ("dite", "")
    assert rows["Cotation (groupes d'échelle)"] == ("1 / 2", "G2")


def test_new_names_once_renaming_has_begun():
    project = build_project(read_database(EXAMPLES / "travail-t2_surveymonkey.sav"))
    assert "new_name" not in _counts(project)
    naming.propose(project)
    assert _counts(project)["new_name"] == (0, 55)
    naming.decide(project, "q0001", "accept", now=NOW)
    part = next(p for p in completeness.parts(project) if p.key == "new_name")
    assert (part.done, part.applicable) == (1, 55)
    assert "q0002" in part.missing and "secteur" not in part.missing


def test_long_lists_are_cut():
    names = [f"v{i}" for i in range(14)]
    assert w.missing_text(names) == "v0, v1, v2, v3, v4, v5, v6, v7, v8, v9 et 4 autres"
    assert w.missing_text(names[:3]) == "v0, v1, v2"


def test_in_both_codebooks(tmp_path):
    project = build_project(read_database(EXAMPLES / "etude-sommeil.sav"))
    text = render_markdown(project)
    assert "## Complétude" in text
    assert "| Libellé | 33 / 34 | sommeil_q7 |" in text
    path = tmp_path / "codebook.xlsx"
    write_xlsx(project, path)
    sheet = openpyxl.load_workbook(path)["Informations"]
    rows = {r[0]: r[1] for r in sheet.iter_rows(values_only=True)}
    assert rows["Complétude : Libellé"] == "33 / 34 ; à documenter : sommeil_q7"
    assert rows["Complétude : Niveau de mesure"] == "27 / 27"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_on_the_base_page(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.sav", tmp_path / "etude-sommeil.sav")
    _project, path = profile_database(tmp_path / "etude-sommeil.sav")
    app = AppTest.from_file(APP, default_timeout=30)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "base"
    app.run()
    assert not app.exception, app.exception
    assert "Complétude" in [s.value for s in app.subheader]
    table = next(d.value for d in app.dataframe if "Élément" in d.value.columns)
    assert list(table["Décidés"]) == ["33 / 34", "17 / 21", "27 / 27", "0 / 2", "incomplète"]
