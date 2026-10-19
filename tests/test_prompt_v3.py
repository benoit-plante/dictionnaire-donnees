"""v0.2, step 5: prompt variables-v3 — the accepted question and glossary go to the model."""

import json

import httpx
import pytest

from ddict import glossary
from ddict.io import read_database
from ddict.llm.client import LocalModelClient
from ddict.llm.enrich import enrich
from ddict.llm.messages import PROMPT_VERSION, build_blocks, system_prompt
from ddict.llm.validate import invention_signals
from ddict.project import build_project
from ddict.project.model import TrackedValue
from ddict.questionnaire import load_questionnaire
from ddict.review import logic

NOW = "2026-10-14T14:00:00"


@pytest.fixture
def project(fictional_files):
    project = build_project(read_database(fictional_files["etude-sommeil.csv"]))
    project.questionnaire = load_questionnaire(fictional_files["questionnaire-sommeil.pdf"])
    glossary.propose_from_questionnaire(project)
    return project


def _contents(project, **kwargs) -> list[dict]:
    return [json.loads(b.messages[1]["content"]) for b in build_blocks(project, **kwargs)]


def _payloads(project, **kwargs) -> dict[str, dict]:
    return {v["name"]: v for c in _contents(project, **kwargs) for v in c["variables"]}


def test_accepted_link_sends_the_exact_question(project):
    logic.link_question(project, "sommeil_q7", "Q7.r7", now=NOW)
    question = _payloads(project)["sommeil_q7"]["question"]
    assert question["item"] == "J'évite les écrans dans l'heure qui précède le coucher."
    assert question["text"].startswith("Au cours du dernier mois")


def test_proposed_or_empty_links_send_nothing(project):
    project.variable("age").question = TrackedValue[str](
        value="Q3", origin="ai", status="proposed", ai_run="run-0001"
    )
    logic.link_question(project, "vague", "none", now=NOW)
    payloads = _payloads(project)
    assert "question" not in payloads["age"]  # may be wrong until a person accepts it
    assert "question" not in payloads["vague"]
    assert "question" not in payloads["genre"]


def test_glossary_holds_accepted_acronyms_of_the_block_only(project):
    glossary.decide(project, "TCC", "accept", now=NOW)
    glossary.decide(project, "QFS", "accept", now=NOW)  # in no name of the base
    glossary.write(project, "ANX", "anxiété", now=NOW)
    # EFA stays proposed: not sent.
    contents = _contents(project)
    with_terms = {c["block"]: c.get("glossary", {}) for c in contents}
    blocks = {v["name"]: c["block"] for c in contents for v in c["variables"]}
    assert with_terms[blocks["aide_tcc"]]["TCC"] == "thérapie cognitivo-comportementale"
    assert with_terms[blocks["anx1"]]["ANX"] == "anxiété"
    sent = json.dumps(contents, ensure_ascii=False)
    assert "QFS" not in sent and "Échelle fictive" not in sent
    assert "glossary" not in contents[0]  # no acronym in id_participant ... sommeil_q1


def test_earlier_prompt_for_trials(project):
    logic.link_question(project, "sommeil_q7", "Q7.r7", now=NOW)
    glossary.write(project, "ANX", "anxiété", now=NOW)
    blocks = build_blocks(project, version="variables-v2")
    assert {b.prompt_version for b in blocks} == {"variables-v2"}
    sent = json.dumps([b.messages[1]["content"] for b in blocks], ensure_ascii=False)
    assert "question" not in sent and "glossary" not in sent
    assert "sources" not in blocks[0].messages[0]["content"].lower()


def test_consent_page_never_sent(project, generator):
    for name in ("courriel", "age", "genre"):
        logic.link_question(project, name, project.questionnaire.questions[0].question_id, now=NOW)
    sent = json.dumps(_contents(project), ensure_ascii=False)
    assert generator.CANARY_CONSENT not in sent
    for canary in generator.CANARIES:
        assert canary not in sent


@pytest.mark.parametrize("version", ["variables-v3", "variables-v4"])
def test_prompt_v3(version):
    """v4 (v0.18) keeps every rule of v3; it only drops the statistics."""
    prompt = system_prompt(version)
    assert PROMPT_VERSION == "variables-v4"
    assert "n'en devine jamais le sens" in prompt
    assert "N'invente jamais le sens des codes" in prompt
    assert "N'invente jamais de seuil clinique" in prompt


@pytest.mark.parametrize(
    ("text", "known", "signals"),
    [
        # Also an instrument named in English (v0.5).
        ("Score CBCL (Child Behavior Checklist)", set(), ("instrument", "acronym")),
        ("Service DPJ (Défenseur des personnes jugées)", set(), ("acronym",)),
        ("Service DPJ (Direction de la protection de la jeunesse)", {"dpj"}, ()),
        ("aide des organismes communautaires Famille (OCF)", set(), ("acronym",)),
        ("aide des organismes communautaires Famille (OCF)", {"ocf"}, ()),
        ("Score CBCL (anxiété)", set(), ()),  # one word: not a definition
        ("Type de service (1 = santé)", set(), ()),
        ("du Centre Jeunesse (DPJ)", set(), ()),  # initials do not spell it
    ],
)
def test_signal_for_an_acronym_defined_outside_the_glossary(text, known, signals):
    assert invention_signals(text, frozenset(known)) == signals


def test_enrichment_flags_an_undefined_acronym(project):
    glossary.decide(project, "TCC", "accept", now=NOW)

    def server(request):
        content = json.loads(json.loads(request.content)["messages"][1]["content"])
        answer = {
            "block": content["block"],
            "variables": [
                {
                    "name": v["name"],
                    "label": "Anxiété",
                    "description": "Item de l'EFA (Échelle fictive d'anxiété)."
                    if v["name"] == "anx1"
                    else "Thérapie cognitivo-comportementale (TCC).",
                }
                for v in content["variables"]
            ],
        }
        text = json.dumps(answer, ensure_ascii=False)
        return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})

    client = LocalModelClient("m", transport=httpx.MockTransport(server))
    list(enrich(project, client, now=lambda: NOW, block_size=8))
    assert "description:acronym" in project.variable("anx1").ai_signals  # EFA not accepted
    assert "description:acronym" not in project.variable("aide_tcc").ai_signals
    assert any(
        "sigle absent du glossaire" in t for t in logic.signal_texts(project.variable("anx1"))
    )
