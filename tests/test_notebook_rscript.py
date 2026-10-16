"""v0.11, step 5: the R master script of the notebook gives, in R, the same values as the
tool for every statistic kept of every analysis, within 10⁻⁶."""

import io
import shutil
import subprocess
import zipfile

import pandas as pd
import pytest

from ddict.analysis import notebook as nb
from ddict.analysis import notebook_export as export
from ddict.analysis.compute import run
from ddict.project import save_project
from test_analysis_data import EXAMPLES, KEY, _prepared, analyses_project
from test_syntax import _rscript

TODAY = "2026-10-16"
CASES = [
    ("table1", {"variables": ["age", "sexe", "niveau_etudes", "bienetre_total"],
                "group": ["groupe"]}, None),
    ("table1", {"variables": ["stress", "region"]}, None),
    ("t_test", {"outcome": ["bienetre_total"], "group": ["groupe"]}, None),
    ("t_test", {"outcome": ["stress"], "group": ["niveau_etudes"]},
     {"levels": "1,3", "method": "student"}),
    ("t_test", {"outcome": ["bienetre_total"], "group": ["groupe"]}, {"method": "mann_whitney"}),
    ("anova", {"outcome": ["stress"], "group": ["niveau_etudes"]}, {"post_hoc": "tukey"}),
    ("anova", {"outcome": ["stress"], "group": ["region"]}, {"method": "kruskal_wallis"}),
    ("chi_square", {"rows": ["teletravail"], "columns": ["secteur"]}, None),
    ("chi_square", {"rows": ["groupe"], "columns": ["teletravail"]}, {"method": "fisher"}),
    ("correlation", {"variables": ["heures_travail", "stress", "soutien"]}, None),
    ("correlation", {"variables": ["heures_travail", "stress"]}, None),
    ("correlation", {"variables": ["stress", "sport", "soutien"]}, {"method": "spearman"}),
    ("regression", {"outcome": ["satisfaction"], "predictors": ["soutien", "charge", "secteur"]},
     None),
]  # fmt: skip
# Statistics the R body does not give: the tests of the conditions, the medians, and the
# working values (each compared in the tests of v0.9 where R gives them).
NOT_IN_R = ("levene", "shapiro", "mdn", "diff", "odds_ratio", "vif", "m1", "m2", "sd1", "sd2")


@pytest.fixture(scope="module")
def notebook_and_results(tmp_path_factory):
    project = analyses_project()
    prepared = _prepared(project, KEY["sav"])
    folder = tmp_path_factory.mktemp("carnet")
    path = folder / "etude-analyses.dd.json"
    save_project(project, path)
    notebook = nb.new_notebook(project, path)
    results = {}
    for key, chosen, options in CASES:
        result = run(project, prepared, key, chosen, options)
        entry = nb.add(notebook, project, result, today=TODAY)
        results[entry.id] = result.statistics
    return project, prepared, notebook, path, results


def test_the_master_script(notebook_and_results):
    project, prepared, notebook, path, _results = notebook_and_results
    nb.retain(notebook, "A2", False)
    nb.move(notebook, "A13", 1)
    written = export.write_results(project, prepared, notebook, path, today=TODAY)
    zipped = written[-1]
    assert zipped.name == "etude-analyses-resultats-R.zip"
    with zipfile.ZipFile(io.BytesIO(zipped.read_bytes())) as archive:
        names = archive.namelist()
        script = archive.read("etude-analyses-resultats.R").decode("utf-8")
    assert names == ["etude-analyses-resultats.R", "etude-analyses-metadonnees.R",
                     "etude-analyses-preparation.R"]  # fmt: skip
    assert script.count('source("etude-analyses-metadonnees.R"') == 1  # the header once
    assert script.index("resultats$A13 <- local({") < script.index("resultats$A1 <- local({")
    assert "resultats$A2 " not in script  # not retained
    nb.retain(notebook, "A2", True)


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
def test_the_same_values_as_r(notebook_and_results, tmp_path):
    project, _prepared_data, notebook, path, results = notebook_and_results
    folder = tmp_path / "r"
    folder.mkdir()
    shutil.copy(EXAMPLES / KEY["sav"], folder / KEY["sav"])
    analyses = [(e.id, e.analysis, nb.resolved(project, e), dict(e.options))
                for e in notebook.entries]  # fmt: skip
    bundle = export.r_bundle(project, path, analyses, today=TODAY)
    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
        archive.extractall(folder)
    (folder / "run.R").write_text(
        'source("etude-analyses-resultats.R", encoding = "UTF-8")\n'
        "valeurs <- unlist(resultats)\n"
        'write.csv(data.frame(nom = names(valeurs), valeur = valeurs), "sortie.csv", '
        "row.names = FALSE)\n",
        encoding="utf-8",
    )
    done = subprocess.run([_rscript(), "run.R"], cwd=folder, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")  # fmt: skip
    if "there is no package called" in done.stderr:
        pytest.skip("haven is not installed in R")
    assert done.returncode == 0, done.stderr[-2000:]
    out = pd.read_csv(folder / "sortie.csv")
    from_r: dict[str, dict[str, float]] = {}
    for name, value in zip(out["nom"], out["valeur"], strict=True):
        entry_id, key = name.split(".", 1)
        from_r.setdefault(entry_id, {})[key] = value
    compared = 0
    for entry_id, statistics in results.items():
        common = [k for k in statistics if k in from_r[entry_id] and not k.startswith(NOT_IN_R)]
        assert common, entry_id
        for key in common:
            assert statistics[key] == pytest.approx(from_r[entry_id][key], rel=1e-6, abs=1e-10), (
                entry_id,
                key,
            )
            compared += 1
    assert compared > 150  # every analysis, every statistic R gives
    # The correlation of three variables: every pair, not only the first (step 5 fix).
    assert {"r_2_1", "r_3_1", "r_3_2"} <= set(from_r["A10"])
    assert {"v1_m_1", "v2_k1_total", "v4_sd_2"} <= set(from_r["A1"])  # Table 1 by position
    assert {"tukey_low_3_1", "tukey_high_2_1"} <= set(from_r["A6"])
