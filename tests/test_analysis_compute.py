"""v0.9, step 4: Table 1, correlation and chi-square computed in the tool, checked against
the answer key (numpy, from the formulas) and against their equivalent R script."""

import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from ddict import i18n
from ddict.analysis.compute import AnalysisRefused, run
from ddict.analysis.results import interval, number, p_value
from ddict.analysis.rscript import r_script
from ddict.export.preparation import render_preparation
from ddict.export.syntax import write_syntax
from test_analysis_data import KEY, _prepared, analyses_project
from test_syntax import _rscript

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
EXACT = KEY["exact"]
TODAY = "2026-10-15"


@pytest.fixture(scope="module")
def ready():
    project = analyses_project()
    return project, _prepared(project, KEY["sav"])


def _run(ready, key, chosen, options=None):
    project, prepared = ready
    return run(project, prepared, key, chosen, options)


# --- Against the answer key. ---


@pytest.mark.parametrize(
    ("rows", "columns", "exact"),
    [
        ("teletravail", "secteur", "khi2_teletravail_secteur"),
        ("sexe", "secteur", "khi2_sexe_secteur"),
    ],
)
def test_chi_square_against_the_key(ready, rows, columns, exact):
    found = _run(ready, "chi_square", {"rows": [rows], "columns": [columns]}).statistics
    assert found["chi2"] == pytest.approx(EXACT[exact]["chi2"])
    assert found["df"] == EXACT[exact]["df"]
    assert found["V"] == pytest.approx(EXACT[exact]["V"])


@pytest.mark.parametrize(
    ("first", "second", "exact"),
    [("heures_travail", "stress", "r_heures_stress"), ("age", "stress", "r_age_stress")],
)
def test_correlation_against_the_key(ready, first, second, exact):
    found = _run(ready, "correlation", {"variables": [first, second]}).statistics
    assert found["r"] == pytest.approx(EXACT[exact]["r"])
    assert found["n"] == EXACT[exact]["n"]


def test_table1(ready):
    result = _run(ready, "table1", {"variables": ["age", "region", "bienetre_total"]})
    rows = {r[0]: r for r in result.tables[0].rows}
    table = ready[1].table
    assert rows["Âge (années)"][1] == str(table["age"].notna().sum())
    assert (
        rows["Âge (années)"][2] == f"{number(table['age'].mean())} ({number(table['age'].std())})"
    )
    assert rows["  Ouest"][2] == "3 (1,0 %) ⚠"
    assert result.warnings == ["Moins de 5 personnes : region : Ouest."]
    assert "bienetre_total (score de G1)" in rows


# --- Warnings, refusals, sentences. ---


def test_chi_square_warnings_and_fisher(ready):
    found = _run(ready, "chi_square", {"rows": ["region"], "columns": ["teletravail"]})
    assert any("effectifs attendus sur 8 sont sous 5" in x for x in found.warnings)
    fisher = _run(ready, "chi_square", {"rows": ["groupe"], "columns": ["teletravail"]},
                  {"method": "fisher"})  # fmt: skip
    assert 0 <= fisher.statistics["fisher_p"] <= 1 and "Test exact de Fisher" in fisher.sentence


def test_refused(ready):
    with pytest.raises(AnalysisRefused) as error:
        _run(ready, "correlation", {"variables": ["stress", "id_participant"]})
    assert "identifiant" in error.value.check.refusals[0]


def test_sentences(ready):
    found = _run(ready, "correlation", {"variables": ["heures_travail", "stress"]})
    assert found.sentence == (
        "La corrélation entre Heures de travail par semaine et Score de stress (0 à 40) était "
        "r(294) = 0,42, IC 95 % [0,32 ; 0,51], p < ,001."
    )
    with i18n.using("en"):
        english = _run(ready, "chi_square", {"rows": ["sexe"], "columns": ["secteur"]})
    assert english.sentence.startswith(
        "Association between Sexe and Secteur d'emploi: χ²(2) = 0.41"
    )


def test_number_conventions():
    assert number(-0.266) == "−0,27" and number(0.0001) == "0,00"
    assert p_value(0.8607) == ",861" and p_value(0.0004) == "< ,001"
    assert interval(-0.27, 0.32) == "IC 95 % [−0,27 ; 0,32]"
    with i18n.using("en"):
        assert p_value(0.8607) == ".861" and interval(-0.27, 0.32) == "95% CI [−0.27, 0.32]"


# --- Against the equivalent R script. ---


def _r_results(ready, key, chosen, options, tmp_path) -> dict[str, float]:
    project = ready[0]
    shutil.copy(EXAMPLES / KEY["sav"], tmp_path / KEY["sav"])
    write_syntax(project, {"r": tmp_path / "etude-analyses-metadonnees.R"}, TODAY)
    (tmp_path / "etude-analyses-preparation.R").write_text(
        render_preparation(project, "r", TODAY), encoding="utf-8"
    )
    script = r_script(project, "etude-analyses", key, chosen, options, TODAY)
    (tmp_path / "analyse.R").write_text(script, encoding="utf-8")
    (tmp_path / "run.R").write_text(
        'source("analyse.R", encoding = "UTF-8")\n'
        "write.csv(data.frame(nom = names(unlist(resultats)), valeur = unlist(resultats)), "
        '"sortie.csv", row.names = FALSE)\n',
        encoding="utf-8",
    )
    done = subprocess.run([_rscript(), "run.R"], cwd=tmp_path, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")  # fmt: skip
    if "there is no package called" in done.stderr:
        pytest.skip("haven is not installed in R")
    assert done.returncode == 0, done.stderr
    out = pd.read_csv(tmp_path / "sortie.csv")
    return dict(zip(out["nom"], out["valeur"], strict=True))


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
@pytest.mark.parametrize(
    ("key", "chosen", "options", "compared"),
    [
        ("chi_square", {"rows": ["teletravail"], "columns": ["secteur"]}, None,
         ["chi2", "df", "p", "V", "n"]),
        ("chi_square", {"rows": ["groupe"], "columns": ["teletravail"]}, {"method": "fisher"},
         ["chi2", "p", "fisher_p", "n"]),
        ("correlation", {"variables": ["heures_travail", "stress"]}, None,
         ["r", "p", "n", "ci_low", "ci_high"]),
        ("correlation", {"variables": ["stress", "sport"]}, {"method": "spearman"},
         ["r", "p", "n"]),
    ],
)  # fmt: skip
def test_the_same_results_as_r(ready, key, chosen, options, compared, tmp_path):
    here = _run(ready, key, chosen, options).statistics
    from_r = _r_results(ready, key, chosen, options, tmp_path)
    for name in compared:
        assert here[name] == pytest.approx(from_r[name], rel=1e-6, abs=1e-12), name


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
def test_table1_the_same_in_r(ready, tmp_path):
    chosen = {"variables": ["age", "bienetre_total"]}
    from_r = _r_results(ready, "table1", chosen, None, tmp_path)
    table = ready[1].table
    for name in chosen["variables"]:
        assert from_r[f"{name}_n"] == table[name].notna().sum()
        assert from_r[f"{name}_moyenne"] == pytest.approx(table[name].mean())
        assert from_r[f"{name}_et"] == pytest.approx(table[name].std())
