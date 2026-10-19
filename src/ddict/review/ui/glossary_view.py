"""The glossary of acronyms (D-015)."""

from __future__ import annotations

import streamlit as st

from ddict import glossary
from ddict.export import wording as w
from ddict.i18n import _
from ddict.project.model import Project
from ddict.review import logic
from ddict.review.ui import bulk_view
from ddict.review.ui import common as c

NEW_TERM = "glossary-new-term"  # the acronym to add, which other pages may fill in (v0.16)


def _glossary_entry(project: Project, item) -> None:
    """An acronym on the common decision card (v0.16, D-121)."""
    term = item.term
    key = f"glossary-{term}"
    input_key = f"input-{key}"
    origin = w.GLOSSARY_ORIGINS[item.origin]
    if item.status != "none":
        origin += f" — {w.GLOSSARY_STATUSES[item.status]}"
    if item.source:
        origin += f" ({item.source})"
    notes = []
    if item.proposed_meaning:
        notes.append(_("Dans le questionnaire : {v}").format(v=item.proposed_meaning))
    names = glossary.variables_using(project, term)
    if names:
        notes.append(_("Variables : {names}").format(names=", ".join(names)))

    def start() -> str:
        current = glossary.entry(c.project(), term)
        return "" if current is None or current.status == "rejected" else current.meaning

    def draw() -> None:
        label = _("Définition de {term}").format(term=term)
        st.text_input(_("Définition"), key=c.field(input_key, start, label=label))

    shown = str(st.session_state.get(input_key, item.meaning)).strip()
    c.decision_card(
        project,
        item,
        key=key,
        title=term,
        show=lambda: st.write(item.meaning),
        field=draw,
        input_key=input_key,
        changed=item.status == "proposed" and shown != item.meaning,
        accept=(logic.glossary_accept, term, c.state(input_key)),
        reject=(logic.glossary_decide, term, "reject"),
        save=(logic.glossary_write, term, c.state(input_key)),
        note=" ; ".join(notes) or None,
        origin_text=origin,
    )
    st.divider()


def page(project: Project) -> None:
    st.header(_("Glossaire des sigles"))
    st.caption(
        _(
            "Les définitions viennent du questionnaire ou de l'équipe ; l'IA n'en propose "
            "jamais. Une définition acceptée aide le modèle et figure dans le codebook."
        )
    )
    shown = {  # what each field shows, corrected or not (D-121)
        e.term: str(st.session_state.get(f"input-glossary-{e.term}") or e.meaning).strip()
        for e in project.glossary
    }
    bulk_view.glossary_panel(project, shown)
    for item in list(project.glossary):
        _glossary_entry(project, item)
    if not project.glossary:
        st.info(_("Aucun sigle pour l'instant."))

    undefined = glossary.undefined_acronyms(project)
    if undefined:
        st.subheader(_("Sigles probables sans définition"))
        for part, names in undefined.items():
            text, button = st.columns([4, 1], vertical_alignment="center")
            text.write(f"**{part.upper()}** : {', '.join(names)}")
            with button:
                c.offer(_("Définir {term}").format(term=part), f"define-{part}", NEW_TERM,
                        part.upper())  # fmt: skip

    st.subheader(_("Ajouter un sigle"))
    with st.form("form-glossary-add", border=False):
        c1, c2 = st.columns([1, 3])
        c1.text_input(_("Sigle"), key=c.field(NEW_TERM, str, label=_("Sigle")))
        c2.text_input(
            _("Définition"), key=c.field("glossary-new-meaning", str, label=_("Définition"))
        )
        c.button(
            _("Ajouter"),
            "glossary-add",
            logic.glossary_write,
            c.state(NEW_TERM),
            c.state("glossary-new-meaning"),
            timed=True,
            reset=(NEW_TERM, "glossary-new-meaning"),
            submit=True,
        )
