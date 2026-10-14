"""v0.2, step 8: Stata, SAS and Excel versions of the fictional base give the same profile
as the .sav, except where the format cannot say what SPSS says."""

import json
from pathlib import Path

import pytest
from openpyxl import Workbook

from ddict.cli import main
from ddict.io import ReadError, read_database, read_dta, read_sas7bdat, read_xlsx
from ddict.project import build_project, load_project

ROOT = Path(__file__).resolve().parent.parent
# Python cannot write SAS files: this one is written by scripts/generer_sas.R and kept.
SAS = ROOT / "exemples" / "bases-fictives" / "etude-sommeil.sas7bdat"
# Fields that depend on value labels, which SAS and Excel files do not carry.
LABEL_FIELDS = {"unlabeled_codes", "unused_labels"}


@pytest.fixture(scope="module")
def reference(fictional_files):
    """Profiles from the .sav, and from the CSV for what only SPSS can declare."""
    sav = build_project(read_database(fictional_files["etude-sommeil.sav"]))
    csv = build_project(read_database(fictional_files["etude-sommeil.csv"]))
    return {e.name: e for e in sav.variables}, {e.name: e.profile for e in csv.variables}


@pytest.fixture(scope="module", params=["dta", "sas7bdat", "xlsx"])
def loaded(request, fictional_files):
    path = SAS if request.param == "sas7bdat" else fictional_files[f"etude-sommeil.{request.param}"]
    return request.param, build_project(read_database(path))


def test_same_profile_as_the_sav(loaded, reference):
    file_format, project = loaded
    sav, csv = reference
    assert project.source.format == file_format
    assert [e.name for e in project.variables] == list(sav)
    for entry in project.variables:
        expected = sav[entry.name]
        if expected.file.declared_missing:
            # SPSS declared missing values (-9, 9) are plain values elsewhere, as in a CSV.
            assert entry.profile == csv[entry.name], entry.name
            continue
        mine = entry.profile.model_dump()
        theirs = expected.profile.model_dump()
        if file_format != "dta":
            for field in LABEL_FIELDS:
                mine.pop(field), theirs.pop(field)
        assert mine == theirs, entry.name


def test_metadata_each_format_carries(loaded, generator):
    file_format, project = loaded
    labels = {e.name: e.file.label for e in project.variables}
    value_labels = {e.name: e.file.value_labels for e in project.variables}
    if file_format == "xlsx":
        assert not any(labels.values()) and not any(value_labels.values())
        return
    assert labels["sommeil_q1"] == generator.COLUMN_LABELS["sommeil_q1"]
    assert labels["sommeil_q7"] is None
    if file_format == "dta":
        assert {v.code: v.label for v in value_labels["sommeil_q1"]} == generator.LIKERT_5
    else:
        assert not any(value_labels.values())  # in a separate SAS format catalog
    assert not any(e.file.declared_missing for e in project.variables)


def test_sas_file_is_up_to_date(fictional_files):
    """The kept SAS file holds the same data as the Stata file written now: if this fails,
    run scripts/generer_sas.R after generer_bases_fictives.py."""
    sas = read_sas7bdat(SAS)
    dta = read_dta(fictional_files["etude-sommeil.dta"])
    assert sas.table.shape == dta.table.shape
    for name in dta.table.columns:
        assert sas.table[name].fillna("").astype(str).tolist() == (
            dta.table[name].fillna("").astype(str).tolist()
        ), name


def test_no_canary_reaches_the_project(loaded, generator):
    _format, project = loaded
    text = json.dumps(project.model_dump(mode="json"), ensure_ascii=False)
    for canary in generator.CANARIES:
        assert canary not in text


def test_profiler_command_reads_every_format(fictional_files, tmp_path, capsys):
    for path in (fictional_files["etude-sommeil.dta"], fictional_files["etude-sommeil.xlsx"], SAS):
        target = tmp_path / f"{path.suffix[1:]}.dd.json"
        assert main(["profiler", str(path), "-o", str(target)]) == 0
        assert load_project(target).source.format == path.suffix[1:]


# --- Excel files as people make them. ---


def _workbook(tmp_path, rows, *, extra_sheet=False):
    workbook = Workbook()
    for row in rows:
        workbook.active.append(row)
    if extra_sheet:
        workbook.create_sheet("notes").append(["à ne pas lire"])
    path = tmp_path / "base.xlsx"
    workbook.save(path)
    return path


def test_excel_types_and_tokens(tmp_path):
    import datetime as dt

    path = _workbook(
        tmp_path,
        [
            ["id", "score", "date", "code_postal", "note"],
            ["a1", 3, dt.datetime(2026, 1, 5), "01234", "NA"],
            ["a2", 4.5, dt.datetime(2026, 2, 7), "H2X", "#N/A"],
            ["a3", None, None, "02000", "ok"],
        ],
        extra_sheet=True,
    )
    loaded = read_xlsx(path)
    table = loaded.table
    assert table["score"].tolist()[:2] == [3.0, 4.5] and table["score"].isna().iloc[2]
    assert table["date"].tolist() == ["2026-01-05", "2026-02-07", ""]
    assert table["code_postal"].tolist() == ["01234", "H2X", "02000"]  # leading zeros kept
    assert loaded.variable("note").missing_tokens == {"NA": 1, "#N/A": 1}
    assert loaded.source.n_columns == 5  # first sheet only


def test_excel_problems_are_explained(tmp_path):
    with pytest.raises(ReadError, match="duplicate"):
        read_xlsx(_workbook(tmp_path, [["a", "a"], [1, 2]]))
    with pytest.raises(ReadError, match="empty"):
        read_xlsx(_workbook(tmp_path, []))
    broken = tmp_path / "broken.xlsx"
    broken.write_bytes(b"not a workbook")
    with pytest.raises(ReadError, match="Excel"):
        read_xlsx(broken)
    nameless = read_xlsx(_workbook(tmp_path, [["a", None, "c"], [1, 2, 3]]))
    assert [v.name for v in nameless.variables] == ["a", "colonne_2", "c"]


@pytest.mark.parametrize("suffix", [".dta", ".sas7bdat"])
def test_broken_stata_and_sas_files(tmp_path, suffix):
    path = tmp_path / f"broken{suffix}"
    path.write_bytes(b"not a data file")
    with pytest.raises(ReadError, match=r"Stata|SAS"):
        read_database(path)
