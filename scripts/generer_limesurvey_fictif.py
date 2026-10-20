"""Write the fictional LimeSurvey survey of the tests (v0.20, D-148): its structure as
LimeSurvey Cloud 7.6 exports it, in its two forms, `.lss` (XML) and the tab-separated `.txt`,
and five invented responses as it exports them, in CSV (codes), Excel and SPSS (`.sav`).

The forms are those seen on 2026-10-19, when this very survey was imported into LimeSurvey 7.6,
exported again and filled with invented responses (`docs/essais/2026-10-19-limesurvey-fictif.md`).
The real exports stay off the repository (they carry the administrator's address); this script
writes the same structure with a fictional administrator. Nothing real; no randomness: two runs
write the same bytes.

Run: uv run python scripts/generer_limesurvey_fictif.py [folder]
(default: exemples/bases-fictives/)
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generer_bases_fictives as common

from ddict.design_limesurvey import COLUMNS, THEMES

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
# The 151 columns of LimeSurvey 7.6, and its themes: those the tool writes (v0.20, E2).
TSV_COLUMNS = list(COLUMNS)


def _names(text: str) -> list[str]:
    return text.split()


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


# --- The responses (A2). ---

RESPONSES_STEM = "reponses-limesurvey"
# The columns of the exports, as LimeSurvey names them in a CSV or Excel file.
COLUMNS = [
    "id", "submitdate", "lastpage", "startlanguage", "seed", "startdate", "datestamp",
    "quota_exit", "genre", "genre[other]", "age", "region", "journal", "profession", "intro",
    "sommeil[SQ001]", "sommeil[SQ002]", "sommeil[SQ003]", "aides[SQ001]", "aides[SQ002]",
    "aides[other]", "nuit",
]  # fmt: skip
# Five invented responses; the last stopped after the first page. None: a cell LimeSurvey
# leaves empty (a question not seen, a number not given); "": an empty answer it writes.
ROWS = [
    ["1", "2026-10-19 19:27:53", "2", "fr", "184453967", "2026-10-19 19:27:07",
     "2026-10-19 19:27:53", None, "1", "", "34", "1", "2026-10-01 00:00:00", "Infirmière", "",
     "3", "2", "3", "Y", "", "", "Réveillée trois fois."],
    ["2", "2026-10-19 19:28:27", "2", "fr", "983672855", "2026-10-19 19:28:02",
     "2026-10-19 19:28:27", None, "2", "", "51", "2", "2026-10-02 00:00:00", "Enseignant", "",
     "1", "4", "1", "", "Y", "", ""],
    ["3", "2026-10-19 19:28:48", "2", "fr", "19063807", "2026-10-19 19:28:43",
     "2026-10-19 19:28:48", None, "-oth-", "Non binaire", "27", "3", "2026-10-03 00:00:00",
     "Étudiant", "", "2", "3", "2", "Y", "Y", "Le bruit blanc", "Difficile."],
    ["4", "2026-10-19 19:29:16", "2", "fr", "1110833683", "2026-10-19 19:29:11",
     "2026-10-19 19:29:16", None, "9", "", None, "", "2026-10-04 00:00:00", "", "", "4", "1",
     "4", "", "", "", ""],
    ["5", None, "1", "fr", "1658836068", "2026-10-19 19:29:25", "2026-10-19 19:29:28", None,
     "1", "", "42", "1", "2026-10-05 00:00:00", "Comptable", None, None, None, None, None, None,
     None, None],
]  # fmt: skip
DATETIMES = {"submitdate", "startdate", "datestamp", "journal"}
# The .sav: a label, a format and a measure for each variable, as LimeSurvey 7.6 wrote them.
SAV_LABELS = {
    "id": "ID de la réponse", "submitdate": "Date de soumission", "lastpage": "Dernière page",
    "startlanguage": "Langue de départ", "seed": "Tête de série",
    "startdate": "Date de lancement", "datestamp": "Date de la dernière action",
    "quota_exit": "Sortie de quota", "genre": "Quel est votre genre ?",
    "genre_other": "[Autre] Quel est votre genre ?", "age": "Quel âge avez-vous ?",
    "region": "Dans quelle région habitez-vous ?",
    "journal": "À quelle date avez-vous rempli le journal du sommeil ?",
    "profession": "Quelle est votre profession ?",
    "intro": "Les questions suivantes portent sur votre sommeil.",
    "sommeil_SQ001": "[vous êtes-vous réveillé·e la nuit ?] Au cours du dernier mois, à quelle "
                     "fréquence…",
    "sommeil_SQ002": "[avez-vous bien dormi ?] Au cours du dernier mois, à quelle fréquence…",
    "sommeil_SQ003": "[avez-vous eu du mal à vous endormir ?] Au cours du dernier mois, à "
                     "quelle fréquence…",
    "aides_SQ001": "[La lecture] Qu'est-ce qui vous aide à dormir ?",
    "aides_SQ002": "[La musique] Qu'est-ce qui vous aide à dormir ?",
    "aides_other": "[Autre] Qu'est-ce qui vous aide à dormir ?",
    "nuit": "Décrivez une nuit difficile.",
}  # fmt: skip
SAV_FORMATS = {
    "id": "F1.0", "submitdate": "DATETIME20", "lastpage": "F1.0", "startlanguage": "A2",
    "seed": "F10.0", "startdate": "DATETIME20", "datestamp": "DATETIME20", "quota_exit": "A1",
    "genre": "A5", "genre_other": "A11", "age": "F2.0", "region": "F1.0",
    "journal": "DATETIME20", "profession": "A11", "intro": "A1", "sommeil_SQ001": "F1.0",
    "sommeil_SQ002": "F1.0", "sommeil_SQ003": "F1.0", "aides_SQ001": "A28",
    "aides_SQ002": "A28", "aides_other": "A14", "nuit": "A23",
}  # fmt: skip
FREQUENCY = {1.0: "Jamais", 2.0: "Parfois", 3.0: "Souvent", 4.0: "Toujours"}
TICKED = {"Y": "Oui", "0": "Non sélectionné"}
SAV_VALUE_LABELS = {
    "genre": {"1": "Femme", "2": "Homme", "9": "Préfère ne pas répondre", "-oth-": "Other"},
    "region": {1.0: "Estrie", 2.0: "Mauricie", 3.0: "Outaouais"},
    "sommeil_SQ001": FREQUENCY, "sommeil_SQ002": FREQUENCY, "sommeil_SQ003": FREQUENCY,
    "aides_SQ001": TICKED, "aides_SQ002": TICKED,
}  # fmt: skip
# SPSS counts dates in seconds from 1582-10-14, which LimeSurvey writes for an empty date.
SPSS_ZERO = dt.datetime(1582, 10, 14)


def sav_name(column: str) -> str:
    return column.replace("[", "_").replace("]", "")


def responses_csv() -> str:
    def cell(value):
        return "" if value is None else '"' + value.replace('"', '""') + '"'

    lines = [",".join(f'"{c}"' for c in COLUMNS)]
    lines += [",".join(cell(v) for v in row) for row in ROWS]
    return "\ufeff" + "\r\n".join(lines) + "\r\n"


def write_responses_xlsx(path: Path) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "ddict - questionnaire fictif (t"  # the survey's title, cut at 31
    sheet.append(COLUMNS)
    for row in ROWS:
        sheet.append([
            None if v in (None, "") else (int(v) if v.isdigit() else v)  # as LimeSurvey does
            for v in row
        ])  # fmt: skip
    workbook.properties.created = common.XLSX_FIXED_TIME
    workbook.properties.modified = common.XLSX_FIXED_TIME
    workbook.save(path)
    _fix_zip_times(path)


def _fix_zip_times(path: Path) -> None:
    """Fixed times in the zip entries and in the workbook's properties: the same bytes."""
    import re
    import zipfile

    with zipfile.ZipFile(path) as archive:
        entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for info, data in entries:
            if info.filename == "docProps/core.xml":
                data = re.sub(
                    rb"(<dcterms:modified[^>]*>)[^<]*", rb"\g<1>2026-01-01T00:00:00Z", data
                )
            fixed = zipfile.ZipInfo(info.filename, date_time=common.XLSX_FIXED_TIME.timetuple()[:6])
            fixed.compress_type = zipfile.ZIP_DEFLATED
            fixed.create_system = 0
            archive.writestr(fixed, data)


def _seconds(value: str | None) -> float:
    """A date and time in SPSS's seconds; LimeSurvey writes 0 (1582-10-14) for an empty one."""
    if value is None:
        return 0.0
    return (dt.datetime.fromisoformat(value) - SPSS_ZERO).total_seconds()


def write_responses_sav(path: Path) -> None:
    data = {}
    for index, column in enumerate(COLUMNS):
        values = [row[index] for row in ROWS]
        name = sav_name(column)
        if column in DATETIMES:
            data[name] = [_seconds(v) for v in values]
        elif SAV_FORMATS[name].startswith("F"):
            data[name] = [float(v) if v not in (None, "") else float("nan") for v in values]
        else:
            data[name] = ["" if v is None else v for v in values]
    meta = {
        "column_labels": SAV_LABELS,
        "variable_value_labels": SAV_VALUE_LABELS,
        "variable_format": SAV_FORMATS,
        "variable_measure": {
            n: "unknown" if n in SAV_VALUE_LABELS or n.endswith("_other") else "nominal"
            for n in SAV_FORMATS
        },
    }
    common.write_sav(pd.DataFrame(data), meta, path)


def write_all(folder: Path) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for suffix, text in ((".lss", lss_text()), (".txt", tsv_text())):
        path = folder / f"{STEM}{suffix}"
        path.write_text(text, encoding="utf-8", newline="\n")
        written.append(path)
    csv_path = folder / f"{RESPONSES_STEM}.csv"
    csv_path.write_bytes(responses_csv().encode("utf-8"))
    xlsx_path, sav_path = folder / f"{RESPONSES_STEM}.xlsx", folder / f"{RESPONSES_STEM}.sav"
    write_responses_xlsx(xlsx_path)
    write_responses_sav(sav_path)
    return [*written, csv_path, xlsx_path, sav_path]


if __name__ == "__main__":
    for path in write_all(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT):
        print(path)
