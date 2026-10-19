"""The one place where a client is made to send a project's messages (v0.18, D-138).

Nothing leaves a project whose team has not allowed it: the check is here, before any
client exists, and not in the privacy gate, so that previews of the messages (which send
nothing) stay always allowed. The protocol, address, model and effort come from the AI
settings of this computer; the key, from Windows' credential manager, at each request.
"""

from __future__ import annotations

from ddict import ai_settings
from ddict.llm import keys
from ddict.llm.client import AnthropicClient, ModelClient, OpenAICompatibleClient
from ddict.llm.defaults import check_endpoint
from ddict.project.model import Project
from ddict.project.permission import is_allowed


class NotAllowed(Exception):
    """The project does not allow sending its metadata to the AI."""


class NoModel(Exception):
    """No model is chosen in the AI settings."""


def client_for(
    project: Project, settings: ai_settings.AiSettings | None = None, **options
) -> ModelClient:
    """The client for this project, or NotAllowed, NoModel, EndpointRefused. `options` go to
    the client (the tests give a fake transport)."""
    if not is_allowed(project):
        raise NotAllowed
    settings = settings or ai_settings.load()
    if not settings.model:
        raise NoModel
    endpoint = check_endpoint(settings.endpoint)
    key = keys.reader(endpoint)
    if settings.protocol == "anthropic":
        return AnthropicClient(
            settings.model, key=key, endpoint=endpoint, effort=settings.effort, **options
        )
    return OpenAICompatibleClient(settings.model, endpoint=endpoint, key=key, **options)
