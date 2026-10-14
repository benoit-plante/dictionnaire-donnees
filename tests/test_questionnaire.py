"""v0.2, step 2: reading a questionnaire and cutting it into questions (no model)."""

import json

import pytest

from ddict.cli import main
from ddict.io import ReadError
from ddict.project import load_project
from ddict.questionnaire import Line, load_questionnaire, segment
from ddict.questionnaire.read import normalize

FORMATS = ["questionnaire-sommeil.pdf", "questionnaire-sommeil.txt"]


def _expected(generator):
    """The questions of the generator, in reading order, as the tool should find them."""
    found = []
    for page, elements in enumerate(generator.QUESTIONNAIRE, start=1):
        for kind, *content in elements:
            if kind == "question":
                text, options, _names = content
                found.append((page, text, "single" if options else "open", options, []))
            elif kind == "checkbox":
                text, options = content
                found.append((page, text, "checkbox", [o for o, _n in options], []))
            elif kind == "grid":
                text, options, rows = content
                found.append((page, text, "grid", options, [r for r, _n in rows]))
    return found


@pytest.fixture(scope="module", params=FORMATS)
def read(request, fictional_files):
    return request.param, load_questionnaire(fictional_files[request.param])


def test_every_question_of_the_fictional_questionnaire(read, generator):
    name, questionnaire = read
    expected = _expected(generator)
    assert len(questionnaire.questions) == len(expected) == 14
    for number, (question, (page, text, kind, options, rows)) in enumerate(
        zip(questionnaire.questions, expected, strict=True), start=1
    ):
        assert question.question_id == f"Q{number}"
        assert (question.text, question.kind) == (text, kind)
        assert [r.text for r in question.rows] == rows
        assert question.page == (page if name.endswith(".pdf") else None)
        if question.question_id != "Q7" or name.endswith(".txt"):
            assert [o.text for o in question.options] == options, question.question_id


def test_question_ranks_match_the_answer_key(read, generator):
    """The tool numbers questions as the key of step 4 expects (Q7 = sleep grid, ...)."""
    _name, questionnaire = read
    kinds = {q.question_id: q.kind for q in questionnaire.questions}
    for variable, (_page, rank, row) in generator.questionnaire_key().items():
        question = questionnaire.questions[rank - 1]
        if row is None:
            assert kinds[question.question_id] in ("open", "single"), variable
        else:
            assert len(question.rows or question.options) >= row, variable


def test_glued_column_titles_are_flagged_not_guessed(fictional_files):
    pdf = load_questionnaire(fictional_files["questionnaire-sommeil.pdf"])
    txt = load_questionnaire(fictional_files["questionnaire-sommeil.txt"])
    assert pdf.questions[6].to_check == ["grid_header_unclear"]
    assert "MoyennementBeaucoup" in [o.text for o in pdf.questions[6].options]
    assert txt.questions[6].to_check == []
    assert [o.text for o in pdf.questions[11].options][-1] == "Presque toujours"  # two lines


def test_consent_page_stays_a_paragraph(read, generator):
    _name, questionnaire = read
    canary = generator.CANARY_CONSENT
    assert any(canary in t.text for t in questionnaire.texts)
    assert not any(canary in q.text for q in questionnaire.questions)


def test_identity_of_the_file(read, fictional_files):
    name, questionnaire = read
    assert (questionnaire.file_name, questionnaire.format) == (name, name[-3:])
    assert questionnaire.n_pages == (4 if name.endswith(".pdf") else None)
    assert len(questionnaire.sha256) == 64


def test_normalize():
    assert normalize("Identiﬁez  vos\N{NO-BREAK SPACE}besoins ") == "Identifiez vos besoins"


# --- Layouts found in a real SurveyMonkey export, written as lines. ---


def _pdf(*rows, page=1):
    """Lines as pypdf's layout mode gives them: (indent, cell, cell, ...)."""
    lines = []
    for row in rows:
        indent, *cells = row
        position, placed = indent, []
        for cell in cells:
            placed.append((position, cell))
            position += len(cell) + 4
        lines.append(Line(page=page, indent=indent, cells=tuple(placed)))
    return lines


def _cut(lines, use_indent=True):
    questions, texts = segment(lines, use_indent=use_indent)
    return questions, [t.text for t in texts]


def test_question_without_mark_after_an_open_question():
    questions, _texts = _cut(
        _pdf(
            (0, "Quel est votre âge ? (en année)"),
            (3, "Sexe de l'enfant"),
            (9, "Garçon"),
            (9, "Fille"),
        )
    )
    assert [(q.text, q.kind, len(q.options)) for q in questions] == [
        ("Quel est votre âge ? (en année)", "open", 0),
        ("Sexe de l'enfant", "single", 2),
    ]


def test_input_fields_are_not_questions():
    questions, _texts = _cut(
        _pdf(
            (0, "Si applicable, date d'union avec l'autre parent :"),
            (0, "Date"),
            (1, "JJ/MM/AAAA"),
            (3, "Êtes-vous séparé(e) ?"),
            (10, "Oui"),
            (10, "Non"),
        )
    )
    assert [(q.text, q.kind) for q in questions] == [
        ("Si applicable, date d'union avec l'autre parent :", "open"),
        ("Êtes-vous séparé(e) ?", "single"),
    ]


def test_column_titles_over_two_lines_make_one_scale():
    lines = [
        Line(1, 0, ((0, "Êtes-vous satisfait·e du soutien reçu ?"),)),
        Line(1, 5, ((5, "Vraiment"), (40, "Un peu"), (75, "Vraiment"))),
        Line(
            1,
            4,
            (
                (4, "insatisfait·e"),
                (24, "Assez insatisfait·e"),
                (39, "insatisfait·e"),
                (57, "Un peu satisfait·e"),
                (65, "Assez satisfait·e"),
                (74, "satisfait·e"),
            ),
        ),
    ]
    (question,), _texts = _cut(lines)
    assert question.kind == "single"
    assert [o.text for o in question.options] == [
        "Vraiment insatisfait·e",
        "Assez insatisfait·e",
        "Un peu insatisfait·e",
        "Un peu satisfait·e",
        "Assez satisfait·e",
        "Vraiment satisfait·e",
    ]


def test_matrix_introduced_by_instructions_with_ellipsis_rows():
    lines = [
        Line(1, 0, ((0, "Les questions suivantes portent sur les 30 derniers jours."),)),
        Line(1, 0, ((0, "Combien de fois avez-vous eu le sentiment..."),)),
        Line(1, 83, ((83, "La plupart du"),)),
        Line(1, 29, ((29, "Jamais"), (40, "Rarement"), (52, "Parfois"), (83, "temps"))),
        Line(1, 1, ((1, "...d'être"),)),
        Line(1, 1, ((1, "nerveux/nerveuse?"),)),
        Line(1, 1, ((1, "...d'être désespéré·e"),)),
        Line(1, 1, ((1, "?"),)),
    ]
    (question,), texts = _cut(lines)
    assert question.kind == "grid" and texts == []
    assert question.text.startswith("Les questions suivantes")
    assert [o.text for o in question.options][-1] == "La plupart du temps"
    assert [r.text for r in question.rows] == [
        "...d'être nerveux/nerveuse?",
        "...d'être désespéré·e ?",
    ]
    assert question.to_check == []


def test_unnumbered_statements_are_flagged():
    lines = [
        Line(1, 0, ((0, "Cochez la case qui correspond le mieux à votre vécu."),)),
        Line(1, 32, ((32, "Jamais"), (45, "Parfois"), (60, "Souvent"))),
        Line(1, 1, ((1, "Je me suis senti·e"),)),
        Line(1, 1, ((1, "optimiste."),)),
        Line(1, 1, ((1, "Je me suis senti·e utile."),)),
    ]
    (question,), _texts = _cut(lines)
    assert [r.text for r in question.rows] == [
        "Je me suis senti·e optimiste.",
        "Je me suis senti·e utile.",
    ]
    assert question.to_check == ["grid_rows_unnumbered"]


def test_a_section_title_after_a_scale_is_not_a_row():
    questions, texts = _cut(
        _pdf(
            (0, "Avez-vous besoin d'aide ?"),
            (6, "Pas du tout", "Un peu", "Souvent"),
            (0, "Parentalité (le fait de s'occuper d'un enfant)"),
            (0, "Avez-vous besoin d'aide avec votre parentalité ?"),
            (6, "Pas du tout", "Un peu", "Souvent"),
        )
    )
    assert [(q.kind, len(q.rows), len(q.options)) for q in questions] == [("single", 0, 3)] * 2
    assert texts == ["Parentalité (le fait de s'occuper d'un enfant)"]


def test_numbered_grid_goes_on_over_the_next_page():
    lines = [
        *_pdf(
            (0, "Pour chaque item, cochez une case."),
            (40, "0", "1", "2"),
            (1, "8. Ne peut pas"),
            (1, "attendre."),
            (1, "10. S'accroche aux adultes."),
        ),
        *_pdf((1, "43. A l'air malheureux."), (1, "44. Humeur colérique."), page=2),
    ]
    (question,), texts = _cut(lines)
    assert [r.number for r in question.rows] == [8, 10, 43, 44]
    assert question.rows[0].text == "Ne peut pas attendre."
    assert texts == []


def test_abbreviation_does_not_end_a_line():
    (question,), _texts = _cut(
        _pdf(
            (0, "Avez-vous besoin d'aide pour les activités domestiques (ex."),
            (0, "ménage, repas) ?"),
            (6, "Oui"),
            (6, "Non"),
        )
    )
    assert question.text == (
        "Avez-vous besoin d'aide pour les activités domestiques (ex. ménage, repas) ?"
    )


def test_text_file_question_without_mark_only_starts_a_paragraph():
    lines = [
        Line(None, 0, ((0, "Langue maternelle"),), after_blank=True),
        Line(None, 0, ((0, "Français"),)),
        Line(None, 0, ((0, "Anglais"),)),
        Line(None, 0, ((0, "Autre (précisez) :"),)),
    ]
    (question,), _texts = _cut(lines, use_indent=False)
    assert [o.text for o in question.options] == ["Français", "Anglais", "Autre (précisez) :"]


# --- Command line. ---


@pytest.fixture
def project_path(fictional_files, tmp_path):
    path = tmp_path / "etude.dd.json"
    main(["profiler", str(fictional_files["etude-sommeil.sav"]), "-o", str(path)])
    return path


def test_command_adds_the_questionnaire(project_path, fictional_files, capsys):
    capsys.readouterr()
    assert main(["questionnaire", str(project_path), str(fictional_files[FORMATS[0]])]) == 0
    out = capsys.readouterr().out
    assert "14 questions" in out and "À vérifier : Q7" in out
    project = load_project(project_path)
    assert project.questionnaire.file_name == FORMATS[0]
    assert len(project.questionnaire.questions) == 14
    assert json.loads(project_path.read_text(encoding="utf-8"))["questionnaire"]["format"] == "pdf"


def test_command_keeps_a_questionnaire_unless_asked(project_path, fictional_files, capsys):
    main(["questionnaire", str(project_path), str(fictional_files[FORMATS[0]])])
    assert main(["questionnaire", str(project_path), str(fictional_files[FORMATS[1]])]) == 2
    assert "--remplacer" in capsys.readouterr().err
    assert load_project(project_path).questionnaire.format == "pdf"
    args = ["questionnaire", str(project_path), str(fictional_files[FORMATS[1]]), "--remplacer"]
    assert main(args) == 0
    assert load_project(project_path).questionnaire.format == "txt"


def test_unreadable_questionnaires(project_path, tmp_path, capsys):
    broken = tmp_path / "abime.pdf"
    broken.write_bytes(b"%PDF-1.4 rien d'autre")
    assert main(["questionnaire", str(project_path), str(broken)]) == 2
    assert "Impossible de lire le questionnaire" in capsys.readouterr().err
    with pytest.raises(ReadError, match="format"):
        load_questionnaire(tmp_path / "questionnaire.docx")
    assert load_project(project_path).questionnaire is None


def test_a_label_followed_by_a_date_field_is_a_question():
    questions, texts = _cut(
        _pdf(
            (0, "Année/Mois d'arrivée au Canada (si applicable)"),
            (0, "Année/Mois"),
            (0, "Date"),
            (1, "JJ/MM/AAAA"),
        )
    )
    assert [(q.text, q.kind) for q in questions] == [
        ("Année/Mois d'arrivée au Canada (si applicable)", "open")
    ]
    assert texts == []


def test_an_open_parenthesis_goes_on_over_the_next_line():
    (question,), _texts = _cut(
        _pdf(
            (0, "Ces services vous ont-ils été utiles ? (0 = Pas du tout / 10 ="),
            (0, "Très utile)"),
            (6, "0", "1", "2"),
        )
    )
    assert question.text.endswith("(0 = Pas du tout / 10 = Très utile)")
    assert [o.text for o in question.options] == ["0", "1", "2"]
