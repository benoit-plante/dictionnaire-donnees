"""Step 1: the fictional databases are reproducible and contain every planned trap."""

import hashlib
import zipfile

import numpy as np
import pandas as pd
import pyreadstat
import pytest

from conftest import ROOT

SAV = "etude-sommeil.sav"
CSV_PLAIN = "etude-sommeil.csv"
CSV_EXCEL_FR = "etude-sommeil_excel-fr.csv"
CSV_EXCEL_UTF8 = "etude-sommeil_excel-utf8.csv"
CSV_OPTIONS = {
    CSV_PLAIN: dict(encoding="utf-8", sep=",", decimal="."),
    CSV_EXCEL_FR: dict(encoding="cp1252", sep=";", decimal=","),
    CSV_EXCEL_UTF8: dict(encoding="utf-8-sig", sep=";", decimal=","),
}


def _digest(path):
    """The bytes of a file; for a workbook, the content of each part, decompressed: the zip
    compression may differ from one computer to another."""
    if path.suffix != ".xlsx":
        return hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as archive:
        return {
            info.filename: hashlib.sha256(archive.read(info.filename)).hexdigest()
            for info in archive.infolist()
        }


@pytest.fixture(scope="module")
def sav(fictional_files):
    df, meta = pyreadstat.read_sav(fictional_files[SAV], user_missing=True)
    return df, meta


def test_two_runs_write_identical_files(generator, fictional_files, tmp_path):
    second = {path.name: path for path in generator.write_all(tmp_path)}
    assert set(second) == set(fictional_files)
    for name, path in fictional_files.items():
        assert _digest(path) == _digest(second[name]), name


def test_committed_examples_match_the_generator(generator, fictional_files):
    committed_dir = ROOT / "exemples" / "bases-fictives"
    for name, path in fictional_files.items():
        committed = committed_dir / name
        assert committed.exists(), f"{name} missing: run scripts/generer_bases_fictives.py"
        assert _digest(committed) == _digest(path), (
            f"{name} is out of date: regenerate it{_first_difference(committed, path)}"
        )


def _first_difference(committed, produced) -> str:
    """Where two workbooks' sheets first differ, to see why on another system."""
    if committed.suffix != ".xlsx":
        return ""
    with zipfile.ZipFile(committed) as a, zipfile.ZipFile(produced) as b:
        first = a.read("xl/worksheets/sheet1.xml").decode("utf-8")
        second = b.read("xl/worksheets/sheet1.xml").decode("utf-8")
    at = next((i for i, (x, y) in enumerate(zip(first, second, strict=False)) if x != y), None)
    if at is None:
        return f" (lengths {len(first)} and {len(second)})"
    return (
        f"\ncommitted: {first[at - 150 : at + 150]!r}\nproduced:  {second[at - 150 : at + 150]!r}"
    )


def test_sav_has_the_planned_shape(generator, sav):
    df, meta = sav
    assert list(df.columns) == generator.COLUMN_ORDER
    assert len(df) == generator.N_ROWS
    assert meta.file_label == "Etude sommeil (fictive)"


def test_reversed_items_correlate_negatively_with_the_rest(generator, sav):
    df, _ = sav
    items = df[generator.SLEEP_ITEMS].where(df[generator.SLEEP_ITEMS] <= 5)
    reversed_items = set(generator.TRAPS["reversed_items"])
    for item in generator.SLEEP_ITEMS:
        rest = items.drop(columns=item).sum(axis=1)
        r = items[item].corr(rest)
        assert (r < 0) == (item in reversed_items), (item, r)


def test_unlabeled_code(generator, sav):
    df, meta = sav
    for name, code in generator.TRAPS["unlabeled_code"].items():
        assert (df[name] == code).sum() >= 1
        assert code not in meta.variable_value_labels[name]


def test_undeclared_sentinels(generator, sav):
    df, meta = sav
    for name, code in generator.TRAPS["undeclared_sentinel"].items():
        assert (df[name] == code).sum() >= 3
        assert name not in meta.missing_ranges


def test_declared_missing(generator, sav):
    df, meta = sav
    for name, code in generator.TRAPS["declared_missing"].items():
        assert meta.missing_ranges[name] == [{"lo": code, "hi": code}]
        assert (df[name] == code).sum() >= 1, name


def test_unused_label(generator, sav):
    df, meta = sav
    for name, code in generator.TRAPS["unused_label"].items():
        assert code in meta.variable_value_labels[name]
        assert (df[name] == code).sum() == 0


def test_small_count(generator, sav):
    df, _ = sav
    for name, code in generator.TRAPS["small_count"].items():
        assert 0 < (df[name] == code).sum() < 5


def test_constant_all_missing_and_duplicate(generator, sav):
    df, _ = sav
    for name in generator.TRAPS["constant"]:
        assert df[name].nunique(dropna=False) == 1
    for name in generator.TRAPS["all_missing"]:
        assert df[name].isna().all()
    first, second = generator.TRAPS["duplicate_column"]
    assert df[first].equals(df[second])


def test_mixed_types(generator, sav):
    df, _ = sav
    for name in generator.TRAPS["mixed_types"]:
        values = df[name].astype(str)
        numeric = pd.to_numeric(values, errors="coerce")
        assert numeric.notna().sum() > 0
        assert numeric.isna().sum() > 0


def test_missing_file_label(generator, sav):
    _, meta = sav
    labels = dict(zip(meta.column_names, meta.column_labels, strict=True))
    for name in generator.TRAPS["no_file_label"]:
        assert not labels[name]


def test_non_contiguous_scale(generator):
    positions = [generator.COLUMN_ORDER.index(item) for item in generator.ANXIETY_ITEMS]
    assert positions != list(range(positions[0], positions[0] + len(positions)))


def test_canaries_only_in_identifiers_and_free_text(generator, sav):
    df, _ = sav
    allowed = set(generator.TRAPS["likely_identifier"]) | set(generator.TRAPS["free_text"])
    for name in df.columns:
        text = " ".join(df[name].map(str))
        found = [canary for canary in generator.CANARIES if canary in text]
        assert bool(found) == (name in allowed), (name, found)


@pytest.mark.parametrize("name", list(CSV_OPTIONS))
def test_csv_variants_hold_the_same_values(fictional_files, name):
    reference = pd.read_csv(fictional_files[CSV_PLAIN], keep_default_na=False, dtype=str)
    variant = pd.read_csv(
        fictional_files[name], keep_default_na=False, dtype=str, **CSV_OPTIONS[name]
    )
    decimal = CSV_OPTIONS[name]["decimal"]
    normalized = variant.apply(
        lambda column: (
            column.str.replace(decimal, ".", regex=False)
            if column.name == "heures_sommeil" or column.name == "heures_sommeil_2"
            else column
        )
    )
    pd.testing.assert_frame_equal(reference, normalized)


def test_csv_variants_differ_as_planned(fictional_files):
    plain = fictional_files[CSV_PLAIN].read_bytes()
    excel_fr = fictional_files[CSV_EXCEL_FR].read_bytes()
    excel_utf8 = fictional_files[CSV_EXCEL_UTF8].read_bytes()
    assert b"\r\n" not in plain.replace(b'"\r\n', b"")
    assert excel_fr.count(b"\r\n") > 200
    assert excel_utf8.startswith(b"\xef\xbb\xbf")
    with pytest.raises(UnicodeDecodeError):
        excel_fr.decode("utf-8")


def test_csv_keeps_a_comment_with_a_line_break_and_a_semicolon(fictional_files):
    df = pd.read_csv(
        fictional_files[CSV_EXCEL_FR], keep_default_na=False, dtype=str, **CSV_OPTIONS[CSV_EXCEL_FR]
    )
    comments = df["commentaire"]
    assert comments.str.contains("\n").any()
    assert comments.str.contains(";").any()
    assert len(df) == 200
    assert np.all(df["vague"] == "1")
