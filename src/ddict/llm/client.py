"""Client for a local server with an OpenAI-compatible API (Ollama, LM Studio, llama.cpp).

Nothing may leave the computer (principle 5), so the client:
- refuses any address that is not this computer (no name resolution: "localhost" or a
  loopback IP address written as such);
- ignores proxy settings from the environment, which could send the request elsewhere;
- never follows redirections.

httpx is an optional dependency (`ddict[ia]`): it is imported here only.
"""

from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit

import httpx

from ddict.llm.defaults import DEFAULT_ENDPOINT

DEFAULT_TIMEOUT = 300.0  # seconds: a small model on a processor can be slow
TEMPERATURE = 0
SEED = 42


class EndpointRefused(ValueError):
    """The address is not on this computer."""


class ModelCallError(RuntimeError):
    """The call failed; `code` is a short reason, kept in the project's AI runs."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def check_local(endpoint: str) -> str:
    """Return the endpoint without a trailing slash, or refuse it."""
    parts = urlsplit(endpoint)
    if parts.scheme not in ("http", "https"):
        raise EndpointRefused(f"Unsupported scheme in {endpoint!r}")
    if parts.username or parts.password:
        raise EndpointRefused("Credentials in the address are not accepted")
    host = parts.hostname or ""
    if host != "localhost":
        try:
            local = ipaddress.ip_address(host).is_loopback
        except ValueError:
            local = False
        if not local:
            raise EndpointRefused(f"{host!r} is not this computer")
    return endpoint.rstrip("/")


class LocalModelClient:
    def __init__(
        self,
        model: str,
        *,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: float = DEFAULT_TIMEOUT,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.endpoint = check_local(endpoint)
        self.model = model
        self._http = httpx.Client(
            timeout=timeout,
            trust_env=False,
            follow_redirects=False,
            transport=transport,
        )

    @property
    def parameters(self) -> dict[str, float | int | str]:
        return {"temperature": TEMPERATURE, "seed": SEED}

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> LocalModelClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def complete(self, messages: list[dict], schema: dict) -> str:
        """Send the messages; return the text of the answer, constrained by the schema."""
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
        try:
            response = self._http.post(f"{self.endpoint}/chat/completions", json=body)
        except httpx.TimeoutException as error:
            raise ModelCallError("timeout", f"No answer within the time limit: {error}") from error
        except httpx.TransportError as error:
            raise ModelCallError("connection", f"Cannot reach {self.endpoint}: {error}") from error
        if response.status_code != 200:
            raise ModelCallError(
                f"http_{response.status_code}",
                f"The server answered {response.status_code}: {response.text[:200]}",
            )
        try:
            return response.json()["choices"][0]["message"]["content"] or ""
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise ModelCallError("bad_server_response", "Unexpected server answer") from error


def list_models(
    endpoint: str = DEFAULT_ENDPOINT,
    *,
    timeout: float = 10.0,
    transport: httpx.BaseTransport | None = None,
) -> list[str]:
    """The models the local server offers (`GET /models`, as Ollama, LM Studio and
    llama.cpp answer it), sorted. Same guards as the client: this computer only, no proxy,
    no redirection. Raises EndpointRefused or ModelCallError."""
    endpoint = check_local(endpoint)
    with httpx.Client(
        timeout=timeout, trust_env=False, follow_redirects=False, transport=transport
    ) as http:
        try:
            response = http.get(f"{endpoint}/models")
        except httpx.TimeoutException as error:
            raise ModelCallError("timeout", f"No answer within the time limit: {error}") from error
        except httpx.TransportError as error:
            raise ModelCallError("connection", f"Cannot reach {endpoint}: {error}") from error
    if response.status_code != 200:
        raise ModelCallError(
            f"http_{response.status_code}", f"The server answered {response.status_code}"
        )
    try:
        return sorted(str(item["id"]) for item in response.json()["data"])
    except (ValueError, KeyError, TypeError) as error:
        raise ModelCallError("bad_server_response", "Unexpected server answer") from error
