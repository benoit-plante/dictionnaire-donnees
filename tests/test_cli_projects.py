"""v0.17, step A4 (plan § 6.3): `ddict projets` — `lister` prints the values of the home
page's table; `suivre`, `retirer`, `chercher` and their English names; `chercher` adds
nothing without `--suivre`. On the projects of `projets_stades`."""

import pytest

import projets_stades as stages
from ddict import overview, tracked
from ddict.cli import main


@pytest.fixture(scope="module")
def made(tmp_path_factory):
    return stages.make(tmp_path_factory.mktemp("stades"))


@pytest.fixture(autouse=True)
def fresh():
    overview.clear_cache()


def _run(capsys, *args) -> tuple[int, str, str]:
    capsys.readouterr()
    code = main(list(args))
    out, err = capsys.readouterr()
    return code, out, err


def test_list_prints_the_tables_values(made, capsys):
    for path in made.values():
        tracked.follow(path)
    code, out, _err = _run(capsys, "projets", "lister")
    assert code == 0
    lines = out.splitlines()
    assert lines[0].split() == [
        "Projet", "Phase", "Codebook", "En", "attente", "Plan", "Carnet", "Base", "Modifié",
        "Dossier",
    ]  # fmt: skip
    rows = overview.rows(list(made.values()))
    assert len(lines) == 1 + len(rows)
    for line, row in zip(lines[1:], rows, strict=True):
        for text in (
            overview.phase_text, overview.codebook_text, overview.waiting_text,
            overview.plan_text, overview.notebook_text, overview.base_text,
            overview.modified_text,
        ):  # fmt: skip
            assert text(row) in line
        assert line.startswith(row.name) and line.endswith(row.folder)


def test_list_without_a_project(capsys):
    code, out, _err = _run(capsys, "projects", "list")
    assert code == 0 and "Aucun projet suivi" in out


def test_follow_and_remove(made, capsys):
    path = made["neuf"]
    before = path.read_bytes()
    assert _run(capsys, "projets", "suivre", str(path))[:2] == (0, f"Projet suivi : {path}\n")
    assert _run(capsys, "projects", "follow", str(path))[1] == f"Déjà suivi : {path}\n"
    assert tracked.load() == [path]
    code, out, _err = _run(capsys, "projets", "retirer", str(path))
    assert code == 0 and "son fichier n'est pas touché" in out
    assert tracked.load() == []
    assert "n'était pas suivi" in _run(capsys, "projects", "remove", str(path))[1]
    assert path.read_bytes() == before


def test_a_project_not_found_can_be_removed_not_followed(made, capsys):
    missing = made["introuvable"]
    code, _out, err = _run(capsys, "projets", "suivre", str(missing))
    assert code == 2 and "Pas un fichier projet (.dd.json) existant" in err
    tracked.follow(missing)  # followed when it was there
    assert _run(capsys, "projets", "retirer", str(missing))[0] == 0
    assert tracked.load() == []


def test_follow_refuses_another_file(made, capsys):
    database = made["neuf"].with_name("etude-sommeil.sav")
    assert _run(capsys, "projets", "suivre", str(database))[0] == 2
    assert tracked.load() == []


def test_search_adds_nothing_without_follow(made, capsys):
    root = made["neuf"].parents[1]  # Études 2026\Vague 2
    tracked.follow(made["plan"])
    code, out, _err = _run(capsys, "projets", "chercher", str(root))
    assert code == 0
    found = [p for p in made.values() if p.is_file()]
    for path in found:
        assert str(path) in out
    assert f"{made['plan']} (déjà suivi)" in out
    assert f"{len(found)} projets trouvés, {len(found) - 1} non suivis. Rien n'est ajouté" in out
    assert tracked.load() == [made["plan"]]
    code, out, _err = _run(capsys, "projects", "search", str(root), "--follow")
    assert code == 0 and f"{len(found) - 1} projets suivis." in out
    assert tracked.load() == sorted(found, key=lambda p: str(p).casefold())


def test_search_a_folder_not_found(tmp_path, capsys):
    code, _out, err = _run(capsys, "projets", "chercher", str(tmp_path / "absent"), "--suivre")
    assert code == 2 and "Dossier introuvable" in err
