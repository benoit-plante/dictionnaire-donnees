"""A project designed before its collection (v0.20, D-145, D-146), written by hand: a fictional
questionnaire of each kind and the variables it plans, with no database. Step B3 will make the
variables from the questionnaire by the tool's own function; this one only shows the format.
Nothing real: the scale and its items are invented."""

from ddict.project.model import (
    Design,
    FileMetadata,
    GridRow,
    Group,
    Planned,
    Privacy,
    Project,
    Provenance,
    Question,
    Questionnaire,
    QuestionOption,
    Section,
    TrackedValue,
    ValueLabel,
    VariableEntry,
)

TEAM = Provenance(kind="team")
MANUAL = Provenance(kind="source", source="Échelle fictive du sommeil, manuel", page=2)
FREQUENCY = [("1", "Jamais"), ("2", "Parfois"), ("3", "Souvent"), ("4", "Toujours")]


def _options(question_id: str, choices, provenance=TEAM) -> list[QuestionOption]:
    return [
        QuestionOption(
            option_id=f"{question_id}.o{rank}", text=text, code=code, provenance=provenance
        )
        for rank, (code, text) in enumerate(choices, start=1)
    ]


def questionnaire() -> Questionnaire:
    return Questionnaire(
        file_name="Étude du sommeil (conception)",
        sha256="0" * 64,
        format="designed",
        sections=[
            Section(section_id="S1", title="Vous"),
            Section(section_id="S2", title="Votre sommeil", instruction="Répondez pour le mois."),
        ],
        questions=[
            Question(
                question_id="Q1",
                section="S1",
                text="Quel est votre genre ?",
                kind="single",
                layout="radio",
                required=True,
                provenance=TEAM,
                options=_options(
                    "Q1",
                    [
                        ("1", "Femme"),
                        ("2", "Homme"),
                        ("3", "Autre"),
                        ("9", "Préfère ne pas répondre"),
                    ],
                ),
            ),
            Question(
                question_id="Q2",
                section="S1",
                text="Quel âge avez-vous ?",
                kind="open",
                answer="number",
                provenance=TEAM,
            ),
            Question(
                question_id="Q3",
                section="S2",
                text="Les questions suivantes portent sur votre sommeil.",
                kind="display",
                provenance=TEAM,
            ),
            Question(
                question_id="Q4",
                section="S2",
                text="Au cours du dernier mois, à quelle fréquence…",
                instruction="Cochez une case par ligne.",
                kind="grid",
                provenance=MANUAL,
                options=_options("Q4", FREQUENCY, MANUAL),
                rows=[
                    GridRow(row_id=f"Q4.r{rank}", text=text, code=f"SQ00{rank}", provenance=MANUAL)
                    for rank, text in enumerate(
                        [
                            "vous êtes-vous réveillé·e la nuit ?",
                            "avez-vous bien dormi ?",
                            "avez-vous eu du mal à vous endormir ?",
                        ],
                        start=1,
                    )
                ],
            ),
            Question(
                question_id="Q5",
                section="S2",
                text="Qu'est-ce qui vous aide à dormir ? Cochez tout ce qui s'applique.",
                kind="checkbox",
                provenance=TEAM,
                options=[
                    *_options("Q5", [("1", "La lecture"), ("2", "La musique")]),
                    QuestionOption(option_id="Q5.o3", text="Autre", code="other", other=True),
                ],
            ),
        ],
    )


def _planned(
    name: str, position: int, question: str, label: str, kind: str, labels=(), storage="numeric"
) -> VariableEntry:
    return VariableEntry(
        name=name,
        position=position,
        file=FileMetadata(
            storage_type=storage,
            label=label,
            value_labels=[ValueLabel(code=int(c), label=t) for c, t in labels],
        ),
        planned=Planned(type=kind),
        privacy=Privacy(privacy_class=TrackedValue[str](value="ordinary", origin="computed")),
        question=TrackedValue[str](value=question, origin="computed"),
        label=TrackedValue[str](value=label, origin="file"),
        description=TrackedValue[str](origin="human"),
        unit=TrackedValue[str](origin="human"),
        group_id=TrackedValue[str](origin="human"),
    )


def project() -> Project:
    """A designed project, before its database: five questions, eight planned variables."""
    genre = [("1", "Femme"), ("2", "Homme"), ("3", "Autre"), ("9", "Préfère ne pas répondre")]
    sleep = [
        _planned(f"Q4_SQ00{n}", 2 + n, f"Q4.r{n}", text, "integer", FREQUENCY)
        for n, text in enumerate(
            [
                "vous êtes-vous réveillé·e la nuit ?",
                "avez-vous bien dormi ?",
                "avez-vous eu du mal à vous endormir ?",
            ],
            start=1,
        )
    ]
    found = Project(
        variables=[
            _planned("Q1", 1, "Q1", "Quel est votre genre ?", "integer", genre),
            _planned("Q2", 2, "Q2", "Quel âge avez-vous ?", "integer"),
            *sleep,
            _planned("Q5_1", 6, "Q5.o1", "La lecture", "text", storage="string"),
            _planned("Q5_2", 7, "Q5.o2", "La musique", "text", storage="string"),
            _planned("Q5_other", 8, "Q5.o3", "Autre", "text", storage="string"),
        ],
        groups=[
            Group(
                group_id="G1",
                members=TrackedValue[list[str]](value=[e.name for e in sleep], origin="computed"),
                basis=["designed_questionnaire"],
                descriptive_label=TrackedValue[str](value="3 items", origin="computed"),
                ai_hypothesis=TrackedValue[str](origin="human"),
                kind="scale",
            )
        ],
        questionnaire=questionnaire(),
        design=Design(
            created="2026-10-19", counters={"Q": 5, "Q1.o": 4, "Q4.o": 4, "Q4.r": 3, "S": 2}
        ),
    )
    for entry in sleep:
        entry.group_id = TrackedValue[str](value="G1", origin="computed")
    return found
