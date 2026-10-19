"""v0.20, step D1: the phase "Concevoir" (D-149) — for a project created by "Concevoir un
questionnaire" only, first in the menu, the page a project opens on while it has no
database; the pages that show the database wait for it, with a button; the creation from the
home page and from the command line. Fictional projects only."""

import json
import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict.cli import main
from ddict.project import load_project, save_project
from ddict.review import navigation
from ddict.workflow import design_path, profile_database
from projet_concu import project as designed

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
EXAMPLES = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"


@pytest.fixture
def design_file(tmp_path):
    path = tmp_path / "Études 2026" / "Étude conçue.dd.json"
    path.parent.mkdir()
    save_project(designed(), path)
    return path


def _open(path, mode=None):
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    if mode is not None:
        app.session_state["mode"] = mode
    app.run()
    assert not app.exception, app.exception
    return app


# --- Without Streamlit -----------------------------------------------------------------------


def test_the_phases_of_a_designed_project():
    project = designed()
    phases = navigation.sections(project)
    assert next(iter(phases)) == "Concevoir"
    assert [p.mode for p in phases["Concevoir"]] == ["design", "design_review", "publish"]
    assert "questionnaire" not in [p.mode for p in phases["Documenter"]]
    assert navigation.first(project) == "design"
    assert navigation.waits_for_base(project, "analyses")
    assert not navigation.waits_for_base(project, "plan")


def test_a_project_with_its_database_is_unchanged(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.sav", tmp_path / "etude-sommeil.sav")
    project, _path = profile_database(tmp_path / "etude-sommeil.sav")
    assert navigation.sections(project) == navigation.SECTIONS
    assert navigation.first(project) == "base"
    assert not any(navigation.waits_for_base(project, m) for m in navigation.PAGES)
    # Once its database is there, a designed project opens on it, "Concevoir" kept.
    later = designed()
    later.source = project.source
    assert navigation.first(later) == "base" and "Concevoir" in navigation.sections(later)


# --- The interface ---------------------------------------------------------------------------


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_designed_project_opens_on_its_questionnaire(design_file):
    app = _open(design_file)
    assert app.session_state["mode"] == "design"
    assert [h.value for h in app.header] == ["Questionnaire"]
    lines = [m.value for m in app.markdown]
    assert any(line.startswith("**1.** Quel est votre genre ?") for line in lines)
    assert any("`Q4_SQ001`" in line for line in lines)
    # The questionnaire page of a database's project is not in its menu.
    assert _open(design_file, "questionnaire").session_state["mode"] == "design"


@pytest.mark.allow_hosts(["127.0.0.1"])
@pytest.mark.parametrize("mode", navigation.NEEDS_BASE)
def test_a_page_that_shows_the_database_waits_for_it(design_file, mode):
    app = _open(design_file, mode)
    assert any("En attente de la base" in i.value for i in app.info)
    button = app.button(key=f"waiting-{mode}")
    button.click().run()
    assert not app.exception, app.exception
    assert app.session_state["mode"] == "design"


@pytest.mark.allow_hosts(["127.0.0.1"])
@pytest.mark.parametrize(
    "mode", ["glossary", "variables", "groups", "names", "plan", "export", "ai"]
)
def test_the_pages_open_without_a_database(design_file, mode):
    app = _open(design_file, mode)
    assert not any("En attente de la base" in i.value for i in app.info)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_planned_variable_on_its_page(design_file):
    app = _open(design_file, "variables")
    texts = " ".join(m.value for m in app.markdown) + " ".join(s.value for s in app.subheader)
    assert "Prévu par le questionnaire" in texts
    assert "Aucune statistique avant l'arrivée de la base." in texts


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_concevoir_un_questionnaire_from_the_home_page(tmp_path):
    folder = tmp_path / "Mon étude"
    folder.mkdir()
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = ""  # no project: the home page
    app.run()
    app.button(key="home-design-create").click().run()
    assert "Choisissez d'abord le dossier" in app.error[0].value
    app.text_input(key="home-design-folder").set_value(str(folder)).run()
    app.text_input(key="home-design-name").set_value("Sommeil : vague 1").run()
    app.button(key="home-design-create").click().run()
    assert not app.exception, app.exception
    path = design_path(folder, "Sommeil : vague 1")
    assert path.name == "Sommeil - vague 1.dd.json" and path.is_file()
    assert app.session_state["project_path"] == str(path)
    project = load_project(path)
    assert project.source is None and project.questionnaire.format == "designed"
    app.run()
    assert app.session_state["mode"] == "design"


# --- The command line ------------------------------------------------------------------------


def test_ddict_questionnaire_creer(tmp_path, capsys):
    assert main(["questionnaire", "creer", str(tmp_path), "--nom", "Sleep", "--langue", "en"]) == 0
    path = tmp_path / "Sleep.dd.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["settings"]["language"] == "en" and data["source"] is None
    assert main(["questionnaire", "creer", str(tmp_path), "--nom", "Sleep"]) == 2
    assert "existe déjà" in capsys.readouterr().err
    assert main(["questionnaire", "creer", str(tmp_path)]) == 2
    assert main(["questionnaire", "creer", str(tmp_path / "absent"), "--nom", "X"]) == 2
    # A file never replaces the questionnaire designed in the tool.
    pdf = EXAMPLES / "questionnaire-sommeil.pdf"
    assert main(["questionnaire", str(path), str(pdf), "--remplacer"]) == 2
    assert "conçu dans l'outil" in capsys.readouterr().err
    assert load_project(path).questionnaire.format == "designed"


# --- Step D4: the page "Base" and the dashboard ----------------------------------------------


def test_the_review_points_are_the_first_task():
    from ddict.project.model import Publication
    from ddict.workflow import tasks

    project = designed()
    found = tasks(project)
    assert found[0].mode == "design_review" and found[0].count == 5
    assert "Points de relecture" in found[0].text
    project.design.publications = [
        Publication(kind="limesurvey", date="2026-10-20", fingerprint="0" * 64,
                    questionnaire=project.questionnaire.model_copy(deep=True))
    ]  # fmt: skip
    assert tasks(project)[0].mode == "design_review"  # sent, the points stay to be seen


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_base_page_opens_and_only_its_summary_waits(design_file):
    app = _open(design_file, "base")
    assert app.session_state["mode"] == "base"
    assert any("En attente de la base" in i.value for i in app.info)
    app.button(key="waiting-base").click().run()
    assert not app.exception, app.exception
    assert app.session_state["mode"] == "design"
