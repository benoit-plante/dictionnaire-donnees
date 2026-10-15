"""v0.5, step 2: the interface in English, with no French left but the team's own data."""

import re
import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import i18n, settings
from ddict.project import load_project, save_project
from ddict.project.model import TrackedValue
from ddict.questionnaire import link
from ddict.review import logic
from ddict.workflow import add_questionnaire, profile_database

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
FRENCH = re.compile(
    r"[àâçéèêëîïôûùœÀÂÇÉÈÊÎÔ«»]|\b(le|la|les|des|du|une|est|pas|aucun|aucune|avec|pour|dans|"
    r"sur|ou|et|à|vos|votre|cette|ces)\b",
    re.IGNORECASE,
)
MODES = ["base", "questionnaire", "glossary", "ai", "variables", "groups", "names", "export"]


def test_every_string_is_translated():
    catalog = i18n._catalog("en")
    import importlib.util

    root = Path(__file__).resolve().parent.parent
    spec = importlib.util.spec_from_file_location(
        "traductions", root / "scripts" / "traductions.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    missing = [m.id for m in module.read("en") if m.id and not m.string]
    assert not missing, missing
    assert catalog.gettext("Nouveau projet") == "New project"


@pytest.fixture
def project_path(fictional_files, tmp_path):
    for name in ("etude-sommeil.sav", "questionnaire-sommeil.txt"):
        shutil.copy(fictional_files[name], tmp_path / name)
    project, path = profile_database(tmp_path / "etude-sommeil.sav")
    add_questionnaire(project, tmp_path / "questionnaire-sommeil.txt")
    logic.link_question(project, "age", "Q3", now="2026-10-14T12:00:00")
    project.variable("genre").label = TrackedValue[str](
        value="Genre déclaré", origin="ai", status="proposed", ai_run="run-0001"
    )
    save_project(project, path)
    return path


def _data(path: Path) -> list[str]:
    """The team's own strings, which stay as written: file labels, value labels, questions,
    glossary, names. Longest first, so that a long one is removed before its parts."""
    project = load_project(path)
    found = {project.source.name, project.source.label or "", str(path), str(path.parent)}
    for e in project.variables:
        found |= {e.name, e.file.label or "", e.label.value or "", e.description.value or ""}
        found |= {v.label for v in e.file.value_labels}
        found |= {v.label for v in e.value_labels.value or []}
        found |= {str(i.value) for i in e.issues}
    for q in project.questionnaire.questions:
        found.add(q.text)
        found |= {o.text for o in q.options} | {r.text for r in q.rows}
        found |= {link.target_text(t) for t in link.targets(project.questionnaire)}
    for g in project.glossary:
        found |= {g.term, g.meaning, g.source or ""}
    return sorted((s for s in found if s), key=len, reverse=True)


def _texts(app) -> list[str]:
    texts = []
    for kind in (
        "title",
        "header",
        "subheader",
        "markdown",
        "caption",
        "info",
        "success",
        "warning",
        "error",
        "text",
    ):
        texts += [str(e.value) for e in getattr(app, kind)]
    for kind in (
        "button",
        "checkbox",
        "radio",
        "selectbox",
        "text_input",
        "text_area",
        "multiselect",
        "number_input",
        "toggle",
    ):
        texts += [str(e.label) for e in getattr(app, kind)]
    texts += [str(e.label) for e in app.expander]
    return texts


@pytest.mark.allow_hosts(["127.0.0.1"])
@pytest.mark.parametrize("mode", MODES)
def test_no_french_left_in_english(project_path, mode):
    settings.save_interface_language("en")
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(project_path)
    app.session_state["mode"] = mode
    app.session_state["filter"] = "all"
    app.run()
    assert not app.exception, app.exception
    data = _data(project_path)
    left = []
    for text in _texts(app):
        for value in data:
            text = text.replace(value, " ")
        if FRENCH.search(text):
            left.append(text.strip()[:120])
    assert not left, left


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_home_page_in_english():
    settings.save_interface_language("en")
    app = AppTest.from_file(APP, default_timeout=30)
    app.session_state["project_path"] = ""
    app.run()
    left = [t for t in _texts(app) if FRENCH.search(t) and t != "Langue · Language"]
    assert not left, left


@pytest.mark.allow_hosts(["127.0.0.1"])
@pytest.mark.parametrize(
    "name", ["age", "genre", "sommeil_q3", "anx1", "commentaire", "date_naissance"]
)
def test_variable_pages_in_english(project_path, name):
    settings.save_interface_language("en")
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(project_path)
    app.session_state["mode"] = "variables"
    app.session_state["filter"] = "all"
    app.session_state["current"] = name
    app.run()
    assert not app.exception, app.exception
    assert app.header[0].value.startswith(name)
    data = _data(project_path)
    left = []
    for text in _texts(app):
        for value in data:
            text = text.replace(value, " ")
        if FRENCH.search(text):
            left.append(text.strip()[:120])
    assert not left, left


def test_english_command_names(project_path, capsys):
    """English aliases of the commands and options; the French ones still work."""
    from ddict.cli import main

    assert main(["export", str(project_path), "--work", "--syntax"]) == 0
    assert project_path.with_name("etude-sommeil-travail.xlsx").exists()
    assert project_path.with_name("etude-sommeil-metadonnees.R").exists()
    assert main(["exporter", str(project_path), "--travail"]) == 0
    assert main(["profile", str(project_path.with_name("etude-sommeil.sav"))]) == 2  # exists
    assert "--remplacer" in capsys.readouterr().err
