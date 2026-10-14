"""v0.2, step 3: the glossary of acronyms, from the questionnaire or the team, never the AI."""

from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError
from streamlit.testing.v1 import AppTest

from ddict import glossary
from ddict.cli import main
from ddict.io import read_sav
from ddict.llm.client import LocalModelClient
from ddict.llm.enrich import enrich
from ddict.llm.schemas import VariableProposal
from ddict.project import build_project, load_project, save_project
from ddict.project.model import GlossaryEntry
from ddict.questionnaire import load_questionnaire

NOW = "2026-10-13T22:00:00"
APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")


@pytest.fixture
def project(fictional_files):
    project = build_project(read_sav(fictional_files["etude-sommeil.sav"]))
    project.questionnaire = load_questionnaire(fictional_files["questionnaire-sommeil.pdf"])
    return project


@pytest.mark.parametrize("name", ["questionnaire-sommeil.pdf", "questionnaire-sommeil.txt"])
def test_acronyms_defined_in_the_questionnaire(fictional_files, generator, name):
    found = glossary.find_definitions(load_questionnaire(fictional_files[name]))
    expected = generator.QUESTIONNAIRE_TRAPS["defined_acronyms"]
    assert {term: meaning for term, meaning, _page in found} == {
        "QFS": expected["QFS"],
        "EFA": expected["EFA"],
        "TCC": expected["TCC"],
    }


@pytest.mark.parametrize(
    ("text", "term", "meaning"),
    [
        ("les organismes communautaires Famille", "OCF", "organismes communautaires Famille"),
        ("du Ministère de la Famille", "MF", "Ministère de la Famille"),
        ("une thérapie cognitivo-comportementale", "TCC", "thérapie cognitivo-comportementale"),
        ("et l'Échelle fictive d'anxiété", "EFA", "Échelle fictive d'anxiété"),
        ("du Centre Jeunesse", "DPJ", None),  # initials do not spell it
        ("une date", "JJ", None),
    ],
)
def test_long_form(text, term, meaning):
    assert glossary.long_form(text, term) == meaning


def test_proposals_wait_for_a_person(project):
    added = glossary.propose_from_questionnaire(project)
    assert [e.term for e in added] == ["QFS", "EFA", "TCC"]
    tcc = glossary.entry(project, "tcc")
    assert (tcc.origin, tcc.status, tcc.source) == (
        "questionnaire",
        "proposed",
        "questionnaire-sommeil.pdf, p. 3",
    )
    assert not glossary.is_accepted(tcc)
    assert glossary.variables_using(project, "TCC") == ["aide_tcc"]


def test_acronyms_in_names(project, generator):
    found = glossary.name_acronyms(project)
    assert found["tcc"] == ["aide_tcc"]
    assert found["anx"] == generator.ANXIETY_ITEMS  # "ANX" in the file labels
    assert "cm" not in found and "nb" not in found  # units and abbreviations
    glossary.propose_from_questionnaire(project)
    assert set(glossary.undefined_acronyms(project)) == {"anx"}


def test_decisions(project):
    glossary.propose_from_questionnaire(project)
    glossary.decide(project, "QFS", "accept", now=NOW)
    glossary.decide(project, "EFA", "reject", now=NOW)
    glossary.write(project, "TCC", "Thérapie cognitivo-comportementale", now=NOW)
    glossary.write(project, "ANX", "Anxiété (échelle fictive)", now=NOW)
    states = {e.term: (e.origin, e.status, e.proposed_meaning) for e in project.glossary}
    assert states == {
        "QFS": ("questionnaire", "validated", None),
        "EFA": ("questionnaire", "rejected", None),
        "TCC": ("questionnaire", "corrected", "thérapie cognitivo-comportementale"),
        "ANX": ("human", "none", None),
    }
    assert [glossary.is_accepted(e) for e in project.glossary] == [True, False, True, True]
    glossary.write(project, "anx", "", now=NOW)  # the team's own entry: removed
    assert glossary.entry(project, "ANX") is None
    with pytest.raises(glossary.GlossaryError):
        glossary.write(project, "TCC", "  ", now=NOW)


def test_new_reading_keeps_decisions_and_drops_stale_proposals(project, fictional_files):
    glossary.propose_from_questionnaire(project)
    glossary.decide(project, "QFS", "accept", now=NOW)
    project.questionnaire.texts = []  # QFS and EFA were defined in paragraphs only
    glossary.propose_from_questionnaire(project)
    assert [(e.term, e.status) for e in project.glossary] == [
        ("QFS", "validated"),
        ("TCC", "proposed"),
    ]


# --- D-015: the model never defines an acronym. ---


def test_no_ai_origin_for_an_entry():
    with pytest.raises(ValidationError):
        GlossaryEntry(term="OCF", meaning="offices de contrôle", origin="ai", status="proposed")
    with pytest.raises(ValidationError):  # a person's entry does not wait for a decision
        GlossaryEntry(term="OCF", meaning="x", origin="human", status="proposed")


def test_model_answers_have_no_field_for_acronyms():
    assert set(VariableProposal.model_fields) == {"name", "label", "description"}


def test_enrichment_leaves_the_glossary_alone(project):
    glossary.propose_from_questionnaire(project)
    before = [e.model_dump() for e in project.glossary]

    def server(request):
        import json

        content = json.loads(json.loads(request.content)["messages"][1]["content"])
        answer = {
            "block": content["block"],
            "variables": [
                {"name": v["name"], "label": "OCF : offices de contrôle", "description": ""}
                for v in content["variables"]
            ],
        }
        text = json.dumps(answer, ensure_ascii=False)
        return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})

    client = LocalModelClient("m", transport=httpx.MockTransport(server))
    list(enrich(project, client, now=lambda: NOW, block_size=12))
    assert [e.model_dump() for e in project.glossary] == before


# --- Command line and interface. ---


def test_questionnaire_command_reports_acronyms(fictional_files, tmp_path, capsys):
    path = tmp_path / "etude.dd.json"
    main(["profiler", str(fictional_files["etude-sommeil.sav"]), "-o", str(path)])
    capsys.readouterr()
    main(["questionnaire", str(path), str(fictional_files["questionnaire-sommeil.pdf"])])
    out = capsys.readouterr().out
    assert "à valider : QFS, EFA, TCC" in out
    assert "sans définition : anx" in out
    assert [e.term for e in load_project(path).glossary] == ["QFS", "EFA", "TCC"]


@pytest.fixture
def app(project, tmp_path):
    glossary.propose_from_questionnaire(project)
    path = tmp_path / "etude.dd.json"
    save_project(project, path)
    test = AppTest.from_file(APP, default_timeout=30)
    test.session_state["project_path"] = str(path)
    test.run()
    test.sidebar.radio(key="mode").set_value("glossary").run()
    assert not test.exception, test.exception
    return test, path


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_glossary_view(app):
    test, path = app
    assert test.header[0].value == "Glossaire des sigles"
    test.button(key="accept-glossary-TCC").click().run()
    assert glossary.entry(load_project(path), "TCC").status == "validated"
    test.text_input(key="glossary-new-term").input("ANX")
    test.text_input(key="glossary-new-meaning").input("Anxiété")
    test.button(key="glossary-add").click().run()
    added = glossary.entry(load_project(path), "ANX")
    assert (added.meaning, added.origin) == ("Anxiété", "human")
    assert test.text_input(key="glossary-new-term").value == ""  # ready for the next one
    assert not any("ANX" in m.value for m in test.markdown if "sans définition" in m.value)
