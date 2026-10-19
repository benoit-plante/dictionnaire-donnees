"""Write the fictional LimeSurvey survey of the tests (v0.20, D-148): its structure as
LimeSurvey Cloud 7.6 exports it, in its two forms, `.lss` (XML) and the tab-separated `.txt`.

The forms are those seen on 2026-10-19, when this very survey was imported into LimeSurvey 7.6,
exported again and filled with invented responses (`docs/essais/2026-10-19-limesurvey-fictif.md`).
The real exports stay off the repository (they carry the administrator's address); this script
writes the same structure with a fictional administrator. Nothing real; no randomness: two runs
write the same bytes.

Run: uv run python scripts/generer_limesurvey_fictif.py [folder]
(default: exemples/bases-fictives/)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "exemples" / "bases-fictives"
STEM = "questionnaire-limesurvey"
SID = "111111"
DB_VERSION = "717"
LANGUAGE = "fr"
TITLE = "Étude fictive du sommeil (LimeSurvey)"
ADMIN, ADMIN_EMAIL = "Équipe fictive", "equipe@example.org"

# (code, LimeSurvey type, text, help, mandatory, other, subquestions, answers)
GROUPS = [
    (
        "Vous",
        [
            ("genre", "L", "Quel est votre genre ?", "", "Y", "Y", [],
             [("1", "Femme"), ("2", "Homme"), ("9", "Préfère ne pas répondre")]),
            ("age", "N", "Quel âge avez-vous ?", "", "N", "N", [], []),
            ("region", "!", "Dans quelle région habitez-vous ?", "", "N", "N", [],
             [("1", "Estrie"), ("2", "Mauricie"), ("3", "Outaouais")]),
            ("journal", "D", "À quelle date avez-vous rempli le journal du sommeil ?", "", "N",
             "N", [], []),
            ("profession", "S", "Quelle est votre profession ?", "", "N", "N", [], []),
        ],
    ),
    (
        "Votre sommeil",
        [
            ("intro", "X", "Les questions suivantes portent sur votre sommeil.", "", "N", "N",
             [], []),
            ("sommeil", "F", "Au cours du dernier mois, à quelle fréquence…",
             "Cochez une case par ligne.", "N", "N",
             [("SQ001", "vous êtes-vous réveillé·e la nuit ?"),
              ("SQ002", "avez-vous bien dormi ?"),
              ("SQ003", "avez-vous eu du mal à vous endormir ?")],
             [("1", "Jamais"), ("2", "Parfois"), ("3", "Souvent"), ("4", "Toujours")]),
            ("aides", "M", "Qu'est-ce qui vous aide à dormir ?", "", "N", "Y",
             [("SQ001", "La lecture"), ("SQ002", "La musique")], []),
            ("nuit", "T", "Décrivez une nuit difficile.", "", "N", "N", [], []),
        ],
    ),
]  # fmt: skip
THEMES = {"L": "listradio", "!": "list_dropdown", "M": "multiplechoice", "F": "arrays/array",
          "S": "shortfreetext", "T": "longfreetext", "N": "numerical", "D": "date",
          "X": "boilerplate"}  # fmt: skip


def _names(text: str) -> list[str]:
    return text.split()


# The 151 columns of LimeSurvey 7.6's tab-separated export, in its order.
TSV_COLUMNS = _names(
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
QUESTION_FIELDS = _names("qid parent_qid sid gid type title preg other mandatory encrypted "
                   "question_order scale_id same_default relevance question_theme_name "
                   "modulename same_script")  # fmt: skip


def _structure():
    """Groups, questions, subquestions and answers with ids as LimeSurvey numbers them on
    import: questions first, then subquestions; the order within a group counts both."""
    groups, questions, subquestions, answers = [], [], [], []
    qid, aid = 659, 677
    pending = []
    for gid, (name, items) in enumerate(GROUPS, start=52):
        groups.append((str(gid), len(groups) + 1, name))
        order = 0
        for code, kind, text, help_text, mandatory, other, subs, choices in items:
            questions.append(dict(qid=str(qid), gid=str(gid), type=kind, title=code,
                                  other=other, mandatory=mandatory, order=order, text=text,
                                  help=help_text))  # fmt: skip
            order += 1
            for sortorder, (answer_code, label) in enumerate(choices, start=1):
                answers.append((str(aid), str(qid), answer_code, sortorder, label))
                aid += 1
            for sub_code, label in subs:
                pending.append((str(qid), str(gid), kind, sub_code, order, label))
                order += 1
            qid += 1
    for parent, gid, kind, sub_code, order, label in pending:
        subquestions.append(dict(qid=str(qid), parent=parent, gid=gid, type=kind,
                                 title=sub_code, order=order, text=label))  # fmt: skip
        qid += 1
    return groups, questions, subquestions, answers


def _cdata(value) -> str:
    return f"<![CDATA[{value}]]>"


def _table(name: str, fields: list[str], rows: list[dict]) -> list[str]:
    lines = [f" <{name}>", "  <fields>"]
    lines += [f"   <fieldname>{f}</fieldname>" for f in fields]
    lines += ["  </fields>", "  <rows>"]
    for row in rows:
        lines.append("   <row>")
        for f in fields:
            if row.get(f) is not None:
                lines.append(f"    <{f}>{_cdata(row[f])}</{f}>")
        lines.append("   </row>")
    lines += ["  </rows>", f" </{name}>"]
    return lines


def lss_text() -> str:
    groups, questions, subquestions, answers = _structure()
    sorted_answers = sorted(answers, key=lambda a: (a[3], a[1]))  # LimeSurvey's order
    question_rows = [
        dict(qid=q["qid"], parent_qid="0", sid=SID, gid=q["gid"], type=q["type"],
             title=q["title"], preg="", other=q["other"], mandatory=q["mandatory"],
             encrypted="N", question_order=q["order"], scale_id="0", same_default="0",
             relevance="1", question_theme_name=THEMES[q["type"]], modulename="",
             same_script="0")
        for q in questions
    ]  # fmt: skip
    sub_rows = [
        dict(qid=s["qid"], parent_qid=s["parent"], sid=SID, gid=s["gid"], type=s["type"],
             title=s["title"], preg="", other="N", mandatory="N", encrypted="N",
             question_order=s["order"], scale_id="0", same_default="0", relevance="1",
             modulename="", same_script="0")
        for s in subquestions
    ]  # fmt: skip
    texts = [(q["qid"], q["text"], q["help"]) for q in questions]
    texts += [(s["qid"], s["text"], "") for s in subquestions]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<document>",
             " <LimeSurveyDocType>Survey</LimeSurveyDocType>",
             f" <DBVersion>{DB_VERSION}</DBVersion>", " <languages>",
             f"  <language>{LANGUAGE}</language>", " </languages>"]  # fmt: skip
    lines += _table(
        "answers",
        ["aid", "qid", "code", "sortorder", "assessment_value", "scale_id"],
        [dict(aid=a, qid=q, code=c, sortorder=o, assessment_value="0", scale_id="0")
         for a, q, c, o, _l in sorted_answers],
    )  # fmt: skip
    lines += _table(
        "answer_l10ns",
        ["id", "aid", "answer", "language"],
        [dict(id=a, aid=a, answer=label, language=LANGUAGE)
         for a, _q, _c, _o, label in sorted_answers],
    )  # fmt: skip
    lines += _table(
        "groups",
        ["gid", "sid", "group_order", "randomization_group", "grelevance"],
        [dict(gid=g, sid=SID, group_order=o, randomization_group="", grelevance="1")
         for g, o, _n in groups],
    )  # fmt: skip
    lines += _table(
        "group_l10ns",
        ["id", "gid", "group_name", "description", "language", "sid", "group_order",
         "randomization_group", "grelevance"],
        [dict(id=g, gid=g, group_name=n, description="", language=LANGUAGE, sid=SID,
              group_order=o, randomization_group="", grelevance="1") for g, o, n in groups],
    )  # fmt: skip
    lines += _table("questions", QUESTION_FIELDS, question_rows)
    lines += _table("subquestions", QUESTION_FIELDS, sub_rows)
    lines += _table(
        "question_l10ns",
        ["id", "qid", "question", "help", "script", "language"],
        [dict(id=str(int(q) + 1), qid=q, question=t, help=h, script="", language=LANGUAGE)
         for q, t, h in texts],
    )  # fmt: skip
    lines += _table(
        "surveys",
        ["sid", "gsid", "admin", "adminemail", "language"],
        [dict(sid=SID, gsid="1", admin=ADMIN, adminemail=ADMIN_EMAIL, language=LANGUAGE)],
    )
    lines += _table(
        "surveys_languagesettings",
        ["surveyls_survey_id", "surveyls_language", "surveyls_title"],
        [dict(surveyls_survey_id=SID, surveyls_language=LANGUAGE, surveyls_title=TITLE)],
    )
    lines.append("</document>")
    return "\n".join(lines) + "\n"


def _cell(value) -> str:
    text = str(value)
    return f'"{text}"' if " " in text else text


def tsv_text() -> str:
    groups, questions, subquestions, answers = _structure()

    def row(**cells) -> str:
        line = [""] * len(TSV_COLUMNS)
        for key, value in cells.items():
            line[TSV_COLUMNS.index(key)] = _cell(value)
        return "\t".join(line)

    lines = ["\t".join(TSV_COLUMNS)]
    lines.append(row(**{"class": "S", "name": "sid", "text": SID}))
    lines.append(row(**{"class": "S", "name": "admin", "text": ADMIN}))
    lines.append(row(**{"class": "S", "name": "adminemail", "text": ADMIN_EMAIL}))
    lines.append(row(**{"class": "S", "name": "language", "text": LANGUAGE}))
    lines.append(row(**{"class": "SL", "name": "surveyls_title", "text": TITLE,
                        "language": LANGUAGE}))  # fmt: skip
    for gid, order, name in groups:
        lines.append(row(**{"id": gid, "class": "G", "type/scale": order, "name": name,
                            "relevance": "1", "language": LANGUAGE}))  # fmt: skip
        for q in (q for q in questions if q["gid"] == gid):
            lines.append(row(**{
                "id": q["qid"], "class": "Q", "type/scale": q["type"], "name": q["title"],
                "relevance": "1", "text": q["text"], "help": q["help"], "language": LANGUAGE,
                "mandatory": q["mandatory"], "encrypted": "N", "other": q["other"],
                "same_default": "0", "question_theme_name": THEMES[q["type"]],
                "same_script": "0"}))  # fmt: skip
            for s in (s for s in subquestions if s["parent"] == q["qid"]):
                lines.append(row(**{
                    "id": s["qid"], "class": "SQ", "name": s["title"], "relevance": "1",
                    "text": s["text"], "language": LANGUAGE, "mandatory": "N", "other": "N",
                    "same_default": "0", "same_script": "0"}))  # fmt: skip
            for _a, qid, code, _o, label in (a for a in answers if a[1] == q["qid"]):
                lines.append(row(**{
                    "id": qid, "class": "A", "type/scale": "0", "name": code, "text": label,
                    "language": LANGUAGE, "assessment_value": "0"}))  # fmt: skip
    return "\n".join(lines) + "\n"


def write_all(folder: Path) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for suffix, text in ((".lss", lss_text()), (".txt", tsv_text())):
        path = folder / f"{STEM}{suffix}"
        path.write_text(text, encoding="utf-8", newline="\n")
        written.append(path)
    return written


if __name__ == "__main__":
    for path in write_all(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT):
        print(path)
