"""v0.9, step 7: the local model proposes analyses of the catalogue (D-073, D-079), against a
fake server: metadata only in the message, nothing outside the catalogue and the project in
the answer, conditions checked, a person takes a proposal up or not."""

import json
import shutil
from pathlib import Path

import httpx
import pytest
from streamlit.testing.v1 import AppTest

import ddict.llm.advise as advise_module
import ddict.llm.client as client_module
from ddict.analysis.catalogue import CATALOGUE
from ddict.cli import main
from ddict.llm.advice_bench import (
    bench_project,
    load_objectives,
    run_advice_bench,
    score,
    summary,
)
from ddict.llm.advise import (
    MAX_LABEL_CHARS,
    MAX_OBJECTIVE_CHARS,
    AdviceError,
    Proposal,
    _common_start,
    _short,
    advice_schema,
    advise,
    build_advice_block,
    usable,
)
from ddict.llm.client import LocalModelClient
from ddict.project import load_project, save_project
from test_analysis_data import EXAMPLES, KEY, analyses_project

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
NOW = "2026-10-16T12:00:00"
OBJECTIVES = load_objectives(EXAMPLES)["objectives"]
GOAL = "Comparer le bien-être entre les groupes intervention et contrôle."
T_TEST = {
    "analysis": "t_test",
    "roles": [
        {"role": "outcome", "variables": ["bienetre_total"]},
        {"role": "group", "variables": ["groupe"]},
    ],
    "method": "",
    "reason": "Deux groupes et un score continu.",
}


def answer(*proposals, block="a-001", **extra):
    return {"block": block, "proposals": list(proposals), **extra}


class Server:
    """Answers every request with the same content; keeps the requests."""

    def __init__(self, content):
        self.content = content
        self.requests = []

    def __call__(self, request):
        self.requests.append(json.loads(request.content))
        text = self.content if isinstance(self.content, str) else json.dumps(self.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


@pytest.fixture(scope="module")
def project():
    return analyses_project()


def _advise(project, content, tmp_path=None):
    server = Server(content)
    with LocalModelClient("modele-test", transport=httpx.MockTransport(server)) as client:
        found = advise(project, client, GOAL, now=NOW, log_dir=tmp_path)
    return found, server


# --- What the model reads. ---


def test_the_message_holds_metadata_only(project):
    block = build_advice_block(project, GOAL)
    content = json.loads(block.messages[1]["content"])
    assert content["objective"] == content["objective_again"] == GOAL
    assert list(content)[-1] == "objective_again"  # repeated after the long lists
    assert [a["key"] for a in content["analyses"]] == [
        "table1", "t_test", "paired", "anova", "chi_square", "correlation", "regression",
        "logistic", "partial", "moderation",
    ]  # fmt: skip
    # D-080: the variables by measure level, each [name, label]: no value, no statistic.
    assert set(content["variables"]) == {"scale", "ordinal", "nominal"}
    variables = {
        name: (level, label)
        for level, pairs in content["variables"].items()
        for name, label in pairs
    }
    assert variables["bienetre_total"] == ("scale", "bienetre_total (score de G1)")
    assert variables["groupe"] == ("nominal", "Groupe de l'étude")
    assert "id_participant" not in variables  # an identifier: left out, as from the analyses
    # D-080: a group of items is one entry, its items by name only.
    assert content["groups"] == [
        {
            "group": "G1",
            "label": "5 items, codes de 1 à 5, préfixe « bienetre »",
            "level": "ordinal",
            "items": ["bienetre_1", "bienetre_2", "bienetre_3", "bienetre_4", "bienetre_5"],
            "score": "bienetre_total",
        }
    ]
    assert "bienetre_1" not in variables and "bienetre_1" in block.names
    text = block.messages[1]["content"]
    assert "Nord" not in text and "999" not in text  # no value label, no missing code
    assert "énergique" not in text  # an item's own label is left out of its group


def test_a_long_label_and_the_common_start_of_a_grid():
    assert _common_start(["Au travail, je me sens calme", "Au travail, je me sens las"]) == (
        "Au travail, je me sens"
    )
    assert _common_start(["Calme", "Las"]) == ""  # nothing in common: the group's description
    assert len(_short("mot " * 40)) == MAX_LABEL_CHARS


def test_a_base_too_large_for_the_model(project, monkeypatch):
    monkeypatch.setattr(advise_module, "MAX_MESSAGE_TOKENS", 500)
    with pytest.raises(AdviceError) as error:
        build_advice_block(project, GOAL)
    assert error.value.reason == "too_large"


def test_the_objective_is_checked(project):
    with pytest.raises(AdviceError) as error:
        build_advice_block(project, "   ")
    assert error.value.reason == "empty"
    with pytest.raises(AdviceError) as error:
        build_advice_block(project, "x" * (MAX_OBJECTIVE_CHARS + 1))
    assert error.value.reason == "too_long"


def test_the_schema_ties_roles_and_variables_to_each_analysis(project):
    schema = advice_schema(project)
    assert schema["properties"]["block"]["enum"] == ["a-001"]
    assert schema["properties"]["proposals"]["maxItems"] == 3
    variants = {
        v["properties"]["analysis"]["enum"][0]: v
        for v in schema["properties"]["proposals"]["items"]["anyOf"]
    }
    assert list(variants) == list(CATALOGUE)
    for variant in variants.values():
        assert variant["additionalProperties"] is False  # no field for code or a threshold
    t_test = variants["t_test"]["properties"]
    assert t_test["method"]["enum"] == ["", "welch", "student", "mann_whitney"]
    roles = {r["properties"]["role"]["enum"][0]: r["properties"]["variables"]
             for r in t_test["roles"]["prefixItems"]}  # fmt: skip
    assert list(roles) == ["outcome", "group"]  # each once, in order, both required
    assert t_test["roles"]["minItems"] == t_test["roles"]["maxItems"] == 2
    table1 = variants["table1"]["properties"]["roles"]
    assert (table1["minItems"], table1["maxItems"]) == (1, 2)  # the group is optional
    assert "stress" in roles["outcome"]["items"]["enum"]
    assert "groupe" not in roles["outcome"]["items"]["enum"]  # nominal: not an outcome
    assert "groupe" in roles["group"]["items"]["enum"]
    assert roles["outcome"]["maxItems"] == 1  # a list that ends
    every = {n for v in variants.values() for r in v["properties"]["roles"]["prefixItems"]
             for n in r["properties"]["variables"]["items"]["enum"]}  # fmt: skip
    assert every == set(usable(project)) and "id_participant" not in every


# --- What it may answer. ---


def test_a_good_answer(project, tmp_path):
    regression = {
        "analysis": "regression",
        "roles": [
            {"role": "outcome", "variables": ["satisfaction"]},
            {"role": "predictors", "variables": ["soutien", "charge"]},
        ],
        "method": "",
        "reason": "Plusieurs prédicteurs.",
    }
    found, server = _advise(project, answer(T_TEST, regression), tmp_path)
    assert found.result.run.outcome == "succeeded"
    first, second = found.proposals
    assert first.chosen == {"outcome": ["bienetre_total"], "group": ["groupe"]}
    assert first.options == {} and first.check.ok
    assert second.chosen["predictors"] == ["soutien", "charge"]
    sent = server.requests[0]["response_format"]["json_schema"]["schema"]
    assert sent == advice_schema(project)
    logged = json.loads(next(tmp_path.glob("conseil-*-a-001.json")).read_text(encoding="utf-8"))
    assert (
        logged["messages"][1]["content"] == build_advice_block(project, GOAL).messages[1]["content"]
    )
    assert project.ai_runs == []  # D-079: nothing recorded in the project


@pytest.mark.parametrize(
    ("content", "detail"),
    [
        (answer(T_TEST | {"analysis": "modele_mixte"}), "schema"),  # outside the catalogue
        (answer(T_TEST | {"code": "t.test(x ~ g)"}), "schema"),  # code: no field for it
        (answer(T_TEST | {"seuil": 0.05}), "schema"),  # a threshold: no field for it
        (answer(T_TEST, conclusion="significatif"), "schema"),
        (answer(T_TEST | {"roles": [{"role": "outcome", "variables": ["inventee"]}]}),
         "unknown_variable"),
        (answer(T_TEST | {"roles": [{"role": "outcome", "variables": ["id_participant"]}]}),
         "unknown_variable"),  # left out of the message, so refused in the answer
        (answer(T_TEST | {"roles": [{"role": "rows", "variables": ["groupe"]}]}),
         "unknown_role"),
        (answer(T_TEST | {"method": "spearman"}), "unknown_method"),
        (answer(T_TEST, T_TEST, T_TEST, T_TEST), "schema"),  # at most three
        (answer(T_TEST, block="a-002"), "block_mismatch"),
        ("Je propose un test t.", "not_json"),
    ],
)  # fmt: skip
def test_refused_answers(project, content, detail):
    found, server = _advise(project, content)
    assert found.proposals is None
    assert (found.result.run.outcome, found.result.run.detail) == ("invalid_response", detail)
    assert len(server.requests) == 2  # one more try, then nothing


def test_conditions_are_flagged(project):
    ordinal = T_TEST | {"roles": [{"role": "outcome", "variables": ["sport"]},
                                  {"role": "group", "variables": ["groupe"]}]}  # fmt: skip
    found, _server = _advise(project, answer(ordinal))
    assert "sport : niveau « ordinal »" in found.proposals[0].check.refusals[0]


def test_no_analysis_fits(project):
    found, _server = _advise(project, answer())
    assert found.result.run.outcome == "succeeded" and found.proposals == ()


# --- The command and the page. ---


def _folder(tmp_path):
    folder = tmp_path / "projet"
    folder.mkdir()
    shutil.copy(EXAMPLES / KEY["sav"], folder / KEY["sav"])
    path = folder / "etude-analyses.dd.json"
    save_project(analyses_project(), path)
    return path


@pytest.fixture
def fake_ollama(monkeypatch):
    server = Server(answer(T_TEST))
    real = client_module.LocalModelClient.__init__

    def init(self, model, *, endpoint=client_module.DEFAULT_ENDPOINT, **kwargs):
        real(self, model, endpoint=endpoint, transport=httpx.MockTransport(server))

    monkeypatch.setattr(client_module.LocalModelClient, "__init__", init)
    return server


def test_the_command(tmp_path, capsys, fake_ollama):
    path = _folder(tmp_path)
    assert main(["conseiller", str(path), GOAL, "--apercu"]) == 0
    preview = path.with_name("etude-analyses.dd-envois") / "apercu" / "a-001.json"
    assert GOAL in preview.read_text(encoding="utf-8")
    assert not fake_ollama.requests
    assert main(["conseiller", str(path), GOAL, "--modele", "qwen-test"]) == 0
    out = capsys.readouterr().out
    assert "1. Test t : comparer deux groupes" in out
    assert "Variable dépendante : bienetre_total" in out and "rien n'est calculé" in out
    assert load_project(path).ai_runs == []
    assert main(["conseiller", str(path), " ", "--modele", "qwen-test"]) == 2


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_page_takes_a_proposal_up(tmp_path, fake_ollama):
    path = _folder(tmp_path)
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "analyses"
    app.run()
    assert app.button(key="advice-ask").disabled  # no objective yet
    app.text_area(key="advice-goal").input(GOAL).run()
    app.button(key="advice-ask").click().run()
    assert not app.exception, app.exception
    assert any("Test t : comparer deux groupes" in m.value for m in app.markdown)
    assert "analysis-result" not in app.session_state  # nothing computed
    app.button(key="advice-take-1").click().run()
    assert app.selectbox(key="analysis-key").value == "t_test"
    assert app.selectbox(key="analysis-t_test-outcome").value == "bienetre_total"
    assert app.selectbox(key="analysis-t_test-group").value == "groupe"
    app.button(key="analysis-run").click().run()
    assert any("t(297,29) = 5,00" in m.value for m in app.markdown)


# --- The bench. ---


def _expected_answer(body):
    """The answer key's proposal for the objective of the request."""
    objective = json.loads(body["messages"][1]["content"])["objective"]
    item = next(o for o in OBJECTIVES if o["objective"] == objective)
    expected = item["expected"]
    if expected is None:
        return answer()
    roles = dict(expected["roles"])
    if expected["analysis"] == "chi_square":
        first, second = roles.pop("variables")
        roles = {"rows": [first], "columns": [second]}
    proposal = {
        "analysis": expected["analysis"],
        "roles": [{"role": r, "variables": names} for r, names in roles.items()],
        "method": expected.get("method", ""),
        "reason": "Selon le corrigé.",
    }
    return answer(proposal)


def test_the_bench_scores_the_key_as_right(tmp_path):
    def server(request):
        text = json.dumps(_expected_answer(json.loads(request.content)))
        return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})

    project = bench_project(EXAMPLES)
    with LocalModelClient("modele-test", transport=httpx.MockTransport(server)) as client:
        scores = run_advice_bench(project, client, OBJECTIVES, now=lambda: NOW, clock=lambda: 0.0)
    total = len(OBJECTIVES)
    assert summary(scores) == {
        "objectives": total,
        "valid_answers": total,
        "first_analysis": total,
        "first_right": total,
        "any_right": total,
        "refused_conditions": 0,
    }
    assert next(s for s in scores if s.objective == "o09").method_right is True


def test_the_bench_counts_misses():
    expected = {"analysis": "correlation", "roles": {"variables": ["sport", "stress"]},
                "method": "spearman"}  # fmt: skip
    wrong = Proposal("correlation", {"variables": ["sport", "age"]}, {}, "")
    right = Proposal("correlation", {"variables": ["stress", "sport"]}, {}, "")
    found = score(expected, (wrong, right))
    assert found == {"first_analysis": True, "first_right": False, "any_right": True,
                     "method_right": False}  # fmt: skip
    assert score(None, (right,))["first_right"] is False  # nothing fits: nothing proposed
    assert score(None, ())["first_right"] is True


def test_an_invalid_answer_is_never_right():
    assert score(None, None)["first_right"] is False
    expected = {"analysis": "anova", "roles": {"outcome": ["stress"], "group": ["region"]}}
    assert score(expected, None)["any_right"] is False
