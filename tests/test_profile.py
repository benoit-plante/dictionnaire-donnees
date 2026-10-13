"""Step 4: profiling finds every trap and the expected values of the fictional database."""

import numpy as np
import pandas as pd
import pytest

from ddict.io import MissingRange, VariableMetadata, read_csv, read_sav
from ddict.profile import ObservedValue, profile_database, profile_variable


@pytest.fixture(scope="module")
def raw(generator):
    """The generator's own table, to compute expected values independently."""
    df, _ = generator.build_dataset()
    return df


@pytest.fixture(scope="module")
def sav(fictional_files):
    return {p.name: p for p in profile_database(read_sav(fictional_files["etude-sommeil.sav"]))}


@pytest.fixture(scope="module")
def csv(fictional_files):
    path = fictional_files["etude-sommeil_excel-fr.csv"]
    return {p.name: p for p in profile_database(read_csv(path))}


def test_inferred_types(sav):
    expected = {
        "id_participant": "text",
        "courriel": "text",
        "date_passation": "datetime",
        "date_naissance": "date",
        "age": "integer",
        "genre": "integer",
        "sommeil_q1": "integer",
        "anx1": "integer",
        "heures_sommeil": "decimal",
        "taille_cm": "mixed",
        "q_retiree": "empty",
        "commentaire": "text",
    }
    for name, inferred in expected.items():
        assert sav[name].inferred_type == inferred, name


def test_csv_infers_the_same_types(sav, csv):
    for name, profile in sav.items():
        assert csv[name].inferred_type == profile.inferred_type, name


def test_counts_match_the_generated_table(sav, raw):
    for name, profile in sav.items():
        column = raw[name]
        empty = column.isna() | column.map(lambda v: isinstance(v, str) and not v.strip())
        assert profile.n_rows == 200
        assert profile.n_system_missing == int(empty.sum()), name
        assert profile.n_valid + profile.n_missing == 200, name


def test_declared_missing_are_counted_apart(sav, raw):
    assert sav["genre"].n_declared_missing == 4
    assert sav["genre"].n_valid == 196
    for item in [f"anx{i}" for i in range(1, 8)]:
        assert sav[item].n_declared_missing == int((raw[item] == -9).sum())
        assert sav[item].min == 0.0
    assert sav["genre"].pct_missing == pytest.approx(2.0)


def test_numeric_statistics(sav, raw):
    hours = raw["heures_sommeil"]
    profile = sav["heures_sommeil"]
    assert profile.min == hours.min()
    assert profile.max == hours.max()
    assert profile.mean == pytest.approx(hours.mean())
    assert profile.sd == pytest.approx(hours.std(ddof=1))
    assert profile.median == pytest.approx(hours.median())
    assert profile.q1 == pytest.approx(hours.quantile(0.25))
    assert profile.q3 == pytest.approx(hours.quantile(0.75))
    assert sav["age"].max == 999.0


def test_date_ranges(sav, csv, raw):
    births = raw["date_naissance"]
    assert sav["date_naissance"].date_min == min(births).isoformat()
    assert sav["date_naissance"].date_max == max(births).isoformat()
    assert sav["date_passation"].date_min.startswith("2026-01")
    for name in ["date_naissance", "date_passation"]:
        assert csv[name].date_min == sav[name].date_min
        assert csv[name].date_max == sav[name].date_max
        assert sav[name].observed_values is None


def test_text_lengths_but_no_listing_of_many_values(sav):
    comment = sav["commentaire"]
    assert comment.n_valid == 60
    assert comment.length_min > 0 and comment.length_max >= comment.length_min
    assert comment.observed_values is None
    assert sav["id_participant"].n_distinct == 200
    assert sav["id_participant"].observed_values is None


def test_observed_values_with_declared_missing(sav, raw):
    genre = sav["genre"].observed_values
    assert [v.code for v in genre] == [1, 2, 3, 9]
    assert genre[2] == ObservedValue(3, 2, False)
    assert genre[3] == ObservedValue(9, 4, True)
    assert sum(v.count for v in genre) == 200
    anx1 = {v.code: v for v in sav["anx1"].observed_values}
    assert anx1[-9].declared_missing
    assert anx1[-9].count == int((raw["anx1"] == -9).sum())


def test_unlabeled_code(sav, csv):
    assert sav["sommeil_q3"].unlabeled_codes == (9,)
    others = [p for name, p in sav.items() if name != "sommeil_q3"]
    assert all(p.unlabeled_codes == () for p in others)
    # Labels only at the ends of a 0-10 scale do not make 1-9 "unlabeled".
    assert sav["satisfaction_globale"].unlabeled_codes == ()
    # A CSV file has no labels.
    assert all(p.unlabeled_codes == () for p in csv.values())


def test_unused_label(sav):
    assert sav["satisfaction_globale"].unused_labels == (99,)
    others = [p for name, p in sav.items() if name != "satisfaction_globale"]
    assert all(p.unused_labels == () for p in others)


def test_suspect_missing_codes(sav, csv, generator):
    expected = dict(generator.TRAPS["undeclared_sentinel"])
    # 9 after a 1-5 scale, without a label: a classic "don't know" code.
    expected["sommeil_q3"] = 9
    found = {name: p.suspect_missing_codes for name, p in sav.items() if p.suspect_missing_codes}
    assert found == {name: (code,) for name, code in expected.items()}
    # Without declarations, the CSV shows the declared missing codes as suspects too.
    for name, code in generator.TRAPS["declared_missing"].items():
        assert csv[name].suspect_missing_codes == (code,), name


def test_flags(sav, csv):
    for profiles in (sav, csv):
        flagged = {name: p.flags for name, p in profiles.items() if p.flags}
        assert flagged == {
            "vague": ("constant",),
            "heures_sommeil_2": ("duplicate",),
            "taille_cm": ("mixed_types",),
            "q_retiree": ("all_missing",),
        }
        assert profiles["heures_sommeil_2"].duplicate_of == "heures_sommeil"
    assert sav["taille_cm"].n_non_numeric == 7


def test_profiles_are_deterministic(fictional_files):
    first = profile_database(read_sav(fictional_files["etude-sommeil.sav"]))
    second = profile_database(read_sav(fictional_files["etude-sommeil.sav"]))
    assert first == second


def _meta(name="x", storage_type="numeric", **kwargs):
    return VariableMetadata(name=name, position=1, storage_type=storage_type, **kwargs)


def test_boolean_and_declared_missing_range():
    profile = profile_variable(
        pd.Series([0.0, 1.0, 1.0, 97.0, 98.0, np.nan]),
        _meta(declared_missing=(MissingRange(97, 99),)),
    )
    assert profile.inferred_type == "boolean"
    assert (profile.n_valid, profile.n_declared_missing, profile.n_system_missing) == (3, 2, 1)


def test_positive_sentinel_needs_a_clear_gap():
    one_to_eight = pd.Series([float(v) for v in [*range(1, 9), 9]])
    assert profile_variable(one_to_eight, _meta()).suspect_missing_codes == ()
    one_to_five = pd.Series([1.0, 2.0, 5.0, 99.0])
    assert profile_variable(one_to_five, _meta()).suspect_missing_codes == (99,)


def test_negative_code_in_a_scale_with_negatives_is_not_suspect():
    values = pd.Series([-3.0, -1.0, 0.0, 2.0, 3.0])
    assert profile_variable(values, _meta()).suspect_missing_codes == ()


def test_more_than_twenty_distinct_values_are_not_listed():
    profile = profile_variable(pd.Series([float(v) for v in range(21)]), _meta())
    assert profile.observed_values is None
    assert profile.n_distinct == 21


def test_codes_with_leading_zeros_are_text():
    series = pd.Series(["0123", "0456", ""], dtype=object)
    profile = profile_variable(series, _meta(storage_type="string"))
    assert profile.inferred_type == "text"
    assert profile.n_system_missing == 1
