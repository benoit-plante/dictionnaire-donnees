"""v0.18, step A3: the API key in the credential manager (a store in memory here, never
Windows' own), the AI settings of this computer, and `ddict ia cle | oublier | tester`.

The key never shows: the witness test sends a known fake key through a whole enrichment,
a refused key and a server error, then looks for it in every file written and every output.
"""

import getpass
import json
import os
from pathlib import Path

import httpx
import pytest

from ddict import ai_settings
from ddict.cli import main
from ddict.io import read_sav
from ddict.llm import client as llm
from ddict.llm import keys
from ddict.llm.client import AnthropicClient, ModelCallError
from ddict.llm.defaults import ANTHROPIC_ENDPOINT
from ddict.llm.enrich import enrich
from ddict.project import build_project, save_project

FAKE_KEY = "sk-ant-FAUSSE-cle-temoin-7f3e9a"  # visibly fake, and found nowhere else
NOW = "2026-10-19T11:00:00"
UNIVERSITY = "https://ia.universite.example/v1"


# --- The settings of this computer ----------------------------------------------------------


def test_settings_default_to_anthropic():
    assert ai_settings.load() == ai_settings.AiSettings(
        protocol="anthropic",
        endpoint=ANTHROPIC_ENDPOINT,
        model="claude-haiku-5-5",
        effort="medium",  # D-140
    )


def test_settings_round_trip_and_deterministic_json():
    chosen = ai_settings.AiSettings("openai", UNIVERSITY, "modele-universite", "medium")
    ai_settings.save(chosen)
    path = Path(os.environ["DDICT_CONFIG_DIR"]) / "ia.json"
    assert path.read_bytes() == (
        b'{\n  "format": 1,\n  "protocole": "openai",\n  "adresse": '
        b'"https://ia.universite.example/v1",\n  "modele": "modele-universite",\n'
        b'  "effort": "medium"\n}\n'
    )
    assert ai_settings.load() == chosen


@pytest.mark.parametrize(
    "text",
    ["pas du JSON", "[]", '{"protocole": "ollama", "effort": "énorme", "modele": 3}'],
)
def test_settings_not_understood_fall_back_to_defaults(text):
    path = Path(os.environ["DDICT_CONFIG_DIR"]) / "ia.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    assert ai_settings.load() == ai_settings.AiSettings()


def test_settings_with_a_signature_are_read():
    """Saved by Notepad or PowerShell 5.1, the file may start with a UTF-8 signature."""
    path = Path(os.environ["DDICT_CONFIG_DIR"]) / "ia.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    signature = "﻿".encode()
    path.write_bytes(signature + b'{"format": 1, "modele": "m", "effort": "medium"}')
    assert ai_settings.load() == ai_settings.AiSettings(model="m", effort="medium")


def test_settings_refuse_an_unknown_protocol():
    with pytest.raises(ValueError):
        ai_settings.save(ai_settings.AiSettings(protocol="ollama"))


# --- The key ---------------------------------------------------------------------------------


def test_key_recorded_replaced_and_forgotten(memory_keys):
    assert not keys.is_recorded(ANTHROPIC_ENDPOINT)
    keys.save(ANTHROPIC_ENDPOINT + "/", f"  {FAKE_KEY}\n")
    assert memory_keys.entries == {("ddict:https://api.anthropic.com", "api-key"): FAKE_KEY}
    keys.save(ANTHROPIC_ENDPOINT, "sk-ant-FAUSSE-autre")
    assert list(memory_keys.entries.values()) == ["sk-ant-FAUSSE-autre"]  # replaced, one copy
    assert keys.reader(ANTHROPIC_ENDPOINT)() == "sk-ant-FAUSSE-autre"
    assert not keys.is_recorded(UNIVERSITY)  # one key per address
    assert keys.forget(ANTHROPIC_ENDPOINT) is True
    assert keys.forget(ANTHROPIC_ENDPOINT) is False
    assert memory_keys.entries == {}


@pytest.mark.parametrize(("typed", "reason"), [("", "empty"), ("   ", "empty"), ("a b", "spaces"),
                                               ("sk-ant-1\nsk-ant-2", "spaces")])  # fmt: skip
def test_what_is_not_a_key_is_refused(typed, reason, memory_keys):
    with pytest.raises(ValueError, match=reason):
        keys.save(ANTHROPIC_ENDPOINT, typed)
    assert memory_keys.entries == {}


class BrokenStore:
    def get_password(self, service, username):
        raise OSError("Credential manager unavailable")

    set_password = delete_password = get_password


def test_a_silent_credential_manager():
    keys.use_backend(BrokenStore())
    with pytest.raises(keys.KeyStoreError):
        keys.is_recorded(ANTHROPIC_ENDPOINT)
    with pytest.raises(keys.KeyStoreError):
        keys.save(ANTHROPIC_ENDPOINT, FAKE_KEY)
    client = AnthropicClient("m", key=keys.reader(ANTHROPIC_ENDPOINT))
    with pytest.raises(ModelCallError) as error:
        client.complete([{"role": "user", "content": "x"}], {"type": "string"})
    assert error.value.code == "key_store"


def test_the_real_store_is_windows_credential_manager():
    keys.use_backend(None)
    assert type(keys._backend()).__name__ == "WinVaultKeyring"


# --- `ddict ia` --------------------------------------------------------------------------------


def _type(monkeypatch, text):
    prompts = []
    monkeypatch.setattr(getpass, "getpass", lambda prompt="": prompts.append(prompt) or text)
    return prompts


def test_cle_records_the_key_typed_without_echo(monkeypatch, capsys, memory_keys):
    prompts = _type(monkeypatch, FAKE_KEY)
    assert main(["ia", "cle"]) == 0
    assert prompts == ["Clé : "]
    assert memory_keys.entries == {("ddict:https://api.anthropic.com", "api-key"): FAKE_KEY}
    out = capsys.readouterr().out
    assert "gestionnaire d'identifiants de Windows" in out and FAKE_KEY not in out


def test_the_key_is_never_an_argument():
    with pytest.raises(SystemExit):
        main(["ia", "cle", FAKE_KEY])


def test_cle_for_the_address_of_the_settings(monkeypatch, memory_keys):
    ai_settings.save(ai_settings.AiSettings("openai", UNIVERSITY, "m", "low"))
    _type(monkeypatch, FAKE_KEY)
    assert main(["ai", "key"]) == 0
    assert list(memory_keys.entries) == [("ddict:https://ia.universite.example/v1", "api-key")]


def test_cle_nothing_typed(monkeypatch, capsys, memory_keys):
    _type(monkeypatch, "")
    assert main(["ia", "cle"]) == 2
    assert "rien n'est enregistré" in capsys.readouterr().err
    assert memory_keys.entries == {}


@pytest.mark.parametrize(
    "args",
    [
        ["--adresse", "http://ia.universite.example/v1"],
        ["--adresse", "https://moi:secret@api.anthropic.com"],
        ["--protocole", "openai"],  # no address of its own
    ],
)
def test_cle_refused_address(args, monkeypatch, capsys, memory_keys):
    _type(monkeypatch, FAKE_KEY)
    assert main(["ia", "cle", *args]) == 2
    assert memory_keys.entries == {}
    assert capsys.readouterr().err


def test_oublier(capsys):
    keys.save(ANTHROPIC_ENDPOINT, FAKE_KEY)
    assert main(["ia", "oublier"]) == 0
    assert "Clé effacée" in capsys.readouterr().out
    assert main(["ia", "oublier"]) == 0
    assert "Aucune clé enregistrée" in capsys.readouterr().out


def _serve(monkeypatch, handler, requests):
    """`ddict ia tester` talks to a fake server, never to the network."""

    def answer(request):
        requests.append(request)
        return handler(request)

    class Fake(llm.AnthropicClient):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, transport=httpx.MockTransport(answer), **kwargs)

    monkeypatch.setattr(llm, "AnthropicClient", Fake)


MODELS = {"data": [{"id": "claude-sonnet-5-5"}, {"id": "claude-haiku-5-5"}], "has_more": False}


def test_tester_without_key(capsys):
    assert main(["ia", "tester"]) == 2
    captured = capsys.readouterr()
    assert "Clé : absente" in captured.out
    assert "ddict ia cle" in captured.err


def test_tester_success(monkeypatch, capsys):
    keys.save(ANTHROPIC_ENDPOINT, FAKE_KEY)
    requests = []
    _serve(monkeypatch, lambda request: httpx.Response(200, json=MODELS), requests)
    assert main(["ia", "tester", "--modele", "claude-haiku-5-5"]) == 0
    out = capsys.readouterr().out
    assert "Clé : enregistrée" in out
    assert "2 modèles offerts" in out and "Aucun contenu de projet" in out
    assert "claude-haiku-5-5 (offert)" in out
    assert [r.method + " " + r.url.path for r in requests] == ["GET /v1/models"]


def test_tester_refused_key(monkeypatch, capsys):
    keys.save(ANTHROPIC_ENDPOINT, FAKE_KEY)
    _serve(monkeypatch, lambda request: httpx.Response(401, json={"type": "error"}), [])
    assert main(["ia", "tester"]) == 2
    assert "La clé est refusée" in capsys.readouterr().err


# --- The witness: the key is found nowhere -------------------------------------------------


def _block_answer(request):
    body = json.loads(request.content)
    content = json.loads(body["messages"][0]["content"])
    answer = {
        "block": content["block"],
        "variables": [
            {"name": v["name"], "label": f"Libellé {v['name']}", "description": ""}
            for v in content["variables"]
        ],
    }
    return httpx.Response(
        200,
        headers={"request-id": "req_temoin"},
        json={
            "content": [{"type": "text", "text": json.dumps(answer)}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        },
    )


def test_the_fake_key_is_found_nowhere(fictional_files, tmp_path, monkeypatch, capsys):
    _type(monkeypatch, FAKE_KEY)
    assert main(["ia", "cle"]) == 0
    _serve(monkeypatch, lambda request: httpx.Response(200, json=MODELS), [])
    assert main(["ia", "tester"]) == 0
    ai_settings.save(ai_settings.AiSettings(model="claude-haiku-5-5"))

    project = build_project(read_sav(fictional_files["etude-sommeil.sav"]))
    path = tmp_path / "etude.dd.json"
    save_project(project, path)
    log_dir = tmp_path / "etude.dd-envois"
    errors = []
    echo = f"invalid x-api-key: {FAKE_KEY}"
    for handler in (
        _block_answer,  # a whole enrichment
        lambda request: httpx.Response(401, text=echo),  # a refused key, repeated by the server
        lambda request: httpx.Response(500, text=echo),  # a server error, the same
    ):
        sent = []

        def answer(request, handler=handler, sent=sent):
            sent.append(request)
            return handler(request)

        with AnthropicClient(
            "claude-haiku-5-5",
            key=keys.reader(ANTHROPIC_ENDPOINT),
            transport=httpx.MockTransport(answer),
            sleep=lambda seconds: None,
        ) as client:
            for event in enrich(
                project,
                client,
                now=lambda: NOW,
                block_size=25,
                redo=True,
                save=lambda p: save_project(p, path),
                log_dir=log_dir,
            ):
                if event.result is not None:
                    errors.append(event.result.run.detail or "")
            if handler is not _block_answer:  # the message of the error itself
                with pytest.raises(ModelCallError) as error:
                    client.complete([{"role": "user", "content": "x"}], {"type": "string"})
                errors.append(str(error.value))
        assert sent[0].headers["x-api-key"] == FAKE_KEY  # it did leave, in the header only

    written = [p for p in (tmp_path, Path(os.environ["DDICT_CONFIG_DIR"])) for p in p.rglob("*")]
    files = [p for p in written if p.is_file()]
    assert any(p.name == "ia.json" for p in files)
    assert any(p.parent == log_dir for p in files)
    for file in files:
        assert FAKE_KEY.encode() not in file.read_bytes(), file.name
    captured = capsys.readouterr()
    assert FAKE_KEY not in captured.out + captured.err
    assert not [e for e in errors if FAKE_KEY in e]
    assert {"auth", "overloaded"} <= set(errors)
