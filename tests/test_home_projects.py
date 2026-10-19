"""v0.17, step B2 (plan § 7.1): the table "Mes projets" at the top of the home page — the
followed projects, the latest changed first; a click on a name opens the project where
something waits; "Ne plus suivre"; the recent projects below, without those followed. On
the projects of `projets_stades`."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import projets_stades as stages
from ddict import overview, recents, tracked

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


def _names(app) -> list[str]:
    return [b.label for b in app.button if (b.key or "").startswith("home-project-")]


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_without_a_project_followed_a_sentence_and_no_table():
    app = _home()
    assert app.header[0].value == "Mes projets"
    assert any("Aucun projet suivi" in m.value for m in app.markdown)
    assert _names(app) == []


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_table_at_the_top_latest_first(made):
    for path in made.values():
        tracked.follow(path)
    app = _home()
    assert app.header[0].value == "Mes projets"
    expected = overview.rows(list(made.values()))
    assert _names(app) == [r.name for r in expected]
    texts = [m.value for m in app.markdown]
    assert "2 retenues · 1 à confirmer · 1 à recalculer" in texts
    assert "figé, 1 amendement" in texts
    assert "Introuvable : le fichier n'est plus à cet endroit." in texts
    disabled = [b.disabled for b in app.button if (b.key or "").startswith("home-project-")]
    assert disabled == [r.problem is not None for r in expected]
    assert disabled[-1]  # not found: last, without a date


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_a_click_opens_the_project_on_its_first_task(made):
    tracked.follow(made["moitie"])
    tracked.follow(made["neuf"])
    app = _home()
    index = next(i for i, r in enumerate(overview.rows(tracked.load()))
                 if r.path == made["moitie"])  # fmt: skip
    app.button(key=f"home-project-{index}").click().run()
    assert not app.exception, app.exception
    assert app.session_state["project_path"] == str(made["moitie"])
    assert app.session_state["mode"] == "glossary"  # "Sigles à valider : 3"
    assert app.sidebar.title[0].value == "etude-sommeil.sav"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_no_longer_followed_from_the_table(made):
    tracked.follow(made["neuf"])
    before = made["neuf"].read_bytes()
    app = _home()
    app.button(key="home-unfollow-0").click().run()
    assert not app.exception, app.exception
    assert tracked.load() == []
    assert _names(app) == []
    assert any("n'est plus suivi" in s.value for s in app.success)
    assert made["neuf"].read_bytes() == before


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_recent_projects_below_without_those_followed(made):
    recents.add(made["neuf"])
    recents.add(made["plan"])
    tracked.follow(made["plan"])
    app = _home()
    headers = [h.value for h in app.header]
    assert headers.index("Mes projets") < headers.index("Projets récents")
    recent = [b.label for b in app.button if (b.key or "").startswith("home-recent-")]
    assert recent == ["etude-sommeil.dd.json"]
    app.button(key="home-follow-0").click().run()  # followed: into the table
    assert [b for b in app.button if (b.key or "").startswith("home-recent-")] == []
    assert sorted(_names(app)) == ["etude-analyses", "etude-sommeil"]
