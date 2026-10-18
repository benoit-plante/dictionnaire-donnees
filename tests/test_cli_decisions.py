"""v0.13, step 7: `ddict niveaux` and `ddict codes`, the measure levels and the suspect
missing codes decided on the command line, with the functions of the pages "Base" and
"Variables": the same project either way. On the fictional sleep study, read as a CSV."""

import shutil

import pytest

from ddict.cli import main
from ddict.project import load_project, measure, save_project
from ddict.review import levels, logic
from test_analysis_data import EXAMPLES

NOW = "2026-10-18T09:00:00"


@pytest.fixture
def path(tmp_path):
    shutil.copy(EXAMPLES / "etude-sommeil.csv", tmp_path / "etude-sommeil.csv")
    assert main(["profiler", str(tmp_path / "etude-sommeil.csv")]) == 0
    return tmp_path / "etude-sommeil.dd.json"


def test_the_levels(path, capsys):
    capsys.readouterr()
    assert main(["niveaux", "lister", str(path)]) == 0
    out = capsys.readouterr().out
    assert "age — échelle (proposé)" in out
    assert main(["niveaux", "accepter", str(path)]) == 2
    assert "ajoutez --tout" in capsys.readouterr().err
    assert main(["niveaux", "accepter", str(path), "age", "vague"]) == 0
    assert "Niveaux de mesure décidés : 2." in capsys.readouterr().out
    assert main(["niveaux", "rejeter", str(path), "sommeil_q1"]) == 0
    assert main(["niveaux", "fixer", str(path), "sommeil_q2", "echelle"]) == 0
    project = load_project(path)
    assert measure.level(project.variable("age")) == "scale"
    assert measure.level(project.variable("sommeil_q2")) == "scale"
    assert project.variable("sommeil_q1").measure_level.status == "rejected"
    # Already decided, or unknown: refused, nothing saved.
    assert main(["niveaux", "rejeter", str(path), "age"]) == 2
    assert "n'attendent plus de décision" in capsys.readouterr().err
    assert main(["niveaux", "fixer", str(path), "inconnue", "nominal"]) == 2
    assert "inconnue : variable inconnue." in capsys.readouterr().err
    assert main(["niveaux", "accepter", str(path), "--tout"]) == 0
    assert levels.waiting(load_project(path)) == 0
    assert main(["levels", "list", str(path)]) == 0  # the English names
    assert "Aucun niveau de mesure proposé." in capsys.readouterr().out


def test_the_codes(path, capsys):
    capsys.readouterr()
    assert main(["codes", "lister", str(path)]) == 0
    assert "age : 999 — à décider" in capsys.readouterr().out
    assert main(["codes", "manquant", str(path), "-9", "anx1", "anx2", "nb_reveils"]) == 0
    assert main(["codes", "valeur", str(path), "999", "age"]) == 0
    assert main(["codes", "manquant", str(path), "7", "age"]) == 2
    assert "7 n'est pas un code suspect de cette variable." in capsys.readouterr().err
    assert main(["codes", "list", str(path)]) == 0
    out = capsys.readouterr().out
    assert "nb_reveils : -9 — code manquant" in out and "age : 999 — vraie valeur" in out
    assert main(["codes", "annuler", str(path), "999", "age"]) == 0
    assert load_project(path).variable("age").sentinel_decisions == []


def test_the_same_project_as_the_pages(path, tmp_path):
    """The commands write what the pages' functions write."""
    page = load_project(path)
    levels.apply_table(page, {"sommeil_q2": "scale"}, {"age": "accept"}, now=NOW)
    for name in ("anx1", "nb_reveils"):
        logic.decide_sentinel(page, name, -9, True, now=NOW)
    assert main(["niveaux", "accepter", str(path), "age"]) == 0
    assert main(["niveaux", "fixer", str(path), "sommeil_q2", "echelle"]) == 0
    assert main(["codes", "manquant", str(path), "-9", "anx1", "nb_reveils"]) == 0
    command = load_project(path)

    def decided(project):
        return [(e.name, e.measure_level.value, e.measure_level.status,
                 [(d.code, d.missing) for d in e.sentinel_decisions])
                for e in project.variables]  # fmt: skip

    assert decided(page) == decided(command)
    save_project(page, tmp_path / "page.dd.json")  # both still valid projects
