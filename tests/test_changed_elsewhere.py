"""v0.17, step C2 (D-130): two sessions on the same project. The second one's decision is
not saved over the first's: the page says so at the top, recalls the decision, and offers
"Recharger le projet"; after the reload, the first session's decision is shown and the
refused one stays, in words, to be made again. A change seen before any decision is said
too; a date touched without a change is not. The same for the notebook. On the fictional
sleep and analyses studies."""

import os
import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import glossary
from ddict.analysis import notebook as nb
from ddict.project import load_project, save_project
from ddict.review.ui import common as c
from ddict.workflow import add_questionnaire, profile_database
from test_notebook_page import _build_by_command, _folder

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")
UI = ROOT / "src" / "ddict" / "review" / "ui"

CHANGED = "Ce projet a été modifié ailleurs depuis que vous l'avez ouvert"
NOT_SAVED = "Votre dernière décision n'est pas enregistrée."


@pytest.fixture
def sleep(tmp_path):
    for name in ("etude-sommeil.sav", "questionnaire-sommeil.pdf"):
        shutil.copy(EXAMPLES / name, tmp_path / name)
    project, path = profile_database(tmp_path / "etude-sommeil.sav")
    add_questionnaire(project, tmp_path / "questionnaire-sommeil.pdf")
    save_project(project, path)
    return path


def _open(path: Path, mode: str) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = mode
    app.run()
    assert not app.exception, app.exception
    return app


def _warnings(app: AppTest) -> list[str]:
    return [w.value for w in app.warning]


def _texts(app: AppTest) -> list[str]:
    return [m.value for m in app.markdown]


def _status(path: Path, term: str) -> str:
    return glossary.entry(load_project(path), term).status


def _accept(app: AppTest, term: str, meaning: str) -> None:
    app.text_input(key=f"input-glossary-{term}").input(meaning)
    app.button(key=f"accept-glossary-{term}").click().run()
    assert not app.exception, app.exception


def test_no_view_saves_but_through_common():
    """One way to save, which checks the file (v0.17): never `save_project` in a view."""
    for path in UI.glob("*.py"):
        if path.name == "common.py":
            continue
        text = path.read_text(encoding="utf-8")
        assert "save_project(" not in text, path.name
        assert "nb.save_notebook(" not in text, path.name


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_two_sessions_on_the_same_project(sleep):
    first, second = _open(sleep, "glossary"), _open(sleep, "glossary")
    _accept(first, "TCC", "Thérapie cognitivo-comportementale (TCC)")
    assert _status(sleep, "TCC") == "corrected"
    assert not any(CHANGED in w for w in _warnings(first))
    # The second session decides without having seen the first one's decision.
    _accept(second, "QFS", "Questionnaire fictif du sommeil (version B)")
    assert _status(sleep, "QFS") == "proposed"  # nothing written over the first one
    assert _status(sleep, "TCC") == "corrected"
    warning = next(w for w in _warnings(second) if CHANGED in w)
    assert NOT_SAVED in warning
    recalled = next(t for t in _texts(second) if t.startswith("Votre décision :"))
    assert "**Glossaire** — « Accepter (QFS) »" in recalled
    assert "Définition de QFS : « Questionnaire fictif du sommeil (version B) »" in recalled
    errors = " ".join(e.value for e in second.error)
    assert "Non enregistré : le projet a été modifié ailleurs" in errors
    # Nothing shown as decided that is not written: the page goes back to the file as read.
    assert glossary.entry(second.session_state["project"], "QFS").status == "proposed"
    # Another decision of the second session is refused as well, until the reload.
    second.button(key="reject-glossary-EFA").click().run()
    assert _status(sleep, "EFA") == "proposed"
    assert len([t for t in _texts(second) if t.startswith("Votre décision :")]) == 2
    # Reload: the first session's decision is there; the refused ones, to make again.
    second.button(key="reload-project").click().run()
    assert not second.exception, second.exception
    assert second.session_state["mode"] == "glossary"
    assert not any(CHANGED in w for w in _warnings(second))
    assert second.session_state["project"].glossary == load_project(sleep).glossary
    assert any("Décision à refaire" in i.value for i in second.info)
    redo = _texts(second)
    assert any("Définition de QFS : « Questionnaire fictif du sommeil (version B) »" in t
               for t in redo)  # fmt: skip
    assert any("« Rejeter (EFA) »" in t for t in redo)
    # Decided again, it is saved; "Fermer" puts the recall away.
    _accept(second, "QFS", "Questionnaire fictif du sommeil (version B)")
    assert _status(sleep, "QFS") == "corrected"
    second.button(key="redo-close").click().run()
    assert not any("Décision à refaire" in i.value for i in second.info)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_change_is_said_before_any_decision(sleep):
    app = _open(sleep, "glossary")
    other = load_project(sleep)
    glossary.decide(other, "EFA", "reject", now="2026-10-18T10:00:00")
    save_project(other, sleep)
    app.run()
    warning = next(w for w in _warnings(app) if CHANGED in w)
    assert NOT_SAVED not in warning  # nothing refused yet
    app.button(key="reload-project").click().run()
    assert not any(CHANGED in w for w in _warnings(app))
    assert app.session_state["project"].glossary == load_project(sleep).glossary


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_date_touched_without_change_says_nothing(sleep):
    """OneDrive may touch the date of a file it did not change."""
    app = _open(sleep, "glossary")
    stat = sleep.stat()
    os.utime(sleep, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))
    app.run()
    assert not any(CHANGED in w for w in _warnings(app))
    _accept(app, "TCC", "Thérapie cognitivo-comportementale (TCC)")
    assert _status(sleep, "TCC") == "corrected"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_field_typed_is_recalled_with_its_label(sleep):
    """On the page of a variable: the place names the variable, the field its label."""
    app = _open(sleep, "variables")
    for name, value in c.variable_fields("heures_sommeil").items():
        app.session_state[name] = value
    app.run()
    other = load_project(sleep)
    other.plan.sample_size = "Ailleurs"
    save_project(other, sleep)
    app.text_input(key="input-heures_sommeil-unit").input("heures").run()
    app.button(key="save-texts-heures_sommeil").click().run()
    recalled = next(t for t in _texts(app) if t.startswith("Votre décision :"))
    assert "**Variables, heures_sommeil**" in recalled
    assert "Unité : « heures »" in recalled
    assert load_project(sleep).variable("heures_sommeil").unit.value is None


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_notebook_changed_meanwhile(tmp_path, capsys, monkeypatch):
    """Someone writes the notebook between the page's reading and its saving: refused."""
    path = _folder(tmp_path)
    _build_by_command(path)
    capsys.readouterr()
    app = _open(path, "notebook")
    reading = nb.open_notebook

    def read_then_someone_else_writes(project, project_path):
        notebook = reading(project, project_path)
        other = nb.load_notebook(nb.notebook_path(project_path))
        other.first_figure = 7
        nb.save_notebook(other, nb.notebook_path(project_path))
        return notebook

    monkeypatch.setattr(nb, "open_notebook", read_then_someone_else_writes)
    app.number_input(key="notebook-first-table").set_value(3).run()
    assert not app.exception, app.exception
    kept = nb.load_notebook(nb.notebook_path(path))
    assert (kept.first_table, kept.first_figure) == (1, 7)
    assert "Non enregistré : le carnet a été modifié ailleurs" in " ".join(
        e.value for e in app.error
    )
    assert any(t.startswith("Votre décision :") and "**Carnet**" in t for t in _texts(app))
