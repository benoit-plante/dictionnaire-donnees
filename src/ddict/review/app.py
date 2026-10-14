"""Streamlit review interface. Started by `ddict reviser`, which forces a local address
and turns off Streamlit's usage statistics.

Run as: streamlit run app.py -- path/to/project.dd.json
Every decision is saved to the project file at once. The views are in `review/ui/`.
"""

from __future__ import annotations

import streamlit as st

from ddict.i18n import _
from ddict.review import logic
from ddict.review.ui import common as c
from ddict.review.ui import glossary_view, groups_view, variables_view

MODES = {"variables": _("Variables"), "groups": _("Groupes"), "glossary": _("Glossaire")}


def main() -> None:
    st.set_page_config(page_title=_("Révision du dictionnaire"), layout="wide")
    project = c.project()
    done, total = logic.progress(project)
    with st.sidebar:
        st.title(project.source.name)
        st.progress(
            done / total if total else 1.0,
            text=_("{done} variables sur {total} sans proposition en attente").format(
                done=done, total=total
            ),
        )
        mode = st.radio(_("Afficher"), list(MODES), key="mode", format_func=MODES.__getitem__)
        chosen = None
        if mode == "variables":
            filters = [
                f for f in variables_view.FILTERS if f != "unlinked" or project.questionnaire
            ]
            which = st.radio(
                _("Filtre"), filters, key="filter", format_func=variables_view.FILTERS.__getitem__
            )
            names = [e.name for e in logic.select(project, which)]
            variables_view.choose_variable(project, names, which)
            if names:
                chosen = st.selectbox(
                    _("Variable"),
                    names,
                    key="variable",
                    format_func=lambda n: variables_view.option_text(project, n),
                    on_change=variables_view.remember_variable,
                )
            else:
                st.info(_("Aucune variable dans ce filtre."))
        elif mode == "glossary":
            pending = sum(1 for e in project.glossary if e.status == "proposed")
            st.caption(
                _("{n} sigles, dont {p} à valider").format(n=len(project.glossary), p=pending)
            )
        elif project.groups:
            chosen = st.selectbox(_("Groupe"), [g.group_id for g in project.groups], key="group")
        else:
            st.info(_("Aucun groupe trouvé."))
    notice = st.session_state.pop("notice", None)
    if notice:
        st.info(notice)
    # A message goes next to its button; at the top only when that button is not shown.
    st.session_state.shown_message = st.session_state.pop("message", None)
    st.session_state.message_placed = False
    top = st.empty()
    if mode == "glossary":
        glossary_view.page(project)
    elif chosen is not None:
        if mode == "variables":
            variables_view.page(project, project.variable(chosen))
        else:
            groups_view.page(project, chosen)
    message = st.session_state.pop("shown_message")
    if message and not st.session_state.message_placed:
        (top.error if message[0] == "error" else top.success)(message[1])


main()
