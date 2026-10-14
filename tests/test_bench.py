"""v0.4, step 6: the model bench, on the two fictional bases, with a fake server."""

import importlib.util
import json
import shutil
from itertools import count
from pathlib import Path

import httpx
import pytest
from streamlit.testing.v1 import AppTest

import ddict.llm.client as client_module
from ddict import bench
from ddict.cli import main
from ddict.llm.client import LocalModelClient
from ddict.project import save_project
from ddict.workflow import profile_database

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")
MODEL = "modele-essai:7b"
NOW = "2026-10-14T18:00:00"


WRONG = {"age": "Q4"}  # the model is wrong here


class Server:
    """Links: the answer key, except for one variable; labels: one citation, one code
    meaning for a variable without labels."""

    def __init__(self):
        self.key = {
            name: target
            for base in bench.load_key()["bases"]
            for name, target in base["links"].items()
        }
        self.sent: list[str] = []

    def __call__(self, request):
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": MODEL}]})
        body = json.loads(request.content)
        self.sent.append(body["messages"][1]["content"])
        content = json.loads(body["messages"][1]["content"])
        if content["block"].startswith("l-"):
            variables = []
            for v in content["variables"]:
                ids = [c["id"] for c in v["candidates"]]
                wanted = WRONG.get(v["name"], self.key.get(v["name"]))
                question = wanted if wanted in ids else ("aucune" if wanted == "none" else ids[0])
                variables.append({"name": v["name"], "question": question})
        else:
            variables = []
            for v in content["variables"]:
                description = f"Description de {v['name']}."
                if v["name"] == "sommeil_q2":
                    description = "Selon Dupont (2019), le sommeil réparateur compte."
                if v["name"] == "vague":
                    description = "Vague de collecte : 1 = printemps."
                variables.append(
                    {"name": v["name"], "label": f"L {v['name']}", "description": description}
                )
        text = json.dumps({"block": content["block"], "variables": variables})
        return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


def _clock():
    ticks = count()
    return lambda: float(next(ticks) * 7)


def _run(server):
    client = LocalModelClient(MODEL, transport=httpx.MockTransport(server))
    items = list(bench.run_bench(client, now=lambda: NOW, clock=_clock()))
    return [i for i in items if isinstance(i, str)], [i for i in items if not isinstance(i, str)]


def test_the_answer_key_matches_the_generators():
    spec = importlib.util.spec_from_file_location(
        "generer_corrige_banc", ROOT / "scripts" / "generer_corrige_banc.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build() == bench.load_key(), "run: uv run python scripts/generer_corrige_banc.py"


def test_measures(fictional_files):
    server = Server()
    progress, results = _run(server)
    assert len(progress) == 4
    sleep, families = results
    assert (sleep.name, sleep.n_key, families.n_key) == ("etude-sommeil", 34, 30)
    assert "age" in sleep.model_wrong
    assert sleep.model_right <= sleep.n_key - 1
    assert sleep.signals.get("citation") == ["sommeil_q2"]
    assert sleep.invented_codes == ["vague"]
    assert (sleep.link_failures, sleep.enrich_failures) == (0, 0)
    assert sleep.link_seconds == 7.0
    # Only the fictional bases go to the model.
    sent = "\n".join(server.sent)
    assert "ZQX" not in sent


def test_the_report_is_reproducible():
    texts = []
    for _ in range(2):
        _progress, results = _run(Server())
        texts.append(
            bench.render_report(
                results, model=MODEL, endpoint="http://127.0.0.1:11434/v1", date="2026-10-14"
            )
        )
    assert texts[0] == texts[1]
    report = texts[0]
    assert report.startswith(f"# Banc d'essai : {MODEL}\n")
    assert "| etude-sommeil |" in report and "| enquete-familles |" in report
    assert "citation (`sommeil_q2`)" in report
    assert "sens de codes (`vague`)" in report
    assert "rien de réel n'a été envoyé" in report


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("1 = Oui, 2 = Non", True),
        ("0 : jamais", True),
        ("Code 2 pour Homme", True),
        ("Sur une échelle de 0 à 10", False),
        ("Heure du coucher (22:30)", False),
        ("Score total, de 0 à 24", False),
    ],
)
def test_code_meaning(text, found):
    assert bool(bench.CODE_MEANING.search(text)) is found


def test_report_name():
    assert bench.report_name("qwen2.5:7b-instruct-q4_K_M", "2026-10-14") == (
        "banc-essai-qwen2.5-7b-instruct-q4_K_M-2026-10-14.md"
    )


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


def test_command(server, tmp_path, capsys):
    assert main(["evaluer", "--modele", MODEL, "--dossier", str(tmp_path)]) == 0
    reports = list(tmp_path.glob("banc-essai-*.md"))
    assert len(reports) == 1
    assert "Rapport :" in capsys.readouterr().out
    assert main(["evaluer", "--modele", MODEL, "--dossier", str(tmp_path / "absent")]) == 2


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_ai_page(server, fictional_files, tmp_path):
    shutil.copy(fictional_files["etude-sommeil.sav"], tmp_path / "etude-sommeil.sav")
    project, path = profile_database(tmp_path / "etude-sommeil.sav")
    save_project(project, path)
    before = path.read_bytes()
    app = AppTest.from_file(APP, default_timeout=120)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "ai"
    app.run()
    assert not app.exception, app.exception
    app.button(key="bench-run").click().run()
    assert not app.exception, app.exception
    assert any("Rapport écrit à côté du projet" in s.value for s in app.success)
    assert len(list(tmp_path.glob("banc-essai-*.md"))) == 1
    assert path.read_bytes() == before  # the project is not touched
