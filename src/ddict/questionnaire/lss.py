"""A LimeSurvey questionnaire (v0.20, D-148): its structure file, `.lss` (XML) or the
tab-separated text format, read as the study's questionnaire, with the exact codes of its
questions, subquestions and answers.

Only the forms seen on a real LimeSurvey are read (`docs/essais/2026-10-19-limesurvey-fictif.md`,
LimeSurvey Cloud 7.6): a `.lss` whose texts are in the `*_l10ns` tables (LimeSurvey 4 and
later), and the text format with its `class` column. Anything else is refused, not guessed.
Since v0.21 (D-169), the relevance of the groups and questions, read by the closed grammar of
`relevance` (an expression outside it is kept as it is, with a point to check, never
guessed), and the random orders. Never read: the survey's settings (administrator, e-mail
addresses, server), its quotas, its old table of conditions (LimeSurvey turns it into the
relevance, which is read) and its tokens.

The XML parser resolves no entity and reaches no network: a structure file is a document
from outside, read as data.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path

from ddict.io.model import ReadError
from ddict.io.sav import file_sha256
from ddict.project import skip
from ddict.project.model import GridRow, Question, Questionnaire, QuestionOption, Section
from ddict.questionnaire import relevance
from ddict.questionnaire.read import normalize

# LimeSurvey's question types, as the tool reads them (D-148); the codes in the export of
# LimeSurvey 7.6. Those with implicit answers (Y, G, 5) and the rest are kept with a point
# to check: their codes were never seen in an export.
SINGLE = {"L": "radio", "!": "dropdown", "O": "radio"}
CHECKBOX = {"M", "P"}
GRID = {"F", "A", "B", "C", "E", "H"}
OPEN = {"S": "short", "T": "long", "U": "long", "N": "number", "D": "date"}
DISPLAY = {"X"}
# The code LimeSurvey gives the "other" answer of a single choice in its exports.
OTHER_CODE = "-oth-"
OTHER_TEXT = {"fr": "Autre", "en": "Other"}
TSV_START = ("id\trelated_id\tclass\t", "class\ttype/scale\t")
_TAG = re.compile(r"<[^>]+>")
_EXPRESSION = re.compile(r"\{[^{}]+\}")
# The attributes of a random order (D-166), and the values that say "none".
ORDERS = ("answer_order", "subquestion_order", "random_order", "random_group")
NOT_RANDOM = {"", "0", "normal"}


@dataclass
class _Question:
    qid: str
    gid: str
    kind: str
    code: str
    order: int
    mandatory: bool
    other: bool
    text: str = ""
    help: str = ""
    subquestions: list[tuple[int, str, str]] = field(default_factory=list)  # order, code, text
    answers: list[tuple[int, str, str]] = field(default_factory=list)  # sortorder, code, text
    relevance: str = ""  # v0.21
    orders: dict[str, str] = field(default_factory=dict)  # ORDERS -> value


def is_limesurvey_text(path: Path) -> bool:
    """Whether a .txt file is LimeSurvey's tab-separated structure, by its first line."""
    try:
        with path.open("rb") as stream:
            start = stream.read(64).decode("utf-8-sig", errors="replace")
    except OSError:
        return False
    return start.startswith(TSV_START)


def _text(raw: str | None) -> str:
    """LimeSurvey writes its texts in HTML: the words, without tags or entities."""
    if not raw:
        return ""
    if "<" in raw or "&" in raw:
        from lxml import html

        try:
            raw = html.fragment_fromstring(raw, create_parent="div").text_content()
        except Exception:  # a broken fragment: the tags taken out by hand
            raw = _TAG.sub(" ", raw)
    return normalize(raw)


# --- The .lss file. ---


def _parser():
    from lxml import etree

    return etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False)


def _rows(root, table: str) -> list[dict[str, str]]:
    section = root.find(table)
    if section is None:
        return []
    found = []
    for row in section.iterfind("rows/row"):
        found.append({child.tag: (child.text or "") for child in row})
    return found


def _int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 0


def _read_lss(content: bytes, name: str, language: str | None):
    from lxml import etree

    try:
        root = etree.fromstring(content, _parser())
    except etree.XMLSyntaxError as error:
        raise ReadError(f"Cannot read {name} as a LimeSurvey .lss file: {error}") from error
    if root.tag != "document" or root.findtext("LimeSurveyDocType") != "Survey":
        raise ReadError(f"{name} is not a LimeSurvey survey structure (.lss)")
    if root.find("question_l10ns") is None:
        raise ReadError(
            f"{name}: this .lss has no question_l10ns table (LimeSurvey 3 or older); only "
            "the form of LimeSurvey 4 and later is read"
        )
    languages = [e.text for e in root.iterfind("languages/language") if e.text]
    chosen = language if language in languages else (languages[0] if languages else None)
    groups = {
        r["gid"]: [_int(r.get("group_order", "0")), "", "", r.get("grelevance", "")]
        for r in _rows(root, "groups")
    }
    for r in _rows(root, "group_l10ns"):
        if r.get("gid") in groups and r.get("language") == chosen:
            groups[r["gid"]][1:3] = [r.get("group_name", ""), r.get("description", "")]
    questions = {
        r["qid"]: _Question(
            qid=r["qid"],
            gid=r.get("gid", ""),
            kind=r.get("type", ""),
            code=r.get("title", ""),
            order=_int(r.get("question_order", "0")),
            mandatory=r.get("mandatory") == "Y",
            other=r.get("other") == "Y",
            relevance=r.get("relevance", ""),
        )
        for r in _rows(root, "questions")
        if r.get("parent_qid", "0") == "0"
    }
    for r in _rows(root, "question_attributes"):
        found = questions.get(r.get("qid", ""))
        if found is not None and r.get("attribute") in ORDERS:
            found.orders[r["attribute"]] = r.get("value", "")
    texts = {
        r["qid"]: (r.get("question", ""), r.get("help", ""))
        for r in _rows(root, "question_l10ns")
        if r.get("language") == chosen
    }
    for qid, question in questions.items():
        question.text, question.help = texts.get(qid, ("", ""))
    for r in _rows(root, "subquestions"):
        parent = questions.get(r.get("parent_qid", ""))
        if parent is not None and r.get("scale_id", "0") == "0":
            text = texts.get(r["qid"], ("", ""))[0]
            parent.subquestions.append((_int(r.get("question_order", "0")), r["title"], text))
    labels = {
        r["aid"]: r.get("answer", "")
        for r in _rows(root, "answer_l10ns")
        if r.get("language") == chosen
    }
    for r in _rows(root, "answers"):
        parent = questions.get(r.get("qid", ""))
        if parent is not None and r.get("scale_id", "0") == "0":
            parent.answers.append(
                (_int(r.get("sortorder", "0")), r["code"], labels.get(r.get("aid", ""), ""))
            )
    return groups, list(questions.values()), chosen


# --- The tab-separated text. ---


def _read_tsv(content: bytes, name: str, language: str | None):
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ReadError(f"Cannot read {name} as UTF-8 text: {error}") from error
    reader = csv.DictReader(io.StringIO(text), delimiter="\t", quotechar='"')
    if reader.fieldnames is None or "class" not in reader.fieldnames:
        raise ReadError(f"{name} is not a LimeSurvey tab-separated structure")
    rows = list(reader)
    base = next((r["text"] for r in rows if r["class"] == "S" and r["name"] == "language"), None)
    languages = [base] if base else []
    for r in rows:
        if r["class"] in ("G", "Q") and r.get("language") and r["language"] not in languages:
            languages.append(r["language"])
    chosen = language if language in languages else (languages[0] if languages else None)
    groups: dict[str, list] = {}
    questions: list[_Question] = []
    group = question = None
    order = 0
    for r in rows:
        if r.get("language") and r["language"] != chosen:
            continue
        kind = r["class"]
        if kind == "G":
            # The group's number is its type/scale (TSVImportSurvey of LimeSurvey 7.6).
            group = r.get("type/scale") or f"G{len(groups) + 1}"
            groups.setdefault(
                group,
                [len(groups) + 1, r.get("name", ""), r.get("text", ""), r.get("relevance", "")],
            )
            order = 0
        elif kind == "Q":
            question = _Question(
                qid=f"{len(questions) + 1}",
                gid=group or "",
                kind=r.get("type/scale", ""),
                code=r.get("name", ""),
                order=order,
                mandatory=r.get("mandatory") == "Y",
                other=r.get("other") == "Y",
                text=r.get("text", ""),
                help=r.get("help", ""),
                relevance=r.get("relevance", ""),
                orders={k: r[k] for k in ORDERS if r.get(k)},
            )
            order += 1
            questions.append(question)
        elif kind == "SQ" and question is not None and (r.get("type/scale") or "0") == "0":
            question.subquestions.append(
                (len(question.subquestions), r.get("name", ""), r.get("text", ""))
            )
        elif kind == "A" and question is not None and (r.get("type/scale") or "0") == "0":
            question.answers.append((len(question.answers), r.get("name", ""), r.get("text", "")))
    return groups, questions, chosen


# --- The questionnaire. ---


def _checks(question: _Question) -> list[str]:
    found = []
    if question.kind not in (*SINGLE, *CHECKBOX, *GRID, *OPEN, *DISPLAY):
        found.append("lss_type_unsupported")
    if _EXPRESSION.search(question.text) or _EXPRESSION.search(question.help):
        found.append("lss_expression")
    return found


def _question(rank: int, question: _Question, section: str | None, language: str) -> Question:
    qid = f"Q{rank}"
    subquestions = sorted(question.subquestions)
    answers = sorted(question.answers)
    kind = question.kind
    options: list[QuestionOption] = []
    rows: list[GridRow] = []
    if kind in GRID:
        rows = [
            GridRow(row_id=f"{qid}.r{n}", text=_text(t), code=c)
            for n, (_o, c, t) in enumerate(subquestions, start=1)
        ]
        options = [
            QuestionOption(option_id=f"{qid}.o{n}", text=_text(t), code=c)
            for n, (_o, c, t) in enumerate(answers, start=1)
        ]
        shape = "grid"
    elif kind in CHECKBOX:
        options = [
            QuestionOption(option_id=f"{qid}.o{n}", text=_text(t), code=c)
            for n, (_o, c, t) in enumerate(subquestions, start=1)
        ]
        shape = "checkbox"
    elif kind in SINGLE:
        options = [
            QuestionOption(option_id=f"{qid}.o{n}", text=_text(t), code=c)
            for n, (_o, c, t) in enumerate(answers, start=1)
        ]
        shape = "single"
    elif kind in DISPLAY:
        shape = "display"
    else:  # open, and the types read as an open question with a point to check
        shape = "open"
    if question.other and shape in ("single", "checkbox"):
        options.append(
            QuestionOption(
                option_id=f"{qid}.o{len(options) + 1}",
                text=OTHER_TEXT.get(language, OTHER_TEXT["en"]),
                code=OTHER_CODE if shape == "single" else None,
                other=True,
            )
        )
    return Question(
        question_id=qid,
        text=_text(question.text),
        kind=shape,  # type: ignore[arg-type]
        options=options,
        rows=rows,
        to_check=_checks(question),
        code=question.code,
        section=section,
        instruction=_text(question.help) or None,
        required=question.mandatory and shape != "display",
        answer=OPEN.get(kind, "short") if shape == "open" else None,  # type: ignore[arg-type]
        layout=SINGLE[kind] if shape == "single" else None,  # type: ignore[arg-type]
    )


def read_limesurvey(path: Path | str, language: str | None = None) -> Questionnaire:
    """A LimeSurvey structure file as the questionnaire (format `lss`): sections in the
    order of the groups, questions in their order within each, ids `Q1`, `Q1.r1`, `Q1.o1`
    in reading order. `language`: the study's, when the survey has it; else its first."""
    path = Path(path)
    try:
        content = path.read_bytes()
    except OSError as error:
        raise ReadError(f"Cannot read {path.name}: {error}") from error
    head = content[:200].lstrip(b"\xef\xbb\xbf").lstrip()
    if head.startswith(b"<"):
        groups, questions, chosen = _read_lss(content, path.name, language)
    elif head.decode("utf-8", errors="replace").startswith(TSV_START):
        groups, questions, chosen = _read_tsv(content, path.name, language)
    else:
        raise ReadError(f"{path.name} is not a LimeSurvey structure file (.lss or .txt)")
    ordered = sorted(groups.items(), key=lambda item: (item[1][0], item[0]))
    sections = [
        Section(section_id=f"S{n}", title=_text(name), instruction=_text(description) or None)
        for n, (_gid, (_order, name, description, _relevance)) in enumerate(ordered, start=1)
    ]
    section_of = {gid: f"S{n}" for n, (gid, _g) in enumerate(ordered, start=1)}
    rank = {gid: n for n, (gid, _g) in enumerate(ordered)}
    found = sorted(questions, key=lambda q: (rank.get(q.gid, len(rank)), q.order))
    read = Questionnaire(
        file_name=path.name,
        sha256=file_sha256(path),
        format="lss",
        sections=sections,
        questions=[
            _question(n, q, section_of.get(q.gid), chosen or "en")
            for n, q in enumerate(found, start=1)
        ],
    )
    _conditions(read, found, [g[3] for _gid, g in ordered])
    _orders(read, found)
    return read


# --- Conditions and random orders (v0.21, D-169). ---


def names(found: Questionnaire) -> dict[str, relevance.Named]:
    """What an expression may name: a question's code, a statement's or an option's
    ("climat_SQ002"), with its id, its nature and the codes of its choices."""
    named: dict[str, relevance.Named] = {}

    def add(name: str | None, target: str) -> None:
        nature = skip.target_of(found, target)
        if name and nature is not None:
            codes = (
                frozenset(skip.choices(nature.question))
                if nature.nature == "choice"
                else frozenset()
            )
            named[name] = (target, nature.nature, codes)

    for question in found.questions:
        add(question.code, question.question_id)
        for row in question.rows:
            add(f"{question.code}_{row.code}" if row.code else None, row.row_id)
        if question.kind == "checkbox":
            for option in question.options:
                add(f"{question.code}_{option.code}" if option.code else None, option.option_id)
    return named


def _read(holder: Question | Section, expression: str, named) -> None:
    """The condition, or the expression kept as it is, with a point to check."""
    try:
        holder.condition = relevance.parse(expression, named)
    except relevance.Unread:
        holder.condition_unread = expression.strip()
        if isinstance(holder, Question):
            holder.to_check = [*holder.to_check, "lss_condition_unread"]


def _conditions(found: Questionnaire, raw: list[_Question], sections: list[str]) -> None:
    named = names(found)
    for section, expression in zip(found.sections, sections, strict=True):
        _read(section, expression, named)
    for question, source in zip(found.questions, raw, strict=True):
        _read(question, source.relevance, named)


def _orders(found: Questionnaire, raw: list[_Question]) -> None:
    """A list's choices, a grid's or boxes' subquestions in random order; a section whose
    questions all share one random group, its questions in random order. Another value, or
    a group shared by some questions only, is a point to check."""
    for question, source in zip(found.questions, raw, strict=True):
        values = {k: v.strip().lower() for k, v in source.orders.items() if k != "random_group"}
        own = "answer_order" if question.kind == "single" else "subquestion_order"
        random = values.get(own) == "random" or values.get("random_order") == "1"
        unread = [k for k, v in values.items() if v not in NOT_RANDOM and v not in ("random", "1")]
        if random and question.kind in ("single", "checkbox", "grid"):
            question.shuffle = True
        elif random:
            unread.append(own)
        if unread:
            question.to_check = [*question.to_check, "lss_order_unread"]
    for section in found.sections:
        mine = [
            (q, s) for q, s in zip(found.questions, raw, strict=True)
            if q.section == section.section_id
        ]  # fmt: skip
        named = {s.orders.get("random_group", "").strip() for _q, s in mine}
        if mine and len(named) == 1 and "" not in named:
            section.shuffle = True
        elif len(named - {""}) > 0:
            for question, source in mine:
                if source.orders.get("random_group", "").strip():
                    question.to_check = [*question.to_check, "lss_order_unread"]
