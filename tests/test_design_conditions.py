"""v0.21, step 4 (§ 5.4 and 5.5 of the plan): the estimated duration of a designed
questionnaire and the review's new points (conditions, random order, attention checks), each
computed on a fictional questionnaire set with its trap. Nothing real."""

import pytest

from ddict import design, design_duration, design_points, i18n
from ddict.design import Draft, Item
from ddict.design_duration import Duration, Part
from projet_concu import project as designed
from test_skip import famille, term, when

NOW = "2026-10-21T10:00:00"


def codes(project, target=None):
    return [p.code for p in design_points.points(project) if target in (None, p.question)]


# --- The duration (D-171). ---


def test_the_duration_of_the_fictional_questionnaire():
    """Counted by hand: the sections' titles and instruction 7 words; Q1 5 + 7 choices; Q2 4;
    the displayed text 7; the grid 8 + 5 + 4 columns + 18 in its statements; the checkbox
    question 12 + 5. Five closed answers (a choice, three statements, the boxes), one short."""
    found = design_duration.estimate(designed())
    assert found.longest == Part(words=82, closed=5, short=1, long=0)
    assert found.shortest == found.longest and not found.filtered
    assert found.speed == 195  # in French
    seconds = 82 * 60 / 195 + 5 * 3 + 1 * 10
    assert found.longest.seconds(195) == pytest.approx(seconds)  # 50 s
    assert (found.low, found.high) == (1, 1)
    with i18n.using("fr"):
        assert design_duration.text(found) == "environ une minute"


def test_a_filtered_question_gives_a_range():
    project = designed()
    design.set_condition(project, "Q4", when(term("Q1", "eq", "1")))  # the grid
    found = design_duration.estimate(project)
    assert found.shortest == Part(words=82 - 35, closed=2, short=1, long=0)
    assert found.longest == Part(words=82, closed=5, short=1, long=0)
    design.set_condition(project, "S2", when(term("Q2", "ge", 18)))  # the section too
    found = design_duration.estimate(project)
    assert found.shortest == Part(words=12 + 4 + 1, closed=1, short=1, long=0)
    assert found.filtered


def test_the_duration_in_words_and_its_formula():
    found = Duration(Part(words=1950, closed=20), Part(words=2145, closed=40, long=1), 195)
    assert (found.low, found.high) == (11, 14)  # 10 min + 60 s; 11 min + 120 s + 60 s
    with i18n.using("fr"):
        assert design_duration.text(found) == "environ 11 à 14 minutes"
        lines = design_duration.formula(found)
        assert "195 mots par minute" in lines[1] and "Trauzettel-Klosinski" in lines[1]
        assert "repères de l'outil" in lines[2]
        assert lines[3].startswith("Chemin le plus court")
        assert lines[4].endswith("40 réponses fermées, 0 réponse courte, 1 réponse longue.")
    with i18n.using("en"):
        assert design_duration.text(found) == "about 11 to 14 minutes"
    english = designed()
    english.settings.language = "en"
    assert design_duration.estimate(english).speed == 228


def test_a_long_answer_counts_a_minute():
    project = design.new_project("Court (fictif)", "fr", "2026-10-21")
    design.add_question(project, Draft(kind="open", text="Racontez.", section="S1", answer="long"))
    found = design_duration.estimate(project)
    assert found.longest == Part(words=1, long=1)
    assert found.high == 1


# --- The review's new points (§ 5.5). ---


def test_a_condition_on_a_question_that_comes_after():
    project = famille()
    design.set_condition(project, "Q2", when(term("Q3", "eq", "1")))
    point = next(p for p in design_points.points(project) if p.code == "condition_forward")
    assert point.question == "Q2"
    assert "question 3" in point.text


def test_a_section_filtered_on_its_own_question_is_a_cycle():
    project = famille()
    design.set_condition(project, "S1", when(term("Q3", "eq", "1")))
    assert "condition_cycle" in codes(project, "Q3")
    assert "condition_forward" not in codes(project, "S1")


def test_a_target_removed_since():
    project = famille()
    design.set_condition(project, "Q4", when(term("Q3", "eq", "1")))
    design.remove_question(project, "Q3")
    point = next(p for p in design_points.points(project) if p.code == "condition_target_gone")
    assert (point.question, point.detail["targets"]) == ("Q4", "Q3")


def test_a_value_no_longer_a_choice():
    project = famille()
    design.set_condition(project, "Q4", when(term("Q3", "eq", "9")))
    question = design.find(project, "Q3")
    kept = tuple(Item(o.text, o.code, item_id=o.option_id) for o in question.options[:2])
    design.modify_question(
        project, "Q3", Draft(kind="single", text=question.text, section="S1", options=kept)
    )
    found = codes(project, "Q4")
    assert "condition_value_gone" in found
    assert "condition_never" in found  # its only code is gone


@pytest.mark.parametrize(
    "condition",
    [
        when(term("Q2", "ge", 18), term("Q2", "lt", 18)),
        when(term("Q2", "gt", 18), term("Q2", "le", 18)),
        when(term("Q2", "eq", 18), term("Q2", "ne", 18)),
        when(term("Q3", "eq", "1"), term("Q3", "eq", "2")),
        when(term("Q3", "in", ["1", "2"]), term("Q3", "not_in", ["1", "2"])),
        when(term("Q3", "not_in", ["1", "2", "9"])),
    ],
)
def test_a_condition_never_true(condition):
    project = famille()
    design.set_condition(project, "Q4", condition)
    assert "condition_never" in codes(project, "Q4")


def test_a_condition_that_can_hold_is_no_point():
    project = famille()
    design.set_condition(project, "Q4", when(term("Q2", "ge", 18), term("Q2", "le", 18)))
    design.set_condition(
        project, "Q6", when(term("Q3", "eq", "1"), term("Q2", "ge", 18), combine="any")
    )
    assert "condition_never" not in codes(project)


def test_a_question_under_one_never_asked_is_never_asked():
    project = famille()
    design.set_condition(project, "Q4", when(term("Q2", "ge", 18), term("Q2", "lt", 18)))
    design.set_condition(project, "Q6", when(term("Q4", "answered")))
    assert "condition_never" in codes(project, "Q6")
    design.set_condition(
        project, "Q6", when(term("Q4", "answered"), term("Q3", "eq", "1"), combine="any")
    )
    assert "condition_never" not in codes(project, "Q6")  # the other term can hold


def test_a_condition_on_an_optional_question():
    project = famille()
    design.set_condition(project, "Q4", when(term("Q3", "eq", "1")))
    assert "condition_optional" in codes(project, "Q4")
    question = design.find(project, "Q3")
    options = tuple(Item(o.text, o.code, item_id=o.option_id) for o in question.options)
    draft = Draft(kind="single", text=question.text, section="S1", required=True, options=options)
    design.modify_question(project, "Q3", draft)
    assert "condition_optional" not in codes(project, "Q4")


def test_a_filtered_section_without_a_displayed_text():
    project = famille()
    design.set_condition(project, "S2", when(term("Q3", "eq", "1")))
    assert "section_without_display" in codes(project, "S2")
    design.add_question(project, Draft(kind="display", text="Pour les parents.", section="S2"))
    assert "section_without_display" not in codes(project, "S2")


def test_random_order_of_a_section_that_holds_what_has_a_place():
    project = famille()
    design.set_shuffle(project, "S2", True)
    assert "shuffle_section_mixed" not in codes(project)
    design.set_condition(project, "Q9", when(term("Q8", "answered")))
    point = next(p for p in design_points.points(project) if p.code == "shuffle_section_mixed")
    assert point.question == "S2" and "condition" in point.detail["what"]
    design.set_attention(project, "Q7.r2", ["4"])
    design.add_question(project, Draft(kind="display", text="Merci.", section="S2"))
    point = next(p for p in design_points.points(project) if p.code == "shuffle_section_mixed")
    assert point.detail["what"].count(",") == 2  # the three


def test_random_order_of_choices_with_a_refusal():
    project = famille()
    design.set_shuffle(project, "Q3", True)
    point = next(p for p in design_points.points(project) if p.code == "shuffle_refusal")
    assert point.detail["choice"] == "« Préfère ne pas répondre »"
    design.set_shuffle(project, "Q5", True)
    assert codes(project, "Q5").count("shuffle_refusal") == 0


def test_an_attention_check_optional_or_under_a_condition():
    project = famille()
    design.set_attention(project, "Q5", ["1"])
    point = next(p for p in design_points.points(project) if p.code == "attention_doubtful")
    assert point.detail["why"] == "facultatif"
    design.set_condition(project, "Q5", when(term("Q2", "ge", 18)))
    point = next(p for p in design_points.points(project) if p.code == "attention_doubtful")
    assert point.detail["why"] == "facultatif et sous une condition"


def test_an_attention_check_whose_answer_is_gone():
    project = famille()
    design.set_attention(project, "Q5", ["3"])
    question = design.find(project, "Q5")
    kept = tuple(Item(o.text, o.code, item_id=o.option_id) for o in question.options[:2])
    design.modify_question(
        project, "Q5", Draft(kind="single", text=question.text, section="S1", options=kept)
    )
    point = next(p for p in design_points.points(project) if p.code == "attention_gone")
    assert point.detail["codes"] == "3"


def test_a_section_point_comes_first_and_is_kept_while_the_section_says_the_same():
    project = famille()
    design.set_condition(project, "S2", when(term("Q3", "eq", "1")))
    found = design_points.points(project)
    first_of_s2 = next(
        n for n, p in enumerate(found) if p.question in ("S2", "Q7", "Q8", "Q9", "Q10")
    )
    assert found[first_of_s2].question == "S2"
    point = next(p for p in found if p.code == "section_without_display")
    design_points.keep(project, point, NOW)
    assert "section_without_display" not in codes(project)
    design.modify_section(project, "S2", "Votre quartier, aujourd'hui")
    assert "section_without_display" in codes(project)


def test_a_questionnaire_without_conditions_has_no_new_point():
    before = {p.code for p in design_points.points(designed())}
    assert not {c for c in before if c.startswith(("condition", "shuffle", "attention", "section"))}
