"""v0.21, step 3 (D-165 to D-168, D-170): a condition, a random order and an attention check
set, changed and removed by `ddict.design`; the refusals; the effective condition; a condition
in plain words, for the committee and for the team, in French and in English; who was asked,
on tables made by hand; the condition carried by the planned variables. Nothing real: the
questionnaire and its answers are invented."""

import math

import pandas as pd
import pytest

from ddict import design, i18n
from ddict.design import DesignError, Draft, Item
from ddict.project import skip
from ddict.project.model import Condition, Term, TrackedValue

NOW = "2026-10-21T10:00:00"
AGREE = (
    Item("Pas du tout d'accord", "1"),
    Item("Plutôt pas d'accord", "2"),
    Item("Plutôt d'accord", "4"),
    Item("Tout à fait d'accord", "5"),
)


def famille():
    """Ten numbered questions in two sections, one of each nature, the codes decided: their
    numbers are their ids (Q1 to Q10), as in the table of § 5.1 of the plan."""
    project = design.new_project("Familles (fictif)", "fr", "2026-10-21")
    design.add_section(project, "Votre quartier")

    def single(text, code, options, section="S1"):
        return Draft(kind="single", text=text, section=section, options=options), code

    drafts = [
        single("Votre genre ?", "genre", (Item("Femme", "1"), Item("Homme", "2"))),
        (Draft(kind="open", text="Votre âge ?", section="S1", answer="number"), "age"),
        single(
            "Avez-vous des enfants ?",
            "enfants",
            (Item("Oui", "1"), Item("Non", "2"), Item("Préfère ne pas répondre", "9")),
        ),
        (Draft(kind="open", text="Combien ?", section="S1", answer="number"), "nbenfants"),
        single(
            "Votre emploi ?",
            "emploi",
            (Item("Temps plein", "1"), Item("Temps partiel", "2"), Item("Sans emploi", "3")),
        ),
        (Draft(kind="open", text="Un commentaire ?", section="S1", answer="long"), "commentaire"),
        (
            Draft(
                kind="grid",
                text="Votre quartier…",
                section="S2",
                options=AGREE,
                rows=(Item("est calme.", "SQ001"), Item("est sûr.", "SQ002")),
            ),
            "climat",
        ),
        (Draft(kind="open", text="Arrivée ?", section="S2", answer="date"), "arrivee"),
        (Draft(kind="open", text="Votre ville ?", section="S2"), "ville"),
        (
            Draft(
                kind="checkbox",
                text="Vos transports ?",
                section="S2",
                options=(Item("Auto", "1"), Item("Vélo", "2"), Item("Autre", other=True)),
            ),
            "transport",
        ),
    ]
    for draft, code in drafts:
        question_id = design.add_question(project, draft)
        design.decide_code(project, question_id, "write", now=NOW, value=code)
    return project


def term(target, operator, value=None):
    return Term(target=target, operator=operator, value=value)


def when(*terms, combine="all"):
    return Condition(combine=combine, terms=list(terms))


def entry(project, name):
    return next(e for e in project.variables if e.name == name)


# --- Each operator on each nature (D-165). ---

NATURES = {
    "Q3": ("choice", "1"),  # a single choice
    "Q7.r2": ("choice", "4"),  # a grid's statement
    "Q10.o2": ("box", None),  # an option to tick
    "Q2": ("number", 18),
    "Q6": ("text", None),  # a long text
    "Q8": ("text", None),  # a date
    "Q9": ("text", None),  # a short text
}
OPERATORS = ("eq", "ne", "in", "not_in", "lt", "le", "gt", "ge", "checked", "answered")


def _value(operator, value):
    if operator in ("checked", "answered"):
        return None
    if operator in ("in", "not_in"):
        return [value if value is not None else "1"]
    return value if value is not None else "1"


@pytest.mark.parametrize("target", NATURES)
@pytest.mark.parametrize("operator", OPERATORS)
def test_each_operator_on_each_nature(target, operator):
    project = famille()
    nature, value = NATURES[target]
    condition = when(term(target, operator, _value(operator, value)))
    before = project.model_dump()
    if operator in skip.OPERATORS[nature]:
        design.set_condition(project, "Q5", condition)
        assert design.find(project, "Q5").condition.terms[0].operator == operator
    else:
        with pytest.raises(DesignError, match="opérateur"):
            design.set_condition(project, "Q5", condition)
        assert project.model_dump() == before


# --- The refusals (§ 5.1): the question does not change. ---


@pytest.mark.parametrize(
    ("owner", "found", "reason"),
    [
        ("Q5", term("Q99", "answered"), "ne peut pas servir"),  # unknown
        ("Q5", term("Q5", "answered"), "elle-même"),  # itself
        ("Q7", term("Q7.r1", "eq", "1"), "elle-même"),  # one of its statements
        ("Q5", term("Q7", "answered"), "ne peut pas servir"),  # a whole grid
        ("Q5", term("Q10", "answered"), "ne peut pas servir"),  # a whole checkbox question
        ("Q5", term("Q10.o3", "checked"), "ne peut pas servir"),  # the "other" option
        ("Q5", term("Q7.r9", "eq", "1"), "ne peut pas servir"),  # a statement gone
        ("Q5", term("Q3", "eq", "7"), "n'est pas un choix"),  # not a code of its choices
        ("Q5", term("Q3", "in", ["1", "7"]), "n'est pas un choix"),
        ("Q5", term("Q7.r2", "eq", "3"), "n'est pas un choix"),  # not a column of the grid
        ("Q5", term("Q2", "ge", "dix-huit"), "attend un nombre"),  # not a number
        ("S2", term("Q3", "gt", "1"), "opérateur"),  # an order on choices
    ],
)
def test_a_condition_is_refused(owner, found, reason):
    project = famille()
    before = project.model_dump()
    with pytest.raises(DesignError, match=reason):
        design.set_condition(project, owner, when(found))
    assert project.model_dump() == before


def test_a_condition_set_changed_and_removed():
    project = famille()
    sealed = project.questionnaire.sha256
    design.set_condition(project, "Q4", when(term("Q3", "eq", 1)))
    found = design.find(project, "Q4")
    assert found.condition == when(term("Q3", "eq", "1"))  # a choice's code, as written
    assert project.questionnaire.sha256 != sealed
    design.set_condition(project, "Q4", when(term("Q2", "ge", "18"), term("Q3", "ne", "2")))
    assert design.find(project, "Q4").condition.terms[0].value == 18  # a number, as a number
    design.set_condition(project, "Q4", None)
    assert design.find(project, "Q4").condition is None
    assert project.questionnaire.sha256 == sealed
    design.set_condition(project, "S2", when(term("Q3", "eq", "1"), combine="any"))
    assert project.questionnaire.sections[1].condition.combine == "any"
    with pytest.raises(DesignError, match="Section inconnue"):
        design.set_condition(project, "S9", when(term("Q3", "eq", "1")))


def test_the_effective_condition_is_the_section_and_the_question():
    project = famille()
    found = project.questionnaire
    design.set_condition(
        project, "S2", when(term("Q3", "eq", "1"), term("Q5", "eq", "1"), combine="any")
    )
    design.set_condition(project, "Q8", when(term("Q2", "ge", 18)))
    section, own = found.sections[1].condition, design.find(project, "Q8").condition
    assert skip.effective(found, design.find(project, "Q8")) == [section, own]
    assert skip.effective(found, design.find(project, "Q9")) == [section]
    assert skip.effective(found, design.find(project, "Q1")) == []


def test_a_change_of_the_question_keeps_what_the_draft_does_not_carry():
    project = famille()
    design.set_condition(project, "Q7", when(term("Q3", "eq", "1")))
    design.set_shuffle(project, "Q7", True)
    design.set_attention(project, "Q7.r2", ["4"])
    grid = design.find(project, "Q7")
    draft = Draft(
        kind="grid",
        text="Votre quartier, aujourd'hui…",
        section="S2",
        options=tuple(Item(o.text, o.code, item_id=o.option_id) for o in grid.options),
        rows=tuple(Item(r.text, r.code, item_id=r.row_id) for r in grid.rows),
    )
    design.modify_question(project, "Q7", draft)
    grid = design.find(project, "Q7")
    assert grid.condition == when(term("Q3", "eq", "1"))
    assert grid.shuffle and grid.rows[1].attention == ["4"]
    # Now an open question: the condition stays, what its kind does not admit goes.
    design.modify_question(project, "Q7", Draft(kind="open", text="Votre quartier ?", section="S2"))
    found = design.find(project, "Q7")
    assert found.condition == when(term("Q3", "eq", "1"))
    assert not found.shuffle and found.attention is None


def test_removing_a_question_says_the_conditions_that_name_it():
    project = famille()
    design.set_condition(project, "Q4", when(term("Q3", "eq", "1")))
    design.set_condition(project, "S2", when(term("Q3", "answered")))
    design.set_condition(project, "Q8", when(term("Q7.r1", "eq", "4")))
    said = design.citations(project, "Q3")
    assert "la condition de S2 vise cette question" in said
    assert "la condition de Q4 vise cette question" in said
    assert design.citations(project, "Q7") == ["la condition de Q8 vise cette question"]
    assert design.citations(project, "Q5") == []
    design.remove_question(project, "Q3")  # said, not refused: the review asks to correct
    assert design.find(project, "Q4").condition == when(term("Q3", "eq", "1"))
    assert entry(project, "nbenfants").asked_if is None  # nothing carried until corrected


# --- Random order (D-166) and attention checks (D-170). ---


def test_random_order_set_and_removed():
    project = famille()
    for owner in ("S2", "Q3", "Q7", "Q10"):
        design.set_shuffle(project, owner, True)
    assert project.questionnaire.sections[1].shuffle
    assert all(design.find(project, q).shuffle for q in ("Q3", "Q7", "Q10"))
    design.set_shuffle(project, "Q7", False)
    assert not design.find(project, "Q7").shuffle
    before = project.model_dump()
    with pytest.raises(DesignError, match="ordre aléatoire"):
        design.set_shuffle(project, "Q2", True)
    assert project.model_dump() == before
    design.set_shuffle(project, "Q2", False)  # nothing to refuse


def test_an_attention_check_set_and_removed():
    project = famille()
    design.set_attention(project, "Q7.r2", [4, "4"])
    grid = design.find(project, "Q7")
    assert grid.rows[1].attention == ["4"]
    group = next(g for g in project.groups if g.question == "Q7")
    assert group.members.value == ["climat_SQ001"]  # it enters no score
    assert group.attached == ["climat_SQ002"]
    design.set_attention(project, "Q5", ["1", "2"])
    assert design.find(project, "Q5").attention == ["1", "2"]
    design.set_attention(project, "Q7.r2", None)
    group = next(g for g in project.groups if g.question == "Q7")
    assert group.members.value == ["climat_SQ001", "climat_SQ002"] and group.attached == []


@pytest.mark.parametrize(
    ("item", "correct", "reason"),
    [
        ("Q7", ["4"], "choix unique"),  # a whole grid
        ("Q2", ["4"], "choix unique"),  # a number
        ("Q7.r9", ["4"], "Énoncé inconnu"),
        ("Q7.r1", ["3"], "n'est pas un choix"),
        ("Q5", [], "au moins une"),
        ("Q99", ["1"], "Question inconnue"),
    ],
)
def test_an_attention_check_is_refused(item, correct, reason):
    project = famille()
    before = project.model_dump()
    with pytest.raises(DesignError, match=reason):
        design.set_attention(project, item, correct)
    assert project.model_dump() == before


# --- The planned variables carry the condition (D-168). ---


def test_the_planned_variables_carry_the_effective_condition():
    project = famille()
    design.set_condition(project, "Q4", when(term("Q3", "eq", "1")))
    carried = entry(project, "nbenfants").asked_if
    assert carried.origin == "computed" and carried.status == "none"
    assert carried.value == [when(term("enfants", "eq", 1))]  # the code as the variable holds it
    design.set_condition(
        project, "S2", when(term("Q10.o2", "checked"), term("Q2", "ge", 18), combine="any")
    )
    design.set_condition(project, "Q7", when(term("Q5", "in", ["1", "2"])))
    for name in ("climat_SQ001", "climat_SQ002"):
        assert entry(project, name).asked_if.value == [
            when(term("transport_2", "checked"), term("age", "ge", 18), combine="any"),
            when(term("emploi", "in", [1, 2])),
        ]
    assert entry(project, "transport_other").asked_if.value[0].combine == "any"
    assert entry(project, "genre").asked_if is None
    # A code changed: the condition follows the variable's new name.
    design.decide_code(project, "Q3", "write", now=NOW, value="enfant")
    assert entry(project, "nbenfants").asked_if.value == [when(term("enfant", "eq", 1))]
    # Removed: no longer carried.
    design.set_condition(project, "Q4", None)
    assert entry(project, "nbenfants").asked_if is None


def test_a_condition_typed_by_a_person_stays():
    project = famille()
    typed = [when(term("emploi", "answered"))]
    entry(project, "nbenfants").asked_if = TrackedValue[list[Condition]](
        value=typed, origin="human"
    )
    design.set_condition(project, "Q4", when(term("Q3", "eq", "1")))
    assert entry(project, "nbenfants").asked_if.value == typed


# --- In plain words (§ 5.1). ---

COMMITTEE = [
    (
        "Q3 eq 1",
        term("Q3", "eq", "1"),
        "Si vous avez répondu « Oui » à la question 3",
        "If you answered “Oui” to question 3",
    ),
    (
        "Q5 in [1, 2]",
        term("Q5", "in", ["1", "2"]),
        "Si vous avez répondu « Temps plein » ou « Temps partiel » à la question 5",
        "If you answered “Temps plein” or “Temps partiel” to question 5",
    ),
    (
        "Q2 ge 18",
        term("Q2", "ge", 18),
        "Si votre réponse à la question 2 est 18 ou plus",
        "If your answer to question 2 is 18 or more",
    ),
    (
        "Q10.o2 checked",
        term("Q10.o2", "checked"),
        "Si vous avez coché « Vélo » à la question 10",
        "If you ticked “Vélo” in question 10",
    ),
    (
        "Q7.r2 eq 4",
        term("Q7.r2", "eq", "4"),
        "Si vous avez répondu « Plutôt d'accord » à l'énoncé « est sûr. » de la question 7",
        "If you answered “Plutôt d'accord” to the statement “est sûr.” of question 7",
    ),
    (
        "Q4 answered",
        term("Q4", "answered"),
        "Si vous avez répondu à la question 4",
        "If you gave an answer to question 4",
    ),
]
TEAM = [
    (term("Q3", "eq", "1"), "Posée si Q3 (enfants) = 1 (Oui)", "Asked if Q3 (enfants) = 1 (Oui)"),
    (
        term("Q5", "in", ["1", "2"]),
        "Posée si Q5 (emploi) ∈ {1 (Temps plein), 2 (Temps partiel)}",
        "Asked if Q5 (emploi) ∈ {1 (Temps plein), 2 (Temps partiel)}",
    ),
    (term("Q2", "ge", 18), "Posée si Q2 (age) ≥ 18", "Asked if Q2 (age) ≥ 18"),
    (
        term("Q10.o2", "checked"),
        "Posée si Q10 (transport) : Vélo coché",
        "Asked if Q10 (transport): Vélo ticked",
    ),
    (
        term("Q7.r2", "eq", "4"),
        "Posée si Q7 (climat_SQ002) = 4 (Plutôt d'accord)",
        "Asked if Q7 (climat_SQ002) = 4 (Plutôt d'accord)",
    ),
    (
        term("Q4", "answered"),
        "Posée si Q4 (nbenfants) a une réponse",
        "Asked if Q4 (nbenfants) has an answer",
    ),
]


@pytest.mark.parametrize(("_name", "found", "french", "english"), COMMITTEE)
def test_a_condition_for_the_committee(_name, found, french, english):
    project = famille()
    with i18n.using("fr"):
        assert skip.committee_text(project, when(found)) == french
    with i18n.using("en"):
        assert skip.committee_text(project, when(found)) == english


@pytest.mark.parametrize(("found", "french", "english"), TEAM)
def test_a_condition_for_the_team(found, french, english):
    project = famille()
    with i18n.using("fr"):
        assert skip.team_text(project, when(found)) == french
    with i18n.using("en"):
        assert skip.team_text(project, when(found)) == english


def test_terms_joined_and_a_section():
    project = famille()
    both = when(term("Q3", "eq", "1"), term("Q2", "ge", 18))
    either = when(term("Q3", "ne", "1"), term("Q10.o2", "checked"), combine="any")
    with i18n.using("fr"):
        assert skip.committee_text(project, both) == (
            "Si vous avez répondu « Oui » à la question 3 et si votre réponse à la question 2 "
            "est 18 ou plus"
        )
        assert skip.committee_text(project, either, section=True) == (
            "Cette section s'adresse aux personnes qui ont répondu autre chose que « Oui » à la "
            "question 3 ou qui ont coché « Vélo » à la question 10"
        )
        assert skip.team_text(project, [either, when(term("Q2", "lt", 65.5))]) == (
            "Posée si (Q3 (enfants) ≠ 1 (Oui) ou Q10 (transport) : Vélo coché) et Q2 (age) < 65,5"
        )
    with i18n.using("en"):
        assert skip.committee_text(project, both) == (
            "If you answered “Oui” to question 3 and if your answer to question 2 is 18 or more"
        )
        assert skip.committee_text(project, either, section=True) == (
            "This section is for people who answered something other than “Oui” to question 3 "
            "or who ticked “Vélo” in question 10"
        )
        assert skip.team_text(project, [either, when(term("Q2", "lt", 65.5))]) == (
            "Asked if (Q3 (enfants) ≠ 1 (Oui) or Q10 (transport): Vélo ticked) and Q2 (age) < 65.5"
        )


def test_the_numbers_skip_a_displayed_text_and_an_undecided_code_is_not_shown():
    project = design.new_project("Court (fictif)", "fr", "2026-10-21")
    design.add_question(project, Draft(kind="display", text="Bienvenue.", section="S1"))
    yes_no = (Item("Oui", "1"), Item("Non", "2"))
    design.add_question(project, Draft(kind="single", text="A ?", section="S1", options=yes_no))
    design.add_question(project, Draft(kind="open", text="B ?", section="S1"))
    design.set_condition(project, "Q3", when(term("Q2", "eq", "1")))
    with i18n.using("fr"):
        assert skip.team_text(project, design.find(project, "Q3").condition) == (
            "Posée si Q1 = 1 (Oui)"
        )
        assert skip.committee_text(project, design.find(project, "Q3").condition) == (
            "Si vous avez répondu « Oui » à la question 1"
        )


def test_a_variable_condition_in_plain_words():
    project = famille()
    design.set_condition(project, "Q4", when(term("Q3", "ne", "2"), term("Q2", "ge", 18)))
    found = entry(project, "nbenfants").asked_if.value
    with i18n.using("fr"):
        assert skip.variable_text(project, found) == ("Posée si enfants ≠ 2 (Non) et age ≥ 18")
    with i18n.using("en"):
        assert skip.variable_text(project, found) == "Asked if enfants ≠ 2 (Non) and age ≥ 18"


# --- Who was asked, on tables made by hand (§ 5.8.1). ---

NA = math.nan


def test_the_four_cases():
    data = pd.DataFrame({"enfants": [1.0, 1.0, 2.0, 2.0, NA], "nbenfants": [2.0, NA, NA, 3.0, NA]})
    conditions = {"nbenfants": [when(term("enfants", "eq", 1))]}
    assert skip.asked(data, conditions)["nbenfants"].tolist() == [True, True, False, False, False]
    assert skip.natures(data, conditions)["nbenfants"].tolist() == [
        skip.ANSWER,
        skip.MISSING,
        skip.NOT_APPLICABLE,
        skip.ANOMALY,
        skip.NOT_APPLICABLE,  # the filter left empty: the term is false
    ]


def test_the_cascade():
    data = pd.DataFrame(
        {
            "enfants": [1, 2, 2],
            "nbenfants": [2, NA, 3],  # the third: an anomaly
            "ages": ["4 et 6", "", "7"],
        }
    )
    conditions = {
        "nbenfants": [when(term("enfants", "eq", 1))],
        "ages": [when(term("nbenfants", "answered"))],
    }
    found = skip.asked(data, conditions)
    assert found["ages"].tolist() == [True, False, True]  # an anomaly counts as its answer
    assert skip.natures(data, conditions)["ages"].tolist() == [
        skip.ANSWER,
        skip.NOT_APPLICABLE,
        skip.ANSWER,
    ]


def test_an_or_with_a_term_not_asked():
    data = pd.DataFrame({"nbenfants": [NA, NA, 2], "emploi": [1, 3, 3], "garde": [NA, NA, NA]})
    conditions = {
        "garde": [when(term("nbenfants", "ge", 1), term("emploi", "eq", 1), combine="any")]
    }
    assert skip.asked(data, conditions)["garde"].tolist() == [True, False, True]


def test_a_missing_code_in_the_filter_is_a_choice():
    """§ 4.2, point 3: 9 "Préfère ne pas répondre" is declared missing, but it was chosen;
    LimeSurvey asks the next question when its condition is "≠ 1"."""
    data = pd.DataFrame({"enfants": [9.0, 1.0, 2.0, NA], "suite": [NA, NA, NA, NA]})
    conditions = {"suite": [when(term("enfants", "ne", 1))]}
    assert skip.asked(data, conditions)["suite"].tolist() == [True, False, True, False]


def test_the_values_as_a_file_holds_them():
    data = pd.DataFrame(
        {
            "enfants": ["1", " 1 ", "2", ""],  # a CSV's texts
            "age": ["18", "17", "abc", None],
            "velo": ["Y", "N", "0", ""],
            "ville": ["Lyon", "  ", None, "Nice"],
        }
    )
    assert skip.holds(data, [when(term("enfants", "eq", 1))]).tolist() == [True, True, False, False]
    assert skip.holds(data, [when(term("enfants", "not_in", ["2"]))]).tolist() == [
        True,
        True,
        False,
        False,
    ]
    assert skip.holds(data, [when(term("age", "ge", 18))]).tolist() == [True, False, False, False]
    assert skip.holds(data, [when(term("age", "lt", 18))]).tolist() == [False, True, False, False]
    assert skip.holds(data, [when(term("velo", "checked"))]).tolist() == [True, False, False, False]
    assert skip.holds(data, [when(term("ville", "answered"))]).tolist() == [
        True,
        False,
        False,
        True,
    ]
    numbers = pd.DataFrame({"velo": [1.0, 0.0, NA]})
    assert skip.holds(numbers, [when(term("velo", "checked"))]).tolist() == [True, False, False]
    with pytest.raises(ValueError, match="no column"):
        skip.holds(data, [when(term("absente", "answered"))])
