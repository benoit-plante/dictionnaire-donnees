"""The phase "Concevoir" (v0.20, D-149): the editor of the questionnaire designed in the tool,
and what the pages that show the database say before it arrives (D-145).

The editor follows the page "Plan": the sections and their questions, one line each, to move,
modify or remove; one question open at a time, in a form of its kind, whose choices and items
are a table. One "Enregistrer" per question (D-124): what is typed and not saved is a draft,
the tables too; every save goes through `c.save` and its check (D-129, D-130).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ddict import design, design_points, naming
from ddict.design import DesignError, Draft, Item
from ddict.i18n import N_, Texts, _
from ddict.project.decisions import is_accepted
from ddict.project.model import Project, Provenance, Question
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
PROVENANCES = Texts({"team": N_("tapé par l'équipe"), "source": N_("tiré d'une source")})


def _excerpt(text: str) -> str:
    return text if len(text) <= EXCERPT else text[: EXCERPT - 1].rstrip() + "…"


def _of(entry) -> str | None:
    return (entry.question.value or "").partition(".")[0] or None


def _provenance_text(provenance: Provenance | None) -> str:
    if provenance is None:
        return ""
    if provenance.kind == "source":
        page = _(", p. {n}").format(n=provenance.page) if provenance.page else ""
        return _("source : {source}{page}").format(source=provenance.source, page=page)
    return _(PROVENANCES.get(provenance.kind, provenance.kind))


# --- Acting: change, save, say so. ---


def _act(change, *args, key: str = MESSAGE, done: str = "", close: bool = False) -> None:
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
    """The form closed, its fields back to what the project holds: nothing left as typed."""
    opened = st.session_state.pop(OPEN, None)
    if opened is None:
        return
    prefix = _prefix(opened)
    fresh = st.session_state.get("fresh", {})
    for key in [k for k in st.session_state if str(k).startswith(prefix)]:
        if key in fresh:
            st.session_state[key] = fresh[key]()
        else:
            del st.session_state[key]


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


def _rows(items, *, other: bool) -> list[dict]:
    return [
        {
            "id": i.option_id if hasattr(i, "option_id") else i.row_id,
            "code": i.code or "",
            "text": i.text,
            **({"other": bool(getattr(i, "other", False))} if other else {}),
        }
        for i in items
    ]


def _columns(other: bool) -> list[str]:
    return ["id", "code", "text", *(["other"] if other else [])]


def _table(key: str, fresh, label: str, *, other: bool) -> None:
    """A table of choices or items. Its rows as typed are a list in the session, followed by
    `c.field` (so that what is typed and not saved is a draft, D-124). The editor stays the
    same while the form is open, on the rows it started from (`-base`): a new editor at each
    change would lose a cell being typed. Started again (a page left and back, a draft taken
    back), it starts from the list."""
    c.field(key, fresh, label=label)
    columns = _columns(other)
    editor = f"{key}-editor"
    if editor not in st.session_state:
        st.session_state[f"{key}-base"] = st.session_state[key]
    frame = pd.DataFrame(st.session_state[f"{key}-base"], columns=columns)
    config = {
        "id": None,  # hidden: the item keeps its id, so its variable keeps its decisions
        "code": st.column_config.TextColumn(_("Code"), width="small"),
        "text": st.column_config.TextColumn(_("Texte"), width="large"),
    }
    if other:
        config["other"] = st.column_config.CheckboxColumn(_("Autre"), width="small")
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
    return [
        {"id": r.get("id"), "code": r.get("code") or "", "text": r.get("text") or "",
         **({"other": bool(r.get("other"))} if "other" in columns else {})}
        for r in found
    ]  # fmt: skip


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
        "rows": _rows(question.rows, other=False),
    }


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
            for r in _rows_now(_prefix(question_id) + name, _columns(name == "options"))
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
    if question_id == NEW:
        question_id = design.add_question(project, draft)
    else:
        design.modify_question(project, question_id, draft)
    if typed and typed != _fresh(design.find(project, question_id), project)["code"]:
        design.decide_code(project, question_id, "write", now=c.now(), value=typed)


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
        if kind == "grid":
            _table(
                prefix + "options",
                lambda: _fresh_now(question_id, "options"),
                _("Colonnes de la grille : les choix de réponse (code, texte)"),
                other=False,
            )
            _table(
                prefix + "rows",
                lambda: _fresh_now(question_id, "rows"),
                _("Énoncés de la grille (code, texte)"),
                other=False,
            )
        save, cancel, _space = st.columns([1, 1, 3])
        save.button(
            _("Enregistrer"),
            key=f"{prefix}save",
            type="primary",
            on_click=_act,
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
        provenance = _provenance_text(question.provenance)
        if provenance:
            parts.append(provenance)
        st.markdown(" — ".join(parts))
        for point in problems:  # the review's points (D3), settled in the form or kept
            st.markdown(f":material/warning: {point.text}")
        key = f"design-{question.question_id}"
        up, down, edit, remove, _space = st.columns([1, 1, 1, 1, 2])
        up.button(
            _("Monter"),
            key=f"{key}-up",
            icon=":material/arrow_upward:",
            disabled=rank == 1,
            on_click=_act,
            args=(design.move_question, question.question_id, rank - 1),
        )
        down.button(
            _("Descendre"),
            key=f"{key}-down",
            icon=":material/arrow_downward:",
            disabled=rank == total,
            on_click=_act,
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
                on_click=_act,
                args=(design.remove_question, question.question_id),
                kwargs={"done": _("Question retirée.")},
            )


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
              on_click=_act, args=(design.move_section, section.section_id, rank - 1))  # fmt: skip
    down.button(_("Descendre"), key=f"{key}-down", icon=":material/arrow_downward:",
                disabled=rank == total, on_click=_act,
                args=(design.move_section, section.section_id, rank + 1))  # fmt: skip
    with edit.popover(_("Modifier"), icon=":material/edit:"):
        st.text_input(_("Titre de la section"), key=title_key)
        st.text_area(_("Consigne de la section (facultative)"), key=instruction_key)
        st.button(
            _("Enregistrer la section"),
            key=f"{key}-save",
            on_click=_act,
            args=(
                lambda p, s: design.modify_section(
                    p, s, st.session_state[title_key], st.session_state[instruction_key]
                ),
                section.section_id,
            ),
        )
    with remove.popover(_("Retirer"), icon=":material/delete:"):
        st.caption(_("Seule une section sans question se retire."))
        st.button(
            _("Retirer la section"),
            key=f"{key}-remove",
            on_click=_act,
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
    _act(_add_section, key="design-new-section-form", done=_("Section ajoutée."))
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
    if point.page == "design":
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
    c.show_message("design-review")
    found = design_points.points(project)
    if not found:
        st.success(_("Aucun point à voir."))
    numbers = {q.question_id: n for n, q in enumerate(design.questionnaire(project).questions, 1)}
    for index, point in enumerate(found):
        question = design.find(project, point.question)
        with st.container(border=True):
            st.markdown(f"**{numbers.get(point.question, '?')}.** {_excerpt(question.text)}")
            st.write(point.text)
            go, keep, _space = st.columns([1, 1, 2])
            go.button(
                _("Aller à la question") if point.page == "design" else _("Ouvrir la page"),
                key=f"design-review-go-{index}",
                icon=":material/arrow_forward:",
                on_click=_go_to_point,
                args=(point,),
            )
            keep.button(
                _("Garder tel quel"),
                key=f"design-review-keep-{index}",
                on_click=_act,
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
