"""v0.16, step A8: the finishing touches. French placeholders (17), a dash for an empty
cell (17), whole bounds for a scale of whole codes (19), groups named by what they are (20),
no deprecated `use_container_width` (21), "Précédente" and "Suivante" (23), the first
numbers of the notebook explained (24). The widths of columns (18) are in the scenario."""

import ast
import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.review.ui import common as c
from ddict.workflow import profile_database
from test_notebook_page import _build_by_command, _folder

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")
REVIEW = ROOT / "src" / "ddict" / "review"


@pytest.fixture
def sleep(tmp_path):
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


def _calls(name: str):
    for path in sorted(REVIEW.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == name:
                yield path.name, node


def test_every_list_has_a_french_placeholder():
    """Without one, Streamlit writes "Choose an option" in an empty list (finding 17)."""
    missing = [
        f"{name}:{node.lineno}"
        for kind in ("selectbox", "multiselect")
        for name, node in _calls(kind)
        if not any(k.arg == "placeholder" for k in node.keywords)
    ]
    assert not missing, missing


def test_every_list_takes_known_parameters():
    """A misspelt keyword ("kplaceholder") is valid Python, and fails only on its page."""
    import inspect

    import streamlit as st

    wrong = [
        f"{name}:{node.lineno}:{k.arg}"
        for kind in ("selectbox", "multiselect")
        for name, node in _calls(kind)
        for k in node.keywords
        if k.arg and k.arg not in inspect.signature(getattr(st, kind)).parameters
    ]
    assert not wrong, wrong


def test_an_empty_cell_is_a_dash():
    assert [c.dash(v) for v in (None, "", "nominal", 0)] == ["—", "—", "nominal", "0"]


def test_no_deprecated_width():
    found = [p.name for p in REVIEW.rglob("*.py") if "use_container_width" in p.read_text("utf-8")]
    assert not found, found  # removed by Streamlit after 2025-12-31 (finding 21)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_whole_bounds_for_whole_codes(sleep):
    app = _open(sleep, "groups")
    app.button(key="offer-bounds-G1").click().run()
    low = app.number_input(key="scoring-min-G1")
    assert low.value == 1 and isinstance(low.value, int)
    assert low.proto.format == "%d" and low.proto.step == 1


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_groups_are_named_by_what_they_are(sleep):
    app = _open(sleep, "groups")
    options = app.sidebar.selectbox(key="group").options
    assert options[0].startswith("G1 — 8 items"), options
    app.sidebar.selectbox(key="group").select("G2").run()
    app.text_input(key="prefix-G2").input("anx")
    app.button(key="save-items-G2").click().run()
    assert not app.exception, app.exception
    assert app.sidebar.selectbox(key="group").value == "G2"  # its new text keeps the choice


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_previous_and_next(sleep):
    app = _open(sleep, "variables")
    app.sidebar.radio(key="filter").set_value("all").run()
    names = app.sidebar.selectbox(key="variable").options
    app.sidebar.selectbox(key="variable").set_value("id_participant").run()
    first = app.sidebar.selectbox(key="variable").value
    assert names[0].startswith(first)
    assert app.button(key="variable-previous").disabled
    assert any(m.value == "1 sur 34" for m in app.markdown)
    app.button(key="variable-next").click().run()
    second = app.sidebar.selectbox(key="variable").value
    assert second != first and app.header[0].value.startswith(second)
    app.button(key="variable-previous").click().run()
    assert app.sidebar.selectbox(key="variable").value == first


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_first_numbers_are_explained(tmp_path, capsys):
    path = _folder(tmp_path)
    _build_by_command(path)
    capsys.readouterr()
    app = _open(path, "notebook")
    assert any("3 si l'introduction" in m.value for m in app.markdown)
