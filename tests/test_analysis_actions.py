"""v0.16, step A6 (finding 15): under "Lancer l'analyse", the bar "Ajouter au carnet · Word ·
Excel · Script R", then the result; an analysis already in the notebook says so, whatever
the session that added it, instead of being added twice."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.analysis import notebook as nb
from ddict.analysis.compute import run
from ddict.analysis.results import Subset
from ddict.review.ui.analyses_view import in_notebook
from test_analysis_data import KEY, _prepared, analyses_project
from test_notebook_page import _folder

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
T_TEST = {"outcome": ["bienetre_total"], "group": ["groupe"]}
NOW = "2026-10-18"


def test_the_same_analysis_is_found_in_the_notebook(tmp_path):
    project = analyses_project()
    prepared = _prepared(project, KEY["sav"])
    result = run(project, prepared, "t_test", T_TEST)
    notebook = nb.open_notebook(project, tmp_path / "etude.dd.json")  # a new one
    assert in_notebook(notebook, project, result) is None
    nb.add(notebook, project, result, today=NOW)
    assert in_notebook(notebook, project, result) == "A1"
    # Another option, other variables or a subgroup: another analysis.
    student = run(project, prepared, "t_test", T_TEST, {"method": "student"})
    assert in_notebook(notebook, project, student) is None
    stress = run(project, prepared, "t_test", {"outcome": ["stress"], "group": ["groupe"]})
    assert in_notebook(notebook, project, stress) is None
    women = Subset("sexe", "eq", 1.0)
    assert in_notebook(notebook, project, run(project, prepared, "t_test", T_TEST,
                                              subgroup=women)) is None  # fmt: skip


def _open(path: Path) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "analyses"
    app.run()
    assert not app.exception, app.exception
    return app


def _run_t_test(app: AppTest) -> None:
    app.selectbox(key="analysis-key").set_value("t_test").run()
    app.selectbox(key="analysis-t_test-outcome").set_value("bienetre_total").run()
    app.selectbox(key="analysis-t_test-group").set_value("groupe").run()
    app.button(key="analysis-run").click().run()
    assert not app.exception, app.exception


def _in_order(node) -> list:
    """The elements of the page, in the order they are drawn."""
    found = []
    for child in getattr(node, "children", {}).values():
        found.append(child)
        found.extend(_in_order(child))
    return found


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_bar_comes_before_the_result(tmp_path):
    app = _open(_folder(tmp_path))
    _run_t_test(app)
    order = _in_order(app.main)

    def where(test) -> int:
        return next(i for i, e in enumerate(order) if test(e))

    run_button = where(lambda e: getattr(e, "key", None) == "analysis-run")
    add = where(lambda e: getattr(e, "key", None) == "analysis-add")
    result = where(lambda e: e.type == "subheader" and e.value == "Résultat")
    assert run_button < add < result
    labels = [e.proto.label for e in order if e.type == "download_button"][:3]
    assert labels == ["Word", "Excel", "Script R"]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_an_analysis_already_in_the_notebook_says_so(tmp_path):
    path = _folder(tmp_path)
    app = _open(path)
    _run_t_test(app)
    assert app.button(key="analysis-add").label == "Ajouter au carnet"
    app.button(key="analysis-add").click().run()
    assert "Ajoutée au carnet : A1" in app.success[0].value
    # Another session, the same analysis: the notebook knows it.
    again = _open(path)
    _run_t_test(again)
    button = again.button(key="analysis-add")
    assert button.label == "Déjà au carnet : A1" and button.disabled
    assert [b for b in again.button if b.key == "go-notebook"]
    assert len(nb.load_notebook(nb.notebook_path(path)).entries) == 1
