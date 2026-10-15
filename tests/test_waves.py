"""v0.7, step 7: the names of an earlier wave, taken again (D-052)."""

import json
from pathlib import Path

import pytest

from ddict import i18n, naming, waves
from ddict.cli import main
from ddict.io import read_database
from ddict.project import build_project, save_project
from ddict.project.model import TrackedValue
from ddict.workflow import rename

EXAMPLES = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"
KEY = json.loads((EXAMPLES / "corrige-surveymonkey.json").read_text(encoding="utf-8"))
NOW = "2026-10-15T12:00:00"
EXPECTED = KEY["waves"]["t2"]["names"]
BETWEEN = KEY["between_waves"]


@pytest.fixture(scope="module")
def wave_1(tmp_path_factory):
    """Wave 1 as the team left it: renamed, its names and prefixes accepted."""
    project = build_project(read_database(EXAMPLES / KEY["waves"]["t1"]["sav"]))
    naming.set_wave(project, "t1")
    for entry in project.variables:
        value = KEY["waves"]["t1"]["names"][entry.name]
        entry.new_name = TrackedValue[str](value=value, origin="human", updated_at=NOW)
    for group in project.groups:
        prefix = KEY["waves"]["t1"]["prefixes"].get(group.members.value[0][:5])
        if prefix:
            group.name_prefix = TrackedValue[str](value=prefix, origin="human")
    folder = tmp_path_factory.mktemp("vague-1")
    save_project(project, folder / "travail-t1.dd.json")
    waves.write_name_table(project, folder / "travail-t1-noms.csv")
    return folder


def _wave_2():
    return build_project(read_database(EXAMPLES / KEY["waves"]["t2"]["sav"]))


def _renamed(reference: Path):
    project = _wave_2()
    report = rename(project, suffix="_t2", reference=reference)
    return project, report


@pytest.mark.parametrize("source", ["project", "documented_copy"])
def test_the_names_of_wave_1_are_taken_again(wave_1, source):
    reference = (
        wave_1 / "travail-t1.dd.json"
        if source == "project"
        else EXAMPLES / "travail-t1-documente.sav"
    )
    project, report = _renamed(reference)
    assert report.source == source
    found = {e.name: e.new_name.value for e in project.variables}
    paired = set(BETWEEN["pairs_t2_to_t1"])
    assert {n: found[n] for n in paired} == {n: EXPECTED[n] for n in paired}
    assert all(project.variable(n).new_name.origin == "reference" for n in paired)
    # The item after the removed one keeps its number of wave 1: eft_11, not eft_10.
    assert found["q0003_0010"] == "eft_11_t2"
    # The differences between the waves.
    assert report.added == BETWEEN["added"]
    assert report.removed == ["eft_10_t1"]
    assert report.value_labels_changed == BETWEEN["value_labels_changed"]
    assert report.candidates == {} and report.fragile == 0
    assert report.label_changes["q0007"] == [(4, "Plus de deux", "Trois ou plus")]
    # The prefixes of the earlier grids, proposed for their groups.
    prefixes = {g.group_id: g.name_prefix for g in project.groups if g.name_prefix.value}
    assert {k: v.value for k, v in prefixes.items()} == {"G1": "eft", "G2": "milieu"}
    assert all(v.origin == "reference" and v.status == "proposed" for v in prefixes.values())


def test_why_a_match(wave_1):
    _project, report = _renamed(wave_1 / "travail-t1.dd.json")
    reasons = {m.variable: m.reasons for m in report.matches}
    assert reasons["date_created"] == ("same_platform_variable",)
    assert "same_label" in reasons["q0003_0001"] and "same_value_labels" in reasons["q0003_0001"]
    # Every "other" text has the same label: its question tells which.
    assert "same_question" in reasons["q0005_other"]


def test_a_table_of_names_never_proposes_a_shifted_name(wave_1):
    project, report = _renamed(wave_1 / "travail-t1-noms.csv")
    assert report.source == "table"
    from_table = [e for e in project.variables if e.new_name.origin == "reference"]
    # The question added in wave 2 shifts the numbering: from it on, no original name is
    # trusted; only the platform variables and the first question are matched.
    assert {e.name for e in from_table} == {
        *KEY["waves"]["t2"]["platform_variables"],
        "q0001",
    }
    assert all(e.new_name.value == EXPECTED[e.name] for e in from_table)
    assert report.fragile == 1  # q0001, by its original name alone
    text = waves.report_markdown(project, report)
    assert "1 appariements reposent sur le seul nom d'origine" in text


def test_the_committed_table_reads(wave_1):
    rows = waves.read_name_table(EXAMPLES / "travail-t1-correspondance.csv")
    assert rows[0] == ("CollectorNm", "nom_collecteur_t1")
    assert len(rows) == 55
    assert waves.read_name_table(wave_1 / "travail-t1-noms.csv") == rows


@pytest.mark.parametrize(
    "text",
    [
        "nom_origine;nouveau_nom\nq0001;secteur\n",
        "original_name,new_name\nq0001,secteur\n",
        "﻿nom_origine,nouveau_nom\r\nq0001,secteur\r\n",
    ],
)
def test_forms_of_the_table(tmp_path, text):
    path = tmp_path / "noms.csv"
    path.write_text(text, encoding="utf-8", newline="")
    assert waves.read_name_table(path) == [("q0001", "secteur")]


@pytest.mark.parametrize("text", ["a,b\nq0001,secteur\n", "nom_origine,nouveau_nom\n", ""])
def test_a_bad_table_is_refused(tmp_path, text):
    path = tmp_path / "noms.csv"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(waves.ReferenceError):
        waves.read_name_table(path)


def test_wave_marks():
    assert waves._mark(["a_t1", "b_t1", "c_t1", "d"]) == (None, "suffix")  # 3 of 4: not most
    assert waves._mark(["a_t1", "b_t1", "c_t1", "d_t1", "e"]) == ("t1", "suffix")
    assert waves._mark(["t3_a", "t3_b"]) == ("t3", "prefix")
    assert waves.without_mark("eft_1_t1", "t1", "suffix") == "eft_1"
    assert waves.without_mark("t1_eft_1", "t1", "prefix") == "eft_1"
    assert waves.without_mark("eft_1", None, "suffix") == "eft_1"


def test_a_decision_is_never_replaced(wave_1):
    project = _wave_2()
    naming.propose(project)
    naming.decide(project, "q0001", "correct", value="domaine", now=NOW)
    rename(project, suffix="_t2", reference=wave_1 / "travail-t1.dd.json")
    assert project.variable("q0001").new_name.value == "domaine"
    assert project.variable("q0006").new_name.value == "formation_sst_t2"


def test_two_variables_as_good_go_to_a_person(wave_1):
    project = _wave_2()
    # Two open questions with the same words: neither gets the earlier name alone.
    project.variable("q0011").file.label = project.variable("q0009").file.label
    report = rename(project, suffix="_t2", reference=wave_1 / "travail-t1.dd.json")
    assert {"q0009", "q0011"} <= set(report.candidates)
    assert report.candidates["q0009"][0].earlier == "situation_danger_t1"
    assert project.variable("q0009").new_name.origin != "reference"


def test_the_report_in_english(wave_1):
    project, report = _renamed(wave_1 / "travail-t1.dd.json")
    with i18n.using("en"):
        text = waves.report_markdown(project, report)
    assert text.startswith("# Differences between the waves")
    assert '4: "Plus de deux" → "Trois ou plus"' in text
    assert "same label" in text


def test_rename_command_with_a_reference(wave_1, tmp_path, capsys):
    path = tmp_path / "travail-t2.dd.json"
    save_project(_wave_2(), path)
    reference = wave_1 / "travail-t1.dd.json"
    assert main(["renommer", str(path), "--suffixe", "_t2", "--reference", str(reference)]) == 0
    out = capsys.readouterr().out
    assert "54 variables appariées, 1 ajoutées" in out
    report = tmp_path / "travail-t2-ecarts-vagues.md"
    assert report.is_file() and "eft_10_t1" in report.read_text(encoding="utf-8")
    bad = tmp_path / "rien.txt"
    bad.write_text("x", encoding="utf-8")
    assert main(["rename", str(path), "--reference", str(bad)]) == 2
    assert "Impossible de lire la vague précédente" in capsys.readouterr().err
