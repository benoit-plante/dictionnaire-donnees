"""v0.13, step 3: the notebook matched to the frozen plan, and the correction for multiple
comparisons (D-102 to D-104), as the validated sheet docs/plan-analyse-article.md (§ 5 to 7)
describes them, on the planted cases of § 6."""

import json
import subprocess
from pathlib import Path

import pytest

from ddict.analysis import notebook as nb
from ddict.analysis import notebook_check as check
from ddict.analysis import plan_notebook as pn
from ddict.analysis import planning as pl
from ddict.analysis.compute import run
from ddict.project.model import TrackedValue
from test_analysis_data import KEY, _prepared, analyses_project
from test_plan import EXAMPLE, RULES
from test_syntax import _rscript

BEFORE = "2026-10-18"
TODAY = "2026-10-20"
LATER = "2026-11-02"


@pytest.fixture
def ready():
    project = analyses_project()
    prepared = _prepared(project, KEY["sav"])
    notebook = nb.new_notebook(project, Path("etude-analyses.dd.json"))
    return project, prepared, notebook


def _add(ready, key, chosen, options=None, today=BEFORE):
    project, prepared, notebook = ready
    return nb.add(notebook, project, run(project, prepared, key, chosen, options), today=today)


def _frozen(ready):
    """The sheet's planted cases: before freezing, the notebook holds a Table 1, H3's ANOVA
    exactly (prior), a Spearman correlation of H2's variables (a variant) and a chi-square
    no hypothesis plans (exploratory)."""
    project, prepared, notebook = ready
    _add(ready, "table1", {"variables": ["age", "sexe"]})
    _add(ready, "anova", {"outcome": ["stress"], "group": ["niveau_etudes"]})
    _add(ready, "correlation", {"variables": ["heures_travail", "stress"]}, {"method": "spearman"})
    _add(ready, "chi_square", {"rows": ["teletravail"], "columns": ["secteur"]})
    for data in EXAMPLE:
        pl.add(project, data, prepared)
    pl.set_rules(project, RULES)
    pn.freeze(notebook, project, prepared, TODAY)
    return project, prepared, notebook


def _entry(notebook, hypothesis):
    return next(e for e in notebook.entries if e.hypothesis == hypothesis)


def _states(ready):
    project, _prepared_data, notebook = ready
    return {e.id: pn.state_text(pn.state(notebook, project, e), e) for e in notebook.entries}


# --- Freezing ties each hypothesis to its entry. ---


def test_freezing_ties_each_hypothesis_to_an_entry(ready):
    project, _prepared_data, notebook = _frozen(ready)
    prior = [p.model_dump(mode="json") for p in project.plan.frozen.prior]
    assert prior == [{"hypothesis": "H3", "entry": "A2", "added": BEFORE}]
    assert [(e.id, e.hypothesis) for e in notebook.entries] == [
        ("A1", None), ("A2", "H3"), ("A3", None), ("A4", None),
        ("A5", "H1"), ("A6", "H2"), ("A7", "H4"), ("A8", "H5"),
    ]  # fmt: skip
    created = _entry(notebook, "H1")
    assert created.added == TODAY and created.retained
    assert created.options == {"alternative": "greater", "method": "welch"}
    assert _states(ready) == {
        "A1": "descriptive",
        "A2": "prévue (H3)",
        "A3": "variante de H2 : Méthode : Spearman au lieu de Pearson",
        "A4": "exploratoire",
        "A5": "prévue (H1)",
        "A6": "prévue (H2)",
        "A7": "prévue (H4)",
        "A8": "prévue, exploratoire (H5)",
    }
    assert pn.deviations(notebook, project) == []


def test_freezing_needs_the_database(ready):
    project, prepared, notebook = ready
    for data in EXAMPLE:
        pl.add(project, data, prepared)
    pl.set_rules(project, RULES)
    with pytest.raises(pl.PlanRefused) as refused:
        pn.freeze(notebook, project, None, TODAY)
    assert refused.value.reasons == [
        "Ouvrez la base pour figer le plan : chaque hypothèse devient une analyse du carnet."
    ]
    assert project.plan.frozen is None and notebook.entries == []


def test_without_a_frozen_plan_nothing_changes(ready):
    project, _prepared_data, notebook = ready
    entry = _add(ready, "table1", {"variables": ["age"]})
    assert pn.state(notebook, project, entry) is None and pn.state_text(None) == ""
    assert pn.sync(notebook, project, None, TODAY) == []
    assert pn.deviations(notebook, project) == []


def test_a_planned_analysis_is_never_removed(ready):
    _project, _prepared_data, notebook = _frozen(ready)
    with pytest.raises(nb.NotebookError) as refused:
        nb.remove(notebook, "A5")
    assert nb.reason_text(refused.value) == (
        "A5 est une analyse prévue par le plan : elle ne se retire pas du carnet. Ne la "
        "retenez plus, ou modifiez le plan."
    )
    nb.remove(notebook, "A4")  # an exploratory one is


# --- Deviations. ---


def test_a_planned_analysis_not_retained_is_a_deviation(ready):
    project, _prepared_data, notebook = _frozen(ready)
    nb.retain(notebook, "A5", False)
    [deviation] = pn.deviations(notebook, project)
    assert (deviation.hypothesis, deviation.kind) == ("H1", "not_retained")
    assert deviation.text == "H1 : l'analyse prévue n'est pas retenue dans le carnet."


def test_a_planned_analysis_that_cannot_be_computed_is_a_deviation(ready):
    project, prepared, notebook = _frozen(ready)
    project.variable("satisfaction").measure_level = TrackedValue[str](
        value="ordinal", origin="human", status="none"
    )
    statuses = check.check_all(notebook, project, prepared, today=LATER)
    [deviation] = pn.deviations(notebook, project, statuses)
    assert (deviation.hypothesis, deviation.kind) == ("H4", "impossible")
    assert deviation.text.startswith("H4 : l'analyse prévue ne peut plus être faite : ")
    assert "satisfaction" in deviation.text


# --- Amendments untie and tie again. ---


def test_an_amendment_replaces_the_planned_analysis(ready):
    project, prepared, notebook = _frozen(ready)
    pl.modify(project, "H2", {"options": {"method": "spearman"}}, prepared,
              "Distribution des heures très asymétrique", LATER)  # fmt: skip
    assert pn.sync(notebook, project, prepared, LATER) == []
    old = next(e for e in notebook.entries if e.id == "A6")
    assert old.hypothesis is None and not old.retained
    assert old.superseded.model_dump(mode="json") == {
        "date": LATER,
        "hypothesis": "H2",
        "change": "modified",
    }
    assert _entry(notebook, "H2").id == "A3"  # the Spearman variant computes it already
    states = _states(ready)
    assert states["A6"] == "remplacée par l'amendement du 2 novembre 2026 (H2)"
    assert states["A3"] == "prévue (H2)"
    assert len(notebook.entries) == 8  # nothing created


def test_an_amendment_without_an_entry_ready_computes_a_new_one(ready):
    project, prepared, notebook = _frozen(ready)
    pl.modify(project, "H3", {"options": {"post_hoc": "tukey"}}, prepared, "Tukey oublié", LATER)
    pn.sync(notebook, project, prepared, LATER)
    new = _entry(notebook, "H3")
    assert new.id == "A9" and new.options == {"method": "anova", "post_hoc": "tukey"}
    assert new.added == LATER


def test_an_hypothesis_removed_unties_its_entry(ready):
    project, prepared, notebook = _frozen(ready)
    pl.remove(project, "H5", "Hors du sujet", LATER)
    pn.sync(notebook, project, prepared, LATER)
    assert _states(ready)["A8"] == "H5 retirée du plan le 2 novembre 2026"


def test_without_the_database_a_new_hypothesis_waits(ready):
    project, prepared, notebook = _frozen(ready)
    data = EXAMPLE[2] | {"options": {"method": "kruskal_wallis"}, "family": None}
    pl.add(project, data, prepared, "Robustesse", LATER)
    waiting = pn.sync(notebook, project, None, LATER)
    assert waiting == ["H6 : l'analyse prévue sera calculée quand la base sera ouverte."]
    [deviation] = pn.deviations(notebook, project)
    assert deviation.text == "H6 : l'analyse prévue n'est pas dans le carnet."
    assert pn.sync(notebook, project, prepared, LATER) == []
    assert _entry(notebook, "H6").options["method"] == "kruskal_wallis"


def test_a_notebook_of_v0_12_reads_as_it_is(ready, tmp_path):
    _project, _prepared_data, notebook = ready
    _add(ready, "table1", {"variables": ["age"]})
    data = json.loads(nb.dumps(notebook))
    data["carnet_version"] = "1.1.0"
    for entry in data["entries"]:
        del entry["hypothesis"], entry["superseded"]
    path = tmp_path / "carnet.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    old = nb.load_notebook(path)
    assert old.carnet_version == "1.2.0" and old.entries == notebook.entries


# --- The tested effect's p-value. ---


def test_the_key_of_a_tested_effect(ready):
    project, prepared, _notebook = ready
    pair = pl.add(project, EXAMPLE[1] | {
        "roles": {"variables": [{"variable": "age"}, {"variable": "heures_travail"},
                                {"variable": "stress"}]},
        "effect": {"kind": "pair", "variables": [{"variable": "stress"},
                                                 {"variable": "heures_travail"}]}},
        prepared)  # fmt: skip
    entry = _add(ready, "correlation", {"variables": ["age", "heures_travail", "stress"]})
    assert pn.effect_p_key(project, prepared, pair, entry) == "p_3_2"
    roles = {"outcome": [{"variable": "satisfaction"}],
             "predictors": [{"variable": "sexe"}, {"variable": "soutien"}]}  # fmt: skip
    entry = _add(
        ready, "regression", {"outcome": ["satisfaction"], "predictors": ["sexe", "soutien"]}
    )
    for variable, key in (("sexe", "p_1"), ("soutien", "p_2")):
        hypothesis = pl.add(project, EXAMPLE[3] | {
            "roles": roles, "effect": {"kind": "predictor", "variable": {"variable": variable}},
            "direction": None}, prepared)  # fmt: skip
        assert pn.effect_p_key(project, prepared, hypothesis, entry) == key
        assert pn.effect_p_key(project, None, hypothesis, entry) is None  # needs the data
    assert entry.computed.statistics["p_2"] > 0


# --- The correction (D-104). ---

P_SETS = [
    [0.010, 0.020, 0.030],
    [0.010, 0.010, 0.040, 0.200],  # ties
    [0.400, 0.600, 0.900, 0.020],  # reaching 1
    [0.0004, 0.049, 0.0012, 0.31, 0.049, 0.008, 0.7],
]


def test_the_sheets_example_of_the_correction():
    assert pn.adjust([0.010, 0.020, 0.030], "holm") == pytest.approx([0.030, 0.040, 0.040])
    assert pn.adjust([0.010, 0.020, 0.030], "bonferroni") == pytest.approx([0.030, 0.060, 0.090])
    assert pn.adjust([0.4, 0.6, 0.9, 0.02], "bonferroni")[2] == 1.0
    assert pn.adjust([0.4, 0.6], "none") == [0.4, 0.6]


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
@pytest.mark.parametrize("method", ["holm", "bonferroni"])
def test_the_correction_equals_rs_p_adjust(method):
    for pvalues in P_SETS:
        vector = ", ".join(repr(p) for p in pvalues)
        code = f'cat(sprintf("%.17g", p.adjust(c({vector}), "{method}")), sep="\\n")'
        output = subprocess.run(
            [_rscript(), "-e", code], capture_output=True, text=True, check=True
        ).stdout
        expected = [float(line) for line in output.split()]
        assert pn.adjust(pvalues, method) == pytest.approx(expected, rel=0, abs=1e-12)


def test_a_family_is_adjusted_and_kept_at_once(ready):
    project, prepared, notebook = _frozen(ready)
    statuses = check.check_all(notebook, project, prepared, today=TODAY)
    assert check.blocking(notebook, statuses) == []  # new adjusted p-values: kept at once
    members = [_entry(notebook, h) for h in ("H1", "H2", "H3")]
    raw = [members[0].computed.statistics["p"], members[1].computed.statistics["p_2_1"],
           members[2].computed.statistics["p"]]  # fmt: skip
    for entry, value in zip(members, pn.adjust(raw, "holm"), strict=True):
        assert entry.computed.statistics[pn.P_ADJ] == pytest.approx(value, rel=1e-12)
        assert entry.computed.statistics[pn.ADJ_M] == 3
    for hypothesis in ("H4", "H5"):  # no family; exploratory
        assert pn.P_ADJ not in _entry(notebook, hypothesis).computed.statistics
    again = check.check_all(notebook, project, prepared, today=TODAY)
    assert {s.state for s in again} == {"current"}


def test_an_amendment_that_changes_the_correction_waits_for_a_confirmation(ready):
    project, prepared, notebook = _frozen(ready)
    check.check_all(notebook, project, prepared, today=TODAY)
    pl.set_rules(project, {"correction": "bonferroni"}, "Avis du comité", LATER)
    statuses = check.check_all(notebook, project, prepared, today=LATER)
    waiting = check.blocking(notebook, statuses)
    assert set(waiting) <= {"A2", "A5", "A6"} and waiting  # the codebook did not change
    for status in statuses:
        if status.entry_id in waiting:
            assert [d.key for d in status.differences] == [pn.P_ADJ]
    for entry_id in waiting:
        check.confirm(notebook, entry_id)
    assert check.blocking(notebook, check.check_all(notebook, project, prepared, today=LATER)) == []


def test_an_hypothesis_leaving_its_family_loses_its_adjusted_p(ready):
    project, prepared, notebook = _frozen(ready)
    check.check_all(notebook, project, prepared, today=TODAY)
    pl.modify(project, "H3", {"family": None}, prepared, "Question à part", LATER)
    statuses = {s.entry_id: s for s in check.check_all(notebook, project, prepared, today=LATER)}
    h3 = _entry(notebook, "H3")
    assert statuses[h3.id].state == "changed"
    assert statuses[h3.id].differences[-1].after is None
    check.confirm(notebook, h3.id)
    assert pn.P_ADJ not in h3.computed.statistics
    for hypothesis in ("H1", "H2"):  # a family of two now
        entry = _entry(notebook, hypothesis)
        assert (entry.pending or entry.computed).statistics[pn.ADJ_M] == 2


def test_an_entry_not_retained_leaves_its_family(ready):
    project, prepared, notebook = _frozen(ready)
    nb.retain(notebook, _entry(notebook, "H2").id, False)
    nb.retain(notebook, _entry(notebook, "H3").id, False)
    check.check_all(notebook, project, prepared, today=TODAY)
    assert pn.P_ADJ not in _entry(notebook, "H1").computed.statistics  # a family of one
