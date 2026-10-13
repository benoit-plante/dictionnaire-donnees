"""Step 2: reading a .sav file finds exactly the metadata written by the generator."""

import datetime as dt
import hashlib
import shutil

import pandas as pd
import pytest

from ddict.io import MissingRange, ReadError, read_sav


@pytest.fixture(scope="module")
def loaded(fictional_files):
    return read_sav(fictional_files["etude-sommeil.sav"])


@pytest.fixture(scope="module")
def expected(generator):
    _, meta = generator.build_dataset()
    return meta


def test_source_identity(loaded, fictional_files):
    path = fictional_files["etude-sommeil.sav"]
    assert loaded.source.name == "etude-sommeil.sav"
    assert loaded.source.format == "sav"
    assert loaded.source.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert (loaded.source.n_rows, loaded.source.n_columns) == (200, 29)
    assert loaded.source.label == "Etude sommeil (fictive)"
    assert loaded.source.encoding == "UTF-8"


def test_names_and_positions(loaded, generator):
    assert [v.name for v in loaded.variables] == generator.COLUMN_ORDER
    assert [v.position for v in loaded.variables] == list(range(1, 30))


def test_variable_labels(loaded, expected):
    for variable in loaded.variables:
        assert variable.label == expected["column_labels"][variable.name], variable.name
    assert loaded.variable("sommeil_q7").label is None


def test_value_labels_with_accents_and_integer_codes(loaded, expected):
    for variable in loaded.variables:
        assert variable.value_labels == expected["variable_value_labels"].get(variable.name, {})
    genre = loaded.variable("genre").value_labels
    assert list(genre) == [1, 2, 3, 9]
    assert all(type(code) is int for code in genre)
    assert genre[3] == "Autre identité"
    assert list(loaded.variable("anx1").value_labels) == [-9, 0, 1, 2, 3]


def test_declared_missing(loaded, expected):
    for variable in loaded.variables:
        codes = expected["missing_ranges"].get(variable.name, [])
        assert variable.declared_missing == tuple(MissingRange(c, c) for c in codes)


def test_measure_levels(loaded, expected):
    for variable in loaded.variables:
        assert variable.measure_level == expected["variable_measure"][variable.name]


def test_formats_and_storage(loaded, expected):
    for name, spss_format in expected["variable_format"].items():
        assert loaded.variable(name).display_format == spss_format
    assert loaded.variable("date_naissance").display_format.startswith("DATE")
    assert loaded.variable("date_passation").display_format.startswith("DATETIME")
    for name in ["id_participant", "courriel", "taille_cm", "commentaire"]:
        assert loaded.variable(name).storage_type == "string"
        assert loaded.variable(name).display_format.startswith("A")
    assert loaded.variable("age").storage_type == "numeric"


def test_declared_missing_values_stay_in_the_table(loaded):
    table = loaded.table
    assert (table["anx1"] == -9).sum() >= 1
    assert (table["genre"] == 9).sum() == 4
    assert table["q_retiree"].isna().all()


def test_dates_are_read_as_dates(loaded):
    table = loaded.table
    assert pd.api.types.is_datetime64_any_dtype(table["date_passation"])
    assert isinstance(table["date_naissance"].dropna().iloc[0], dt.date)


def test_path_with_accents_and_spaces(fictional_files, tmp_path):
    folder = tmp_path / "Données de l'équipe"
    folder.mkdir()
    copy = folder / "étude sommeil.sav"
    shutil.copyfile(fictional_files["etude-sommeil.sav"], copy)
    assert read_sav(copy).source.n_rows == 200


def test_unreadable_file_raises_read_error(tmp_path):
    bogus = tmp_path / "pas-un-spss.sav"
    bogus.write_text("ceci n'est pas un fichier SPSS", encoding="utf-8")
    with pytest.raises(ReadError, match=r"pas-un-spss\.sav"):
        read_sav(bogus)


def test_missing_file_raises_read_error(tmp_path):
    with pytest.raises(ReadError):
        read_sav(tmp_path / "absent.sav")
