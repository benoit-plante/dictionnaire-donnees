"""v0.18, step A4: whether a project may send its metadata to the AI (D-138), project
format 0.8.0, `ddict ia autoriser | interdire`, and the one place where a client is made."""

import json
from datetime import date

import httpx
import pytest

import ddict.cli_ai as cli_ai
from ddict import ai_settings
from ddict.cli import main
from ddict.io import read_sav
from ddict.llm import build_blocks, keys
from ddict.llm.client import AnthropicClient, OpenAICompatibleClient
from ddict.llm.connect import NoModel, NotAllowed, client_for
from ddict.llm.defaults import ANTHROPIC_ENDPOINT, EndpointRefused
from ddict.llm.run import run_block
from ddict.project import (
    SCHEMA_VERSION,
    build_project,
    dumps,
    fingerprint,
    load_project,
    permission,
    save_project,
)

FAKE_KEY = "sk-ant-FAUSSE-cle-permission-0000"
TODAY = date.today().isoformat()


@pytest.fixture
def project(fictional_files):
    return build_project(read_sav(fictional_files["etude-sommeil.sav"]))


@pytest.fixture
def path(project, tmp_path):
    path = tmp_path / "etude-sommeil.dd.json"
    save_project(project, path)
    return path


# --- The project file -------------------------------------------------------------------------


def test_a_project_of_v0_17_opens_not_allowed(project, tmp_path):
    data = json.loads(dumps(project))
    del data["settings"]["ai"]
    data["schema_version"] = "0.7.0"  # as v0.17 wrote it
    path = tmp_path / "ancien.dd.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    old = load_project(path)
    assert SCHEMA_VERSION == "0.10.0" and old.schema_version == "0.10.0"
    assert not permission.is_allowed(old)
    assert json.loads(dumps(old))["settings"]["ai"] == {"allowed": False, "since": None}
    assert dumps(old) == dumps(project)  # nothing else changes


def test_a_new_project_is_not_allowed(project):
    assert project.settings.ai.allowed is False and project.settings.ai.since is None


def test_round_trip_byte_for_byte(project, tmp_path):
    permission.allow(project, "2026-10-19")
    path = tmp_path / "permis.dd.json"
    save_project(project, path)
    first = path.read_bytes()
    assert b'"ai": {\n      "allowed": true,\n      "since": "2026-10-19"\n    }' in first
    again = load_project(path)
    assert again.settings.ai.since == "2026-10-19"
    assert dumps(again).encode("utf-8") == first


def test_allow_and_forbid(project):
    assert permission.allow(project, "2026-10-19") is True
    assert permission.allow(project, "2026-10-20") is False  # its day is kept
    assert project.settings.ai.since == "2026-10-19"
    assert permission.forbid(project) is True
    assert permission.forbid(project) is False
    assert project.settings.ai.since is None


def test_allowing_is_not_a_decision_on_the_data(project):
    """The fingerprint of the decisions (analyses to compute again) does not move."""
    before = fingerprint.fingerprint(project)
    permission.allow(project, "2026-10-19")
    assert fingerprint.fingerprint(project) == before


# --- `ddict ia autoriser | interdire` ---------------------------------------------------------


def test_cli_allow_then_forbid(path, capsys):
    assert main(["ia", "autoriser", str(path)]) == 0
    out = capsys.readouterr().out
    assert "maintenant permis" in out and "Jamais une réponse" in out
    assert load_project(path).settings.ai.model_dump() == {"allowed": True, "since": TODAY}

    assert main(["ia", "autoriser", str(path)]) == 0
    assert f"déjà permis pour ce projet (depuis le {TODAY})" in capsys.readouterr().out

    assert main(["ai", "deny", str(path)]) == 0
    assert "l'aperçu des messages le reste" in capsys.readouterr().out
    assert not load_project(path).settings.ai.allowed

    assert main(["ia", "interdire", str(path)]) == 0
    assert "rien ne change" in capsys.readouterr().out
    assert main(["ai", "allow", str(path)]) == 0


def test_cli_allow_refused_when_the_file_changed_elsewhere(path, monkeypatch, capsys):
    """Another person decided meanwhile: nothing is written (D-129, D-130)."""

    def load_then_changed(target):
        found = load_project(target)
        other = load_project(target)
        other.settings.language = "en"
        save_project(other, target)
        return found

    monkeypatch.setattr(cli_ai, "load_project", load_then_changed)
    assert main(["ia", "autoriser", str(path)]) == 2
    assert capsys.readouterr().err
    saved = load_project(path)
    assert not saved.settings.ai.allowed and saved.settings.language == "en"


# --- The one place where a client is made ---------------------------------------------------


SETTINGS = ai_settings.AiSettings("anthropic", ANTHROPIC_ENDPOINT, "claude-haiku-5-5", "low")


def test_nothing_leaves_a_project_not_allowed(project):
    with pytest.raises(NotAllowed):
        client_for(project, SETTINGS)
    # The preview stays allowed: it sends nothing.
    assert build_blocks(project, size=25)


def test_a_client_for_an_allowed_project(project):
    permission.allow(project, "2026-10-19")
    keys.save(ANTHROPIC_ENDPOINT, FAKE_KEY)
    sent = []

    def answer(request):
        sent.append(request)
        body = json.loads(request.content)
        content = json.loads(body["messages"][0]["content"])
        reply = {
            "block": content["block"],
            "variables": [
                {"name": v["name"], "label": "Libellé", "description": ""}
                for v in content["variables"]
            ],
        }
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": json.dumps(reply)}],
                "stop_reason": "end_turn",
            },
        )

    with client_for(project, SETTINGS, transport=httpx.MockTransport(answer)) as client:
        assert isinstance(client, AnthropicClient)
        assert (client.endpoint, client.model, client.effort) == (
            ANTHROPIC_ENDPOINT,
            "claude-haiku-5-5",
            "low",
        )
        result = run_block(client, build_blocks(project, size=25)[0], run_id="r", now="t")
    assert result.run.outcome == "succeeded"
    assert sent[0].headers["x-api-key"] == FAKE_KEY


def test_settings_of_this_computer_are_used(project):
    permission.allow(project, "2026-10-19")
    ai_settings.save(
        ai_settings.AiSettings("openai", "https://ia.universite.example/v1", "modele-u", "low")
    )
    with client_for(project) as client:
        assert isinstance(client, OpenAICompatibleClient)
        assert client.endpoint == "https://ia.universite.example/v1"


def test_no_model_or_a_refused_address(project):
    permission.allow(project, "2026-10-19")
    with pytest.raises(NoModel):
        client_for(project, ai_settings.AiSettings(model=""))
    with pytest.raises(EndpointRefused):
        client_for(project, ai_settings.AiSettings("openai", "http://ia.universite.example", "m"))
