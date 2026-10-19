"""v0.17, step A2 (D-131): a followed project moved elsewhere stays in the table, "not
found"; "Le retrouver…" puts its new path in its place, and its row comes back complete;
"Ne plus suivre" takes it off. On the fictional sleep study."""

import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import overview, tracked
from ddict.review.ui import dialog
from ddict.workflow import profile_database

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")


@pytest.fixture
def moved(tmp_path):
    """A followed project, then its folder moved: (old path, new path)."""
    folder = tmp_path / "Études 2026" / "Vague 2"
    folder.mkdir(parents=True)
    shutil.copy(EXAMPLES / "etude-sommeil.sav", folder / "etude-sommeil.sav")
    _project, path = profile_database(folder / "etude-sommeil.sav")
    tracked.follow(path)
    overview.clear_cache()
    shutil.move(folder, tmp_path / "Archives Vague 2")
    return path, tmp_path / "Archives Vague 2" / path.name


def _home() -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = ""
    app.run()
    assert not app.exception, app.exception
    return app


def _choose(monkeypatch, chosen):
    monkeypatch.setattr(dialog, "choose", lambda kind: None if chosen is None else str(chosen))


def test_replace_in_the_list(tmp_path):
    old, new, other = (tmp_path / f"{n}.dd.json" for n in ("a", "b", "c"))
    tracked.follow(old)
    tracked.follow(other)
    assert tracked.replace(old, new)
    assert tracked.load() == [new, other]
    tracked.follow(old)
    assert tracked.replace(old, other)  # already followed: one line
    assert tracked.load() == [new, other]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_moved_then_found_again(moved, monkeypatch):
    old, new = moved
    app = _home()
    texts = [m.value for m in app.markdown]
    assert "Introuvable : le fichier n'est plus à cet endroit." in texts
    assert app.button(key="home-project-0").disabled
    before = new.read_bytes()
    _choose(monkeypatch, new)
    app.button(key="home-find-0").click().run()
    assert not app.exception, app.exception
    assert tracked.load() == [new]
    assert not app.button(key="home-project-0").disabled
    assert any(m.value.startswith("4 · ") for m in app.markdown)  # the row complete again
    assert any(m.value == "trouvée" for m in app.markdown)
    assert any("fait à partir de la base etude-sommeil.sav" in s.value for s in app.success)
    assert not [b for b in app.button if b.key == "home-find-0"]
    assert new.read_bytes() == before
    assert not old.exists()


@pytest.mark.allow_hosts(["127.0.0.1"])
@pytest.mark.parametrize("which", ["cancelled", "database", "broken"])
def test_nothing_changes_without_a_readable_project(moved, monkeypatch, which):
    old, new = moved
    broken = new.with_name("abime.dd.json")
    broken.write_text("{ coupé", encoding="utf-8")
    chosen = {"cancelled": None, "database": new.with_name("etude-sommeil.sav"),
              "broken": broken}[which]  # fmt: skip
    _choose(monkeypatch, chosen)
    app = _home()
    app.button(key="home-find-0").click().run()
    assert not app.exception, app.exception
    assert tracked.load() == [old]
    assert any("rien n'est changé" in e.value for e in app.error)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_found_again_where_it_was_already_followed(moved, monkeypatch):
    _old, new = moved
    tracked.follow(new)
    _choose(monkeypatch, new)
    app = _home()
    app.button(key=f"home-find-{len(tracked.load()) - 1}").click().run()
    assert tracked.load() == [new]
    assert [b.label for b in app.button if (b.key or "").startswith("home-project-")] == [
        "etude-sommeil"
    ]  # fmt: skip


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_project_not_found_no_longer_followed(moved):
    app = _home()
    app.button(key="home-unfollow-0").click().run()
    assert tracked.load() == []
    assert moved[1].is_file()
