"""v0.17, step C1 (D-129): a save never overwrites what someone else wrote since the file was
read. Two objects read from the same file: the first saves, the second is refused and the
file keeps the first one's decisions. The same for the notebook and the command line. On
the fictional sleep study, in a folder with accents and spaces."""

import os
import shutil

import pytest

from ddict import cli_decisions
from ddict.analysis import notebook as nb
from ddict.cli import main
from ddict.io import read_database
from ddict.project import ProjectChanged, build_project, dumps, load_project, ondisk, save_project
from test_analysis_data import EXAMPLES


@pytest.fixture
def path(tmp_path):
    folder = tmp_path / "Études 2026" / "Vague 2"
    folder.mkdir(parents=True)
    shutil.copy(EXAMPLES / "etude-sommeil.csv", folder / "etude-sommeil.csv")
    assert main(["profiler", str(folder / "etude-sommeil.csv")]) == 0
    return folder / "etude-sommeil.dd.json"


def test_the_second_save_is_refused_and_the_first_kept(path):
    first, second = load_project(path), load_project(path)
    first.plan.sample_size = "Première session"
    second.plan.sample_size = "Seconde session"
    save_project(first, path)
    with pytest.raises(ProjectChanged) as refused:
        save_project(second, path)
    assert refused.value.reason == "changed"
    assert path.read_bytes() == dumps(first).encode("utf-8")
    # The first one goes on saving: it remembers what it wrote.
    first.plan.sample_size = "Encore la première"
    save_project(first, path)
    assert load_project(path).plan.sample_size == "Encore la première"
    # Read again, the second one may save.
    second = load_project(path)
    second.plan.sample_size = "Seconde, après relecture"
    save_project(second, path)
    assert load_project(path).plan.sample_size == "Seconde, après relecture"


def test_the_bytes_written_have_not_changed(path):
    project = load_project(path)
    save_project(project, path)
    content = path.read_bytes()
    assert content == dumps(project).encode("utf-8")
    assert b"\r" not in content
    assert not path.with_name(path.name + ".tmp").exists()


def test_a_change_of_the_same_size_and_date_is_seen(path):
    """ "validated" and "corrected" have the same length: the date and size would miss it."""
    project = load_project(path)
    stat = path.stat()
    content = path.read_bytes()
    changed = content.replace(b'"status": "proposed"', b'"status": "rejected"', 1)
    assert changed != content and len(changed) == len(content)
    path.write_bytes(changed)
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    with pytest.raises(ProjectChanged):
        save_project(project, path)
    assert path.read_bytes() == changed


def test_a_date_touched_without_change_is_no_alarm(path):
    """OneDrive may touch the date of a file it did not change."""
    project = load_project(path)
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))
    assert ondisk.unchanged(path, ondisk.remembered(project))
    save_project(project, path)


def test_a_file_gone_is_not_written_again(path):
    project = load_project(path)
    path.unlink()
    with pytest.raises(ProjectChanged) as refused:
        save_project(project, path)
    assert refused.value.reason == "missing"
    assert not path.exists()


def test_a_new_project_does_not_overwrite_a_file(path):
    fresh = build_project(read_database(path.with_name("etude-sommeil.csv")))
    before = path.read_bytes()
    with pytest.raises(ProjectChanged) as refused:
        save_project(fresh, path)
    assert refused.value.reason == "exists"
    assert path.read_bytes() == before
    save_project(fresh, path, overwrite=True)  # "Remplacer le projet existant"
    assert path.read_bytes() == dumps(fresh).encode("utf-8")


def test_unchanged_tells_a_real_change(path):
    project = load_project(path)
    other = load_project(path)
    other.plan.sample_size = "Ailleurs"
    save_project(other, path)
    assert not ondisk.unchanged(path, ondisk.remembered(project))
    assert ondisk.unchanged(path, ondisk.remembered(other))


def test_the_path_is_compared_without_case(path):
    project = load_project(path)
    upper = path.with_name(path.name.upper())
    assert ondisk.key(upper) == ondisk.key(path)
    save_project(project, upper)  # the same file, under Windows


def test_the_notebook_follows_the_same_rule(path):
    project = load_project(path)
    target = nb.notebook_path(path)
    first, second = nb.open_notebook(project, path), nb.open_notebook(project, path)
    first.first_table = 2
    nb.save_notebook(first, target)
    # A new notebook begun before the first was written: refused.
    second.first_table = 3
    with pytest.raises(nb.NotebookChanged) as refused:
        nb.save_notebook(second, target)
    assert refused.value.reason == "exists"
    # Two notebooks read from the file: the second save is refused.
    first, second = nb.load_notebook(target), nb.load_notebook(target)
    first.first_figure = 4
    nb.save_notebook(first, target)
    second.first_figure = 5
    with pytest.raises(nb.NotebookChanged) as refused:
        nb.save_notebook(second, target)
    assert refused.value.reason == "changed"
    kept = nb.load_notebook(target)
    assert (kept.first_table, kept.first_figure) == (2, 4)


def test_the_command_line_refuses_and_says_so(path, monkeypatch, capsys):
    """Someone saves while the command runs: the command saves nothing, exits non-zero."""

    def load_then_someone_else_saves(where):
        project = load_project(where)
        other = load_project(where)
        other.plan.sample_size = "Depuis l'interface"
        save_project(other, where)
        return project

    monkeypatch.setattr(cli_decisions, "load_project", load_then_someone_else_saves)
    capsys.readouterr()
    assert main(["niveaux", "accepter", str(path), "age"]) == 2
    err = capsys.readouterr().err
    assert "a été modifié ailleurs pendant la commande" in err
    assert "Rien n'est enregistré : relancez la commande." in err
    kept = load_project(path)
    assert kept.plan.sample_size == "Depuis l'interface"
    assert kept.variable("age").measure_level.status == "proposed"
