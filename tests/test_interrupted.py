"""v0.17, step C3: an interrupted save leaves `<file>.tmp`, said when the project is opened
(interface and command line), never removed by the tool; a file held a moment by Windows
(OneDrive syncing it) is tried again, then said, the project intact, and the next save
works. On the fictional sleep study."""

import os
import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import glossary
from ddict.analysis import notebook as nb
from ddict.cli import main
from ddict.project import dumps, load_project, ondisk, save_project
from ddict.workflow import add_questionnaire, leftover_notes, profile_database

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")
REPLACE = Path.replace


@pytest.fixture
def sleep(tmp_path):
    for name in ("etude-sommeil.sav", "questionnaire-sommeil.pdf"):
        shutil.copy(EXAMPLES / name, tmp_path / name)
    project, path = profile_database(tmp_path / "etude-sommeil.sav")
    add_questionnaire(project, tmp_path / "questionnaire-sommeil.pdf")
    save_project(project, path)
    return path


@pytest.fixture
def no_pause(monkeypatch):
    monkeypatch.setattr(ondisk, "PAUSE", 0)


def _held(times: int):
    """Path.replace refused by Windows `times` times, then done."""
    calls = {"n": 0}

    def replace(self, target):
        calls["n"] += 1
        if calls["n"] <= times:
            raise PermissionError(32, "The process cannot access the file")
        return REPLACE(self, target)

    return replace, calls


def _leave_tmp(path: Path) -> Path:
    left = path.with_name(path.name + ".tmp")
    left.write_text('{"schema_version": "0.7', encoding="utf-8")  # cut in the middle
    return left


# --- A file held a moment. ---


def test_held_once_then_free(sleep, monkeypatch, no_pause):
    replace, calls = _held(1)
    monkeypatch.setattr(Path, "replace", replace)
    project = load_project(sleep)
    project.plan.sample_size = "Après une seconde tentative"
    save_project(project, sleep)
    assert calls["n"] == 2
    assert load_project(sleep).plan.sample_size == "Après une seconde tentative"


def test_held_too_long_writes_nothing(sleep, monkeypatch, no_pause):
    before = sleep.read_bytes()
    replace, calls = _held(99)
    monkeypatch.setattr(Path, "replace", replace)
    project = load_project(sleep)
    known = ondisk.remembered(project)
    project.plan.sample_size = "Jamais écrit"
    with pytest.raises(ondisk.FileBusy):
        save_project(project, sleep)
    assert calls["n"] == ondisk.TRIES
    assert sleep.read_bytes() == before
    assert ondisk.leftover(sleep) is None  # its own temporary file, removed
    assert ondisk.remembered(project) == known
    monkeypatch.setattr(Path, "replace", REPLACE)
    save_project(project, sleep)  # free again: the save works
    assert sleep.read_bytes() == dumps(project).encode("utf-8")


def test_a_file_that_cannot_be_read_is_not_said_changed(sleep, monkeypatch):
    """Held a moment while its date moved: no alarm; the save will check."""
    project = load_project(sleep)
    stat = sleep.stat()
    os.utime(sleep, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))

    def refused(path):
        raise PermissionError(32, "The process cannot access the file")

    monkeypatch.setattr(ondisk, "read", refused)
    assert ondisk.unchanged(sleep, ondisk.remembered(project))


def test_the_command_line_says_the_file_is_busy(sleep, monkeypatch, capsys, no_pause):
    before = sleep.read_bytes()
    monkeypatch.setattr(Path, "replace", _held(99)[0])
    capsys.readouterr()
    assert main(["codes", "valeur", str(sleep), "999", "age"]) == 2
    assert "est occupé, peut-être par la synchronisation de OneDrive" in capsys.readouterr().err
    assert sleep.read_bytes() == before


# --- An interrupted save. ---


def test_a_leftover_is_said_by_the_command_line_and_kept(sleep, capsys):
    left = _leave_tmp(sleep)
    capsys.readouterr()
    assert main(["niveaux", "lister", str(sleep)]) == 0
    err = capsys.readouterr().err
    assert "Un enregistrement a été interrompu" in err
    assert "etude-sommeil.dd.json.tmp est resté. Le projet ouvert est le dernier" in err
    assert left.is_file()
    # A save writes the project in full; the left file is then its own, put in place.
    assert main(["codes", "valeur", str(sleep), "999", "age"]) == 0
    assert not left.exists()


def test_the_notebook_leftover_too(sleep):
    project = load_project(sleep)
    nb.save_notebook(nb.new_notebook(project, sleep), nb.notebook_path(sleep))
    _leave_tmp(nb.notebook_path(sleep))
    notes = leftover_notes(sleep)
    assert len(notes) == 1 and "etude-sommeil-carnet.json.tmp" in notes[0]
    assert "Le carnet est le dernier enregistré en entier" in notes[0]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_leftover_is_said_on_opening(sleep):
    left = _leave_tmp(sleep)
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(sleep)
    app.session_state["mode"] = "base"
    app.run()
    assert not app.exception, app.exception
    assert any("Un enregistrement a été interrompu" in w.value for w in app.warning)
    app.button(key="leftovers-close").click().run()
    assert not any("Un enregistrement a été interrompu" in w.value for w in app.warning)
    assert left.is_file()


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_interface_says_the_file_is_busy(sleep, monkeypatch, no_pause):
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(sleep)
    app.session_state["mode"] = "glossary"
    app.run()
    monkeypatch.setattr(Path, "replace", _held(99)[0])
    meaning = "Thérapie cognitivo-comportementale (TCC)"
    app.text_input(key="input-glossary-TCC").input(meaning)
    app.button(key="accept-glossary-TCC").click().run()
    assert not app.exception, app.exception
    assert any("Le fichier est occupé" in e.value for e in app.error)
    # Nothing shown as decided that is not saved; what was typed stays in its field.
    assert glossary.entry(app.session_state["project"], "TCC").status == "proposed"
    assert glossary.entry(load_project(sleep), "TCC").status == "proposed"
    assert app.text_input(key="input-glossary-TCC").value == meaning
    monkeypatch.setattr(Path, "replace", REPLACE)
    app.button(key="accept-glossary-TCC").click().run()
    assert glossary.entry(load_project(sleep), "TCC").status == "corrected"
