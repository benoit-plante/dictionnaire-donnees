"""Where a client is made (v0.18, D-138).

`client_for` is the one place for a project's messages: nothing leaves a project whose team
has not allowed it. The check is here, before any client exists, and not in the privacy
gate, so that previews of the messages (which send nothing) stay always allowed.
`client_from` serves what sends nothing of a project: the connection test (the list of
models) and the bench, on the fictional bases only.

The protocol, address, model and effort come from the AI settings of this computer; the
key, from Windows' credential manager, at each request.
"""

from __future__ import annotations

from ddict import ai_settings
from ddict.llm import client as llm
from ddict.llm import keys
from ddict.llm.defaults import check_endpoint
from ddict.project.model import Project
from ddict.project.permission import is_allowed


class NotAllowed(Exception):
    """The project does not allow sending its metadata to the AI."""


class NoModel(Exception):
    """No model is chosen in the AI settings."""


def client_from(
    settings: ai_settings.AiSettings | None = None, *, need_model: bool = True, **options
) -> llm.ModelClient:
    """A client from the settings, or NoModel, EndpointRefused. `options` go to the client
    (the tests give a fake transport)."""
    settings = settings or ai_settings.load()
    if need_model and not settings.model:
        raise NoModel
    endpoint = check_endpoint(settings.endpoint)
    key = keys.reader(endpoint)
    if settings.protocol == "anthropic":
        return llm.AnthropicClient(
            settings.model, key=key, endpoint=endpoint, effort=settings.effort, **options
        )
    return llm.OpenAICompatibleClient(settings.model, endpoint=endpoint, key=key, **options)


def client_for(
    project: Project, settings: ai_settings.AiSettings | None = None, **options
) -> llm.ModelClient:
    """The client for this project's messages, or NotAllowed, NoModel, EndpointRefused."""
    if not is_allowed(project):
        raise NotAllowed
    return client_from(settings, **options)
