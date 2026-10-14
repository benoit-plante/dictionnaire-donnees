"""Streamlit review interface. Started by `ddict reviser`, which forces a local address
and turns off Streamlit's usage statistics.

Run as: streamlit run app.py [-- path/to/project.dd.json]
Without a project, the home page opens (v0.3). Every decision is saved to the project file
at once. The views are in `review/ui/`.
"""

from __future__ import annotations

import streamlit as st

from ddict.i18n import _
from ddict.review import logic
from ddict.review.ui import (
    ai_view,
    base_view,
    glossary_view,
    groups_view,
    home_view,
    questionnaire_view,
    variables_view,
)
from ddict.review.ui import common as c
from ddict.workflow import tasks

# In the recommended order (v0.3): the database, the questionnaire and its acronyms first.
MODES = {
    "base": _("Base"),
    "questionnaire": _("Questionnaire"),
    "glossary": _("Glossaire"),
    "ai": _("IA locale"),
    "variables": _("Variables"),
    "groups": _("Groupes"),
}


def _messages_start():
    """A message goes next to its button; at the top only when that button is not shown."""
    st.session_state.shown_message = st.session_state.pop("message", None)
    st.session_state.message_placed = False
    return st.empty()


def _messages_end(top) -> None:
    message = st.session_state.pop("shown_message")
    if message and not st.session_state.message_placed:
        (top.error if message[0] == "error" else top.success)(message[1])


def _go(mode: str, which: str | None) -> None:
    st.session_state.mode = mode
    if which is not None:
        st.session_state.filter = which


def _dashboard(project) -> None:
    """What waits for the team, in the recommended order; each line leads to its page."""
    waiting = tasks(project)
    st.caption(_("À faire") if waiting else _("Rien en attente."))
    for index, task in enumerate(waiting):
        st.button(
            task.text.format(n=task.count),
            key=f"task-{index}",
            on_click=_go,
            args=(task.mode, task.filter),
            use_container_width=True,
        )


def main() -> None:
    st.set_page_config(page_title=_("Révision du dictionnaire"), layout="wide")
    if not c.has_project():
        top = _messages_start()
        home_view.page()
        _messages_end(top)
        return
    project = c.project()
    done, total = logic.progress(project)
    with st.sidebar:
        st.button(_("Accueil"), key="home", on_click=c.close_project, icon=":material/home:")
        st.title(project.source.name)
        st.progress(
            done / total if total else 1.0,
            text=_("{done} variables sur {total} sans proposition en attente").format(
                done=done, total=total
            ),
        )
        _dashboard(project)
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
        elif mode == "groups" and project.groups:
            chosen = st.selectbox(_("Groupe"), [g.group_id for g in project.groups], key="group")
        elif mode == "groups":
            st.info(_("Aucun groupe trouvé."))
    notice = st.session_state.pop("notice", None)
    if notice:
        st.info(notice)
    top = _messages_start()
    if mode == "base":
        base_view.page(project)
    elif mode == "questionnaire":
        questionnaire_view.page(project)
    elif mode == "glossary":
        glossary_view.page(project)
    elif mode == "ai":
        ai_view.page(project)
    elif chosen is not None:
        if mode == "variables":
            variables_view.page(project, project.variable(chosen))
        else:
            groups_view.page(project, chosen)
    _messages_end(top)


main()
