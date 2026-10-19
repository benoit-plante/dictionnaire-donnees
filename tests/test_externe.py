"""v0.18, step A5: the first real contact with Anthropic (D-139).

Skipped unless DDICT_TESTS_EXTERNES=1 and a key is recorded in Windows' credential manager
(the author types it with `ddict ia cle`; the tests only say whether it is there). Never run
by continuous integration. The network opens to api.anthropic.com only, for these tests
only. Fictional bases only: no participant ever answered them.

What only the real service can say: whether the four schemas sent are accepted (an error
400 does not show against the fake server), with Haiku 5.5 and Sonnet 5.5; and that a fake
key is refused. Each call is small: about ten calls in all, a few cents.

Run (PowerShell, at the root of the repository):
    $env:DDICT_TESTS_EXTERNES = "1"; uv run pytest -m externe -s tests/test_externe.py
"""

import json
import os
import socket
from pathlib import Path

import pytest
from pytest_socket import SocketConnectBlockedError

from ddict import glossary, naming
from ddict.io import read_database
from ddict.llm import build_blocks, keys
from ddict.llm.advise import advice_schema, build_advice_block, parse_advice
from ddict.llm.client import AnthropicClient, ModelCallError
from ddict.llm.defaults import ANTHROPIC_ENDPOINT
from ddict.llm.link import build_link_blocks, link_schema, parse_link_response
from ddict.llm.run import run_block
from ddict.llm.stems import build_stem_blocks, parse_stem_response, stem_schema
from ddict.project import build_project
from ddict.questionnaire import load_questionnaire
from ddict.workflow import add_questionnaire
from test_analysis_data import analyses_project

HOST = "api.anthropic.com"
MODELS = ("claude-haiku-5-5", "claude-sonnet-5-5")
EXAMPLES = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"
NOW = "2026-10-19T12:00:00"

pytestmark = [
    pytest.mark.externe,
    pytest.mark.allow_hosts([HOST]),
    pytest.mark.skipif(
        os.environ.get("DDICT_TESTS_EXTERNES") != "1",
        reason="DDICT_TESTS_EXTERNES=1 non défini : aucun appel réel",
    ),
]


@pytest.fixture
def real_key(memory_keys):
    """The key recorded by the author, read from Windows' credential manager when a request
    leaves; the tests never see its value."""
    keys.use_backend(None)
    if not keys.is_recorded(ANTHROPIC_ENDPOINT):
        pytest.skip("Clé absente : lancez d'abord « uv run ddict ia cle »")
    return keys.reader(ANTHROPIC_ENDPOINT)


def _client(model, key):
    return AnthropicClient(model, key=key, timeout=180)


def _report(usage_name, model, result):
    """Shown with -s: what each call cost, in tokens."""
    tokens = [call.get("usage", {}) for call in result.calls]
    print(f"\n{usage_name} / {model}: {result.run.outcome} {result.run.detail or ''} {tokens}")
    if result.error:  # what the server said, the key erased from it
        print(f"  {result.error}")


@pytest.fixture(scope="module")
def blocks(fictional_files):
    sleep = build_project(read_database(fictional_files["etude-sommeil.sav"]))
    sleep.questionnaire = load_questionnaire(fictional_files["questionnaire-sommeil.pdf"])
    glossary.propose_from_questionnaire(sleep)
    work = build_project(read_database(EXAMPLES / "travail-t2_surveymonkey.sav"))
    add_questionnaire(work, EXAMPLES / "travail-t2_surveymonkey.xlsx")
    naming.propose(work)
    analyses = analyses_project()
    objective = "Les hommes et les femmes dorment-ils aussi bien ?"
    return {
        "libellés": (build_blocks(sleep, size=6)[0], None, None),
        "rattachement": (
            build_link_blocks(sleep, size=6)[0],
            link_schema(),
            parse_link_response,
        ),
        "radicaux": (build_stem_blocks(work, size=4)[0], stem_schema(), parse_stem_response),
        "conseillère": (
            build_advice_block(analyses, objective, "advise-v3"),  # as Anthropic gets it
            advice_schema(analyses, flat=True),  # as `advise` sends it to Anthropic
            parse_advice,
        ),
    }


def test_a_fake_key_is_refused():
    client = _client(MODELS[0], lambda: "sk-ant-FAUSSE-cle-refusee-0000")
    with client, pytest.raises(ModelCallError) as error:
        client.list_models()
    assert error.value.code == "auth"


def test_the_two_models_are_offered(real_key):
    with _client(MODELS[0], real_key) as client:
        offered = client.list_models()
    assert set(MODELS) <= set(offered)


@pytest.mark.parametrize("model", MODELS)
@pytest.mark.parametrize("usage_name", ["libellés", "rattachement", "radicaux", "conseillère"])
def test_the_schemas_sent_are_accepted(real_key, blocks, model, usage_name):
    block, schema, parse = blocks[usage_name]
    options = {"schema": schema, "parse": parse} if schema else {}
    with _client(model, real_key) as client:
        result = run_block(client, block, run_id="externe", now=NOW, **options)
    _report(usage_name, model, result)
    # A refused schema or request would be a 400: the point of this step.
    assert result.run.detail not in {"bad_request", "auth", "http_404"}
    assert result.run.outcome == "succeeded", (result.run.detail, result.answers)
    assert result.calls and result.calls[0]["request_id"]
    json.loads(result.answers[-1])


def test_no_other_host_is_reachable():
    with pytest.raises(SocketConnectBlockedError):
        socket.create_connection(("example.com", 443), timeout=5)
