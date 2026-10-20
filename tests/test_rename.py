"""Plan-accueil, step D2 (D-161): give a project its title in the interface — from its detail
in "Mes projets", and from the sidebar of the open project; taken off by "Revenir au nom du
fichier"; no file renamed; the notebook and its analyses as they were (nothing "to
recompute"); a file changed elsewhere or busy: nothing written, said."""

import json
import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import projets_stades as stages
from ddict import overview, tracked
from ddict.project import load_project, ondisk, title

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
TITLE = "Stress et travail, cohorte 2026"


@pytest.fixture(scope="module")
def made(tmp_path_factory):
    return stages.make(tmp_path_factory.mktemp("stades"))


@pytest.fixture
def carnet(made, tmp_path):
    """The project with a notebook (two analyses retained), in a folder of its own."""
    folder = tmp_path / "Études 2026" / "Équipe"
    shutil.copytree(made["carnet"].parent, folder)
    overview.clear_cache()
    return folder / made["carnet"].name


def _home(*followed: Path) -> AppTest:
    for path in followed:
        tracked.follow(path)
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = ""
    app.run()
    assert not app.exception, app.exception
    return app


def _open(path: Path) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.run()
    assert not app.exception, app.exception
    return app


def _files(folder: Path) -> list[str]:
    return sorted(p.name for p in folder.iterdir())


# --- From the detail of "Mes projets". ---


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_rename_from_the_detail_then_open_with_its_notebook(carnet):
    before = overview.row(carnet)
    files = _files(carnet.parent)
    app = _home(carnet)
    assert app.text_input(key="home-title").value == ""
    assert app.text_input(key="home-title").placeholder == "etude-analyses"
    app.text_input(key="home-title").input(f"  {TITLE}  ")
    app.button(key="home-title-save").click().run()
    assert not app.exception, app.exception
    assert any("Titre enregistré" in s.value for s in app.success)
    assert load_project(carnet).title == TITLE
    assert _files(carnet.parent) == files  # no file renamed
    assert app.subheader[0].value == TITLE
    assert app.sidebar.button(key="home-project-0").label.startswith(TITLE)
    after = overview.row(carnet)
    counts = ("retained", "to_confirm", "to_recompute", "notebook", "phase")
    assert [getattr(after, c) for c in counts] == [getattr(before, c) for c in counts]
    app.button(key="home-open-chosen").click().run()  # opened: its notebook is there
    assert not app.exception, app.exception
    assert app.sidebar.title[0].value == TITLE
    assert "etude-analyses.sav" in [c.value for c in app.sidebar.caption]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_back_to_the_files_name(carnet):
    title.rename(carnet, TITLE)
    app = _home(carnet)
    assert app.text_input(key="home-title").value == TITLE
    app.button(key="home-title-clear").click().run()
    assert load_project(carnet).title is None
    assert app.subheader[0].value == "etude-analyses"
    assert app.text_input(key="home-title").value == ""
    assert not [b for b in app.button if b.key == "home-title-clear"]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_field_follows_the_project_shown(carnet, made):
    title.rename(carnet, TITLE)
    app = _home(carnet, made["neuf"])
    rows = overview.rows(tracked.load())
    for index, row in enumerate(rows):
        app.sidebar.button(key=f"home-project-{index}").click().run()
        assert app.text_input(key="home-title").value == (row.title or "")


@pytest.mark.allow_hosts(["127.0.0.1"])
@pytest.mark.parametrize("trouble", ["changed", "busy"])
def test_nothing_written_when_the_file_is_not_free(carnet, monkeypatch, trouble):
    busy = trouble == "busy"
    error = ondisk.FileBusy(carnet) if busy else ondisk.FileChanged(carnet, "changed")

    def refuse(path, text):
        raise error

    before = carnet.read_bytes()
    app = _home(carnet)
    monkeypatch.setattr(title, "rename", refuse)
    app.text_input(key="home-title").input(TITLE)
    app.button(key="home-title-save").click().run()
    said = "modifié ailleurs" if trouble == "changed" else "occupé"
    assert any(said in e.value for e in app.error)
    assert carnet.read_bytes() == before


# --- From the open project. ---


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_rename_from_the_open_project(carnet):
    app = _open(carnet)
    assert app.sidebar.title[0].value == "etude-analyses.sav"
    app.sidebar.text_input(key="project-title").input(TITLE)
    app.sidebar.button(key="project-title-save").click().run()
    assert not app.exception, app.exception
    assert load_project(carnet).title == TITLE
    assert app.sidebar.title[0].value == TITLE
    assert "etude-analyses.sav" in [c.value for c in app.sidebar.caption]
    app.sidebar.button(key="project-title-clear").click().run()
    assert load_project(carnet).title is None
    assert app.sidebar.title[0].value == "etude-analyses.sav"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_changed_elsewhere_the_title_is_not_written(carnet):
    app = _open(carnet)
    data = json.loads(carnet.read_text(encoding="utf-8"))
    data["dataset"]["description"] = "Écrit par une autre personne."
    carnet.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    app.sidebar.text_input(key="project-title").input(TITLE)
    app.sidebar.button(key="project-title-save").click().run()
    assert not app.exception, app.exception
    found = load_project(carnet)
    assert found.title is None and found.dataset.description == "Écrit par une autre personne."
    assert any("modifié ailleurs" in w.value for w in app.warning)
