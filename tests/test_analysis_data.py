"""v0.9, step 3: the data ready for an analysis, the catalogue and its conditions (D-070,
D-074)."""

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from context_examples import PROJECTS, SOURCE
from ddict.analysis import conditions, data
from ddict.analysis.catalogue import CATALOGUE
from ddict.export.preparation import render_preparation
from ddict.export.syntax import write_syntax
from ddict.io import read_database
from ddict.project import build_project
from ddict.project.decisions import validate
from ddict.project.model import SentinelDecision
from ddict.review import study
from test_syntax import _rscript

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
KEY = json.loads((EXAMPLES / "corrige-analyses.json").read_text(encoding="utf-8"))
NOW = "2026-10-15T12:00:00"


def analyses_project():
    """The fictional database of the analyses, its scale scored as the answer key says."""
    project = build_project(read_database(EXAMPLES / KEY["sav"]))
    scoring = KEY["scoring"]
    group = next(g for g in project.groups if "bienetre_1" in (g.members.value or []))
    group.reverse_items = scoring["reverse_items"]
    study.set_scoring(project, group.group_id, scoring["group_items"], "sum", 1.0, 5.0,
                      scoring["min_items_answered"], scoring["score_name"], SOURCE, "")  # fmt: skip
    return project


def _prepared(project, name):
    return data.apply_decisions(project, read_database(EXAMPLES / name).table)


# --- The data ready for an analysis. ---


def test_decisions_applied_in_memory():
    project = PROJECTS["etude-sommeil"]()
    prepared = _prepared(project, "etude-sommeil.sav")
    table = prepared.table
    assert table["age"].max() < 999  # confirmed missing code
    assert table["genre"].isin([9]).sum() == 0  # declared in the file
    assert table["sommeil_q3"].max() <= 5  # 9 confirmed missing
    assert prepared.reversed == {"sommeil_q3_inv": "sommeil_q3", "sommeil_q6_inv": "sommeil_q6"}
    assert prepared.scores == {"sommeil_total": "G1"}
    assert table["sommeil_total"].notna().sum() == 192


def test_final_names():
    project = PROJECTS["travail-t2_surveymonkey"]()
    table = _prepared(project, "travail-t2_surveymonkey.sav").table
    assert "secteur_t2" in table and "q0001" not in table


def test_the_database_next_to_the_project(tmp_path):
    project = build_project(read_database(EXAMPLES / KEY["sav"]))
    with pytest.raises(data.DataError) as error:
        data.prepare(project, tmp_path / "etude-analyses.dd.json")
    assert error.value.reason == "not_found"
    other = tmp_path / KEY["sav"]
    other.write_bytes((EXAMPLES / "etude-sommeil.sav").read_bytes())
    with pytest.raises(data.DataError) as error:
        data.prepare(project, tmp_path / "etude-analyses.dd.json")
    assert error.value.reason == "other_file"
    original = EXAMPLES / KEY["sav"]
    before = hashlib.sha256(original.read_bytes()).hexdigest()
    prepared = data.prepare(project, tmp_path / "x.dd.json", given=original)
    assert len(prepared.table) == KEY["rows"]
    assert hashlib.sha256(original.read_bytes()).hexdigest() == before  # never changed


def test_the_score_of_the_analyses_base():
    table = _prepared(analyses_project(), KEY["csv"]).table
    exact = KEY["exact"]["t_groupe"]
    intervention = table.loc[table.groupe == 1, "bienetre_total"].dropna()
    assert len(intervention) == exact["n"][0]
    assert intervention.mean() == pytest.approx(exact["means"][0])


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
@pytest.mark.parametrize(
    ("make", "base", "score"),
    [
        (lambda: PROJECTS["etude-sommeil"](), "etude-sommeil.sav", "sommeil_total"),
        (analyses_project, "etude-analyses.sav", "bienetre_total"),
    ],
)
def test_the_same_scores_as_the_r_preparation_script(make, base, score, tmp_path):
    project = make()
    write_syntax(project, {"r": tmp_path / "m.R"}, NOW[:10])
    (tmp_path / "p.R").write_text(render_preparation(project, "r", NOW[:10]), encoding="utf-8")
    out = tmp_path / "out.csv"
    runner = tmp_path / "run.R"
    runner.write_text(
        f'donnees <- haven::read_sav("{(EXAMPLES / base).as_posix()}", user_na = TRUE)\n'
        f'source("{(tmp_path / "m.R").as_posix()}", encoding = "UTF-8")\n'
        f'source("{(tmp_path / "p.R").as_posix()}", encoding = "UTF-8")\n'
        f'write.csv(data.frame(s = as.numeric(donnees[["{score}"]])), "{out.as_posix()}", '
        "row.names = FALSE)\n",
        encoding="utf-8",
    )
    done = subprocess.run([_rscript(), str(runner)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")  # fmt: skip
    if "there is no package called" in done.stderr:
        pytest.skip("haven is not installed in R")
    assert done.returncode == 0, done.stderr
    from_r = pd.read_csv(out)["s"]
    here = _prepared(project, base).table[score]
    assert np.allclose(from_r, here, equal_nan=True)


# --- The catalogue and its conditions. ---


def test_the_catalogue():
    assert list(CATALOGUE) == ["table1", "t_test", "anova", "chi_square", "correlation",
                               "regression"]  # fmt: skip
    assert CATALOGUE["t_test"].options["method"][0] == "welch"  # Welch by default (D-077)


def test_candidates():
    project = analyses_project()
    outcome = conditions.candidates(project, CATALOGUE["t_test"], "outcome")
    assert "bienetre_total" in outcome and "stress" in outcome  # a score is a scale variable
    assert "groupe" not in outcome and "id_participant" not in outcome
    variables = conditions.candidates(project, CATALOGUE["correlation"], "variables")
    assert "sport" in variables and "secteur" not in variables  # ordinal yes, nominal no


@pytest.fixture(scope="module")
def ready():
    project = analyses_project()
    return project, _prepared(project, KEY["sav"])


def _check(ready, analysis, chosen, options=None):
    project, prepared = ready
    return conditions.check(project, analysis, chosen, options, prepared)


def test_refusals(ready):
    found = _check(ready, "correlation", {"variables": ["stress", "id_participant"]})
    assert found.refusals == ["id_participant : identifiant, texte ou date, exclu des analyses."]
    found = _check(ready, "correlation", {"variables": ["stress", "secteur"]})
    assert "ne convient pas au rôle « variables »" in found.refusals[0]
    found = _check(ready, "t_test", {"outcome": ["stress"], "group": ["niveau_etudes"]})
    assert found.refusals == ["niveau_etudes : 3 modalités ; choisissez-en deux."]
    found = _check(ready, "t_test", {"outcome": ["stress"], "group": ["niveau_etudes"]},
                   {"levels": "1,3"})  # fmt: skip
    assert found.ok
    found = _check(ready, "anova", {"outcome": ["stress"], "group": ["groupe"]})
    assert "2 modalités observées ; il en faut de 3 à 10" in found.refusals[0]
    found = _check(ready, "regression", {"outcome": ["satisfaction"], "predictors": []})
    assert "de 1 à 10 variables" in found.refusals[0]


def test_warnings(ready):
    found = _check(ready, "anova", {"outcome": ["stress"], "group": ["region"]})
    assert found.ok and found.warnings == ["region : moins de 5 personnes dans 4 Ouest."]
    found = _check(ready, "correlation", {"variables": ["stress", "sport"]})
    assert found.ok and "Spearman convient mieux" in found.warnings[0]
    assert not _check(ready, "correlation", {"variables": ["stress", "sport"]},
                      {"method": "spearman"}).warnings  # fmt: skip


def test_too_few_observations_per_predictor(ready):
    project, prepared = ready
    few = data.PreparedData(prepared.table.head(25), prepared.scores, prepared.reversed)
    found = conditions.check(project, "regression",
                             {"outcome": ["satisfaction"], "predictors": ["soutien", "charge",
                                                                          "secteur"]},
                             None, few)  # fmt: skip
    assert "il en faut au moins 10 par prédicteur" in found.refusals[0]


def test_a_level_not_decided_and_a_long_format():
    project = build_project(read_database(EXAMPLES / KEY["csv"]))  # a CSV: levels proposed
    found = conditions.check(project, "correlation", {"variables": ["stress", "heures_travail"]})
    assert "niveau de mesure non décidé" in found.refusals[0]
    for name in ("stress", "heures_travail"):
        entry = project.variable(name)
        entry.measure_level = validate(entry.measure_level, now=NOW)
    assert conditions.check(project, "correlation",
                            {"variables": ["stress", "heures_travail"]}).ok  # fmt: skip
    study.set_dataset(project, "repeated_observation", "", "long", "", "", {}, "", now=NOW)
    found = conditions.check(project, "correlation", {"variables": ["stress", "heures_travail"]})
    assert "format long" in found.warnings[0]


def test_a_confirmed_missing_code_is_removed():
    """In the CSV, nothing declares -9 of stress: removed once the team confirms it."""
    project = build_project(read_database(EXAMPLES / KEY["csv"]))
    assert (_prepared(project, KEY["csv"]).table["stress"] == -9).sum() == 4
    project.variable("stress").sentinel_decisions = [SentinelDecision(code=-9, missing=True)]
    assert (_prepared(project, KEY["csv"]).table["stress"] == -9).sum() == 0
