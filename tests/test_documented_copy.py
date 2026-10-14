"""v0.4, step 4: the documented copy of the database (D-026)."""

import shutil
from pathlib import Path

import pyreadstat
import pytest
from streamlit.testing.v1 import AppTest

from ddict.cli import main
from ddict.export import documented
from ddict.export.documented import CopyError, CopyExists, differences, write_documented_copy
from ddict.io import read_database
from ddict.io.sav import file_sha256
from ddict.project import build_project, load_project, save_project
from ddict.review import logic
from ddict.workflow import documented_copy, profile_database

NOW = "2026-10-14T15:00:00"
APP = str(Path(__file__).resolve().parent.parent / "src" / "ddict" / "review" / "app.py")


@pytest.fixture
def project_path(fictional_files, tmp_path):
    folder = tmp_path / "projet"
    folder.mkdir()
    shutil.copy(fictional_files["etude-sommeil.sav"], folder / "etude-sommeil.sav")
    project, path = profile_database(folder / "etude-sommeil.sav")
    logic.decide_sentinel(project, "age", 999, True, now=NOW)
    save_project(project, path)
    return path


def _read(path, **options):
    return pyreadstat.read_sav(str(path), user_missing=True, **options)


def test_same_data_with_the_decisions(project_path):
    original = project_path.with_name("etude-sommeil.sav")
    before = (file_sha256(original), original.stat().st_mtime_ns)
    project_before = project_path.read_bytes()

    result = documented_copy(load_project(project_path), project_path)

    assert result.path == project_path.with_name("etude-sommeil-documente.sav")
    assert (result.n_rows, result.n_columns) == (200, 34)
    raw = {"disable_datetime_conversion": True}
    assert differences(_read(original, **raw)[0], _read(result.path, **raw)[0]) == 0
    _, a = _read(original, metadataonly=True)
    _, b = _read(result.path, metadataonly=True)
    assert b.column_names_to_labels == a.column_names_to_labels
    assert b.variable_value_labels == a.variable_value_labels
    assert b.variable_measure == a.variable_measure
    assert b.original_variable_types == a.original_variable_types  # dates stay dates
    assert b.missing_ranges == {**a.missing_ranges, "age": [{"lo": 999.0, "hi": 999.0}]}
    # The original is untouched, and nothing of the data enters the project.
    assert (file_sha256(original), original.stat().st_mtime_ns) == before
    assert project_path.read_bytes() == project_before
    assert not list(project_path.parent.glob("*.en-cours"))


@pytest.mark.parametrize(
    "name",
    ["etude-sommeil.csv", "etude-sommeil_excel-fr.csv", "etude-sommeil.dta", "etude-sommeil.xlsx"],
)
def test_other_formats_become_a_sav(fictional_files, tmp_path, name):
    database = tmp_path / name
    shutil.copy(fictional_files[name], database)
    project = build_project(read_database(database))
    result = write_documented_copy(project, database)
    assert result.path.name == Path(name).stem + "-documente.sav"
    copy, _meta = _read(result.path)
    assert differences(read_database(database).table, copy) == 0


def test_never_written_over_without_asking(project_path):
    project = load_project(project_path)
    first = documented_copy(project, project_path)
    first.path.write_bytes(b"une copie plus ancienne")
    with pytest.raises(CopyExists):
        documented_copy(project, project_path)
    assert first.path.read_bytes() == b"une copie plus ancienne"
    documented_copy(project, project_path, replace=True)
    assert _read(first.path)[0].shape == (200, 34)


def test_a_copy_that_differs_is_deleted(project_path, monkeypatch):
    project = load_project(project_path)
    target = project_path.with_name("etude-sommeil-documente.sav")
    target.write_bytes(b"une copie plus ancienne")

    def altered(path, file_format):
        table, _meta = _read(path, disable_datetime_conversion=True)
        table.loc[3, "age"] = 41.0
        return table

    monkeypatch.setattr(documented, "_read_back", altered)
    with pytest.raises(CopyError) as caught:
        documented_copy(project, project_path, replace=True)
    assert (caught.value.reason, caught.value.detail) == ("not_identical", "1")
    assert target.read_bytes() == b"une copie plus ancienne"  # the old one kept
    assert not list(project_path.parent.glob("*.en-cours"))


def test_the_database_is_found_and_checked(project_path, tmp_path):
    project = load_project(project_path)
    original = project_path.with_name("etude-sommeil.sav")
    moved = tmp_path / "ailleurs.sav"
    original.replace(moved)
    with pytest.raises(CopyError) as caught:
        documented_copy(project, project_path)
    assert caught.value.reason == "not_found"
    assert documented_copy(project, project_path, database=moved).path == tmp_path / (
        "ailleurs-documente.sav"
    )
    other = tmp_path / "autre.sav"
    shutil.copy(moved, other)
    with other.open("ab") as handle:
        handle.write(b"\0")
    with pytest.raises(CopyError) as caught:
        documented_copy(project, project_path, database=other)
    assert caught.value.reason == "other_file"
    with pytest.raises(CopyError) as caught:
        documented_copy(project, project_path, database=moved, target=moved)
    assert caught.value.reason == "same_file"


def test_more_missing_codes_than_spss_holds(project_path):
    project = load_project(project_path)
    entry = project.variable("genre")
    entry.profile.suspect_missing_codes = [7, 8, 99]  # with the declared 9: four codes
    for code in (7, 8, 99):
        logic.decide_sentinel(project, "genre", code, True, now=NOW)
    result = documented_copy(project, project_path)
    assert result.missing_not_written == ["genre"]
    # The code declared in the file is kept.
    assert _read(result.path, metadataonly=True)[1].missing_ranges["genre"] == [
        {"lo": 9.0, "hi": 9.0}
    ]


def test_command(project_path, capsys):
    assert main(["documenter", str(project_path)]) == 0
    assert "identique à l'original case par case" in capsys.readouterr().out
    assert main(["documenter", str(project_path)]) == 2
    assert "--remplacer" in capsys.readouterr().err
    assert main(["documenter", str(project_path), "--remplacer"]) == 0


def _open(path):
    app = AppTest.from_file(APP, default_timeout=30)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "export"
    app.run()
    assert not app.exception, app.exception
    return app


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_export_page(project_path):
    app = _open(project_path)
    app.button(key="export-copy-write").click().run()
    assert "identiques case par case" in app.success[0].value
    assert project_path.with_name("etude-sommeil-documente.sav").exists()
    assert app.button(key="export-copy-write").disabled  # it exists now
    app.checkbox(key="copy-replace").check().run()
    app.button(key="export-copy-write").click().run()
    assert "identiques case par case" in app.success[0].value


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_export_page_without_the_database(project_path):
    project_path.with_name("etude-sommeil.sav").unlink()
    app = _open(project_path)
    assert any("introuvable à côté du projet" in x.value for x in app.info)
    assert not [b for b in app.button if b.key == "export-copy-write"]
