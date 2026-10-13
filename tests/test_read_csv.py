"""Step 3: the three CSV variants give the same table, guessed without any option."""

import numpy as np
import pandas as pd
import pytest

from ddict.io import ReadError, read_csv, read_database

VARIANTS = {
    "etude-sommeil.csv": ("utf-8", ",", "."),
    "etude-sommeil_excel-fr.csv": ("cp1252", ";", ","),
    "etude-sommeil_excel-utf8.csv": ("utf-8-sig", ";", ","),
}


@pytest.fixture(scope="module")
def loaded(fictional_files):
    return {name: read_csv(fictional_files[name]) for name in VARIANTS}


@pytest.mark.parametrize("name", list(VARIANTS))
def test_guesses_encoding_delimiter_and_decimal(loaded, name):
    source = loaded[name].source
    assert (source.encoding, source.delimiter, source.decimal) == VARIANTS[name]
    assert (source.format, source.n_rows, source.n_columns) == ("csv", 200, 29)


@pytest.mark.parametrize("name", list(VARIANTS))
def test_variants_give_the_same_table(loaded, name):
    pd.testing.assert_frame_equal(loaded[name].table, loaded["etude-sommeil.csv"].table)


def test_numeric_columns_match_the_sav_file(loaded, fictional_files, generator):
    from ddict.io import read_sav

    sav = read_sav(fictional_files["etude-sommeil.sav"]).table
    csv_table = loaded["etude-sommeil_excel-fr.csv"].table
    numeric = [n for n in generator.COLUMN_ORDER if csv_table[n].dtype == "float64"]
    assert "heures_sommeil" in numeric and "anx1" in numeric and "q_retiree" in numeric
    for name in numeric:
        np.testing.assert_array_equal(csv_table[name].to_numpy(), sav[name].to_numpy(), name)


def test_storage_types(loaded):
    data = loaded["etude-sommeil_excel-fr.csv"]
    assert data.variable("age").storage_type == "numeric"
    for name in ["id_participant", "courriel", "taille_cm", "commentaire", "date_naissance"]:
        assert data.variable(name).storage_type == "string", name


def test_free_text_keeps_line_breaks_semicolons_and_accents(loaded, fictional_files):
    comments = loaded["etude-sommeil_excel-fr.csv"].table["commentaire"]
    assert comments.str.contains("\n").any()
    assert comments.str.contains(";").any()
    assert comments.str.contains("très").any()
    assert (comments == "").sum() == 140


def test_read_database_picks_the_reader(fictional_files):
    assert read_database(fictional_files["etude-sommeil.csv"]).source.format == "csv"
    assert read_database(fictional_files["etude-sommeil.sav"]).source.format == "sav"


def _write(tmp_path, content, encoding="utf-8", name="test.csv"):
    path = tmp_path / name
    path.write_bytes(content.encode(encoding))
    return path


def test_leading_zeros_keep_a_column_as_text(tmp_path):
    path = _write(tmp_path, "code,n\n0123,1\n0456,2\n")
    table = read_csv(path).table
    assert list(table["code"]) == ["0123", "0456"]
    assert table["n"].dtype == "float64"


def test_zero_and_decimals_below_one_stay_numeric(tmp_path):
    path = _write(tmp_path, "x;y\n0;0,5\n10;-0,25\n")
    data = read_csv(path)
    assert data.source.decimal == ","
    assert list(data.table["x"]) == [0.0, 10.0]
    assert list(data.table["y"]) == [0.5, -0.25]


def test_semicolon_file_with_dot_decimals(tmp_path):
    data = read_csv(_write(tmp_path, "a;b\n1.5;x\n2.25;y\n"))
    assert (data.source.delimiter, data.source.decimal) == (";", ".")
    assert list(data.table["a"]) == [1.5, 2.25]


def test_tab_delimiter(tmp_path):
    data = read_csv(_write(tmp_path, "a\tb\n1\t2\n"))
    assert data.source.delimiter == "\t"


def test_empty_header_name_is_named_by_position(tmp_path):
    data = read_csv(_write(tmp_path, "a,,c\n1,2,3\n"))
    assert [v.name for v in data.variables] == ["a", "colonne_2", "c"]


def test_options_can_be_forced(tmp_path):
    path = _write(tmp_path, "a;b\n1,5;2\n")
    data = read_csv(path, delimiter=";", decimal=".", encoding="utf-8")
    assert data.table["a"].tolist() == ["1,5"]


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("a,b\n1,2\n3\n", "number of fields"),
        ("a,a\n1,2\n", "duplicate column names: a"),
        ("", "delimiter"),
    ],
)
def test_malformed_files_raise_read_error(tmp_path, content, message):
    with pytest.raises(ReadError, match=message):
        read_csv(_write(tmp_path, content))


def test_unsupported_extension(tmp_path):
    with pytest.raises(ReadError, match="Unsupported"):
        read_database(_write(tmp_path, "a,b\n", name="base.txt"))
