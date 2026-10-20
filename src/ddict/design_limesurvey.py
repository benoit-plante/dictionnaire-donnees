"""The designed questionnaire as a file to import into LimeSurvey (v0.20, step E2, D-148):
LimeSurvey's tab-separated structure (`.txt`), written by computation, never by the AI, in
the form LimeSurvey Cloud 7.6 exports it (docs/essais/2026-10-19-limesurvey-fictif.md).

The common trunk only: single choice (buttons, drop-down list), checkboxes with "other",
grid (array), short and long text, number, date, displayed text; required or not; sections
as groups; one language, the study's. No branching, randomisation or quota. What LimeSurvey
does not keep (provenance, reversed items, scoring, instrument) stays in the project, and the
summary says so. A question that would stop the import, or import otherwise than designed,
refuses the writing and sends to the review.
"""

from __future__ import annotations

import contextlib
import html
import re
from dataclasses import dataclass, field
from pathlib import Path

from ddict import design, design_word
from ddict.i18n import N_, Texts, _
from ddict.project.model import Project, Question

SUFFIX = ".txt"
MIME = "text/tab-separated-values"
# LimeSurvey 7.6's theme of each question type, as it gives them on import.
THEMES = {"L": "listradio", "!": "list_dropdown", "M": "multiplechoice", "F": "arrays/array",
          "S": "shortfreetext", "T": "longfreetext", "N": "numerical", "D": "date",
          "X": "boilerplate"}  # fmt: skip


def _words(text: str) -> tuple[str, ...]:
    return tuple(text.split())


# Each type in the words of the page.
TYPE_NAMES = Texts(
    {
        "L": N_("choix unique"),
        "!": N_("liste déroulante"),
        "M": N_("à cocher"),
        "F": N_("grille"),
        "S": N_("texte court"),
        "T": N_("texte long"),
        "N": N_("nombre"),
        "D": N_("date"),
        "X": N_("texte d'affichage"),
    }
)
# The 151 columns of LimeSurvey 7.6's tab-separated export, in its order.
COLUMNS = _words(
    "id related_id class type/scale name relevance text help language validation mandatory "
    "encrypted other default same_default question_theme_name same_script allowed_filetypes "
    "alphasort answer_order answer_width answer_width_bycolumn array_filter array_filter_exclude "
    "array_filter_style assessment_value category_separator choice_input_columns choice_title "
    "commented_checkbox commented_checkbox_auto cssclass date_format date_max date_min "
    "display_columns display_rows display_type dropdown_dates dropdown_dates_minute_step "
    "dropdown_dates_month_style dropdown_prefix dropdown_prepostfix dropdown_separators "
    "dropdown_size dualscale_headerA dualscale_headerB em_validation_q em_validation_q_tip "
    "em_validation_sq em_validation_sq_tip equals_num_value equation exclude_all_others "
    "exclude_all_others_auto hidden hide_tip input_boxes input_size keep_codes_order "
    "label_input_columns location_city location_country location_defaultcoordinates "
    "location_mapheight location_mapservice location_mapwidth location_mapzoom "
    "location_nodefaultfromip location_postal location_state max_answers max_filesize "
    "max_num_of_files max_num_value max_num_value_n max_subquestions maximum_chars min_answers "
    "min_num_of_files min_num_value min_num_value_n multiflexible_checkbox multiflexible_max "
    "multiflexible_min multiflexible_step num_value_int_only numbers_only "
    "other_comment_mandatory other_numbers_only other_replace_text page_break parent_order "
    "placeholder prefix printable_help public_statistics random_group random_order rank_title "
    "repeat_headings reverse samechoiceheight samelistheight scale_export show_comment "
    "show_grand_total show_title show_totals showpopups slider_accuracy slider_custom_handle "
    "slider_default slider_default_set slider_handle slider_layout slider_max "
    "slider_middlestart slider_min slider_orientation slider_rating slider_reset "
    "slider_reversed slider_separator slider_showminmax statistics_graphtype "
    "statistics_showgraph statistics_showmap subquestion_order suffix text_input_columns "
    "text_input_width time_limit time_limit_action time_limit_countdown_message "
    "time_limit_disable_next time_limit_disable_prev time_limit_message "
    "time_limit_message_delay time_limit_message_style time_limit_timer_style "
    "time_limit_warning time_limit_warning_2 time_limit_warning_2_display_time "
    "time_limit_warning_2_message time_limit_warning_2_style time_limit_warning_display_time "
    "time_limit_warning_message time_limit_warning_style use_dropdown value_range_allows_missing"
)
# What LimeSurvey takes as a code. A question's code: letters and digits, a letter first
# (observed: "aides_sommeil" became "aidessommeil"). The lengths, checked on LimeSurvey
# Cloud 7.6 on 2026-10-19: a question's code of 21 characters stops the import with a
# database error; a choice's code of 6 is dropped without a word; options coded by digits
# only ("1") are kept.
QUESTION_CODE = re.compile(r"[A-Za-z][A-Za-z0-9]{0,19}")
ITEM_CODE = re.compile(r"[A-Za-z0-9]{1,20}")
ANSWER_CODE = re.compile(r"[A-Za-z0-9]{1,5}")
# Braces start an expression of LimeSurvey's Expression Manager: a text would be computed.
EXPRESSION = re.compile(r"[{}]")
OTHER_WORDS = {"autre", "other"}  # LimeSurvey's own word for the "other" option


class Unwritable(ValueError):
    """What would stop the import, or import otherwise than designed: nothing was written."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = problems


class FileOpen(Exception):
    def __init__(self, path: Path) -> None:
        super().__init__(path.name)
        self.path = path


@dataclass
class Summary:
    """What the file holds, and what stays in the project."""

    groups: int = 0
    questions: int = 0
    required: int = 0
    subquestions: int = 0  # LimeSurvey's import report counts them apart
    answers: int = 0
    kinds: dict[str, int] = field(default_factory=dict)  # LimeSurvey type -> count
    left: list[str] = field(default_factory=list)  # what LimeSurvey will not have
    problems: list[str] = field(default_factory=list)  # what refuses the writing


def _where(number: int | None, question: Question) -> str:
    if number is None:
        return _("texte d'affichage {id}").format(id=question.question_id)
    return _("question {n}").format(n=number)


def _problems(project: Project, number: int | None, question: Question) -> list[str]:
    where = _where(number, question)
    found = []
    code = design.code(project, question)
    if not QUESTION_CODE.fullmatch(code):
        found.append(
            _(
                "{where} : le code {code} ne convient pas à LimeSurvey (une lettre d'abord, "
                "puis lettres et chiffres, 20 au plus)."
            ).format(where=where, code=code)
        )
    texts = [question.text, question.instruction or ""]
    texts += [o.text for o in question.options] + [r.text for r in question.rows]
    if any(EXPRESSION.search(t) for t in texts):
        found.append(
            _(
                "{where} : une accolade {{ ou }} serait lue par LimeSurvey comme une expression "
                "à calculer ; retirez-la."
            ).format(where=where)
        )
    items = list(question.rows) if question.kind == "grid" else []
    if question.kind == "checkbox":
        items = [o for o in question.options if not o.other]
    answers = []
    if question.kind in ("single", "grid"):
        answers = [o for o in question.options if not o.other]
    for item in items:
        if not item.code or not ITEM_CODE.fullmatch(item.code):
            found.append(
                _(
                    "{where} : l'énoncé ou l'option « {text} » n'a pas un code que LimeSurvey "
                    "accepte (lettres et chiffres, 20 au plus)."
                ).format(where=where, text=item.text)
            )
    for answer in answers:
        if not answer.code or not ANSWER_CODE.fullmatch(answer.code):
            found.append(
                _(
                    "{where} : le choix « {text} » n'a pas un code que LimeSurvey accepte "
                    "(lettres et chiffres, 5 au plus)."
                ).format(where=where, text=answer.text)
            )
    for codes in ([i.code for i in items], [a.code for a in answers]):
        doubles = sorted({c for c in codes if c and codes.count(c) > 1})
        if doubles:
            found.append(
                _("{where} : code en double ({codes}).").format(
                    where=where, codes=", ".join(doubles)
                )
            )
    if question.kind in ("single", "checkbox", "grid") and not answers and not items:
        found.append(_("{where} : aucun choix.").format(where=where))
    if question.kind == "grid" and not items:
        found.append(_("{where} : une grille sans énoncé.").format(where=where))
    return found


def summary(project: Project) -> Summary:
    """What the file would hold, and what refuses it, computed before any writing."""
    found = Summary()
    codes: dict[str, str] = {}
    provenance = 0
    for _section, questions in design_word.numbered(project):
        found.groups += 1
        for item in questions:
            question = item.question
            found.questions += 1
            found.required += question.required
            kind = design.limesurvey_type(question)
            found.kinds[kind] = found.kinds.get(kind, 0) + 1
            found.problems += _problems(project, item.number, question)
            if question.kind == "grid":
                found.subquestions += len(question.rows)
            if question.kind == "checkbox":
                found.subquestions += sum(not o.other for o in question.options)
            if question.kind in ("single", "grid"):
                found.answers += sum(not o.other for o in question.options)
            code = design.code(project, question)
            if code.lower() in codes:  # LimeSurvey compares codes without case
                found.problems.append(
                    _("{where} : même code LimeSurvey que {other} ({code}).").format(
                        where=_where(item.number, question), other=codes[code.lower()],
                        code=code,
                    )
                )  # fmt: skip
            codes.setdefault(code.lower(), _where(item.number, question))
            provenance += question.provenance is not None and question.provenance.kind != "team"
    if not found.questions:
        found.problems.append(_("Le questionnaire n'a aucune question."))
    if provenance:
        found.left.append(
            _("la provenance des textes tirés d'une source (questions : {n})").format(n=provenance)
        )
    designed = [g for g in project.groups if g.question is not None]
    if any(g.reverse_items for g in designed):
        found.left.append(_("les items inversés"))
    if any(g.scoring is not None for g in designed):
        found.left.append(_("la cotation des échelles"))
    if any(g.instrument_name is not None for g in designed):
        found.left.append(_("le nom des instruments et leur source"))
    found.left.append(_("les décisions du dictionnaire (étiquettes, niveaux de mesure, noms)"))
    return found


def _cell(value) -> str:
    """A cell as LimeSurvey's own export writes it: quoted when it holds a space."""
    text = str(value)
    if any(c in text for c in ' "\t'):
        return '"' + text.replace('"', '""') + '"'
    return text


def _html(text: str | None) -> str:
    """LimeSurvey's texts are HTML: the words escaped, a new line a <br />."""
    if not text:
        return ""
    return " <br /> ".join(html.escape(line, quote=False) for line in text.splitlines())


def text(project: Project) -> str:
    """The file, or Unwritable with every problem."""
    found = summary(project)
    if found.problems:
        raise Unwritable(found.problems)
    language = project.settings.language
    lines = ["\t".join(COLUMNS)]

    def row(**cells) -> None:
        line = [""] * len(COLUMNS)
        for key, value in cells.items():
            line[COLUMNS.index(key)] = _cell(value)
        lines.append("\t".join(line))

    title = design.questionnaire(project).file_name
    row(**{"class": "S", "name": "language", "text": language})
    row(**{"class": "SL", "name": "surveyls_title", "text": title, "language": language})
    numbered = design_word.numbered(project)
    # Each group and question has an id, and each group its number in type/scale: without
    # them, LimeSurvey 7.6 merges the groups (the trial of 2026-10-19).
    next_id = len(numbered) + 1
    for rank, (section, questions) in enumerate(numbered, start=1):
        name = section.title or _("Section {n}").format(n=rank)
        row(**{"id": rank, "class": "G", "type/scale": rank, "name": name, "relevance": "1",
               "text": _html(section.instruction), "language": language})  # fmt: skip
        for item in questions:
            question = item.question
            qid, next_id = next_id, next_id + 1
            kind = design.limesurvey_type(question)
            other = next((o for o in question.options if o.other), None)
            cells = {
                "id": qid, "class": "Q", "type/scale": kind,
                "name": design.code(project, question), "relevance": "1",
                "text": _html(question.text), "help": _html(question.instruction),
                "language": language, "mandatory": "Y" if question.required else "N",
                "encrypted": "N", "other": "Y" if other is not None else "N",
                "same_default": "0", "question_theme_name": THEMES[kind], "same_script": "0",
            }  # fmt: skip
            if other is not None and other.text.strip().lower() not in OTHER_WORDS:
                cells["other_replace_text"] = other.text
            row(**cells)
            subquestions = question.rows if question.kind == "grid" else []
            if question.kind == "checkbox":
                subquestions = [o for o in question.options if not o.other]
            for sub in subquestions:
                sid, next_id = next_id, next_id + 1
                row(**{"id": sid, "class": "SQ", "name": sub.code, "relevance": "1",
                       "text": _html(sub.text), "language": language, "mandatory": "N",
                       "other": "N", "same_default": "0", "same_script": "0"})  # fmt: skip
            if question.kind in ("single", "grid"):
                for option in (o for o in question.options if not o.other):
                    row(**{"id": qid, "class": "A", "type/scale": "0", "name": option.code,
                           "text": _html(option.text), "language": language,
                           "assessment_value": "0"})  # fmt: skip
    return "\n".join(lines) + "\n"


def file_name(project: Project) -> str:
    """ "Étude du sommeil - LimeSurvey.txt"."""
    return f"{design_word.stem(project)} - LimeSurvey{SUFFIX}"


def write(project: Project, folder: Path) -> Path:
    """Write the file next to the project, through a temporary file."""
    content = text(project).encode("utf-8")
    path = folder / file_name(project)
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_bytes(content)
        temporary.replace(path)
    except PermissionError as error:
        with contextlib.suppress(OSError):
            temporary.unlink()
        raise FileOpen(path) from error
    return path


def import_steps(project: Project) -> list[str]:
    """The import into LimeSurvey Cloud 7.6, step by step, as done in the trial of
    2026-10-19, and checked by the import of a file the tool wrote, 2026-10-19."""
    found = summary(project)
    return [
        _("Dans LimeSurvey, ouvrez la liste des questionnaires."),
        _("Ouvrez le menu « + », puis choisissez « Importer »."),
        _(
            "Dans « Importer un questionnaire », choisissez le fichier {name} (laissez "
            "« Importer sur le groupe de questionnaires par défaut »)."
        ).format(name=file_name(project)),
        _("Cliquez sur « Importer un questionnaire »."),
        _(
            "Le rapport d'importation doit annoncer {groups} groupes, {questions} questions, "
            "{subquestions} sous-questions et {answers} réponses, sans avertissement. Un "
            "avertissement dit qu'un code a été changé : notez-le, et corrigez-le dans l'outil."
        ).format(
            groups=found.groups,
            questions=found.questions,
            subquestions=found.subquestions,
            answers=found.answers,
        ),
        _(
            "Ouvrez l'aperçu du questionnaire dans LimeSurvey et relisez-le : seul LimeSurvey "
            "montre ce que verront les personnes qui répondent. LimeSurvey ajoute de lui-même "
            "un choix « Sans réponse » aux questions à choix et aux grilles qui ne sont pas "
            "obligatoires."
        ),
    ]
