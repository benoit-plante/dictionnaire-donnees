"""v0.4, step 1: the second fictional database, a survey of families, and its answer key."""

import hashlib
from pathlib import Path

import pytest

from ddict import glossary
from ddict.io import read_database
from ddict.project import build_project
from ddict.questionnaire import load_questionnaire

ROOT = Path(__file__).resolve().parent.parent
FILES = ["enquete-familles.csv", "questionnaire-familles.txt", "questionnaire-familles.pdf"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_two_runs_write_identical_files(family_generator, family_files, tmp_path):
    again = {p.name: p for p in family_generator.write_all(tmp_path)}
    assert sorted(again) == sorted(FILES)
    for name in FILES:
        assert _sha(again[name]) == _sha(family_files[name]), name


def test_committed_examples_match_the_generator(family_files):
    for name in FILES:
        committed = ROOT / "exemples" / "bases-fictives" / name
        assert _sha(committed) == _sha(family_files[name]), (
            f"{name} differs: run uv run python scripts/generer_enquete_familles.py"
        )


@pytest.fixture(scope="module")
def project(family_files):
    project = build_project(read_database(family_files["enquete-familles.csv"]))
    project.questionnaire = load_questionnaire(family_files["questionnaire-familles.pdf"])
    return project


def test_the_data(family_generator, project):
    assert (len(project.variables), project.source.n_rows) == (30, 150)
    assert [e.name for e in project.variables] == family_generator.COLUMN_ORDER
    assert not any(e.file.label or e.file.value_labels for e in project.variables)  # a CSV
    assert project.variable("soutien_partenaire").file.missing_tokens[0].token == "NA"
    classes = {e.name: e.privacy.privacy_class.value for e in project.variables}
    for name in family_generator.TRAPS["likely_identifier"]:
        assert classes[name] == "likely_identifier"
    assert classes["commentaire"] == "free_text"


def test_follow_ups_are_consistent(family_generator):
    df = family_generator.build_dataset()
    for parent, children in family_generator.TRAPS["follow_up_checkboxes"].items():
        no = df[parent] == 2
        assert df.loc[no, children].isna().all().all(), parent  # "Si oui" only
        assert df.loc[~no, children].eq(1).any().all(), parent  # every option is ticked
    items = family_generator.STRESS_ITEMS
    assert (df[items].sum(axis=1) == df["stress_total"]).all()
    assert set(df[items].stack().unique()) <= {0, 1, 2, 3, 4}


@pytest.mark.parametrize("name", ["questionnaire-familles.pdf", "questionnaire-familles.txt"])
def test_the_questionnaire(family_generator, family_files, name):
    questionnaire = load_questionnaire(family_files[name])
    questions = questionnaire.questions
    assert len(questions) == 18
    key = family_generator.answer_key()
    for variable, (page, rank, row) in key.items():
        question = questions[rank - 1]
        assert question.page in (page, None), variable  # a text file has no pages
        if row is not None:
            parts = question.rows if question.kind == "grid" else question.options
            assert len(parts) >= row, variable
    traps = family_generator.TRAPS
    repeated = [q for q in questions if q.text == traps["repeated_question"]["text"]]
    assert len(repeated) == 3
    assert [q.kind for q in questions if q.text.startswith("Si oui")] == ["checkbox", "checkbox"]
    found = {term: meaning for term, meaning, _page in glossary.find_definitions(questionnaire)}
    assert found == traps["defined_acronyms"]
    text = " ".join(q.text for q in questions)
    assert traps["consent_page_canary"] not in text  # the consent page is no question


def test_every_variable_is_in_the_key_or_listed_as_not_asked(family_generator):
    key = set(family_generator.answer_key())
    not_asked = set(family_generator.TRAPS["variables_without_question"])
    assert key | not_asked == set(family_generator.COLUMN_ORDER)
    assert not key & not_asked


def test_true_value_labels(family_generator, project):
    """langue_maison was recoded alphabetically: labels in option order would be wrong."""
    true = family_generator.TRUE_VALUE_LABELS["langue_maison"]
    options = ["Français", "Anglais", "Autre"]
    assert [true[code] for code in sorted(true)] != options
    observed = {o.code for o in project.variable("langue_maison").profile.observed_values}
    assert observed == set(true)
