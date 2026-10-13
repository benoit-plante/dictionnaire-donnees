"""Step 5: classification of variables, masking of small counts, no canary past the gate."""

import dataclasses

import pandas as pd
import pytest

from ddict.io import LoadedData, SourceFile, VariableMetadata, read_csv, read_sav
from ddict.privacy import (
    MIN_CELL_COUNT,
    SafeCount,
    classify_database,
    classify_variable,
    safe_database,
)
from ddict.profile import profile_database, profile_variable


def _pipeline(data):
    profiles = profile_database(data)
    classes = classify_database(data, profiles)
    return profiles, classes


@pytest.fixture(scope="module", params=["etude-sommeil.sav", "etude-sommeil_excel-fr.csv"])
def database(request, fictional_files):
    path = fictional_files[request.param]
    data = read_sav(path) if path.suffix == ".sav" else read_csv(path)
    profiles, classes = _pipeline(data)
    return data, profiles, classes


def _by_name(items):
    return {item.name: item for item in items}


def test_fictional_database_classification(database, generator):
    _, _, classes = database
    found = {c.name: c.privacy_class for c in classes if c.privacy_class != "ordinary"}
    expected = {name: "likely_identifier" for name in generator.TRAPS["likely_identifier"]}
    expected.update({name: "quasi_identifier" for name in generator.TRAPS["quasi_identifier"]})
    expected.update({name: "free_text" for name in generator.TRAPS["free_text"]})
    assert found == expected


def test_reasons(database):
    _, _, classes = database
    classes = _by_name(classes)
    assert classes["id_participant"].reasons == ("identifier_name",)
    assert classes["courriel"].reasons == ("identifier_name", "email_values")
    assert classes["commentaire"].reasons == ("free_text_name", "long_text_values")
    assert classes["date_naissance"].reasons == ("birth_date_name", "wide_date_range")


def test_small_counts_are_masked(database):
    data, profiles, classes = database
    safe = _by_name(safe_database(data.variables, profiles, classes, audience="storage"))
    genre = {count.code: count for count in safe["genre"].observed_values}
    assert genre[3] == SafeCount(3, None, False)
    assert genre[3].masked
    assert genre[1].count >= MIN_CELL_COUNT
    for variable in safe.values():
        for count in variable.observed_values or ():
            assert count.count is None or count.count >= MIN_CELL_COUNT


def test_sensitive_variables_keep_only_metadata(database):
    data, profiles, classes = database
    safe = _by_name(safe_database(data.variables, profiles, classes, audience="storage"))
    for name in ["id_participant", "courriel", "date_naissance", "commentaire"]:
        variable = safe[name]
        assert variable.n_valid > 0
        assert variable.observed_values is None
        assert variable.n_distinct is None
        assert variable.date_min is variable.date_max is None


def test_dates_are_reduced_to_years_for_the_model(database):
    data, profiles, classes = database
    model = _by_name(safe_database(data.variables, profiles, classes, audience="model"))
    storage = _by_name(safe_database(data.variables, profiles, classes, audience="storage"))
    assert (model["date_passation"].date_min, model["date_passation"].date_max) == (
        "2026",
        "2026",
    )
    assert storage["date_passation"].date_min.startswith("2026-01-")


@pytest.mark.parametrize("audience", ["model", "storage"])
def test_no_canary_past_the_gate(database, generator, audience):
    data, profiles, classes = database
    safe = safe_database(data.variables, profiles, classes, audience=audience)
    text = repr([dataclasses.asdict(variable) for variable in safe])
    for canary in generator.CANARIES:
        assert canary not in text


def _data(columns, labels=None):
    table = pd.DataFrame(columns)
    variables = tuple(
        VariableMetadata(
            name=name,
            position=i,
            storage_type="numeric" if table[name].dtype == "float64" else "string",
            label=(labels or {}).get(name),
        )
        for i, name in enumerate(table.columns, start=1)
    )
    source = SourceFile(name="t.csv", format="csv", sha256="0", n_rows=len(table), n_columns=0)
    return LoadedData(source=source, variables=variables, table=table)


def _classes(columns, labels=None):
    data = _data(columns, labels)
    _, classes = _pipeline(data)
    return {c.name: c for c in classes}


def test_rare_text_categories_are_hidden_not_only_masked():
    data = _data({"ville": ["Montréal"] * 30 + ["Québec"] * 10 + ["ZQXRARE"] * 2})
    profiles, classes = _pipeline(data)
    (safe,) = safe_database(data.variables, profiles, classes, audience="model")
    assert classes[0].privacy_class == "ordinary"
    assert [c.code for c in safe.observed_values] == ["Montréal", "Québec"]
    assert safe.n_rare_values_hidden == 1
    assert "ZQXRARE" not in repr(dataclasses.asdict(safe))


def test_formats_without_telling_names():
    n = 12
    classes = _classes(
        {
            "contact": [f"p{i}@example.org" for i in range(n)],
            "joindre": [f"514-555-{1000 + i}" for i in range(n)],
            "secteur": ["H2X 1Y4", "G1R 2B5", "H3A 0G4"] * 4,
            "code_unique": [f"A{i:03d}" for i in range(n)],
        }
    )
    assert classes["contact"].reasons == ("email_values",)
    assert classes["joindre"].reasons == ("phone_values",)
    assert classes["secteur"].privacy_class == "quasi_identifier"
    assert classes["secteur"].reasons == ("postal_code_values",)
    assert classes["code_unique"].reasons == ("unique_text_values",)


def test_ordinary_variables_are_not_flagged():
    n = 12
    classes = _classes(
        {
            "temps_reaction_ms": [float(300 + 7 * i) for i in range(n)],  # all distinct
            "accidents": [float(i % 3) for i in range(n)],  # contains "ident"
            "notes": [float(60 + i) for i in range(n)],  # school grades, not free text
            "reponse": ["oui", "non"] * (n // 2),
        }
    )
    assert {c.privacy_class for c in classes.values()} == {"ordinary"}


def test_label_can_reveal_an_identifier():
    classes = _classes({"v1": ["a", "b"]}, labels={"v1": "Numéro de dossier"})
    assert classes["v1"].reasons == ("identifier_name",)


def test_birth_date_by_range_only():
    dates = pd.Series(["1950-01-01", "1990-06-01", "2001-03-03"])
    meta = VariableMetadata(name="d1", position=1, storage_type="string")
    profile = profile_variable(dates, meta)
    assert classify_variable(meta, profile, dates).reasons == ("wide_date_range",)
