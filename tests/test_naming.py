"""v0.7, step 6: new names proposed by the rules and decided by a person (D-048 to D-050)."""

import json
from pathlib import Path

import pytest

from ddict import naming
from ddict.cli import main
from ddict.io import read_database
from ddict.project import build_project, load_project, save_project
from ddict.project.decisions import is_accepted
from ddict.project.model import TrackedValue
from ddict.workflow import add_questionnaire, rename

EXAMPLES = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"
KEY = json.loads((EXAMPLES / "corrige-surveymonkey.json").read_text(encoding="utf-8"))
NOW = "2026-10-15T12:00:00"


def _wave(wave: str):
    return build_project(read_database(EXAMPLES / KEY["waves"][wave]["sav"]))


def _give_prefixes_and_stems(project, wave: str) -> None:
    """What a person would give: the prefixes of the grids, the stems of the questions."""
    expected = KEY["waves"][wave]
    for group in project.groups:
        rank = group.members.value[0][:5]  # "q0003"
        if rank in expected["prefixes"]:
            naming.set_prefix(project, group.group_id, expected["prefixes"][rank], now=NOW)
    for key, stem in expected["stems"].items():
        naming.decide_stem(project, key, "correct", value=stem, now=NOW)


# --- The rules. ---


def test_wave_1_gets_the_expected_names():
    project = _wave("t1")
    naming.set_wave(project, "t1")
    _give_prefixes_and_stems(project, "t1")
    naming.propose(project)
    found = {e.name: e.new_name.value for e in project.variables}
    assert found == KEY["waves"]["t1"]["names"]
    assert all(e.new_name.origin == "rule" for e in project.variables)
    assert naming.summary(project) == {"proposed": 55, "accepted": 0, "to_name": 0, "conflicts": 0}


def test_what_the_rules_propose_alone():
    project = _wave("t2")
    naming.propose(project)
    names = {e.name: e.new_name.value for e in project.variables}
    # Platform variables: their fixed names (D-050).
    assert names["respondent_id"] == "respondent_id"
    assert names["date_created"] == "date_debut"
    assert names["last_name"] == "nom_famille"
    assert names["custom_1"] == "donnees_personnalisees_1"
    # Stems from the words of the questions, small words and question words aside.
    stems = {s.key: s.stem.value for s in project.stems}
    assert stems["q0001"] == "secteur"
    assert stems["q0008"] == "consignes_securite"
    assert stems["q0011"] == "commentaires"
    assert all(s.stem.origin == "rule" and s.stem.status == "proposed" for s in project.stems)
    assert names["q0008_0002"] == "consignes_securite_2"
    assert names["q0008_other"] == "consignes_securite_autre_txt"
    # Grid items wait for a person to give their group's prefix; "id" has no usable word.
    assert names["q0003_0001"] is None and names["q0012"] is None
    assert set(naming.to_name(project)) == {
        *(f"q0003_{k:04d}" for k in range(1, 13)),
        *(f"q0004_{k:04d}" for k in range(1, 6)),
        "q0012",
    }


def test_names_in_english_for_a_study_in_english():
    project = _wave("t2")
    project.settings.language = "en"
    naming.propose(project)
    assert project.variable("date_created").new_name.value == "start_date"
    assert project.variable("q0005_other").new_name.value.endswith("_other_txt")


def test_the_wave_mark_as_a_suffix_or_a_prefix():
    project = _wave("t2")
    rename(project, suffix="_t2")
    assert project.variable("respondent_id").new_name.value == "respondent_id_t2"
    rename(project, prefix="t2_")
    assert project.variable("respondent_id").new_name.value == "t2_respondent_id"
    assert project.settings.naming.position == "prefix"


def test_rank_in_the_group_without_a_platform():
    project = build_project(read_database(EXAMPLES / "etude-sommeil.sav"))
    group = next(g for g in project.groups if "anx1" in g.members.value)
    naming.set_prefix(project, group.group_id, "efa", now=NOW)
    naming.propose(project)
    members = group.members.value
    assert [project.variable(m).new_name.value for m in members] == [
        f"efa_{k}" for k in range(1, len(members) + 1)
    ]


def test_stems_from_accepted_links_without_a_platform():
    project = build_project(read_database(EXAMPLES / "etude-sommeil.sav"))
    add_questionnaire(project, EXAMPLES / "questionnaire-sommeil.txt")
    q3 = next(q for q in project.questionnaire.questions if q.text.startswith("Quel âge"))
    project.variable("age").question = TrackedValue[str](value=q3.question_id, origin="human")
    naming.propose(project)
    assert project.variable("age").new_name.value == "age"


def test_two_questions_with_the_same_words_get_two_stems():
    project = _wave("t2")
    project.variable("q0011").file.label = project.variable("q0009").file.label
    naming.propose(project)
    stems = {s.key: s.stem.value for s in project.stems}
    assert stems["q0011"] == stems["q0009"] + "_2"


# --- Decisions. ---


def test_proposals_never_override_a_decision():
    project = _wave("t2")
    naming.propose(project)
    naming.decide(project, "q0001", "accept", now=NOW)
    naming.decide(project, "q0002", "correct", value="anciennete", now=NOW)
    naming.decide(project, "q0006", "reject", now=NOW)
    naming.decide(project, "q0012", "correct", value="id_participant", now=NOW)  # written
    naming.decide_stem(project, "q0001", "correct", value="domaine", now=NOW)
    naming.decide_stem(project, "q0007", "correct", value="nb_pauses", now=NOW)
    naming.propose(project)
    assert project.variable("q0001").new_name.value == "secteur"  # accepted: kept
    assert project.variable("q0002").new_name.value == "anciennete"
    assert project.variable("q0006").new_name.status == "rejected"
    assert project.variable("q0012").new_name.value == "id_participant"
    assert project.variable("q0012").new_name.origin == "human"
    assert project.variable("q0007").new_name.value == "nb_pauses"  # proposed: follows
    assert naming.final_name(project.variable("q0001")) == "secteur"
    assert naming.final_name(project.variable("q0007")) == "q0007"  # only a proposal
    assert naming.summary(project)["accepted"] == 3


def test_a_proposal_withdrawn_when_its_rule_goes():
    project = _wave("t2")
    group = project.groups[0]
    naming.set_prefix(project, group.group_id, "eft", now=NOW)
    naming.propose(project)
    assert project.variable("q0003_0001").new_name.value == "eft_1"
    naming.set_prefix(project, group.group_id, "", now=NOW)
    naming.propose(project)
    assert project.variable("q0003_0001").new_name.value is None


# --- Validity. ---


@pytest.mark.parametrize(
    ("name", "problem"),
    [
        ("Age", "style"),
        ("âge", "style"),
        ("1er_item", "style"),
        ("item_", "style"),
        ("item__1", "style"),
        ("un nom", "style"),
        ("x" * 33, "length"),
        ("to", "reserved"),
        ("WITH", "style"),  # upper case first; lower case "with" is reserved
        ("with", "reserved"),
        ("q0002", "original_name"),  # the original name of another variable
        ("Q0002", "style"),
    ],
)
def test_names_the_rules_refuse(name, problem):
    project = _wave("t2")
    assert problem in naming.problems(project, "q0001", name)


def test_a_name_used_by_another_is_refused_case_aside():
    project = _wave("t2")
    naming.propose(project)
    assert naming.problems(project, "q0002", "secteur") == ["duplicate"]
    assert naming.problems(project, "q0001", "q0001") == []  # its own original name
    with pytest.raises(naming.NamingError) as error:
        naming.decide(project, "q0002", "correct", value="secteur", now=NOW)
    assert error.value.problems == ["duplicate"]


def test_the_maximum_length_includes_the_wave_mark():
    project = _wave("t2")
    project.settings.naming.max_length = 12
    naming.set_wave(project, "t2")
    naming.propose(project)
    # "consignes_securite_1_t2" is too long: not proposed, the variable stays to name.
    assert project.variable("q0008_0001").new_name.value is None
    assert project.variable("q0001").new_name.value == "secteur_t2"


def test_a_conflict_is_found():
    project = _wave("t2")
    naming.propose(project)
    # Accepted in a former version with a name now taken: the conflict is shown.
    project.variable("q0002").new_name = TrackedValue[str](
        value="secteur", origin="human", updated_at=NOW
    )
    assert set(naming.conflicts(project)) == {"q0001", "q0002"}
    assert naming.summary(project)["conflicts"] == 2


@pytest.mark.parametrize("prefix", ["K6", "k 6", "to"])
def test_a_prefix_follows_the_rules(prefix):
    project = _wave("t2")
    with pytest.raises(naming.NamingError):
        naming.set_prefix(project, project.groups[0].group_id, prefix, now=NOW)


def test_slug():
    assert naming.slug("Âge (années)") == "age_annees"
    assert naming.slug("  Santé & sécurité  ") == "sante_securite"


# --- The project file and the command. ---


def test_names_are_kept_in_the_project(tmp_path):
    project = _wave("t2")
    naming.set_prefix(project, project.groups[0].group_id, "eft", now=NOW)
    rename(project, suffix="_t2")
    naming.decide(project, "q0001", "accept", now=NOW)
    path = tmp_path / "projet.dd.json"
    save_project(project, path)
    again = load_project(path)
    assert again == project
    assert is_accepted(again.variable("q0001").new_name)
    assert again.groups[0].name_prefix.value == "eft"
    assert again.settings.naming.wave == "t2"


def test_rename_command(tmp_path, capsys):
    project = _wave("t2")
    path = tmp_path / "projet.dd.json"
    save_project(project, path)
    assert main(["renommer", str(path), "--suffixe", "_t2"]) == 0
    out = capsys.readouterr().out
    assert "37 noms proposés, 0 acceptés, 18 variables à nommer." in out
    assert "Marque de vague : _t2" in out
    assert load_project(path).variable("q0001").new_name.value == "secteur_t2"
    assert main(["rename", str(path), "--prefix", "t2_"]) == 0
    assert load_project(path).variable("q0001").new_name.value == "t2_secteur"
    assert main(["renommer", str(path), "--suffixe", "t 2!"]) == 0  # slugged to "t_2"
