"""v0.7, step 3: corrections found on two real SurveyMonkey exports (docs/plan-v0.7.md, § 3.5).

Each finding of the trial has its rule, checked here on small made-up columns; the counts on
the fictional export are in test_surveymonkey.py.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ddict.export.wording import entry_anomalies
from ddict.groups import find_groups, item_prefix
from ddict.io import LoadedData, SourceFile, VariableMetadata, read_database
from ddict.privacy import classify_database
from ddict.privacy.classify import classify_variable
from ddict.profile import profile_database
from ddict.profile.compute import is_missing_label, profile_variable
from ddict.project import build_project

EXAMPLES = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"
LIKERT = {1: "Jamais", 2: "Rarement", 3: "Parfois", 4: "Souvent", 5: "Toujours"}


def _data(columns: dict, labels: dict | None = None, label_of: dict | None = None) -> LoadedData:
    table = pd.DataFrame(columns)
    variables = tuple(
        VariableMetadata(
            name=name,
            position=i,
            storage_type="numeric" if table[name].dtype == "float64" else "string",
            label=(label_of or {}).get(name),
            value_labels=(labels or {}).get(name, {}),
        )
        for i, name in enumerate(table.columns, start=1)
    )
    source = SourceFile(name="t.sav", format="sav", sha256="0", n_rows=len(table), n_columns=0)
    return LoadedData(source=source, variables=variables, table=table)


def _groups(data):
    profiles = profile_database(data)
    return find_groups(data, profiles, classify_database(data, profiles))


# --- The common prefix needs a meaningful stem. ---


@pytest.mark.parametrize(
    ("name", "prefix"),
    [
        ("q1", None),
        ("q0001", None),
        ("q_2", None),
        ("Q12", None),
        ("ab1", None),
        ("ab_1", "ab"),
        ("anx3", "anx"),
        ("sommeil_q3", "sommeil_q"),
    ],
)
def test_a_prefix_needs_a_meaningful_stem(name, prefix):
    assert item_prefix(name) == prefix


def test_numbered_questions_are_not_a_scale():
    rng = np.random.default_rng(3)
    columns = {f"q{k:04d}": rng.integers(1, 4, size=40).astype(float) for k in (1, 2, 6, 7)}
    assert _groups(_data(columns)) == ()


# --- A variable left out of a group does not cut it in two. ---


def test_a_left_out_item_does_not_cut_the_grid():
    rng = np.random.default_rng(1)
    latent = rng.normal(size=60)
    item = lambda: np.clip(np.round(3 + latent + rng.normal(scale=0.7, size=60)), 1, 5)  # noqa: E731
    names = ["vie_a", "travail_b", "sante_c", "constant_d", "loisirs_e", "famille_f", "amis_g"]
    columns = {name: item() for name in names}
    columns["constant_d"] = np.full(60, 3.0)  # left out: constant
    (group,) = _groups(_data(columns, labels={name: LIKERT for name in names}))
    assert group.members == tuple(n for n in names if n != "constant_d")


def test_a_different_neighbour_still_cuts_the_run():
    rng = np.random.default_rng(2)
    latent = rng.normal(size=60)
    item = lambda: np.clip(np.round(3 + latent + rng.normal(scale=0.7, size=60)), 1, 5)  # noqa: E731
    names = ["vie_a", "travail_b", "sante_c", "age", "loisirs_e", "famille_f", "amis_g"]
    columns = {name: item() for name in names}
    columns["age"] = np.full(60, 30.0)
    labels = {name: LIKERT for name in names if name != "age"}
    found = _groups(_data(columns, labels=labels))
    assert [g.members for g in found] == [
        ("vie_a", "travail_b", "sante_c"),
        ("loisirs_e", "famille_f", "amis_g"),
    ]


# --- An identifier by its label only when the label designates one. ---


def _class(name: str, label: str | None, values) -> str:
    series = pd.Series(values)
    variable = VariableMetadata(
        name=name,
        position=1,
        storage_type="numeric" if series.dtype == "float64" else "string",
        label=label,
    )
    return classify_variable(variable, profile_variable(series, variable), series).privacy_class


LIKERT_VALUES = [float(v) for v in [1, 2, 3, 4, 5] * 8]


@pytest.mark.parametrize(
    "label",
    [
        "J'ai pu identifier les sources de tension dans mon équipe.",
        "Identifier ses émotions avant de réagir est facile pour moi.",
        "Je sais identifier mes forces et mes faiblesses au travail.",
    ],
)
def test_the_verb_identifier_in_a_sentence_is_not_an_identifier(label):
    assert _class("q0003_0005", label, LIKERT_VALUES) == "ordinary"


@pytest.mark.parametrize(
    "label",
    ["Identifiant", "ID", "id", "Numéro de participant", "Quel est votre nom ?",
     "Participant identifier", "Identifiant unique du participant dans la base de données"],
)  # fmt: skip
def test_a_label_that_names_an_identifier_still_counts(label):
    assert _class("q0012", label, [f"F{k:03d}" for k in range(40)]) == "likely_identifier"


def test_an_identifier_name_still_counts_whatever_the_label():
    assert _class("id_participant", "Code", [f"F{k:03d}" for k in range(40)]) == (
        "likely_identifier"
    )


# --- Survey dates written as text. ---


def test_dates_with_a_12_hour_clock_are_datetimes():
    texts = ["03/02/2026 07:15:23 AM", "03/13/2026 01:05:00 PM", "03/20/2026 11:59:59 PM"]
    variable = VariableMetadata(name="StartDate", position=1, storage_type="string")
    profile = profile_variable(pd.Series(texts), variable)
    assert profile.inferred_type == "datetime"
    assert (profile.date_min, profile.date_max) == ("2026-03-02T07:15:23", "2026-03-20T23:59:59")
    assert _class("StartDate", None, texts) == "ordinary"  # no longer free text


def test_dates_with_a_24_hour_clock_are_read_day_first():
    texts = ["13/02/2026 14:05", "01/03/2026 08:30"]
    variable = VariableMetadata(name="horodatage", position=1, storage_type="string")
    profile = profile_variable(pd.Series(texts), variable)
    assert profile.inferred_type == "datetime"
    assert profile.date_min == "2026-02-13T14:05:00"


def test_a_text_that_only_starts_like_a_date_stays_text():
    texts = ["03/02/2026 07:15:23 AM", "pas de date"]
    variable = VariableMetadata(name="note", position=1, storage_type="string")
    assert profile_variable(pd.Series(texts), variable).inferred_type == "text"


# --- "Ne sais pas" and its kind, by their label. ---


@pytest.mark.parametrize(
    "label",
    ["Ne sais pas", "Je ne sais pas", "NSP", "Préfère ne pas répondre", "Refus",
     "Refus de répondre", "Sans objet", "Ne s'applique pas", "Don't know",
     "Prefer not to answer", "Prefer not to say", "Refused", "Not applicable", "N/A"],
)  # fmt: skip
def test_non_answer_labels(label):
    assert is_missing_label(label)


@pytest.mark.parametrize(
    "label",
    ["Jamais", "Toujours", "Refuser une tâche", "Pas du tout d'accord", "Nationale",
     "J'ai refusé une promotion parce que je ne savais pas quoi faire"],
)  # fmt: skip
def test_answer_labels(label):
    assert not is_missing_label(label)


def test_a_non_answer_code_is_a_suspect_missing_code_when_observed():
    labels = {**LIKERT, 6: "Ne sais pas", 7: "Préfère ne pas répondre", 8: "Refus"}
    variable = VariableMetadata(
        name="item", position=1, storage_type="numeric", value_labels=labels
    )
    values = pd.Series([float(v) for v in [1, 2, 3, 4, 5, 6, 7] * 6])
    # 7 follows 6: not a sentinel by its value, but by its label; 8 is never chosen.
    assert profile_variable(values, variable).suspect_missing_codes == (6, 7)


# --- A "scale" level for labelled grid items is doubtful. ---


def test_the_scale_level_of_labelled_grid_items_is_flagged():
    project = build_project(read_database(EXAMPLES / "travail-t2_surveymonkey.sav"))
    likert = project.variable("q0003_0001")
    assert "measure_level_doubtful" in likert.profile.flags
    assert likert.file.measure_level == "scale"  # flagged, not changed
    assert any("Niveau de mesure « échelle » douteux" in a for a in entry_anomalies(likert))
    nominal = project.variable("q0004_0001")  # a grid declared nominal
    assert "measure_level_doubtful" not in nominal.profile.flags
    assert "measure_level_doubtful" not in project.variable("q0001").profile.flags  # no group


def test_the_codebook_says_a_code_is_suspect_by_its_label():
    project = build_project(read_database(EXAMPLES / "travail-t2_surveymonkey.sav"))
    found = entry_anomalies(project.variable("q0004_0001"))
    assert "Code 6 (« Ne sais pas ») probablement manquant, non déclaré" in found
    assert "Code 7 (« Préfère ne pas répondre ») probablement manquant, non déclaré" in found
