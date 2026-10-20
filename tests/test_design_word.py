"""v0.20, step E1: the designed questionnaire in Word (D-152), in two versions, and the page
"Publier" with its preview. The same questionnaire gives the same bytes; the version for the
ethics committee has no name, no code and no provenance; a file open in Word is refused,
never left half written. Fictional projects only."""

import io
import zipfile
from datetime import date
from pathlib import Path

import pytest
from docx import Document
from streamlit.testing.v1 import AppTest

from ddict import design, design_word, i18n
from ddict.cli import EXIT_ERROR, main
from ddict.design import Draft, Item
from ddict.project import save_project
from ddict.project.model import Publication, SourcedText
from ddict.review.ui.publish_view import NAMES
from projet_concu import project as designed

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")


def _text(project, which) -> str:
    return design_word.read_text(design_word.render(project, which))


def _sent(project, kind="ethics", day="2026-10-20"):
    found = design.questionnaire(project)
    project.design.publications.append(
        Publication(kind=kind, date=day, fingerprint=found.sha256,
                    questionnaire=found.model_copy(deep=True))
    )  # fmt: skip


# --- The file ---------------------------------------------------------------------------------


@pytest.mark.parametrize("which", design_word.VERSIONS)
def test_the_same_questionnaire_gives_the_same_bytes(which):
    project = designed()
    project.design.changed = "2026-11-02"
    first = design_word.render(project, which)
    assert design_word.render(project, which) == first
    again = designed()
    again.design.changed = "2026-11-02"
    assert design_word.render(again, which) == first
    with zipfile.ZipFile(io.BytesIO(first)) as archive:
        assert {e.date_time for e in archive.infolist()} == {(2026, 11, 2, 0, 0, 0)}
    properties = Document(io.BytesIO(first)).core_properties
    assert properties.created.date().isoformat() == "2026-11-02"
    assert properties.modified == properties.created and properties.revision == 1


def test_the_version_for_the_ethics_committee():
    project = designed()
    text = _text(project, "ethics")
    assert "1. Quel est votre genre ? *" in text
    assert "* Réponse obligatoire." in text
    assert "○ Préfère ne pas répondre" in text and "☐ La musique" in text
    assert "☐ Autre : ____" in text
    assert "____________________ (nombre)" in text
    assert "Les questions suivantes portent sur votre sommeil." in text  # displayed, no number
    assert "3. Au cours du dernier mois, à quelle fréquence…" in text
    assert "avez-vous bien dormi ?" in text and "Jamais" in text
    # No name, no code, no provenance.
    for word in ("[", "SQ00", "Q4_", "LimeSurvey", "Provenance", "manuel", "Variables",
                 "Points de relecture", "Code"):  # fmt: skip
        assert word not in text, word
    assert "version 1 du" in text and design.questionnaire(project).sha256[:12] in text


def test_the_working_version():
    project = designed()
    group = next(g for g in project.groups if g.question == "Q4")
    group.reverse_items = ["Q4_SQ002"]
    group.instrument_name = SourcedText(value="Échelle fictive du sommeil",
                                        source="Manuel fictif, p. 2")  # fmt: skip
    text = _text(project, "working")
    assert "○ [9] Préfère ne pas répondre" in text
    assert "Q1 — Code : Q1 — choix unique — type LimeSurvey L — obligatoire" in text
    assert "Q2 — Code : Q2 — ouverte (nombre) — type LimeSurvey N" in text
    assert "Variables : Q4_SQ001, Q4_SQ002, Q4_SQ003" in text
    assert "[SQ002] avez-vous bien dormi ? (inversé)" in text
    assert "[SQ001] vous êtes-vous réveillé·e la nuit ?\n" in text  # not reversed
    assert "Provenance : source : Échelle fictive du sommeil, manuel, p. 2" in text
    assert "instrument : Échelle fictive du sommeil (Manuel fictif, p. 2)" in text
    assert "Points de relecture" in text
    assert "question 3 : Le code de la question n'est pas décidé" in text


def test_the_working_version_shows_no_code_where_limesurvey_has_none():
    # Seen in the author's trial (2026-10-20): "[4] Autre", a code no export ever holds.
    project = designed()
    other = next(o for q in project.questionnaire.questions for o in q.options if o.other)
    other.code = "4"
    text = _text(project, "working")
    assert "☐ Autre : ____" in text and "[4] Autre" not in text
    assert "Variable : Q3 (toujours vide)" in text  # the display text's empty column


def test_a_kept_point_is_said_kept():
    from ddict import design_points

    project = designed()
    point = design_points.points(project)[0]
    design_points.keep(project, point, "2026-10-19T10:00:00")
    assert "(gardé tel quel)" in _text(project, "working")


def test_the_version_and_the_day_of_the_last_change():
    project = designed()
    project.design.changed = "2026-10-19"
    assert design_word.version(project) == (1, "2026-10-19")
    _sent(project)
    assert design_word.version(project)[0] == 1  # the version sent
    _sent(project, "limesurvey")
    assert design_word.version(project)[0] == 1  # the same content, sent twice
    design.add_question(project, Draft(kind="open", text="Un commentaire ?", section="S2"))
    assert design_word.version(project)[0] == 2
    assert project.design.changed == date.today().isoformat()
    # A change that changes nothing keeps the day.
    project.design.changed = "2026-10-21"
    design.modify_section(project, "S1", "Vous")
    assert project.design.changed == "2026-10-21"


def test_the_study_language_and_the_interface_language():
    project = design.new_project("Sleep study", "en", "2026-10-19")
    design.add_question(
        project,
        Draft(kind="single", text="Do you sleep well?", section="S1", required=True,
              options=(Item("Yes", "1"), Item("No", "2"))),
    )  # fmt: skip
    with i18n.using("fr"):
        ethics = _text(project, "ethics")
        working = _text(project, "working")
    assert "* Required answer." in ethics and "1. Do you sleep well? *" in ethics
    assert "Sleep study" in ethics and "version 1 of" in ethics
    assert "choix unique — type LimeSurvey L — obligatoire" in working  # the tool's words


def test_a_file_open_in_word_is_refused(tmp_path, monkeypatch):
    project = designed()
    path = design_word.write(project, "ethics", tmp_path)
    assert path.name == "Étude du sommeil (conception) - comité.docx"
    before = path.read_bytes()

    def held(self, target):
        raise PermissionError(13, "The process cannot access the file")

    monkeypatch.setattr(Path, "replace", held)
    design.add_question(project, Draft(kind="open", text="Un commentaire ?", section="S2"))
    with pytest.raises(design_word.WordOpen):
        design_word.write(project, "ethics", tmp_path)
    assert path.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == [path.name]  # no temporary file


def test_the_command_line(tmp_path, capsys, monkeypatch):
    path = tmp_path / "Étude conçue.dd.json"
    save_project(designed(), path)
    assert main(["questionnaire", "word", str(path)]) == 0
    out = capsys.readouterr().out
    assert "Word pour le comité d'éthique" in out and "Word de travail" in out
    names = sorted(p.name for p in tmp_path.glob("*.docx"))
    assert names == [
        "Étude du sommeil (conception) - comité.docx",
        "Étude du sommeil (conception) - travail.docx",
    ]

    def held(self, target):
        raise PermissionError(13, "held")

    monkeypatch.setattr(Path, "replace", held)
    assert main(["questionnaire", "word", str(path)]) == EXIT_ERROR
    assert "Fermez Étude du sommeil (conception) - comité.docx dans Word" in (
        capsys.readouterr().err
    )


# --- The page "Publier" -----------------------------------------------------------------------


@pytest.fixture
def design_file(tmp_path):
    path = tmp_path / "Étude conçue.dd.json"
    save_project(designed(), path)
    return path


def _open(path):
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "publish"
    app.run()
    assert not app.exception, app.exception
    return app


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_page_publier(design_file):
    app = _open(design_file)
    assert [h.value for h in app.header] == ["Publier"]
    assert any("Seul LimeSurvey fait foi" in c.value for c in app.caption)
    radio = app.radio(key="publish-Q1")
    assert radio.disabled and radio.options == ["Femme", "Homme", "Autre",
                                                "Préfère ne pas répondre"]  # fmt: skip
    assert app.checkbox(key="publish-Q5-2").label == "Autre : …"
    assert not any("`Q1`" in m.value for m in app.markdown)
    app.toggle(key=NAMES).set_value(True).run()
    assert app.radio(key="publish-Q1").options[0] == "[1] Femme"
    assert any("`Q1`" in r.label for r in app.radio)
