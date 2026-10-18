"""Streamlit review interface. Started by `ddict reviser`, which forces a local address
and turns off Streamlit's usage statistics.

Run as: streamlit run app.py [-- path/to/project.dd.json]
Without a project, the home page opens (v0.3). Every decision is saved to the project file
at once. The views are in `review/ui/`.
"""

from __future__ import annotations

import streamlit as st

from ddict import settings
from ddict.i18n import N_, Texts, _
from ddict.review import logic, shutdown
from ddict.review.ui import (
    ai_view,
    analyses_view,
    base_view,
    bulk_view,
    export_view,
    glossary_view,
    groups_view,
    home_view,
    method_view,
    names_view,
    notebook_view,
    plan_view,
    questionnaire_view,
    variables_view,
)
from ddict.review.ui import common as c
from ddict.workflow import tasks

# In the recommended order (v0.3): the database, the questionnaire and its acronyms first.
MODES = Texts(
    {
        "base": N_("Base"),
        "questionnaire": N_("Questionnaire"),
        "glossary": N_("Glossaire"),
        "ai": N_("IA locale"),
        "variables": N_("Variables"),
        "groups": N_("Groupes"),
        "names": N_("Noms"),
        "plan": N_("Plan"),
        "analyses": N_("Analyses"),
        "notebook": N_("Carnet"),
        "method": N_("Méthode"),
        "export": N_("Export"),
    }
)


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
    if which is not None and mode == "names":
        st.session_state[names_view.FILTER] = which
    elif which is not None:
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


QUITTING = "quitting"


def _quit_button() -> None:
    """At the bottom of the sidebar (v0.7.1, D-055): the way to stop the tool."""
    st.divider()
    st.button(
        _("Quitter l'outil"),
        key="quit",
        on_click=lambda: st.session_state.update({QUITTING: True}),
        icon=":material/power_settings_new:",
        help=_("Arrête l'outil. Vos décisions sont déjà enregistrées dans le fichier projet."),
    )


def _stopped() -> None:
    st.title(_("L'outil est arrêté."))
    st.write(_("Vous pouvez fermer cette fenêtre. Vos décisions sont enregistrées."))
    shutdown.stop_soon()
    st.stop()


def main() -> None:
    settings.apply()  # read at each run: a change on the home page applies at once
    st.set_page_config(page_title=_("Révision du dictionnaire"), layout="wide")
    if st.session_state.get(QUITTING):
        _stopped()
    if not c.has_project():
        with st.sidebar:
            _quit_button()
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
        _quit_button()
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
    elif mode == "export":
        export_view.page(project)
    elif mode == "names":
        names_view.page(project)
    elif mode == "plan":
        plan_view.page(project)
    elif mode == "analyses":
        analyses_view.page(project)
    elif mode == "notebook":
        notebook_view.page(project)
    elif mode == "method":
        method_view.page(project)
    elif mode == "variables" and chosen is None:
        bulk_view.links_panel(project)
    elif chosen is not None:
        if mode == "variables":
            bulk_view.links_panel(project)
            variables_view.page(project, project.variable(chosen))
        else:
            groups_view.page(project, chosen)
    _messages_end(top)


main()
