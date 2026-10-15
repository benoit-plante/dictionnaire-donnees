"""v0.6, step 4: neighbour questions for a variable without candidates (D-040)."""

import json

import pytest

from ddict import bench
from ddict.llm.link import LINK_PROMPT_VERSION, NEIGHBOUR_PROMPT_VERSION, build_link_blocks
from ddict.llm.messages import system_prompt
from ddict.questionnaire import link


@pytest.fixture(scope="module")
def english():
    base = next(b for b in bench.load_key()["bases"] if b["name"] == "sleep-study")
    return bench._project(bench.data_dir(), base), base["links"]


def test_neighbours_hold_the_right_question(english):
    project, key = english
    near = link.neighbours(project)
    assert set(near) == {"age", "n_awakenings"}
    assert key["age"] in near["age"] and key["n_awakenings"] in near["n_awakenings"]
    assert all(len(ids) <= link.MAX_NEIGHBOURS for ids in near.values())
    # Not for a constant or empty variable, and never for one that has candidates.
    found = link.candidates(project)
    assert not set(near) & {n for n, ids in found.items() if ids}
    assert "wave" not in near and "q_removed" not in near


def test_the_computation_alone_does_not_choose_among_neighbours(english):
    project, _key = english
    assert link.best_guess(project)["age"] == link.NO_QUESTION


def test_the_model_sees_them_marked(english):
    project, _key = english
    sent = {
        v["name"]: v
        for b in build_link_blocks(project, size=40)
        for v in json.loads(b.messages[1]["content"])["variables"]
    }
    assert [c["id"] for c in sent["age"]["candidates"]] == link.neighbours(project)["age"]
    assert all(c.get("neighbour") is True for c in sent["age"]["candidates"])
    assert not any("neighbour" in c for c in sent["gender"]["candidates"])


@pytest.mark.parametrize(("language", "word"), [("fr", "« neighbour »"), ("en", '"neighbour"')])
def test_the_instructions_explain_them(language, word):
    assert (LINK_PROMPT_VERSION, NEIGHBOUR_PROMPT_VERSION) == ("link-v2", "link-v3")
    assert word in system_prompt(NEIGHBOUR_PROMPT_VERSION, language)
    assert word not in system_prompt(LINK_PROMPT_VERSION, language)


def test_in_blocks_of_their_own(english):
    """The rule about neighbours, given to every variable, led the model astray elsewhere."""
    project, _key = english
    blocks = build_link_blocks(project, size=6)
    near = [b for b in blocks if b.prompt_version == "link-v3.en"]
    assert [n for b in near for n in b.names] == ["age", "n_awakenings"]
    assert all(b.prompt_version == "link-v2.en" for b in blocks if b not in near)
    assert blocks[-1] is near[-1]  # after the other blocks
