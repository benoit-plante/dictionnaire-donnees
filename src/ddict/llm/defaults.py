"""Settings shared by the command line, the interface and the clients, importable without
httpx: the defaults, and the rule for an address (D-135)."""

from __future__ import annotations

import ipaddress
from urllib.parse import SplitResult, urlsplit

ANTHROPIC_ENDPOINT = "https://api.anthropic.com"
PROTOCOLS = ("anthropic", "openai")  # the Messages API of Anthropic, or OpenAI-compatible
EFFORTS = ("low", "medium", "high", "xhigh", "max")
DEFAULT_EFFORT = "low"


class EndpointRefused(ValueError):
    """The address is not accepted."""


def _is_this_computer(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _check_parts(endpoint: str) -> SplitResult:
    parts = urlsplit(endpoint)
    if parts.scheme not in ("http", "https"):
        raise EndpointRefused(f"Unsupported scheme in {endpoint!r}")
    if parts.username or parts.password:
        raise EndpointRefused("Credentials in the address are not accepted")
    if parts.query or parts.fragment:
        raise EndpointRefused("A query or a fragment in the address is not accepted")
    if not parts.hostname:
        raise EndpointRefused(f"No host in {endpoint!r}")
    return parts


def check_endpoint(endpoint: str) -> str:
    """Return the endpoint without a trailing slash, or refuse it: HTTPS, or plain HTTP to
    this computer only (no name resolution: "localhost" or a loopback IP address)."""
    parts = _check_parts(endpoint)
    if parts.scheme == "http" and not _is_this_computer(parts.hostname or ""):
        raise EndpointRefused(f"HTTPS is required for {parts.hostname!r}")
    return endpoint.rstrip("/")
