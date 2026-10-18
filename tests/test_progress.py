"""v0.16, step B2 (findings 2 and 3): the progress bar says how far the codebook is
documented, and the dashboard goes on past the labels: the plan to freeze, the notebook's
numbers to confirm, the Method's holes, the draft to check."""

import os
import shutil
import time
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.analysis import notebook as nb
from ddict.cli import main
from ddict.project import load_project, save_project
from ddict.project.model import Frozen
from ddict.review import logic, navigation
from ddict.workflow import NotebookState, Task, profile_database, tasks
from test_notebook_page import _build_by_command, _confirm_999, _folder, _sleep
from test_plan_page import COMMANDS, _plan

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")


def _open(path: Path, mode: str = "export") -> AppTest:
    app = AppTest.from_file(APP, default_timeout=120)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = mode
    app.run()
    assert not app.exception, app.exception
    return app


def _dashboard(app: AppTest) -> list[str]:
    return [b.label for b in app.sidebar.button if b.key and b.key.startswith("task-")]


# --- The progress of the codebook. ---


def test_a_new_project_is_far_from_documented(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.sav", tmp_path / "etude-sommeil.sav")
    project, _path = profile_database(tmp_path / "etude-sommeil.sav")
    share = logic.codebook_progress(project)
    assert 0.4 < share < 0.7  # the file's labels count, the rest is still to do
    old_done, old_total = logic.progress(project)
    assert old_done == old_total  # what the old bar said: full


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_bar_says_the_codebook(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.sav", tmp_path / "etude-sommeil.sav")
    _project, path = profile_database(tmp_path / "etude-sommeil.sav")
    app = _open(path)
    share = logic.codebook_progress(load_project(path))
    text = f"Codebook documenté à {round(100 * share)} %"
    assert app.sidebar.get("progress")[0].proto.text == text
    project = load_project(path)
    project.dataset.unit_of_observation = "participant"
    save_project(project, path)
    assert logic.codebook_progress(load_project(path)) > share  # a decision moves it


# --- The dashboard past the labels. ---


def test_without_its_path_the_dashboard_is_as_before(tmp_path, capsys):
    path = _folder(tmp_path)
    _build_by_command(path)
    capsys.readouterr()
    project = load_project(path)
    before = tasks(project)
    after = tasks(project, path)
    assert after[: len(before)] == before  # the old tasks, first and unchanged
    assert [t.text for t in after[len(before) :]] == [
        "Trous de la Méthode à combler (groupes) : {n}"
    ]


def test_the_plan_to_freeze(tmp_path, capsys):
    path = _folder(tmp_path)
    for arguments in COMMANDS:
        assert _plan(path, *arguments) == 0
    capsys.readouterr()
    project = load_project(path)
    assert Task(1, "Plan à figer", "plan") in tasks(project)
    project.plan.frozen = Frozen(date="2026-10-18", fingerprint="0" * 64)
    assert all(t.mode != "plan" for t in tasks(project))


def test_the_notebook_numbers_to_confirm(tmp_path):
    project = load_project(_folder(tmp_path))
    found = tasks(project, None, NotebookState(to_confirm=2, impossible=1))
    assert found[-2:] == [
        Task(2, "Chiffres à confirmer au carnet : {n}", "notebook"),
        Task(1, "Analyses impossibles à calculer : {n}", "notebook"),
    ]


def test_the_draft_to_check(tmp_path, capsys):
    path = _folder(tmp_path)
    _build_by_command(path)
    assert main(["article", str(path)]) == 0
    capsys.readouterr()
    draft = path.with_name("etude-analyses-article.docx")
    assert Task(1, "Vérifier les chiffres de l'ébauche", "verify") in tasks(
        load_project(path), path
    )
    assert main(["verifier", str(path), str(draft)]) in (0, 1)
    capsys.readouterr()
    assert all(t.mode != "verify" for t in tasks(load_project(path), path))
    later = time.time() + 5  # the draft written again after its check
    os.utime(draft, (later, later))
    assert any(t.mode == "verify" for t in tasks(load_project(path), path))


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_change_to_confirm_shows_in_the_sidebar(tmp_path):
    path = _sleep(tmp_path)
    assert main(["carnet", "ajouter", str(path), "correlation", "--variables", "age",
                 "heures_sommeil"]) == 0  # fmt: skip
    app = _open(path)
    assert not any(label.startswith("Chiffres à confirmer") for label in _dashboard(app))
    _confirm_999(path)  # a decision that changes A1's numbers
    app = _open(path)
    assert "Chiffres à confirmer au carnet : 1" in _dashboard(app)
    titles = [info["page_name"] for info in app._registered_pages.values()]
    assert "Carnet (1)" in titles
    next(b for b in app.sidebar.button if b.label.startswith("Chiffres")).click().run()
    assert app.header[0].value == "Carnet"
    assert nb.load_notebook(nb.notebook_path(path)).entries[0].pending is not None


def test_the_states_follow_the_new_tasks():
    counts = navigation.waiting([Task(1, "", "plan"), Task(2, "", "notebook")])
    assert counts == {"plan": 1, "notebook": 2}
