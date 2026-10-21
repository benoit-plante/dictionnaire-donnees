"""v0.21, step 6 (§ 5.7.1 of the plan): the conditions and the random orders written in the
file for LimeSurvey, each form of the table of § 5.7.1, the summary, the refusal of a
condition left without its target. Fictional only (`projet_filtres`, `test_skip`)."""

import pytest

from ddict import design, design_limesurvey
from ddict.design_limesurvey import Unwritable, expression
from projet_concu import project as designed
from projet_filtres import project as filtres
from test_skip import famille, term, when

# The table of § 5.7.1, on the questionnaire of `test_skip` (codes enfants, emploi, age, …).
FORMS = [
    (term("Q3", "eq", "1"), '(enfants.NAOK != "" and enfants.NAOK == "1")'),
    (
        term("Q5", "in", ["1", "2"]),
        '(emploi.NAOK != "" and (emploi.NAOK == "1" or emploi.NAOK == "2"))',
    ),
    (term("Q5", "not_in", ["3"]), '(emploi.NAOK != "" and emploi.NAOK != "3")'),
    (term("Q2", "ge", 18), '(age.NAOK != "" and age.NAOK >= 18)'),
    (term("Q10.o2", "checked"), '(transport_2.NAOK == "Y")'),
    (term("Q7.r2", "eq", "4"), '(climat_SQ002.NAOK != "" and climat_SQ002.NAOK == "4")'),
    (term("Q4", "answered"), '(nbenfants.NAOK != "")'),
    (term("Q2", "lt", 17.5), '(age.NAOK != "" and age.NAOK < 17.5)'),
    (term("Q5", "ne", "3"), '(emploi.NAOK != "" and emploi.NAOK != "3")'),
]


@pytest.mark.parametrize(("found", "written"), FORMS)
def test_each_form_of_a_term(found, written):
    project = famille()
    design.set_condition(project, "Q6", when(found))
    assert expression(project, design.find(project, "Q6").condition) == written


def test_terms_joined_and_always():
    project = famille()
    assert expression(project, None) == "1"
    both = when(term("Q3", "eq", "1"), term("Q2", "ge", 18), combine="any")
    assert expression(project, both) == (
        '(enfants.NAOK != "" and enfants.NAOK == "1") or (age.NAOK != "" and age.NAOK >= 18)'
    )


def _rows(project):
    lines = design_limesurvey.text(project).splitlines()
    header = lines[0].split("\t")
    return [dict(zip(header, line.split("\t"), strict=True)) for line in lines[1:]]


def _unquoted(cell: str) -> str:
    return cell[1:-1].replace('""', '"') if cell.startswith('"') else cell


def test_the_file_holds_the_conditions_and_the_random_orders():
    rows = _rows(filtres())
    groups = {r["name"].strip('"'): r for r in rows if r["class"] == "G"}
    questions = {r["name"]: r for r in rows if r["class"] == "Q"}
    assert _unquoted(groups["Votre famille"]["relevance"]) == "1"
    assert _unquoted(groups["Votre quartier"]["relevance"]) == (
        '(enfants.NAOK != "" and enfants.NAOK != "9")'
    )
    assert _unquoted(questions["nbenfants"]["relevance"]) == (
        '(enfants.NAOK != "" and enfants.NAOK == "1")'
    )
    assert _unquoted(questions["agesenfants"]["relevance"]) == '(nbenfants.NAOK != "")'
    assert _unquoted(questions["garde"]["relevance"]) == (
        '(nbenfants.NAOK != "" and nbenfants.NAOK >= 1) or '
        '(emploi.NAOK != "" and (emploi.NAOK == "1" or emploi.NAOK == "2"))'
    )
    assert _unquoted(questions["velo"]["relevance"]) == '(transport_2.NAOK == "Y")'
    assert _unquoted(questions["calme"]["relevance"]) == (
        '(climat_SQ001.NAOK != "" and climat_SQ001.NAOK == "4")'
    )
    assert questions["genre"]["relevance"] == "1"
    # The random orders.
    assert questions["emploi"]["answer_order"] == "random"
    assert questions["climat"]["subquestion_order"] == "random"
    assert questions["transport"]["subquestion_order"] == "random"
    assert questions["genre"]["answer_order"] == questions["genre"]["subquestion_order"] == ""
    assert questions["climat"]["random_group"] == questions["transport"]["random_group"] == "S2"
    assert questions["genre"]["random_group"] == ""
    # The subquestions are always asked with their question.
    assert {r["relevance"] for r in rows if r["class"] == "SQ"} == {"1"}


def test_the_summary_counts_and_says_what_stays():
    found = design_limesurvey.summary(filtres())
    assert (found.conditions, found.shuffled) == (8, 4)
    assert any("items de contrôle" in line for line in found.left)
    steps = design_limesurvey.import_steps(filtres())
    assert any("logique du questionnaire" in step for step in steps)
    plain = design_limesurvey.summary(designed())
    assert (plain.conditions, plain.shuffled) == (0, 0)
    assert not any("logique" in step for step in design_limesurvey.import_steps(designed()))


def test_a_questionnaire_without_conditions_writes_the_same_file():
    """The file of the v0.20: "1" everywhere, no random order."""
    rows = _rows(designed())
    assert {r["relevance"] for r in rows if r["class"] in ("G", "Q", "SQ")} == {"1"}
    assert {r["answer_order"] + r["subquestion_order"] + r["random_group"] for r in rows} == {""}


def test_a_condition_left_without_its_target_refuses_the_writing():
    project = famille()
    design.set_condition(project, "Q4", when(term("Q3", "eq", "1")))
    design.remove_question(project, "Q3")
    found = design_limesurvey.summary(project)
    assert any("retiré (Q3)" in p for p in found.problems)
    with pytest.raises(Unwritable):
        design_limesurvey.text(project)


def test_no_text_and_no_brace_enters_an_expression():
    for row in _rows(filtres()):
        relevance = _unquoted(row["relevance"])
        assert "{" not in relevance and "}" not in relevance
        assert all(c.isascii() for c in relevance)
