"""v0.14, step 6: the subgroup of an analysis, an entry of the notebook or an hypothesis
(D-113; docs/catalogue-elargi.md, § 7), and the expected direction named by the groups."""

import io
import shutil
import subprocess
import zipfile

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from ddict.analysis import article_text as article
from ddict.analysis import notebook as nb
from ddict.analysis import notebook_check as check
from ddict.analysis import notebook_export as export
from ddict.analysis import plan_notebook as pn
from ddict.analysis import planning as pl
from ddict.analysis import prereg
from ddict.analysis.apa import describe, plain
from ddict.analysis.compute import AnalysisRefused, run
from ddict.analysis.report import render_report
from ddict.analysis.results import Subset
from ddict.analysis.rscript import r_script
from ddict.cli import main
from ddict.export.syntax import write_syntax
from ddict.io import read_database
from ddict.project import build_project, load_project, save_project
from ddict.workflow import analysis_files
from test_analysis_page import APP
from test_paired import EXACT, EXAMPLES, KEY, PAIR, TODAY, ready  # noqa: F401
from test_syntax import _rscript
from test_text_categories import _base

WOMEN = Subset("sexe", "eq", 1.0)


def _run(ready, subset, key="paired", chosen=PAIR, options=None):  # noqa: F811
    project, prepared = ready
    return run(project, prepared, key, chosen, options, subset)


# --- The analysis on a subgroup. ---


def test_the_women_as_the_key_says(ready):  # noqa: F811
    result = _run(ready, WOMEN)
    exact = EXACT["t_apparie_t1_t2_femmes"]
    s = result.statistics
    assert s["n"] == exact["n"] and s["t"] == pytest.approx(exact["t"], abs=1e-8)
    assert s["d"] == pytest.approx(exact["d_z"], abs=1e-9)
    assert result.sentence.startswith("Sous-groupe (sexe = Femme). Anxiété au début")
    assert result.subgroup_text == "sexe = Femme"
    assert (result.n_used, result.n_excluded) == (126, 114)  # the others count as left out


def test_the_condition_in_every_note_and_the_report(ready, tmp_path):  # noqa: F811
    project, prepared = ready
    result = _run(ready, WOMEN)
    document = describe(project, prepared, result)
    for item in (*document.tables, *document.figures):
        assert plain(item.note).startswith("Sous-groupe : sexe = Femme. ")
    files = analysis_files(tmp_path / "etude-suivi.dd.json")
    report = render_report(project, prepared, result, files, TODAY)
    assert "- **Sous-groupe** : sexe = Femme" in report
    assert "(valeurs manquantes, ou hors du sous-groupe)" in report


@pytest.mark.parametrize(
    ("subset", "text"),
    [
        (Subset("sexe", "in", [1.0, 2.0]), "sexe parmi Femme, Homme"),
        (Subset("age", "ge", 40.0), "age ≥ 40"),
        (Subset("sexe", "ne", 3.0), "sexe ≠ Autre identité"),
    ],
)
def test_the_operators(ready, subset, text):  # noqa: F811
    _project, prepared = ready
    result = _run(ready, subset)
    assert result.subgroup_text == text
    table = prepared.table
    kept = {
        "in": table["sexe"].isin([1.0, 2.0]),
        "ge": table["age"] >= 40,
        "ne": table["sexe"].notna() & (table["sexe"] != 3),
    }[subset.operator]
    assert result.n_used == int(
        (kept & table["anxiete_t1"].notna() & table["anxiete_t2"].notna()).sum()
    )


def test_the_refusals(ready):  # noqa: F811
    with pytest.raises(AnalysisRefused) as identifier:
        _run(ready, Subset("id_participant", "eq", "S-001"))
    assert "identifiant, texte ou date" in identifier.value.check.refusals[0]
    with pytest.raises(AnalysisRefused) as nobody:
        _run(ready, Subset("age", "gt", 200.0))
    assert nobody.value.check.refusals == ["Personne n'est dans le sous-groupe."]
    with pytest.raises(AnalysisRefused) as one:  # the subgroup leaves the group one modality
        _run(ready, WOMEN, "t_test", {"outcome": ["anxiete_t1"], "group": ["sexe"]})
    assert any("modalités" in r for r in one.value.check.refusals)


def test_no_order_on_categories_written_as_text(tmp_path):
    project, path = _base(tmp_path)
    from ddict.analysis.data import prepare

    prepared = prepare(project, path)
    with pytest.raises(AnalysisRefused) as refused:
        run(project, prepared, "t_test", {"outcome": ["satisfaction"], "group": ["groupe"]},
            None, Subset("secteur", "lt", "public"))  # fmt: skip
    assert "n'ont pas d'ordre" in refused.value.check.refusals[0]
    result = run(project, prepared, "t_test", {"outcome": ["satisfaction"], "group": ["groupe"]},
                 None, Subset("secteur", "eq", "privé"))  # fmt: skip
    assert result.subgroup_text == "secteur = privé"


# --- R. ---


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
@pytest.mark.parametrize(
    "subset", [WOMEN, Subset("sexe", "in", [1.0, 2.0]), Subset("age", "ge", 40.0)]
)
def test_the_same_results_in_r(ready, subset, tmp_path):  # noqa: F811
    project = ready[0]
    here = _run(ready, subset).statistics
    shutil.copy(EXAMPLES / KEY["sav"], tmp_path / KEY["sav"])
    write_syntax(project, {"r": tmp_path / "etude-suivi-metadonnees.R"}, TODAY)
    script = r_script(project, "etude-suivi", "paired", PAIR, None, TODAY, subgroup=subset)
    assert "donnees <- donnees[ddict_vrai(" in script
    (tmp_path / "analyse.R").write_text(script, encoding="utf-8")
    (tmp_path / "run.R").write_text(
        'source("analyse.R", encoding = "UTF-8")\n'
        "write.csv(data.frame(nom = names(unlist(resultats)), valeur = unlist(resultats)), "
        '"sortie.csv", row.names = FALSE)\n',
        encoding="utf-8",
    )
    done = subprocess.run([_rscript(), "run.R"], cwd=tmp_path, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")  # fmt: skip
    assert done.returncode == 0, done.stderr
    out = pd.read_csv(tmp_path / "sortie.csv")
    from_r = dict(zip(out["nom"], out["valeur"], strict=True))
    for name in ("n", "t", "df", "p", "diff", "d", "d_low", "d_high", "m1", "sd2"):
        assert here[name] == pytest.approx(from_r[name], rel=1e-6, abs=1e-10), name


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
def test_a_text_subgroup_in_the_master_script(tmp_path):
    project, path = _base(tmp_path)
    from ddict.analysis.data import prepare

    prepared = prepare(project, path)
    notebook = nb.new_notebook(project, path)
    chosen = {"outcome": ["satisfaction"], "group": ["groupe"]}
    result = run(project, prepared, "t_test", chosen, None, Subset("secteur", "eq", "privé"))
    entry = nb.add(notebook, project, result, today=TODAY)
    assert entry.subgroup is not None and entry.subgroup.value == "privé"
    analyses = [(entry.id, entry.analysis, nb.resolved(project, entry), dict(entry.options),
                 nb.resolved_subgroup(project, entry.subgroup))]  # fmt: skip
    with zipfile.ZipFile(io.BytesIO(export.r_bundle(project, path, analyses, today=TODAY))) as z:
        z.extractall(tmp_path)
    (tmp_path / "run.R").write_text(
        'source("etude-textes-article.R", encoding = "UTF-8")\n'
        "writeLines(format(c(resultats$A1$n1 + resultats$A1$n2, resultats$A1$t), digits = 15), "
        '"sortie.txt")\n',
        encoding="utf-8",
    )
    done = subprocess.run([_rscript(), "run.R"], cwd=tmp_path, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")  # fmt: skip
    assert done.returncode == 0, done.stderr
    lines = (tmp_path / "sortie.txt").read_text(encoding="utf-8").split()
    n, t = (float(x) for x in lines)
    assert n == result.n_used and t == pytest.approx(result.statistics["t"], rel=1e-6)


# --- The notebook and the article. ---


def test_in_the_notebook_and_the_article(ready, tmp_path):  # noqa: F811
    project, prepared = ready
    path = tmp_path / "etude-suivi.dd.json"
    notebook = nb.new_notebook(project, path)
    entry = nb.add(notebook, project, _run(ready, WOMEN), today=TODAY)
    nb.save_notebook(notebook, nb.notebook_path(path))
    again = nb.load_notebook(nb.notebook_path(path))
    assert again.entries[0].subgroup == entry.subgroup
    assert check.recompute(project, prepared, again.entries[0]).statistics["n"] == 126
    document, _analyses = export._results(project, prepared, again, language="fr", today=TODAY)
    methode = next(s for s in document.sections if s.key == "analyses")
    assert "L'analyse A1 porte sur un sous-groupe : sexe = Femme." in plain(methode.paragraphs[-1])


# --- The plan. ---


def test_in_the_plan(ready, tmp_path):  # noqa: F811
    project, prepared = ready
    project = project.model_copy(deep=True)
    data = pl.data_from_names(project, "Chez les femmes, l'anxiété baisse.", "paired", PAIR, {},
                              direction="first_higher", subgroup=WOMEN)  # fmt: skip
    hypothesis = pl.add(project, data, prepared, None, TODAY)
    assert hypothesis.subgroup.operator == "eq" and pl.review(project, hypothesis, prepared).ok
    assert "sous-groupe : sexe = Femme" in plain(prereg._models(project)[0])
    notebook = nb.new_notebook(project, tmp_path / "etude-suivi.dd.json")
    project.plan.alpha, project.plan.data_origin = 0.05, "primary"
    project.plan.data_status = "before_analysis"
    pn.freeze(notebook, project, prepared, TODAY)
    assert notebook.entries[0].subgroup == hypothesis.subgroup
    assert notebook.entries[0].computed.statistics["n"] == 126
    men = data | {
        "subgroup": pl.data_from_names(
            project, "x", "paired", PAIR, {}, subgroup=Subset("sexe", "eq", 2.0)
        )["subgroup"]
    }
    pl.modify(project, "H1", {"subgroup": men["subgroup"]}, prepared, "Les hommes.", TODAY)
    summary = article.amendment_summary(project, project.plan.amendments[0])
    assert summary == "sous-groupe : sexe = Homme au lieu de sexe = Femme"
    pn.sync(notebook, project, prepared, TODAY)
    assert notebook.entries[0].superseded is not None and notebook.entries[1].subgroup is not None


# --- The command line. ---


def _suivi(tmp_path, name="projet"):
    folder = tmp_path / name
    folder.mkdir()
    shutil.copy(EXAMPLES / KEY["sav"], folder / KEY["sav"])
    path = folder / "etude-suivi.dd.json"
    save_project(build_project(read_database(folder / KEY["sav"])), path)
    return path


def test_the_command_line(tmp_path, capsys):
    path = _suivi(tmp_path)
    analysis = ["apparie", "--premiere", "anxiete_t1", "--seconde", "anxiete_t2"]
    assert main(["analyser", str(path), *analysis, "--sous-groupe", "sexe", "eq", "femme",
                 "--format", "aucun"]) == 0  # fmt: skip
    assert capsys.readouterr().out.startswith("Sous-groupe (sexe = Femme). ")
    assert main(["analyser", str(path), *analysis, "--sous-groupe", "sexe", "eq"]) == 2
    assert "variable, opérateur" in capsys.readouterr().err
    assert main(["carnet", "ajouter", str(path), *analysis, "--sous-groupe", "sexe", "in", "1",
                 "2"]) == 0  # fmt: skip
    assert main(["carnet", "lister", str(path)]) == 0
    assert "   Sous-groupe : sexe parmi Femme, Homme" in capsys.readouterr().out
    assert main(["plan", "ajouter", str(path), *analysis, "--enonce", "Les femmes.",
                 "--sous-groupe", "sexe", "eq", "1"]) == 0  # fmt: skip
    assert load_project(path).plan.hypotheses[0].subgroup is not None
    assert main(["plan", "modifier", str(path), "H1", "--sous-groupe", "aucun"]) == 0
    assert load_project(path).plan.hypotheses[0].subgroup is None


# --- The pages. ---


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_analyses_page(tmp_path):
    path = _suivi(tmp_path)
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "analyses"
    app.run()
    app.selectbox(key="analysis-key").set_value("paired").run()
    app.selectbox(key="analysis-paired-first").set_value("anxiete_t1").run()
    app.selectbox(key="analysis-paired-second").set_value("anxiete_t2").run()
    app.selectbox(key="analysis-subgroup-variable").set_value("sexe").run()
    app.selectbox(key="analysis-subgroup-value").set_value(1.0).run()
    app.button(key="analysis-run").click().run()
    assert not app.exception, app.exception
    sentence = next(m.value for m in app.markdown if m.value.startswith("> "))
    assert sentence.startswith("> Sous-groupe (sexe = Femme).") and "t(125) = 6,08" in sentence


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_plan_page_names_the_groups(tmp_path):
    path = _suivi(tmp_path)
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "plan"
    app.run()
    app.text_area(key="plan-new-statement").set_value("Chez les femmes, l'anxiété baisse.").run()
    app.selectbox(key="plan-new-analysis").set_value("paired").run()
    app.selectbox(key="plan-new-role-paired-first").set_value("anxiete_t1").run()
    app.selectbox(key="plan-new-role-paired-second").set_value("anxiete_t2").run()
    radio = app.radio(key="plan-new-direction")
    assert radio.options[1] == (
        "Anxiété au début du programme (0 à 40) plus élevé que Anxiété à la fin du programme "
        "(0 à 40)"
    )
    radio.set_value("first_higher").run()
    app.selectbox(key="plan-new-subgroup-variable").set_value("sexe").run()
    app.selectbox(key="plan-new-subgroup-value").set_value(1.0).run()
    app.button(key="plan-form-save").click().run()
    assert not app.exception, app.exception
    hypothesis = load_project(path).plan.hypotheses[0]
    assert hypothesis.subgroup is not None and hypothesis.options["alternative"] == "greater"


@pytest.mark.parametrize(
    ("key", "chosen"),
    [
        ("table1", {"variables": ["stress", "sommeil"], "group": ["abandon"]}),
        ("anova", {"outcome": ["stress"], "group": ["sexe"]}),
        ("chi_square", {"rows": ["sexe"], "columns": ["abandon"]}),
        ("t_test", {"outcome": ["stress"], "group": ["abandon"]}),
        ("paired", PAIR),
        ("rm_anova", {"measures": ["anxiete_t1", "anxiete_t2", "anxiete_t3"]}),
        ("correlation", {"variables": ["stress", "sommeil"]}),
        ("regression", {"outcome": ["stress"], "predictors": ["charge", "soutien"]}),
        ("logistic", {"outcome": ["abandon"], "predictors": ["motivation"]}),
        ("partial", {"variables": ["stress", "sommeil"], "covariates": ["charge"]}),
        ("moderation", {"outcome": ["epuisement"], "focal": ["charge"], "moderator": ["soutien"]}),
    ],
)
def test_the_tables_and_figures_are_of_the_subgroup(ready, key, chosen):  # noqa: F811
    """The counts, means and points of the tables and figures are those of the subgroup's
    people, as if the analysis had been run on them alone (the AMATUS trial of v0.14)."""
    from ddict.analysis.data import apply_subset

    project, prepared = ready
    subset = Subset("age", "ge", 40.0)
    alone = describe(project, apply_subset(prepared, subset),
                     run(project, apply_subset(prepared, subset), key, chosen))  # fmt: skip
    found = describe(project, prepared, run(project, prepared, key, chosen, None, subset))
    said = "Sous-groupe : age ≥ 40. "
    assert len(found.tables) == len(alone.tables) and len(found.figures) == len(alone.figures)
    for made, expected in zip(found.tables, alone.tables, strict=True):
        assert (made.rows, plain(made.note)) == (expected.rows, said + plain(expected.note))
    for made, expected in zip(found.figures, alone.figures, strict=True):
        assert made.series == expected.series
        assert plain(made.note) == said + plain(expected.note)
