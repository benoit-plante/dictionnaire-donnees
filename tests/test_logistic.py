"""v0.14, step 4: the binary logistic regression (docs/catalogue-elargi.md, § 4), checked
against the answer key of the follow-up base, against R's glm, in every format, and in the
plan and the article."""

import shutil
from dataclasses import replace

import pytest
from streamlit.testing.v1 import AppTest

from ddict.analysis import article_text as article
from ddict.analysis import conditions, prereg
from ddict.analysis import planning as pl
from ddict.analysis.apa import describe, plain
from ddict.analysis.book import Codebook
from ddict.analysis.compute import run
from ddict.analysis.formats import FORMATS, available
from ddict.analysis.formats.figures import log_ticks
from ddict.analysis.method_text import _method_sentences
from ddict.cli import main
from ddict.io import read_database
from ddict.project import build_project, save_project
from test_analysis_page import APP
from test_paired import EXACT, EXAMPLES, KEY, ready  # noqa: F401
from test_partial_moderation import _r_results
from test_syntax import _rscript

CHOSEN = {"outcome": ["abandon"], "predictors": ["motivation", "age"]}
NOMINAL = {"outcome": ["abandon"], "predictors": ["motivation", "sexe"]}


def _run(ready, chosen=CHOSEN, options=None):  # noqa: F811
    project, prepared = ready
    return run(project, prepared, "logistic", chosen, options)


# --- Against the answer key and the sheet. ---


def test_against_the_key(ready):  # noqa: F811
    result = _run(ready)
    exact = EXACT["logistique_abandon"]
    s = result.statistics
    assert (s["n"], s["events"]) == (exact["n"], exact["events"])
    for i, (coef, ratio) in enumerate(zip(exact["coef"], exact["odds_ratios"], strict=True)):
        assert s[f"coef_{i}"] == pytest.approx(coef, abs=1e-7)
        assert s[f"or_{i}"] == pytest.approx(ratio, rel=1e-7)
    assert s["chi2"] == pytest.approx(exact["chi2"], abs=1e-7)
    assert s["mcfadden"] == pytest.approx(exact["mcfadden_r2"], abs=1e-9)


def test_the_sentence_and_the_table(ready):  # noqa: F811
    result = _run(ready)
    assert result.sentence == (
        "Régression logistique de « A abandonné le programme » (Oui, 76 sur 240) : χ²(2) = "
        "38,11, p < ,001 face au modèle sans prédicteur, R² de Nagelkerke = ,21. Les "
        "coefficients et les rapports de cotes sont dans le tableau."
    )
    assert result.tables[0].rows[1][5:] == ["0,60", "IC 95 % [0,50 ; 0,72]"]
    first = _run(ready, options={"event": "first"})
    assert "(Non, 164 sur 240)" in first.sentence
    assert first.statistics["or_1"] == pytest.approx(1 / result.statistics["or_1"])


# --- The conditions and the warnings. ---


def test_the_conditions(ready):  # noqa: F811
    project, prepared = ready
    three = conditions.check(project, "logistic", {**CHOSEN, "outcome": ["sexe"]}, data=prepared)
    assert any("3 modalités observées" in r for r in three.refusals)
    many = ["motivation", "age", "charge", "soutien", "stress", "sommeil", "epuisement",
            "anxiete_t1"]  # fmt: skip
    rare = conditions.check(project, "logistic", {"outcome": ["abandon"], "predictors": many},
                            data=prepared)  # fmt: skip
    assert any("76 personnes dans la modalité la plus rare pour 8 prédicteurs" in r
               for r in rare.refusals)  # fmt: skip
    assert conditions.check(project, "logistic", CHOSEN, data=prepared).ok


def test_separation_is_said(ready):  # noqa: F811
    project, prepared = ready
    table = prepared.table.copy()
    table["motivation"] = table["abandon"] * 5 + 1  # motivation tells the outcome exactly
    result = run(project, replace(prepared, table=table), "logistic", CHOSEN, None)
    assert any(w.startswith("Séparation complète ou quasi complète") for w in result.warnings)
    assert not _run(ready).warnings


# --- Against R. ---


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
@pytest.mark.parametrize(("chosen", "options"), [(CHOSEN, None), (NOMINAL, {"event": "first"})])
def test_the_same_results_as_r(ready, chosen, options, tmp_path):  # noqa: F811
    here = _run(ready, chosen, options).statistics
    from_r = _r_results(ready, "logistic", chosen, options, tmp_path)
    common = [k for k in here if k in from_r]
    assert len(common) >= 20
    for name in common:
        assert here[name] == pytest.approx(from_r[name], rel=1e-6, abs=1e-10), name


# --- Tables and figures. ---


@pytest.mark.parametrize("language", ["fr", "en"])
@pytest.mark.parametrize("chosen", [CHOSEN, NOMINAL])
@pytest.mark.parametrize("fmt", list(FORMATS))
def test_every_format_renders_everything(ready, fmt, chosen, language):  # noqa: F811
    project, prepared = ready
    document = describe(project, prepared, _run(ready, chosen), language=language)
    found = FORMATS[fmt]
    assert found in available(document)
    text = " ".join(found.read_text(found.render(document)).replace(chr(0xA0), " ").split())
    expected = [t for f in document.figures for t in (f.title, plain(f.note))]
    if found.tables:
        table = document.tables[0]
        expected += [table.title, plain(table.note), *[plain(c.header) for c in table.columns]]
        expected += [plain(cell) for row in table.rows for cell in row.cells]
    missing = [t for t in expected if " ".join(t.replace(chr(0xA0), " ").split()) not in text]
    assert not missing, missing


def test_the_figure_of_odds_ratios(ready):  # noqa: F811
    project, prepared = ready
    figure = describe(project, prepared, _run(ready)).figures[0]
    assert (figure.kind, figure.reference, figure.log_scale) == ("coefficients", 1.0, True)
    assert figure.series[0].values[0] == pytest.approx(0.6034676764)


@pytest.mark.parametrize(
    ("low", "high", "ticks"),
    [
        (0.47, 1.0, [0.5, 0.7, 1.0]),
        (0.88, 1.0, [0.9, 0.95, 1.0]),  # the AMATUS trial: under a decade, still several
        (0.3, 4.0, [0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0]),
        (0.05, 20.0, [0.1, 1.0, 10.0]),
    ],
)
def test_plain_values_on_the_logarithmic_axis(low, high, ticks):
    """Not the powers of ten (5e-1, 6e-1...) that overlap, as matplotlib writes them."""
    assert log_ticks(low, high) == ticks


# --- In the Method, the plan and the article. ---


def test_the_method_sentence():
    assert "rapports de cotes" in plain(_method_sentences("logistic", "second", "none")[0])


def test_in_the_plan_and_the_article(ready):  # noqa: F811
    project, prepared = ready
    data = pl.data_from_names(project, "La motivation retient.", "logistic", CHOSEN, {},
                              pair=None, predictor="motivation", model=False,
                              direction="negative", kind="confirmatory", family="")  # fmt: skip
    hypothesis = pl.build(project, data, "H1")
    assert pl.review(project, hypothesis, prepared).ok
    assert prereg._effect(project, hypothesis) == "le rapport de cotes de motivation"
    assert prereg._direction(project, hypothesis) == "un rapport de cotes inférieur à 1"
    result = run(project, prepared, "logistic", CHOSEN, hypothesis.options)
    tested = article.Tested(hypothesis, result, "p_1", variable="motivation")
    book = Codebook(project, prepared)
    assert article.observed(book, prepared, tested) == (
        "Le rapport de cotes observé de Motivation au début du programme (1 à 10) était "
        "inférieur à 1."
    )
    assert article.effect_only(book, tested, "holm") == (
        "Motivation au début du programme (1 à 10) : RC = 0,60, IC 95 % [0,50 ; 0,72], "
        "z = −5,43, p < ,001."
    )


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
    app.selectbox(key="analysis-key").set_value("logistic").run()
    app.selectbox(key="analysis-logistic-outcome").set_value("abandon").run()
    app.multiselect(key="analysis-logistic-predictors").set_value(["motivation", "age"]).run()
    app.button(key="analysis-run").click().run()
    assert not app.exception, app.exception
    app.button(key="analysis-write").click().run()
    assert main(["analyser", str(paths[1]), "logistique", "--dependante", "abandon",
                 "--predicteurs", "motivation", "age"]) == 0  # fmt: skip
    for suffix in (".md", ".R"):
        name = f"etude-suivi-analyse-1{suffix}"
        assert paths[0].with_name(name).read_text(encoding="utf-8") == paths[1].with_name(
            name
        ).read_text(encoding="utf-8")
