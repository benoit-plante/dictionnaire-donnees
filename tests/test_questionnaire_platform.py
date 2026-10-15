"""v0.7, step 5: questionnaires of platform exports (docs/plan-v0.7.md, § 3.5).

The layouts below copy the shapes of lines seen in two real SurveyMonkey PDFs (indentation,
cells, final punctuation), with invented words: numbered questions, column titles stacked
over three lines, grids going on over the next page without their titles, rows that are
questions, long options.
"""

from pathlib import Path

import pytest

from ddict.io import read_database
from ddict.project import build_project
from ddict.project.model import QuestionnaireText
from ddict.questionnaire import link
from ddict.questionnaire.read import Line
from ddict.questionnaire.segment import segment
from ddict.workflow import add_questionnaire, platform_summary, questionnaire_summary

EXAMPLES = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"


def pdf(*rows: tuple) -> list[Line]:
    """Lines of a PDF: (page, indent, text) or (page, [(position, text), ...])."""
    lines = []
    for row in rows:
        if isinstance(row[1], list):
            page, cells = row
            lines.append(Line(page, cells[0][0], tuple(cells)))
        else:
            page, indent, text = row
            lines.append(Line(page, indent, ((indent, text),)))
    return lines


def text_file(*texts: str) -> list[Line]:
    """Lines of a text file; "" is a blank line, tabs separate cells."""
    lines, blank = [], False
    for text in texts:
        if not text:
            blank = True
            continue
        cells = tuple((k, c) for k, c in enumerate(text.split("\t")) if c)
        lines.append(Line(None, 0, cells, after_blank=blank))
        blank = False
    return lines


def kinds(lines: list[Line], use_indent: bool) -> list[tuple[str, int, int]]:
    questions, _texts = segment(lines, use_indent=use_indent)
    return [(q.kind, len(q.rows), len(q.options)) for q in questions]


# --- Numbered questions. ---


def test_numbered_questions_in_a_text_file():
    lines = text_file(
        "Une étude fictive.",
        "",
        "1. Dans quel secteur travaillez-vous ?",
        "Commerce",
        "Industrie",
        "",
        "2) Décrivez votre poste.",
        "",
        "3. Quelles langues parlez-vous ? (Cochez toutes les réponses qui s'appliquent)",
        "Français",
        "Anglais",
    )
    questions, texts = segment(lines, use_indent=False)
    assert [(q.kind, q.text) for q in questions] == [
        ("single", "Dans quel secteur travaillez-vous ?"),
        ("open", "Décrivez votre poste."),
        ("checkbox", "Quelles langues parlez-vous ? (Cochez toutes les réponses qui s'appliquent)"),
    ]
    assert [t.text for t in texts] == ["Une étude fictive."]


def test_numbered_questions_in_a_pdf():
    # As in a real export: numbered questions, indented options, an open question in between.
    lines = pdf(
        (1, 0, "Merci de participer à cette étude fictive !"),
        (2, 3, "1. Avez-vous un emploi ?"),
        (2, 10, "Oui"),
        (2, 10, "Non"),
        (2, 0, "2. Pourquoi avez-vous choisi ce domaine ?"),
        (2, 3, "3. Combien d'heures travaillez-vous ?"),
        (2, 10, "Moins de 20"),
        (2, 10, "20 ou plus"),
    )
    assert kinds(lines, True) == [("single", 0, 2), ("open", 0, 0), ("single", 0, 2)]


def test_questions_numbered_with_q():
    lines = text_file("Q1. Votre âge ?", "", "Q2. Votre ville ?")
    questions, _texts = segment(lines, use_indent=False)
    assert [q.text for q in questions] == ["Votre âge ?", "Votre ville ?"]


def test_a_numbered_grid_alone_stays_a_grid():
    lines = text_file(
        "À quelle fréquence… ?",
        "\tJamais\tSouvent\tToujours",
        "1. Je dors bien.",
        "2. Je me réveille tôt.",
        "3. Je fais la sieste.",
        "4. Je rêve.",
    )
    assert kinds(lines, False) == [("grid", 4, 3)]


# --- Questions worded as instructions. ---


def test_instruction_questions():
    lines = pdf(
        (1, 0, "Cochez les consignes que vous avez reçues."),
        (1, 3, "Plan d'évacuation"),
        (1, 3, "Premiers soins"),
        (1, 0, "Décrivez une situation récente."),
        (1, 0, "Coche les moyens de transport que tu utilises."),
        (1, 3, "Vélo"),
        (1, 3, "Marche"),
    )
    assert kinds(lines, True) == [("checkbox", 0, 2), ("open", 0, 0), ("checkbox", 0, 2)]


def test_an_instruction_followed_by_a_paragraph_is_a_paragraph():
    lines = pdf(
        (1, 0, "Indiquez votre accord en signant le formulaire."),
        (1, 0, "Le formulaire est conservé par l'équipe pendant cinq ans."),
    )
    questions, texts = segment(lines, use_indent=True)
    assert questions == [] and len(texts) == 2


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("Cochez les activités que vous pratiquez.", "checkbox"),
        ("Coche tous les sports que tu pratiques.", "checkbox"),
        ("Tick all that apply.", "checkbox"),
        ("Cochez la case qui correspond le mieux.", "single"),
        ("Cochez une seule réponse.", "single"),
    ],
)
def test_checkboxes_by_their_wording(text, kind):
    lines = pdf((1, 0, text), (1, 3, "Une option"), (1, 3, "Une autre"))
    assert kinds(lines, True)[0][0] == kind


# --- Grids of SurveyMonkey's PDF. ---

STACKED_TITLES = (
    (1, 101, "Préfère"),
    (1, 101, "ne pas"),
    (1, [(30, "Très"), (45, "Plutôt"), (60, "Ni l'un"), (75, "Plutôt"), (90, "Très"),
         (101, "répondre")]),
)  # fmt: skip


def test_column_titles_stacked_over_three_lines():
    lines = pdf(
        (1, 0, "Indiquez votre satisfaction à l'égard des aspects suivants."),
        *STACKED_TITLES,
        (1, 1, "L'éclairage."),
        (1, 1, "Le bruit."),
    )
    questions, _texts = segment(lines, use_indent=True)
    (grid,) = questions
    assert grid.kind == "grid" and [r.text for r in grid.rows] == ["L'éclairage.", "Le bruit."]
    assert [o.text for o in grid.options][-1] == "Préfère ne pas répondre"


def test_the_top_of_a_title_is_no_question():
    # The top of the first title, alone far to the right, made a false question (real PDF).
    lines = pdf(
        (1, 0, "Pour chaque énoncé, indiquez votre accord."),
        (1, 122, "Préfère ne"),
        (1, 126, "pas"),
        (1, [(31, "Pas du tout"), (62, "Un peu"), (92, "Beaucoup"), (122, "répondre")]),
        (1, 1, "Êtes-vous satisfait·e de l'éclairage ?"),
        (1, 1, "Êtes-vous satisfait·e du bruit ?"),
        (1, 1, "Êtes-vous satisfait·e de la température ?"),
    )
    assert kinds(lines, True) == [("grid", 3, 4)]


def test_rows_that_are_questions_stay_rows():
    lines = pdf(
        (1, 0, "Dans quelle mesure êtes-vous satisfait·e de votre milieu ?"),
        (1, [(60, "Peu"), (80, "Assez"), (100, "Très")]),
        (1, 0, "Êtes-vous satisfait·e de l'éclairage ?"),
        (1, 0, "Êtes-vous satisfait·e du bruit ?"),
        (2, 0, "Quelles tâches faites-vous ?"),
        (2, 3, "Accueil"),
        (2, 3, "Manutention"),
    )
    assert kinds(lines, True) == [("grid", 2, 3), ("single", 0, 2)]


def test_a_section_title_under_columns_is_not_a_row():
    lines = pdf(
        (1, 0, "Comment allez-vous ?"),
        (1, [(60, "Mal"), (80, "Bien")]),
        (1, 0, "Votre travail"),
        (1, 0, "Combien d'heures travaillez-vous ?"),
    )
    assert kinds(lines, True) == [("single", 0, 2), ("open", 0, 0)]


def test_a_grid_goes_on_over_the_next_page():
    lines = pdf(
        (1, 0, "À quelle fréquence avez-vous vécu ces situations ?"),
        (1, [(60, "Jamais"), (80, "Parfois"), (100, "Souvent")]),
        (1, 1, "J'ai eu trop de travail."),
        (1, 1, "J'ai manqué de temps pour"),
        (2, 0, "mes pauses."),  # a row cut by the page
        (2, 0, "J'ai été interrompu·e."),
        (2, 0, "J'ai reçu des consignes contradictoires."),
        (2, 0, "Les questions suivantes portent sur votre santé."),  # the next one's
        (2, 0, "Comment est votre santé :"),
        (2, 9, "Bonne"),
        (2, 9, "Mauvaise"),
    )
    questions, texts = segment(lines, use_indent=True)
    grid = questions[0]
    assert [r.text for r in grid.rows] == [
        "J'ai eu trop de travail.",
        "J'ai manqué de temps pour mes pauses.",
        "J'ai été interrompu·e.",
        "J'ai reçu des consignes contradictoires.",
    ]
    assert [t.text for t in texts] == ["Les questions suivantes portent sur votre santé."]
    assert kinds(lines, True)[1] == ("single", 0, 2)


def test_long_options_aligned_with_the_others():
    long = "Une option qui dit en détail une situation précise, " * 3
    lines = pdf(
        (1, 0, "1. Cochez les situations vécues :"),
        (1, 7, "Une option courte."),
        (1, 7, long.strip()),
        (1, 7, "Autre (veuillez préciser)"),
        (1, 0, "2. Votre âge ?"),
        (1, 0, "3. Votre ville ?"),
    )
    assert kinds(lines, True)[0] == ("checkbox", 0, 3)


# --- Checked against the structure of the export. ---


def _project(questionnaire: str):
    project = build_project(read_database(EXAMPLES / "travail-t2_surveymonkey.sav"))
    add_questionnaire(project, EXAMPLES / questionnaire)
    return project


@pytest.mark.parametrize(
    "file_name",
    [
        "questionnaire-travail.pdf",
        "questionnaire-travail-numerote.pdf",
        "questionnaire-travail.txt",
        "travail-t2_surveymonkey.xlsx",
    ],
)
def test_a_questionnaire_that_agrees_with_the_export(file_name):
    project = _project(file_name)
    assert link.platform_coverage(project) == (11, 0)  # "id" asks nothing
    assert all(not q.to_check or q.to_check == ["grid_rows_unnumbered"]
               for q in project.questionnaire.questions)  # fmt: skip
    assert platform_summary(project) == [
        "Structure de l'export SurveyMonkey : 11 questions, toutes retrouvées dans ce "
        "questionnaire."
    ]


def test_what_the_structure_says_about_a_questionnaire():
    project = _project("questionnaire-travail.pdf")
    questions = project.questionnaire.questions
    del questions[2].rows[-1]  # a row lost by the reading
    questions[9].kind = "single"  # checkboxes read as a single choice
    questions[9].options = questions[9].options[:-2]
    del questions[5]  # a question not found
    link.check_against_platform(project)
    assert "platform_rows_differ" in questions[2].to_check
    checkbox = questions[8]
    assert checkbox.kind == "checkbox"
    assert {"kind_from_platform", "platform_options_differ"} <= set(checkbox.to_check)
    assert link.platform_coverage(project) == (11, 1)
    assert platform_summary(project) == [
        "Structure de l'export SurveyMonkey : 11 questions, dont 1 sans question concordante "
        "dans ce questionnaire."
    ]
    lines = questionnaire_summary(project.questionnaire)
    assert any("pas le même nombre d'énoncés que dans la base" in line for line in lines)
    # Checked again, the same codes, not twice.
    link.check_against_platform(project)
    assert questions[2].to_check.count("platform_rows_differ") == 1


def test_no_check_without_a_platform():
    project = build_project(read_database(EXAMPLES / "etude-sommeil.sav"))
    add_questionnaire(project, EXAMPLES / "questionnaire-sommeil.pdf")
    assert platform_summary(project) == []
    codes = {c for q in project.questionnaire.questions for c in q.to_check}
    assert not codes & set(link.PLATFORM_CHECKS)


def test_the_instructions_of_the_next_grid_are_not_a_row():
    # A real PDF: a grid going on over the page, then the next grid's instructions and its
    # column titles; those instructions are not a last row of the first grid.
    lines = pdf(
        (1, 0, "À quelle fréquence avez-vous vécu ces situations ?"),
        (1, [(60, "Jamais"), (80, "Parfois"), (100, "Souvent")]),
        (1, 1, "J'ai eu trop de travail."),
        (1, 1, "J'ai manqué de temps."),
        (2, 0, "J'ai été interrompu·e."),
        (3, 0, "Les énoncés suivants portent sur votre équipe."),
        (3, 0, "Indiquez votre accord avec chacun."),
        (3, [(60, "Pas du tout"), (80, "Un peu"), (100, "Beaucoup")]),
        (3, 1, "Mon équipe m'aide."),
        (3, 1, "Mon équipe m'écoute."),
    )
    questions, _texts = segment(lines, use_indent=True)
    assert [len(q.rows) for q in questions] == [3, 2]


def test_the_structure_finds_what_the_layout_hides():
    project = _project("questionnaire-travail.pdf")
    questionnaire = project.questionnaire
    # As in a real PDF: an open question without "?" read as a paragraph, and the last
    # row of a grid read as the paragraph before the next question.
    situation = next(q for q in questionnaire.questions if q.text.startswith("Décrivez"))
    questionnaire.questions.remove(situation)
    questionnaire.texts.append(QuestionnaireText(page=situation.page, text=situation.text))
    grid = questionnaire.questions[2]
    last = grid.rows.pop()
    questionnaire.texts.append(QuestionnaireText(page=grid.page, text=last.text))
    link.check_against_platform(project)
    found = next(q for q in questionnaire.questions if q.text == situation.text)
    assert found.kind == "open" and found.to_check == ["found_by_platform"]
    assert [q.question_id for q in questionnaire.questions] == [
        f"Q{k}" for k in range(1, len(questionnaire.questions) + 1)
    ]
    assert grid.rows[-1].text == last.text and "found_by_platform" in grid.to_check
    assert grid.rows[-1].row_id == f"{grid.question_id}.r{len(grid.rows)}"
    assert link.platform_coverage(project) == (11, 0)
    assert link.platform_choices(project)["q0009"] == found.question_id


def test_no_repair_without_an_agreeing_paragraph():
    project = _project("questionnaire-travail.pdf")
    questionnaire = project.questionnaire
    removed = questionnaire.questions.pop(8)  # gone, and no paragraph says it
    link.check_against_platform(project)
    assert all(q.text != removed.text for q in questionnaire.questions)
    assert link.platform_coverage(project) == (11, 1)
