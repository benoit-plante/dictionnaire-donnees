"""Clients for the AI (D-135): the Anthropic Messages API, or a server with an
OpenAI-compatible API (an institution's).

No participant data leaves the computer (principle 5, D-134): what is sent is built by the
privacy gate, from metadata only. The clients add their own guards:
- HTTPS only, except for an address of this computer written as such (no name resolution:
  "localhost" or a loopback IP address), which never crosses a network;
- no credentials, query or fragment in the address;
- proxy settings from the environment are ignored, as they could send the request
  elsewhere, and redirections are never followed;
- the API key is asked from `key` at each request and kept nowhere (D-137); an error
  message never repeats it.

`LocalModelClient` is the route of v0.17 (Ollama on this computer only), kept until step C2
of v0.18.

httpx is an optional dependency (`ddict[ia]`): it is imported here only.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol

import httpx

from ddict.llm.defaults import (
    ANTHROPIC_ENDPOINT,
    DEFAULT_EFFORT,
    DEFAULT_ENDPOINT,
    EFFORTS,
    check_endpoint,
    check_local,
)
from ddict.llm.defaults import (
    EndpointRefused as EndpointRefused,  # raised by the clients, re-exported
)
from ddict.llm.schemas import wire_schema

DEFAULT_TIMEOUT = 300.0  # seconds: a small model on a processor can be slow
TEMPERATURE = 0
SEED = 42

ANTHROPIC_VERSION = "2023-06-01"
# Thinking counts in max_tokens: room for it and for the answer of a whole block.
DEFAULT_MAX_TOKENS = 16000
MAX_MODEL_PAGES = 10

# Busy or limited: one wait, then one more request (retry-after, at most MAX_WAIT seconds).
RETRIED = {429: "rate_limit", 500: "overloaded", 503: "overloaded", 529: "overloaded"}
DEFAULT_WAIT = 5.0
MAX_WAIT = 60.0
REFUSED = {400: "bad_request", 401: "auth", 403: "auth"}
MAX_ERROR_CHARS = 600

KeySource = Callable[[], str | None]


class ModelCallError(RuntimeError):
    """The call failed; `code` is a short reason, kept in the project's AI runs."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class ModelClient(Protocol):
    """What the runs need of a client, whatever its protocol."""

    endpoint: str
    model: str
    last_call: dict

    @property
    def parameters(self) -> dict[str, float | int | str]: ...

    def complete(self, messages: list[dict], schema: dict) -> str: ...


def _wait(response: httpx.Response) -> float:
    try:
        seconds = float(response.headers.get("retry-after", DEFAULT_WAIT))
    except ValueError:  # an HTTP date: not worth parsing
        seconds = DEFAULT_WAIT
    return min(MAX_WAIT, max(0.0, seconds))


def _error_text(response: httpx.Response) -> str:
    """What the server says of an error: the message of an Anthropic or OpenAI error, else
    the start of the body. It says why a request or a schema is refused (400)."""
    try:
        message = response.json()["error"]["message"]
    except (ValueError, KeyError, TypeError):
        message = None
    return str(message)[:MAX_ERROR_CHARS] if message else response.text[:200]


def _counts(usage: object) -> dict[str, int]:
    """The token counts of an answer, numbers only."""
    if not isinstance(usage, dict):
        return {}
    return {k: v for k, v in sorted(usage.items()) if isinstance(v, int)}


class _Client:
    """The HTTP side shared by both protocols."""

    def __init__(
        self,
        model: str,
        *,
        endpoint: str,
        key: KeySource | None,
        timeout: float,
        transport: httpx.BaseTransport | None,
        sleep: Callable[[float], None],
    ) -> None:
        self.endpoint = check_endpoint(endpoint)
        self.model = model
        self._key = key
        self._sleep = sleep
        self.last_call: dict = {}  # request id and tokens of the last answer
        self._http = httpx.Client(
            timeout=timeout,
            trust_env=False,
            follow_redirects=False,
            transport=transport,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _headers(self, key: str | None) -> dict[str, str]:
        raise NotImplementedError

    def _send(
        self, method: str, path: str, *, body: dict | None = None, params: dict | None = None
    ) -> httpx.Response:
        try:
            key = self._key() if self._key else None
        except Exception as error:  # the credential manager did not answer
            raise ModelCallError("key_store", "The API key could not be read") from error
        headers = self._headers(key)
        url = f"{self.endpoint}{path}"
        for attempt in (1, 2):
            try:
                response = self._http.request(
                    method, url, json=body, params=params, headers=headers
                )
            except httpx.TimeoutException as error:
                raise ModelCallError("timeout", "No answer within the time limit") from error
            except httpx.TransportError as error:
                raise ModelCallError("connection", f"Cannot reach {self.endpoint}") from error
            if response.status_code not in RETRIED or attempt == 2:
                break
            self._sleep(_wait(response))
        status = response.status_code
        if status != 200:
            excerpt = _error_text(response)
            if key:
                excerpt = excerpt.replace(key, "…")
            code = REFUSED.get(status) or RETRIED.get(status) or f"http_{status}"
            raise ModelCallError(code, f"The server answered {status}: {excerpt}")
        return response


class AnthropicClient(_Client):
    """The Messages API of Anthropic. No sampling parameter (Haiku 5.5 and Sonnet 5.5
    refuse them), an explicit effort, no fallback to another model (D-135)."""

    protocol = "anthropic"

    def __init__(
        self,
        model: str,
        *,
        key: KeySource,
        endpoint: str = ANTHROPIC_ENDPOINT,
        effort: str = DEFAULT_EFFORT,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout: float = DEFAULT_TIMEOUT,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if effort not in EFFORTS:
            raise ValueError(f"Unknown effort {effort!r}")
        super().__init__(
            model, endpoint=endpoint, key=key, timeout=timeout, transport=transport, sleep=sleep
        )
        self.effort = effort
        self.max_tokens = max_tokens

    @property
    def parameters(self) -> dict[str, float | int | str]:
        return {"effort": self.effort, "max_tokens": self.max_tokens}

    def _headers(self, key: str | None) -> dict[str, str]:
        if not key:
            raise ModelCallError("auth", "No API key is recorded")
        return {"x-api-key": key, "anthropic-version": ANTHROPIC_VERSION}

    def complete(self, messages: list[dict], schema: dict) -> str:
        """Send the messages; return the text of the answer, constrained by the schema.

        The instructions travel in `system`: the API takes no system role in `messages`.
        """
        self.last_call = {}
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        body: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": m["role"], "content": m["content"]}
                for m in messages
                if m["role"] != "system"
            ],
            "output_config": {
                "effort": self.effort,
                "format": {"type": "json_schema", "schema": wire_schema(schema)},
            },
        }
        if system:
            body["system"] = system
        response = self._send("POST", "/v1/messages", body=body)
        try:
            data = response.json()
            blocks = data["content"]
            text = "".join(b["text"] for b in blocks if b.get("type") == "text")
        except (ValueError, KeyError, TypeError) as error:
            raise ModelCallError("bad_server_response", "Unexpected server answer") from error
        self.last_call = {
            "request_id": response.headers.get("request-id"),
            "usage": _counts(data.get("usage")),
        }
        if data.get("stop_reason") == "refusal":
            raise ModelCallError("refusal", "The model declined to answer")
        if data.get("stop_reason") == "max_tokens":
            raise ModelCallError("truncated", "The answer was cut at max_tokens")
        return text

    def list_models(self) -> list[str]:
        """The models the key may use, sorted (`GET /v1/models`, every page)."""
        names: list[str] = []
        params: dict = {"limit": 1000}
        for _page in range(MAX_MODEL_PAGES):
            response = self._send("GET", "/v1/models", params=params)
            try:
                data = response.json()
                names += [str(item["id"]) for item in data["data"]]
            except (ValueError, KeyError, TypeError) as error:
                raise ModelCallError("bad_server_response", "Unexpected server answer") from error
            if not data.get("has_more") or not data.get("last_id"):
                break
            params = {"limit": 1000, "after_id": data["last_id"]}
        return sorted(names)


class OpenAICompatibleClient(_Client):
    """A server with an OpenAI-compatible API (`/chat/completions`, `/models`), such as an
    institution's; the address is required and includes its version path (`…/v1`)."""

    protocol = "openai"

    def __init__(
        self,
        model: str,
        *,
        endpoint: str,
        key: KeySource | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        super().__init__(
            model, endpoint=endpoint, key=key, timeout=timeout, transport=transport, sleep=sleep
        )

    @property
    def parameters(self) -> dict[str, float | int | str]:
        return {"temperature": TEMPERATURE, "seed": SEED}

    def _headers(self, key: str | None) -> dict[str, str]:
        return {"Authorization": f"Bearer {key}"} if key else {}

    def complete(self, messages: list[dict], schema: dict) -> str:
        """Send the messages; return the text of the answer, constrained by the schema."""
        self.last_call = {}
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": TEMPERATURE,
            "seed": SEED,
            "stream": False,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "block_response", "schema": schema, "strict": True},
            },
        }
        response = self._send("POST", "/chat/completions", body=body)
        try:
            data = response.json()
            text = data["choices"][0]["message"]["content"] or ""
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise ModelCallError("bad_server_response", "Unexpected server answer") from error
        request_id = response.headers.get("x-request-id")
        usage = _counts(data.get("usage"))
        if request_id or usage:
            self.last_call = {"request_id": request_id, "usage": usage}
        return text

    def list_models(self) -> list[str]:
        """The models the server offers (`GET /models`), sorted."""
        response = self._send("GET", "/models")
        try:
            return sorted(str(item["id"]) for item in response.json()["data"])
        except (ValueError, KeyError, TypeError) as error:
            raise ModelCallError("bad_server_response", "Unexpected server answer") from error


class LocalModelClient(OpenAICompatibleClient):
    """The route of v0.17: a server on this computer only (Ollama by default), no key."""

    def __init__(
        self,
        model: str,
        *,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: float = DEFAULT_TIMEOUT,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        super().__init__(
            model,
            endpoint=check_local(endpoint),
            timeout=timeout,
            transport=transport,
            sleep=sleep,
        )


def list_models(
    endpoint: str = DEFAULT_ENDPOINT,
    *,
    timeout: float = 10.0,
    transport: httpx.BaseTransport | None = None,
) -> list[str]:
    """The models of the local server (route of v0.17). Raises EndpointRefused or
    ModelCallError."""
    with OpenAICompatibleClient(
        "", endpoint=check_local(endpoint), timeout=timeout, transport=transport
    ) as client:
        return client.list_models()
