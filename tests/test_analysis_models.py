"""v0.9, step 5: t test, ANOVA and linear regression, checked against the answer key, against
their equivalent R script, and against the examples validated in the catalogue."""

import numpy as np
import pytest

from context_examples import PROJECTS
from ddict import i18n
from ddict.analysis.compute import AnalysisRefused, run
from ddict.analysis.data import PreparedData
from test_analysis_compute import _r_results
from test_analysis_data import KEY, _prepared, analyses_project
from test_syntax import _rscript

EXACT = KEY["exact"]


@pytest.fixture(scope="module")
def ready():
    project = analyses_project()
    return project, _prepared(project, KEY["sav"])


def _run(ready, key, chosen, options=None):
    project, prepared = ready
    return run(project, prepared, key, chosen, options)


# --- Against the answer key. ---


@pytest.mark.parametrize(("group", "exact"), [("groupe", "t_groupe"), ("sexe", "t_sexe")])
def test_t_test_against_the_key(ready, group, exact):
    found = _run(ready, "t_test", {"outcome": ["bienetre_total"], "group": [group]}).statistics
    assert found["t"] == pytest.approx(EXACT[exact]["t"])
    assert found["df"] == pytest.approx(EXACT[exact]["df"])
    assert found["d"] == pytest.approx(EXACT[exact]["d"])
    assert [found["n1"], found["n2"]] == EXACT[exact]["n"]


def test_anova_against_the_key(ready):
    found = _run(ready, "anova", {"outcome": ["stress"], "group": ["niveau_etudes"]}).statistics
    exact = EXACT["anova_etudes"]
    assert found["F"] == pytest.approx(exact["F"])
    assert [found["df1"], found["df2"]] == exact["df"]
    assert found["eta2"] == pytest.approx(exact["eta2"])
    assert found["omega2"] == pytest.approx(exact["omega2"])


def test_regression_against_the_key(ready):
    found = _run(
        ready, "regression", {"outcome": ["satisfaction"], "predictors": ["soutien", "charge"]}
    ).statistics
    exact = EXACT["regression_satisfaction"]
    assert [found[f"coef_{i}"] for i in range(3)] == pytest.approx(exact["coef"])
    assert found["r2"] == pytest.approx(exact["r2"])


# --- The examples validated in the catalogue (docs/catalogue-analyses.md). ---


@pytest.fixture(scope="module")
def sleep():
    project = PROJECTS["etude-sommeil"]()
    return project, _prepared(project, "etude-sommeil.sav")


def test_the_catalogue_examples(sleep):
    project, prepared = sleep
    t = run(project, prepared, "t_test", {"outcome": ["sommeil_total"], "group": ["genre"]},
            {"levels": "1,2"})  # fmt: skip
    assert t.sentence.endswith(
        "M = 23,69 (ÉT = 7,86) pour Femme et M = 23,50 (ÉT = 7,18) pour Homme, "
        "t(172,26) = 0,18, p = ,861, d = 0,03, IC 95 % [−0,27 ; 0,32]."
    )
    assert t.n_excluded == 14
    anova = run(project, prepared, "anova", {"outcome": ["sommeil_total"], "group": ["genre"]})
    assert "F(2, 185) = 1,05, p = ,351, η² = ,01, ω² = ,00" in anova.sentence
    assert anova.warnings == ["genre : moins de 5 personnes dans 3 Autre identité."]
    reg = run(project, prepared, "regression",
              {"outcome": ["sommeil_total"], "predictors": ["age", "heures_sommeil"]})  # fmt: skip
    rows = {r[0]: r for r in reg.tables[0].rows}
    assert rows["Nb heures sommeil (moy)"][1:5] == ["4,93", "0,35", "IC 95 % [4,24 ; 5,63]", "0,72"]
    assert "F(2, 186) = 97,43, p < ,001" in reg.sentence


# --- Warnings and refusals. ---


def test_warnings(ready, sleep):
    found = _run(ready, "anova", {"outcome": ["stress"], "group": ["region"]})
    assert found.warnings == ["region : moins de 5 personnes dans 4 Ouest."]
    project, prepared = sleep
    chosen = {"outcome": ["sommeil_total"], "predictors": ["heures_sommeil", "heures_sommeil_2"]}
    with pytest.raises(AnalysisRefused) as error:  # two identical columns: no unique answer
        run(project, prepared, "regression", chosen)
    assert "prédicteurs sont redondants" in error.value.check.refusals[0]
    table = prepared.table.copy()  # nearly the same: allowed, with a warning
    noise = np.random.default_rng(1).normal(0, 0.05, len(table))
    table["heures_sommeil_2"] = table["heures_sommeil"] + noise
    close = PreparedData(table, prepared.scores, prepared.reversed)
    assert any("VIF > 5" in x for x in run(project, close, "regression", chosen).warnings)


def test_a_group_of_one_is_refused(ready):
    project, prepared = ready
    table = prepared.table.copy()
    table.loc[table.index[table["region"] == 4][:2], "region"] = None  # one person left
    one = PreparedData(table, prepared.scores, prepared.reversed)
    with pytest.raises(AnalysisRefused) as error:
        run(project, one, "t_test", {"outcome": ["stress"], "group": ["region"]},
            {"levels": "1,4"})  # fmt: skip
    assert "un groupe de moins de 2 personnes (4 Ouest)" in error.value.check.refusals[0]


def test_in_english(ready):
    with i18n.using("en"):
        found = _run(ready, "anova", {"outcome": ["stress"], "group": ["niveau_etudes"]},
                     {"method": "kruskal_wallis"})  # fmt: skip
    assert found.sentence.startswith("Score de stress (0 à 40) by Plus haut niveau d'études: H(2)")


# --- Against the equivalent R script. ---

CASES = [
    ("t_test", {"outcome": ["bienetre_total"], "group": ["groupe"]}, None,
     ["t", "df", "p", "diff_low", "diff_high", "d", "d_low", "d_high", "levene_F", "levene_p"]),
    ("t_test", {"outcome": ["stress"], "group": ["niveau_etudes"]},
     {"levels": "1,3", "method": "student"}, ["t", "df", "p", "d", "d_low", "d_high"]),
    ("t_test", {"outcome": ["bienetre_total"], "group": ["groupe"]},
     {"method": "mann_whitney"}, ["U", "p", "rb"]),
    ("anova", {"outcome": ["stress"], "group": ["niveau_etudes"]}, {"post_hoc": "tukey"},
     ["F", "df1", "df2", "p", "eta2", "omega2", "levene_F", "tukey_2_1", "tukey_3_1",
      "tukey_3_2", "tukey_p_3_1"]),
    ("anova", {"outcome": ["stress"], "group": ["region"]}, {"method": "kruskal_wallis"},
     ["H", "df", "p", "epsilon2"]),
    ("regression", {"outcome": ["satisfaction"], "predictors": ["soutien", "charge", "secteur"]},
     None, ["r2", "r2adj", "F", "df1", "df2", "coef_0", "coef_1", "coef_3", "se_2", "low_4",
            "high_4", "p_1", "beta_1", "beta_3", "vif_1", "vif_3"]),
]  # fmt: skip


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
@pytest.mark.parametrize(("key", "chosen", "options", "compared"), CASES)
def test_the_same_results_as_r(ready, key, chosen, options, compared, tmp_path):
    here = _run(ready, key, chosen, options).statistics
    from_r = _r_results(ready, key, chosen, options, tmp_path)
    for name in compared:
        assert here[name] == pytest.approx(from_r[name], rel=1e-6, abs=1e-10), name
