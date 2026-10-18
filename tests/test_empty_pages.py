"""v0.16, step A3: never a blank page, and a plan just begun is not a fault. The page
"Variables" opens on a filter that holds variables and says so in its main area when the
chosen filter is empty; the page "Plan" lists what freezing needs, without any red."""

import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.cli import main
from ddict.project import load_project
from ddict.project.model import TrackedValue
from ddict.review import logic
from ddict.review.ui import variables_view
from ddict.workflow import profile_database
from test_notebook_page import _folder
from test_plan_page import COMMANDS, _plan

EXAMPLES = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"
APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
NOW = "2026-10-18T12:00:00"


@pytest.fixture
def new_project(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.sav", tmp_path / "etude-sommeil.sav")
    _project, path = profile_database(tmp_path / "etude-sommeil.sav")
    return path


def _open(path: Path, mode: str) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = mode
    app.run()
    assert not app.exception, app.exception
    return app


# --- Variables. ---


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_new_project_opens_on_its_first_task(new_project):
    # Nothing to review in a new project: the first task leading here is the suspect codes.
    app = _open(new_project, "variables")
    assert app.sidebar.radio(key="filter").value == "suspects"
    assert app.sidebar.selectbox(key="variable").value is not None
    assert app.header, "the main area shows a variable"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_an_empty_filter_says_so_in_the_main_area(new_project):
    app = _open(new_project, "variables")
    app.sidebar.radio(key="filter").set_value("to_review").run()
    assert [i.value for i in app.main.info] == ["Aucune variable dans le filtre « À réviser »."]
    labels = {b.key: b.label for b in app.main.button if b.key.startswith("show-filter-")}
    assert labels["show-filter-all"] == "Toutes (34)"
    assert "show-filter-to_review" not in labels  # only the filters that hold variables
    app.button(key="show-filter-all").click().run()
    assert app.sidebar.radio(key="filter").value == "all"
    assert app.sidebar.selectbox(key="variable").value is not None


def test_the_filter_to_open_on(new_project):
    project = load_project(new_project)
    assert variables_view.default_filter(project) == "suspects"
    for entry in project.variables:
        for code in entry.profile.suspect_missing_codes:
            logic.decide_sentinel(project, entry.name, code, True, now=NOW)
    assert variables_view.default_filter(project) == "all"  # no task leads to the page
    project.variables[0].label = TrackedValue[str](
        value="Proposé", origin="ai", status="proposed", ai_run="run-0001"
    )
    assert variables_view.default_filter(project) == "to_review"  # as before v0.16


# --- Plan. ---


BOXES = {":material/check_box:": True, ":material/check_box_outline_blank:": False}


def _ready(app: AppTest) -> list[tuple[str, bool]]:
    """The lines of "Pour figer le plan": read-only boxes."""
    lines = [m.value.split(" ", 1) for m in app.main.markdown]
    return [(text, BOXES[box]) for box, text in (line for line in lines if len(line) == 2)
            if box in BOXES]  # fmt: skip


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_new_plan_shows_no_red(tmp_path):
    path = _folder(tmp_path)
    app = _open(path, "plan")
    assert not app.error, [e.value for e in app.error]
    assert _ready(app) == [
        ("Au moins une hypothèse", False),
        ("Le seuil α du plan", False),
        ("L'origine des données et leur état quand le plan a été écrit", False),
        ("La base ouverte : chaque hypothèse devient une analyse du carnet", True),
        ("Chaque hypothèse calculable sur la base", False),
    ]
    assert app.button(key="plan-freeze").disabled


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_complete_plan_ticks_every_line(tmp_path, capsys):
    path = _folder(tmp_path)
    for arguments in COMMANDS:
        assert _plan(path, *arguments) == 0
    capsys.readouterr()
    app = _open(path, "plan")
    assert all(done for _label, done in _ready(app)), _ready(app)
    assert not app.button(key="plan-freeze").disabled


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_plan_without_its_database(tmp_path, capsys):
    path = _folder(tmp_path)
    for arguments in COMMANDS:
        assert _plan(path, *arguments) == 0
    capsys.readouterr()
    (path.parent / "etude-analyses.sav").unlink()
    app = _open(path, "plan")
    ready = dict(_ready(app))
    assert not ready["La base ouverte : chaque hypothèse devient une analyse du carnet"]
    assert app.button(key="plan-freeze").disabled
    assert main(["plan", "lister", str(path)]) == 0  # the command line is unchanged
