"""v0.3, step 4: the local model from the interface — detection, preview, runs, resume."""

import json
import shutil
from pathlib import Path

import httpx
import pytest
from streamlit.testing.v1 import AppTest

import ddict.llm.client as client_module
from ddict.project import load_project, save_project
from ddict.workflow import add_questionnaire, profile_database

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
MODEL = "qwen2.5:7b-instruct-q4_K_M"


class Server:
    """A fake local server: the list of models, and answers for links and labels."""

    def __init__(self):
        self.chat_calls = 0

    def __call__(self, request):
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "mistral:latest"}, {"id": MODEL}]})
        self.chat_calls += 1
        body = json.loads(request.content)
        content = json.loads(body["messages"][1]["content"])
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
        return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


@pytest.fixture
def server(monkeypatch):
    fake = Server()
    real_list, real_client = client_module.list_models, client_module.LocalModelClient

    def list_models(endpoint=client_module.DEFAULT_ENDPOINT, **kwargs):
        return real_list(endpoint, transport=httpx.MockTransport(fake))

    class Client(real_client):
        def __init__(self, model, **kwargs):
            super().__init__(model, transport=httpx.MockTransport(fake), **kwargs)

    monkeypatch.setattr(client_module, "list_models", list_models)
    monkeypatch.setattr(client_module, "LocalModelClient", Client)
    return fake


@pytest.fixture
def project_path(fictional_files, tmp_path):
    for name in ("etude-sommeil.sav", "questionnaire-sommeil.pdf"):
        shutil.copy(fictional_files[name], tmp_path / name)
    project, path = profile_database(tmp_path / "etude-sommeil.sav")
    add_questionnaire(project, tmp_path / "questionnaire-sommeil.pdf")
    save_project(project, path)
    return path


def _open(path):
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "ai"
    app.run()
    assert not app.exception, app.exception
    return app


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_models_are_listed_and_previewed_without_sending(server, project_path):
    app = _open(project_path)
    assert app.header[0].value == "IA locale"
    assert app.selectbox(key="ai-model").value == MODEL  # the recommended one first
    assert app.selectbox(key="ai-model").options == ["mistral:latest", MODEL]
    assert any('"block": "l-001"' in code.value for code in app.code)  # the preview
    assert server.chat_calls == 0


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_link_then_enrich_then_resume(server, project_path):
    app = _open(project_path)
    app.button(key="ai-link").click().run()
    assert not app.exception, app.exception
    project = load_project(project_path)
    assert {r.prompt_version for r in project.ai_runs} == {"link-v2"}
    assert sum(1 for e in project.variables if e.question.status == "proposed") == 32
    assert any("6 blocs réussis, 0 déjà faits, 0 en échec" in s.value for s in app.success)
    assert (project_path.parent / "etude-sommeil.dd-envois").is_dir()  # the exchanges are kept

    calls = server.chat_calls
    app.button(key="ai-link").click().run()  # nothing new: every block is done
    assert server.chat_calls == calls
    assert any("0 blocs réussis, 6 déjà faits" in s.value for s in app.success)

    app.button(key="ai-enrich").click().run()
    project = load_project(project_path)
    assert project.variable("age").label.status == "proposed"
    assert any(r.prompt_version == "variables-v3" for r in project.ai_runs)


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_only_this_computer(project_path):
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(project_path)
    app.session_state["mode"] = "ai"
    app.session_state["ai-endpoint"] = "http://192.0.2.1:11434/v1"
    app.run()
    assert not app.exception, app.exception
    assert "Adresse refusée" in app.error[0].value
    assert app.button(key="ai-link").disabled and app.button(key="ai-enrich").disabled


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_server_not_running(project_path, monkeypatch):
    def down(endpoint=None, **kwargs):
        raise client_module.ModelCallError("connection", "refused")

    monkeypatch.setattr(client_module, "list_models", down)
    app = _open(project_path)
    assert "ne répond pas. Ollama est-il lancé" in app.warning[0].value
    assert any(f"ollama pull {MODEL}" in code.value for code in app.code)
    assert app.button(key="ai-link").disabled
