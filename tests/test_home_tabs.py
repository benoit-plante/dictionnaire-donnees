"""The tabs of the home page (plan-accueil, step C2, D-160): Mes projets, Nouveau projet,
Concevoir un questionnaire, Ouvrir un projet, Réglages, in the sidebar; the page at the root
address never the one the address names (no "Page not found" on a reload); the tab kept
after an action; back from a project on "Mes projets"."""

import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from accueil import tab
from ddict import settings
from ddict.review import navigation
from ddict.review.ui import home_view
from ddict.workflow import profile_database

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")
EXAMPLES = ROOT / "exemples" / "bases-fictives"
TITLES = {
    "projets": ("Mes projets", "My projects"),
    "nouveau": ("Nouveau projet", "New project"),
    "concevoir": ("Concevoir un questionnaire", "Design a questionnaire"),
    "ouvrir": ("Ouvrir un projet", "Open a project"),
    "reglages": ("Réglages", "Settings"),
}


def _home() -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = ""
    app.run()
    assert not app.exception, app.exception
    return app


# --- The page at the root address. ---


TABS = list(home_view.TABS)


@pytest.mark.parametrize(
    ("current", "url", "expected"),
    [
        ("projets", None, "projets"),  # tests: no address
        ("projets", "http://127.0.0.1:8501/", "projets"),
        ("projets", "http://127.0.0.1:8501/nouveau", "projets"),  # a reload on /nouveau
        ("nouveau", "http://127.0.0.1:8501/nouveau", "projets"),  # never the one asked
        ("projets", "http://127.0.0.1:8501/projets", "nouveau"),
        ("projets", "http://127.0.0.1:8501/plan", "projets"),  # "Accueil" from a project
        ("ouvrir", "http://127.0.0.1:8501/ouvrir/", "projets"),
    ],
)
def test_the_root_page_is_never_the_one_the_address_names(current, url, expected):
    assert navigation.root(current, TABS, url) == expected


def test_the_tabs_and_their_order():
    assert TABS == ["projets", "nouveau", "concevoir", "ouvrir", "reglages"]
    assert home_view.FIRST_TAB == "projets"


# --- In the interface. ---


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_mes_projets_first_then_each_tab():
    app = _home()
    assert app.title[0].value == "Mes projets"
    assert app.session_state[home_view.TAB] == "projets"
    for name, (french, _english) in TITLES.items():
        assert tab(app, name).title[0].value == french
        assert app.session_state[home_view.TAB] == name
    assert [b.key for b in app.sidebar.button] == ["quit"]  # the menu, then "Quitter"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_each_tab_in_english():
    settings.save_interface_language("en")
    app = _home()
    for name, (_french, english) in TITLES.items():
        assert tab(app, name).title[0].value == english
        assert app.caption[0].value.startswith("The English interface is a trial version")


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_tab_stays_after_an_action():
    app = tab(_home(), "nouveau")
    app.button(key="home-create").click().run()  # nothing chosen: an error, same tab
    assert "Choisissez d'abord une base" in app.error[0].value
    assert app.title[0].value == "Nouveau projet"
    assert app.session_state[home_view.TAB] == "nouveau"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_no_project_followed_leads_to_the_search():
    app = _home()
    app.button(key="home-go-search").click().run()
    assert not app.exception, app.exception
    assert app.title[0].value == "Ouvrir un projet"
    assert app.button(key="home-search").label == "Chercher les projets dans un dossier…"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_back_from_a_project_on_mes_projets(tmp_path):
    base = tmp_path / "etude-sommeil.sav"
    shutil.copy(EXAMPLES / "etude-sommeil.sav", base)
    _project, path = profile_database(base)
    app = tab(_home(), "ouvrir")
    app.text_input(key="home-project").input(str(path)).run()
    app.button(key="home-open").click().run()
    assert app.sidebar.title[0].value == "etude-sommeil.sav"
    app.sidebar.button(key="home").click().run()  # "Accueil"
    assert not app.exception, app.exception
    assert app.title[0].value == "Mes projets"
