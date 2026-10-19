"""v0.4, step 6: the model bench, on the two fictional bases, with a fake server."""

import importlib.util
import json
import shutil
from collections import Counter
from itertools import count
from pathlib import Path

import httpx
import pytest
from streamlit.testing.v1 import AppTest

import ddict.llm.client as client_module
from ddict import ai_settings, bench
from ddict.cli import main
from ddict.project import save_project
from ddict.workflow import profile_database
from fake_ai import institution, serve_commands

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")
MODEL = "modele-essai:7b"
NOW = "2026-10-14T18:00:00"


WRONG = {"age": "Q4"}  # the model is wrong here
STEMS = json.loads(
    (ROOT / "exemples" / "bases-fictives" / "corrige-surveymonkey.json").read_text(encoding="utf-8")
)["waves"]["t2"]["stems"]
STEM_ANSWERS = {"q0007": "eft_pauses", "q0012": ""}  # an invented acronym; unsure


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
        self.systems: list[str] = []

    def __call__(self, request):
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": MODEL}]})
        body = json.loads(request.content)
        self.sent.append(body["messages"][1]["content"])
        self.systems.append(body["messages"][0]["content"])
        content = json.loads(body["messages"][1]["content"])
        if content["block"].startswith("r-"):  # stems (v0.7): the key's, but two
            questions = [
                {"key": q["key"], "stem": STEM_ANSWERS.get(q["key"], STEMS.get(q["key"], ""))}
                for q in content["questions"]
            ]
            text = json.dumps({"block": content["block"], "questions": questions})
            return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})
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
    client = institution(MODEL, server)
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
    assert len(progress) == 9
    sleep, families, english, control, stems = results
    # Stems (v0.7): the rules alone, then with the model.
    assert stems.equal(stems.computed) == 3  # secteur, consignes_securite, commentaires
    assert stems.equal(stems.model) == 8  # the key's, but q0007 and q0012
    assert stems.model["q0007"] == "eft_pauses"
    # Acronyms the questions do not hold: "eft", invented, and "sst" (the key's own choice).
    assert stems.flagged == ["q0006", "q0007"]
    assert stems.model["q0012"] is None  # unsure: no stem, and none from the rules either
    assert stems.answered == 9 and stems.failures == 0
    assert (control.name, control.n_key) == ("etude-activite", 23)
    assert english.name == "sleep-study" and english.n_key == 34
    # The English study gets the English instructions (v0.5).
    assert any(s.startswith("You help a research team") for s in server.systems)
    assert any(s.startswith("Tu aides une équipe") for s in server.systems)
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
                results, model=MODEL, endpoint="https://ia.universite.example/v1", date="2026-10-14"
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
    serve_commands(monkeypatch, fake, model=MODEL)
    return fake


def test_command(server, tmp_path, capsys):
    assert main(["evaluer", "--dossier", str(tmp_path)]) == 0  # the model of the settings
    reports = list(tmp_path.glob("banc-essai-*.md"))
    assert len(reports) == 1
    assert "Rapport :" in capsys.readouterr().out
    assert main(["evaluer", "--modele", MODEL, "--dossier", str(tmp_path / "absent")]) == 2


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_ai_page(fictional_files, tmp_path, monkeypatch):
    """v0.18: through the settings of the AI page, after a confirmation (it is billed)."""
    fake = Server()
    real = client_module.OpenAICompatibleClient

    class Client(real):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, transport=httpx.MockTransport(fake), **kwargs)

    monkeypatch.setattr(client_module, "OpenAICompatibleClient", Client)
    ai_settings.save(ai_settings.AiSettings("openai", "https://ia.universite.example/v1", MODEL))
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
    assert any("facturé sur votre clé" in w.value for w in app.warning)  # asked first
    app.button(key="bench-cancel").click().run()
    assert not list(tmp_path.glob("banc-essai-*.md"))
    app.button(key="bench-run").click().run()
    app.button(key="bench-confirm").click().run()
    assert not app.exception, app.exception
    assert any("Rapport écrit à côté du projet" in s.value for s in app.success)
    assert len(list(tmp_path.glob("banc-essai-*.md"))) == 1
    assert path.read_bytes() == before  # the project is not touched


def test_why_links_were_missed():
    """v0.6, step 2: each missed link is classified, and undone right choices counted."""
    key = {"a": "Q1", "b": "Q2", "c": "none", "d": "Q4", "e": "Q5", "f": "Q6", "g": "none"}
    candidates = {"a": ["Q1"], "b": ["Q3"], "c": ["Q7"], "d": ["Q4", "Q8"], "e": ["Q5"]}
    # f and g have no candidate: they are not sent to the model, which answers nothing.
    proposed = {"a": "Q1", "b": "Q3", "c": "Q7", "d": "Q8", "e": None, "f": None, "g": None}
    computed = {"a": "Q1", "b": "Q3", "c": "Q7", "d": "Q4", "e": "Q5", "f": "none", "g": "none"}
    missed, undone = bench.classify_misses(key, candidates, proposed, computed)
    assert missed == {
        "no_candidate": ["b", "f"],
        "wrong_choice": ["d"],
        "not_asked": ["c"],
        "no_answer": ["e", "g"],
    }
    assert undone == ["d", "e"]  # not g: the model never saw it


def test_the_report_says_why():
    _progress, results = _run(Server())
    report = bench.render_report(
        results, model=MODEL, endpoint="https://ia.universite.example/v1", date="2026-10-14"
    )
    assert "Pourquoi les rattachements du modèle ont été manqués" in report
    assert "Bonne question absente des candidates" in report
    sleep = results[0]
    assert sum(len(v) for v in sleep.missed.values()) == len(sleep.model_wrong)


class CountingServer(Server):
    """The same answers, with the tokens a service reports (v0.18)."""

    def __call__(self, request):
        response = super().__call__(request)
        data = response.json()
        data["usage"] = {"prompt_tokens": 1000, "completion_tokens": 100}
        return httpx.Response(response.status_code, json=data)


def test_tokens_cost_and_level_2():
    """v0.18: the blocks of an API key, the tokens and cost of each pass, and the labels at
    level 2 (with statistics) next to level 1, for the bench only (D-136)."""
    server = CountingServer()
    client = institution(MODEL, server)
    items = list(bench.run_bench(client, now=lambda: NOW, clock=_clock(), level2=True))
    results = [i for i in items if not isinstance(i, str)]
    bases = [r for r in results if isinstance(r, bench.BaseResult)]
    assert all(r.level2 is not None and r.level2.n_enriched == r.n_enriched for r in bases)
    assert all(r.link_tokens["input"] and r.enrich_tokens["output"] for r in bases)
    level2 = [m for m in server.sent if '"pct_missing"' in m]
    assert level2 and len(level2) < len(server.sent)  # level 1 sends no statistic
    report = bench.render_report(
        results, model="claude-haiku-5-5", endpoint="https://api.anthropic.com", date="2026-10-19"
    )
    assert "## Libellés : niveau 1 et niveau 2" in report
    assert "## Jetons et coût" in report and " $ |" in report
    calls = len(server.sent)
    assert f"**{1000 * calls}** | **{100 * calls}**" in report


def test_cost_at_the_published_prices():
    million = Counter(input=1_000_000, output=1_000_000)
    assert bench.cost("claude-haiku-5-5", million) == pytest.approx(0.60)
    assert bench.cost("claude-sonnet-5-5", million) == pytest.approx(12.00)
    assert bench.cost("modele-inconnu", million) is None
