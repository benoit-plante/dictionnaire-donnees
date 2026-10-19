"""Step 10: the local model client, tested against a fake server in memory (no network)."""

import json

import httpx
import pytest

from ddict.io import read_sav
from ddict.llm import build_blocks
from ddict.llm.client import (
    DEFAULT_ENDPOINT,
    EndpointRefused,
    LocalModelClient,
    ModelCallError,
    check_local,
)
from ddict.llm.run import MAX_ATTEMPTS, run_block
from ddict.llm.validate import InvalidResponse, invention_signals, parse_block_response
from ddict.project import build_project

NOW = "2026-10-13T15:00:00"


@pytest.fixture(scope="module")
def block(fictional_files):
    project = build_project(read_sav(fictional_files["etude-sommeil.sav"]))
    return build_blocks(project, size=4)[0]


def _good_answer(request_body):
    content = json.loads(request_body["messages"][1]["content"])
    return {
        "block": content["block"],
        "variables": [
            {"name": v["name"], "label": f"Libellé {v['name']}", "description": ""}
            for v in content["variables"]
        ],
    }


class FakeServer:
    """Answers each request with the next scenario: a function of the request body."""

    def __init__(self, *scenarios):
        self.scenarios = list(scenarios)
        self.requests = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        self.requests.append((request, body))
        scenario = self.scenarios.pop(0) if len(self.scenarios) > 1 else self.scenarios[0]
        return scenario(body)


def chat(content):
    """A server answer whose message content is `content` (a dict becomes JSON)."""
    text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
    return lambda body: httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


def good(body):
    return chat(_good_answer(body))(body)


def _client(server):
    return LocalModelClient(
        "modele-test", transport=httpx.MockTransport(server), sleep=lambda seconds: None
    )


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://127.0.0.1:11434/v1",
        "http://localhost:1234/v1/",
        "http://[::1]:8080/v1",
        "http://127.0.0.2:8080",
    ],
)
def test_local_addresses_are_accepted(endpoint):
    assert check_local(endpoint) == endpoint.rstrip("/")


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://192.168.1.10:11434/v1",
        "http://10.0.0.5/v1",
        "https://api.openai.com/v1",
        "http://localhost.example.com/v1",
        "http://127.0.0.1.nip.io/v1",
        "http://user:secret@localhost/v1",
        "file:///etc/passwd",
        "ftp://localhost/v1",
    ],
)
def test_other_addresses_are_refused(endpoint):
    with pytest.raises(EndpointRefused):
        check_local(endpoint)
    with pytest.raises(EndpointRefused):
        LocalModelClient("m", endpoint=endpoint)


def test_default_endpoint_is_ollama_on_this_computer():
    assert check_local(DEFAULT_ENDPOINT) == "http://127.0.0.1:11434/v1"


def test_request_sent_to_the_server(block):
    server = FakeServer(good)
    with _client(server) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    request, body = server.requests[0]
    assert str(request.url) == "http://127.0.0.1:11434/v1/chat/completions"
    assert body["model"] == "modele-test"
    assert body["temperature"] == 0 and body["seed"] == 42 and body["stream"] is False
    assert body["messages"] == list(block.messages)
    schema = body["response_format"]["json_schema"]["schema"]
    assert "VariableProposal" in json.dumps(schema)
    assert result.run.outcome == "succeeded"
    assert [p.name for p in result.proposals] == list(block.names)


def test_proxy_settings_are_ignored(block, monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example.com:3128")
    monkeypatch.setenv("ALL_PROXY", "http://proxy.example.com:3128")
    server = FakeServer(good)
    with _client(server) as client:
        assert client._http._trust_env is False
        run_block(client, block, run_id="run-0001", now=NOW)
    assert server.requests[0][0].url.host == "127.0.0.1"


def test_redirections_are_not_followed(block):
    redirect = lambda body: httpx.Response(  # noqa: E731
        307, headers={"Location": "https://ailleurs.example.com/v1/chat/completions"}
    )
    server = FakeServer(redirect)
    with _client(server) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    assert len(server.requests) == 1
    assert (result.run.outcome, result.run.detail) == ("failed", "http_307")


def test_trace_of_a_successful_run(block):
    with _client(FakeServer(good)) as client:
        run = run_block(client, block, run_id="run-0007", now=NOW).run
    assert run.run_id == "run-0007"
    assert run.block == block.block_id
    assert run.endpoint == "http://127.0.0.1:11434/v1"
    assert run.model == "modele-test"
    assert run.parameters == {"temperature": 0, "seed": 42}
    assert run.prompt_version == "variables-v3"
    assert run.message_sha256 == block.sha256
    assert (run.attempts, run.outcome, run.detail) == (1, "succeeded", None)


def _with(change):
    """A good answer, then modified by `change`."""

    def scenario(body):
        answer = _good_answer(body)
        change(answer)
        return chat(answer)(body)

    return scenario


def _extra_field(answer):
    answer["variables"][0]["seuil_clinique"] = 14


def _invented_variable(answer):
    answer["variables"].append({"name": "variable_inventee", "label": "X", "description": ""})


def _missing_variable(answer):
    answer["variables"].pop()


def _reordered(answer):
    answer["variables"].reverse()


def _other_block(answer):
    answer["block"] = "b-999"


def _too_long(answer):
    answer["variables"][0]["label"] = "x" * 200


def _with_issues(answer):
    answer["variables"][0]["issues"] = ["Le code 9 n'a pas d'étiquette."]


@pytest.mark.parametrize(
    ("scenario", "code"),
    [
        (chat("pas du JSON"), "not_json"),
        (chat(""), "empty_response"),
        (chat({"answer": "?"}), "schema"),
        (_with(_extra_field), "schema"),
        (_with(_too_long), "schema"),
        (_with(_with_issues), "schema"),  # no longer asked (D-009)
        (_with(_invented_variable), "names_mismatch"),
        (_with(_missing_variable), "names_mismatch"),
        (_with(_reordered), "names_mismatch"),
        (_with(_other_block), "block_mismatch"),
    ],
)
def test_invalid_answers_are_refused_whole_and_traced(block, scenario, code):
    server = FakeServer(scenario)
    with _client(server) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    assert result.proposals is None
    assert (result.run.outcome, result.run.detail) == ("invalid_response", code)
    assert result.run.attempts == MAX_ATTEMPTS == len(server.requests)


def test_a_second_try_can_succeed(block):
    server = FakeServer(chat("pas du JSON"), good)
    with _client(server) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    assert (result.run.outcome, result.run.attempts) == ("succeeded", 2)
    assert result.proposals is not None


@pytest.mark.parametrize(
    ("response", "code"),
    [
        (httpx.Response(404, text="model not found"), "http_404"),
        (httpx.Response(500, text="erreur"), "overloaded"),  # after one wait (v0.18)
        (httpx.Response(200, json={"unexpected": True}), "bad_server_response"),
        (httpx.Response(200, text="<html>"), "bad_server_response"),
    ],
)
def test_server_errors_are_traced_without_retry(block, response, code):
    server = FakeServer(lambda body: response)
    with _client(server) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    assert (result.run.outcome, result.run.detail, result.run.attempts) == ("failed", code, 1)


def test_server_not_running(block):
    def refuse(request):
        raise httpx.ConnectError("connection refused", request=request)

    with LocalModelClient("m", transport=httpx.MockTransport(refuse)) as client:
        with pytest.raises(ModelCallError) as error:
            client.complete(list(block.messages), {})
        result = run_block(client, block, run_id="run-0001", now=NOW)
    assert error.value.code == "connection"
    assert (result.run.outcome, result.run.detail) == ("failed", "connection")


def test_trace_never_holds_the_exchange(block):
    with _client(FakeServer(good)) as client:
        run = run_block(client, block, run_id="run-0001", now=NOW).run
    text = run.model_dump_json()
    assert "Libellé" not in text
    assert "messages" not in text


def test_parse_accepts_exactly_the_block(block):
    answer = _good_answer({"messages": list(block.messages)})
    proposals = parse_block_response(json.dumps(answer), block)
    assert len(proposals) == len(block.names)
    with pytest.raises(InvalidResponse):
        parse_block_response(json.dumps({**answer, "block": "b-002"}), block)


@pytest.mark.parametrize(
    ("text", "signals"),
    [
        ("Satisfaction à l'égard du sommeil", ()),
        ("Mesure tirée de Beck et al. (1996)", ("citation",)),
        ("Selon Morin, 2003, l'insomnie", ("citation",)),
        ("Un score ≥ 14 indique une dépression", ("threshold",)),
        ("Seuil clinique de 10", ("threshold",)),
        ("Item du PHQ-9", ("instrument",)),
        ("Score EQ-5D", ("instrument",)),
        ("Item de l'Inventaire de Beck", ("instrument",)),
        ("Taille en cm ; NSP accepté", ()),
    ],
)
def test_invention_signals(text, signals):
    assert invention_signals(text) == signals


def test_a_neighbor_answered_with_the_block_is_dropped(block):
    """The last variable of a block has a neighbor in the next block; the model may answer it."""
    content = json.loads(block.messages[1]["content"])
    outside = content["variables"][-1]["neighbors"][-1]
    assert outside not in block.names
    answer = _good_answer({"messages": block.messages})
    answer["variables"].append({"name": outside, "label": "Voisine", "description": ""})
    proposals = parse_block_response(json.dumps(answer), block)
    assert tuple(p.name for p in proposals) == block.names
