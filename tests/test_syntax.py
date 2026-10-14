"""v0.4, step 3: command files for SPSS, R and Stata (D-025, D-027)."""

import os
import shutil
import subprocess
from pathlib import Path

import pyreadstat
import pytest
from streamlit.testing.v1 import AppTest

from ddict.cli import main
from ddict.export.syntax import decisions, render_syntax, write_syntax
from ddict.io import read_database
from ddict.project import build_project, load_project, save_project
from ddict.project.model import Group, TheoreticalRange, TrackedValue
from ddict.review import logic
from ddict.workflow import profile_database

TODAY = "2026-10-14"
ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "src" / "ddict" / "review" / "app.py")


def _rscript() -> str | None:
    found = shutil.which("Rscript")
    if found:
        return found
    candidates = sorted(
        Path(os.environ.get("PROGRAMFILES", "C:/Program Files")).glob("R/R-*/bin/Rscript.exe")
    )
    return str(candidates[-1]) if candidates else None


def _pspp() -> str | None:
    found = shutil.which("pspp")
    if found:
        return found
    candidates = sorted(
        Path(os.environ.get("PROGRAMFILES", "C:/Program Files")).glob("PSPP/bin/pspp.exe")
    )
    return str(candidates[-1]) if candidates else None


@pytest.fixture
def project(fictional_files):
    return build_project(read_database(fictional_files["etude-sommeil.sav"]))


def test_only_accepted_decisions(project):
    age = decisions(project.variable("age"))
    assert (age.label, age.labels, age.missing) == ("Age", [], [])
    logic.decide_sentinel(project, "age", 999, True, now=TODAY)
    logic.decide_sentinel(project, "nb_reveils", -9, False, now=TODAY)
    assert decisions(project.variable("age")).missing == [999]  # confirmed by the team
    assert decisions(project.variable("nb_reveils")).missing == []
    assert decisions(project.variable("genre")).missing == [9]  # declared in the file
    entry = project.variable("sommeil_q7")  # no label in the file
    entry.label = TrackedValue[str](value="Proposé", origin="ai", status="proposed", ai_run="r1")
    assert decisions(entry).label == ""  # a proposal is not applied
    for program in ("spss", "r", "stata"):
        assert "Proposé" not in render_syntax(project, program, TODAY)


def test_spss(project):
    logic.decide_sentinel(project, "age", 999, True, now=TODAY)
    text = render_syntax(project, "spss", TODAY)
    assert text.startswith("* Encoding: UTF-8.\n")
    assert (
        "VALUE LABELS genre 1 'Femme' 2 'Homme' 3 'Autre identité' 9 'Préfère ne pas répondre'."
        in text
    )
    assert "MISSING VALUES genre (9).\n" in text
    assert "MISSING VALUES age (999).\n" in text
    assert "VARIABLE LEVEL sommeil_q1 (ORDINAL).\n" in text


def test_escaping(project):
    entry = project.variable("age")
    entry.label = TrackedValue[str](value="L'heure \"$x\" `y'", origin="human")
    spss = render_syntax(project, "spss", TODAY)
    assert "VARIABLE LABELS age 'L''heure \"$x\" `y'''." in spss
    r = render_syntax(project, "r", TODAY)
    assert 'attr(donnees[["age"]], "label") <- "L\'heure \\"$x\\" `y\'"' in r
    stata = render_syntax(project, "stata", TODAY)
    assert 'label variable age `"L\'heure "\\$x" \\`y\'"\'' in stata


def test_stata(project):
    text = render_syntax(project, "stata", TODAY)
    assert 'label define genre 1 `"Femme"\' 2 `"Homme"\'' in text
    assert "label values genre genre\n" in text
    # No user-defined missing codes in Stata: the replacement is only suggested.
    assert "\n* mvdecode genre, mv(9)\n" in text
    assert "\nmvdecode" not in text


def test_reversed_items_are_only_suggested(project):
    project.groups.append(
        Group(
            group_id="G1",
            members=TrackedValue[list[str]](value=["anx1", "anx2"], origin="human"),
            descriptive_label=TrackedValue[str](origin="human"),
            ai_hypothesis=TrackedValue[str](origin="human"),
            reverse_items=["anx2"],
        )
    )
    project.variable("anx2").theoretical_range = TheoreticalRange(min=0, max=3, source="Manuel")
    assert '# donnees[["anx2_inv"]] <- 3 - donnees[["anx2"]]' in render_syntax(project, "r", TODAY)
    assert "* COMPUTE anx2_inv = 3 - anx2." in render_syntax(project, "spss", TODAY)
    assert "* generate anx2_inv = 3 - anx2" in render_syntax(project, "stata", TODAY)


def test_names_a_program_refuses(project):
    project.variables[0].name = "1 identifiant"
    assert "* 1 identifiant : nom de variable non valide pour SPSS, omise." in render_syntax(
        project, "spss", TODAY
    )
    assert "* 1 identifiant : nom de variable non valide pour Stata, omise." in render_syntax(
        project, "stata", TODAY
    )


def test_no_participant_value(project):
    for program in ("spss", "r", "stata"):
        text = render_syntax(project, program, TODAY)
        assert "ZQX" not in text  # the canaries of the fictional data


def _same_metadata(expected: Path, produced: Path) -> None:
    _, a = pyreadstat.read_sav(str(expected), user_missing=True, metadataonly=True)
    _, b = pyreadstat.read_sav(str(produced), user_missing=True, metadataonly=True)
    assert b.column_names_to_labels == a.column_names_to_labels
    assert b.variable_value_labels == a.variable_value_labels
    assert b.missing_ranges == a.missing_ranges


@pytest.mark.skipif(_rscript() is None, reason="R is not installed")
def test_r_script_on_the_csv_gives_back_the_sav_metadata(project, fictional_files, tmp_path):
    write_syntax(project, {"r": tmp_path / "m.R"}, TODAY)
    runner = tmp_path / "run.R"
    runner.write_text(
        "args <- commandArgs(trailingOnly = TRUE)\n"
        'donnees <- read.csv(args[1], fileEncoding = "UTF-8", check.names = FALSE)\n'
        'source(args[2], encoding = "UTF-8")\n'
        "haven::write_sav(donnees, args[3])\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.sav"
    done = subprocess.run(
        [
            _rscript(),
            str(runner),
            str(fictional_files["etude-sommeil.csv"]),
            str(tmp_path / "m.R"),
            str(out),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if "there is no package called" in done.stderr:
        pytest.skip("haven is not installed in R")
    assert done.returncode == 0, done.stderr
    _same_metadata(fictional_files["etude-sommeil.sav"], out)


@pytest.mark.skipif(_pspp() is None, reason="PSPP is not installed (D-027)")
def test_spss_syntax_runs_in_pspp(project, fictional_files, tmp_path):
    data, _meta = pyreadstat.read_sav(str(fictional_files["etude-sommeil.sav"]), user_missing=True)
    bare = tmp_path / "bare.sav"
    pyreadstat.write_sav(data, str(bare))  # the same data, without the metadata
    write_syntax(project, {"spss": tmp_path / "m.sps"}, TODAY)
    out = tmp_path / "out.sav"
    job = tmp_path / "job.sps"
    job.write_text(
        f"GET FILE='{bare}'.\nINSERT FILE='{tmp_path / 'm.sps'}' ENCODING='UTF-8'.\n"
        f"SAVE OUTFILE='{out}'.\n",
        encoding="utf-8",
    )
    done = subprocess.run([_pspp(), str(job)], capture_output=True, text=True, errors="replace")
    assert done.returncode == 0 and "error" not in done.stdout.lower(), done.stdout + done.stderr
    _same_metadata(fictional_files["etude-sommeil.sav"], out)


@pytest.fixture
def project_path(fictional_files, tmp_path):
    folder = tmp_path / "projet"
    folder.mkdir()
    shutil.copy(fictional_files["etude-sommeil.sav"], folder / "etude-sommeil.sav")
    project, path = profile_database(folder / "etude-sommeil.sav")
    logic.decide_sentinel(project, "age", 999, True, now=TODAY)
    save_project(project, path)
    return path


def test_command(project_path, capsys):
    assert main(["exporter", str(project_path), "--syntaxe"]) == 0
    names = [
        "etude-sommeil-metadonnees.sps",
        "etude-sommeil-metadonnees.R",
        "etude-sommeil-metadonnees.do",
    ]
    out = capsys.readouterr().out
    for name in names:
        assert name in out
        assert project_path.with_name(name).exists()
    sps = project_path.with_name(names[0]).read_bytes()
    assert b"MISSING VALUES age (999).\n" in sps and b"\r\n" not in sps
    assert main(["exporter", str(project_path)]) == 0  # without --syntaxe: codebook only


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_export_page(project_path):
    app = AppTest.from_file(APP, default_timeout=30)
    app.session_state["project_path"] = str(project_path)
    app.session_state["mode"] = "export"
    app.run()
    assert not app.exception, app.exception
    app.button(key="export-syntax-write").click().run()
    assert "etude-sommeil-metadonnees.sps" in app.success[0].value
    written = project_path.with_name("etude-sommeil-metadonnees.R").read_text(encoding="utf-8")
    assert written == render_syntax(load_project(project_path), "r")
