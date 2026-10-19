"""v0.18, step A2: the Anthropic and OpenAI-compatible clients, tested against a fake server
in memory (no network), and the schema sent to Anthropic."""

import json

import httpx
import pytest

from ddict.io import read_sav
from ddict.llm import build_blocks
from ddict.llm.advise import advice_schema
from ddict.llm.client import (
    ANTHROPIC_ENDPOINT,
    MAX_WAIT,
    AnthropicClient,
    EndpointRefused,
    ModelCallError,
    OpenAICompatibleClient,
    check_endpoint,
)
from ddict.llm.enrich import _log
from ddict.llm.link import link_schema
from ddict.llm.run import MAX_ATTEMPTS, run_block
from ddict.llm.schemas import (
    ACCEPTED_KEYWORDS,
    MAX_OPTIONAL_PARAMETERS,
    MAX_UNION_PARAMETERS,
    optional_parameters,
    response_schema,
    schema_nodes,
    union_parameters,
    wire_schema,
)
from ddict.llm.stems import stem_schema
from ddict.project import build_project
from test_analysis_data import analyses_project

NOW = "2026-10-19T10:00:00"
FAKE_KEY = "sk-ant-FAUSSE-cle-de-test-0000"  # visibly fake (D-137)


@pytest.fixture(scope="module")
def block(fictional_files):
    project = build_project(read_sav(fictional_files["etude-sommeil.sav"]))
    return build_blocks(project, size=4)[0]


def _good_answer(user_text):
    content = json.loads(user_text)
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
        body = json.loads(request.content) if request.content else None
        self.requests.append((request, body))
        scenario = self.scenarios.pop(0) if len(self.scenarios) > 1 else self.scenarios[0]
        return scenario(body)


def message(answer, *, stop="end_turn", thinking=False, request_id="req_test_1"):
    """An Anthropic answer whose text block holds `answer` (a dict becomes JSON)."""
    text = answer if isinstance(answer, str) else json.dumps(answer, ensure_ascii=False)
    content = [{"type": "thinking", "thinking": "", "signature": "x"}] if thinking else []
    content.append({"type": "text", "text": text})
    return lambda body: httpx.Response(
        200,
        headers={"request-id": request_id},
        json={
            "id": "msg_1",
            "type": "message",
            "role": "assistant",
            "content": content,
            "stop_reason": stop,
            "usage": {"input_tokens": 120, "output_tokens": 45, "service_tier": "standard"},
        },
    )


def good(body):
    return message(_good_answer(body["messages"][0]["content"]))(body)


def _with(change):
    def scenario(body):
        answer = _good_answer(body["messages"][0]["content"])
        change(answer)
        return message(answer)(body)

    return scenario


def _anthropic(server, **kwargs):
    kwargs.setdefault("key", lambda: FAKE_KEY)
    kwargs.setdefault("sleep", lambda seconds: None)
    return AnthropicClient("claude-haiku-5-5", transport=httpx.MockTransport(server), **kwargs)


# --- The address --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://api.anthropic.com",
        "https://ia.universite.example/v1/",
        "http://127.0.0.1:8000/v1",
        "http://localhost:1234/v1",
        "http://[::1]:8080",
    ],
)
def test_https_or_this_computer_is_accepted(endpoint):
    assert check_endpoint(endpoint) == endpoint.rstrip("/")


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://ia.universite.example/v1",
        "http://192.168.1.10:11434/v1",
        "http://127.0.0.1.nip.io/v1",
        "https://user:secret@api.anthropic.com",
        "https://api.anthropic.com/?key=abc",
        "https://api.anthropic.com/#x",
        "https://",
        "file:///etc/passwd",
        "ftp://api.anthropic.com",
    ],
)
def test_other_addresses_are_refused(endpoint):
    with pytest.raises(EndpointRefused):
        check_endpoint(endpoint)
    with pytest.raises(EndpointRefused):
        AnthropicClient("m", key=lambda: FAKE_KEY, endpoint=endpoint)
    with pytest.raises(EndpointRefused):
        OpenAICompatibleClient("m", endpoint=endpoint)


# --- Anthropic: the request ----------------------------------------------------------------


def test_request_sent_to_anthropic(block):
    server = FakeServer(good)
    with _anthropic(server) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    request, body = server.requests[0]
    assert str(request.url) == f"{ANTHROPIC_ENDPOINT}/v1/messages"
    assert request.headers["x-api-key"] == FAKE_KEY
    assert request.headers["anthropic-version"] == "2023-06-01"
    assert body["model"] == "claude-haiku-5-5"
    # The instructions travel in `system`; no system role in the messages.
    assert body["system"] == block.messages[0]["content"]
    assert body["messages"] == [block.messages[1]]
    # No sampling parameter (refused by Haiku 5.5 and Sonnet 5.5), no fallback (D-135).
    for refused in ("temperature", "top_p", "top_k", "seed", "fallbacks", "stream"):
        assert refused not in body
    assert body["output_config"]["effort"] == "low"
    assert body["output_config"]["format"] == {
        "type": "json_schema",
        "schema": wire_schema(response_schema()),
    }
    assert "maxLength" not in json.dumps(body["output_config"])
    assert result.run.outcome == "succeeded"
    assert [p.name for p in result.proposals] == list(block.names)


def test_trace_and_calls(block, tmp_path):
    with _anthropic(FakeServer(good), effort="medium") as client:
        result = run_block(client, block, run_id="run-0007", now=NOW)
    run = result.run
    assert run.endpoint == ANTHROPIC_ENDPOINT
    assert run.model == "claude-haiku-5-5"
    assert run.parameters == {"effort": "medium", "max_tokens": 16000}
    assert result.calls == (
        {"request_id": "req_test_1", "usage": {"input_tokens": 120, "output_tokens": 45}},
    )
    _log(tmp_path, block, result)
    record = json.loads((tmp_path / f"run-0007-{block.block_id}.json").read_text("utf-8"))
    assert record["calls"][0]["request_id"] == "req_test_1"


def test_unknown_effort_is_refused():
    with pytest.raises(ValueError):
        AnthropicClient("m", key=lambda: FAKE_KEY, effort="extreme")


def test_thinking_blocks_come_first(block):
    answer = lambda body: message(  # noqa: E731
        _good_answer(body["messages"][0]["content"]), thinking=True
    )(body)
    with _anthropic(FakeServer(answer)) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    assert result.run.outcome == "succeeded"


def test_proxy_settings_are_ignored(block, monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example.com:3128")
    monkeypatch.setenv("ALL_PROXY", "http://proxy.example.com:3128")
    server = FakeServer(good)
    with _anthropic(server) as client:
        assert client._http._trust_env is False
        run_block(client, block, run_id="run-0001", now=NOW)
    assert server.requests[0][0].url.host == "api.anthropic.com"


def test_redirections_are_not_followed(block):
    redirect = lambda body: httpx.Response(  # noqa: E731
        307, headers={"Location": "https://ailleurs.example.com/v1/messages"}
    )
    server = FakeServer(redirect)
    with _anthropic(server) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    assert len(server.requests) == 1
    assert (result.run.outcome, result.run.detail) == ("failed", "http_307")


# --- Anthropic: answers and errors ---------------------------------------------------------


def _too_long(answer):
    answer["variables"][0]["label"] = "x" * 81


def _extra_field(answer):
    answer["variables"][0]["seuil_clinique"] = 14


@pytest.mark.parametrize(
    ("scenario", "code"),
    [
        # The bound left out of the schema sent is still checked here (D-135).
        (_with(_too_long), "schema"),
        (_with(_extra_field), "schema"),
        (message("pas du JSON"), "not_json"),
        (message({"block": "b-001"}, stop="refusal"), "refusal"),
        (message('{"block": "b-0', stop="max_tokens"), "truncated"),
    ],
)
def test_unusable_answers_are_tried_again_then_refused(block, scenario, code):
    server = FakeServer(scenario)
    with _anthropic(server) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    assert result.proposals is None
    assert (result.run.outcome, result.run.detail) == ("invalid_response", code)
    assert result.run.attempts == MAX_ATTEMPTS == len(server.requests)


def test_a_refusal_then_an_answer(block):
    server = FakeServer(message({}, stop="refusal"), good)
    with _anthropic(server) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    assert (result.run.outcome, result.run.attempts) == ("succeeded", 2)
    assert len(result.calls) == 2


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (400, "bad_request"),
        (401, "auth"),
        (403, "auth"),
        (404, "http_404"),
        (418, "http_418"),
    ],
)
def test_refusals_stop_without_retry(block, status, code):
    server = FakeServer(lambda body: httpx.Response(status, json={"type": "error"}))
    with _anthropic(server) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    assert (result.run.outcome, result.run.detail, result.run.attempts) == ("failed", code, 1)
    assert len(server.requests) == 1


@pytest.mark.parametrize(("status", "code"), [(429, "rate_limit"), (529, "overloaded")])
def test_busy_server_one_wait_then_success(block, status, code):
    busy = lambda body: httpx.Response(status, headers={"retry-after": "3"})  # noqa: E731
    waits = []
    server = FakeServer(busy, good)
    with _anthropic(server, sleep=waits.append) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    assert waits == [3.0]
    assert (result.run.outcome, result.run.attempts) == ("succeeded", 1)


@pytest.mark.parametrize(
    ("status", "code", "headers", "wait"),
    [
        (429, "rate_limit", {"retry-after": "600"}, MAX_WAIT),
        (529, "overloaded", {}, 5.0),
        (500, "overloaded", {"retry-after": "Wed, 21 Oct 2026 07:28:00 GMT"}, 5.0),
    ],
)
def test_busy_server_one_wait_then_stop(block, status, code, headers, wait):
    waits = []
    server = FakeServer(lambda body: httpx.Response(status, headers=headers))
    with _anthropic(server, sleep=waits.append) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    assert waits == [wait]
    assert len(server.requests) == 2
    assert (result.run.outcome, result.run.detail, result.run.attempts) == ("failed", code, 1)


def test_no_key_sends_nothing(block):
    server = FakeServer(good)
    with _anthropic(server, key=lambda: None) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    assert server.requests == []
    assert (result.run.outcome, result.run.detail) == ("failed", "auth")


def test_the_key_is_never_repeated(block):
    echo = lambda body: httpx.Response(500, text=f"bad key {FAKE_KEY} here")  # noqa: E731
    with _anthropic(FakeServer(echo)) as client:
        with pytest.raises(ModelCallError) as error:
            client.complete(list(block.messages), response_schema())
        assert FAKE_KEY not in repr(client.__dict__)
    assert error.value.code == "overloaded"
    assert FAKE_KEY not in str(error.value)


def test_unexpected_answer(block):
    server = FakeServer(lambda body: httpx.Response(200, json={"unexpected": True}))
    with _anthropic(server) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    assert (result.run.outcome, result.run.detail) == ("failed", "bad_server_response")


def test_models_of_every_page():
    pages = [
        {"data": [{"id": "claude-sonnet-5-5"}], "has_more": True, "last_id": "claude-sonnet-5-5"},
        {"data": [{"id": "claude-haiku-5-5"}], "has_more": False, "last_id": "claude-haiku-5-5"},
    ]
    server = FakeServer(*[lambda body, p=p: httpx.Response(200, json=p) for p in pages])
    with _anthropic(server) as client:
        assert client.list_models() == ["claude-haiku-5-5", "claude-sonnet-5-5"]
    first, second = (request for request, _ in server.requests)
    assert first.url.path == "/v1/models" and first.url.params["limit"] == "1000"
    assert second.url.params["after_id"] == "claude-sonnet-5-5"
    assert first.headers["x-api-key"] == FAKE_KEY


# --- OpenAI-compatible server --------------------------------------------------------------


def chat(answer):
    text = json.dumps(answer, ensure_ascii=False)
    return lambda body: httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


def openai_good(body):
    return chat(_good_answer(body["messages"][1]["content"]))(body)


def test_request_sent_to_an_institution(block):
    server = FakeServer(openai_good)
    with OpenAICompatibleClient(
        "modele-universite",
        endpoint="https://ia.universite.example/v1",
        key=lambda: FAKE_KEY,
        transport=httpx.MockTransport(server),
    ) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    request, body = server.requests[0]
    assert str(request.url) == "https://ia.universite.example/v1/chat/completions"
    assert request.headers["authorization"] == f"Bearer {FAKE_KEY}"
    assert body["messages"] == list(block.messages)
    assert body["temperature"] == 0 and body["seed"] == 42
    # The full schema: these servers take the bounds.
    assert body["response_format"]["json_schema"]["schema"] == response_schema()
    assert result.run.outcome == "succeeded"
    assert result.run.parameters == {"temperature": 0, "seed": 42}
    assert result.calls == ()


def test_institution_without_key_and_its_models():
    server = FakeServer(lambda body: httpx.Response(200, json={"data": [{"id": "b"}, {"id": "a"}]}))
    with OpenAICompatibleClient(
        "", endpoint="https://ia.universite.example/v1", transport=httpx.MockTransport(server)
    ) as client:
        assert client.list_models() == ["a", "b"]
    request = server.requests[0][0]
    assert str(request.url) == "https://ia.universite.example/v1/models"
    assert "authorization" not in request.headers


def test_institution_refuses_the_key(block):
    server = FakeServer(lambda body: httpx.Response(401))
    with OpenAICompatibleClient(
        "m",
        endpoint="https://ia.universite.example/v1",
        key=lambda: FAKE_KEY,
        transport=httpx.MockTransport(server),
    ) as client:
        result = run_block(client, block, run_id="run-0001", now=NOW)
    assert (result.run.outcome, result.run.detail) == ("failed", "auth")


# --- The schema sent to Anthropic -----------------------------------------------------------


@pytest.fixture(scope="module")
def schemas():
    return {
        "variables": response_schema(),
        "link": link_schema(),
        "stems": stem_schema(),
        "advice": advice_schema(analyses_project()),
        "advice, flat": advice_schema(analyses_project(), flat=True),
    }


def _keywords(schema):
    return {key for node in schema_nodes(schema) for key in node}


def test_the_four_schemas_sent_are_within_the_limits(schemas):
    for name, schema in schemas.items():
        wired = wire_schema(schema)
        assert _keywords(wired) <= ACCEPTED_KEYWORDS, name
        assert all(node.get("minItems", 0) <= 1 for node in schema_nodes(wired)), name
        assert optional_parameters(wired) <= MAX_OPTIONAL_PARAMETERS, name
        assert union_parameters(wired) <= MAX_UNION_PARAMETERS, name


def test_wire_schema_keeps_the_choices(schemas):
    wired = wire_schema(schemas["advice"])
    proposals = wired["properties"]["proposals"]
    assert "maxItems" not in proposals
    analyses = proposals["items"]["anyOf"]
    assert len(analyses) == len(schemas["advice"]["properties"]["proposals"]["items"]["anyOf"])
    for analysis in analyses:
        roles = analysis["properties"]["roles"]
        assert "prefixItems" not in roles and roles.get("minItems", 0) <= 1
        assert "maxLength" not in analysis["properties"]["reason"]
    # The variables a role may take stay listed.
    assert any(
        node.get("enum") and node.get("type") == "string" and len(node["enum"]) > 1
        for node in schema_nodes(wired)
    )
    # The original is untouched.
    assert "prefixItems" in json.dumps(schemas["advice"])


def test_wire_schema_details():
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["title"],
        "title": "Racine",
        "properties": {
            "title": {"type": "string", "maxLength": 5, "title": "Title"},
            "pair": {
                "type": "array",
                "prefixItems": [{"type": "string"}],
                "minItems": 3,
                "maxItems": 3,
            },
            "n": {"type": "integer", "minimum": 0, "maximum": 9},
        },
    }
    assert wire_schema(schema) == {
        "type": "object",
        "additionalProperties": False,
        "required": ["title"],
        "properties": {
            "title": {"type": "string"},  # a property named "title" stays
            "pair": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "n": {"type": "integer"},
        },
    }
    assert optional_parameters(schema) == 2


def test_an_open_object_is_a_programming_error():
    with pytest.raises(ValueError):
        wire_schema({"type": "object", "properties": {"a": {"type": "string"}}})
