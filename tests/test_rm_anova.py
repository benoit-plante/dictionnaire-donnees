"""v0.14, step 5: the repeated-measures ANOVA (docs/catalogue-elargi.md, § 3), checked against
the answer key of the follow-up base, against R (anova.mlm, mauchly.test), in every format,
and in the plan and the article."""

import shutil
from dataclasses import replace

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from ddict.analysis import conditions, prereg
from ddict.analysis import planning as pl
from ddict.analysis.apa import describe, plain
from ddict.analysis.compute import run
from ddict.analysis.formats import FORMATS, available
from ddict.analysis.method_text import _method_sentences
from ddict.analysis.models import holm
from ddict.cli import main
from ddict.io import read_database
from ddict.project import build_project, save_project
from ddict.project.model import TrackedValue
from test_analysis_page import APP
from test_paired import EXACT, EXAMPLES, KEY, ready  # noqa: F401
from test_partial_moderation import _r_results
from test_syntax import _rscript

TIMES = {"measures": ["anxiete_t1", "anxiete_t2", "anxiete_t3"]}


def _run(ready, options=None, chosen=TIMES):  # noqa: F811
    project, prepared = ready
    return run(project, prepared, "rm_anova", chosen, options)


# --- Against the answer key and the sheet. ---


def test_against_the_key(ready):  # noqa: F811
    s = _run(ready).statistics
    exact = EXACT["anova_rm_anxiete"]
    assert s["n"] == exact["n"]
    assert [s["m_1"], s["m_2"], s["m_3"]] == pytest.approx(exact["means"], abs=1e-10)
    assert s["F"] == pytest.approx(exact["F"], abs=1e-8)
    assert [s["df1"], s["df2"]] == exact["df"]
    assert s["eta2p"] == pytest.approx(exact["eta2_partial"], abs=1e-10)
    assert s["gg_eps"] == pytest.approx(exact["gg_epsilon"], abs=1e-10)


def test_the_sentence_corrected_when_mauchly_rejects(ready):  # noqa: F811
    result = _run(ready)
    assert result.statistics["mauchly_p"] < 0.05
    assert result.statistics["p"] == result.statistics["gg_p"]
    assert result.sentence == (
        "Comparaison de 3 mesures : F(1,72 ; 346,74) = 28,93, p < ,001, η²p = ,13, ε = 0,86 "
        "(Greenhouse-Geisser) ; moyennes : Anxiété au début du programme (0 à 40) 21,60 ; "
        "Anxiété à la fin du programme (0 à 40) 18,69 ; Anxiété trois mois après (0 à 40) "
        "17,86 (n = 203)."
    )
    assert (result.n_used, result.n_excluded) == (203, 37)


def test_the_english_sentence_has_english_punctuation(ready):  # noqa: F811
    """v0.15: the means were joined by the French " ; " in English too."""
    from ddict import i18n

    with i18n.using("en"):
        sentence = _run(ready).sentence
    assert "21.60; Anxiété à la fin" in sentence and " ; " not in sentence


def test_uncorrected_when_sphericity_holds(ready):  # noqa: F811
    """Compound symmetry (a person's level plus independent errors): Mauchly does not reject,
    and the sentence gives the plain degrees of freedom."""
    project, prepared = ready
    rng = np.random.default_rng(7)
    table = prepared.table.copy()
    person = rng.normal(0, 5, len(table))
    for i, name in enumerate(TIMES["measures"]):
        table[name] = 20 - i + person + rng.normal(0, 3, len(table))
    result = run(project, replace(prepared, table=table), "rm_anova", TIMES, None)
    s = result.statistics
    assert s["mauchly_p"] >= 0.05 and s["p"] == s["p_uncorrected"]
    assert f"F(2, {2 * (len(table) - 1)}) = " in result.sentence
    assert "Greenhouse" not in result.sentence and not result.warnings


def test_holm_as_r_does_it():
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert holm([0.5, 0.2]) == pytest.approx([0.5, 0.4])


def test_the_pairwise_comparisons(ready):  # noqa: F811
    result = _run(ready, {"post_hoc": "holm"})
    s = result.statistics
    assert s["ph_1_2_t"] == pytest.approx(7.315750926815942)
    assert s["ph_2_3_p_holm"] == pytest.approx(0.14546475896755973)
    assert len(result.tables[1].rows) == 3


# --- The conditions. ---


def test_the_conditions(ready):  # noqa: F811
    project, prepared = ready
    two = conditions.check(project, "rm_anova", {"measures": ["anxiete_t1", "anxiete_t2"]})
    assert any("de 3 à 10 variables" in r for r in two.refusals)
    few = conditions.check(project, "rm_anova", TIMES,
                           data=replace(prepared, table=prepared.table.head(2)))  # fmt: skip
    assert any("il en faut au moins 3" in r for r in few.refusals)
    long = project.model_copy(deep=True)
    long.dataset.structure = TrackedValue[str](value="long", origin="human", status="validated")
    assert any("format long" in r for r in conditions.check(long, "rm_anova", TIMES).refusals)


# --- Against R. ---


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
@pytest.mark.parametrize("options", [None, {"post_hoc": "holm"}])
def test_the_same_results_as_r(ready, options, tmp_path):  # noqa: F811
    here = _run(ready, options).statistics
    from_r = _r_results(ready, "rm_anova", TIMES, options, tmp_path)
    common = [k for k in here if k in from_r]
    assert len(common) >= 19
    for name in common:
        assert here[name] == pytest.approx(from_r[name], rel=1e-6, abs=1e-10), name


# --- Tables and figures. ---


@pytest.mark.parametrize("language", ["fr", "en"])
@pytest.mark.parametrize("options", [None, {"post_hoc": "holm"}])
@pytest.mark.parametrize("fmt", list(FORMATS))
def test_every_format_renders_everything(ready, fmt, options, language):  # noqa: F811
    project, prepared = ready
    document = describe(project, prepared, _run(ready, options), language=language)
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


def test_the_figure(ready):  # noqa: F811
    project, prepared = ready
    figure = describe(project, prepared, _run(ready)).figures[0]
    assert figure.kind == "line" and len(figure.categories) == 3
    assert [round(v, 2) for v in figure.series[0].values] == [21.6, 18.69, 17.86]


# --- In the Method, the plan and the article. ---


def test_the_method_sentences():
    found = [plain(t) for t in _method_sentences("rm_anova", "", "holm")]
    assert "Greenhouse-Geisser" in found[0] and "Holm" in found[1]


def test_in_the_plan(ready):  # noqa: F811
    project, prepared = ready
    data = pl.data_from_names(project, "L'anxiété change.", "rm_anova", TIMES, {}, pair=None,
                              predictor=None, model=False, direction="", kind="confirmatory",
                              family="")  # fmt: skip
    hypothesis = pl.build(project, data, "H1")
    assert hypothesis.effect.kind == "group"
    assert pl.review(project, hypothesis, prepared).ok
    assert prereg._effect(project, hypothesis) == "l'effet du temps"
    directed = pl.build(project, {**data, "direction": "positive"}, "H2")
    assert any("ne teste pas de sens" in r for r in pl.review(project, directed).refusals)


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
    app.selectbox(key="analysis-key").set_value("rm_anova").run()
    app.multiselect(key="analysis-rm_anova-measures").set_value(TIMES["measures"]).run()
    app.button(key="analysis-run").click().run()
    assert not app.exception, app.exception
    app.button(key="analysis-write").click().run()
    assert main(["analyser", str(paths[1]), "anova_rm", "--mesures", *TIMES["measures"]]) == 0
    for suffix in (".md", ".R"):
        name = f"etude-suivi-analyse-1{suffix}"
        assert paths[0].with_name(name).read_text(encoding="utf-8") == paths[1].with_name(
            name
        ).read_text(encoding="utf-8")
