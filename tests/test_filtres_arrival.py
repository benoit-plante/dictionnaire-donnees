"""v0.21, step 8 (§ 5.8.1 to 5.8.3 of the plan): the database of a filtered questionnaire
arrives; for each variable with a condition, how many were asked it, how many not (not
applicable), how many left it empty, how many answered under a false condition; the
conformity report says them, counts only, a small count "< 5". Nothing real: the base of
`scripts/generer_base_filtres.py`, compared to its answer key."""

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import arrival
from ddict.io.load import read_database
from ddict.project import load_project, save_project, skip

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
KEY = json.loads((EXAMPLES / "corrige-filtres.json").read_text(encoding="utf-8"))


def _generator():
    script = ROOT / "scripts" / "generer_base_filtres.py"
    spec = importlib.util.spec_from_file_location("generer_base_filtres", script)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return _generator()


def test_the_generator_writes_the_same_files(tmp_path, generator):
    for written in generator.write_all(tmp_path):
        assert written.read_bytes() == (EXAMPLES / written.name).read_bytes(), written.name


@pytest.mark.parametrize("suffix", [".sav", ".csv"])
def test_the_counts_are_those_of_the_answer_key(generator, suffix):
    project = generator.project()
    base = EXAMPLES / f"reponses-filtres{suffix}"
    found = arrival.receive(project, base)
    assert (found.absent, found.extra) == ([], [])
    counts = skip.counts(project, read_database(base).table)
    assert {n: c.__dict__ for n, c in counts.items()} == KEY["variables"]
    assert found.anomalies == {"nbenfants": 3, **{f"climat_SQ{k:03d}": 7 for k in range(1, 8)}}


def test_the_planted_cases(generator):
    variables = KEY["variables"]
    assert variables["nbenfants"] == {
        "asked": 160, "not_applicable": 137, "missing": 5, "anomalies": 3,
    }  # fmt: skip
    # Not applicable: 10 refusals, 120 "Non", 6 empty, 4 "9", minus the 3 anomalies.
    assert variables["climat_SQ004"]["missing"] == 6
    assert variables["nuit"]["asked"] == 146  # 150 full time, 4 under 18
    assert variables["transport_SQ001"]["missing"] == 5  # nothing ticked
    assert variables["age"]["not_applicable"] == 10


def test_the_report_says_counts_only(generator):
    project = generator.project()
    base = EXAMPLES / "reponses-filtres.sav"
    found = arrival.receive(project, base)
    text = arrival.report_markdown(project, found)
    assert "## Questions filtrées" in text
    assert "| `nbenfants` | 160 | 137 | 5 |" in text
    assert "| `climat_SQ007` | 210 | 83 | < 5 |" in text  # 2 left the check empty
    assert "## Réponses sous une condition fausse" in text
    assert "- `nbenfants` : < 5" in text and "- `climat_SQ001` : 7" in text
    # Never a person, a line or a value.
    for witness in ("Commentaire fictif", "Moyen fictif", "2026-11-02", "respondent"):
        assert witness not in text
    assert "Base lue. Conformité au questionnaire — variables avec des réponses" in (
        arrival.summary_text(found)
    )


def test_the_conditions_are_kept_at_arrival(generator):
    project = generator.project()
    planned = {e.name: e.asked_if for e in project.variables}
    arrival.receive(project, EXAMPLES / "reponses-filtres.sav")
    for entry in project.variables:
        if entry.name in planned:
            assert entry.asked_if == planned[entry.name]
    assert project.variable("nuit").asked_if.value[-1].terms[0].target == "age"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_page_base_shows_the_counts(tmp_path, generator):
    folder = tmp_path / "Familles"
    folder.mkdir()
    shutil.copy(EXAMPLES / "reponses-filtres.sav", folder / "reponses-filtres.sav")
    project = generator.project()
    arrival.receive(project, folder / "reponses-filtres.sav")
    path = folder / "familles.dd.json"
    save_project(project, path)
    app = AppTest.from_file(str(ROOT / "src" / "ddict" / "review" / "app.py"), default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "base"
    app.run()
    assert not app.exception, app.exception
    text = "\n".join(m.value for m in app.markdown)
    assert "| `nbenfants` | 160 | 137 | 5 |" in text
    assert load_project(path).variable("nbenfants").asked_if is not None
