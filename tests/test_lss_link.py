"""v0.20, step A3: a LimeSurvey base linked to a LimeSurvey structure file by the codes of its
questions, items and options (D-148): sure choices (D-041), no text deciding; a text that
differs is a point to check, a code the questionnaire lacks is not linked."""

from pathlib import Path

import pytest

from ddict.io import load
from ddict.project import build_project
from ddict.questionnaire import link
from ddict.workflow import add_questionnaire
from test_lss import REAL, files, generator  # noqa: F401 (fixtures)

EXPECTED = {
    "genre": "Q1", "genre_other": "Q1.o4", "age": "Q2", "region": "Q3", "journal": "Q4",
    "profession": "Q5", "intro": "Q6", "sommeil_SQ001": "Q7.r1", "sommeil_SQ002": "Q7.r2",
    "sommeil_SQ003": "Q7.r3", "aides_SQ001": "Q8.o1", "aides_SQ002": "Q8.o2",
    "aides_other": "Q8.o3", "nuit": "Q9",
}  # fmt: skip
PLATFORM = ["id", "submitdate", "lastpage", "startlanguage", "seed", "startdate", "datestamp",
            "quota_exit"]  # fmt: skip


def _project(base, structure):
    project = build_project(load.read_database(base))
    add_questionnaire(project, structure)
    return project


@pytest.mark.parametrize("kind", ["sav", "csv", "xlsx"])
def test_every_variable_by_its_code(files, kind):  # noqa: F811
    project = _project(files[kind], files["lss"])
    assert link.by_code(project)
    sure = link.sure_choices(project)
    assert {n: sure[n] for n in EXPECTED} == EXPECTED
    assert all(sure[n] == link.NO_QUESTION for n in PLATFORM)
    assert all(q.to_check == [] for q in project.questionnaire.questions)
    assert link.platform_coverage(project) == (9, 0)
    # The structure's choice comes first among the candidates.
    assert link.candidates(project)["sommeil_SQ002"][0] == "Q7.r2"


def test_the_tab_separated_structure_links_the_same(files):  # noqa: F811
    lss = link.sure_choices(_project(files["sav"], files["lss"]))
    assert link.sure_choices(_project(files["sav"], files["txt"])) == lss


def test_other_words_at_the_same_code_are_a_point_to_check(files, tmp_path):  # noqa: F811
    text = files["lss"].read_text(encoding="utf-8")
    changed = tmp_path / "modifie.lss"
    changed.write_text(
        text.replace("Quel âge avez-vous ?", "Votre âge, en années ?").replace(
            "avez-vous bien dormi ?", "avez-vous dormi profondément ?"
        ),
        encoding="utf-8",
    )
    project = _project(files["sav"], changed)
    sure = link.sure_choices(project)
    assert sure["age"] == "Q2" and sure["sommeil_SQ002"] == "Q7.r2"  # the codes decide
    checks = {q.code: q.to_check for q in project.questionnaire.questions}
    assert checks["age"] == ["platform_text_differs"]
    assert checks["genre"] == []
    # A CSV has no labels: nothing to compare, nothing said.
    csv = _project(files["csv"], changed)
    assert all(q.to_check == [] for q in csv.questionnaire.questions)


def test_a_code_the_questionnaire_lacks(files, tmp_path):  # noqa: F811
    text = files["lss"].read_text(encoding="utf-8")
    changed = tmp_path / "recode.lss"
    changed.write_text(
        text.replace("<title><![CDATA[nuit]]></title>", "<title><![CDATA[nuitdifficile]]></title>"),
        encoding="utf-8",
    )
    project = _project(files["sav"], changed)
    assert "nuit" not in link.platform_choices(project)
    checks = {q.code: q.to_check for q in project.questionnaire.questions}
    assert checks["nuitdifficile"] == ["not_in_platform_structure"]
    assert link.platform_coverage(project) == (9, 1)


@pytest.mark.limesurvey
@pytest.mark.skipif(not (REAL and Path(REAL).is_dir()), reason="DDICT_LIMESURVEY non défini")
def test_the_author_exports_link_by_their_codes():
    real = Path(REAL)
    for base in ("reponses.sav", "reponses-codes.csv", "reponses-codes.xlsx"):
        sure = link.sure_choices(_project(real / base, real / "fictif-454667.lss"))
        assert {n: sure[n] for n in EXPECTED} == EXPECTED, base
