"""A project designed before its collection (v0.20, D-145, D-146), made by the tool's own
functions (`ddict.design`): a fictional questionnaire of each kind and the variables it plans,
with no database. Nothing real: the scale and its items are invented."""

from ddict import design
from ddict.design import Draft, Item
from ddict.project.model import Project, Provenance

TEAM = Provenance(kind="team")
MANUAL = Provenance(kind="source", source="Échelle fictive du sommeil, manuel", page=2)
FREQUENCY = (Item("Jamais", "1"), Item("Parfois", "2"), Item("Souvent", "3"), Item("Toujours", "4"))
ROWS = (
    "vous êtes-vous réveillé·e la nuit ?",
    "avez-vous bien dormi ?",
    "avez-vous eu du mal à vous endormir ?",
)


def project() -> Project:
    """Five questions in two sections, eight planned variables."""
    found = design.new_project("Étude du sommeil (conception)", "fr", "2026-10-19")
    design.modify_section(found, "S1", "Vous")
    design.add_section(found, "Votre sommeil", "Répondez pour le mois.")
    design.add_question(
        found,
        Draft(
            kind="single",
            text="Quel est votre genre ?",
            section="S1",
            required=True,
            provenance=TEAM,
            options=(
                Item("Femme", "1"),
                Item("Homme", "2"),
                Item("Autre", "3"),
                Item("Préfère ne pas répondre", "9"),
            ),
        ),
    )
    design.add_question(
        found,
        Draft(kind="open", text="Quel âge avez-vous ?", section="S1", answer="number"),
    )
    design.add_question(
        found,
        Draft(
            kind="display", text="Les questions suivantes portent sur votre sommeil.", section="S2"
        ),
    )
    design.add_question(
        found,
        Draft(
            kind="grid",
            text="Au cours du dernier mois, à quelle fréquence…",
            section="S2",
            instruction="Cochez une case par ligne.",
            provenance=MANUAL,
            options=tuple(Item(i.text, i.code, provenance=MANUAL) for i in FREQUENCY),
            rows=tuple(
                Item(text, f"SQ00{n}", provenance=MANUAL) for n, text in enumerate(ROWS, start=1)
            ),
        ),
    )
    design.add_question(
        found,
        Draft(
            kind="checkbox",
            text="Qu'est-ce qui vous aide à dormir ? Cochez tout ce qui s'applique.",
            section="S2",
            options=(Item("La lecture", "1"), Item("La musique", "2"), Item("Autre", other=True)),
        ),
    )
    return found
