"""v0.20, step B4: the data dictionary and the analysis plan before the collection — the
codebook and the analysis context of a designed project, the plan frozen without a database
(D-153), then each hypothesis tied to its entry when the database arrives. Fictional data."""

import json

import pytest

from ddict.analysis import notebook as nb
from ddict.analysis import plan_notebook as pn
from ddict.analysis import planning as pl
from ddict.analysis.planning import plan_fingerprint
from ddict.cli import main
from ddict.export import wording as w
from ddict.export.context import render_context
from ddict.export.markdown import render_markdown
from ddict.project import dumps, load_project, save_project
from ddict.project.decisions import validate
from ddict.project.model import Planned
from ddict.workflow import export_context
from projet_concu import project as designed
from test_analysis_data import KEY, _prepared, analyses_project
from test_plan import EXAMPLE, RULES

TODAY = "2026-10-20"
NOW = "2026-10-20T09:00:00"
CORRELATION = {
    "statement": "L'âge est lié à la qualité du sommeil.",
    "analysis": "correlation",
    "roles": {"variables": [{"variable": "Q2"}, {"variable": "Q4_SQ002"}]},
}
PLANNED_TYPES = {"boolean", "integer", "decimal", "date", "datetime", "text"}


def _before_collection(project):
    """The same study as if its questionnaire had been designed in the tool: its variables
    planned, with no database yet."""
    found = project.model_copy(deep=True)
    for entry in found.variables:
        kind = entry.profile.inferred_type
        entry.planned = Planned(type=kind if kind in PLANNED_TYPES else "text")
        entry.profile = None
    found.source = None
    return found


def _arrived(planned, based):
    """The database arrives: each variable gets the profile of its column (step E4 does it
    for real, from the file)."""
    found = planned.model_copy(deep=True)
    found.source = based.source
    for entry in found.variables:
        entry.profile = based.variable(entry.name).profile
    return found


# --- The codebook and the context ------------------------------------------------------------


def test_the_planned_dictionary_has_codes_and_no_counts():
    text = render_markdown(designed())
    assert "| Code | Étiquette | Manquant déclaré |" in text
    assert "| Effectif |" not in text and "masqués" not in text
    assert "| 9 | Préfère ne pas répondre |  |" in text
    assert "| Niveau de mesure | 0 / 7 |" in text  # proposed by the rules, to decide


def test_the_analysis_context_before_the_collection(tmp_path):
    project = designed()
    text = render_context(project, statistics=True)
    assert text.startswith("# Contexte d'analyse : Étude du sommeil (conception)")
    assert w.PLANNED_DICTIONARY in text and "8 variables prévues" in text
    assert "## Statistiques" not in text
    path = tmp_path / "Étude conçue.dd.json"
    save_project(project, path)
    written = export_context(project, path)
    assert [p.name for p in written] == ["Étude conçue-contexte.md"]
    assert not (tmp_path / "Étude conçue-datapackage.json").exists()


def test_the_command_line_says_what_waits_for_the_database(tmp_path, capsys):
    path = tmp_path / "conçue.dd.json"
    save_project(designed(), path)
    assert main(["exporter", str(path), "--syntaxe", "--contexte"]) == 2
    out, err = capsys.readouterr()
    assert "Pas encore de base" in err and "contexte.md" in out
    assert "Codebook Excel" in out and "Rapport Markdown" in out


# --- The plan, frozen before the collection (D-153) -----------------------------------------


def test_the_plan_is_frozen_before_the_database_then_each_hypothesis_gets_its_entry(tmp_path):
    based = analyses_project()
    planned = _before_collection(based)
    for data in EXAMPLE:
        pl.add(planned, data, None)
    pl.set_rules(planned, {**RULES, "data_status": "before_creation"})
    assert pl.freeze_refusals(planned) == []
    assert pn.freeze(None, planned, None, TODAY) == []
    frozen = planned.plan.frozen
    assert frozen.date == TODAY and frozen.prior == []
    # The database arrives: nothing of the plan changes, the notebook follows it.
    arrived = _arrived(planned, based)
    assert plan_fingerprint(arrived.plan) == frozen.fingerprint
    path = tmp_path / "etude-analyses.dd.json"
    notebook = nb.new_notebook(arrived, path)
    assert pn.sync(notebook, arrived, _prepared(arrived, KEY["sav"]), TODAY) == []
    assert {e.hypothesis for e in notebook.entries} == {h.id for h in arrived.plan.hypotheses}
    assert all(e.retained for e in notebook.entries)


def test_a_project_with_its_database_still_needs_it_to_freeze():
    project = analyses_project()
    for data in EXAMPLE:
        pl.add(project, data, None)
    pl.set_rules(project, RULES)
    try:
        pn.freeze(None, project, None, TODAY)
    except pl.PlanRefused as error:
        assert "Ouvrez la base" in error.reasons[0]
    else:
        raise AssertionError("frozen without its database")
    assert project.plan.frozen is None


def test_ddict_plan_figer_without_a_database(tmp_path, capsys):
    project = designed()
    for entry in project.variables:
        if entry.measure_level.status == "proposed":
            entry.measure_level = validate(entry.measure_level, now=NOW)
    pl.add(project, CORRELATION, None)
    path = tmp_path / "Étude du sommeil" / "conçue.dd.json"
    path.parent.mkdir()
    save_project(project, path)
    assert main(["plan", "regles", str(path), "--alpha", "0.05", "--origine", "primaires",
                 "--etat", "avant-creation"]) == 0  # fmt: skip
    assert main(["plan", "figer", str(path)]) == 0
    out = capsys.readouterr().out
    assert "Plan arrêté" in out and "deviendra une analyse du carnet" in out
    saved = load_project(path)
    assert saved.plan.frozen is not None and saved.source is None
    assert not nb.notebook_path(path).exists()  # no notebook before the database
    assert json.loads(dumps(saved))["plan"]["frozen"]["prior"] == []
    assert main(["plan", "lister", str(path)]) == 0


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_plan_page_freezes_before_the_database(tmp_path):
    from streamlit.testing.v1 import AppTest

    from test_notebook_page import APP

    project = designed()
    for entry in project.variables:
        if entry.measure_level.status == "proposed":
            entry.measure_level = validate(entry.measure_level, now=NOW)
    pl.add(project, CORRELATION, None)
    pl.set_rules(project, {**RULES, "data_status": "before_creation"})
    path = tmp_path / "Étude conçue" / "conçue.dd.json"
    path.parent.mkdir()
    save_project(project, path)
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "plan"
    app.run()
    assert not app.exception, app.exception
    text = " ".join(m.value for m in app.markdown)
    assert "Chaque hypothèse conforme au codebook prévu" in text
    assert "La base ouverte" not in text
    freeze = app.button(key="plan-freeze")
    assert not freeze.disabled
    freeze.click().run()
    assert not app.exception, app.exception
    assert load_project(path).plan.frozen is not None
    assert not nb.notebook_path(path).exists()
