"""v0.6, step 3: "no question" proposed by the computation, on strong evidence (D-039)."""

import json

import pytest

from ddict import bench
from ddict.llm.link import build_link_blocks
from ddict.questionnaire import link

NOT_ASKED_WITH_CANDIDATES = {
    "etude-sommeil": {"date_passation", "id_participant"},
    "enquete-familles": {"date_reponse", "id_famille", "stress_total"},
    "sleep-study": {"date_completed", "participant_id"},
}


@pytest.fixture(scope="module")
def bases():
    return {
        base["name"]: (bench._project(bench.data_dir(), base), base["links"])
        for base in bench.load_key()["bases"]
    }


@pytest.mark.parametrize("name", sorted(NOT_ASKED_WITH_CANDIDATES))
def test_none_first_exactly_where_there_is_no_question(bases, name):
    project, key = bases[name]
    found = link.candidates(project)
    first_none = {n for n, ids in found.items() if ids and ids[0] == link.NO_QUESTION}
    assert first_none == NOT_ASKED_WITH_CANDIDATES[name]
    # No variable that has a question loses it at the top.
    assert all(key[n] == link.NO_QUESTION for n in first_none)


def test_reasons(bases):
    project, _key = bases["enquete-familles"]
    assert link.no_question_reason(project.variable("id_famille")) == "identifier"
    assert link.no_question_reason(project.variable("date_reponse")) == "completion_date"
    assert link.no_question_reason(project.variable("stress_total")) == "computed_score"
    sleep, _key = bases["etude-sommeil"]
    assert link.no_question_reason(sleep.variable("courriel")) is None  # an e-mail is asked
    assert link.no_question_reason(sleep.variable("date_naissance")) is None  # a lifetime
    assert link.no_question_reason(sleep.variable("sommeil_q1")) is None


def test_the_sum_of_a_group_is_found_when_profiling(bases):
    project, _key = bases["enquete-familles"]
    sums = {e.name: e.profile.sum_of_group for e in project.variables if e.profile.sum_of_group}
    stress = next(g.group_id for g in project.groups if "stress_1" in (g.members.value or []))
    assert sums == {"stress_total": stress}


def test_the_model_sees_none_first(bases):
    project, _key = bases["etude-sommeil"]
    sent = {
        v["name"]: v
        for b in build_link_blocks(project, size=40)
        for v in json.loads(b.messages[1]["content"])["variables"]
    }
    assert sent["id_participant"]["candidates"][0] == {
        "id": "aucune",
        "question": "(identifiant)",
        "computed": "sure",
    }
    assert (
        sent["date_passation"]["candidates"][0]["question"] == "(date de passation ou de réponse)"
    )
    english, _key = bases["sleep-study"]
    sent = {
        v["name"]: v
        for b in build_link_blocks(english, size=40)
        for v in json.loads(b.messages[1]["content"])["variables"]
    }
    assert sent["participant_id"]["candidates"][0] == {
        "id": "none",
        "question": "(identifier)",
        "computed": "sure",
    }


def test_best_guess_is_none(bases):
    project, _key = bases["sleep-study"]
    assert link.best_guess(project)["date_completed"] == link.NO_QUESTION
