"""v0.17, step A3 (D-132): look for projects in a folder — down to 4 levels, hidden, system
and program folders passed over, links and junctions never followed, limits said, no file
opened; on the home page, nothing checked at first, only the checked ones followed."""

import _winapi
import builtins
import ctypes
import os
import stat
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from accueil import tab
from ddict import tracked
from ddict.review.ui import dialog

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")


def _file(path: Path, text: str = "{}") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _attribute(path: Path, attribute: int) -> None:
    assert ctypes.windll.kernel32.SetFileAttributesW(str(path), attribute)


@pytest.fixture
def tree(tmp_path):
    """A folder with projects where they are looked for, and where they are not."""
    root = tmp_path / "Recherche"
    found = [
        _file(root / "a.dd.json"),
        _file(root / "ÉTUDE B.DD.JSON"),
        _file(root / "Études 2026" / "Vague 2" / "etude-sommeil.dd.json"),
        _file(root / "1" / "2" / "3" / "4" / "profond.dd.json"),
        _file(root / "abime.dd.json", "\x00 pas un projet"),  # listed: never opened
    ]
    for passed in (
        root / "1" / "2" / "3" / "4" / "5" / "trop-profond.dd.json",
        root / ".git" / "x.dd.json",
        root / "$RECYCLE.BIN" / "x.dd.json",
        root / "AppData" / "x.dd.json",
        root / "node_modules" / "x.dd.json",
        root / "etude.dd-envois" / "x.dd.json",
        root / "Caché" / "x.dd.json",
        root / "Système" / "x.dd.json",
        root / "a.dd.json.tmp",
        root / "notes.json",
    ):
        _file(passed)
    _attribute(root / "Caché", stat.FILE_ATTRIBUTE_HIDDEN)
    _attribute(root / "Système", stat.FILE_ATTRIBUTE_SYSTEM)
    elsewhere = _file(tmp_path / "Ailleurs" / "y.dd.json")
    _winapi.CreateJunction(str(elsewhere.parent), str(root / "Jonction"))
    _winapi.CreateJunction(str(root), str(root / "Boucle"))  # as "Ma musique" in Documents
    return root, sorted(found, key=lambda p: str(p).casefold())


def test_what_is_found_and_what_is_passed_over(tree):
    root, found = tree
    result = tracked.search(root)
    assert result.found == found
    assert result.stopped is None


def test_no_file_is_opened(tree, monkeypatch):
    root, found = tree

    def opened(*args, **kwargs):
        raise AssertionError("a file was opened")

    monkeypatch.setattr(builtins, "open", opened)
    assert tracked.search(root).found == found


def test_a_folder_that_cannot_be_read_is_passed_over(tree, monkeypatch):
    root, found = tree
    real = os.scandir

    def scandir(path):
        if Path(path).name == "Études 2026":
            raise PermissionError(5, "Access is denied")
        return real(path)

    monkeypatch.setattr(os, "scandir", scandir)
    assert tracked.search(root).found == [p for p in found if "Études 2026" not in str(p)]


def test_the_limits_are_said(tree, monkeypatch):
    root, _found = tree
    monkeypatch.setattr(tracked, "MAX_FOLDERS", 2)
    assert tracked.search(root).stopped == "folders"
    monkeypatch.setattr(tracked, "MAX_FOLDERS", 20_000)
    monkeypatch.setattr(tracked, "MAX_PROJECTS", 2)
    result = tracked.search(root)
    assert result.stopped == "projects" and len(result.found) == 2


def test_several_followed_at_once(tmp_path):
    first, second = tmp_path / "a.dd.json", tmp_path / "b.dd.json"
    tracked.follow(first)
    assert tracked.follow_all([first, second])
    assert tracked.load() == [first, second]


# --- On the home page. ---


def _home(monkeypatch, chosen) -> AppTest:
    monkeypatch.setattr(dialog, "choose", lambda kind: None if chosen is None else str(chosen))
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = ""
    tab(app, "ouvrir")  # D-160: under "Ouvrir un projet"
    app.button(key="home-search").click().run()
    assert not app.exception, app.exception
    return app


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_nothing_checked_then_only_the_checked_followed(tree, monkeypatch):
    root, found = tree
    tracked.follow(found[0])
    app = _home(monkeypatch, root)
    boxes = [b for b in app.checkbox if b.key.startswith("home-found-")]
    assert len(boxes) == len(found) - 1 and not any(b.value for b in boxes)
    already = [b for b in app.checkbox if b.key.startswith("home-followed-")]
    assert len(already) == 1 and already[0].value and already[0].disabled
    assert "(déjà suivi)" in already[0].label
    assert app.button(key="home-follow-found").disabled
    boxes[0].check().run()
    boxes[2].check().run()
    assert app.button(key="home-follow-found").label == "Suivre ces 2 projets"
    app.button(key="home-follow-found").click().run()
    assert not app.exception, app.exception
    assert tracked.load() == sorted([found[0], found[1], found[3]], key=lambda p: str(p).casefold())
    assert any(s.value == "2 projets suivis." for s in app.success)
    assert not [b for b in app.checkbox if b.key.startswith("home-found-")]  # closed


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_limit_said_on_the_home_page(tree, monkeypatch):
    monkeypatch.setattr(tracked, "MAX_FOLDERS", 2)
    app = _home(monkeypatch, tree[0])
    assert any("Recherche arrêtée après 20 000 dossiers" in w.value for w in app.warning)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_no_folder_chosen(monkeypatch):
    app = _home(monkeypatch, None)
    assert any(e.value == "Aucun dossier choisi." for e in app.error)
    assert tracked.load() == []
