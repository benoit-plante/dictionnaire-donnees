"""v0.21, step 9 (§ 5.8.4 of the plan, D-167): the codes of the blanks, their refusals, and
the preparation scripts of SPSS and R on a filtered base: who was asked, recomputed from the
conditions on the values as recorded (the code 9, declared missing, is a choice); the same
exclusions as the tool's, the code of the not applicable in the empty cells of a question not
asked, the code of the missing in those of a question asked; in PSPP and in R. Nothing real:
the base of `scripts/generer_base_filtres.py`."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pyreadstat
import pytest

from ddict import arrival
from ddict.analysis import exclusions as computed
from ddict.analysis.data import apply_decisions, decided, not_applicable
from ddict.export.preparation import render_preparation
from ddict.export.syntax import write_syntax
from ddict.io.load import read_database
from ddict.project import blank, exclusions, skip
from test_syntax import _pspp, _rscript

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
BASE = EXAMPLES / "reponses-filtres.sav"
TODAY = "2026-10-21"


def _generator():
    script = ROOT / "scripts" / "generer_base_filtres.py"
    spec = importlib.util.spec_from_file_location("generer_base_filtres", script)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _project(codes=True):
    project = _generator().project()
    arrival.receive(project, BASE)
    group = next(g.group_id for g in project.groups if "climat_SQ001" in (g.members.value or []))
    exclusions.add(project, {"kind": "completeness", "group": group, "min_answered": 5,
                             "reason": "Grille du travail incomplète"})  # fmt: skip
    exclusions.add(project, {"kind": "condition", "variable": "nbenfants", "operator": "missing",
                             "reason": "Nombre d'enfants non donné"})  # fmt: skip
    if codes:
        blank.set_codes(project, -8, -9)
    return project


@pytest.fixture(scope="module")
def ready():
    project = _project()
    table = read_database(BASE).table
    return project, table


def _expected(project, table):
    """What the tool computes: the flow, and among the people kept, for each variable, how
    many cells get the code of the not applicable and of the missing."""
    data, _r, _s = decided(project, table)
    na = not_applicable(project, table)
    rank = computed.ranks(project, data, na)
    kept = (rank == 0).to_numpy()
    natures = skip.natures(table, skip.conditions_of(project), skip.boxes_of(project))
    found = {}
    for name in ("nbenfants", "nuit", "age", "bienetre_SQ001", "climat_SQ001"):
        nature = natures[name][kept]
        found[name] = (
            int((nature == skip.NOT_APPLICABLE).sum()),
            int((nature == skip.MISSING).sum()),
        )
    flow = {f"E{n}": int((rank == n).sum()) for n in (1, 2)}
    return flow, found, int(kept.sum())


# --- The codes and their refusals. ---


def test_the_codes_are_kept_and_refused():
    project = _project(codes=False)
    blank.set_codes(project, -8, -9)
    assert (project.settings.blank_codes.not_applicable, project.settings.blank_codes.missing) == (
        -8,
        -9,
    )
    for codes, reason in [
        ((1, None), "déjà une valeur"),  # a choice, a value observed
        ((9, None), "déjà une valeur"),  # "Préfère ne pas répondre", declared missing
        ((-8, -8), "deux codes"),
        (("x", None), "est un nombre"),
    ]:
        with pytest.raises(blank.BlankError, match=reason):
            blank.set_codes(project, *codes)
    assert project.settings.blank_codes.not_applicable == -8  # unchanged
    blank.set_codes(project, None, None)
    assert project.settings.blank_codes.missing is None


def test_the_scripts_say_the_flags_and_the_codes(ready):
    project, _table = ready
    spss = render_preparation(project, "spss", TODAY)
    assert "VALUE(enfants) = 1" in spss  # the values as recorded
    assert "IF (ddict_posee" in spss and "SYSMIS(nbenfants)) nbenfants = -8." in spss
    assert "ADD VALUE LABELS nbenfants -8 'Non applicable' -9 'Sans réponse'." in spss
    assert "non applicable : -8 ; sans réponse : -9" in spss
    r = render_preparation(project, "r", TODAY)
    assert 'ddict_code(donnees[["nbenfants"]], !donnees[["ddict_posee' in r
    plain = _generator().project()
    arrival.receive(plain, BASE)
    assert "ddict_posee" not in render_preparation(plain, "spss", TODAY)  # nothing to do


def test_the_tool_counts(ready):
    project, table = ready
    flow, _found, n = _expected(project, table)
    prepared = apply_decisions(project, table)
    assert dict(prepared.flow.excluded) == flow and prepared.flow.analysed == n
    assert flow["E1"] == 6 and flow["E2"] == 5 - _overlap(project, table)


def _overlap(project, table):
    """The people both rules would exclude: counted by the first."""
    data, _r, _s = decided(project, table)
    na = not_applicable(project, table)
    first = computed.hits(project, data, project.exclusions.rules[0], na)
    second = computed.hits(project, data, project.exclusions.rules[1], na)
    return int((first & second).sum())


@pytest.mark.skipif(_pspp() is None, reason="PSPP is not installed (D-027)")
def test_pspp_gives_the_same_counts_and_codes(ready, tmp_path):
    project, table = ready
    flow, found, n = _expected(project, table)
    data, _meta = pyreadstat.read_sav(str(BASE), user_missing=True)
    bare = tmp_path / "bare.sav"
    pyreadstat.write_sav(data, str(bare))  # the same data, without the metadata
    write_syntax(project, {"spss": tmp_path / "m.sps"}, TODAY)
    script = render_preparation(project, "spss", TODAY)
    (tmp_path / "p.sps").write_text(script, encoding="utf-8")
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
        assert done.returncode == 0, said
        assert not any(w in said for w in ("error", "warning", "erreur", "avertissement")), said
    everyone, _meta = pyreadstat.read_sav(str(tmp_path / "all.sav"))
    counts = everyone["ddict_exclusion"].value_counts()
    assert {f"E{k}": int(counts.get(k, 0)) for k in (1, 2)} == flow
    kept, meta = pyreadstat.read_sav(str(tmp_path / "kept.sav"), user_missing=True)
    assert len(kept) == n
    for name, (na, missing) in found.items():
        assert (int((kept[name] == -8).sum()), int((kept[name] == -9).sum())) == (na, missing), name
    assert {r["lo"] for r in meta.missing_ranges["nbenfants"]} == {-8.0, -9.0}
    assert {r["lo"] for r in meta.missing_ranges["enfants"]} == {9.0, -8.0, -9.0}  # 9 kept
    assert meta.variable_value_labels["nbenfants"][-8.0] == "Non applicable"
    assert not any(c.startswith("ddict_posee") for c in kept.columns)


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
def test_r_gives_the_same_counts_and_codes(ready, tmp_path):
    project, table = ready
    flow, found, n = _expected(project, table)
    write_syntax(project, {"r": tmp_path / "m.R"}, TODAY)
    (tmp_path / "p.R").write_text(render_preparation(project, "r", TODAY), encoding="utf-8")
    out = tmp_path / "out.csv"
    columns = ", ".join(f'"{name}"' for name in found)
    job = tmp_path / "job.R"
    job.write_text(
        f'donnees <- haven::read_sav("{BASE.as_posix()}", user_na = TRUE)\n'
        f'source("{(tmp_path / "m.R").as_posix()}", encoding = "UTF-8")\n'
        'print <- function(x, ...) { assign("compte", x, envir = globalenv()); '
        "base::print(x, ...) }\n"
        f'source("{(tmp_path / "p.R").as_posix()}", encoding = "UTF-8")\n'
        "rm(print)\n"
        f"noms <- c({columns})\n"
        "na8 <- sapply(noms, function(v) sum(as.numeric(vctrs::vec_data(donnees[[v]])) == -8, "
        "na.rm = TRUE))\n"
        "na9 <- sapply(noms, function(v) sum(as.numeric(vctrs::vec_data(donnees[[v]])) == -9, "
        "na.rm = TRUE))\n"
        "declare <- all(c(-8, -9) %in% attr(donnees[['nbenfants']], 'na_values'))\n"
        f"write.csv(data.frame(nom = noms, na = na8, manquant = na9, n = nrow(donnees), "
        f"e1 = compte[2], e2 = compte[3], declare = declare, "
        f'restes = sum(grepl("^ddict_posee", names(donnees)))), "{out.as_posix()}", '
        "row.names = FALSE)\n",
        encoding="utf-8",
    )
    done = subprocess.run([_rscript(), str(job)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")  # fmt: skip
    if "there is no package called" in done.stderr:
        pytest.skip("haven is not installed in R")
    assert done.returncode == 0, done.stderr[-2000:]
    import pandas as pd

    result = pd.read_csv(out)
    assert set(result["n"]) == {n}
    assert {"E1": int(result["e1"][0]), "E2": int(result["e2"][0])} == flow
    got = {r.nom: (int(r.na), int(r.manquant)) for r in result.itertuples()}
    assert got == found
    assert bool(result["declare"][0]) and int(result["restes"][0]) == 0


def test_the_command_line_and_the_codebook(tmp_path, capsys):
    from ddict.cli import main
    from ddict.export import render_markdown
    from ddict.project import load_project, save_project

    path = tmp_path / "familles.dd.json"
    save_project(_project(codes=False), path)
    assert "Codes des vides" not in render_markdown(load_project(path))
    assert main(["codes", "vides", str(path), "--non-applicable", "-8", "--manquant", "-9"]) == 0
    assert "non applicable : -8 ; sans réponse : -9" in capsys.readouterr().out
    assert (
        "- Codes des vides dans les scripts SPSS et R : non applicable : -8 ; sans réponse : -9"
        in render_markdown(load_project(path))
    )
    assert main(["codes", "vides", str(path), "--non-applicable", "1"]) == 2
    assert "déjà une valeur" in capsys.readouterr().err
    assert main(["codes", "vides", str(path), "--effacer"]) == 0
    assert load_project(path).settings.blank_codes.not_applicable is None


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_page_export(tmp_path):
    import shutil

    from streamlit.testing.v1 import AppTest

    from ddict.project import load_project, save_project

    shutil.copy(BASE, tmp_path / BASE.name)
    path = tmp_path / "familles.dd.json"
    save_project(_project(codes=False), path)
    app = AppTest.from_file(str(ROOT / "src" / "ddict" / "review" / "app.py"), default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "export"
    app.run()
    assert not app.exception, app.exception
    assert any("ne distinguent pas les deux" in x.value for x in app.caption)
    app.text_input(key="export-blank-na").set_value("-8")
    app.text_input(key="export-blank-missing").set_value("-9")
    app.button(key="export-blank-save").click().run()
    assert not app.exception, app.exception
    codes = load_project(path).settings.blank_codes
    assert (codes.not_applicable, codes.missing) == (-8, -9)
    app.text_input(key="export-blank-na").set_value("1")
    app.button(key="export-blank-save").click().run()
    assert any("déjà une valeur" in e.value for e in app.error)
