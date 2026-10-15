"""v0.7, step 9: the "Names" page, the prefix of a group, the dashboard (D-048 to D-053)."""

import json
import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import naming
from ddict.io import read_database
from ddict.project import build_project, load_project
from ddict.review import names
from ddict.review.logic import ReviewError
from ddict.workflow import add_questionnaire, profile_database, tasks

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")
KEY = json.loads((EXAMPLES / "corrige-surveymonkey.json").read_text(encoding="utf-8"))
NOW = "2026-10-15T12:00:00"
BASE = "travail-t2_surveymonkey.sav"


@pytest.fixture
def project():
    return build_project(read_database(EXAMPLES / BASE))


def _texts(found):
    return [t.text.format(n=t.count) for t in found]


# --- Without the interface. ---


def test_the_table_of_names_and_its_filters(project):
    assert len(names.rows(project, "to_name")) == 55  # nothing proposed yet
    names.propose(project)
    assert len(names.rows(project, "proposed")) == 37
    assert len(names.rows(project, "to_name")) == 18
    row = next(r for r in names.rows(project) if r.name == "q0008_0001")
    assert (row.new_name, row.origin, row.status) == (
        "consignes_securite_1",
        "règle de nommage",
        "proposé",
    )
    assert row.question == "" and row.label  # no questionnaire yet
    add_questionnaire(project, EXAMPLES / "travail-t2_surveymonkey.xlsx")
    row = next(r for r in names.rows(project) if r.name == "q0008_0001")
    assert row.question.startswith("Q8.o1 : Cochez les consignes")  # its sure link
    names.decide(project, "q0001", "accept", now=NOW)
    assert [r.name for r in names.rows(project, "decided")] == ["q0001"]


def test_corrections_in_the_table(project):
    names.propose(project)
    changed = names.apply_edits(
        project, {"q0001": "domaine", "q0002": "", "q0006": "formation_sst"}, now=NOW
    )
    assert changed == 3
    assert project.variable("q0001").new_name.status == "corrected"
    assert project.variable("q0002").new_name.value is None  # withdrawn: original name
    assert project.variable("q0006").new_name.value == "formation_sst"
    assert names.apply_edits(project, {"q0001": "domaine"}, now=NOW) == 0  # unchanged
    with pytest.raises(ReviewError, match=r"q0007 : nom refusé \(déjà le nom"):
        names.apply_edits(project, {"q0007": "domaine"}, now=NOW)
    with pytest.raises(ReviewError, match="minuscules"):
        names.apply_edits(project, {"q0007": "Pauses"}, now=NOW)


def test_grouped_decisions_by_group_or_question(project):
    names.propose(project)
    scopes = names.scopes(project)
    group = next(g for g in project.groups if "q0005_0001" in g.members.value)
    assert scopes[group.group_id][-1] == "q0005_other"  # its "other" text with it
    assert scopes["q0001"] == ["q0001"]
    assert "respondent_id" in scopes["*"]
    assert names.scope_text(project, "q0001") == "Question q0001 (secteur)"
    names.accept_names(project, scopes[group.group_id], now=NOW)
    assert all(project.variable(n).new_name.status == "validated" for n in scopes[group.group_id])
    assert group.group_id not in names.scopes(project)
    with pytest.raises(ReviewError, match="n'attendent plus"):
        names.accept_names(project, ["q0005_0001"], now=NOW)
    with pytest.raises(ReviewError, match="Aucune variable cochée"):
        names.accept_names(project, [], now=NOW)


def test_the_prefix_of_a_group(project):
    names.set_group_prefix(project, "G1", "eft", now=NOW)
    assert project.variable("q0003_0004").new_name.value == "eft_4"
    with pytest.raises(ReviewError, match="Préfixe refusé"):
        names.set_group_prefix(project, "G1", "EFT 1", now=NOW)
    with pytest.raises(ReviewError, match="Aucun préfixe proposé"):
        names.accept_group_prefix(project, "G1", now=NOW)


def test_stems_and_settings(project):
    names.propose(project)
    rows = {key: stem for key, _text, stem, _status in names.stem_rows(project)}
    assert rows["q0005"] == "taches_semaine"
    assert names.apply_stems(project, {"q0005": "taches", "q0001": ""}, now=NOW) == 1
    assert project.variable("q0005_0002").new_name.value == "taches_2"
    with pytest.raises(ReviewError, match="radical refusé"):
        names.apply_stems(project, {"q0005": "Tâches"}, now=NOW)
    names.set_settings(project, "t2", "prefix", 32)
    assert project.variable("q0005_0002").new_name.value == "t2_taches_2"
    with pytest.raises(ReviewError, match="Marque de vague invalide"):
        names.set_settings(project, "2t", "suffix", 32)  # a mark starts with a letter
    with pytest.raises(ReviewError, match="entre 8 et 64"):
        names.set_settings(project, "t2", "suffix", 4)


def test_an_earlier_wave_that_cannot_be_read(project, tmp_path):
    bad = tmp_path / "rien.csv"
    bad.write_text("a,b\n", encoding="utf-8")
    with pytest.raises(ReviewError, match="Impossible de lire la vague précédente"):
        names.take_earlier_wave(project, bad)


def test_the_dashboard(project):
    assert not any("Noms" in t or "préfixe" in t for t in _texts(tasks(project)))
    names.propose(project)  # renaming begun
    found = _texts(tasks(project))
    assert "Grilles sans préfixe de noms : 2" in found
    assert "Noms proposés à valider : 37" in found
    # In the recommended order: before the labels, after the value labels.
    names.set_group_prefix(project, "G1", "eft", now=NOW)
    names.set_group_prefix(project, "G2", "milieu", now=NOW)
    assert "Grilles sans préfixe de noms : 2" not in _texts(tasks(project))


# --- In the interface. ---


@pytest.fixture
def project_path(tmp_path):
    shutil.copy(EXAMPLES / BASE, tmp_path / BASE)
    _project, path = profile_database(tmp_path / BASE)
    return path


def _app(path: Path, mode: str) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=30)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = mode
    app.run()
    assert not app.exception, app.exception
    return app


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_names_page(project_path):
    app = _app(project_path, "names")
    assert app.header[0].value == "Noms des variables"
    app.text_input(key="names-wave").input("t2")
    app.button(key="names-settings-save").click().run()
    assert not app.exception, app.exception
    project = load_project(project_path)
    assert project.settings.naming.wave == "t2"
    assert project.variable("q0001").new_name.value == "secteur_t2"
    assert any("37 noms proposés" in m.value for m in app.markdown)

    # Grouped decision: the list is shown first, then accepted.
    app.selectbox(key="bulk-names-scope").select("q0001").run()
    app.button(key="bulk-names-open").click().run()
    assert any("secteur_t2" in box.label for box in app.checkbox)
    app.button(key="bulk-names-accept").click().run()
    assert not app.exception, app.exception
    assert load_project(project_path).variable("q0001").new_name.status == "validated"

    # One variable, rejected.
    app.radio(key="names-filter").set_value("proposed").run()
    app.selectbox(key="names-chosen").select("q0007").run()
    app.button(key="names-reject").click().run()
    assert load_project(project_path).variable("q0007").new_name.status == "rejected"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_prefix_in_the_groups_view(project_path):
    app = _app(project_path, "groups")
    app.text_input(key="prefix-G1").input("eft")
    app.button(key="save-prefix-G1").click().run()
    assert not app.exception, app.exception
    project = load_project(project_path)
    assert project.groups[0].name_prefix.value == "eft"
    assert project.variable("q0003_0012").new_name.value == "eft_12"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_dashboard_leads_to_the_proposed_names(project_path):
    project = load_project(project_path)
    naming.propose(project)
    from ddict.project import save_project

    save_project(project, project_path)
    app = _app(project_path, "base")
    labels = [b.label for b in app.sidebar.button if b.key and b.key.startswith("task-")]
    index = labels.index("Noms proposés à valider : 37")
    app.sidebar.button(key=f"task-{index}").click().run()
    assert app.header[0].value == "Noms des variables"
    assert app.radio(key="names-filter").value == "proposed"
