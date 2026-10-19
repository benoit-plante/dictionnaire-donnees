"""v0.6, step 5: the computation's sure choice shown to the model; a disagreement flagged,
never hidden (D-041)."""

import json

import pytest

from ddict import bench
from ddict.llm.link import DISAGREES, LinkChoice, apply_links, build_link_blocks
from ddict.llm.run import BlockResult
from ddict.project.model import AiRun
from ddict.questionnaire import link
from ddict.review import logic

NOW = "2026-10-14T20:00:00"


@pytest.fixture
def project():
    base = next(b for b in bench.load_key()["bases"] if b["name"] == "etude-sommeil")
    return bench._project(bench.data_dir(), base)


def _result(*choices):
    run = AiRun(
        run_id="run-0001",
        block="l-001",
        endpoint="https://ia.universite.example/v1",
        model="m",
        prompt_version="link-v2",
        message_sha256="0" * 64,
        started_at=NOW,
        outcome="succeeded",
    )
    return BlockResult(run, tuple(LinkChoice(name=n, question=q) for n, q in choices))


def test_sure_choices(project):
    sure = link.sure_choices(project)
    assert sure["sommeil_q2"] == "Q7.r2"
    assert "sommeil_q1" not in sure  # not clear enough
    assert sure["date_passation"] == link.NO_QUESTION  # strong evidence (D-039)
    found = link.candidates(project)
    assert all(found[name][0] == target for name, target in sure.items())


def test_the_model_sees_it(project):
    sent = {
        v["name"]: v
        for b in build_link_blocks(project, size=40)
        for v in json.loads(b.messages[1]["content"])["variables"]
    }
    marked = [c["id"] for c in sent["sommeil_q2"]["candidates"] if c.get("computed") == "sure"]
    assert marked == ["Q7.r2"]
    assert not any(c.get("computed") for c in sent["sommeil_q1"]["candidates"])


def test_a_disagreement_is_kept_and_flagged(project):
    apply_links(project, _result(("sommeil_q2", "Q7.r3"), ("sommeil_q4", "Q7.r4")))
    first, second = project.variable("sommeil_q2"), project.variable("sommeil_q4")
    assert first.question.value == "Q7.r3"  # never replaced in silence
    assert DISAGREES in first.ai_signals
    assert DISAGREES not in second.ai_signals  # it agrees
    assert any("choix sûr du calcul" in text for text in logic.signal_texts(first))
    # A person's decision settles the signal.
    logic.link_question(project, "sommeil_q2", "Q7.r2", now=NOW)
    assert DISAGREES not in project.variable("sommeil_q2").ai_signals


def test_none_against_a_sure_none(project):
    apply_links(project, _result(("date_passation", "Q2")))
    assert DISAGREES in project.variable("date_passation").ai_signals
    apply_links(project, _result(("id_participant", "aucune")))
    assert DISAGREES not in project.variable("id_participant").ai_signals
