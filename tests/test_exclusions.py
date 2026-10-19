"""v0.12, step 3: the exclusion rules (D-093, D-094), kept in the project, applied in memory
before the analyses and in the preparation scripts, with the same counts in the tool, PSPP
and R as the answer key of the fictional database of administration."""

import json
import subprocess
from pathlib import Path

import pandas as pd
import pyreadstat
import pytest

from ddict.analysis.data import apply_decisions
from ddict.export.preparation import render_preparation
from ddict.export.syntax import write_syntax
from ddict.io import read_database
from ddict.project import build_project, fingerprint, load_project, save_project
from ddict.project import exclusions as ex
from ddict.review import study
from ddict.workflow import documented_copy
from test_syntax import _pspp, _rscript

EXAMPLES = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"
KEY = json.loads((EXAMPLES / "corrige-passation.json").read_text(encoding="utf-8"))
SAV = EXAMPLES / KEY["sav"]
TODAY = "2026-10-16"
EXPECTED = KEY["exact"]["flow"]["excluded"]
OTHER_ORDER = KEY["exact"]["flow_e5_before_e4"]["excluded"]


def _project(rules=True):
    database = read_database(SAV)
    project = build_project(database)
    scoring = KEY["scoring"]
    study.set_scoring(project, "G1", scoring["group_items"], "sum", 1.0, 4.0,
                      scoring["min_items_answered"], scoring["score_name"], scoring["source"],
                      "")  # fmt: skip
    project.groups[0].reverse_items = scoring["reverse_items"]
    if rules:
        for rule in KEY["rules"]:
            ex.add(project, {k: v for k, v in rule.items() if k != "id"})
    return project, database.table


@pytest.fixture(scope="module")
def ready():
    return _project()


# --- In the tool. ---


def test_the_counts_of_the_answer_key(ready):
    project, table = ready
    prepared = apply_decisions(project, table)
    assert dict(prepared.flow.excluded) == EXPECTED
    assert (prepared.flow.start, prepared.flow.analysed) == (400, 347)
    assert len(prepared.table) == 347


def test_the_order_changes_the_counts_never_the_n():
    project, table = _project()
    ex.move(project, "E5", 4)
    flow = apply_decisions(project, table).flow
    assert [r for r, _n in flow.excluded] == ["E1", "E2", "E3", "E5", "E4", "E6"]
    assert dict(flow.excluded) == OTHER_ORDER and flow.analysed == 347


def test_without_rules_nothing_changes():
    project, table = _project(rules=False)
    prepared = apply_decisions(project, table)
    assert prepared.flow is None and len(prepared.table) == 400


def test_a_condition_on_a_score():
    project, table = _project(rules=False)
    ex.add(project, {"kind": "condition", "score": "G1", "operator": "missing",
                     "reason": "Score d'anxiété manquant"})  # fmt: skip
    flow = apply_decisions(project, table).flow
    # The refusals (questionnaire empty) and the incomplete scales have no score.
    assert flow.excluded == (("E1", 12 + 14),)


# --- What is refused (D-093). ---


def _refused(project, data, words):
    with pytest.raises(ex.ExclusionRefused) as error:
        ex.add(project, data)
    assert words in " ".join(error.value.reasons), error.value.reasons


def test_what_is_refused():
    project, _table = _project(rules=False)
    _refused(project, {"kind": "condition", "variable": "id_participant", "operator": "eq",
                       "value": "ZQXID-0001", "reason": "x"}, "nommerait une personne")  # fmt: skip
    _refused(project, {"kind": "condition", "variable": "courriel", "operator": "eq",
                       "value": "a@b.c", "reason": "x"}, "nommerait une personne")  # fmt: skip
    _refused(project, {"kind": "condition", "variable": "inconnue", "operator": "eq",
                       "value": 1, "reason": "x"}, "variable inconnue")  # fmt: skip
    _refused(project, {"kind": "completeness", "group": "G1", "min_answered": 7,
                       "reason": "x"}, "le groupe en compte 6")  # fmt: skip
    _refused(project, {"kind": "duration", "start": "age", "end": "fin", "min_seconds": 60,
                       "reason": "x", "source": "s"}, "pas une date")  # fmt: skip
    _refused(project, {"kind": "duration", "start": "debut", "end": "fin", "min_seconds": 60,
                       "reason": "x"}, "donnez sa source")  # fmt: skip
    _refused(project, {"kind": "condition", "score": "G2", "operator": "missing",
                       "reason": "x"}, "aucune cotation structurée")  # fmt: skip
    assert project.exclusions.rules == [] and project.exclusions.next_id == 1
    # The duplicate rule may compare identifiers: it names no value.
    ex.add(project, {"kind": "duplicate", "variables": ["courriel"], "reason": "Doublon"})


def test_identifiers_are_never_given_again():
    project, _table = _project()
    ex.remove(project, "E6")
    rule = ex.add(project, {"kind": "duplicate", "variables": ["courriel"], "reason": "Doublon"})
    assert rule.id == "E7"


# --- The project file and the fingerprint (format 0.4.0). ---


def test_the_project_file_and_its_fingerprint(tmp_path):
    project, _table = _project(rules=False)
    before = fingerprint.fingerprint(project)
    path = tmp_path / "etude-passation.dd.json"
    save_project(project, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "0.9.0" and data["exclusions"] == {"next_id": 1, "rules": []}
    del data["exclusions"]
    data["schema_version"] = "0.3.0"  # a project of v0.8 to v0.11
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    old = load_project(path)
    assert old.schema_version == "0.9.0" and old.exclusions.rules == []
    assert fingerprint.fingerprint(old) == before  # no rule: the same fingerprint
    ex.add(old, KEY["rules"][0] | {"id": None})
    assert fingerprint.fingerprint(old) != before
    save_project(old, path)
    again = load_project(path)
    assert again.exclusions == old.exclusions
    ex.remove(again, "E1")
    assert fingerprint.fingerprint(again) == before


def test_the_documented_copy_keeps_everyone(ready, tmp_path):
    project, _table = ready
    path = tmp_path / "etude-passation.dd.json"
    (tmp_path / SAV.name).write_bytes(SAV.read_bytes())
    save_project(project, path)
    result = documented_copy(project, path)
    assert result.n_rows == 400


# --- In SPSS (PSPP) and R. ---


def _counts(column: pd.Series) -> dict[str, int]:
    found = column.value_counts()
    return {f"E{n}": int(found.get(n, 0)) for n in range(1, 7)}


@pytest.mark.skipif(_pspp() is None, reason="PSPP is not installed (D-027)")
def test_pspp_gives_the_same_counts(ready, tmp_path):
    project, _table = ready
    data, _meta = pyreadstat.read_sav(str(SAV), user_missing=True)
    bare = tmp_path / "bare.sav"
    pyreadstat.write_sav(data, str(bare))  # the same data, without the metadata
    write_syntax(project, {"spss": tmp_path / "m.sps"}, TODAY)
    script = render_preparation(project, "spss", TODAY)
    (tmp_path / "p.sps").write_text(script, encoding="utf-8")
    # The same script without its selection, to read who each rule excluded.
    (tmp_path / "all.sps").write_text(
        script.replace("SELECT IF (ddict_exclusion = 0).\n", ""), encoding="utf-8"
    )
    for name, out in (("p.sps", "kept.sav"), ("all.sps", "all.sav")):
        job = tmp_path / f"job-{name}"
        job.write_text(
            f"GET FILE='{bare}'.\nINSERT FILE='{tmp_path / 'm.sps'}' ENCODING='UTF-8'.\n"
            f"INSERT FILE='{tmp_path / name}' ENCODING='UTF-8'.\n"
            f"SAVE OUTFILE='{tmp_path / out}'.\n",
            encoding="utf-8",
        )
        done = subprocess.run([_pspp(), str(job)], capture_output=True, text=True,
                              errors="replace")  # fmt: skip
        said = (done.stdout + done.stderr).lower()
        assert done.returncode == 0 and "error" not in said and "warning" not in said, said
    everyone, _meta = pyreadstat.read_sav(str(tmp_path / "all.sav"))
    assert _counts(everyone["ddict_exclusion"]) == EXPECTED
    assert list(everyone["id_participant"]) == list(data["id_participant"])  # order kept
    kept, _meta = pyreadstat.read_sav(str(tmp_path / "kept.sav"))
    assert len(kept) == 347 and set(kept["ddict_exclusion"]) == {0}
    assert not {"ddict_ordre", "ddict_double6"} & set(kept.columns)


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
def test_r_gives_the_same_counts(ready, tmp_path):
    project, _table = ready
    write_syntax(project, {"r": tmp_path / "m.R"}, TODAY)
    (tmp_path / "p.R").write_text(render_preparation(project, "r", TODAY), encoding="utf-8")
    out = tmp_path / "out.csv"
    job = tmp_path / "job.R"
    job.write_text(
        f'donnees <- haven::read_sav("{SAV.as_posix()}", user_na = TRUE)\n'
        f'source("{(tmp_path / "m.R").as_posix()}", encoding = "UTF-8")\n'
        'print <- function(x, ...) { assign("compte", x, envir = globalenv()); '
        "base::print(x, ...) }\n"
        f'source("{(tmp_path / "p.R").as_posix()}", encoding = "UTF-8")\n'
        "rm(print)\n"
        f'write.csv(data.frame(compte = as.vector(compte), n = nrow(donnees)), "{out.as_posix()}", '
        "row.names = FALSE)\n",
        encoding="utf-8",
    )
    done = subprocess.run([_rscript(), str(job)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")  # fmt: skip
    if "there is no package called" in done.stderr:
        pytest.skip("haven is not installed in R")
    assert done.returncode == 0, done.stderr[-2000:]
    result = pd.read_csv(out)
    counts = list(result["compte"])
    assert counts[0] == 347 and dict(zip(EXPECTED, counts[1:], strict=True)) == EXPECTED
    assert set(result["n"]) == {347}


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
def test_the_master_script_analyses_the_people_kept(ready, tmp_path):
    """The R master script of the notebook runs the preparation script, exclusions
    included: R gives the tool's values, computed on the 347 people kept."""
    import io
    import shutil
    import zipfile

    from ddict.analysis import notebook as nb
    from ddict.analysis import notebook_export as export
    from ddict.analysis.compute import run

    project, table = ready
    prepared = apply_decisions(project, table)
    path = tmp_path / "etude-passation.dd.json"
    notebook = nb.new_notebook(project, path)
    chosen = {"variables": ["stress", "anx_total"]}
    result = run(project, prepared, "correlation", chosen)
    nb.add(notebook, project, result, today=TODAY)
    assert result.statistics["n"] == 347
    analyses = [(e.id, e.analysis, nb.resolved(project, e), dict(e.options))
                for e in notebook.entries]  # fmt: skip
    bundle = export.r_bundle(project, path, analyses, today=TODAY)
    shutil.copy(SAV, tmp_path / SAV.name)
    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
        archive.extractall(tmp_path)
    (tmp_path / "run.R").write_text(
        'source("etude-passation-article.R", encoding = "UTF-8")\n'
        "valeurs <- unlist(resultats)\n"
        'write.csv(data.frame(nom = names(valeurs), valeur = valeurs), "sortie.csv", '
        "row.names = FALSE)\n",
        encoding="utf-8",
    )
    done = subprocess.run([_rscript(), "run.R"], cwd=tmp_path, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")  # fmt: skip
    assert done.returncode == 0, done.stderr[-2000:]
    out = pd.read_csv(tmp_path / "sortie.csv")
    from_r = dict(zip(out["nom"], out["valeur"], strict=True))
    assert from_r["A1.n"] == 347
    assert from_r["A1.r"] == pytest.approx(result.statistics["r"], rel=1e-6)
