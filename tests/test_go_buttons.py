"""v0.16, step A5 (finding 11): each message that points to another page carries a button
that opens it, with what it needs filled in ("Définir anx" opens the glossary with the
acronym in its field)."""

import ast
import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.cli import main
from ddict.project import load_project, save_project
from ddict.project.model import TrackedValue
from ddict.workflow import add_questionnaire, profile_database
from test_notebook_page import _build_by_command, _folder

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")
VIEWS = ROOT / "src" / "ddict" / "review" / "ui"


@pytest.fixture
def sleep(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.sav", tmp_path / "etude-sommeil.sav")
    _project, path = profile_database(tmp_path / "etude-sommeil.sav")
    return path


@pytest.fixture
def sleep_with_questionnaire(sleep):
    shutil.copy(EXAMPLES / "questionnaire-sommeil.pdf", sleep.parent / "questionnaire-sommeil.pdf")
    project = load_project(sleep)
    add_questionnaire(project, sleep.parent / "questionnaire-sommeil.pdf")
    save_project(project, sleep)
    return sleep


def _open(path: Path, mode: str) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = mode
    app.run()
    assert not app.exception, app.exception
    return app


def _go(app: AppTest, key: str, header: str) -> AppTest:
    app.button(key=key).click().run()
    assert not app.exception, app.exception
    assert app.header[0].value.startswith(header), app.header[0].value
    return app


# --- Every message that names another page has its button. ---


def _strings(node) -> str:
    return "".join(
        n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)
    )


def test_every_message_naming_a_page_has_a_button():
    """In each view, a function that tells the person to go to another page ("sur la page
    Base", "page « Questionnaire »") also draws a button to go there."""
    descriptive = {  # where the page is named to describe, not to send the person there
        ("notebook_view.py", "page"),  # "Les analyses ajoutées depuis la page Analyses…"
        ("recode_view.py", "listing"),  # its buttons are drawn per recoding (tested below)
        ("analyses_view.py", "_add"),  # a callback: its button follows the message, below
    }
    missing = []
    for path in sorted(VIEWS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for function in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
            text = _strings(function)
            sends = any(
                marker in text for marker in ("sur la page ", "(page « ", "page Base.", "page IA")
            )
            calls = {
                n.func.attr
                for n in ast.walk(function)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            }
            known = (path.name, function.name) in descriptive
            if sends and not calls & {"go_button", "offer"} and not known:
                missing.append(f"{path.name}:{function.name}")
    assert not missing, missing


# --- Each button opens its page, filled in. ---


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_define_an_acronym_from_the_questionnaire(sleep_with_questionnaire):
    app = _open(sleep_with_questionnaire, "questionnaire")
    assert app.button(key="go-define-anx").label == "Définir anx"
    _go(app, "go-define-anx", "Glossaire des sigles")
    assert app.text_input(key="glossary-new-term").value == "ANX"
    assert app.text_input(key="glossary-new-meaning").value == ""
    app = _open(sleep_with_questionnaire, "questionnaire")
    _go(app, "go-glossary-pending", "Glossaire des sigles")


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_define_an_acronym_on_the_glossary_page(sleep_with_questionnaire):
    app = _open(sleep_with_questionnaire, "glossary")
    app.button(key="define-anx").click().run()
    assert app.text_input(key="glossary-new-term").value == "ANX"
    app.text_input(key="glossary-new-meaning").input("Anxiété")
    app.button(key="glossary-add").click().run()
    assert any(e.term == "ANX" for e in load_project(sleep_with_questionnaire).glossary)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_add_the_questionnaire_from_the_ai_page(sleep):
    _go(_open(sleep, "ai"), "go-questionnaire", "Questionnaire")


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_choose_the_model_from_the_advice(sleep):
    _go(_open(sleep, "analyses"), "go-ai-advice", "IA")


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_decide_the_levels_when_no_variable_fits(tmp_path):
    # A CSV file gives no measure level: none is in force until the team decides.
    shutil.copy(EXAMPLES / "etude-sommeil.csv", tmp_path / "etude-sommeil.csv")
    _project, path = profile_database(tmp_path / "etude-sommeil.csv")
    app = _open(path, "analyses")
    app.selectbox(key="analysis-key").set_value("t_test").run()
    assert any("aucune variable ne convient" in i.value for i in app.info)
    _go(app, "go-base-analysis-t_test-outcome", "etude-sommeil.csv")
    app = _open(path, "plan")
    app.selectbox(key="plan-new-analysis").set_value("t_test").run()
    assert [b.key for b in app.button if b.key.startswith("go-base-")]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_notebook_from_the_analyses_and_back(tmp_path):
    path = _folder(tmp_path)
    app = _go(_open(path, "notebook"), "go-analyses", "Analyses")  # the notebook is empty
    app.selectbox(key="analysis-key").set_value("t_test").run()
    app.selectbox(key="analysis-t_test-outcome").set_value("bienetre_total").run()
    app.selectbox(key="analysis-t_test-group").set_value("groupe").run()
    app.button(key="analysis-run").click().run()
    app.button(key="analysis-add").click().run()
    _go(app, "go-notebook", "Carnet")


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_method_from_the_notebook_and_the_groups_from_the_method(tmp_path, capsys):
    path = _folder(tmp_path)
    _build_by_command(path)
    capsys.readouterr()
    app = _go(_open(path, "notebook"), "go-method", "Méthode")
    _go(app, "go-groups", "G1")


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_change_a_recoding_on_its_variable(tmp_path, capsys):
    path = _folder(tmp_path)
    _go(_open(path, "groups"), "go-variables-recode", "")
    assert main(["recoder", "regrouper", str(path), "sexe", "--nom", "sexe_2", "--libelle",
                 "Sexe, deux modalités", "--groupe", "1", "1", "--groupe", "2", "2",
                 "--raison", "Essai."]) == 0  # fmt: skip
    capsys.readouterr()
    app = _open(path, "groups")
    rule = load_project(path).recodes.rules[0]
    _go(app, f"go-recode-{rule.id}", rule.source.variable)
    assert app.sidebar.selectbox(key="variable").value == rule.source.variable


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_settle_the_conflicts_of_names_from_the_export(sleep):
    project = load_project(sleep)
    for entry in project.variables[1:3]:  # two variables, the same new name
        entry.new_name = TrackedValue[str](value="meme_nom", origin="human")
    save_project(project, sleep)
    app = _open(sleep, "export")
    app.button(key="export-copy-write").click().run()
    assert any("conflits" in e.value for e in app.error)
    _go(app, "go-names-conflicts", "Noms")
    assert app.radio(key="names-filter").value == "conflicts"
