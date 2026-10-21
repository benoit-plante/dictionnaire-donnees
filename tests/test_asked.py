"""v0.21, step 8 (§ 5.8.7 of the plan, D-168): a variable's condition declared by the team for
a database without a designed questionnaire, the refusals, `ddict conditions`, the conditions
of a LimeSurvey structure proposed to an existing base, and the page of a variable. The same
counts as the answer key on the SurveyMonkey export of the same invented responses. Nothing
real: the files of `scripts/generer_base_filtres.py`."""

import json
import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.cli import main
from ddict.io.load import read_database
from ddict.project import asked, build_project, load_project, save_project, skip
from ddict.project.model import Condition, Term
from ddict.workflow import add_questionnaire

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
KEY = json.loads((EXAMPLES / "corrige-filtres.json").read_text(encoding="utf-8"))
SM = KEY["surveymonkey"]  # LimeSurvey's names -> SurveyMonkey's
NOW = "2026-10-21T10:00:00"


def when(*terms, combine="all"):
    return Condition(
        combine=combine, terms=[Term(target=t, operator=o, value=v) for t, o, v in terms]
    )


def _surveymonkey(tmp_path):
    base = tmp_path / "reponses-filtres-surveymonkey.sav"
    shutil.copy(EXAMPLES / base.name, base)
    return build_project(read_database(base)), base


def _declare(project) -> None:
    """The conditions of the questionnaire, typed by the team on SurveyMonkey's names."""
    consent = (SM["consent"], "eq", "1")
    work = (SM["emploi"], "in", ["1", "2"])
    for name in KEY["variables"]:
        if name == "nbenfants":
            condition = when(consent, (SM["enfants"], "eq", "1"))
        elif name.startswith("climat_"):
            condition = when(consent, work)
        elif name == "nuit":
            condition = when(consent, (SM["age"], "ge", "18"), (SM["emploi"], "eq", "1"))
        else:
            condition = when(consent)
        asked.set_asked_if(project, [SM[name]], [condition], now=NOW)


def test_the_same_counts_on_the_surveymonkey_export(tmp_path):
    project, base = _surveymonkey(tmp_path)
    _declare(project)
    counts = skip.counts(project, read_database(base).table)
    boxes = [SM[f"transport_SQ{k:03d}"] for k in (1, 2, 3)]
    assert all(b in skip.boxes_of(project) for b in boxes)  # grouped: a multiple response
    expected = {SM[n]: c for n, c in KEY["variables"].items()}
    found = {n: c.__dict__ for n, c in counts.items()}
    assert found == expected
    entry = project.variable(SM["nbenfants"])
    assert entry.asked_if.origin == "human" and entry.asked_if.value[0].terms[1].value == 1


@pytest.mark.parametrize(
    ("owner", "term", "reason"),
    [
        ("q0004", ("q0099", "answered", None), "Variable inconnue"),
        ("q0004", ("q0004", "answered", None), "elle-même"),
        ("q0004", ("q0003", "ge", "1"), "opérateur"),  # an order on choices
        ("q0004", ("q0003", "eq", "7"), "n'est pas un choix"),
        ("q0004", ("q0002", "ge", "dix-huit"), "attend un nombre"),
        ("q0004", ("q0011", "eq", "x"), "texte libre"),  # the comments: never their value
        ("q0099", ("q0003", "eq", "1"), "Variable inconnue"),
    ],
)
def test_a_condition_is_refused(tmp_path, owner, term, reason):
    project, _base = _surveymonkey(tmp_path)
    before = project.model_dump()
    with pytest.raises(asked.AskedError, match=reason):
        asked.set_asked_if(project, [owner], [when(term)], now=NOW)
    assert project.model_dump() == before


def test_an_identifier_or_a_free_text_may_be_answered(tmp_path):
    project, _base = _surveymonkey(tmp_path)
    asked.set_asked_if(project, ["q0012"], [when(("q0011", "answered", None))], now=NOW)
    assert project.variable("q0012").asked_if.value[0].terms[0].operator == "answered"
    asked.set_asked_if(project, ["q0012"], None, now=NOW)
    assert project.variable("q0012").asked_if is None


def test_the_command_line(tmp_path, capsys):
    project, _base = _surveymonkey(tmp_path)
    path = tmp_path / "travail.dd.json"
    save_project(project, path)
    code = main(["conditions", "poser", str(path), "--variable", "q0004",
                 "--terme", "q0001", "=", "1", "--terme", "q0003", "=", "1"])  # fmt: skip
    assert code == 0
    assert load_project(path).variable("q0004").asked_if.value == [
        when(("q0001", "eq", 1), ("q0003", "eq", 1))
    ]
    capsys.readouterr()
    assert main(["conditions", "lister", str(path)]) == 0
    out = capsys.readouterr().out
    assert "q0004 — Posée si q0001 = 1 (Oui) et q0003 = 1 (Oui) (tapée par l'équipe)" in out
    assert "posée à 160, non applicable 137, manquant 5, anomalies < 5" in out
    code = main(["conditions", "poser", str(path), "--variable", "q0004",
                 "--terme", "q0003", "parmi", "1", "7"])  # fmt: skip
    assert code == 2 and "7 n'est pas un choix" in capsys.readouterr().err
    assert main(["conditions", "retirer", str(path), "--variable", "q0004"]) == 0
    assert load_project(path).variable("q0004").asked_if is None


def test_a_limesurvey_structure_proposes_its_conditions(tmp_path):
    base = tmp_path / "reponses-filtres.sav"
    shutil.copy(EXAMPLES / base.name, base)
    project = build_project(read_database(base))
    add_questionnaire(project, EXAMPLES / "questionnaire-filtres.txt")  # proposes them
    entry = project.variable("nbenfants")
    assert entry.asked_if.origin == "questionnaire" and entry.asked_if.status == "proposed"
    assert skip.counts(project, read_database(base).table).get("nbenfants") is None  # waiting
    for name in KEY["variables"]:
        asked.decide(project, name, "accept", now=NOW)
    counts = skip.counts(project, read_database(base).table)
    assert {n: c.__dict__ for n, c in counts.items()} == KEY["variables"]
    with pytest.raises(asked.AskedError):
        asked.decide(project, "nbenfants", "accept", now=NOW)  # already decided


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_page_of_a_variable(tmp_path):
    project, _base = _surveymonkey(tmp_path)
    path = tmp_path / "travail.dd.json"
    save_project(project, path)
    app = AppTest.from_file(str(ROOT / "src" / "ddict" / "review" / "app.py"), default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "variables"
    app.session_state["filter"] = "all"
    app.session_state["current"] = "q0004"
    app.run()
    assert not app.exception, app.exception
    app.session_state["asked-q0004-terms"] = [
        {"target": "q0001", "operator": "=", "value": "1"},
        {"target": "q0003", "operator": "=", "value": "1"},
    ]
    app.button(key="asked-save-q0004").click().run()
    assert not app.exception, app.exception
    saved = load_project(path)
    assert saved.variable("q0004").asked_if.value == [when(("q0001", "eq", 1), ("q0003", "eq", 1))]
    captions = " ".join(x.value for x in app.caption)
    assert "Posée à 160 ; non applicable 137 ; posée sans réponse 5" in captions
    app.session_state["asked-q0004-terms"] = [{"target": "q0003", "operator": "≥", "value": "1"}]
    app.button(key="asked-save-q0004").click().run()
    assert any("opérateur" in e.value for e in app.error)
