"""v0.15, step 6: the reproduction package (D-119; docs/verification-depot.md, § 3): what it
holds and never holds, the same bytes each time, no value of the database (witness strings),
and the R master script that, unpacked beside the database, gives the notebook's figures."""

import io
import re
import shutil
import subprocess
import zipfile

import pandas as pd
import pytest

from ddict.analysis import deposit
from ddict.analysis import notebook as nb
from ddict.analysis.compute import run
from ddict.analysis.data import prepare
from ddict.io import read_database
from ddict.project import build_project, load_project, save_project
from test_recode import EXAMPLES, KEY

TODAY = "2026-10-18"
ANALYSES = [
    ("paired", {"first": ["anxiete_t1"], "second": ["anxiete_t2"]}),
    ("t_test", {"outcome": ["stress"], "group": ["abandon"]}),
    ("correlation", {"variables": ["stress", "sommeil"]}),
]


def _study(folder):
    shutil.copy(EXAMPLES / KEY["sav"], folder / KEY["sav"])
    path = folder / "etude-suivi.dd.json"
    project = build_project(read_database(folder / KEY["sav"]))
    save_project(project, path)
    prepared = prepare(project, path)
    notebook = nb.new_notebook(project, path)
    for key, chosen in ANALYSES:
        nb.add(notebook, project, run(project, prepared, key, chosen), today=TODAY)
    nb.save_notebook(notebook, nb.notebook_path(path))
    return project, prepared, notebook, path


@pytest.fixture
def study(tmp_path):
    return _study(tmp_path)


def _texts(data: bytes, name: str) -> str:
    """The text of a file of the package, the XML of a Word or Excel file included."""
    if name.endswith((".docx", ".xlsx")):
        with zipfile.ZipFile(io.BytesIO(data)) as inner:
            return " ".join(inner.read(n).decode("utf-8", "replace") for n in inner.namelist())
    return data.decode("utf-8")


def test_what_the_package_holds(study):
    project, prepared, notebook, path = study
    files = deposit.package(project, prepared, notebook, path, today=TODAY)
    assert sorted(files) == [
        "EMPREINTES.txt", "README.md", "analyses/etude-suivi-carnet.json",
        "codebook/etude-suivi-datapackage.json", "codebook/etude-suivi.md",
        "codebook/etude-suivi.xlsx", "scripts/etude-suivi-article.R",
        "scripts/etude-suivi-metadonnees.R", "scripts/etude-suivi.sps",
    ]  # fmt: skip
    assert not any(n.endswith((".sav", ".dd.json", "-article.docx")) for n in files)
    readme = files["README.md"].decode("utf-8")
    assert readme.startswith("# [à compléter : titre de l'étude] — matériel de reproduction")
    assert "le carnet des 3 analyses retenues" in readme and "`plan/`" not in readme
    assert "Licence : [à compléter : licence]." in readme
    without_version = re.sub(r"dictionnaire-donnees \d+\.\d+\.\d+", "", readme)
    assert not re.search(r"\d+[,.]\d", without_version)  # no statistic: counts, dates
    sums = files["EMPREINTES.txt"].decode("utf-8")
    assert project.source.sha256 in sums and "analyses/etude-suivi-carnet.json" in sums
    again = deposit.package(project, prepared, notebook, path, today=TODAY)
    assert deposit.zipped(files) == deposit.zipped(again)  # the same bytes each time


def test_with_a_plan(study):
    from ddict.analysis import planning as pl

    project, prepared, notebook, path = study
    data = pl.data_from_names(project, "L'anxiété baisse.", "paired", ANALYSES[0][1], {},
                              direction="first_higher")  # fmt: skip
    pl.add(project, data, prepared, None, TODAY)
    files = deposit.package(project, prepared, notebook, path, today=TODAY)
    assert "plan/etude-suivi-preenregistrement.docx" in files
    assert "plan/etude-suivi-preenregistrement.md" in files
    assert "le préenregistrement du plan d'analyse, non arrêté" in files["README.md"].decode()


def test_no_value_of_the_database(study, tmp_path):
    """Witness strings: the identifiers and a free text of the base appear nowhere."""
    from test_text_categories import _base

    project, prepared, notebook, path = study
    files = deposit.package(project, prepared, notebook, path, today=TODAY)
    table = read_database(path.with_name(KEY["sav"])).table
    witnesses = set(table["id_participant"].astype(str))
    assert len(witnesses) == 240
    for name, data in files.items():
        text = _texts(data, name)
        assert not [w for w in witnesses if w in text], name
    # A free text, in a base whose categories are texts.
    folder = tmp_path / "textes"
    folder.mkdir()
    texts_project, texts_path = _base(folder)
    texts_prepared = prepare(texts_project, texts_path)
    texts_notebook = nb.new_notebook(texts_project, texts_path)
    result = run(texts_project, texts_prepared, "t_test",
                 {"outcome": ["satisfaction"], "group": ["groupe"]})  # fmt: skip
    nb.add(texts_notebook, texts_project, result, today=TODAY)
    for name, data in deposit.package(texts_project, texts_prepared, texts_notebook,
                                      texts_path, today=TODAY).items():  # fmt: skip
        assert "Réponse libre numéro" not in _texts(data, name), name


def test_refused_without_the_database_or_with_a_pending_analysis(study):
    from ddict.analysis.notebook_export import ExportBlocked
    from ddict.project import exclusions as rules

    project, _prepared, notebook, path = study
    with pytest.raises(deposit.DepositError):
        deposit.package(project, None, notebook, path, today=TODAY)
    rules.add(project, {"kind": "condition", "variable": "age", "operator": "lt", "value": 25,
                        "reason": "Moins de 25 ans"})  # fmt: skip
    with pytest.raises(ExportBlocked):
        deposit.package(project, prepare(project, path), notebook, path, today=TODAY)


def test_r_runs_the_unpacked_package(study, tmp_path):
    from test_syntax import _rscript

    if _rscript() is None:
        pytest.skip("R is not installed")
    project, prepared, notebook, path = study
    target, _files = deposit.write_deposit(project, prepared, notebook, path, today=TODAY)
    unpacked = tmp_path / "depot"
    with zipfile.ZipFile(target) as archive:
        archive.extractall(unpacked)
    scripts = unpacked / "scripts"
    shutil.copy(path.with_name(KEY["sav"]), scripts / KEY["sav"])  # as the README says
    (scripts / "run.R").write_text(
        'source("etude-suivi-article.R", encoding = "UTF-8")\n'
        "valeurs <- unlist(resultats)\n"
        'write.csv(data.frame(nom = names(valeurs), valeur = valeurs), "sortie.csv", '
        "row.names = FALSE)\n",
        encoding="utf-8",
    )
    done = subprocess.run([_rscript(), "run.R"], cwd=scripts, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")  # fmt: skip
    if "there is no package called" in done.stderr:
        pytest.skip("haven is not installed in R")
    assert done.returncode == 0, done.stderr[-2000:]
    out = pd.read_csv(scripts / "sortie.csv")
    from_r = dict(zip(out["nom"], out["valeur"], strict=True))
    kept = nb.load_notebook(nb.notebook_path(path))
    for entry, keys in zip(kept.entries, [("t", "df", "n"), ("t", "df", "p"), ("r_2_1",)],
                           strict=True):  # fmt: skip
        for key in keys:
            assert entry.computed.statistics[key] == pytest.approx(
                from_r[f"{entry.id}.{key}"], rel=1e-6
            ), (entry.id, key)


def test_the_command(study, capsys):
    from ddict.cli import main

    _project, _prepared, _notebook, path = study
    assert main(["deposer", str(path), "--langue", "en"]) == 0
    out = capsys.readouterr().out
    assert "etude-suivi-depot.zip" in out and "La base n'y est pas" in out
    readme = zipfile.ZipFile(path.with_name("etude-suivi-depot.zip")).read("README.md")
    assert readme.decode("utf-8").startswith("# [to complete:")


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_page(study):
    from streamlit.testing.v1 import AppTest

    from test_analysis_page import APP

    _project, _prepared, _notebook, path = study
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "notebook"
    app.run()
    assert not app.exception, app.exception
    app.button(key="notebook-deposit").click().run()
    assert not app.exception, app.exception
    assert path.with_name("etude-suivi-depot.zip").is_file()
    assert any("La base n'y est pas" in s.value for s in app.success)
    assert load_project(path).recodes.rules == []
