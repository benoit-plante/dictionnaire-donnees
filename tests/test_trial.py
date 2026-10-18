"""v0.16, step A7 (finding 16, D-125): the home page begins with the recent projects, and
offers to try the tool on the fictional database, copied into a working folder."""

import os
import shutil
import tomllib
from datetime import datetime
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import recents
from ddict.project import load_project, save_project
from ddict.review import trial
from ddict.workflow import profile_database

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")


@pytest.fixture
def where(tmp_path, monkeypatch):
    monkeypatch.setenv("DDICT_CONFIG_DIR", str(tmp_path / "config"))
    folder = tmp_path / "Documents" / trial.FOLDER
    monkeypatch.setenv("DDICT_TRIAL_DIR", str(folder))
    return folder


def _home() -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = ""
    app.run()
    assert not app.exception, app.exception
    return app


def test_the_trial_is_made_once_then_opened_again(where):
    path = trial.start()
    assert path == where / "etude-sommeil.dd.json"
    assert sorted(p.name for p in where.iterdir()) == [
        "etude-sommeil.dd.json", "etude-sommeil.sav", "questionnaire-sommeil.pdf"
    ]  # fmt: skip
    project = load_project(path)
    assert len(project.variables) == 34 and project.questionnaire is not None
    (where / "etude-sommeil-notes.txt").write_text("à garder", encoding="utf-8")
    project.dataset.description = "Décision de l'essai."
    save_project(project, path)
    assert trial.start() == path  # opened again, decisions kept
    assert load_project(path).dataset.description == "Décision de l'essai."
    trial.start(again=True)  # made anew: its decisions are lost, other files are kept
    assert load_project(path).dataset.description is None
    assert (where / "etude-sommeil-notes.txt").is_file()


def test_the_documents_folder():
    found = trial.documents()
    assert found.is_absolute()
    if os.name == "nt":
        assert found.is_dir()


def test_the_database_is_in_the_installed_package():
    """The installed tool has no examples folder: the trial's files are in its package."""
    with (ROOT / "pyproject.toml").open("rb") as stream:
        included = tomllib.load(stream)["tool"]["hatch"]["build"]["targets"]["wheel"][
            "force-include"
        ]
    for name in (trial.DATABASE, trial.QUESTIONNAIRE):
        assert included[f"exemples/bases-fictives/{name}"] == f"ddict/banc/{name}"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_try_from_the_home_page(where):
    app = _home()
    button = app.button(key="home-trial")
    assert button.label == "Essayer avec la base fictive"
    assert any(str(where) in m.value for m in app.markdown)
    button.click().run()
    assert not app.exception, app.exception
    assert app.sidebar.title[0].value == "etude-sommeil.sav"  # the project is open
    again = _home()
    assert again.button(key="home-trial").label == "Reprendre l'essai"
    assert again.button(key="home-trial-again").disabled  # until the box is ticked
    again.checkbox(key="home-trial-sure").check().run()
    again.button(key="home-trial-again").click().run()
    assert again.sidebar.title[0].value == "etude-sommeil.sav"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_recent_projects_come_first(where, tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.sav", tmp_path / "etude-sommeil.sav")
    _project, output = profile_database(tmp_path / "etude-sommeil.sav")
    recents.add(output)
    app = _home()
    headers = [h.value for h in app.header]
    assert headers[:2] == ["Projets récents", "Essayer l'outil"]
    assert headers.index("Projets récents") < headers.index("Nouveau projet")
    texts = [m.value for m in app.markdown]
    assert str(output.parent) in texts
    modified = datetime.fromtimestamp(output.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    assert modified in texts


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_no_recent_project_no_empty_section(where):
    app = _home()
    assert "Projets récents" not in [h.value for h in app.header]
    assert app.header[0].value == "Essayer l'outil"
