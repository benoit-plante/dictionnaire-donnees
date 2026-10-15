"""v0.8, step 7: the preparation scripts, reversed items and scores (D-062, D-068)."""

import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import pytest

from context_examples import PROJECTS, SOURCE
from ddict.cli import main
from ddict.export import wording as w
from ddict.export.preparation import plan, render_preparation
from ddict.export.syntax import write_syntax
from ddict.io import read_database
from ddict.project import build_project, save_project
from ddict.review import study
from test_syntax import _pspp, _rscript

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
TODAY = "2026-10-15"
ITEMS = [f"sommeil_q{i}" for i in range(1, 9)]


@pytest.fixture
def project():
    return PROJECTS["etude-sommeil"]()


def _expected(table: pd.DataFrame, rule: str = "prorate") -> pd.Series:
    """The score computed here, independently: q3 and q6 reversed (6 - x), the confirmed
    missing code 9 of q3 left out, at least 7 of the 8 items answered."""
    items = table[ITEMS].apply(pd.to_numeric, errors="coerce")
    items = items.where(items != 9)  # 9: missing (confirmed by the team)
    for name in ("sommeil_q3", "sommeil_q6"):
        items[name] = 6 - items[name]
    answered = items.notna().sum(axis=1)
    value = items.mean(axis=1) * 8 if rule == "prorate" else items.sum(axis=1)
    return value.where(answered >= 7)


def test_what_the_scripts_do(project):
    reversals, scores, notes = plan(project)
    assert [(r.name, r.new, r.total) for r in reversals] == [
        ("sommeil_q3", "sommeil_q3_inv", 6),
        ("sommeil_q6", "sommeil_q6_inv", 6),
    ]
    (score,) = scores
    assert score.name == "sommeil_total" and score.least == 7 and score.prorate
    assert score.items[2] == "sommeil_q3_inv"
    assert notes == []
    sps = render_preparation(project, "spss", TODAY)
    assert "COMPUTE sommeil_q3_inv = 6 - sommeil_q3." in sps
    assert "COMPUTE sommeil_total = MEAN.7(sommeil_q1, sommeil_q2, sommeil_q3_inv," in sps
    assert sps.rstrip().endswith("EXECUTE.")
    text = w.scoring_text(project, project.groups[0])
    assert (
        "items manquants : somme proportionnelle (moyenne des items répondus multipliée par 8)"
        in text
    )


def test_the_rule_for_missing_items(project):
    study.set_scoring(project, "G1", ITEMS, "sum", 1.0, 5.0, 7, "sommeil_total", SOURCE, "",
                      "sum_answered")  # fmt: skip
    sps = render_preparation(project, "spss", TODAY)
    assert "COMPUTE sommeil_total = SUM.7(" in sps and "* 8." not in sps
    assert "rowSums(ddict_items, na.rm = TRUE)" in render_preparation(project, "r", TODAY)
    # Every item required: the rule does not apply, and is not said.
    study.set_scoring(project, "G1", ITEMS, "sum", 1.0, 5.0, None, "sommeil_total", SOURCE, "")
    assert "SUM.8(" in render_preparation(project, "spss", TODAY)
    assert "items manquants" not in w.scoring_text(project, project.groups[0])


def test_what_cannot_be_done_is_said(project):
    study.set_scoring(project, "G1", [], "sum", None, None, None, "", SOURCE, "Score T du manuel.")
    project.groups[1].reverse_items = ["anx2"]  # ends from the labels: 0 and 3
    reversals, scores, notes = plan(project)
    assert ("anx2", "anx2_inv", 3) in [(r.name, r.new, r.total) for r in reversals]
    assert not scores
    assert notes == ["G1 : cotation décrite en note seulement, score non calculé."]


def _run_r(script: str, tmp_path: Path) -> subprocess.CompletedProcess:
    runner = tmp_path / "run.R"
    runner.write_text(script, encoding="utf-8")
    done = subprocess.run([_rscript(), str(runner)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")  # fmt: skip
    if "there is no package called" in done.stderr:
        pytest.skip("haven is not installed in R")
    return done


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
def test_r_gives_the_expected_scores(project, tmp_path):
    write_syntax(project, {"r": tmp_path / "m.R"}, TODAY)
    (tmp_path / "p.R").write_text(render_preparation(project, "r", TODAY), encoding="utf-8")
    csv = EXAMPLES / "etude-sommeil.csv"
    out = tmp_path / "out.csv"
    done = _run_r(
        f'donnees <- read.csv("{csv.as_posix()}", fileEncoding = "UTF-8", check.names = FALSE)\n'
        f'source("{(tmp_path / "m.R").as_posix()}", encoding = "UTF-8")\n'
        f'source("{(tmp_path / "p.R").as_posix()}", encoding = "UTF-8")\n'
        'write.csv(data.frame(total = as.numeric(donnees[["sommeil_total"]]), '
        'q3 = as.numeric(donnees[["sommeil_q3_inv"]])), '
        f'"{out.as_posix()}", row.names = FALSE)\n',
        tmp_path,
    )
    assert done.returncode == 0, done.stderr
    result = pd.read_csv(out)
    table = pd.read_csv(csv)
    expected = _expected(table)
    assert np.allclose(result["total"], expected, equal_nan=True)
    assert result["total"].notna().sum() == expected.notna().sum() > 150
    q3 = pd.to_numeric(table["sommeil_q3"], errors="coerce")
    assert np.allclose(result["q3"], (6 - q3).where(q3 != 9), equal_nan=True)
    # The original variables are not changed.
    assert "sommeil_q3" in table and table["sommeil_q3"].max() == 9


@pytest.mark.skipif(_pspp() is None, reason="PSPP is not installed (D-027)")
def test_pspp_gives_the_expected_scores(project, tmp_path):
    sav = EXAMPLES / "etude-sommeil.sav"
    data, _meta = pyreadstat.read_sav(str(sav), user_missing=True)
    bare = tmp_path / "bare.sav"
    pyreadstat.write_sav(data, str(bare))  # the same data, without the metadata
    write_syntax(project, {"spss": tmp_path / "m.sps"}, TODAY)
    (tmp_path / "p.sps").write_text(render_preparation(project, "spss", TODAY), encoding="utf-8")
    out = tmp_path / "out.sav"
    job = tmp_path / "job.sps"
    job.write_text(
        f"GET FILE='{bare}'.\nINSERT FILE='{tmp_path / 'm.sps'}' ENCODING='UTF-8'.\n"
        f"INSERT FILE='{tmp_path / 'p.sps'}' ENCODING='UTF-8'.\nSAVE OUTFILE='{out}'.\n",
        encoding="utf-8",
    )
    done = subprocess.run([_pspp(), str(job)], capture_output=True, text=True, errors="replace")
    said = (done.stdout + done.stderr).lower()
    assert done.returncode == 0 and "error" not in said and "warning" not in said, said
    result, meta = pyreadstat.read_sav(str(out))
    assert np.allclose(result["sommeil_total"], _expected(data), equal_nan=True)
    assert meta.column_names_to_labels["sommeil_q3_inv"] == "sommeil_q3 inversé"
    assert "ddict_ecart" not in result.columns


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
def test_a_score_already_in_the_database_is_compared(tmp_path):
    """enquete-familles has stress_total, the exact sum of its six items (v0.6, D-039)."""
    project = build_project(read_database(EXAMPLES / "enquete-familles.csv"))
    items = [f"stress_{i}" for i in range(1, 7)]
    study.set_scoring(project, "G1", items, "sum", 0.0, 4.0, None, "stress_score", SOURCE, "")
    (score,) = plan(project)[1]
    assert score.existing == "stress_total"
    csv = (EXAMPLES / "enquete-familles.csv").as_posix()

    def run(name: str) -> subprocess.CompletedProcess:
        (tmp_path / name).write_text(render_preparation(project, "r", TODAY), encoding="utf-8")
        return _run_r(
            f'donnees <- read.csv("{csv}", fileEncoding = "UTF-8", check.names = FALSE)\n'
            f'source("{(tmp_path / name).as_posix()}", encoding = "UTF-8")\n',
            tmp_path,
        )

    done = run("same.R")
    assert done.returncode == 0 and "écarts" not in done.stderr, done.stderr
    project.groups[0].reverse_items = ["stress_2"]  # now the score differs from the base's
    done = run("reversed.R")
    assert done.returncode == 0, done.stderr
    assert "écarts entre stress_score et stress_total" in done.stderr


def test_written_with_the_command_files(project, tmp_path, capsys):
    path = tmp_path / "etude-sommeil.dd.json"
    save_project(project, path)
    assert main(["exporter", str(path), "--syntaxe"]) == 0
    out = capsys.readouterr().out
    assert "etude-sommeil-preparation.sps" in out and "etude-sommeil-preparation.R" in out
    # Nothing to prepare: no preparation file.
    bare = tmp_path / "nu.dd.json"
    save_project(build_project(read_database(EXAMPLES / "etude-sommeil.sav")), bare)
    assert main(["exporter", str(bare), "--syntaxe"]) == 0
    assert "preparation" not in capsys.readouterr().out


@pytest.mark.skipif(_pspp() is None, reason="PSPP is not installed (D-027)")
def test_pspp_runs_the_comparison(tmp_path):
    project = build_project(read_database(EXAMPLES / "enquete-familles.csv"))
    items = [f"stress_{i}" for i in range(1, 7)]
    study.set_scoring(project, "G1", items, "sum", 0.0, 4.0, None, "stress_score", SOURCE, "")
    project.groups[0].reverse_items = ["stress_2"]
    table = pd.read_csv(EXAMPLES / "enquete-familles.csv")
    data = tmp_path / "data.sav"
    pyreadstat.write_sav(table[[*items, "stress_total"]], str(data))
    (tmp_path / "p.sps").write_text(render_preparation(project, "spss", TODAY), encoding="utf-8")
    out = tmp_path / "out.sav"
    job = tmp_path / "job.sps"
    job.write_text(
        f"GET FILE='{data}'.\nINSERT FILE='{tmp_path / 'p.sps'}' ENCODING='UTF-8'.\n"
        f"SAVE OUTFILE='{out}'.\n",
        encoding="utf-8",
    )
    done = subprocess.run([_pspp(), str(job)], capture_output=True, text=True, errors="replace")
    said = (done.stdout + done.stderr).lower()
    assert done.returncode == 0 and "error" not in said, said
    assert "ddict_ecart" in said  # the table of differences was shown
    result, _meta = pyreadstat.read_sav(str(out))
    assert "ddict_ecart" not in result.columns and "stress_2_inv" in result.columns
