"""v0.7, step 9: the "Names" page, the prefix of a group, the dashboard (D-048 to D-053)."""

import json
import shutil
from pathlib import Path

import httpx
import pytest
from streamlit.testing.v1 import AppTest

from ddict import naming
from ddict.io import read_database
from ddict.project import build_project, load_project, save_project
from ddict.review import names
from ddict.review.logic import ReviewError
from ddict.workflow import add_questionnaire, profile_database, tasks
from fake_ai import serve_commands

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
        "règle",
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


def test_decisions_in_the_table(project):
    """v0.7.1 (D-056): accept or reject on a row, next to written names."""
    names.propose(project)
    waiting = {r.name for r in names.rows(project) if r.waiting}
    assert "q0001" in waiting
    assert not waiting & {r.name for r in names.rows(project, "to_name")}
    done = names.apply_table(
        project,
        {"q0001": "domaine"},
        {"q0001": "accept", "q0006": "accept", "q0007": "reject", "q0002": ""},
        now=NOW,
    )
    assert done == 3
    assert project.variable("q0001").new_name.status == "corrected"  # the written name
    assert project.variable("q0006").new_name.status == "validated"
    assert project.variable("q0007").new_name.status == "rejected"
    # Nothing changes when one row is wrong.
    before = project.variable("q0008_0001").new_name.status
    with pytest.raises(ReviewError, match="n'attendent plus de décision : q0006"):
        names.apply_table(project, {}, {"q0008_0001": "accept", "q0006": "accept"}, now=NOW)
    assert project.variable("q0008_0001").new_name.status == before
    with pytest.raises(ReviewError, match="nom modifié et « Rejeter »"):
        names.apply_table(project, {"q0008_0002": "consignes_2"}, {"q0008_0002": "reject"}, now=NOW)


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
    with pytest.raises(ReviewError, match="nom de base refusé"):
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

    # In the table: "Accept" filled in for the proposed names, read, then saved.
    app.radio(key="names-filter").set_value("proposed").run()
    assert not app.exception, app.exception
    app.button(key="names-prefill").click().run()
    assert not app.exception, app.exception
    assert load_project(project_path).variable("q0001").new_name.status == "proposed"  # not yet
    app.button(key="names-table-save").click().run()
    assert not app.exception, app.exception
    project = load_project(project_path)
    assert project.variable("q0001").new_name.status == "validated"
    assert not names.rows(project, "proposed")
    assert any("37 noms enregistrés" in s.value for s in app.success)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_prefix_in_the_groups_view(project_path):
    app = _app(project_path, "groups")
    app.text_input(key="prefix-G1").input("eft")
    app.button(key="save-items-G1").click().run()
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


def _stems_server(requests):
    """The fake server answers each question with the answer key's stem."""
    stems = KEY["waves"]["t2"]["stems"]

    def answer(request):
        requests.append(request)
        content = json.loads(json.loads(request.content)["messages"][1]["content"])
        questions = [
            {"key": q["key"], "stem": stems.get(q["key"], "")} for q in content["questions"]
        ]
        text = json.dumps({"block": content["block"], "questions": questions})
        return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})

    return answer


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_ai_proposes_stems_on_the_names_page(project_path, monkeypatch):
    """v0.18 (D-141): offered in the interface since the bench, only for a project that
    allows it; each stem stays a proposal."""
    requests = []
    serve_commands(monkeypatch, _stems_server(requests))
    project = load_project(project_path)
    add_questionnaire(project, EXAMPLES / "travail-t2_surveymonkey.xlsx")
    save_project(project, project_path)
    app = _app(project_path, "names")
    assert app.button(key="names-ai-stems").disabled  # the project does not allow it
    app.checkbox(key="ai-allowed").check().run()
    app.button(key="names-ai-stems").click().run()
    assert not app.exception, app.exception
    assert requests
    assert any("blocs réussis, 0 en échec" in s.value for s in app.success)
    found = naming.stem(load_project(project_path), "q0005")
    assert found.stem.origin == "ai" and found.stem.status == "proposed"
    assert found.stem.value == "taches"
