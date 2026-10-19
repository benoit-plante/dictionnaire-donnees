"""Step 11: enrichment block by block — proposals, human decisions kept, resume, logs."""

import json

import httpx
import pytest

from ddict.cli import main
from ddict.export import render_markdown
from ddict.io import read_sav
from ddict.llm.enrich import enrich
from ddict.project import build_project, load_project, validate
from ddict.project.model import TrackedValue
from fake_ai import institution, serve_commands

NOW = "2026-10-13T16:00:00"


def _answer(body, describe=None):
    content = json.loads(body["messages"][1]["content"])
    variables = []
    for v in content["variables"]:
        description = describe(v["name"]) if describe else f"Description de {v['name']}."
        variables.append(
            {
                "name": v["name"],
                "label": f"Libellé IA {v['name']}",
                "description": description,
            }
        )
    return {"block": content["block"], "variables": variables}


class Server:
    def __init__(self, describe=None, fail_after=None):
        self.describe = describe
        self.fail_after = fail_after
        self.status = None  # an HTTP error to answer instead
        self.calls = 0

    def __call__(self, request):
        self.calls += 1
        if self.status is not None:
            return httpx.Response(self.status, text="model not found")
        if self.fail_after is not None and self.calls > self.fail_after:
            raise httpx.ConnectError("refused", request=request)
        body = json.loads(request.content)
        text = json.dumps(_answer(body, self.describe), ensure_ascii=False)
        return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


@pytest.fixture
def project(fictional_files):
    return build_project(read_sav(fictional_files["etude-sommeil.sav"]))


def _run(project, server, **kwargs):
    client = institution("modele-test", server)
    return list(enrich(project, client, now=lambda: NOW, block_size=12, **kwargs))


def test_every_variable_gets_proposals(project):
    events = _run(project, Server())
    assert [e.result.run.outcome for e in events] == ["succeeded"] * 3
    assert [r.run_id for r in project.ai_runs] == ["run-0001", "run-0002", "run-0003"]
    q1 = project.variable("sommeil_q1")
    assert (q1.label.value, q1.label.origin, q1.label.status, q1.label.ai_run) == (
        "Libellé IA sommeil_q1",
        "ai",
        "proposed",
        "run-0001",
    )
    assert q1.description.value == "Description de sommeil_q1."
    assert project.variable("sommeil_q3").issues == []


def test_pending_issues_from_an_older_prompt_are_dropped(project):
    """D-009: issues are no longer asked; those a person accepted stay."""
    q3 = project.variable("sommeil_q3")
    old = {"origin": "ai", "ai_run": "run-0000"}
    q3.issues = [
        TrackedValue[str](value="En attente", status="proposed", **old),
        TrackedValue[str](value="Acceptée", status="validated", **old),
    ]
    _run(project, Server())
    assert [i.value for i in project.variable("sommeil_q3").issues] == ["Acceptée"]


def test_file_label_stays_until_the_proposal_is_accepted(project):
    _run(project, Server())
    report = render_markdown(project, kind="final")
    assert "### `sommeil_q1` — Q1 endormissement" in report
    assert "Libellé IA" not in report
    project.variable("sommeil_q1").label = validate(project.variable("sommeil_q1").label, now=NOW)
    assert "### `sommeil_q1` — Libellé IA sommeil_q1" in render_markdown(project, kind="final")


def test_human_decisions_are_never_replaced(project):
    q2 = project.variable("sommeil_q2")
    q2.description = TrackedValue[str](value="Écrite par l'équipe.", origin="human")
    _run(project, Server())
    first = project.variable("sommeil_q4")
    first.label = validate(first.label, now=NOW)
    _run(project, Server(), redo=True)
    assert project.variable("sommeil_q2").description.value == "Écrite par l'équipe."
    assert project.variable("sommeil_q4").label.status == "validated"
    assert project.variable("sommeil_q4").label.ai_run == "run-0001"
    # A pending proposal is replaced by the newer one.
    assert project.variable("sommeil_q5").label.ai_run == "run-0004"


def test_resume_skips_blocks_already_done(project):
    server = Server(fail_after=1)
    events = _run(project, server)
    assert [e.result.run.outcome for e in events] == ["succeeded", "failed"]
    assert project.ai_runs[-1].detail == "connection"  # stops: the server is down
    events = _run(project, Server())
    assert [e.result is None for e in events] == [True, False, False]
    assert [r.outcome for r in project.ai_runs] == ["succeeded", "failed", "succeeded", "succeeded"]


def test_another_model_is_not_considered_done(project):
    _run(project, Server())
    other = institution("autre-modele", Server())
    events = list(enrich(project, other, now=lambda: NOW, block_size=12))
    assert all(e.result is not None for e in events)


def test_inventions_are_flagged(project):
    def describe(name):
        return "Un score ≥ 14 selon Beck et al. (1996)." if name == "sommeil_q1" else ""

    _run(project, Server(describe=describe))
    assert project.variable("sommeil_q1").ai_signals == [
        "description:citation",
        "description:threshold",
    ]
    assert project.variable("sommeil_q2").ai_signals == []
    assert project.variable("sommeil_q2").description.value is None  # empty: no proposal


def test_project_saved_after_each_block_and_exchanges_logged(project, tmp_path, generator):
    saved = []
    _run(project, Server(), save=lambda p: saved.append(len(p.ai_runs)), log_dir=tmp_path)
    assert saved == [1, 2, 3]
    files = sorted(p.name for p in tmp_path.iterdir())
    assert files == ["run-0001-b-001.json", "run-0002-b-002.json", "run-0003-b-003.json"]
    record = json.loads((tmp_path / files[0]).read_text(encoding="utf-8"))
    assert record["run"]["message_sha256"] == project.ai_runs[0].message_sha256
    assert "Libellé IA id_participant" in record["answers"][0]
    text = "".join(p.read_text(encoding="utf-8") for p in tmp_path.iterdir())
    for canary in generator.CANARIES:
        assert canary not in text


@pytest.fixture
def fake_server(monkeypatch):
    """The command line goes through the AI settings: here the fake server (v0.18)."""
    server = Server()
    serve_commands(monkeypatch, server, model="modele-test")
    return server


def _profiled(fictional_files, tmp_path, allow=True):
    project_path = tmp_path / "etude.dd.json"
    main(["profiler", str(fictional_files["etude-sommeil.sav"]), "-o", str(project_path)])
    if allow:
        assert main(["ia", "autoriser", str(project_path)]) == 0
    return project_path


def test_command(fictional_files, tmp_path, capsys, fake_server):
    project_path = _profiled(fictional_files, tmp_path)
    assert main(["enrichir", str(project_path), "--taille-bloc", "8"]) == 0
    out = capsys.readouterr().out
    assert "Bloc b-001 (8 variables) : réussi." in out
    project = load_project(project_path)
    assert len(project.ai_runs) == 5
    assert {r.model for r in project.ai_runs} == {"modele-test"}  # from the settings
    assert project.variable("anx1").label.status == "proposed"
    assert len(list((tmp_path / "etude.dd-envois").glob("run-*.json"))) == 5
    assert main(["enrichir", str(project_path), "--taille-bloc", "8"]) == 0
    assert "déjà fait" in capsys.readouterr().out
    assert fake_server.calls == 5


def test_blocks_of_25_through_an_api_key(fictional_files, tmp_path, capsys, fake_server):
    project_path = _profiled(fictional_files, tmp_path)
    assert main(["enrichir", str(project_path)]) == 0
    assert "Bloc b-001 (25 variables) : réussi." in capsys.readouterr().out
    assert fake_server.calls == 2


def test_command_explains_a_missing_model(fictional_files, tmp_path, capsys, fake_server):
    project_path = _profiled(fictional_files, tmp_path)
    capsys.readouterr()
    fake_server.status = 404
    assert main(["enrichir", str(project_path), "--modele", "modele-absent"]) == 2
    out, err = capsys.readouterr()
    assert "« modele-absent » est introuvable" in err
    assert "Aucune nouvelle proposition" in err and "à réviser" not in out


def test_command_needs_a_model(fictional_files, tmp_path, capsys):
    """Anthropic has a default model (D-140); an institution's server has none."""
    project_path = _profiled(fictional_files, tmp_path)
    capsys.readouterr()
    command = ["enrichir", str(project_path), "--protocole", "openai"]
    assert main([*command, "--adresse", "https://ia.universite.example/v1"]) == 2
    assert "--modele" in capsys.readouterr().err


def test_command_without_a_key_sends_nothing(fictional_files, tmp_path, capsys):
    project_path = _profiled(fictional_files, tmp_path)
    capsys.readouterr()
    assert main(["enrichir", str(project_path)]) == 2  # the default model, no key recorded
    assert "ddict ia cle" in capsys.readouterr().err


def test_command_refuses_a_project_not_allowed(fictional_files, tmp_path, capsys, fake_server):
    project_path = _profiled(fictional_files, tmp_path, allow=False)
    capsys.readouterr()
    assert main(["enrichir", str(project_path)]) == 2
    assert "ddict ia autoriser" in capsys.readouterr().err
    assert fake_server.calls == 0 and load_project(project_path).ai_runs == []
    assert main(["enrichir", str(project_path), "--apercu"]) == 0  # the preview, always


def test_command_refuses_a_plain_http_address(fictional_files, tmp_path, capsys):
    project_path = _profiled(fictional_files, tmp_path)
    capsys.readouterr()
    code = main(
        ["enrichir", str(project_path), "--modele", "m", "--adresse", "http://ia.example.com/v1"]
    )
    assert code == 2
    assert "Adresse refusée" in capsys.readouterr().err
    assert load_project(project_path).ai_runs == []


def test_label_guessed_without_a_file_label_is_flagged(project):
    _run(project, Server())
    assert project.variable("sommeil_q7").file.label is None
    assert project.variable("sommeil_q7").ai_signals == ["label:no_file_label"]
    assert project.variable("sommeil_q8").ai_signals == []


def test_labels_are_not_flagged_when_the_file_has_none(project):
    """In a CSV every label is a guess: flagging them all would flag nothing."""
    for entry in project.variables:
        entry.file.label = None
    _run(project, Server())
    assert all("label:no_file_label" not in e.ai_signals for e in project.variables)
