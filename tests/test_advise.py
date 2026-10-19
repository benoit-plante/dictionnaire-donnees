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
from ddict import ai_settings
from ddict.analysis.catalogue import CATALOGUE
from ddict.cli import main
from ddict.llm.advice_bench import (
    FOLLOW_UP_FILE,
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
from ddict.project import load_project, save_project
from fake_ai import institution, serve_commands
from test_analysis_data import EXAMPLES, KEY, analyses_project

APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")
NOW = "2026-10-16T12:00:00"
OBJECTIVES = load_objectives(EXAMPLES)["objectives"]
FOLLOW_UP = load_objectives(EXAMPLES, FOLLOW_UP_FILE)  # v0.14: the widened catalogue
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
    with institution("modele-test", server) as client:
        found = advise(project, client, GOAL, now=NOW, log_dir=tmp_path)
    return found, server


# --- What the model reads. ---


def test_the_message_holds_metadata_only(project):
    block = build_advice_block(project, GOAL)
    content = json.loads(block.messages[1]["content"])
    assert content["objective"] == content["objective_again"] == GOAL
    assert list(content)[-1] == "objective_again"  # repeated after the long lists
    assert [a["key"] for a in content["analyses"]] == [
        "table1", "t_test", "paired", "rm_anova", "anova", "chi_square", "correlation",
        "regression", "logistic", "partial", "moderation",
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
            "label": "5 items, préfixe « bienetre »",  # never the observed codes (D-136)
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


def test_advise_v3_sends_whole_labels_and_the_items_labels(project, monkeypatch):
    """For Anthropic (v0.18, B3): no compression of D-080, one bound only."""
    monkeypatch.setattr(advise_module, "MAX_LABEL_CHARS", 10)  # v2 would cut every label
    block = build_advice_block(project, GOAL, "advise-v3")
    assert block.prompt_version == "advise-v3"
    assert "chacun [nom, libellé]" in block.messages[0]["content"]
    content = json.loads(block.messages[1]["content"])
    variables = {n: label for pairs in content["variables"].values() for n, label in pairs}
    assert variables["groupe"] == "Groupe de l'étude"  # whole
    group = content["groups"][0]
    assert group["label"] == "5 items, préfixe « bienetre »"
    assert [n for n, _label in group["items"]] == [f"bienetre_{k}" for k in range(1, 6)]
    assert any("énergique" in label for _n, label in group["items"])  # the items' labels
    assert "…" not in block.messages[1]["content"]
    compact = build_advice_block(project, GOAL)
    assert compact.prompt_version == "advise-v2" and "…" in compact.messages[1]["content"]


def test_advise_v3_one_bound(project, monkeypatch):
    monkeypatch.setattr(advise_module, "MAX_MESSAGE_TOKENS", 10)  # D-080's: not this one's
    assert build_advice_block(project, GOAL, "advise-v3")
    monkeypatch.setattr(advise_module, "MAX_MESSAGE_CHARS", 2000)
    with pytest.raises(AdviceError) as error:
        build_advice_block(project, GOAL, "advise-v3")
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


def _anthropic_advise(project, content):
    def reply(request):
        body = json.loads(request.content)
        sent.append(body["output_config"]["format"]["schema"])
        systems.append(body["system"])
        text = json.dumps(content, ensure_ascii=False)
        return httpx.Response(
            200, json={"content": [{"type": "text", "text": text}], "stop_reason": "end_turn"}
        )

    sent, systems = [], []
    with client_module.AnthropicClient(
        "claude-haiku-5-5", key=lambda: "sk-ant-FAUSSE", transport=httpx.MockTransport(reply)
    ) as client:
        found = advise(project, client, GOAL, now=NOW)
    return found, sent


def test_anthropic_gets_the_flat_schema(project):
    """The strict schema's grammar is "too large" for Anthropic (v0.18, A5): one list of the
    analyses, the roles, the methods and the variables; the checks stay on this computer."""
    found, sent = _anthropic_advise(project, answer(T_TEST))
    assert found.result.run.outcome == "succeeded"
    assert found.result.run.prompt_version == "advise-v3"  # the whole message (B3)
    assert found.proposals[0].chosen == {"outcome": ["bienetre_total"], "group": ["groupe"]}
    proposal = sent[0]["properties"]["proposals"]["items"]
    assert "anyOf" not in json.dumps(sent[0])
    assert proposal["properties"]["analysis"]["enum"] == list(CATALOGUE)
    variables = proposal["properties"]["roles"]["items"]["properties"]["variables"]
    assert variables["items"]["enum"] == list(usable(project))
    # What the grammar no longer stops is refused here, or shown before a person confirms.
    for wrong, detail in [
        ({"roles": [{"role": "rows", "variables": ["groupe"]}]}, "unknown_role"),
        ({"method": "spearman"}, "unknown_method"),
    ]:
        refused, _sent = _anthropic_advise(project, answer(T_TEST | wrong))
        assert refused.result.run.detail == detail
    unfit = T_TEST | {"roles": [{"role": "outcome", "variables": ["groupe"]},
                                {"role": "group", "variables": ["stress"]}]}  # fmt: skip
    shown, _sent = _anthropic_advise(project, answer(unfit))
    assert not shown.proposals[0].check.ok


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
def fake_server(monkeypatch):
    server = Server(answer(T_TEST))
    serve_commands(monkeypatch, server)
    return server


def test_the_command(tmp_path, capsys, fake_server):
    path = _folder(tmp_path)
    assert main(["conseiller", str(path), GOAL, "--apercu"]) == 0
    preview = path.with_name("etude-analyses.dd-envois") / "apercu" / "a-001.json"
    assert GOAL in preview.read_text(encoding="utf-8")
    assert '"prompt_version": "advise-v2"' in preview.read_text(encoding="utf-8")
    assert main(["conseiller", str(path), GOAL]) == 2  # the project does not allow it
    assert "ddict ia autoriser" in capsys.readouterr().err
    assert not fake_server.requests
    assert main(["ia", "autoriser", str(path)]) == 0
    assert main(["conseiller", str(path), GOAL]) == 0
    out = capsys.readouterr().out
    assert "1. Test t : comparer deux groupes" in out
    assert "Variable dépendante : bienetre_total" in out and "rien n'est calculé" in out
    assert load_project(path).ai_runs == []
    assert main(["conseiller", str(path), " "]) == 2


def test_the_command_previews_what_anthropic_gets(tmp_path):
    path = _folder(tmp_path)
    assert main(["conseiller", str(path), GOAL, "--apercu", "--protocole", "anthropic"]) == 0
    preview = path.with_name("etude-analyses.dd-envois") / "apercu" / "a-001.json"
    assert '"prompt_version": "advise-v3"' in preview.read_text(encoding="utf-8")


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_page_takes_a_proposal_up(tmp_path, monkeypatch):
    """v0.18: through the AI settings (here an institution's server), for a project that
    allows it."""
    server = Server(answer(T_TEST))
    real = client_module.OpenAICompatibleClient

    class Client(real):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, transport=httpx.MockTransport(server), **kwargs)

    monkeypatch.setattr(client_module, "OpenAICompatibleClient", Client)
    ai_settings.save(ai_settings.AiSettings("openai", "https://ia.universite.example/v1", "m"))
    path = _folder(tmp_path)
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "analyses"
    app.run()
    assert app.button(key="advice-ask").disabled  # no objective yet
    app.text_area(key="advice-goal").input(GOAL).run()
    assert app.button(key="advice-ask").disabled  # the project does not allow it yet
    assert any("n'est pas permis pour ce projet" in i.value for i in app.info)
    app.checkbox(key="ai-allowed").check().run()
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
    item = next(o for o in [*OBJECTIVES, *FOLLOW_UP["objectives"]]
                if o["objective"] == objective)  # fmt: skip
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


@pytest.mark.parametrize("follow_up", [False, True])
def test_the_bench_scores_the_key_as_right(follow_up):
    """Every role and method of the catalogue gets through the answer's model: the
    follow-up objectives use those of v0.14 (paired, repeated measures, moderation...)."""

    def server(request):
        text = json.dumps(_expected_answer(json.loads(request.content)))
        return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})

    objectives = FOLLOW_UP["objectives"] if follow_up else OBJECTIVES
    project = bench_project(EXAMPLES, FOLLOW_UP["sav"] if follow_up else None)
    with institution("modele-test", server) as client:
        scores = run_advice_bench(project, client, objectives, now=lambda: NOW, clock=lambda: 0.0)
    total = len(objectives)
    assert summary(scores) == {
        "objectives": total,
        "valid_answers": total,
        "first_analysis": total,
        "first_right": total,
        "any_right": total,
        "refused_conditions": 0,
        "input_tokens": 0,  # the fake server gives no usage
        "output_tokens": 0,
    }
    if not follow_up:
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
