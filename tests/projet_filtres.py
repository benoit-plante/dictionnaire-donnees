"""A designed questionnaire with filters (v0.21, steps 6 and 7), made by the tool's own
functions: the cases the author checks in LimeSurvey Cloud 7.6 (plan, § 5.7.4). A choice coded
"0"; a cascade (Q5 depends on Q4, itself filtered); an "or" whose one term names a question
that may not be asked; a number compared with 18; "≠" on a question that may be left empty;
a filtered section; a statement and an option as targets; every random order; an attention
check. Nothing real: the questions are invented."""

from ddict import design
from ddict.design import Draft, Item
from ddict.project.model import Condition, Project, Term

NOW = "2026-10-21T10:00:00"
AGREE = (
    Item("Pas du tout d'accord", "1"),
    Item("Plutôt pas d'accord", "2"),
    Item("Plutôt d'accord", "3"),
    Item("Tout à fait d'accord", "4"),
)


def _when(*terms, combine="all"):
    return Condition(
        combine=combine, terms=[Term(target=t, operator=o, value=v) for t, o, v in terms]
    )


def project() -> Project:
    found = design.new_project("Familles et quartier (essai des filtres)", "fr", "2026-10-21")
    design.modify_section(found, "S1", "Votre famille")
    design.add_section(found, "Votre quartier", "Répondez pour le quartier où vous vivez.")
    design.add_section(found, "Pour finir")
    drafts = [
        ("genre", Draft(kind="single", text="Quel est votre genre ?", section="S1", required=True,
                        options=(Item("Femme", "1"), Item("Homme", "2"), Item("Autre", "3")))),
        ("age", Draft(kind="open", text="Quel âge avez-vous ?", section="S1", answer="number")),
        ("enfants", Draft(kind="single", text="Avez-vous des enfants ?", section="S1",
                          options=(Item("Non", "0"), Item("Oui", "1"),
                                   Item("Préfère ne pas répondre", "9")))),
        ("nbenfants", Draft(kind="open", text="Combien d'enfants avez-vous ?", section="S1",
                            answer="number")),
        ("agesenfants", Draft(kind="open", text="Quel âge ont-ils ?", section="S1")),
        ("majeur", Draft(kind="open", text="Depuis quand votez-vous ?", section="S1",
                         answer="date")),
        ("emploi", Draft(kind="single", text="Quelle est votre situation d'emploi ?", section="S1",
                         options=(Item("Temps plein", "1"), Item("Temps partiel", "2"),
                                  Item("Sans emploi", "3")))),
        ("garde", Draft(kind="open", text="Qui garde les enfants pendant le travail ?",
                        section="S1")),
        ("sansenfant", Draft(kind="open", text="Souhaitez-vous ajouter quelque chose ?",
                             section="S1", answer="long")),
        ("climat", Draft(kind="grid", text="Votre quartier…", section="S2",
                         instruction="Une réponse par ligne.", options=AGREE,
                         rows=(Item("est calme.", "SQ001"), Item("est sûr.", "SQ002"),
                               Item("Pour cet énoncé, choisissez « Plutôt d'accord ».",
                                    "SQ003")))),
        ("transport", Draft(kind="checkbox", text="Comment vous déplacez-vous ?", section="S2",
                            options=(Item("En voiture", "1"), Item("À vélo", "2"),
                                     Item("Autre", other=True)))),
        ("merci", Draft(kind="display", text="Merci pour vos réponses.", section="S3")),
        ("velo", Draft(kind="open", text="Combien de kilomètres à vélo par semaine ?",
                       section="S3", answer="number")),
        ("calme", Draft(kind="open", text="Qu'est-ce qui rend votre quartier calme ?",
                        section="S3")),
    ]  # fmt: skip
    for code, draft in drafts:
        question_id = design.add_question(found, draft)
        if draft.kind != "display":
            design.decide_code(found, question_id, "write", now=NOW, value=code)
    design.set_condition(found, "Q4", _when(("Q3", "eq", "1")))  # "Oui", next to a "0"
    design.set_condition(found, "Q5", _when(("Q4", "answered", None)))  # the cascade
    design.set_condition(found, "Q6", _when(("Q2", "ge", 18)))  # 9 and 18, as numbers
    # An "or" whose first term names Q4, not asked to a person without children.
    design.set_condition(
        found, "Q8", _when(("Q4", "ge", 1), ("Q7", "in", ["1", "2"]), combine="any")
    )
    design.set_condition(found, "Q9", _when(("Q3", "ne", "1")))  # false when left empty
    design.set_condition(found, "S2", _when(("Q3", "not_in", ["9"])))  # a section
    design.set_condition(found, "Q13", _when(("Q11.o2", "checked", None)))  # an option
    design.set_condition(found, "Q14", _when(("Q10.r1", "eq", "4")))  # a statement
    design.set_shuffle(found, "Q7", True)  # a list's choices
    design.set_shuffle(found, "Q10", True)  # a grid's statements
    design.set_shuffle(found, "Q11", True)  # the boxes, "Autre" last
    design.set_shuffle(found, "S2", True)  # the questions of a section
    design.set_attention(found, "Q10.r3", ["3"])
    return found
