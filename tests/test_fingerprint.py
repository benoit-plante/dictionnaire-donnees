"""v0.8, step 2: the fingerprint of a codebook, from the team's decisions only."""

from pathlib import Path

import pytest

from ddict.export import render_markdown
from ddict.export.syntax import spss
from ddict.project import fingerprint, load_project, save_project
from ddict.project.decisions import validate
from ddict.project.model import SentinelDecision, TrackedValue

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "tests" / "reference" / "etude-sommeil.dd.json"
NOW = "2026-10-15T12:00:00"
LATER = "2026-11-01T08:30:00"


@pytest.fixture
def project():
    return load_project(REFERENCE)


def test_the_same_on_every_computer(project):
    # The committed reference project: every system must give this value (the macOS
    # workflow runs this test there). It changes only when the reference is regenerated.
    assert fingerprint.fingerprint(project) == (
        "49e959e5a7da1328c85be3b3bc165ca9e95ae5b49f4e3d9ce269002d7773e741"
    )
    assert fingerprint.short(project) == "49e959e5a7da"


def test_same_decisions_same_fingerprint(project, tmp_path):
    before = fingerprint.fingerprint(project)
    save_project(project, tmp_path / "copie.dd.json")
    assert fingerprint.fingerprint(load_project(tmp_path / "copie.dd.json")) == before


def test_a_decision_changes_it(project):
    before = fingerprint.fingerprint(project)
    project.variable("age").sentinel_decisions = [SentinelDecision(code=999, missing=True)]
    after = fingerprint.fingerprint(project)
    assert after != before
    # The date of a decision is not a decision.
    project.variable("age").sentinel_decisions = [
        SentinelDecision(code=999, missing=True, updated_at=LATER)
    ]
    assert fingerprint.fingerprint(project) == after


def test_proposals_count_only_once_accepted(project):
    before = fingerprint.fingerprint(project)
    entry = project.variable("sommeil_q7")  # no label in the file
    proposed = TrackedValue[str](
        value="Écrans avant le coucher", origin="ai", status="proposed", ai_run="r1"
    )
    entry.label = proposed
    assert fingerprint.fingerprint(project) == before  # waiting: not a decision
    entry.label = proposed.model_copy(update={"status": "rejected", "updated_at": NOW})
    assert fingerprint.fingerprint(project) == before  # rejected: neither
    entry.label = validate(proposed, now=NOW)
    accepted = fingerprint.fingerprint(project)
    assert accepted != before
    entry.label = validate(proposed, now=LATER)
    assert fingerprint.fingerprint(project) == accepted  # when it was accepted: no matter


def test_statistics_and_settings_are_not_decisions(project):
    before = fingerprint.fingerprint(project)
    project.variable("age").profile.mean = 99.5
    project.settings.min_cell_count = 10
    project.ai_runs = []
    assert fingerprint.fingerprint(project) == before


def test_shown_in_the_exports(project):
    short = fingerprint.short(project)
    assert f"Empreinte du codebook : `{short}`" in render_markdown(project)
    assert f"Empreinte du codebook : {short}." in spss(project, "2026-10-15")
