"""v0.16, step B3 (finding 14): the long pages in tabs. Base (the summary first), a group
(items, scoring, instrument, recodings), the result of an analysis (result, APA tables and
figures, files); a button of another page opens the right tab."""

import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.review.ui import base_view, groups_view
from ddict.workflow import profile_database
from test_notebook_page import _build_by_command, _folder

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")


def _open(path: Path, mode: str) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = mode
    app.run()
    assert not app.exception, app.exception
    return app


def _labels(app: AppTest) -> list[str]:
    return [t.label for t in app.tabs]


@pytest.fixture
def sleep(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.sav", tmp_path / "etude-sommeil.sav")
    _project, path = profile_database(tmp_path / "etude-sommeil.sav")
    return path


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_base_page_shows_its_summary_first(sleep):
    app = _open(sleep, "base")
    assert _labels(app) == ["Résumé", "Description", "Niveaux de mesure", "Sensibles (4)"]
    summary = app.tabs[0]
    assert [m.value for m in summary.metric][:2] == ["34", "200"]
    assert "Complétude" in [s.value for s in summary.subheader]
    assert app.tabs[1].selectbox(key="dataset-structure") is not None  # the form, second


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_group_in_tabs(sleep):
    app = _open(sleep, "groups")
    assert _labels(app) == ["Items", "Cotation", "Instrument", "Recodages"]
    assert app.tabs[0].multiselect(key="reverse-G1") is not None
    assert app.tabs[1].text_input(key="scoring-name-G1") is not None
    assert app.tabs[2].text_input(key="instrument-G1") is not None
    assert "Recodages" in [s.value for s in app.tabs[3].subheader]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_without_a_group_only_the_recodings(tmp_path):
    shutil.copy(EXAMPLES / "etude-suivi.sav", tmp_path / "etude-suivi.sav")
    _project, path = profile_database(tmp_path / "etude-suivi.sav")
    app = _open(path, "groups")  # the follow-up study has no group
    assert not app.tabs
    assert "Recodages" in [s.value for s in app.subheader]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_result_of_an_analysis_in_tabs(tmp_path):
    app = _open(_folder(tmp_path), "analyses")
    app.selectbox(key="analysis-key").set_value("t_test").run()
    app.selectbox(key="analysis-t_test-outcome").set_value("bienetre_total").run()
    app.selectbox(key="analysis-t_test-group").set_value("groupe").run()
    app.button(key="analysis-run").click().run()
    assert _labels(app) == ["Résultat", "Tableaux et figures", "Fichiers"]
    assert any(m.value.startswith("> ") for m in app.tabs[0].markdown)
    assert app.tabs[2].button(key="analysis-write") is not None
    app.button(key="analysis-write").click().run()
    assert "Fichiers écrits à côté du projet" in app.tabs[2].success[0].value  # in its tab


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_buttons_open_the_right_tab(tmp_path, capsys):
    shutil.copy(EXAMPLES / "etude-sommeil.csv", tmp_path / "etude-sommeil.csv")
    _project, csv = profile_database(tmp_path / "etude-sommeil.csv")
    app = _open(csv, "analyses")
    app.selectbox(key="analysis-key").set_value("t_test").run()
    app.button(key="go-base-analysis-t_test-outcome").click().run()
    assert app.session_state[base_view.TAB] == "Niveaux de mesure"
    path = _folder(tmp_path)
    _build_by_command(path)
    capsys.readouterr()
    app = _open(path, "method")
    app.button(key="go-groups").click().run()
    assert app.session_state[groups_view.TAB] == "Instrument"
