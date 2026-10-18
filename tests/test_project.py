"""Step 6: the project file — provenance, decisions, reproducible save and load."""

import json
import os

import pytest
from pydantic import ValidationError

from conftest import ROOT
from ddict.io import read_csv, read_sav
from ddict.project import (
    DecisionError,
    ProjectError,
    TrackedValue,
    build_project,
    correct,
    dumps,
    enter,
    is_accepted,
    load_project,
    reject,
    save_project,
    source_differences,
    validate,
)
from ddict.project.model import Group, TheoreticalRange, Threshold, VariableEntry

# The reference project file of the fictional base. It lives with the tests, not in exemples/:
# there it made "Créer le projet" answer "a project exists already" (0.3.0 trial).
GOLDEN = ROOT / "tests" / "reference" / "etude-sommeil.dd.json"
NOW = "2026-10-13T14:00:00"


@pytest.fixture(scope="module")
def data(fictional_files):
    return read_sav(fictional_files["etude-sommeil.sav"])


@pytest.fixture(scope="module")
def project(data):
    return build_project(data)


def test_matches_the_reference_file(project):
    """The reference shows the format; regenerate with UPDATE_GOLDEN=1 after a wanted change."""
    text = dumps(project)
    if os.environ.get("UPDATE_GOLDEN"):
        GOLDEN.write_text(text, encoding="utf-8", newline="\n")
    assert GOLDEN.read_text(encoding="utf-8") == text


def test_save_load_save_is_byte_identical(project, tmp_path):
    first = tmp_path / "projet.dd.json"
    second = tmp_path / "copie.dd.json"
    save_project(project, first)
    reloaded = load_project(first)
    assert reloaded == project
    save_project(reloaded, second)
    assert first.read_bytes() == second.read_bytes()
    assert b"\r\n" not in first.read_bytes()
    assert not (tmp_path / "projet.dd.json.tmp").exists()


def test_two_builds_are_identical(data):
    assert dumps(build_project(data)) == dumps(build_project(data))


def test_key_order_follows_the_design(project):
    data = json.loads(dumps(project))
    assert list(data) == [
        "schema_version",
        "source",
        "settings",
        "variables",
        "groups",
        "ai_runs",
        "questionnaire",
        "glossary",
        "stems",  # v0.7: the stems of the new names
        "dataset",  # v0.8: the description of the database
        "exclusions",  # v0.12: the exclusion rules (D-093)
        "plan",  # v0.13: the analysis plan (D-101)
        "recodes",  # v0.15: the recodings (D-120)
    ]
    assert list(data["variables"][0])[:5] == ["name", "position", "file", "profile", "privacy"]


def test_no_canary_and_no_path_in_the_project(project, generator, fictional_files):
    text = dumps(project)
    for canary in generator.CANARIES:
        assert canary not in text
    assert str(fictional_files["etude-sommeil.sav"].parent) not in text
    assert project.source.name == "etude-sommeil.sav"


def test_provenance_of_initial_values(project):
    q1 = project.variable("sommeil_q1")
    assert (q1.label.value, q1.label.origin, q1.label.status) == (
        "Q1 endormissement",
        "file",
        "none",
    )
    q7 = project.variable("sommeil_q7")
    assert (q7.label.value, q7.label.origin) == (None, "human")
    privacy = project.variable("courriel").privacy
    assert (privacy.privacy_class.value, privacy.privacy_class.origin) == (
        "likely_identifier",
        "computed",
    )
    assert project.variable("genre").profile.observed_values[2].count is None


def test_statistics_are_rounded(project):
    mean = project.variable("heures_sommeil").profile.mean
    assert mean == round(mean, 4)


def _ai(value="Libellé proposé"):
    return TrackedValue[str](value=value, origin="ai", status="proposed", ai_run="run-0001")


def test_ai_proposal_lifecycle():
    proposal = _ai()
    assert not is_accepted(proposal)
    assert is_accepted(validate(proposal, now=NOW))
    corrected = correct(proposal, "Mon libellé", now=NOW)
    assert (corrected.value, corrected.proposed_value, corrected.status) == (
        "Mon libellé",
        "Libellé proposé",
        "corrected",
    )
    assert is_accepted(corrected)
    again = correct(corrected, "Autre libellé", now=NOW)
    assert again.proposed_value == "Libellé proposé"
    rejected = reject(proposal, now=NOW)
    assert rejected.status == "rejected" and not is_accepted(rejected)


def test_file_value_can_be_corrected_but_not_rejected():
    from_file = TrackedValue[str](value="Q4 satisf sommeil", origin="file")
    assert is_accepted(from_file)
    corrected = correct(from_file, "Satisfaction à l'égard du sommeil", now=NOW)
    assert corrected.proposed_value == "Q4 satisf sommeil"
    with pytest.raises(DecisionError):
        reject(from_file, now=NOW)


def test_human_entry():
    empty = TrackedValue[str](origin="human")
    assert not is_accepted(empty)
    entered = enter(empty, "heures", now=NOW)
    assert is_accepted(entered) and entered.updated_at == NOW
    with pytest.raises(DecisionError):
        validate(entered, now=NOW)


@pytest.mark.parametrize(
    "fields",
    [
        dict(value="x", origin="ai", status="proposed"),  # no ai_run
        dict(value="x", origin="file", status="proposed"),  # only AI proposes
        dict(value="x", origin="human", ai_run="run-1"),  # ai_run on a human value
        dict(value="x", origin="ai", ai_run="run-1"),  # AI value without a status
        dict(value="x", origin="file", status="corrected"),  # original value lost
    ],
)
def test_inconsistent_tracked_values_are_refused(fields):
    with pytest.raises(ValidationError):
        TrackedValue[str](**fields)


@pytest.mark.parametrize("source", ["", "   "])
def test_sourced_fields_need_a_source(source):
    with pytest.raises(ValidationError):
        Threshold(value=14, meaning="Dépression légère", source=source)
    with pytest.raises(ValidationError):
        TheoreticalRange(min=0, max=63, source=source)


def test_sourced_fields_with_a_source_are_kept(project, tmp_path):
    entry = project.variable("sommeil_q1")
    changed = entry.model_copy(
        update={
            "thresholds": [Threshold(value=14, meaning="Seuil fictif", source="Manuel, p. 12")],
            "theoretical_range": TheoreticalRange(min=1, max=5, source="Questionnaire"),
        }
    )
    variables = [changed if v.name == entry.name else v for v in project.variables]
    updated = project.model_copy(update={"variables": variables})
    path = tmp_path / "p.dd.json"
    save_project(updated, path)
    reloaded = load_project(path).variable("sommeil_q1")
    assert reloaded.thresholds[0].source == "Manuel, p. 12"


def test_ai_cannot_fill_human_only_fields():
    """Thresholds, ranges, references and instrument names have no origin: humans only."""
    for model in (VariableEntry, Group):
        for name in ("thresholds", "theoretical_range", "instrument_name", "references"):
            if name in model.model_fields:
                assert "origin" not in str(model.model_fields[name].annotation)


def test_unknown_fields_are_refused(project, tmp_path):
    data = json.loads(dumps(project))
    data["variables"][0]["clinical_cutoff"] = 14
    path = tmp_path / "p.dd.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ProjectError, match="not a valid project"):
        load_project(path)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("{", "Cannot read"),
        ('{"schema_version": "9.0.0"}', "unsupported schema version"),
        ("[]", "unsupported schema version"),
    ],
)
def test_unreadable_project_files(tmp_path, content, message):
    path = tmp_path / "p.dd.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ProjectError, match=message):
        load_project(path)


def test_same_database_has_no_differences(project, data):
    assert source_differences(project, data) == []


def test_modified_database_is_detected(project, fictional_files, tmp_path):
    original = fictional_files["etude-sommeil.csv"].read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    shorter = tmp_path / "etude-sommeil.csv"
    shorter.write_text("".join(lines[:-1]), encoding="utf-8", newline="")
    assert source_differences(project, read_csv(shorter)) == ["content", "rows"]
