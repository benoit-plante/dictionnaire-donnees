"""v0.3, step 3: the Base and Questionnaire pages, and the dashboard of what waits."""

import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ddict import glossary
from ddict.io import ReadError
from ddict.project import load_project
from ddict.project.model import TrackedValue
from ddict.workflow import QuestionnaireExists, add_questionnaire, profile_database, tasks

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")


@pytest.fixture
def folder(fictional_files, tmp_path):
    for name in ("etude-sommeil.sav", "questionnaire-sommeil.pdf", "questionnaire-sommeil.txt"):
        shutil.copy(fictional_files[name], tmp_path / name)
    return tmp_path


def _texts(found):
    return [t.text.format(n=t.count) for t in found]


# --- Without the interface. ---


def test_tasks_follow_the_recommended_order(folder):
    project, _path = profile_database(folder / "etude-sommeil.sav")
    # ANX and TCC are capitals in the file's labels: acronyms to define, even without it.
    assert _texts(tasks(project)) == [
        "Ajouter le questionnaire de l'étude",
        "Sigles sans définition : 2",
        "Codes suspects à confirmer : 3",  # age 999, sommeil_q3 9, nb_reveils -9
        "Niveaux de mesure proposés : 1",  # langue_maison: text declared "scale" (v0.8)
    ]
    add_questionnaire(project, folder / "questionnaire-sommeil.pdf")
    assert _texts(tasks(project)) == [
        "Sigles à valider : 3",
        "Sigles sans définition : 1",
        "Variables sans question : 34",
        "Codes suspects à confirmer : 3",
        "Niveaux de mesure proposés : 1",
    ]
    project.variable("age").question = TrackedValue[str](
        value="Q3", origin="ai", status="proposed", ai_run="run-0001"
    )
    project.variable("age").label = TrackedValue[str](
        value="Âge", origin="ai", status="proposed", ai_run="run-0002"
    )
    for item in list(project.glossary):
        glossary.decide(project, item.term, "accept", now="2026-10-14T12:00:00")
    glossary.write(project, "ANX", "anxiété", now="2026-10-14T12:00:00")
    found = tasks(project)
    assert _texts(found) == [
        "Rattachements proposés à réviser : 1",
        "Variables sans question : 33",
        "Codes suspects à confirmer : 3",
        "Niveaux de mesure proposés : 1",
        "Libellés ou descriptions proposés : 1",
    ]
    assert (found[1].mode, found[1].filter) == ("variables", "unlinked")


def test_add_questionnaire(folder):
    project, _path = profile_database(folder / "etude-sommeil.sav")
    assert add_questionnaire(project, folder / "questionnaire-sommeil.pdf") == 0
    with pytest.raises(QuestionnaireExists):
        add_questionnaire(project, folder / "questionnaire-sommeil.txt")
    project.variable("age").question = TrackedValue[str](value="Q3", origin="human")
    assert add_questionnaire(project, folder / "questionnaire-sommeil.txt", replace=True) == 1
    broken = folder / "abime.pdf"
    broken.write_bytes(b"not a pdf")
    with pytest.raises(ReadError):
        add_questionnaire(project, broken, replace=True)


# --- In the interface: from the home page to the glossary, without any command. ---


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_from_home_to_glossary(folder):
    app = AppTest.from_file(APP, default_timeout=30)
    app.session_state["project_path"] = ""
    app.run()
    app.text_input(key="home-database").input(str(folder / "etude-sommeil.sav")).run()
    app.button(key="home-create").click().run()
    assert not app.exception, app.exception

    # The project opens on its database.
    assert app.header[0].value == "etude-sommeil.sav — Etude sommeil (fictive)"
    assert [m.value for m in app.metric][:2] == ["34", "200"]
    assert app.sidebar.button(key="task-0").label == "Ajouter le questionnaire de l'étude"

    app.sidebar.button(key="task-0").click().run()
    assert app.header[0].value == "Questionnaire de l'étude"
    app.text_input(key="questionnaire-path").input(str(folder / "questionnaire-sommeil.pdf"))
    app.button(key="questionnaire-read").click().run()
    assert not app.exception, app.exception
    assert any("14 questions" in m.value for m in app.markdown)
    assert any("Q7 (titres de colonnes collés)" in w.value for w in app.warning)
    assert any("à valider : QFS, EFA, TCC" in i.value for i in app.info)
    assert app.sidebar.button(key="task-0").label == "Sigles à valider : 3"

    app.sidebar.button(key="task-0").click().run()
    assert app.header[0].value == "Glossaire des sigles"
    app.button(key="accept-glossary-TCC").click().run()
    project = load_project(folder / "etude-sommeil.dd.json")
    assert project.questionnaire.file_name == "questionnaire-sommeil.pdf"
    assert glossary.entry(project, "TCC").status == "validated"
    assert app.sidebar.button(key="task-0").label == "Sigles à valider : 2"


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_questionnaire_problems_and_replacement(folder):
    _project, path = profile_database(folder / "etude-sommeil.sav")
    app = AppTest.from_file(APP, default_timeout=30)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "questionnaire"
    app.run()
    app.button(key="questionnaire-read").click().run()
    assert "Choisissez d'abord le fichier" in app.error[0].value
    broken = folder / "abime.pdf"
    broken.write_bytes(b"not a pdf")
    app.text_input(key="questionnaire-path").input(str(broken))
    app.button(key="questionnaire-read").click().run()
    assert "Impossible de lire le questionnaire" in app.error[0].value

    app.text_input(key="questionnaire-path").input(str(folder / "questionnaire-sommeil.pdf"))
    app.button(key="questionnaire-read").click().run()
    assert app.success[0].value == "Questionnaire lu."
    app.text_input(key="questionnaire-path").input(str(folder / "questionnaire-sommeil.txt"))
    app.button(key="questionnaire-read").click().run()  # now "Remplacer le questionnaire"
    assert not app.exception, app.exception
    assert load_project(path).questionnaire.file_name == "questionnaire-sommeil.txt"
