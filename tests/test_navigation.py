"""v0.16, step B1 (finding 1, D-122): the pages by phase, Documenter, Analyser, Rédiger, then
the settings; each page shows what waits there, or a tick."""

import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.project import load_project, save_project
from ddict.project.model import Frozen
from ddict.review import navigation
from ddict.workflow import Task, add_questionnaire, profile_database, tasks

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")


@pytest.fixture
def sleep(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.sav", tmp_path / "etude-sommeil.sav")
    _project, path = profile_database(tmp_path / "etude-sommeil.sav")
    return path


def _open(path: Path, mode: str | None = None) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    if mode:
        app.session_state["mode"] = mode
    app.run()
    assert not app.exception, app.exception
    return app


def _titles(app: AppTest) -> list[str]:
    """The pages of the navigation, as AppTest registers them."""
    return [info["page_name"] for info in app._registered_pages.values()]


def test_the_three_phases_then_the_settings():
    sections = {
        section: [page.mode for page in pages] for section, pages in navigation.SECTIONS.items()
    }
    assert sections == {
        "Documenter": ["base", "questionnaire", "glossary", "variables", "groups", "names",
                       "export"],
        "Analyser": ["plan", "analyses", "notebook"],
        "Rédiger": ["method", "verify"],
        "Réglages": ["ai"],
    }  # fmt: skip


def test_the_state_of_a_page(sleep):
    project = load_project(sleep)
    counts = navigation.waiting(
        [Task(3, "", "glossary"), Task(2, "", "variables"), Task(1, "", "variables", "x")]
    )
    assert counts == {"glossary": 3, "variables": 3}
    assert navigation.title(project, "glossary", counts) == "Glossaire (3)"
    assert navigation.title(project, "questionnaire", counts) == "Questionnaire ✓"
    assert navigation.title(project, "groups", counts) == "Groupes"  # its tasks come later
    assert navigation.title(project, "export", counts) == "Export"  # nothing to follow
    assert navigation.title(project, "plan", counts) == "Plan"
    project.plan.frozen = Frozen(date="2026-10-18", fingerprint="0" * 64)
    assert navigation.title(project, "plan", counts) == "Plan ✓"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_navigation_shows_each_page_with_its_state(sleep):
    app = _open(sleep)
    assert app.header[0].value.startswith("etude-sommeil.sav")  # a project opens on Base
    assert app.session_state["mode"] == "base"
    counts = navigation.waiting(tasks(load_project(sleep)))
    expected = [
        navigation.title(load_project(sleep), page.mode, counts)
        for pages in navigation.SECTIONS.values()
        for page in pages
    ]
    assert _titles(app) == expected
    assert "Questionnaire (1)" in expected and "Glossaire (2)" in expected
    assert not [r for r in app.sidebar.radio if r.key == "mode"]  # no more list of 13


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_task_of_the_dashboard_opens_its_page(sleep):
    app = _open(sleep)
    task = next(b for b in app.sidebar.button if b.label.startswith("Codes suspects"))
    task.click().run()
    assert not app.exception, app.exception
    assert app.session_state["mode"] == "variables"
    assert app.sidebar.radio(key="filter").value == "suspects"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_ai_is_reached_from_the_pages_that_use_it(sleep, tmp_path):
    shutil.copy(EXAMPLES / "questionnaire-sommeil.pdf", tmp_path / "questionnaire-sommeil.pdf")
    project = load_project(sleep)
    add_questionnaire(project, tmp_path / "questionnaire-sommeil.pdf")
    save_project(project, sleep)
    app = _open(sleep, "questionnaire")
    app.button(key="go-ai-questionnaire").click().run()
    assert app.header[0].value == "IA"
    app = _open(sleep, "variables")
    app.button(key="go-ai-variables").click().run()
    assert app.header[0].value == "IA"
