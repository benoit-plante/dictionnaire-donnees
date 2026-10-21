"""v0.21, step 7 (D-169, § 5.7.2 and 5.7.3 of the plan): the conditions and the random orders
read back from a LimeSurvey structure, `.txt` and `.lss`, by a closed grammar; an expression
outside it refused and listed, never guessed; the three new kinds of difference of a
re-export, and taking them into the project. Fictional only: the files are written by the tool
or by `scripts/generer_limesurvey_fictif.py`, then changed as LimeSurvey would."""

import importlib.util
import sys
from pathlib import Path

import pytest
from lxml import etree

from ddict import design, design_compare, design_limesurvey
from ddict.design import DesignError
from ddict.questionnaire import relevance
from ddict.questionnaire.lss import names, read_limesurvey
from ddict.questionnaire.relevance import Unread, parse
from projet_filtres import project as filtres
from test_limesurvey_conditions import FORMS
from test_skip import famille, term, when

ROOT = Path(__file__).resolve().parent.parent
NOW = "2026-10-21T10:00:00"


def _written(project, folder: Path) -> Path:
    return design_limesurvey.write(project, folder)


def _set_relevance(path: Path, cls: str, name: str, expression: str, column="relevance") -> None:
    """The file as if LimeSurvey had it so: one cell changed."""
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    for n, line in enumerate(lines[1:], start=1):
        cells = line.split("\t")
        if cells[header.index("class")] == cls and cells[header.index("name")].strip('"') == name:
            cells[header.index(column)] = design_limesurvey._cell(expression)
            lines[n] = "\t".join(cells)
            break
    else:
        raise AssertionError(name)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


# --- Each written form read back as it was (§ 5.7.1). ---


@pytest.mark.parametrize(("found", "_written_form"), FORMS)
def test_each_form_read_back(tmp_path, found, _written_form):
    project = famille()
    design.set_condition(project, "Q6", when(found))
    read = read_limesurvey(_written(project, tmp_path))
    mine = design.find(project, "Q6").condition
    assert relevance.canonical(read.questions[5].condition) == relevance.canonical(mine)
    assert design_compare.with_limesurvey(project, read) == []


def test_the_trial_questionnaire_read_back_without_a_difference(tmp_path):
    project = filtres()
    read = read_limesurvey(_written(project, tmp_path))
    assert design_compare.with_limesurvey(project, read) == []
    assert [s.shuffle for s in read.sections] == [False, True, False]
    assert [q.code for q in read.questions if q.shuffle] == ["emploi", "climat", "transport"]
    garde = next(q for q in read.questions if q.code == "garde")
    assert garde.condition == when(term("Q4", "ge", 1), term("Q7", "in", ["1", "2"]), combine="any")
    assert not any(q.to_check for q in read.questions)


# --- Outside the grammar: refused, listed, never guessed. ---

REFUSED = [
    "is_empty(enfants)",  # a function
    '((enfants.NAOK != "" and enfants.NAOK == "1"))',  # brackets in brackets
    "{enfants} == 1",  # a brace
    '(inconnu.NAOK != "" and inconnu.NAOK == "1")',  # an unknown code
    '(enfants.NAOK != "" and enfants.NAOK == "7")',  # not one of its codes
    '(age.NAOK != "" and age.NAOK >= "18")',  # a number between quotes: compared as a text
    '(enfants.NAOK != "" and enfants.NAOK == 1)',  # a code without quotes
    '(enfants.NAOK != "" and enfants.NAOK > "1")',  # a choice compared by order
    '(enfants.NAOK == "1")',  # the empty answer not tested first
    'enfants.NAOK == "1"',  # no brackets
    '(enfants == "1")',  # without .NAOK
    '(transport_2.NAOK != "")',  # an option "answered"
    '(enfants.NAOK == "Y")',  # a choice "ticked"
    '(age.NAOK != "") and (enfants.NAOK != "") or (emploi.NAOK != "")',  # and with or
    '(age.NAOK != "") and',  # cut short
    '(age.NAOK != "" and emploi.NAOK != "")',  # two codes in one term
    '(enfants.NAOK != "" and (enfants.NAOK == "1" and enfants.NAOK == "2"))',
    '(ville.NAOK != "" and ville.NAOK == "Lyon")',  # a text's value
]


@pytest.mark.parametrize("expression", REFUSED)
def test_an_expression_outside_the_grammar_is_refused(tmp_path, expression):
    path = _written(famille(), tmp_path)
    read = read_limesurvey(path)
    with pytest.raises(Unread):
        parse(expression, names(read))
    _set_relevance(path, "Q", "commentaire", expression)
    read = read_limesurvey(path)
    question = next(q for q in read.questions if q.code == "commentaire")
    assert question.condition is None
    assert question.condition_unread == expression
    assert "lss_condition_unread" in question.to_check


def test_always_and_spaces():
    found = names(read_limesurvey_text())
    assert parse("1", found) is None and parse("", found) is None and parse(None, found) is None
    spaced = '( enfants.NAOK!=""  and enfants.NAOK=="1" )'
    assert parse(spaced, found) == when(term("Q3", "eq", "1"))


def read_limesurvey_text():
    import tempfile

    folder = Path(tempfile.mkdtemp())
    return read_limesurvey(_written(famille(), folder))


def test_a_random_order_of_another_value_is_a_point_to_check(tmp_path):
    path = _written(famille(), tmp_path)
    _set_relevance(path, "Q", "emploi", "alphabetical", column="answer_order")
    _set_relevance(path, "Q", "climat", "random", column="random_group")  # one of four
    read = read_limesurvey(path)
    emploi = next(q for q in read.questions if q.code == "emploi")
    assert not emploi.shuffle and "lss_order_unread" in emploi.to_check
    climat = next(q for q in read.questions if q.code == "climat")
    assert "lss_order_unread" in climat.to_check
    assert not read.sections[1].shuffle


# --- The .lss. ---


def _generator():
    script = ROOT / "scripts" / "generer_limesurvey_fictif.py"
    spec = importlib.util.spec_from_file_location("generer_limesurvey_fictif", script)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_an_lss_with_conditions_and_random_orders(tmp_path):
    root = etree.fromstring(_generator().lss_text().encode("utf-8"))
    questions = {r.findtext("title"): r for r in root.iterfind("questions/rows/row")}
    qid = {title: r.findtext("qid") for title, r in questions.items()}

    def relevance_of(title, expression):
        questions[title].find("relevance").text = etree.CDATA(expression)

    relevance_of("profession", '(age.NAOK != "" and age.NAOK >= 18)')
    relevance_of("nuit", '(aides_SQ001.NAOK == "Y")')
    relevance_of("region", "is_empty(genre)")
    groups = list(root.iterfind("groups/rows/row"))
    groups[1].find("grelevance").text = etree.CDATA('(genre.NAOK != "" and genre.NAOK != "9")')
    table = etree.SubElement(root, "question_attributes")
    rows = etree.SubElement(table, "rows")
    attributes = [("region", "answer_order", "random"), ("sommeil", "subquestion_order", "random")]
    second = [
        r.findtext("title")
        for r in questions.values()
        if r.findtext("gid") == groups[1].findtext("gid")
    ]
    attributes += [(title, "random_group", "rg") for title in second]
    for title, attribute, value in attributes:
        row = etree.SubElement(rows, "row")
        for tag, text in (("qid", qid[title]), ("attribute", attribute), ("value", value)):
            etree.SubElement(row, tag).text = text
    path = tmp_path / "fictif.lss"
    path.write_bytes(etree.tostring(root, xml_declaration=True, encoding="UTF-8"))
    read = read_limesurvey(path)
    by_code = {q.code: q for q in read.questions}
    age = by_code["age"].question_id
    assert by_code["profession"].condition == when(term(age, "ge", 18))
    aides = by_code["aides"]
    assert by_code["nuit"].condition == when(term(aides.options[0].option_id, "checked"))
    assert by_code["region"].condition is None
    assert by_code["region"].condition_unread == "is_empty(genre)"
    assert by_code["region"].shuffle and by_code["sommeil"].shuffle
    assert read.sections[1].condition == when(term(by_code["genre"].question_id, "ne", "9"))
    assert read.sections[1].shuffle and not read.sections[0].shuffle


# --- Comparing a re-export (§ 5.7.3). ---


def test_a_condition_changed_in_limesurvey_is_said_and_taken(tmp_path):
    project = famille()
    design.set_condition(project, "Q4", when(term("Q3", "eq", "1")))
    path = _written(project, tmp_path)
    _set_relevance(path, "Q", "nbenfants", '(enfants.NAOK != "" and enfants.NAOK != "2")')
    [difference] = design_compare.with_limesurvey(project, read_limesurvey(path))
    assert (difference.kind, difference.fields) == ("changed", ["condition"])
    assert difference.conditions == (
        "Posée si Q3 (enfants) = 1 (Oui)",
        "Posée si Q3 (enfants) ≠ 2 (Non)",
    )
    design_compare.take(project, difference, now=NOW)
    assert design.find(project, "Q4").condition == when(term("Q3", "ne", "2"))
    assert design_compare.with_limesurvey(project, read_limesurvey(path)) == []


def test_a_condition_removed_in_limesurvey(tmp_path):
    project = famille()
    design.set_condition(project, "Q4", when(term("Q3", "eq", "1")))
    path = _written(project, tmp_path)
    _set_relevance(path, "Q", "nbenfants", "1")
    [difference] = design_compare.with_limesurvey(project, read_limesurvey(path))
    assert difference.conditions == ("Posée si Q3 (enfants) = 1 (Oui)", "Toujours posée")
    design_compare.take(project, difference, now=NOW)
    assert design.find(project, "Q4").condition is None


def test_a_condition_unread_cannot_be_taken(tmp_path):
    project = famille()
    path = _written(project, tmp_path)
    _set_relevance(path, "Q", "nbenfants", "is_empty(enfants)")
    [difference] = design_compare.with_limesurvey(project, read_limesurvey(path))
    assert difference.fields == ["condition_unread"]
    assert difference.conditions == ("Toujours posée", "is_empty(enfants)")
    before = project.model_dump()
    with pytest.raises(DesignError, match="pas de la forme"):
        design_compare.take(project, difference, now=NOW)
    assert project.model_dump() == before


def test_a_random_order_and_a_section_changed_in_limesurvey(tmp_path):
    project = famille()
    path = _written(project, tmp_path)
    _set_relevance(path, "Q", "climat", "random", column="subquestion_order")
    _set_relevance(path, "G", "Votre quartier", '(enfants.NAOK != "" and enfants.NAOK == "1")')
    differences = design_compare.with_limesurvey(project, read_limesurvey(path))
    section = next(d for d in differences if d.kind == "section")
    grid = next(d for d in differences if d.kind == "changed")
    assert section.fields == ["condition"] and section.code == "Votre quartier"
    assert section.conditions == ("Toujours posée", "Posée si Q3 (enfants) = 1 (Oui)")
    assert grid.fields == ["shuffle"]
    for difference in differences:
        design_compare.take(project, difference, now=NOW)
    assert project.questionnaire.sections[1].condition == when(term("Q3", "eq", "1"))
    assert design.find(project, "Q7").shuffle
    assert design_compare.with_limesurvey(project, read_limesurvey(path)) == []


def test_a_condition_on_what_the_project_does_not_have_cannot_be_taken(tmp_path):
    project = famille()
    path = _written(project, tmp_path)
    design.remove_question(project, "Q2")  # "age" gone from the project, not from LimeSurvey
    _set_relevance(path, "Q", "nbenfants", '(age.NAOK != "" and age.NAOK >= 18)')
    differences = design_compare.with_limesurvey(project, read_limesurvey(path))
    changed = next(d for d in differences if d.code == "nbenfants")
    assert "age" in changed.refused
    with pytest.raises(DesignError, match="age"):
        design_compare.take(project, changed, now=NOW)


def test_a_version_sent_and_a_condition_changed_since():
    project = famille()
    design_compare.mark_sent(project, "ethics", "2026-10-21")
    design.set_condition(project, "Q4", when(term("Q3", "eq", "1")))
    design.set_shuffle(project, "Q7", True)
    found = design_compare.since(project.design.publications[0], project)
    assert {d.code: d.fields for d in found} == {"Q4": ["condition"], "Q7": ["shuffle"]}


@pytest.mark.allow_hosts(["127.0.0.1"])
def test_the_page_shows_and_takes_a_condition(tmp_path):
    from streamlit.testing.v1 import AppTest

    from ddict.project import load_project, save_project

    project = famille()
    design.set_condition(project, "Q4", when(term("Q3", "eq", "1")))
    path = tmp_path / "familles.dd.json"
    save_project(project, path)
    reexport = _written(project, tmp_path)
    _set_relevance(reexport, "Q", "nbenfants", '(enfants.NAOK != "" and enfants.NAOK != "2")')
    _set_relevance(reexport, "Q", "emploi", "is_empty(enfants)")
    _set_relevance(reexport, "G", "Votre quartier", '(age.NAOK != "" and age.NAOK >= 18)')
    app = AppTest.from_file(str(ROOT / "src" / "ddict" / "review" / "app.py"), default_timeout=60)
    app.session_state["project_path"] = str(path)
    app.session_state["mode"] = "publish"
    app.session_state["publish-reexport"] = str(reexport)
    app.run()
    assert not app.exception, app.exception
    texts = [m.value for m in app.markdown]
    assert "- Projet : Posée si Q3 (enfants) = 1 (Oui)" in texts
    assert "- LimeSurvey : Posée si Q3 (enfants) ≠ 2 (Non)" in texts
    assert "- LimeSurvey (non lue) : `is_empty(enfants)`" in texts
    assert "**Section changée** — Votre quartier" in texts
    app.button(key="publish-take-changed-emploi").click().run()
    assert any("pas de la forme" in e.value for e in app.error)
    app.button(key="publish-take-changed-nbenfants").click().run()
    app.button(key="publish-take-section-Votre quartier").click().run()
    assert not app.exception, app.exception
    saved = load_project(path)
    assert design.find(saved, "Q4").condition == when(term("Q3", "ne", "2"))
    assert saved.questionnaire.sections[1].condition == when(term("Q2", "ge", 18))
    assert design.find(saved, "Q5").condition is None
