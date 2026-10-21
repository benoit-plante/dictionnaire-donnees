"""The phase "Concevoir" (v0.20, D-149): the editor of the questionnaire designed in the tool,
and what the pages that show the database say before it arrives (D-145).

The editor follows the page "Plan": the sections and their questions, one line each, to move,
modify or remove; one question open at a time, in a form of its kind, whose choices and items
are a table. One "Enregistrer" per question (D-124): what is typed and not saved is a draft,
the tables too; every save goes through `c.save` and its check (D-129, D-130).
"""

from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from ddict import design, design_duration, design_points, design_word, naming
from ddict.design import DesignError, Draft, Item
from ddict.i18n import N_, Texts, _
from ddict.project import skip
from ddict.project.decisions import is_accepted
from ddict.project.model import Condition, Project, Provenance, Question, Term
from ddict.review import navigation
from ddict.review.ui import common as c
from ddict.review.ui.questionnaire_view import KIND_NAMES

EXCERPT = 70  # characters of a question's text on its line
OPEN = "design-open"  # the question open in the form: its id, NEW, or nothing
NEW = "new"
NEW_SECTION = "design-new-section"  # the section a new question goes to
SECTION_FILTER = "design-section-filter"
ALL = "all"
MESSAGE = "design-questions"  # the messages of the list
KINDS = ("single", "checkbox", "grid", "open", "display")
ANSWERS = Texts(
    {
        "short": N_("texte court"),
        "long": N_("texte long"),
        "number": N_("nombre"),
        "date": N_("date"),
    }
)
LAYOUTS = Texts({"radio": N_("boutons"), "dropdown": N_("liste déroulante")})
PROVENANCES = design_word.PROVENANCES
# v0.21 (D-165): the operators of a term, as the table of a condition shows them.
OPERATOR_NAMES = Texts(
    {
        "eq": N_("="),
        "ne": N_("≠"),
        "in": N_("parmi"),
        "not_in": N_("pas parmi"),
        "lt": N_("<"),
        "le": N_("≤"),
        "gt": N_(">"),
        "ge": N_("≥"),
        "checked": N_("est cochée"),
        "answered": N_("a une réponse"),
    }
)
COMBINES = Texts({"all": N_("toutes les lignes (et)"), "any": N_("au moins une ligne (ou)")})
TERM_COLUMNS = ["target", "operator", "value"]
TARGET_EXCERPT = 40


def _excerpt(text: str) -> str:
    return text if len(text) <= EXCERPT else text[: EXCERPT - 1].rstrip() + "…"


def _of(entry) -> str | None:
    return (entry.question.value or "").partition(".")[0] or None


# --- Acting: change, save, say so. ---


def act(change, *args, key: str = MESSAGE, done: str = "", close: bool = False) -> None:
    """Change the questionnaire, then save; on a refusal, say why and keep what was typed."""
    project = c.project()
    before = c.recall()
    kept = project.model_copy(deep=True)
    try:
        change(project, *args)
    except DesignError as error:
        # A change made of two (a question, then its code) leaves nothing half done.
        for name in Project.model_fields:
            setattr(project, name, getattr(kept, name))
        st.session_state.message = ("error", " ".join(error.reasons), key)
        return
    if not c.save(key, before):
        return
    if close:
        _close()
    st.session_state.message = ("success", done or _("Enregistré."), key)


def _close() -> None:
    """The form closed, the fields of every opening of it gone: nothing left as typed. A
    table's rows are no widget and stay in the session: kept, those of an earlier opening
    would differ from the project once the question changed, and read as a draft."""
    opened = st.session_state.pop(OPEN, None)
    if opened is None:
        return
    prefix = f"design-q-{opened}-"
    for key in [k for k in st.session_state if str(k).startswith(prefix)]:
        del st.session_state[key]
    for name in ("fresh", c.PLACES, c.LABELS):
        found = st.session_state.get(name, {})
        for key in [k for k in found if str(k).startswith(prefix)]:
            del found[key]


def _open(question_id: str, section: str | None = None) -> None:
    """Open a question in the form. Its fields get new keys each time, unless a draft of it
    waits (D-124): a field gone and back under the same key may show, in the browser, a value
    of its former life (seen: an empty text after "Enregistrer", then "Modifier")."""
    _close()
    st.session_state[OPEN] = question_id
    if section is not None:
        st.session_state[NEW_SECTION] = section
    drafts = st.session_state.get(c.DRAFTS, [])
    if not any(d.place.mode == "design" and d.place.item == question_id for d in drafts):
        counter = f"design-form-{question_id}"
        st.session_state[counter] = st.session_state.get(counter, 0) + 1


# --- The form of a question. ---


def _prefix(question_id: str) -> str:
    """The start of the keys of a question's fields, for this opening of its form."""
    return f"design-q-{question_id}-{st.session_state.get(f'design-form-{question_id}', 0)}-"


def _rows(items, *, other: bool, attention: bool = False) -> list[dict]:
    return [
        {
            "id": i.option_id if hasattr(i, "option_id") else i.row_id,
            "code": i.code or "",
            "text": i.text,
            **({"other": bool(getattr(i, "other", False))} if other else {}),
            **({"attention": ", ".join(i.attention or [])} if attention else {}),
        }
        for i in items
    ]


def _columns(other: bool, attention: bool = False) -> list[str]:
    return [
        "id",
        "code",
        "text",
        *(["other"] if other else []),
        *(["attention"] if attention else []),
    ]


def _table(
    key: str,
    fresh,
    label: str,
    *,
    other: bool = False,
    attention: bool = False,
    columns: list[str] | None = None,
    config: dict | None = None,
) -> None:
    """A table of choices or items. Its rows as typed are a list in the session, followed by
    `c.field` (so that what is typed and not saved is a draft, D-124). The editor stays the
    same while the form is open, on the rows it started from (`-base`): a new editor at each
    change would lose a cell being typed. Started again (a page left and back, a draft taken
    back), it starts from the list."""
    c.field(key, fresh, label=label)
    editor = f"{key}-editor"
    if editor not in st.session_state:
        st.session_state[f"{key}-base"] = st.session_state[key]
    if columns is None:
        columns = _columns(other, attention)
        config = {
            "id": None,  # hidden: the item keeps its id, so its variable keeps its decisions
            "code": st.column_config.TextColumn(_("Code"), width="small"),
            "text": st.column_config.TextColumn(_("Texte"), width="large"),
        }
        if other:
            config["other"] = st.column_config.CheckboxColumn(_("Autre"), width="small")
        if attention:
            config["attention"] = st.column_config.TextColumn(
                _("Item de contrôle : bonnes réponses"),
                help=_("Les codes des bonnes réponses ; vide : ce n'est pas un item de contrôle."),
            )
    rows = [_row(r, columns) for r in st.session_state[f"{key}-base"]]  # a cell never NaN
    frame = pd.DataFrame(rows, columns=columns)
    st.write(label)
    st.data_editor(
        frame,
        key=editor,
        num_rows="dynamic",
        hide_index=True,
        column_config=config,
        on_change=_merge,
        args=(key, columns),
        width="stretch",
    )


def _rows_now(key: str, columns: list[str]) -> list[dict]:
    """The rows as typed now: those the editor started from, with its edits."""
    editor = f"{key}-editor"
    edits = st.session_state.get(editor) or {}
    if any(edits.get(k) for k in ("edited_rows", "added_rows", "deleted_rows")):
        return merged(st.session_state[f"{key}-base"], edits, columns)
    return st.session_state.get(key) or []  # nothing edited yet: the list as it is


def merged(rows: list[dict], edits: dict, columns: list[str]) -> list[dict]:
    """A table's rows after the edits of its editor (Streamlit's `edited_rows`, `added_rows`,
    `deleted_rows`): the rows kept keep their id, so their variables keep their decisions."""
    found = [dict(r) for r in rows]
    for index, changed in edits.get("edited_rows", {}).items():
        found[int(index)].update(changed)
    found += [{c: r.get(c) for c in columns} for r in edits.get("added_rows", [])]
    deleted = {int(i) for i in edits.get("deleted_rows", [])}
    found = [r for i, r in enumerate(found) if i not in deleted]
    return [_row(r, columns) for r in found]


def _row(row: dict, columns: list[str]) -> dict:
    """A row as the drafts compare it: an id or None, a box ticked or not, else a text."""
    return {
        c: row.get(c) if c == "id" else bool(row.get(c)) if c == "other" else row.get(c) or ""
        for c in columns
    }


def _merge(key: str, columns: list[str]) -> None:
    """The rows as typed, into the list the drafts follow."""
    st.session_state[key] = _rows_now(key, columns)


def _fresh(question: Question | None, project: Project) -> dict:
    """What the form shows when it opens: the question, or an empty one."""
    sections = design.questionnaire(project).sections
    section = st.session_state.get(NEW_SECTION) or sections[0].section_id
    if question is None:
        return {
            "kind": "single", "section": section, "text": "", "instruction": "", "code": "",
            "required": False, "answer": "short", "layout": "radio", "provenance": "team",
            "source": "", "page": None, "options": [], "rows": [],
            "terms": [], "combine": "all", "shuffle": False, "attention": "",
        }  # fmt: skip
    provenance = question.provenance
    stem = naming.stem(project, question.question_id)
    return {
        "code": stem.stem.value if stem and stem.stem.value and is_accepted(stem.stem) else "",
        "kind": question.kind,
        "section": question.section or section,
        "text": question.text,
        "instruction": question.instruction or "",
        "required": question.required,
        "answer": question.answer or "short",
        "layout": question.layout or "radio",
        "provenance": provenance.kind if provenance and provenance.kind == "source" else "team",
        "source": (provenance.source or "") if provenance else "",
        "page": provenance.page if provenance else None,
        "options": _rows(question.options, other=True),
        "rows": _rows(question.rows, other=False, attention=True),
        "terms": condition_rows(project, question.condition),
        "combine": question.condition.combine if question.condition else "all",
        "shuffle": question.shuffle,
        "attention": ", ".join(question.attention or []),
    }


# --- A condition as a table (v0.21, D-165). ---


def _short(text: str) -> str:
    return text if len(text) <= TARGET_EXCERPT else text[: TARGET_EXCERPT - 1].rstrip() + "…"


def target_labels(project: Project) -> dict[str, str]:
    """What a term may name, as the table shows it ("3. Avez-vous des enfants ?", "7. Votre
    quartier… — est sûr.") and its id: a choice, a number or a text, a grid's statement, an
    option to tick."""
    found = design.questionnaire(project)
    numbers = skip.numbers(found)
    labels: dict[str, str] = {}

    def add(label: str, target: str) -> None:
        labels[label if label not in labels else f"{label} ({target})"] = target

    for question in found.questions:
        number = numbers.get(question.question_id)
        if number is None:
            continue
        head = f"{number}. {_short(question.text)}"
        if question.kind in ("single", "open"):
            add(head, question.question_id)
        elif question.kind == "grid":
            for row in question.rows:
                add(f"{head} — {_short(row.text)}", row.row_id)
        elif question.kind == "checkbox":
            for option in question.options:
                if not option.other:
                    add(f"{head} — {_short(option.text)}", option.option_id)
    return labels


def _value_text(term: Term) -> str:
    values = skip.values_of(term)
    return ", ".join(skip.code_text(v) for v in values)


def condition_rows(project: Project, condition: Condition | None) -> list[dict]:
    """A condition as the rows of its table; a target gone since shows its id."""
    if condition is None:
        return []
    by_id = {target: label for label, target in target_labels(project).items()}
    return [
        {
            "target": by_id.get(term.target, term.target),
            "operator": _(OPERATOR_NAMES[term.operator]),
            "value": _value_text(term),
        }
        for term in condition.terms
    ]


def condition_from(
    project: Project, rows: list[dict], combine: str, labels: dict[str, str] | None = None
) -> Condition | None:
    """The condition the table says; None when it is empty (always asked). What cannot be a
    term is refused with its line; what the questionnaire refuses, `design.set_condition`
    says. `labels`: what the table shows -> the target (v0.21, step 8: a variable's name)."""
    labels = target_labels(project) if labels is None else labels
    operators = {_(OPERATOR_NAMES[k]): k for k in OPERATOR_NAMES}
    terms, problems = [], []
    for number, row in enumerate(rows, start=1):
        target = (row.get("target") or "").strip()
        operator = operators.get((row.get("operator") or "").strip())
        value = (row.get("value") or "").strip()
        if not (target or row.get("operator") or value):
            continue
        if not target:
            problems.append(
                _("Ligne {n} : choisissez la question ou la variable visée.").format(n=number)
            )
            continue
        if operator is None:
            problems.append(_("Ligne {n} : choisissez un opérateur.").format(n=number))
            continue
        found: str | list[str] | None = None
        if operator in ("in", "not_in"):
            found = [v.strip() for v in re.split(r"[,;]", value) if v.strip()]
            if not found:
                problems.append(_("Ligne {n} : donnez au moins un code.").format(n=number))
                continue
        elif operator not in ("checked", "answered"):
            if not value:
                problems.append(_("Ligne {n} : donnez une valeur.").format(n=number))
                continue
            found = value
        terms.append(Term(target=labels.get(target, target), operator=operator, value=found))
    if problems:
        raise DesignError(problems)
    if not terms:
        return None
    if len(terms) > 10:
        raise DesignError([_("Une condition a au plus 10 lignes.")])
    return Condition(combine=combine if combine in ("all", "any") else "all", terms=terms)


def codes(text: str | None) -> list[str] | None:
    """Codes typed "4" or "4, 5"; None when there is none."""
    found = [v.strip() for v in re.split(r"[,;]", text or "") if v.strip()]
    return found or None


def _condition_block(project: Project, key: str, fresh_rows, fresh_combine) -> None:
    """The block "Posée si": its lines, joined by "and" or "or", and the codes of the choices
    the lines name, to type them."""
    st.markdown(":material/filter_alt: " + _("**Posée si**"))
    st.caption(_("Sans ligne, toujours posée. Une réponse laissée vide ne remplit aucune ligne."))
    labels = target_labels(project)
    typed = st.session_state.get(f"{key}terms") or fresh_rows()
    options = list(labels) + [
        r["target"] for r in typed if r.get("target") and r["target"] not in labels
    ]
    st.radio(
        _("Conditions à remplir"),
        list(COMBINES),
        key=c.field(f"{key}combine", fresh_combine, label=_("Posée si")),
        format_func=COMBINES.__getitem__,
        horizontal=True,
    )
    _table(
        f"{key}terms",
        fresh_rows,
        _(
            "Lignes de la condition (question visée, opérateur, valeur ; plusieurs codes "
            "séparés par des virgules)"
        ),
        columns=TERM_COLUMNS,
        config={
            "target": st.column_config.SelectboxColumn(
                _("Question visée"), options=options, width="large"
            ),
            "operator": st.column_config.SelectboxColumn(
                _("Opérateur"),
                options=[_(OPERATOR_NAMES[k]) for k in OPERATOR_NAMES],
                width="small",
            ),
            "value": st.column_config.TextColumn(_("Valeur"), width="small"),
        },
    )
    found = design.questionnaire(project)
    shown = []
    for row in st.session_state.get(f"{key}terms") or []:
        target = skip.target_of(found, labels.get(row.get("target") or "", ""))
        if (
            target is not None
            and target.nature == "choice"
            and target.question.question_id not in shown
        ):
            shown.append(target.question.question_id)
            choices = skip.choices(target.question)
            st.caption(
                _("Codes de la question {n} : {codes}").format(
                    n=skip.numbers(found).get(target.question.question_id),
                    codes=", ".join(f"{k} = {v}" for k, v in choices.items()),
                )
            )


def _value(question_id: str, name: str):
    return st.session_state.get(_prefix(question_id) + name)


def _draft(question_id: str) -> Draft:
    """The question as the form says it now."""
    kind = _value(question_id, "kind")
    provenance = None
    if _value(question_id, "provenance") == "source":
        page = _value(question_id, "page")
        provenance = Provenance(
            kind="source",
            source=(_value(question_id, "source") or "").strip() or "?",
            page=int(page) if page else None,
        )
    else:
        provenance = Provenance(kind="team")

    def items(name: str) -> tuple[Item, ...]:
        return tuple(
            Item(
                text=r["text"] or "",
                code=r["code"] or None,
                other=bool(r.get("other")),
                provenance=provenance,
                item_id=r.get("id") or None,
            )
            for r in _rows_now(
                _prefix(question_id) + name, _columns(name == "options", name == "rows")
            )
            if (r["text"] or "").strip()
        )

    with_options = kind in ("single", "checkbox", "grid")
    return Draft(
        kind=kind,
        text=_value(question_id, "text") or "",
        section=_value(question_id, "section"),
        instruction=_value(question_id, "instruction") or None,
        required=bool(_value(question_id, "required")),
        answer=_value(question_id, "answer") if kind == "open" else None,
        layout=_value(question_id, "layout") if kind == "single" else None,
        provenance=provenance,
        options=items("options") if with_options else (),
        rows=items("rows") if kind == "grid" else (),
    )


def _save_question(project: Project, question_id: str) -> None:
    code_key = _prefix(question_id) + "code"  # read before a new question gets its id
    typed = (st.session_state.get(code_key) or "").strip()
    if typed and not naming.valid_stem(typed):  # refused before anything changes
        raise DesignError(
            [_("Code refusé : minuscules, chiffres et « _ », en commençant par une lettre.")]
        )
    draft = _draft(question_id)
    if draft.provenance and draft.provenance.source == "?":
        raise DesignError([_("Nommez la source du texte (« Manuel, p. 4 »).")])
    # v0.21: read before a new question gets its id, refused before anything changes.
    prefix = _prefix(question_id)
    condition = condition_from(
        project,
        _rows_now(prefix + "terms", TERM_COLUMNS),
        _value(question_id, "combine") or "all",
    )
    shuffle = bool(_value(question_id, "shuffle")) and draft.kind in design.SHUFFLED
    attention = codes(_value(question_id, "attention")) if draft.kind == "single" else None
    checks = [
        codes(r.get("attention"))
        for r in _rows_now(prefix + "rows", _columns(False, attention=True))
        if (r.get("text") or "").strip()
    ] if draft.kind == "grid" else []  # fmt: skip
    if question_id == NEW:
        question_id = design.add_question(project, draft)
    else:
        design.modify_question(project, question_id, draft)
    if typed and typed != _fresh(design.find(project, question_id), project)["code"]:
        design.decide_code(project, question_id, "write", now=c.now(), value=typed)
    question = design.find(project, question_id)
    if condition != question.condition:
        design.set_condition(project, question_id, condition)
    if shuffle != question.shuffle:
        design.set_shuffle(project, question_id, shuffle)
    if attention != question.attention:
        design.set_attention(project, question_id, attention)
    for row, check in zip(design.find(project, question_id).rows, checks, strict=False):
        if check != row.attention:
            design.set_attention(project, row.row_id, check)


def _form(project: Project, question_id: str) -> None:
    question = None if question_id == NEW else design.find(project, question_id)
    prefix = _prefix(question_id)

    def field(name: str, label: str) -> str:
        return c.field(prefix + name, lambda n=name: _fresh_now(question_id, n), label=label)

    with st.container(border=True):
        st.subheader(_("Nouvelle question") if question is None else _("Modifier la question"))
        sections = design.questionnaire(project).sections
        titles = {s.section_id: s.title or _("Section sans titre") for s in sections}
        st.selectbox(
            _("Nature"),
            KINDS,
            placeholder=_("Choisir…"),
            key=field("kind", _("Nature")),
            format_func=lambda k: KIND_NAMES.get(k, k),
        )
        st.selectbox(
            _("Section"),
            list(titles),
            placeholder=_("Choisir…"),
            key=field("section", _("Section")),
            format_func=titles.get,
        )
        st.text_area(_("Texte de la question"), key=field("text", _("Texte de la question")))
        st.text_input(_("Consigne (facultative)"), key=field("instruction", _("Consigne")))
        if st.session_state[prefix + "kind"] != "display":
            code_key = field("code", _("Code de la question"))
            st.text_input(
                _("Code de la question (radical des noms)"),
                key=code_key,
                help=_(
                    "Minuscules, chiffres et « _ ». Dans LimeSurvey, le même code sans ses « _ » "
                    "(« aides_sommeil » devient « aidessommeil »)."
                ),
            )
            proposed = naming.stem(project, question_id) if question is not None else None
            if proposed and proposed.stem.value and not st.session_state[code_key]:
                c.offer(
                    _("Reprendre la proposition : {code}").format(code=proposed.stem.value),
                    f"{prefix}code-offer",
                    code_key,
                    proposed.stem.value,
                )
        kind = st.session_state[prefix + "kind"]
        if kind != "display":
            st.checkbox(_("Obligatoire"), key=field("required", _("Obligatoire")))
        if kind == "open":
            st.selectbox(
                _("Réponse attendue"),
                list(ANSWERS),
                placeholder=_("Choisir…"),
                key=field("answer", _("Réponse attendue")),
                format_func=ANSWERS.__getitem__,
            )
        if kind == "single":
            st.radio(
                _("Présentation"),
                list(LAYOUTS),
                key=field("layout", _("Présentation")),
                format_func=LAYOUTS.__getitem__,
                horizontal=True,
            )
        st.radio(
            _("Provenance du texte"),
            list(PROVENANCES),
            key=field("provenance", _("Provenance du texte")),
            format_func=PROVENANCES.__getitem__,
            horizontal=True,
        )
        if st.session_state[prefix + "provenance"] == "source":
            left, right = st.columns([3, 1])
            left.text_input(_("Source"), key=field("source", _("Source")))
            right.number_input(_("Page"), min_value=1, step=1, key=field("page", _("Page")))
        if kind in ("single", "checkbox"):
            _table(
                prefix + "options",
                lambda: _fresh_now(question_id, "options"),
                _("Choix de réponse (code, texte ; cochez « Autre » pour l'option à préciser)"),
                other=True,
            )
        if kind == "grid":  # the items first, as in the Word and in LimeSurvey
            _table(
                prefix + "rows",
                lambda: _fresh_now(question_id, "rows"),
                _("Énoncés de la grille (code, texte ; un item de contrôle a ses bonnes réponses)"),
                attention=True,
            )
            _table(
                prefix + "options",
                lambda: _fresh_now(question_id, "options"),
                _("Colonnes de la grille : les choix de réponse (code, texte)"),
                other=False,
            )
        if kind in design.SHUFFLED:
            st.checkbox(
                {
                    "single": _("Présenter les choix dans un ordre aléatoire"),
                    "checkbox": _("Présenter les options dans un ordre aléatoire"),
                    "grid": _("Présenter les énoncés dans un ordre aléatoire"),
                }[kind],
                key=field("shuffle", _("Ordre aléatoire")),
                help=_("Tiré pour chaque personne ; l'option « Autre » reste à la fin."),
            )
        if kind == "single":
            st.text_input(
                _("Item de contrôle : bonnes réponses (codes ; vide : ce n'est pas un item de "
                  "contrôle)"),
                key=field("attention", _("Item de contrôle")),
            )  # fmt: skip
        _condition_block(
            project,
            prefix,
            lambda: _fresh_now(question_id, "terms"),
            lambda: _fresh_now(question_id, "combine"),
        )
        save, cancel, _space = st.columns([1, 1, 3])
        save.button(
            _("Enregistrer"),
            key=f"{prefix}save",
            type="primary",
            on_click=act,
            args=(_save_question, question_id),
            kwargs={"key": f"{prefix}save", "close": True},
        )
        cancel.button(_("Annuler"), key=f"{prefix}cancel", on_click=_close)
        c.show_message(f"{prefix}save")


def _fresh_now(question_id: str, name: str):
    """A field's value as the project holds it now (read at each run, for the drafts)."""
    project = c.project()
    question = None
    if question_id != NEW:
        try:
            question = design.find(project, question_id)
        except DesignError:
            question = None
    return _fresh(question, project)[name]


# --- The list. ---


def _question_line(
    project: Project, number: int, question: Question, rank: int, total: int, problems
):
    names = [e.name for e in project.variables if _of(e) == question.question_id]
    with st.container(border=True):
        parts = [f"**{number}.** {_excerpt(question.text)}", f"*{KIND_NAMES.get(question.kind)}*"]
        if names:
            shown = ", ".join(f"`{n}`" for n in names[:3])
            if len(names) > 3:
                shown += " " + _("et {n} autres").format(n=len(names) - 3)
            parts.append(shown)
        provenance = design_word.provenance_text(question.provenance)
        if provenance:
            parts.append(provenance)
        st.markdown(" — ".join(parts))
        for line in _settings(project, question):
            st.caption(line)
        for point in problems:  # the review's points (D3), settled in the form or kept
            st.markdown(f":material/warning: {point.text}")
        key = f"design-{question.question_id}"
        up, down, edit, remove, _space = st.columns([1, 1, 1, 1, 2])
        up.button(
            _("Monter"),
            key=f"{key}-up",
            icon=":material/arrow_upward:",
            disabled=rank == 1,
            on_click=act,
            args=(design.move_question, question.question_id, rank - 1),
        )
        down.button(
            _("Descendre"),
            key=f"{key}-down",
            icon=":material/arrow_downward:",
            disabled=rank == total,
            on_click=act,
            args=(design.move_question, question.question_id, rank + 1),
        )
        edit.button(
            _("Modifier"),
            key=f"{key}-edit",
            icon=":material/edit:",
            on_click=_open,
            args=(question.question_id,),
        )
        with remove.popover(_("Retirer"), icon=":material/delete:"):
            st.caption(
                _("La question et ses variables quittent le projet ; son numéro ne reviendra pas.")
            )
            for text in design.citations(project, question.question_id):
                st.warning(text)
            st.button(
                _("Retirer la question"),
                key=f"{key}-remove",
                on_click=act,
                args=(design.remove_question, question.question_id),
                kwargs={"done": _("Question retirée.")},
            )


def _settings(project: Project, question: Question) -> list[str]:
    """What the question's condition, random order and attention checks say (v0.21)."""
    found = []
    if question.condition is not None:
        found.append(skip.team_text(project, question.condition))
    if question.shuffle:
        found.append(_("Ordre aléatoire."))
    if question.attention:
        found.append(
            _("Item de contrôle : bonnes réponses {codes}.").format(
                codes=", ".join(question.attention)
            )
        )
    for row in question.rows:
        if row.attention:
            found.append(
                _("Item de contrôle « {row} » : bonnes réponses {codes}.").format(
                    row=_short(row.text), codes=", ".join(row.attention)
                )
            )
    return found


def _save_section(project: Project, section_id: str) -> None:
    key = f"design-{section_id}-"
    condition = condition_from(
        project,
        _rows_now(key + "terms", TERM_COLUMNS),
        st.session_state.get(key + "combine") or "all",
    )
    design.modify_section(
        project, section_id, st.session_state[key + "title"], st.session_state[key + "instruction"]
    )
    section = next(s for s in design.questionnaire(project).sections if s.section_id == section_id)
    if condition != section.condition:
        design.set_condition(project, section_id, condition)
    if bool(st.session_state.get(key + "shuffle")) != section.shuffle:
        design.set_shuffle(project, section_id, bool(st.session_state.get(key + "shuffle")))


def _section_controls(project: Project, section, rank: int, total: int) -> None:
    key = f"design-{section.section_id}"
    title_key = c.field(f"{key}-title", lambda s=section.section_id: _section(s).title,
                        label=_("Titre de la section"))  # fmt: skip
    instruction_key = c.field(
        f"{key}-instruction",
        lambda s=section.section_id: _section(s).instruction or "",
        label=_("Consigne de la section"),
    )
    up, down, edit, remove, add, _space = st.columns([1, 1, 1, 1, 2, 1])
    up.button(_("Monter"), key=f"{key}-up", icon=":material/arrow_upward:", disabled=rank == 1,
              on_click=act, args=(design.move_section, section.section_id, rank - 1))  # fmt: skip
    down.button(_("Descendre"), key=f"{key}-down", icon=":material/arrow_downward:",
                disabled=rank == total, on_click=act,
                args=(design.move_section, section.section_id, rank + 1))  # fmt: skip
    shuffle_key = c.field(
        f"{key}-shuffle",
        lambda s=section.section_id: _section(s).shuffle,
        label=_("Ordre aléatoire"),
    )
    with edit.popover(_("Modifier"), icon=":material/edit:"):
        st.text_input(_("Titre de la section"), key=title_key)
        st.text_area(_("Consigne de la section (facultative)"), key=instruction_key)
        st.checkbox(_("Présenter ses questions dans un ordre aléatoire"), key=shuffle_key)
        _condition_block(
            project,
            f"{key}-",
            lambda s=section.section_id: condition_rows(c.project(), _section(s).condition),
            lambda s=section.section_id: (
                _section(s).condition.combine if _section(s).condition else "all"
            ),
        )
        st.button(
            _("Enregistrer la section"),
            key=f"{key}-save",
            on_click=act,
            args=(_save_section, section.section_id),
        )
    with remove.popover(_("Retirer"), icon=":material/delete:"):
        st.caption(_("Seule une section sans question se retire."))
        st.button(
            _("Retirer la section"),
            key=f"{key}-remove",
            on_click=act,
            args=(design.remove_section, section.section_id),
        )
    add.button(
        _("Ajouter une question ici"),
        key=f"{key}-add",
        icon=":material/add:",
        on_click=_open,
        args=(NEW, section.section_id),
    )


def _section(section_id: str):
    for section in design.questionnaire(c.project()).sections:
        if section.section_id == section_id:
            return section
    raise KeyError(section_id)


SECTION_TITLE = "design-new-section-title"


def _add_section(project: Project) -> None:
    design.add_section(project, st.session_state.get(SECTION_TITLE) or "")


def _added_section() -> None:
    """Add the section, then empty its title once saved: Streamlit's `clear_on_submit` empties
    it before the callback reads it."""
    act(_add_section, key="design-new-section-form", done=_("Section ajoutée."))
    kind, _text, _key = st.session_state.get("message", (None, None, None))
    if kind == "success":
        st.session_state[SECTION_TITLE] = ""


def _new_section() -> None:
    """An adding form, as on the other pages (D-124)."""
    with st.form("design-new-section-form"):
        st.text_input(_("Titre de la nouvelle section"), key=SECTION_TITLE)
        st.form_submit_button(
            _("Ajouter la section"), icon=":material/add:", on_click=_added_section
        )
    c.show_message("design-new-section-form")


def page(project: Project) -> None:
    st.header(_("Questionnaire"))
    st.caption(
        _(
            "Le questionnaire de l'étude, conçu dans l'outil : il est la source du dictionnaire "
            "de données, et chaque question donne ses variables avant la collecte."
        )
    )
    questionnaire = design.questionnaire(project)
    sections = questionnaire.sections
    choices = [ALL, *(s.section_id for s in sections)]
    if st.session_state.get(SECTION_FILTER) not in choices:
        st.session_state[SECTION_FILTER] = ALL
    titles = {s.section_id: s.title or _("Section sans titre") for s in sections}
    st.selectbox(
        _("Section"),
        choices,
        placeholder=_("Choisir…"),
        key=SECTION_FILTER,
        format_func=lambda s: _("Toutes les sections") if s == ALL else titles[s],
    )
    c.show_message(MESSAGE)
    opened = st.session_state.get(OPEN)
    chosen = st.session_state[SECTION_FILTER]
    problems = design_points.by_question(project)
    number = 0
    for rank, section in enumerate(sections, start=1):
        questions = [q for q in questionnaire.questions if q.section == section.section_id]
        if chosen not in (ALL, section.section_id):
            number += len(questions)
            continue
        st.subheader(titles[section.section_id])
        if section.instruction:
            st.write(section.instruction)
        if section.condition is not None:
            st.caption(skip.team_text(project, section.condition))
        if section.shuffle:
            st.caption(_("Questions de la section en ordre aléatoire."))
        _section_controls(project, section, rank, len(sections))
        if not questions:
            st.caption(_("Aucune question dans cette section."))
        for position, question in enumerate(questions, start=1):
            number += 1
            _question_line(
                project, number, question, position, len(questions),
                problems.get(question.question_id, []),
            )  # fmt: skip
            if opened == question.question_id:
                _form(project, question.question_id)
        if opened == NEW and st.session_state.get(NEW_SECTION, sections[0].section_id) == (
            section.section_id
        ):
            _form(project, NEW)
    st.divider()
    _new_section()


# --- The review (D3). ---


def _go_to_point(point) -> None:
    """The place where a point is settled: the question open in its form, the page "Noms",
    or the group of an instrument."""
    if point.page == "design" and point.question.startswith("S"):  # a section's (v0.21)
        c.go_to("design", **{SECTION_FILTER: point.question})
    elif point.page == "design":
        counter = f"design-form-{point.question}"
        c.go_to("design", **{OPEN: point.question, SECTION_FILTER: ALL,
                             counter: st.session_state.get(counter, 0) + 1})  # fmt: skip
    elif point.page == "groups":
        group = next((g.group_id for g in c.project().groups if g.question == point.question), None)
        c.go_to("groups", **({"group": group} if group else {}))
    else:
        c.go_to("names")


def _keep(project: Project, point) -> None:
    design_points.keep(project, point, c.now())


def review_page(project: Project) -> None:
    st.header(_("Relecture"))
    st.write(
        _(
            "Les points à voir dans le questionnaire, tous calculés. Un point se règle en "
            "corrigeant la question, ou se ferme par « Garder tel quel » : il revient si la "
            "question change."
        )
    )
    _duration(project)
    c.show_message("design-review")
    found = design_points.points(project)
    if not found:
        st.success(_("Aucun point à voir."))
    numbers = {q.question_id: n for n, q in enumerate(design.questionnaire(project).questions, 1)}
    sections = {s.section_id: s for s in design.questionnaire(project).sections}
    for index, point in enumerate(found):
        with st.container(border=True):
            if point.question in sections:
                title = sections[point.question].title or _("Section sans titre")
                st.markdown(_("**Section** {title}").format(title=title))
            else:
                question = design.find(project, point.question)
                st.markdown(f"**{numbers.get(point.question, '?')}.** {_excerpt(question.text)}")
            st.write(point.text)
            go, keep, _space = st.columns([1, 1, 2])
            go.button(
                (
                    _("Aller à la section")
                    if point.question in sections
                    else _("Aller à la question")
                )
                if point.page == "design"
                else _("Ouvrir la page"),
                key=f"design-review-go-{index}",
                icon=":material/arrow_forward:",
                on_click=_go_to_point,
                args=(point,),
            )
            keep.button(
                _("Garder tel quel"),
                key=f"design-review-keep-{index}",
                on_click=act,
                args=(_keep, point),
                kwargs={
                    "key": "design-review",
                    "done": _("Point fermé : il reviendra si la question change."),
                },
            )
    closed = [
        p for p in design_points.points(project, kept=True) if design_points.is_kept(project, p)
    ]
    if closed:
        with st.expander(_("Points gardés tels quels ({n})").format(n=len(closed))):
            for point in closed:
                st.write(f"{numbers.get(point.question, '?')}. {point.text}")


def _duration(project: Project) -> None:
    """The estimated duration, with its formula and its terms (D-171)."""
    if not design.questionnaire(project).questions:
        return
    found = design_duration.estimate(project)
    st.markdown(_("**Durée estimée** : {duration}.").format(duration=design_duration.text(found)))
    with st.expander(_("La formule")):
        for line in design_duration.formula(found):
            st.write(line)


def opened_question() -> str | None:
    """The question open in the form, for the drafts' place (D-124)."""
    return st.session_state.get(OPEN)


def waiting_for_base(project: Project, mode: str) -> None:
    """A page that shows the database, before it arrives: it says so, and leads to the step
    that comes first (v0.20, D-145)."""
    st.header(_(navigation.PAGES[mode].title))
    waiting_note(project, f"waiting-{mode}")


def waiting_note(project: Project, key: str) -> None:
    """What waits for the database, and the button to the step that comes first."""
    st.info(
        _(
            "En attente de la base : cette page s'ouvrira quand les réponses de la collecte "
            "seront arrivées. D'ici là, le questionnaire est la source du dictionnaire."
        )
    )
    if project.design is not None:
        c.go_button(_("Aller au questionnaire"), key=key, mode="design")
