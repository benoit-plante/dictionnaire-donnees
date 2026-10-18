"""v0.13, step 7 (the AMATUS trial): categories written as text in a CSV ("oui", "non") enter
the analyses once their level is nominal, an empty text is a missing value, and the R
scripts read the CSV as the tool did (separator, decimal mark, text columns) and give the
same values. On a fictional base derived from the database of the analyses."""

import io
import subprocess
import zipfile

import pandas as pd
import pytest

from ddict import i18n
from ddict.analysis import conditions
from ddict.analysis import notebook as nb
from ddict.analysis import notebook_export as export
from ddict.analysis.book import Codebook
from ddict.analysis.compute import run
from ddict.analysis.data import code_key, prepare
from ddict.cli import main
from ddict.export.syntax import _r_reader
from ddict.io import read_database
from ddict.project import build_project, load_project, measure, save_project
from ddict.review import levels
from test_analysis_data import EXAMPLES, KEY
from test_syntax import _rscript

TODAY = "2026-10-18"
NOW = "2026-10-18T09:00:00"
GROUPS = {1: "contrôle", 2: "intervention"}
STUDIES = {1: "secondaire", 2: "collège", 3: "université"}
REGIONS = {1: "nord-est", 2: "sud", 3: "ouest", 4: "centre-ville"}
TEXTS = ["groupe", "niveau_etudes", "region", "secteur"]
CASES = [
    ("table1", {"variables": ["heures_travail", "secteur"], "group": ["groupe"]}, None),
    ("t_test", {"outcome": ["satisfaction"], "group": ["groupe"]}, {"method": "student"}),
    ("t_test", {"outcome": ["satisfaction"], "group": ["niveau_etudes"]},
     {"levels": "secondaire,université"}),
    ("anova", {"outcome": ["satisfaction"], "group": ["region"]}, {"post_hoc": "tukey"}),
    ("chi_square", {"rows": ["groupe"], "columns": ["secteur"]}, None),
    ("regression", {"outcome": ["satisfaction"], "predictors": ["soutien", "region"]}, None),
]  # fmt: skip
NOT_IN_R = ("levene", "shapiro", "mdn", "diff", "odds_ratio", "vif", "m1", "m2", "sd1", "sd2")


def _base(folder):
    """The fictional CSV with its categories as texts, ";" and a decimal comma; the group
    of ten people left empty; and a comment, free text."""
    table = pd.read_csv(EXAMPLES / KEY["csv"])
    table["groupe"] = table["groupe"].map(GROUPS)
    table.loc[:9, "groupe"] = ""
    table["niveau_etudes"] = table["niveau_etudes"].map(STUDIES)
    table["region"] = table["region"].map(REGIONS)
    table["secteur"] = table["secteur"].map({1: "public", 2: "privé"})
    table["commentaire"] = [f"Réponse libre numéro {i} sur le travail" for i in range(len(table))]
    path = folder / "etude-textes.csv"
    table.to_csv(path, sep=";", decimal=",", index=False, encoding="utf-8")
    project = build_project(read_database(path))
    proposed = [e.name for e in project.variables if e.measure_level.status == "proposed"]
    levels.apply_table(project, {}, {n: "accept" for n in proposed}, now=NOW)
    project_path = folder / "etude-textes.dd.json"
    save_project(project, project_path)
    return project, project_path


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    return _base(tmp_path_factory.mktemp("textes"))


def test_text_categories_enter_the_analyses(base):
    project, _path = base
    assert all(measure.level(project.variable(n)) == "nominal" for n in TEXTS)
    assert conditions.texts(project) >= set(TEXTS)
    check = conditions.check(project, "t_test", {"outcome": ["satisfaction"],
                                                 "group": ["groupe"]})  # fmt: skip
    assert check.refusals == []
    assert "groupe" in conditions.candidates(project, conditions.CATALOGUE["anova"], "group")
    # Free text stays out, whatever its level.
    found = conditions.check(project, "chi_square", {"rows": ["commentaire"],
                                                     "columns": ["groupe"]})  # fmt: skip
    assert "commentaire : identifiant, texte ou date, exclu des analyses." in found.refusals


def test_an_empty_text_is_missing(base):
    project, path = base
    prepared = prepare(project, path)
    assert prepared.table["groupe"].isna().sum() == 10
    assert set(prepared.table["groupe"].dropna()) == set(GROUPS.values())
    result = run(project, prepared, "t_test", {"outcome": ["satisfaction"], "group": ["groupe"]})
    assert result.n_used == 290
    assert (result.statistics["n1"], result.statistics["n2"]) == (
        (prepared.table["groupe"] == "contrôle").sum(),
        (prepared.table["groupe"] == "intervention").sum(),
    )


def test_two_text_levels_chosen(base, capsys):
    project, path = base
    prepared = prepare(project, path)
    result = run(project, prepared, *CASES[2])
    chosen = prepared.table["niveau_etudes"].isin(["secondaire", "université"])
    assert result.n_used == int(chosen.sum())
    assert Codebook(project, prepared).category("niveau_etudes", "université") == "université"
    # The same from the command line, with the codes as the team types them.
    arguments = ["plan", "ajouter", str(path), "test_t", "--enonce", "Une hypothèse.",
                 "--dependante", "satisfaction", "--groupe", "niveau_etudes",
                 "--modalites", "secondaire,université"]  # fmt: skip
    assert main(arguments) == 0, capsys.readouterr().err
    assert load_project(path).plan.hypotheses[0].options["levels"] == "secondaire,université"
    capsys.readouterr()
    assert main(["plan", "lister", str(path)]) == 0
    assert "modalités comparées : secondaire, université ;" in capsys.readouterr().out
    # The analysis report names them too.
    arguments = [
        "analyser",
        str(path),
        "test_t",
        "--dependante",
        "satisfaction",
        "--groupe",
        "niveau_etudes",
        "--modalites",
        "secondaire,université",
        "--format",
        "aucun",
    ]
    assert main(arguments) == 0, capsys.readouterr().err
    report = path.with_name("etude-textes-analyse-1.md").read_text(encoding="utf-8")
    assert "secondaire, université" in report


def test_text_codes_in_keys():
    assert code_key("in-service") == "sin_service"
    assert code_key("université") == "suniversit_"
    assert (code_key(2.0), code_key(-9), code_key(2.5)) == ("2", "m9", "2p5")


def test_the_r_reader_reads_the_csv_as_the_tool(base):
    project, _path = base
    reader = _r_reader(project)
    assert reader.startswith('read.csv("etude-textes.csv", sep = ";", dec = ",", ')
    assert 'fileEncoding = "UTF-8", na.strings = c("", "NA", ' in reader
    assert "check.names = FALSE" in reader
    assert '"groupe" = "character"' in reader and '"heures_travail"' not in reader


def test_the_analyses_list_in_english(base):
    project, path = base
    with i18n.using("en"):
        line = export._variables(Codebook(project, prepare(project, path)),
                                 {"outcome": ["satisfaction"], "group": ["groupe"]})  # fmt: skip
    assert line == "Dependent variable: satisfaction; Grouping variable: groupe"


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
def test_the_same_values_in_r(tmp_path):
    project, path = _base(tmp_path)
    prepared = prepare(project, path)
    notebook = nb.new_notebook(project, path)
    results = {}
    for key, chosen, options in CASES:
        result = run(project, prepared, key, chosen, options)
        results[nb.add(notebook, project, result, today=TODAY).id] = result.statistics
    analyses = [(e.id, e.analysis, nb.resolved(project, e), dict(e.options))
                for e in notebook.entries]  # fmt: skip
    with zipfile.ZipFile(io.BytesIO(export.r_bundle(project, path, analyses, today=TODAY))) as z:
        z.extractall(tmp_path)
    (tmp_path / "run.R").write_text(
        'source("etude-textes-article.R", encoding = "UTF-8")\n'
        "valeurs <- unlist(resultats)\n"
        'write.csv(data.frame(nom = names(valeurs), valeur = valeurs), "sortie.csv", '
        "row.names = FALSE)\n",
        encoding="utf-8",
    )
    done = subprocess.run([_rscript(), "run.R"], cwd=tmp_path, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")  # fmt: skip
    if "there is no package called" in done.stderr:
        pytest.skip("haven is not installed in R")
    assert done.returncode == 0, done.stderr[-2000:]
    out = pd.read_csv(tmp_path / "sortie.csv")
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
    assert compared > 40
    assert {"v1_m_scontr_le", "v2_kspriv__total"} <= set(from_r["A1"])  # text keys
    assert {"tukey_ssud_scentre_ville", "tukey_p_snord_est_scentre_ville"} <= set(from_r["A4"])
    assert from_r["A2"]["n1"] + from_r["A2"]["n2"] == 290  # the empty group left out
