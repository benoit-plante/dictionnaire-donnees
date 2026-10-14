"""v0.3, step 2: the home page — new project, open a project, recent projects, `ddict` alone."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import cli, recents
from ddict.project import load_project
from ddict.review.ui import dialog
from ddict.workflow import ProjectExists, profile_database, profile_summary

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")


@pytest.fixture
def base(fictional_files, tmp_path):
    path = tmp_path / "donnees" / "etude-sommeil.sav"
    path.parent.mkdir()
    shutil.copy(fictional_files["etude-sommeil.sav"], path)
    return path


# --- Without the interface. ---


def test_recent_projects(tmp_path):
    files = []
    for name in ("a", "b", "c"):
        path = tmp_path / f"{name}.dd.json"
        path.write_text("{}", encoding="utf-8")
        files.append(path)
        recents.add(path)
    recents.add(files[0])  # opened again: back on top, once
    assert [p.name for p in recents.load()] == ["a.dd.json", "c.dd.json", "b.dd.json"]
    files[2].unlink()  # a project moved or deleted is not listed
    assert [p.name for p in recents.load()] == ["a.dd.json", "b.dd.json"]
    saved = json.loads((recents.config_dir() / recents.FILE_NAME).read_text(encoding="utf-8"))
    assert all(isinstance(p, str) for p in saved)  # paths only
    recents.clear()
    assert recents.load() == []


def test_recent_projects_are_capped_and_survive_a_damaged_file(tmp_path):
    for index in range(recents.MAX_RECENTS + 3):
        path = tmp_path / f"p{index}.dd.json"
        path.write_text("{}", encoding="utf-8")
        recents.add(path)
    assert len(recents.load()) == recents.MAX_RECENTS
    (recents.config_dir() / recents.FILE_NAME).write_text("not json", encoding="utf-8")
    assert recents.load() == []


def test_profile_database(base):
    project, output = profile_database(base)
    assert output == base.with_name("etude-sommeil.dd.json") and output.is_file()
    assert profile_summary(project).startswith("34 variables, 200 lignes ; 4 variables sensibles")
    with pytest.raises(ProjectExists):
        profile_database(base)
    profile_database(base, replace=True)


def test_dialog_returns_the_chosen_path(monkeypatch):
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="C:/données/base.sav\n")

    monkeypatch.setattr(dialog.subprocess, "run", run)
    assert dialog.choose("database") == "C:/données/base.sav"
    assert calls[0][-3:] == ["-m", "ddict.review.ui.dialog", "database"]

    monkeypatch.setattr(
        dialog.subprocess, "run", lambda c, **k: subprocess.CompletedProcess(c, 0, stdout="")
    )
    assert dialog.choose("project") is None  # cancelled

    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, 1)

    monkeypatch.setattr(dialog.subprocess, "run", timeout)
    assert dialog.choose("questionnaire") is None
    with pytest.raises(ValueError):
        dialog.choose("anything")


def test_ddict_alone_opens_the_home_page(monkeypatch):
    launched = []
    monkeypatch.setattr(cli, "_launch", lambda path, port: launched.append((path, port)) or 0)
    assert cli.main([]) == 0
    assert cli.main(["--port", "8600"]) == 0
    assert launched == [(None, 8501), (None, 8600)]
    command, _env = cli.review_command(None, 8501)
    assert "--" not in command  # no project given to the interface


# --- In the interface. ---


@pytest.fixture
def home():
    test = AppTest.from_file(APP, default_timeout=30)
    test.session_state["project_path"] = ""  # no project: the home page
    test.run()
    assert not test.exception, test.exception
    return test


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_new_project_from_a_pasted_path(home, base):
    assert home.title[0].value == "Dictionnaire de données"
    home.text_input(key="home-database").input(f'"{base}"').run()  # quotes from Explorer
    home.button(key="home-create").click().run()
    assert not home.exception, home.exception
    assert base.with_name("etude-sommeil.dd.json").is_file()
    assert home.sidebar.title[0].value == "etude-sommeil.sav"  # the project is open
    assert [p.name for p in recents.load()] == ["etude-sommeil.dd.json"]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_existing_project_is_opened_not_replaced(home, base):
    _project, output = profile_database(base)
    before = output.read_text(encoding="utf-8")
    home.text_input(key="home-database").input(str(base)).run()
    home.button(key="home-create").click().run()
    assert any("existe déjà" in e.value for e in home.error)
    assert output.read_text(encoding="utf-8") == before
    home.button(key="home-open-existing").click().run()
    assert home.sidebar.title[0].value == "etude-sommeil.sav"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_problems_are_explained(home, tmp_path):
    home.button(key="home-create").click().run()
    assert "Choisissez d'abord une base" in home.error[0].value
    broken = tmp_path / "abime.sav"
    broken.write_bytes(b"not a database")
    home.text_input(key="home-database").input(str(broken)).run()
    home.button(key="home-create").click().run()
    assert "Impossible de lire la base" in home.error[0].value
    home.text_input(key="home-project").input(str(tmp_path / "absent.dd.json")).run()
    home.button(key="home-open").click().run()
    assert "introuvable" in home.error[0].value


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_browse_fills_the_field(home, base, monkeypatch):
    monkeypatch.setattr(dialog, "choose", lambda kind: str(base))
    home.button(key="browse-home-database").click().run()
    assert home.text_input(key="home-database").value == str(base)
    monkeypatch.setattr(dialog, "choose", lambda kind: None)
    home.button(key="browse-home-project").click().run()
    assert "Aucun fichier choisi" in home.error[0].value


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_recent_projects_and_back_home(home, base):
    _project, output = profile_database(base)
    recents.add(output)
    home.run()
    home.button(key="home-recent-0").click().run()
    assert home.sidebar.title[0].value == "etude-sommeil.sav"
    home.sidebar.button(key="home").click().run()  # "Accueil"
    assert home.title[0].value == "Dictionnaire de données"
    home.button(key="home-clear").click().run()
    assert recents.load() == []
    assert load_project(output).source.name == "etude-sommeil.sav"  # nothing else touched
