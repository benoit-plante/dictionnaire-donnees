"""v0.20, step E2: the designed questionnaire as a file to import into LimeSurvey (D-148).
The file is LimeSurvey 7.6's tab-separated structure; read again by the tool's own reader
(step A1), it gives back the questionnaire. What would stop the import refuses the writing.
Fictional projects only."""

import csv
import io
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import design, design_limesurvey
from ddict.cli import EXIT_ERROR, main
from ddict.design import Draft, Item
from ddict.project import save_project
from ddict.project.model import SourcedText
from ddict.questionnaire.lss import read_limesurvey
from ddict.questionnaire.read import normalize
from projet_concu import project as designed

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
EXAMPLE = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"


def _every_kind():
    """The designed project, with a question of each LimeSurvey type of the trunk."""
    project = designed()
    for draft in (
        Draft(kind="single", text="Dans quelle région habitez-vous ?", section="S1",
              layout="dropdown", options=(Item("Estrie", "1"), Item("Mauricie", "2"))),
        Draft(kind="open", text="À quelle date avez-vous rempli le journal ?", section="S1",
              answer="date"),
        Draft(kind="open", text="Quelle est votre profession ?", section="S1", answer="short"),
        Draft(kind="single", text="Où dormez-vous ?", section="S2", required=True,
              options=(Item("Chez moi", "1"), Item("Ailleurs, précisez", other=True))),
        Draft(kind="open", text="Décrivez une nuit difficile.\nPrenez votre temps.",
              section="S2", answer="long", instruction="Ni nom, ni lieu & ni date < 2020."),
    ):  # fmt: skip
        design.add_question(project, draft)
    return project


def _rows(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text), delimiter="\t", quotechar='"'))


def _same(left, right) -> None:
    """Two questionnaires that say the same, whatever their ids."""
    assert [(s.title, s.instruction) for s in left.sections] == [
        (s.title, s.instruction) for s in right.sections
    ]
    assert len(left.questions) == len(right.questions)
    for mine, back in zip(left.questions, right.questions, strict=True):
        words = normalize(" ".join(mine.text.split()))  # as any questionnaire is read
        assert (words, mine.kind, mine.required, mine.answer, mine.layout) == (
            back.text, back.kind, back.required, back.answer, back.layout,
        ), mine.question_id  # fmt: skip
        assert (mine.instruction and normalize(mine.instruction)) == back.instruction
        assert [(r.code, normalize(r.text)) for r in mine.rows] == [
            (r.code, r.text) for r in back.rows
        ]
        assert [(o.code, normalize(o.text)) for o in mine.options if not o.other] == [
            (o.code, o.text) for o in back.options if not o.other
        ]
        assert any(o.other for o in mine.options) == any(o.other for o in back.options)


# --- The file ---------------------------------------------------------------------------------


def test_read_again_it_gives_back_the_questionnaire(tmp_path):
    project = _every_kind()
    path = design_limesurvey.write(project, tmp_path)
    assert path.name == "Étude du sommeil (conception) - LimeSurvey.txt"
    back = read_limesurvey(path, "fr")
    _same(design.questionnaire(project), back)
    codes = [design.code(project, q) for q in design.questionnaire(project).questions]
    assert [q.code for q in back.questions] == codes


def test_the_form_of_limesurvey_7():
    text = design_limesurvey.text(_every_kind())
    assert not text.startswith("﻿") and "\r" not in text
    lines = text.splitlines()
    header = (EXAMPLE / "questionnaire-limesurvey.txt").read_text(encoding="utf-8").splitlines()[0]
    assert lines[0] == header
    assert all(len(line.split("\t")) == 151 for line in lines)
    rows = _rows(text)
    groups = [r for r in rows if r["class"] == "G"]
    assert [r["type/scale"] for r in groups] == ["1", "2"]  # numbered, else merged
    ids = [r["id"] for r in rows if r["class"] in ("G", "Q", "SQ")]
    assert all(ids) and len(set(ids)) == len(ids)
    questions = {r["name"]: r for r in rows if r["class"] == "Q"}
    assert {k: r["type/scale"] for k, r in questions.items()} == {
        "Q1": "L", "Q2": "N", "Q3": "X", "Q4": "F", "Q5": "M", "Q6": "!", "Q7": "D",
        "Q8": "S", "Q9": "L", "Q10": "T",
    }  # fmt: skip
    assert questions["Q1"]["mandatory"] == "Y" and questions["Q2"]["mandatory"] == "N"
    assert questions["Q5"]["other"] == "Y" and questions["Q4"]["other"] == "N"
    assert questions["Q9"]["other_replace_text"] == "Ailleurs, précisez"
    assert questions["Q5"]["other_replace_text"] == ""  # "Autre": LimeSurvey's own word
    assert questions["Q4"]["question_theme_name"] == "arrays/array"
    assert questions["Q10"]["text"] == ("Décrivez une nuit difficile. <br /> Prenez votre temps.")
    assert questions["Q10"]["help"] == "Ni nom, ni lieu &amp; ni date &lt; 2020."
    # The answers of a question carry its id; the choices of a checkbox are subquestions.
    answers = [r for r in rows if r["class"] == "A" and r["id"] == questions["Q1"]["id"]]
    assert [a["name"] for a in answers] == ["1", "2", "3", "9"]
    assert "Préfère ne pas répondre" in text and '"Préfère ne pas répondre"' in text


def test_the_same_questionnaire_gives_the_same_file():
    assert design_limesurvey.text(_every_kind()) == design_limesurvey.text(_every_kind())


def test_the_summary_says_what_stays_in_the_tool():
    project = designed()
    group = next(g for g in project.groups if g.question == "Q4")
    group.reverse_items = ["Q4_SQ002"]
    group.instrument_name = SourcedText(value="Échelle fictive", source="Manuel fictif, p. 2")
    found = design_limesurvey.summary(project)
    assert (found.groups, found.questions, found.required) == (2, 5, 1)
    assert (found.subquestions, found.answers) == (5, 8)
    assert found.kinds == {"L": 1, "N": 1, "X": 1, "F": 1, "M": 1}
    assert not found.problems
    left = " ".join(found.left)
    for words in ("provenance", "items inversés", "nom des instruments", "dictionnaire"):
        assert words in left
    steps = " ".join(design_limesurvey.import_steps(project))
    assert "menu « + »" in steps and "Étude du sommeil (conception) - LimeSurvey.txt" in steps
    assert "2 groupes, 5 questions, 5 sous-questions et 8 réponses" in steps


# --- What refuses the writing -----------------------------------------------------------------


def _refused(project) -> list[str]:
    with pytest.raises(design_limesurvey.Unwritable) as raised:
        design_limesurvey.text(project)
    assert raised.value.problems == design_limesurvey.summary(project).problems
    return raised.value.problems


def test_a_brace_would_be_computed_by_limesurvey():
    project = designed()
    design.add_question(project, Draft(kind="open", text="Votre âge {en années} ?", section="S1"))
    [problem] = _refused(project)
    assert problem.startswith("question 3 : une accolade { ou }")


def test_a_choice_without_a_code_or_with_a_long_one():
    project = designed()
    design.add_question(
        project,
        Draft(kind="single", text="Votre ville ?", section="S1",
              options=(Item("Montréal", "MTL"), Item("Québec", "QUEBEC"), Item("Laval"))),
    )  # fmt: skip
    problems = _refused(project)
    assert any("« Québec »" in p and "5 au plus" in p for p in problems)
    assert any("« Laval »" in p for p in problems)
    assert not any("« Montréal »" in p for p in problems)


def test_a_question_code_limesurvey_would_change(monkeypatch):
    project = designed()
    codes = {"Q1": "1genre", "Q2": "Age", "Q4": "age", "Q5": "x" * 21}
    monkeypatch.setattr(design, "code", lambda p, q: codes.get(q.question_id, q.question_id))
    problems = " ".join(_refused(project))
    assert "le code 1genre ne convient pas" in problems
    assert "question 3 : même code LimeSurvey que question 2 (age)" in problems
    assert f"le code {'x' * 21} ne convient pas" in problems


def test_an_empty_questionnaire():
    project = design.new_project("Vide", "fr", "2026-10-19")
    assert _refused(project) == ["Le questionnaire n'a aucune question."]


# --- The command line and the page ------------------------------------------------------------


def test_the_command_line(tmp_path, capsys):
    path = tmp_path / "Étude conçue.dd.json"
    save_project(designed(), path)
    assert main(["questionnaire", "limesurvey", str(path)]) == 0
    out = capsys.readouterr().out
    assert "Fichier LimeSurvey :" in out and "1. Dans LimeSurvey" in out
    written = tmp_path / "Étude du sommeil (conception) - LimeSurvey.txt"
    assert written.read_text(encoding="utf-8") == design_limesurvey.text(designed())

    refused = designed()
    design.add_question(refused, Draft(kind="open", text="Âge {x} ?", section="S1"))
    save_project(refused, path, overwrite=True)
    written.unlink()
    assert main(["questionnaire", "limesurvey", str(path)]) == EXIT_ERROR
    assert "une accolade" in capsys.readouterr().err
    assert not written.exists()


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_page_publier(tmp_path):
    path = tmp_path / "Étude conçue.dd.json"
    save_project(designed(), path)
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "publish"
    app.run()
    assert not app.exception, app.exception
    texts = " ".join(m.value for m in app.markdown)
    assert "Le fichier contient 2 groupes et 5 questions" in texts
    assert "Ouvrez le menu « + »" in texts
    assert not app.error

    refused = designed()
    design.add_question(refused, Draft(kind="open", text="Âge {x} ?", section="S1"))
    save_project(refused, path, overwrite=True)
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "publish"
    app.run()
    assert "LimeSurvey refuserait" in app.error[0].value
    app.button(key="publish-limesurvey-review").click().run()
    assert app.session_state["mode"] == "design_review"
