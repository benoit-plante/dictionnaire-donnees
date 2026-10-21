"""v0.21, step 2 (D-172): format 0.12.0 — the conditions, the random order, the attention
checks, a variable's condition, the codes of the blanks and the "attention" rule; a 0.11.0
project reads as it is, with the same codebook, the same fingerprints and its publications
and kept review points untouched; a 0.12.0 file is newer for the 0.20.2."""

import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

import projet_concu
from ddict import design, design_compare, design_points
from ddict.export import render_markdown
from ddict.project import SCHEMA_VERSION, dumps, fingerprint, load_project, save_project, store
from ddict.project.model import (
    AttentionCheck,
    AttentionRule,
    BlankCodes,
    Condition,
    Question,
    Term,
    TrackedValue,
)
from ddict.project.store import ProjectNewer

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "tests" / "reference" / "etude-sommeil.dd.json"
DAY = "2026-10-20"


def _as_0_11(data: dict) -> dict:
    """A 0.12.0 project's JSON as the 0.20.2 wrote it: without the fields of 0.12.0."""
    data["schema_version"] = "0.11.0"
    data["settings"].pop("blank_codes")
    for entry in data["variables"]:
        entry.pop("asked_if")
    found = data.get("questionnaire")
    questionnaires = [found] if found else []
    if data.get("design"):
        questionnaires += [p["questionnaire"] for p in data["design"]["publications"]]
    for questionnaire in questionnaires:
        for section in questionnaire["sections"]:
            section.pop("condition"), section.pop("shuffle")
        for question in questionnaire["questions"]:
            question.pop("condition"), question.pop("shuffle"), question.pop("attention")
            for row in question["rows"]:
                row.pop("attention")
    return data


def _write_old(project, path: Path) -> Path:
    data = _as_0_11(json.loads(dumps(project)))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# --- The version. ---


def test_the_new_fields_are_written(tmp_path):
    assert SCHEMA_VERSION == "0.12.0"
    project = load_project(REFERENCE)
    data = json.loads(dumps(project))
    assert data["schema_version"] == "0.12.0"
    assert data["settings"]["blank_codes"] == {"not_applicable": None, "missing": None}
    assert all(entry["asked_if"] is None for entry in data["variables"])


def test_a_0_11_0_project_reads_as_it_is(tmp_path):
    reference = load_project(REFERENCE)
    old = load_project(_write_old(reference, tmp_path / "ancien.dd.json"))
    assert old.schema_version == "0.12.0"
    assert dumps(old) == dumps(reference)
    assert fingerprint.fingerprint(old) == fingerprint.fingerprint(reference)
    assert render_markdown(old) == render_markdown(reference)


def test_a_0_12_0_project_is_newer_for_the_tool_before(tmp_path, monkeypatch):
    path = tmp_path / "projet.dd.json"
    save_project(load_project(REFERENCE), path)
    monkeypatch.setattr(store, "SCHEMA_VERSION", "0.11.0")  # the reader of the 0.20.2
    with pytest.raises(ProjectNewer):
        load_project(path)


def test_a_full_0_12_0_project_saves_byte_for_byte(tmp_path):
    project = projet_concu.project()
    q1, q2 = project.questionnaire.questions[:2]
    q2.condition = Condition(terms=[Term(target=q1.question_id, operator="eq", value="1")])
    project.questionnaire.sections[1].shuffle = True
    project.settings.blank_codes = BlankCodes(not_applicable=-8, missing=-9)
    project.variables[0].asked_if = TrackedValue[list[Condition]](
        value=[Condition(combine="any", terms=[Term(target="x", operator="answered")])],
        origin="human",
    )
    project.exclusions.rules.append(
        AttentionRule(
            id="E1",
            checks=[AttentionCheck(variable=project.variables[0].name, correct=["1"])],
            empty="ignored",
            reason="Item de contrôle échoué",
        )
    )
    first, second = tmp_path / "a.dd.json", tmp_path / "b.dd.json"
    save_project(project, first)
    again = load_project(first)
    assert again == project
    save_project(again, second)
    assert first.read_bytes() == second.read_bytes()


# --- The designed questionnaire keeps its fingerprints (D-172). ---


def test_a_designed_questionnaire_keeps_its_fingerprint_and_publications(tmp_path):
    project = projet_concu.project()
    design_compare.mark_sent(project, "limesurvey", DAY)
    sealed = project.questionnaire.sha256
    old = load_project(_write_old(project, tmp_path / "concu.dd.json"))
    assert design.content_fingerprint(old.questionnaire) == sealed
    assert old.design.publications[0].fingerprint == sealed
    assert design_compare.warnings(old) == []
    # A change, then its undoing: the fingerprint comes back, no publication is "changed".
    title = old.questionnaire.sections[0].title
    design.modify_section(old, "S1", "Autre titre")
    assert design_compare.warnings(old) != []
    design.modify_section(old, "S1", title)
    assert old.questionnaire.sha256 == sealed
    assert design_compare.warnings(old) == []


def test_kept_review_points_keep_their_fingerprint():
    project = projet_concu.project()
    for question in project.questionnaire.questions:
        before = json.loads(json.dumps(question.model_dump(mode="json")))
        for key in ("condition", "shuffle", "attention"):
            before.pop(key)
        for row in before["rows"]:
            row.pop("attention")
        text = json.dumps(before, sort_keys=True, ensure_ascii=False)  # the 0.20.2's formula
        assert design_points.fingerprint(question) == hashlib.sha256(text.encode()).hexdigest()


def test_a_filled_field_changes_the_fingerprint():
    project = projet_concu.project()
    found = project.questionnaire
    sealed = design.content_fingerprint(found)
    grid = next(q for q in found.questions if q.kind == "grid")
    grid.shuffle = True
    assert design.content_fingerprint(found) != sealed
    grid.shuffle = False
    assert design.content_fingerprint(found) == sealed
    grid.rows[0].attention = ["2"]
    assert design.content_fingerprint(found) != sealed
    grid.rows[0].attention = None
    found.sections[0].condition = Condition(terms=[Term(target="Q1", operator="answered")])
    assert design.content_fingerprint(found) != sealed


# --- The codebook's fingerprint (D-172). ---


def test_a_variable_condition_counts_once_accepted():
    project = load_project(REFERENCE)
    before = fingerprint.fingerprint(project)
    entry = project.variables[3]
    condition = Condition(terms=[Term(target=project.variables[2].name, operator="answered")])
    entry.asked_if = TrackedValue[list[Condition]](
        value=[condition], origin="questionnaire", status="proposed"
    )
    assert fingerprint.fingerprint(project) == before  # read in a .lss, waiting
    entry.asked_if = TrackedValue[list[Condition]](value=[condition], origin="human")
    typed = fingerprint.fingerprint(project)
    assert typed != before
    entry.asked_if = None
    assert fingerprint.fingerprint(project) == before


def test_the_blank_codes_count_only_once_chosen():
    project = load_project(REFERENCE)
    before = fingerprint.fingerprint(project)
    project.settings.blank_codes = BlankCodes(not_applicable=-8)
    assert fingerprint.fingerprint(project) != before
    project.settings.blank_codes = BlankCodes()
    assert fingerprint.fingerprint(project) == before


# --- The models refuse what has no meaning. ---


@pytest.mark.parametrize(
    "fields",
    [
        {"operator": "eq"},  # one value
        {"operator": "eq", "value": ["1"]},
        {"operator": "in", "value": []},  # a list
        {"operator": "not_in", "value": "1"},
        {"operator": "checked", "value": "Y"},  # none
        {"operator": "answered", "value": "1"},
        {"operator": "between", "value": "1"},  # unknown
        {"operator": "eq", "value": "1", "target": " "},  # no target
    ],
)
def test_a_term_without_meaning_is_refused(fields):
    with pytest.raises(ValidationError):
        Term(**{"target": "Q3", **fields})


def test_a_condition_has_one_to_ten_terms():
    term = Term(target="Q3", operator="answered")
    with pytest.raises(ValidationError):
        Condition(terms=[])
    with pytest.raises(ValidationError):
        Condition(terms=[term] * 11)
    with pytest.raises(ValidationError):
        Condition(combine="xor", terms=[term])
    assert Condition(terms=[term] * 10).combine == "all"


def test_random_order_and_attention_where_they_mean_something():
    with pytest.raises(ValidationError):
        Question(question_id="Q1", text="Âge", kind="open", answer="number", shuffle=True)
    with pytest.raises(ValidationError):
        Question(question_id="Q1", text="Grille", kind="grid", attention=["1"])
    with pytest.raises(ValidationError):
        Question(question_id="Q1", text="Choix", kind="single", attention=[])
    assert Question(question_id="Q1", text="Choix", kind="single", attention=["1"], shuffle=True)


def test_two_codes_for_the_blanks():
    with pytest.raises(ValidationError):
        BlankCodes(not_applicable=-9, missing=-9)
    assert BlankCodes(not_applicable=-8, missing=-9).missing == -9


def test_an_attention_rule_counts_what_it_can():
    check = AttentionCheck(variable="ctrl1", correct=[4])
    with pytest.raises(ValidationError):
        AttentionRule(id="E1", checks=[check], min_failed=2, empty="failed", reason="r")
    with pytest.raises(ValidationError):
        AttentionRule(id="E1", checks=[check, check], empty="failed", reason="r")
    with pytest.raises(ValidationError):
        AttentionRule(id="E1", checks=[check], reason="r")  # the empty item: no default
    with pytest.raises(ValidationError):
        AttentionCheck(variable="ctrl1", correct=[])
