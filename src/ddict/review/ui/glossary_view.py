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


def _glossary_entry(project: Project, item) -> None:
    term = item.term
    key = f"glossary-{term}"
    st.markdown(f"**{term}** — {item.meaning}")
    caption = w.GLOSSARY_ORIGINS[item.origin]
    if item.status != "none":
        caption += f" — {w.GLOSSARY_STATUSES[item.status]}"
    if item.source:
        caption += f" ({item.source})"
    st.caption(caption)
    if item.proposed_meaning:
        st.caption(_("Dans le questionnaire : {v}").format(v=item.proposed_meaning))
    names = glossary.variables_using(project, term)
    if names:
        st.caption(_("Variables : {names}").format(names=", ".join(names)))
    reset = (f"input-{key}",)

    def start() -> str:
        current = glossary.entry(c.project(), term)
        return "" if current is None or current.status == "rejected" else current.meaning

    st.text_input(_("Définition"), key=c.field(f"input-{key}", start))
    if item.status == "proposed":
        # One gesture (v0.16, D-121): "Accepter" takes the meaning shown, corrected or not.
        if st.session_state[f"input-{key}"].strip() != item.meaning:
            st.write(_("« Accepter » enregistrera votre correction ; la définition du "
                       "questionnaire sera gardée comme origine."))  # fmt: skip
        with st.container(horizontal=True):  # side by side (v0.16)
            c.button(
                _("Accepter"),
                f"accept-{key}",
                logic.glossary_accept,
                term,
                c.state(f"input-{key}"),
                timed=True,
                primary=True,
                reset=reset,
                message=False,
            )
            c.button(
                _("Rejeter"),
                f"reject-{key}",
                logic.glossary_decide,
                term,
                "reject",
                timed=True,
                reset=reset,
                message=False,
            )
    c.show_message(f"accept-{key}")
    c.show_message(f"reject-{key}")
    if item.status != "proposed":
        c.button(
            _("Enregistrer"),
            f"save-{key}",
            logic.glossary_write,
            term,
            c.state(f"input-{key}"),
            timed=True,
            reset=reset,
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
            st.write(f"**{part.upper()}** : {', '.join(names)}")

    st.subheader(_("Ajouter un sigle"))
    with st.form("form-glossary-add", border=False):
        c1, c2 = st.columns([1, 3])
        c1.text_input(_("Sigle"), key=c.field("glossary-new-term", str))
        c2.text_input(_("Définition"), key=c.field("glossary-new-meaning", str))
        c.button(
            _("Ajouter"),
            "glossary-add",
            logic.glossary_write,
            c.state("glossary-new-term"),
            c.state("glossary-new-meaning"),
            timed=True,
            reset=("glossary-new-term", "glossary-new-meaning"),
            submit=True,
        )
