"""v0.12, step 6: Cronbach's alpha on the sample analysed and its Feldt interval (D-096),
equal to the answer key of the fictional database of administration and to R."""

import subprocess

import pandas as pd
import pytest

from ddict.analysis.data import apply_decisions
from ddict.analysis.reliability import feldt, reliabilities
from ddict.export.preparation import render_preparation
from ddict.export.syntax import write_syntax
from test_exclusions import KEY, SAV, TODAY, _project
from test_syntax import _rscript

ANXIETY = KEY["exact"]["anxiety"]


@pytest.fixture(scope="module")
def ready():
    return _project()


def test_the_answer_key(ready):
    project, table = ready
    [found] = reliabilities(project, apply_decisions(project, table))
    assert (found.group, found.score, found.items) == ("G1", "anx_total", 6)
    assert found.n == ANXIETY["n"] == 343
    assert found.alpha == pytest.approx(ANXIETY["alpha"], abs=1e-9)
    assert [found.low, found.high] == pytest.approx(ANXIETY["ci95"], abs=1e-9)


def test_on_the_sample_analysed_not_the_file():
    project, table = _project(rules=False)
    [everyone] = reliabilities(project, apply_decisions(project, table))
    assert everyone.n > ANXIETY["n"]  # the rules change who enters the alpha
    assert everyone.alpha != pytest.approx(ANXIETY["alpha"], abs=1e-6)


def test_the_reversed_item_counts():
    project, table = _project()
    project.groups[0].reverse_items = []  # anx3 no longer reversed: a much lower alpha
    [found] = reliabilities(project, apply_decisions(project, table))
    assert found.alpha < ANXIETY["alpha"] - 0.1


def test_too_few_answers(ready):
    project, table = ready
    prepared = apply_decisions(project, table)
    small = prepared.__class__(prepared.table.head(1), prepared.scores, prepared.reversed)
    [found] = reliabilities(project, small)
    assert found.alpha is None and found.n == 1


def test_feldt_widens_with_fewer_people():
    narrow = feldt(0.8, 500, 6)
    wide = feldt(0.8, 50, 6)
    assert wide[0] < narrow[0] < 0.8 < narrow[1] < wide[1]


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
def test_the_same_in_r(ready, tmp_path):
    """The data prepared by the scripts (exclusions included), the formulas written in R."""
    project, _table = ready
    write_syntax(project, {"r": tmp_path / "m.R"}, TODAY)
    (tmp_path / "p.R").write_text(render_preparation(project, "r", TODAY), encoding="utf-8")
    items = ", ".join(
        f'as.numeric(donnees[["{n}"]])'
        for n in ["anx1", "anx2", "anx3_inv", "anx4", "anx5", "anx6"]
    )
    out = tmp_path / "out.csv"
    job = tmp_path / "job.R"
    job.write_text(
        f'donnees <- haven::read_sav("{SAV.as_posix()}", user_na = TRUE)\n'
        f'source("{(tmp_path / "m.R").as_posix()}", encoding = "UTF-8")\n'
        f'source("{(tmp_path / "p.R").as_posix()}", encoding = "UTF-8")\n'
        f"x <- cbind({items})\n"
        "x <- x[complete.cases(x), ]\n"
        "n <- nrow(x); k <- ncol(x)\n"
        "a <- k / (k - 1) * (1 - sum(apply(x, 2, var)) / var(rowSums(x)))\n"
        "low <- 1 - (1 - a) * qf(0.975, n - 1, (n - 1) * (k - 1))\n"
        "high <- 1 - (1 - a) * qf(0.025, n - 1, (n - 1) * (k - 1))\n"
        f'write.csv(data.frame(n = n, a = a, low = low, high = high), "{out.as_posix()}", '
        "row.names = FALSE)\n",
        encoding="utf-8",
    )
    done = subprocess.run([_rscript(), str(job)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")  # fmt: skip
    if "there is no package called" in done.stderr:
        pytest.skip("haven is not installed in R")
    assert done.returncode == 0, done.stderr[-2000:]
    r = pd.read_csv(out).iloc[0]
    project_table = apply_decisions(*ready)
    [found] = reliabilities(project, project_table)
    assert r["n"] == found.n
    assert found.alpha == pytest.approx(r["a"], rel=1e-6)
    assert found.low == pytest.approx(r["low"], rel=1e-6)
    assert found.high == pytest.approx(r["high"], rel=1e-6)
