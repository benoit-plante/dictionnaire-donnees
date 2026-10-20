"""Plan-accueil, step C4 (§ 7.4, D-160): nothing the home page did before is lost — each of
its functions is in one tab, and in that tab only. The functions themselves are tested
in test_home, test_home_projects, test_found_again, test_search_projects, test_tracked,
test_design_pages and test_i18n; here, where each one is."""

import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from accueil import tab
from ddict import recents, tracked
from ddict.review.ui import dialog
from ddict.workflow import profile_database

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")
EXAMPLES = ROOT / "exemples" / "bases-fictives"

# § 7.4: the widgets of each function, by the tab they are in.
WHERE = {
    "projets": (
        "home-project-0",  # the list: a click shows a project
        "home-open-chosen",  # open it where something waits
        "home-task-0",  # open it on one of its tasks
        "home-folder",  # its folder in the Explorer (new)
        "home-unfollow",  # no longer follow it
    ),
    "nouveau": ("browse-home-database", "home-database", "home-create"),
    "concevoir": (
        "home-design-browse",
        "home-design-folder",
        "home-design-name",
        "home-design-language",
        "home-design-create",
    ),
    "ouvrir": (
        "browse-home-project",  # a project file
        "home-project",
        "home-open",
        "home-recent-0",  # the recent projects
        "home-follow-0",
        "home-clear",
        "home-search",  # the projects of a folder
    ),
    "reglages": ("interface-language",),
}


@pytest.fixture
def project(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.sav", tmp_path / "etude-sommeil.sav")
    return profile_database(tmp_path / "etude-sommeil.sav")[1]


def _home() -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = ""
    app.run()
    assert not app.exception, app.exception
    return app


def _keys(app: AppTest) -> set[str]:
    """The keys of the widgets in the window and the sidebar."""
    found = set()
    for kind in ("button", "text_input", "button_group", "checkbox"):
        found |= {w.key for w in getattr(app, kind) if w.key}
        found |= {w.key for w in getattr(app.sidebar, kind) if w.key}
    return found


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_each_function_in_its_tab_and_there_only(project, tmp_path):
    tracked.follow(project)
    other = tmp_path / "autre" / "etude-sommeil.dd.json"  # a recent project not followed
    other.parent.mkdir()
    shutil.copy(project, other)
    recents.add(other)
    app = _home()
    shown = {name: _keys(tab(app, name)) for name in WHERE}
    for name, keys in WHERE.items():
        for key in keys:
            assert key in shown[name], (key, name)
            elsewhere = [n for n in WHERE if n != name and key in shown[n]]
            assert not elsewhere, (key, elsewhere)
    assert not [k for keys in shown.values() for k in keys if k.startswith("home-trial")]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_an_existing_project_open_or_replace_in_nouveau(project):
    app = tab(_home(), "nouveau")
    app.text_input(key="home-database").input(str(project.with_name("etude-sommeil.sav"))).run()
    app.button(key="home-create").click().run()
    assert {"home-open-existing", "home-replace"} <= _keys(app)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_project_moved_found_again_in_mes_projets(project, tmp_path):
    tracked.follow(tmp_path / "parti" / "etude-sommeil.dd.json")  # not there any more
    app = _home()
    assert "home-find" in _keys(app)
    assert "home-find" not in _keys(tab(app, "ouvrir"))


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_projects_found_followed_in_ouvrir(project, monkeypatch):
    monkeypatch.setattr(dialog, "choose", lambda kind: str(project.parent))
    app = tab(_home(), "ouvrir")
    app.button(key="home-search").click().run()
    assert {"home-found-0", "home-follow-found", "home-search-close"} <= _keys(app)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_no_project_followed_a_button_to_the_search():
    app = _home()
    assert "home-go-search" in _keys(app)
    assert app.button(key="home-go-search").label == "Chercher les projets dans un dossier…"
