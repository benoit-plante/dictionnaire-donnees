"""Plan-accueil, step C3 (D-160): "Mes projets" — the followed projects listed in the sidebar,
the latest changed first; a click shows a project's detail without opening it; "Ouvrir"
and each task open it where something waits; "Ouvrir le dossier"; "Ne plus suivre"; back
from a project, its detail; the recent projects under "Ouvrir un projet", without those
followed. On the projects of `projets_stades`."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import projets_stades as stages
from accueil import tab
from ddict import overview, recents, tracked
from ddict.review.ui import home_view

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")


@pytest.fixture(scope="module")
def made(tmp_path_factory):
    return stages.make(tmp_path_factory.mktemp("stades"))


@pytest.fixture(autouse=True)
def fresh():
    overview.clear_cache()


def _home() -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = ""
    app.run()
    assert not app.exception, app.exception
    return app


def _listed(app) -> list[str]:
    """The names in the sidebar's list, without their phase."""
    return [
        b.label.split("  \n")[0]
        for b in app.sidebar.button
        if (b.key or "").startswith("home-project-")
    ]


def _texts(app) -> list[str]:
    return [m.value for m in app.markdown]


def _show(app, made, stage) -> AppTest:
    """Click the project of `stage` in the list."""
    index = next(i for i, r in enumerate(overview.rows(tracked.load()))
                 if r.path == made[stage])  # fmt: skip
    app.sidebar.button(key=f"home-project-{index}").click().run()
    assert not app.exception, app.exception
    return app


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_without_a_project_followed_a_sentence_and_no_list():
    app = _home()
    assert app.title[0].value == "Mes projets"
    assert any("Aucun projet suivi" in m for m in _texts(app))
    assert _listed(app) == []


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_list_in_the_sidebar_latest_first(made):
    for path in made.values():
        tracked.follow(path)
    app = _home()
    expected = overview.rows(list(made.values()))
    assert _listed(app) == [r.name for r in expected]
    labels = [b.label for b in app.sidebar.button if (b.key or "").startswith("home-project-")]
    assert labels[-1].endswith("\nIntrouvable")  # not found: last, without a date
    assert any(label.endswith("\nVersion plus récente") for label in labels)
    assert any(label.endswith("\nIllisible") for label in labels)
    shown = app.sidebar.button(key="home-project-0")
    assert shown.proto.type == "primary"  # the latest changed is shown first
    assert app.subheader[0].value == expected[0].name
    assert [b.key for b in app.sidebar.button][-1] == "quit"  # "Quitter" under the list


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_click_shows_the_detail_without_opening(made):
    tracked.follow(made["carnet"])
    tracked.follow(made["moitie"])
    app = _show(_home(), made, "carnet")
    assert app.session_state["project_path"] == ""  # not opened
    texts = _texts(app)
    assert home_view.SEPARATOR.join(["Documenter", "**Analyser**", "Rédiger"]) in texts
    assert "2 retenues · 1 à confirmer · 1 à recalculer" in texts
    assert "etude-analyses.sav — trouvée à côté du projet" in texts
    assert app.get("progress")[0].proto.value == round(overview.row(made["carnet"]).codebook * 100)
    files = next(m for m in texts if m.startswith("- "))
    assert "etude-analyses-carnet.json" in files


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_detail_of_a_designed_project(made):
    tracked.follow(made["concu"])
    app = _home()
    texts = _texts(app)
    phases = ["**Concevoir**", "En collecte", "Documenter", "Analyser", "Rédiger"]
    assert home_view.SEPARATOR.join(phases) in texts
    assert "Pas encore : le questionnaire est en conception." in texts
    assert any(t.startswith("Conçu dans l'outil : ") for t in texts)
    assert "Pas encore de carnet" in texts


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_detail_of_a_project_not_found(made):
    tracked.follow(made["introuvable"])
    app = _home()
    assert app.warning[0].value == "Introuvable : le fichier n'est plus à cet endroit."
    assert app.button(key="home-find").label == "Le retrouver…"
    assert not [b for b in app.button if b.key in ("home-open-chosen", "home-folder")]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_ouvrir_opens_the_project_on_its_first_task(made):
    tracked.follow(made["moitie"])
    tracked.follow(made["neuf"])
    app = _show(_home(), made, "moitie")
    app.button(key="home-open-chosen").click().run()
    assert not app.exception, app.exception
    assert app.session_state["project_path"] == str(made["moitie"])
    assert app.session_state["mode"] == "glossary"  # "Sigles à valider : 3"
    assert app.sidebar.title[0].value == "etude-sommeil.sav"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_each_task_opens_its_page(made):
    tracked.follow(made["moitie"])
    row = overview.row(made["moitie"])
    assert len(row.tasks) > 1
    app = _home()
    assert [b.label for b in app.button if (b.key or "").startswith("home-task-")] == [
        t.text.format(n=t.count) for t in row.tasks
    ]
    app.button(key="home-task-1").click().run()
    assert not app.exception, app.exception
    assert app.session_state["project_path"] == str(made["moitie"])
    assert app.session_state["mode"] == row.tasks[1].mode


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_ouvrir_le_dossier(made, monkeypatch):
    opened = []
    monkeypatch.setattr(home_view.os, "startfile", opened.append, raising=False)
    tracked.follow(made["neuf"])
    app = _home()
    app.button(key="home-folder").click().run()
    assert opened == [made["neuf"].parent]
    assert app.title[0].value == "Mes projets"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_no_longer_followed_from_the_detail(made):
    tracked.follow(made["neuf"])
    before = made["neuf"].read_bytes()
    app = _home()
    app.button(key="home-unfollow").click().run()
    assert not app.exception, app.exception
    assert tracked.load() == []
    assert _listed(app) == []
    assert any("n'est plus suivi" in s.value for s in app.success)
    assert made["neuf"].read_bytes() == before


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_back_from_a_project_shows_it(made):
    tracked.follow(made["moitie"])
    tracked.follow(made["neuf"])
    app = _show(_home(), made, "neuf")
    app.button(key="home-open-chosen").click().run()
    app.sidebar.button(key="home").click().run()  # "Accueil"
    assert not app.exception, app.exception
    assert app.title[0].value == "Mes projets"
    assert app.session_state[home_view.CHOSEN] == str(made["neuf"])


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_recent_projects_without_those_followed(made):
    recents.add(made["neuf"])
    recents.add(made["plan"])
    tracked.follow(made["plan"])
    app = tab(_home(), "ouvrir")  # D-160: under "Ouvrir un projet"
    recent = [b.label for b in app.button if (b.key or "").startswith("home-recent-")]
    assert recent == ["etude-sommeil.dd.json"]
    app.button(key="home-follow-0").click().run()  # followed: into the list
    assert [b for b in app.button if (b.key or "").startswith("home-recent-")] == []
    tab(app, "projets")
    assert sorted(_listed(app)) == ["etude-analyses", "etude-sommeil"]
