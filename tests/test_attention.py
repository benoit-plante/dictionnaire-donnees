"""v0.21, step 10 (§ 5.3 of the plan, D-170): the attention checks. The rule "attention"
(failures counted, the empty a failure or ignored, a check not asked never failed), its
refusals, its sentence; the signal of the page "Méthode" and "En faire une règle", which
fills the form without applying anything; the command line; the same counts in the tool,
PSPP and R. Nothing real: the base of `scripts/generer_base_filtres.py`."""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pyreadstat
import pytest
from streamlit.testing.v1 import AppTest

from ddict import arrival
from ddict.analysis import quality
from ddict.analysis.data import apply_decisions
from ddict.export.preparation import render_preparation
from ddict.export.syntax import write_syntax
from ddict.io.load import read_database
from ddict.project import exclusions, load_project, save_project
from ddict.project.exclusions import ExclusionRefused
from test_syntax import _pspp, _rscript

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
BASE = EXAMPLES / "reponses-filtres.sav"
KEY = json.loads((EXAMPLES / "corrige-filtres.json").read_text(encoding="utf-8"))
CHECKS = [("climat_SQ007", ["4"]), ("controle", ["1"])]
TODAY = "2026-10-21"


def _generator():
    script = ROOT / "scripts" / "generer_base_filtres.py"
    spec = importlib.util.spec_from_file_location("generer_base_filtres", script)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def project():
    found = _generator().project()
    arrival.receive(found, BASE)
    return found


@pytest.fixture(scope="module")
def table():
    return read_database(BASE).table


def _rule(project, least=1, empty="ignored"):
    data = exclusions.attention_data(project, CHECKS, least, empty)
    return exclusions.add(project, {**data, "reason": "Items de contrôle échoués"})


@pytest.mark.parametrize(
    ("least", "empty"), [(1, "ignored"), (1, "failed"), (2, "ignored"), (2, "failed")]
)
def test_the_rule_counts_as_the_answer_key(project, table, least, empty):
    _rule(project, least, empty)
    prepared = apply_decisions(project, table)
    assert prepared.flow.excluded == (("E1", KEY["attention_rule"][f"min{least}_{empty}"]),)


def test_the_signal_among_the_people_kept(project, table):
    found = quality.attention(project, apply_decisions(project, table))
    assert found.checks == (("climat_SQ007", ("4",)), ("controle", ("1",)))
    assert found.failed_one == KEY["attention_rule"]["min1_ignored"]
    assert found.failed_all == KEY["attention"]["both_failed"]
    assert found.empty == KEY["attention_any_empty"]
    text = quality.attention_text(found)
    assert text.startswith(f"{found.failed_one} personnes ont échoué à au moins un des 2 items")


@pytest.mark.parametrize(
    ("checks", "least", "empty", "reason"),
    [
        ([("inconnue", ["1"])], 1, "ignored", "variable inconnue"),
        ([("commentaires", ["x"])], 1, "ignored", "texte libre"),
        ([("controle", ["9"])], 1, "ignored", "n'est pas un code"),
        ([("controle", [])], 1, "ignored", "bonne réponse"),
        (CHECKS, 3, "ignored", "3 échecs exigés, mais la règle compte 2"),
        (CHECKS, 1, None, "laissé vide"),
        ([], 1, "ignored", "au moins un item"),
    ],
)
def test_a_rule_is_refused(project, checks, least, empty, reason):
    with pytest.raises((ExclusionRefused, ValueError)) as error:
        data = exclusions.attention_data(project, checks, least, empty)
        exclusions.add(project, {**data, "reason": "r"})
    assert reason in str(error.value) or any(reason in r for r in error.value.reasons)
    assert project.exclusions.rules == []


def test_the_rule_in_words(project):
    rule = _rule(project, 1, "failed")
    assert exclusions.rule_text(rule) == (
        "échec à au moins 1 des 2 items de contrôle (climat_SQ007 = 4, controle = 1) ; un item "
        "laissé vide compte comme un échec"
    )


def test_an_attention_check_is_never_a_member_of_its_grid_group(project):
    group = next(g for g in project.groups if "climat_SQ001" in (g.members.value or []))
    assert "climat_SQ007" not in group.members.value
    assert "climat_SQ007" in group.attached


def test_the_command_line(project, tmp_path, capsys):
    from ddict.cli import main

    path = tmp_path / "familles.dd.json"
    save_project(project, path)
    shutil.copy(BASE, tmp_path / BASE.name)
    code = main(["exclusions", "ajouter", str(path), "--attention", "climat_SQ007=4",
                 "controle=1", "--vide", "ignore", "--raison", "Items échoués"])  # fmt: skip
    assert code == 0, capsys.readouterr().err
    rule = load_project(path).exclusions.rules[0]
    assert (rule.kind, rule.min_failed, rule.empty) == ("attention", 1, "ignored")
    assert [c.correct for c in rule.checks] == [[4], [1]]
    assert main(["exclusions", "ajouter", str(path), "--attention", "controle=1",
                 "--raison", "x"]) == 2  # fmt: skip
    assert "laissé vide" in capsys.readouterr().err
    capsys.readouterr()
    assert main(["exclusions", "signaux", str(path)]) == 0
    assert "Items de contrôle : " in capsys.readouterr().out


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_page_makes_a_rule_without_applying_it(project, tmp_path):
    shutil.copy(BASE, tmp_path / BASE.name)
    path = tmp_path / "familles.dd.json"
    save_project(project, path)
    app = AppTest.from_file(str(ROOT / "src" / "ddict" / "review" / "app.py"), default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "method"
    app.run()
    assert not app.exception, app.exception
    assert any("ont échoué à au moins un des 2 items" in m.value for m in app.markdown)
    app.button(key="method-signal-attention").click().run()
    assert not app.exception, app.exception
    assert app.session_state["method-kind"] == "attention"
    assert app.session_state["method-new-attention"] == ["climat_SQ007", "controle"]
    assert app.session_state["method-new-right-controle"] == "1"
    assert load_project(path).exclusions.rules == []  # nothing applied
    app.radio(key="method-new-empty").set_value("ignored")
    app.text_input(key="method-new-reason").set_value("Items de contrôle échoués")
    app.button(key="method-add").click().run()
    assert not app.exception, app.exception
    [rule] = load_project(path).exclusions.rules
    assert rule.kind == "attention" and rule.empty == "ignored"


# --- In SPSS (PSPP) and R. ---


def _scripts_project():
    found = _generator().project()
    arrival.receive(found, BASE)
    _rule(found, 1, "failed")
    _rule(found, 2, "ignored")
    return found


def _flow(project, table):
    prepared = apply_decisions(project, table)
    return dict(prepared.flow.excluded), prepared.flow.analysed


@pytest.mark.skipif(_pspp() is None, reason="PSPP is not installed (D-027)")
def test_pspp_gives_the_same_counts(table, tmp_path):
    project = _scripts_project()
    flow, n = _flow(project, table)
    data, _meta = pyreadstat.read_sav(str(BASE), user_missing=True)
    bare = tmp_path / "bare.sav"
    pyreadstat.write_sav(data, str(bare))
    write_syntax(project, {"spss": tmp_path / "m.sps"}, TODAY)
    script = render_preparation(project, "spss", TODAY)
    (tmp_path / "all.sps").write_text(
        script.replace("SELECT IF (ddict_exclusion = 0).\n", ""), encoding="utf-8"
    )
    job = tmp_path / "job.sps"
    job.write_text(
        f"GET FILE='{bare}'.\nINSERT FILE='{tmp_path / 'm.sps'}' ENCODING='UTF-8'.\n"
        f"INSERT FILE='{tmp_path / 'all.sps'}' ENCODING='UTF-8'.\n"
        f"SAVE OUTFILE='{tmp_path / 'all.sav'}'.\n",
        encoding="utf-8",
    )
    done = subprocess.run([_pspp(), str(job)], capture_output=True, text=True, errors="replace")
    said = (done.stdout + done.stderr).lower()
    assert done.returncode == 0, said
    assert not any(w in said for w in ("error", "warning", "erreur", "avertissement")), said
    everyone, _meta = pyreadstat.read_sav(str(tmp_path / "all.sav"))
    counts = everyone["ddict_exclusion"].value_counts()
    assert {f"E{k}": int(counts.get(k, 0)) for k in (1, 2)} == flow
    assert int(counts.get(0, 0)) == n


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
def test_r_gives_the_same_counts(table, tmp_path):
    project = _scripts_project()
    flow, n = _flow(project, table)
    write_syntax(project, {"r": tmp_path / "m.R"}, TODAY)
    (tmp_path / "p.R").write_text(render_preparation(project, "r", TODAY), encoding="utf-8")
    out = tmp_path / "out.csv"
    job = tmp_path / "job.R"
    job.write_text(
        f'donnees <- haven::read_sav("{BASE.as_posix()}", user_na = TRUE)\n'
        f'source("{(tmp_path / "m.R").as_posix()}", encoding = "UTF-8")\n'
        'print <- function(x, ...) { assign("compte", x, envir = globalenv()); '
        "base::print(x, ...) }\n"
        f'source("{(tmp_path / "p.R").as_posix()}", encoding = "UTF-8")\n'
        "rm(print)\n"
        f'write.csv(data.frame(compte = as.vector(compte)), "{out.as_posix()}", '
        "row.names = FALSE)\n",
        encoding="utf-8",
    )
    done = subprocess.run([_rscript(), str(job)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")  # fmt: skip
    if "there is no package called" in done.stderr:
        pytest.skip("haven is not installed in R")
    assert done.returncode == 0, done.stderr[-2000:]
    import pandas as pd

    counts = list(pd.read_csv(out)["compte"])
    assert counts[0] == n and {"E1": counts[1], "E2": counts[2]} == flow


def test_the_method_counts_the_checks_of_a_rule_without_a_questionnaire(tmp_path):
    """On SurveyMonkey's export, no questionnaire marks them: the rule's are counted."""
    from ddict.analysis import method, method_text
    from ddict.analysis import notebook as nb
    from ddict.analysis.apa import plain
    from ddict.project import build_project

    base = tmp_path / "reponses-filtres-surveymonkey.sav"
    shutil.copy(EXAMPLES / base.name, base)
    found = build_project(read_database(base))
    names = KEY["surveymonkey"]
    checks = [(names["climat_SQ007"], ["4"]), (names["controle"], ["1"])]
    data = exclusions.attention_data(found, checks, 1, "ignored")
    exclusions.add(found, {**data, "reason": "Items de contrôle échoués"})
    prepared = apply_decisions(found, read_database(base).table)
    facts = method.facts(found, prepared, nb.new_notebook(found, tmp_path / "t.dd.json"))
    assert facts.attention == 2
    text = plain(method_text.participants(found, facts, 1))
    assert "Le questionnaire comprenait deux items de contrôle de l'attention." in text


def test_the_plan_says_whom_a_filtered_variable_was_asked(project):
    """v0.21, step 9 (§ 5.8.5): an hypothesis on a filtered variable is told, never refused."""
    from types import SimpleNamespace

    from ddict.analysis import notebook as nb
    from ddict.review.ui.plan_view import _filtered

    hypothesis = SimpleNamespace(
        roles={"variables": [nb.reference(project, "nbenfants"), nb.reference(project, "consent")]}
    )
    assert _filtered(project, hypothesis) == [
        "nbenfants : posée seulement si consent = Oui et enfants = Oui ; l'analyse portera sur "
        "les personnes à qui elle a été posée."
    ]
