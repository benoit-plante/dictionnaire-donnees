"""v0.11, step 3: recompute the notebook, say what changed, confirm (D-089), as the
validated sheet docs/carnet-analyses.md, § 5 and 6, describes it."""

from pathlib import Path

import pytest

from ddict.analysis import notebook as nb
from ddict.analysis import notebook_check as check
from ddict.analysis.compute import run
from ddict.analysis.data import apply_decisions
from ddict.io import read_database
from ddict.project import build_project
from ddict.project.model import TrackedValue
from ddict.review import logic, study
from test_analysis_data import KEY, _prepared, analyses_project

EXAMPLES = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"
TODAY = "2026-10-16"
LATER = "2026-10-17"
NOW = "2026-10-16T12:00:00"
CORRELATION = {"variables": ["age", "heures_sommeil"]}


@pytest.fixture
def sleep():
    """The sleep study: its code 999 of age is suspect, not declared in the file."""
    database = read_database(EXAMPLES / "etude-sommeil.sav")
    project = build_project(database)
    notebook = nb.new_notebook(project, Path("etude-sommeil.dd.json"))
    result = run(project, apply_decisions(project, database.table), "correlation", CORRELATION)
    nb.add(notebook, project, result, today=TODAY)
    return project, database.table, notebook


def _prepared_now(project, table):
    return apply_decisions(project, table)


# --- The sheet's scenario (§ 6). ---


def test_a_missing_code_confirmed_after_the_fact(sleep):
    project, table, notebook = sleep
    entry = notebook.entries[0]
    assert entry.computed.statistics["n"] == 200
    logic.decide_sentinel(project, "age", 999, True, now=NOW)
    [status] = check.check_all(notebook, project, _prepared_now(project, table), today=LATER)
    assert status.state == "changed"
    shown = {d.key: (d.shown_before, d.shown_after) for d in status.differences}
    assert shown["n"] == ("200", "197")
    assert shown["r"] == (",04", ",07")
    assert shown["p"] == (",572", ",342")
    assert shown["ci_low"] == ("−,10", "−,07") and shown["ci_high"] == (",18", ",21")
    assert shown["n_used"] == ("200", "197")
    assert not {"r_2_1", "p_2_1", "n_2_1", "low_2_1", "high_2_1"} & set(shown)  # said once
    assert entry.pending is not None and entry.computed.statistics["n"] == 200  # not yet
    assert check.blocking(notebook, [status]) == ["A1"]  # the export waits
    check.confirm(notebook, "A1")
    assert entry.computed.statistics["n"] == 197 and entry.pending is None
    [status] = check.check_all(notebook, project, _prepared_now(project, table), today=LATER)
    assert status.state == "current"


def test_a_decision_without_effect(sleep):
    project, table, notebook = sleep
    entry = notebook.entries[0]
    before = entry.computed.fingerprint
    logic.decide(project, "age", "label", "correct", now=NOW, value="Âge déclaré (années)")
    [status] = check.check_all(notebook, project, _prepared_now(project, table), today=LATER)
    assert status.state == "unchanged" and not status.differences
    assert entry.computed.fingerprint != before and entry.computed.date == LATER
    assert entry.pending is None
    [status] = check.check_all(notebook, project, _prepared_now(project, table), today=LATER)
    assert status.state == "current"


def test_a_decision_taken_back(sleep):
    project, table, notebook = sleep
    logic.decide_sentinel(project, "age", 999, True, now=NOW)
    check.check_all(notebook, project, _prepared_now(project, table), today=LATER)
    assert notebook.entries[0].pending is not None
    logic.decide_sentinel(project, "age", 999, None, now=NOW)  # back as it was
    [status] = check.check_all(notebook, project, _prepared_now(project, table), today=LATER)
    assert status.state == "current" and notebook.entries[0].pending is None


def test_an_unretained_change_does_not_block(sleep):
    project, table, notebook = sleep
    nb.retain(notebook, "A1", False)
    logic.decide_sentinel(project, "age", 999, True, now=NOW)
    statuses = check.check_all(notebook, project, _prepared_now(project, table), today=LATER)
    assert statuses[0].state == "changed" and check.blocking(notebook, statuses) == []


# --- Impossible analyses. ---


def test_a_measure_level_that_no_longer_fits():
    project = analyses_project()
    prepared = _prepared(project, KEY["sav"])
    notebook = nb.new_notebook(project, Path("etude-analyses.dd.json"))
    chosen = {"outcome": ["stress"], "group": ["groupe"]}
    nb.add(notebook, project, run(project, prepared, "t_test", chosen), today=TODAY)
    project.variable("stress").measure_level = TrackedValue[str](
        value="ordinal", origin="human", status="none"
    )
    [status] = check.check_all(notebook, project, prepared, today=LATER)
    assert status.state == "impossible"
    assert "stress" in status.reason and "ordinal" in status.reason
    assert notebook.entries[0].id == "A1"  # never removed


def test_a_score_whose_scoring_was_removed():
    project = analyses_project()
    prepared = _prepared(project, KEY["sav"])
    notebook = nb.new_notebook(project, Path("etude-analyses.dd.json"))
    chosen = {"outcome": ["bienetre_total"], "group": ["groupe"]}
    nb.add(notebook, project, run(project, prepared, "t_test", chosen), today=TODAY)
    group = next(g for g in project.groups if "bienetre_1" in (g.members.value or []))
    study.remove_scoring(project, group.group_id)
    [status] = check.check_all(notebook, project, apply_decisions(project, prepared.table),
                               today=LATER)  # fmt: skip
    assert status.state == "impossible" and "plus de cotation" in status.reason


# --- The database. ---


def test_without_the_database_nothing_is_recomputed(sleep):
    project, _table, notebook = sleep
    logic.decide_sentinel(project, "age", 999, True, now=NOW)
    [status] = check.check_all(notebook, project, None, today=LATER, reason="introuvable")
    assert (status.state, status.reason) == ("no_database", "introuvable")
    assert notebook.entries[0].pending is None  # the notebook stays as it was, readable
    assert notebook.entries[0].computed.sentence  # its sentence still shows


def test_a_notebook_of_another_database(sleep):
    project, table, notebook = sleep
    notebook.project.source_sha256 = "0" * 64
    [status] = check.check_all(notebook, project, _prepared_now(project, table), today=LATER)
    assert status.state == "no_database" and "autre base" in status.reason


# --- An export never copies the notebook. ---


def test_always_recomputes_even_a_current_entry(sleep):
    project, table, notebook = sleep
    [status] = check.check_all(notebook, project, _prepared_now(project, table), today=TODAY,
                               always=True)  # fmt: skip
    assert status.state == "current" and status.result is not None
    assert status.result.statistics["r"] == pytest.approx(
        notebook.entries[0].computed.statistics["r"]
    )


def test_differences_ignore_keys_of_another_version(sleep):
    _project, _table, notebook = sleep
    before = notebook.entries[0].computed
    after = before.model_copy(update={"statistics": {**before.statistics, "new_key": 1.0}})
    assert check.differences(before, after) == ()
    tiny = before.model_copy(
        update={"statistics": {**before.statistics, "r": before.statistics["r"] * (1 + 1e-12)}}
    )
    assert check.differences(before, tiny) == ()  # below 10⁻⁹: nothing changed
    small = before.model_copy(
        update={"statistics": {**before.statistics, "r": before.statistics["r"] + 1e-5}}
    )
    [found] = check.differences(before, small)
    assert found.shown_before != found.shown_after  # more decimals, never two equal numbers
