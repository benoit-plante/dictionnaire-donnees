"""The AI page (v0.18, step C1; the local model of v0.3 before): the settings of this
computer, the key (a store in memory, never Windows' own), the connection test, what
leaves, the box of the sidebar, and the runs, against a fake Anthropic server."""

import json
import shutil
from pathlib import Path

import httpx
import pytest
from streamlit.testing.v1 import AppTest

import ddict.llm.client as client_module
from ddict import ai_settings
from ddict.llm import keys
from ddict.llm.defaults import ANTHROPIC_ENDPOINT
from ddict.project import load_project, save_project
from ddict.workflow import add_questionnaire, profile_database

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
MODEL = "claude-haiku-5-5"
FAKE_KEY = "sk-ant-FAUSSE-cle-page-ia-0000"
# Streamlit's test runner needs a socket on this computer; nothing else is reachable.
pytestmark = pytest.mark.allow_hosts(["127.0.0.1"])


class Server:
    """A fake Anthropic: the list of models, and answers for links and labels."""

    def __init__(self, status=200):
        self.status = status
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        if self.status != 200:
            return httpx.Response(self.status, json={"error": {"message": "refusée"}})
        if request.url.path == "/v1/models":
            data = [{"id": "claude-sonnet-5-5"}, {"id": MODEL}]
            return httpx.Response(200, json={"data": data, "has_more": False})
        body = json.loads(request.content)
        content = json.loads(body["messages"][0]["content"])
        if content["block"].startswith("l-"):
            variables = [
                {"name": v["name"], "question": v["candidates"][0]["id"]}
                for v in content["variables"]
            ]
        else:
            variables = [
                {"name": v["name"], "label": f"Libellé {v['name']}", "description": ""}
                for v in content["variables"]
            ]
        text = json.dumps({"block": content["block"], "variables": variables})
        return httpx.Response(
            200, json={"content": [{"type": "text", "text": text}], "stop_reason": "end_turn"}
        )

    @property
    def messages(self):
        return [r for r in self.requests if r.url.path == "/v1/messages"]


REAL_CLIENT = client_module.AnthropicClient


def _serve(monkeypatch, fake):
    class Client(REAL_CLIENT):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, transport=httpx.MockTransport(fake), **kwargs)

    monkeypatch.setattr(client_module, "AnthropicClient", Client)
    return fake


@pytest.fixture
def server(monkeypatch):
    return _serve(monkeypatch, Server())


@pytest.fixture
def project_path(fictional_files, tmp_path):
    for name in ("etude-sommeil.sav", "questionnaire-sommeil.pdf"):
        shutil.copy(fictional_files[name], tmp_path / name)
    project, path = profile_database(tmp_path / "etude-sommeil.sav")
    add_questionnaire(project, tmp_path / "questionnaire-sommeil.pdf")
    save_project(project, path)
    return path


@pytest.fixture
def ready():
    """Settings saved and a key recorded, as after a first visit to the page."""
    ai_settings.save(ai_settings.AiSettings(model=MODEL))
    keys.save(ANTHROPIC_ENDPOINT, FAKE_KEY)


def _open(path):
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "ai"
    app.run()
    assert not app.exception, app.exception
    return app


def _texts(app):
    found = [e.value for kind in ("markdown", "caption", "success", "error", "info", "warning")
             for e in getattr(app, kind)]  # fmt: skip
    return "\n".join(str(v) for v in found)


def test_a_project_not_allowed_sends_nothing(server, ready, project_path):
    app = _open(project_path)
    assert app.header[0].value == "IA"
    assert "n'est pas permis pour ce projet" in _texts(app)
    assert app.button(key="ai-link").disabled and app.button(key="ai-enrich").disabled
    assert any('"block": "l-001"' in code.value for code in app.code)  # the preview, always
    assert app.checkbox(key="ai-allowed").value is False
    assert server.requests == []


def test_what_leaves_is_said(project_path):
    app = _open(project_path)
    text = _texts(app)
    assert "Ne partent jamais" in text and "30 jours" in text and "2026-10-19" in text
    assert "privacy.claude.com" in text


def test_settings_and_key(project_path, memory_keys):
    app = _open(project_path)
    assert app.text_input(key="ai-endpoint").value == ANTHROPIC_ENDPOINT
    app.text_input(key="ai-model").input("claude-sonnet-5-5").run()
    app.selectbox(key="ai-effort").set_value("medium").run()
    app.button(key="ai-settings").click().run()
    assert ai_settings.load() == ai_settings.AiSettings(model="claude-sonnet-5-5", effort="medium")
    assert "Clé d'API : absente." in _texts(app)

    app.text_input(key="ai-key-input").input(FAKE_KEY).run()
    app.button(key="ai-key").click().run()
    assert not app.exception, app.exception
    assert memory_keys.entries == {("ddict:https://api.anthropic.com", "api-key"): FAKE_KEY}
    assert app.text_input(key="ai-key-input").value == ""  # not kept in the page
    assert app.session_state["ai-key-input"] == ""
    assert "Clé d'API : enregistrée." in _texts(app)
    assert FAKE_KEY not in _texts(app)

    app.button(key="ai-forget").click().run()
    assert memory_keys.entries == {}
    assert "Clé d'API : absente." in _texts(app)


def test_a_refused_address(project_path):
    app = _open(project_path)
    app.radio(key="ai-protocol").set_value("openai").run()
    assert app.text_input(key="ai-endpoint").value == ""
    app.text_input(key="ai-endpoint").input("http://ia.universite.example/v1").run()
    assert "Adresse refusée" in app.error[0].value
    app.button(key="ai-settings").click().run()
    assert ai_settings.load() == ai_settings.AiSettings()  # nothing saved


def test_connection(monkeypatch, ready, project_path):
    fake = _serve(monkeypatch, Server())
    app = _open(project_path)
    app.button(key="ai-test").click().run()
    assert "2 modèles offerts" in app.success[0].value
    assert [r.url.path for r in fake.requests] == ["/v1/models"]
    assert fake.requests[0].headers["x-api-key"] == FAKE_KEY

    _serve(monkeypatch, Server(status=401))
    app.button(key="ai-test").click().run()
    assert "La clé est refusée" in app.error[0].value


def test_allow_then_link_then_enrich_then_resume(server, ready, project_path):
    app = _open(project_path)
    app.checkbox(key="ai-allowed").check().run()
    assert not app.exception, app.exception
    assert load_project(project_path).settings.ai.allowed
    assert "Permis depuis le" in _texts(app)

    app.button(key="ai-link").click().run()
    assert not app.exception, app.exception
    project = load_project(project_path)
    assert {r.prompt_version for r in project.ai_runs} <= {"link-v2", "link-v3"}
    assert {r.model for r in project.ai_runs} == {MODEL}
    assert sum(1 for e in project.variables if e.question.status == "proposed") == 32
    links = len(server.messages)
    assert links < 6  # blocks of 20 through an API key, not of 6
    assert any(f"{links} blocs réussis, 0 déjà faits, 0 en échec" in s.value for s in app.success)
    assert (project_path.parent / "etude-sommeil.dd-envois").is_dir()  # the exchanges are kept

    app.button(key="ai-link").click().run()  # nothing new: every block is done
    assert len(server.messages) == links
    assert any(f"0 blocs réussis, {links} déjà faits" in s.value for s in app.success)

    app.button(key="ai-enrich").click().run()
    project = load_project(project_path)
    assert project.variable("age").label.status == "proposed"
    assert any(r.prompt_version == "variables-v4" for r in project.ai_runs)


def test_allowing_refused_when_the_file_changed_elsewhere(server, ready, project_path):
    app = _open(project_path)
    other = load_project(project_path)
    other.settings.language = "en"
    save_project(other, project_path)
    app.checkbox(key="ai-allowed").check().run()
    assert not app.exception, app.exception
    saved = load_project(project_path)
    assert not saved.settings.ai.allowed and saved.settings.language == "en"
    assert app.checkbox(key="ai-allowed").value is False
    assert any("modifié ailleurs" in w.value for w in app.warning)


def test_a_refused_key_stops_the_run(monkeypatch, ready, project_path):
    project = load_project(project_path)
    project.settings.ai.allowed = True
    save_project(project, project_path)
    fake = _serve(monkeypatch, Server(status=401))
    app = _open(project_path)
    app.button(key="ai-link").click().run()
    assert len(fake.messages) == 1  # the first block, then the run stops
    assert any("La clé d'API est refusée" in e.value for e in app.error)
