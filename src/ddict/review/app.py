"""Streamlit review interface. Started by `ddict reviser`, which forces a local address
and turns off Streamlit's usage statistics.

Run as: streamlit run app.py [-- path/to/project.dd.json]
Without a project, the home page opens (v0.3). Every decision is saved to the project file
at once. The views are in `review/ui/`.
"""

from __future__ import annotations

from urllib.parse import urlparse

import streamlit as st

from ddict import settings
from ddict.i18n import _
from ddict.review import logic, navigation, shutdown
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
    verify_view,
)
from ddict.review.ui import common as c
from ddict.workflow import tasks


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
    if which is not None and mode == "names":
        c.go_to(mode, **{names_view.FILTER: which})
    elif which is not None:
        c.go_to(mode, filter=which)
    else:
        c.go_to(mode)


def _dashboard(waiting) -> None:
    """What waits for the team, in the recommended order; each line leads to its page."""
    st.caption(_("À faire") if waiting else _("Rien en attente."))
    for index, task in enumerate(waiting):
        st.button(
            task.text.format(n=task.count),
            key=f"task-{index}",
            on_click=_go,
            args=(task.mode, task.filter),
            width="stretch",
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


def _root_page() -> str:
    """The page at the root address: the session's "mode", the first page otherwise. Never
    the page the address asks for by name: Streamlit serves the root page at the root only,
    and a reload on "/base" would say "Page not found"."""
    current = st.session_state.get("mode")
    if current not in navigation.PAGES:
        current = navigation.FIRST
    asked = urlparse(st.context.url or "").path.rstrip("/").rsplit("/", 1)[-1]
    if asked != current:
        return current
    return next(m for m in navigation.PAGES if m != current)


def _navigation(project, waiting):
    """The pages by phase (v0.16, D-122), each with its state. The session's "mode" names the
    page shown at the root address (the first one, or the one a test chooses); a page asked
    for by a button ("goto", set by `c.go_to`) is opened with `st.switch_page`."""
    counts = navigation.waiting(waiting)
    root = _root_page()
    pages = {
        info.mode: st.Page(
            lambda: None,  # the page is drawn below, with the sidebar it needs
            title=navigation.title(project, info.mode, counts),
            icon=info.icon,
            url_path=info.mode,
            default=info.mode == root,
        )
        for info in navigation.PAGES.values()
    }
    sections = {
        _(section): [pages[info.mode] for info in infos]
        for section, infos in navigation.SECTIONS.items()
    }
    shown = st.navigation(sections, position="sidebar", expanded=True)
    mode = next(m for m, page in pages.items() if page.url_path == shown.url_path)
    goto = st.session_state.pop(c.GOTO, None)
    if goto in pages and goto != mode:
        st.switch_page(pages[goto])
    st.session_state.mode = mode
    shown.run()
    return mode


def main() -> None:
    settings.apply()  # read at each run: a change on the home page applies at once
    st.set_page_config(page_title=_("Révision du dictionnaire"), layout="wide")
    if st.session_state.get(QUITTING):
        _stopped()
    if not c.has_project():
        # The home page is a page of its own, without the project's (v0.16): the menu of the
        # project's pages would stay on screen otherwise.
        st.navigation(
            [st.Page(lambda: None, title=_("Accueil"), url_path="accueil", default=True)],
            position="hidden",
        ).run()
        with st.sidebar:
            _quit_button()
        top = _messages_start()
        home_view.page()
        _messages_end(top)
        return
    project = c.project()
    waiting = tasks(project, c.project_path(), notebook_view.dashboard_state(project))
    mode = _navigation(project, waiting)
    with st.sidebar:
        st.button(_("Accueil"), key="home", on_click=c.close_project, icon=":material/home:")
        st.title(project.source.name)
        share = logic.codebook_progress(project)  # v0.16: never full on a new project
        st.progress(share, text=_("Codebook documenté à {p} %").format(p=round(100 * share)))
        _dashboard(waiting)
        chosen = None
        if mode == "variables":
            filters = [
                f for f in variables_view.FILTERS if f != "unlinked" or project.questionnaire
            ]
            if st.session_state.get("filter") not in filters:  # v0.16: never an empty page
                st.session_state.filter = variables_view.default_filter(project)
            which = st.radio(
                _("Filtre"), filters, key="filter", format_func=variables_view.FILTERS.__getitem__
            )
            names = [e.name for e in logic.select(project, which)]
            variables_view.choose_variable(project, names, which)
            if names:
                chosen = st.selectbox(
                    _("Variable"),
                    names,
                    placeholder=_("Choisir…"),
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
            chosen = st.selectbox(
                _("Groupe"),
                [g.group_id for g in project.groups],
                placeholder=_("Choisir…"),
                key="group",
                # v0.16 (finding 20): what the group is, not only its number.
                format_func=lambda g: groups_view.option_text(project, g),
            )
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
    elif mode == "verify":
        verify_view.page(project)
    elif mode == "method":
        method_view.page(project)
    elif mode == "variables" and chosen is None:
        bulk_view.links_panel(project)
        variables_view.empty_filter(project, which, filters)
    elif mode == "variables":
        variables_view.neighbours(names, chosen)  # v0.16 (finding 23): at the top
        bulk_view.links_panel(project)
        variables_view.page(project, project.variable(chosen))
        questionnaire_view.ai_link("variables")
    elif mode == "groups":
        groups_view.page(project, chosen)
    _messages_end(top)


main()
