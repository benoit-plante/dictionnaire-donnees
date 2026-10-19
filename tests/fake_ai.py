"""An institution's AI server, compatible with OpenAI, faked in memory (v0.18): the tests of
the AI talk to it, never to the network. The answers are those each test gives."""

import httpx

from ddict import ai_settings
from ddict.llm import client as client_module
from ddict.project import permission

ADDRESS = "https://ia.universite.example/v1"
REAL = client_module.OpenAICompatibleClient


def _transport(handler) -> httpx.BaseTransport:
    return handler if isinstance(handler, httpx.BaseTransport) else httpx.MockTransport(handler)


def institution(model: str, handler, **kwargs) -> client_module.OpenAICompatibleClient:
    """A client of the fake server; `handler` answers each request."""
    return REAL(
        model, endpoint=ADDRESS, transport=_transport(handler), sleep=lambda s: None, **kwargs
    )


def serve_commands(monkeypatch, handler, model: str = "modele-test") -> None:
    """The commands and pages go through the AI settings: these name the fake server, whose
    clients answer with `handler`."""

    class Client(REAL):
        def __init__(self, *args, **kwargs):
            kwargs.pop("transport", None)
            kwargs.setdefault("sleep", lambda s: None)
            super().__init__(*args, transport=_transport(handler), **kwargs)

    monkeypatch.setattr(client_module, "OpenAICompatibleClient", Client)
    ai_settings.save(ai_settings.AiSettings("openai", ADDRESS, model))


def allowed(project):
    """The project allows its metadata to be sent (D-138), as a team decides it."""
    permission.allow(project, "2026-10-19")
    return project
