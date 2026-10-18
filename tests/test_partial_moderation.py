"""v0.14, step 3: the partial correlation and the moderation (docs/catalogue-elargi.md, § 5
and 6), checked against the answer key of the follow-up base, against R, in every format,
and in the plan and the article."""

import shutil
import subprocess

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from ddict.analysis import article_text as article
from ddict.analysis import conditions, prereg
from ddict.analysis import planning as pl
from ddict.analysis.apa import describe, plain
from ddict.analysis.book import Codebook
from ddict.analysis.compute import run
from ddict.analysis.formats import FORMATS, available
from ddict.analysis.method_text import _method_sentences
from ddict.analysis.rscript import r_script
from ddict.cli import main
from ddict.export.syntax import write_syntax
from ddict.io import read_database
from ddict.project import build_project, save_project
from test_analysis_page import APP
from test_paired import EXACT, EXAMPLES, KEY, TODAY, ready  # noqa: F401
from test_syntax import _rscript

PARTIAL = {"variables": ["stress", "sommeil"], "covariates": ["charge"]}
MODERATION = {"outcome": ["epuisement"], "focal": ["charge"], "moderator": ["soutien"]}
NOMINAL = {"outcome": ["epuisement"], "focal": ["charge"], "moderator": ["abandon"],
           "covariates": ["age"]}  # fmt: skip


def _run(ready, key, chosen, options=None):  # noqa: F811
    project, prepared = ready
    return run(project, prepared, key, chosen, options)


# --- Against the answer key and the sheet. ---


def test_partial_against_the_key(ready):  # noqa: F811
    result = _run(ready, "partial", PARTIAL)
    exact = EXACT["partielle_stress_sommeil"]
    s = result.statistics
    assert s["n"] == exact["n"]
    assert s["r"] == pytest.approx(exact["r_partial"], abs=1e-10)
    assert s["r_simple"] == pytest.approx(exact["r"], abs=1e-10)
    assert result.sentence == (
        "La corrélation partielle entre score de stress (0 à 40) et heures de sommeil par nuit "
        "(covariables : charge de travail perçue (0 à 10)) était r(237) = −,12, IC 95 % "
        "[−,24 ; ,01], p = ,075 ; la corrélation simple était r = −,38 (n = 240)."
    )


def test_moderation_against_the_key(ready):  # noqa: F811
    result = _run(ready, "moderation", MODERATION)
    exact = EXACT["moderation_epuisement"]
    s = result.statistics
    for i, coef in enumerate(exact["coef"]):
        assert s[f"coef_{i}"] == pytest.approx(coef, abs=1e-9)
    assert s["b"] == pytest.approx(exact["coef"][3], abs=1e-9)
    assert s["delta_r2"] == pytest.approx(exact["delta_r2"], abs=1e-10)
    slopes = exact["simple_slopes"]
    assert [s["slope_1"], s["slope_2"], s["slope_3"]] == pytest.approx(
        [slopes["low"], slopes["mean"], slopes["high"]], abs=1e-9
    )
    assert result.sentence.endswith(
        "La pente de charge de travail perçue (0 à 10) était b = 1,93 à −1 ÉT de soutien des "
        "collègues (0 à 10), 1,29 à sa moyenne et 0,66 à +1 ÉT."
    )


def test_a_nominal_moderator(ready):  # noqa: F811
    result = _run(ready, "moderation", NOMINAL)
    assert result.statistics["slope_1_at"] == 0 and result.statistics["slope_2_at"] == 1
    assert result.sentence.endswith("était b = 1,21 pour Non et 1,34 pour Oui.")
    assert [r[0] for r in result.tables[1].rows] == ["Non", "Oui"]


# --- The conditions. ---


def test_the_conditions(ready):  # noqa: F811
    project, prepared = ready
    twice = conditions.check(project, "partial", {"variables": ["stress", "sommeil"],
                                                  "covariates": ["stress"]})  # fmt: skip
    assert "stress : la même variable dans deux rôles." in twice.refusals
    three = conditions.check(project, "moderation", {**MODERATION, "moderator": ["sexe"]},
                             data=prepared)  # fmt: skip
    assert any("une variable nominale en a deux ici" in r for r in three.refusals)
    assert conditions.check(project, "partial", PARTIAL, data=prepared).ok
    assert conditions.check(project, "moderation", NOMINAL, data=prepared).ok


# --- Against the equivalent R script. ---


def _r_results(ready, key, chosen, options, tmp_path) -> dict[str, float]:  # noqa: F811
    project = ready[0]
    shutil.copy(EXAMPLES / KEY["sav"], tmp_path / KEY["sav"])
    write_syntax(project, {"r": tmp_path / "etude-suivi-metadonnees.R"}, TODAY)
    script = r_script(project, "etude-suivi", key, chosen, options, TODAY)
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
    ("key", "chosen", "options"),
    [
        ("partial", PARTIAL, None),
        ("partial", {"variables": ["stress", "sommeil"], "covariates": ["charge", "abandon"]},
         None),
        ("moderation", MODERATION, None),
        ("moderation", MODERATION, {"center": "no"}),
        ("moderation", NOMINAL, None),
    ],
)  # fmt: skip
def test_the_same_results_as_r(ready, key, chosen, options, tmp_path):  # noqa: F811
    here = _run(ready, key, chosen, options).statistics
    from_r = _r_results(ready, key, chosen, options, tmp_path)
    common = [k for k in here if k in from_r]
    assert len(common) >= 10
    for name in common:
        assert here[name] == pytest.approx(from_r[name], rel=1e-6, abs=1e-10), name


# --- Tables and figures. ---


@pytest.mark.parametrize("language", ["fr", "en"])
@pytest.mark.parametrize(
    ("key", "chosen"), [("partial", PARTIAL), ("moderation", MODERATION), ("moderation", NOMINAL)]
)
@pytest.mark.parametrize("fmt", list(FORMATS))
def test_every_format_renders_everything(ready, fmt, key, chosen, language):  # noqa: F811
    project, prepared = ready
    document = describe(project, prepared, _run(ready, key, chosen), language=language)
    found = FORMATS[fmt]
    assert found in available(document)
    text = " ".join(found.read_text(found.render(document)).replace(chr(0xA0), " ").split())
    expected = [t for f in document.figures for t in (f.title, plain(f.note))]
    if found.tables:
        for table in document.tables:
            expected += [table.title, plain(table.note), *[plain(c.header) for c in table.columns]]
            expected += [plain(cell) for row in table.rows for cell in row.cells]
    missing = [t for t in expected if " ".join(t.replace(chr(0xA0), " ").split()) not in text]
    assert not missing, missing


def test_the_figures(ready):  # noqa: F811
    project, prepared = ready
    partial = describe(project, prepared, _run(ready, "partial", PARTIAL)).figures[0]
    assert partial.kind == "scatter" and len(partial.points) == 240 and partial.line[0] == 0.0
    slopes = describe(project, prepared, _run(ready, "moderation", MODERATION)).figures[0]
    assert slopes.kind == "line" and len(slopes.series) == 3
    assert slopes.categories == ("−1 ÉT", "moyenne", "+1 ÉT")


# --- In the Method, the plan and the article. ---


def test_the_method_sentences():
    assert "résidus" in plain(_method_sentences("partial", "", "none")[0])
    assert "terme d'interaction" in plain(_method_sentences("moderation", "", "none")[0])


@pytest.mark.parametrize(
    ("key", "chosen", "effect", "name", "seen"),
    [
        ("partial", PARTIAL, "partial", "la corrélation partielle entre stress et sommeil",
         "La corrélation partielle observée était négative."),
        ("moderation", MODERATION, "interaction", "l'interaction entre charge et soutien",
         "L'interaction observée était négative."),
    ],
)  # fmt: skip
def test_in_the_plan_and_the_article(ready, key, chosen, effect, name, seen):  # noqa: F811
    project, prepared = ready
    data = pl.data_from_names(project, "Une hypothèse.", key, chosen, {}, pair=None,
                              predictor=None, model=False, direction="negative",
                              kind="confirmatory", family="F1")  # fmt: skip
    hypothesis = pl.build(project, data, "H1")
    assert hypothesis.effect.kind == effect
    assert pl.review(project, hypothesis, prepared).ok
    assert prereg._effect(project, hypothesis) == name
    assert prereg._direction(project, hypothesis).endswith("négative")
    result = run(project, prepared, key, chosen, hypothesis.options)
    tested = article.Tested(hypothesis, result, "p", p_adj=0.5, m=2)
    assert article.observed(Codebook(project, prepared), prepared, tested) == seen
    document = article.adjusted_tables(describe(project, prepared, result), tested, "holm")
    table = document.tables[0]
    headers = [plain(c.header) for c in table.columns]
    assert "p corrigé (Holm)" in headers
    at = headers.index("p corrigé (Holm)")
    assert [plain(r.cells[at]) for r in table.rows][-1] == ",500"


# --- The page and the command line. ---


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_page_gives_the_command_result(tmp_path):
    paths = []
    for name in ("page", "commande"):
        folder = tmp_path / name
        folder.mkdir()
        shutil.copy(EXAMPLES / KEY["sav"], folder / KEY["sav"])
        path = folder / "etude-suivi.dd.json"
        save_project(build_project(read_database(folder / KEY["sav"])), path)
        paths.append(path)
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(paths[0])
    app.session_state["mode"] = "analyses"
    app.run()
    app.selectbox(key="analysis-key").set_value("moderation").run()
    app.selectbox(key="analysis-moderation-outcome").set_value("epuisement").run()
    app.selectbox(key="analysis-moderation-focal").set_value("charge").run()
    app.selectbox(key="analysis-moderation-moderator").set_value("soutien").run()
    app.button(key="analysis-run").click().run()
    assert not app.exception, app.exception
    app.button(key="analysis-write").click().run()
    assert main(["analyser", str(paths[1]), "moderation", "--dependante", "epuisement",
                 "--focal", "charge", "--moderateur", "soutien"]) == 0  # fmt: skip
    for suffix in (".md", ".R"):
        name = f"etude-suivi-analyse-1{suffix}"
        assert paths[0].with_name(name).read_text(encoding="utf-8") == paths[1].with_name(
            name
        ).read_text(encoding="utf-8")
