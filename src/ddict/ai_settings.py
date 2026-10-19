"""The AI settings of this computer (v0.18, plan § 5.4): protocol, address, model and
effort, in %APPDATA%\\ddict\\ia.json next to the lists of projects (`recents.config_dir`).

Never the API key, which stays in Windows' credential manager (D-137), and never a study's
name: the settings say where the AI is, not what is sent to it. Whether a project may send
anything is decided in the project itself (D-138). Importable without httpx.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from ddict.llm.defaults import (
    ANTHROPIC_ENDPOINT,
    DEFAULT_EFFORT,
    DEFAULT_MODEL,
    EFFORTS,
    PROTOCOLS,
)
from ddict.recents import config_dir

FILE_NAME = "ia.json"
FORMAT = 1


@dataclass(frozen=True)
class AiSettings:
    protocol: str = "anthropic"
    endpoint: str = ANTHROPIC_ENDPOINT
    model: str = DEFAULT_MODEL  # D-140; an OpenAI-compatible server has none by default
    effort: str = DEFAULT_EFFORT


def default_endpoint(protocol: str) -> str:
    """Anthropic has its address; an OpenAI-compatible server has none by default."""
    return ANTHROPIC_ENDPOINT if protocol == "anthropic" else ""


def default_model(protocol: str) -> str:
    """Anthropic's chosen model (D-140); an OpenAI-compatible server's is its own."""
    return DEFAULT_MODEL if protocol == "anthropic" else ""


def load() -> AiSettings:
    """The settings of this computer; the defaults for what is missing or not understood."""
    try:
        # utf-8-sig: a file saved by Notepad or PowerShell 5.1 may start with a signature.
        found = json.loads((config_dir() / FILE_NAME).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return AiSettings()
    if not isinstance(found, dict):
        return AiSettings()
    protocol = found.get("protocole")
    protocol = protocol if protocol in PROTOCOLS else "anthropic"
    endpoint = found.get("adresse")
    model = found.get("modele")
    effort = found.get("effort")
    return AiSettings(
        protocol=protocol,
        endpoint=endpoint.strip() if isinstance(endpoint, str) else default_endpoint(protocol),
        model=model.strip() if isinstance(model, str) else default_model(protocol),
        effort=effort if effort in EFFORTS else DEFAULT_EFFORT,
    )


def to_json(settings: AiSettings) -> str:
    """Deterministic: keys in a fixed order, UTF-8, LF."""
    values = {
        "format": FORMAT,
        "protocole": settings.protocol,
        "adresse": settings.endpoint,
        "modele": settings.model,
        "effort": settings.effort,
    }
    return json.dumps(values, ensure_ascii=False, indent=2) + "\n"


def save(settings: AiSettings) -> None:
    """Write the settings. Raises OSError: a person chose them, a failure must be said."""
    if settings.protocol not in PROTOCOLS or settings.effort not in EFFORTS:
        raise ValueError(f"Unknown protocol or effort in {settings!r}")
    target = config_dir() / FILE_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(to_json(settings))
