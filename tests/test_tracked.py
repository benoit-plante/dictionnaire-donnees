"""v0.17, step A1 (D-131): the projects followed, kept on this computer — paths only, written
the same way every time, never resolved; a new project is followed;
"Suivre ce projet" on a recent project and in the sidebar, "Ne plus suivre" touches no
project file. On the fictional sleep study."""

import json
import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import recents, tracked
from ddict.cli import main
from ddict.workflow import profile_database

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")


@pytest.fixture
def base(tmp_path):
    folder = tmp_path / "Études 2026" / "Vague 2"
    folder.mkdir(parents=True)
    path = folder / "etude-sommeil.sav"
    shutil.copy(EXAMPLES / "etude-sommeil.sav", path)
    return path


def _list_file() -> Path:
    return recents.config_dir() / tracked.FILE_NAME


def _home() -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = ""
    app.run()
    assert not app.exception, app.exception
    return app


# --- The list. ---


def test_the_list_is_written_the_same_way(tmp_path):
    first, second = tmp_path / "b.dd.json", tmp_path / "A.dd.json"
    tracked.follow(first)
    tracked.follow(second)
    written = _list_file().read_bytes()
    _list_file().unlink()
    tracked.follow(second)
    tracked.follow(first)
    assert _list_file().read_bytes() == written
    assert b"\r\n" not in written
    assert json.loads(written) == {"format": 1, "projets": [str(second), str(first)]}


def test_accents_spaces_and_a_project_not_found(tmp_path):
    path = tmp_path / "Études 2026" / "Équipe Côté" / "étude été.dd.json"  # never created
    assert tracked.follow(path)
    assert tracked.load() == [path]
    assert tracked.is_followed(path)
    assert "Études 2026" in _list_file().read_text(encoding="utf-8")  # not \u00c9


def test_a_network_drive_is_kept_as_given():
    path = Path("Z:\\Équipe\\etude.dd.json")
    tracked.follow(path)
    assert json.loads(_list_file().read_text(encoding="utf-8"))["projets"] == [str(path)]


def test_one_line_per_project_whatever_the_case(tmp_path):
    path = tmp_path / "Etude.dd.json"
    tracked.follow(path)
    assert tracked.follow(Path(str(path).upper()))
    assert len(tracked.load()) == 1
    assert tracked.is_followed(Path(str(path).lower()))


def test_no_longer_followed_touches_no_file(base):
    _project, path = profile_database(base)
    recents.add(path)
    tracked.follow(path)
    before, stat = path.read_bytes(), path.stat()
    assert tracked.unfollow(path)
    assert tracked.load() == []
    assert path.read_bytes() == before and path.stat().st_mtime_ns == stat.st_mtime_ns
    assert recents.load() == [path.resolve()]
    assert tracked.unfollow(path)  # not followed: nothing to do


def test_a_damaged_list_is_never_overwritten(tmp_path):
    _list_file().parent.mkdir(parents=True, exist_ok=True)
    _list_file().write_text("{ coupé", encoding="utf-8")
    assert not tracked.follow(tmp_path / "etude.dd.json")
    assert not tracked.unfollow(tmp_path / "etude.dd.json")
    assert _list_file().read_text(encoding="utf-8") == "{ coupé"
    assert tracked.load() == []


def test_a_list_that_cannot_be_written_is_no_error(tmp_path, monkeypatch):
    blocked = tmp_path / "config"
    blocked.write_text("un fichier, pas un dossier", encoding="utf-8")
    monkeypatch.setenv("DDICT_CONFIG_DIR", str(blocked / "ddict"))
    assert not tracked.follow(tmp_path / "etude.dd.json")


# --- What is followed. ---


def test_ddict_profiler_follows_the_new_project(base):
    assert main(["profiler", str(base)]) == 0
    assert tracked.load() == [base.with_name("etude-sommeil.dd.json")]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_new_project_is_followed_then_no_longer(base):
    app = _home()
    app.text_input(key="home-database").input(str(base)).run()
    app.button(key="home-create").click().run()
    assert not app.exception, app.exception
    path = base.with_name("etude-sommeil.dd.json")
    assert tracked.load() == [path]
    assert app.button(key="follow-project").label == "Ne plus suivre"
    before = path.read_bytes()
    app.button(key="follow-project").click().run()
    assert tracked.load() == []
    assert path.read_bytes() == before
    assert app.button(key="follow-project").label == "Suivre ce projet"
    app.button(key="follow-project").click().run()
    assert tracked.load() == [path]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_follow_a_recent_project(base):
    _project, path = profile_database(base)
    recents.add(path)
    app = _home()
    app.button(key="home-follow-0").click().run()
    assert not app.exception, app.exception
    assert tracked.load() == [path]
    assert any("maintenant suivi" in s.value for s in app.success)
    assert not [b for b in app.button if b.key == "home-follow-0"]  # now in "Mes projets"
