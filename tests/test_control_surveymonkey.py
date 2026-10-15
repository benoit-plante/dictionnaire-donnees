"""v0.7: the control export, a second fictional SurveyMonkey export in English with kinds of
questions the two real exports did not have (contact information, ranking, slider, text
boxes, a grid with comments, a matrix of drop-down menus).

Measured once with the code of the end of step 10, before any fix (docs/essais/), then
these tests: no false group, no false link, the right identifiers; and the conventions the
tool does not know (names on three levels) left outside the structure.
"""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from ddict import naming
from ddict.io import read_database
from ddict.llm.link import build_link_blocks
from ddict.llm.stems import build_stem_blocks
from ddict.project import build_project
from ddict.questionnaire import link
from ddict.workflow import add_questionnaire

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "exemples" / "bases-fictives"
KEY = json.loads((EXAMPLES / "corrige-controle-surveymonkey.json").read_text(encoding="utf-8"))
FILES = [
    "trajets_surveymonkey.sav",
    "trajets_surveymonkey.xlsx",
    "questionnaire-trajets.txt",
    "corrige-controle-surveymonkey.json",
]


def _generator():
    sys.path.insert(0, str(ROOT / "scripts"))
    path = ROOT / "scripts" / "generer_controle_surveymonkey.py"
    spec = importlib.util.spec_from_file_location("generer_controle_surveymonkey", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_committed_files_match_the_generator(tmp_path):
    written = {p.name: p for p in _generator().write_all(tmp_path)}
    assert sorted(written) == sorted(FILES)
    for name in FILES:
        assert _sha(written[name]) == _sha(EXAMPLES / name), (
            f"{name} differs: run uv run python scripts/generer_controle_surveymonkey.py"
        )


def _groups(project) -> list[dict]:
    return [
        {"kind": g.kind, "members": g.members.value}
        | ({"attached": g.attached} if g.kind == "multiple_response" else {})
        for g in project.groups
    ]


@pytest.fixture(scope="module")
def project():
    return build_project(read_database(EXAMPLES / KEY["sav"]))


def test_only_the_scales_and_the_checkboxes_are_groups(project):
    assert _groups(project) == KEY["groups"]


def test_neither_text_fields_nor_a_ranking_make_a_scale_in_the_excel_export():
    project = build_project(read_database(EXAMPLES / KEY["xlsx"]))
    firsts = [g.members.value[0] for g in project.groups]
    assert "q0003_0001" not in firsts and "q0005_0001" not in firsts
    assert [g.kind for g in project.groups] == ["scale", "multiple_response", "scale"]


def test_contact_information_holds_identifiers(project):
    identifiers = {
        e.name for e in project.variables if e.privacy.privacy_class.value == "likely_identifier"
    }
    assert set(KEY["likely_identifiers"]) <= identifiers
    assert project.variable("q0003_0002").privacy.privacy_class.value != "likely_identifier"


@pytest.mark.parametrize("questionnaire", ["questionnaire_txt", "xlsx"])
def test_the_structural_links(questionnaire):
    project = build_project(read_database(EXAMPLES / KEY["sav"]))
    add_questionnaire(project, EXAMPLES / KEY[questionnaire])
    choices = link.platform_choices(project)
    expected = {n: t for n, t in KEY["links"].items() if t}
    if questionnaire == "xlsx":
        # The header knows the "other" option of a single choice, not its choices: Q2.o1.
        expected["q0002_other"] = "Q2.o1"
    assert {n: choices.get(n) for n in expected} == expected
    # What every structural link points to agrees with the variable's text.
    for name, target_id in choices.items():
        if target_id == link.NO_QUESTION:
            continue
        found = link.target(project.questionnaire, target_id)
        entry = project.variable(name)
        texts = [entry.file.label, *(v.label for v in entry.file.value_labels)]
        if name.endswith("_other"):
            texts = ["Other (please specify)", "Comments"]
        assert any(link.texts_agree(t, found.part or found.question.text) for t in texts), name


def test_an_unknown_convention_stays_outside_the_structure(project):
    # A matrix of drop-down menus, named on three levels: no group, no structural link.
    names = [e.name for e in project.variables if e.name.startswith("q0010_")]
    assert len(names) == 4
    grouped = {m for g in project.groups for m in g.members.value}
    assert not set(names) & grouped
    add_questionnaire(project, EXAMPLES / KEY["questionnaire_txt"])
    choices = link.platform_choices(project)
    assert not set(names) & set(choices)


def test_stems_for_questions_of_several_fields():
    project = build_project(read_database(EXAMPLES / KEY["sav"]))
    add_questionnaire(project, EXAMPLES / KEY["xlsx"])
    naming.propose(project)
    stems = {s.key: s.stem.value for s in project.stems}
    assert stems["q0003"] == "contact_information"
    assert "q0005" in stems and "q0007" in stems  # a ranking, text boxes: a stem each
    assert "q0004" not in stems  # a scale takes a prefix
    assert project.variable("q0005_0002").new_name.value == f"{stems['q0005']}_2"


def test_no_participant_value_leaves(project):
    project = build_project(read_database(EXAMPLES / KEY["sav"]))
    add_questionnaire(project, EXAMPLES / KEY["questionnaire_txt"])
    sent = [b.messages[1]["content"] for b in build_link_blocks(project, size=6)]
    sent += [b.messages[1]["content"] for b in build_stem_blocks(project, size=8)]
    assert KEY["canary"] not in "\n".join(sent)
    # The project keeps the questionnaire's information page (D-012); exports leave it out.
