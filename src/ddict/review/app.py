"""Streamlit review interface. Started by `ddict reviser`, which forces a local address
and turns off Streamlit's usage statistics.

Run as: streamlit run app.py [-- path/to/project.dd.json]
Without a project, the home page opens (v0.3). Every decision is saved to the project file
at once. The views are in `review/ui/`.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from ddict import settings, tracked
from ddict.export.wording import dataset_title
from ddict.i18n import N_, _
from ddict.project import aside, permission
from ddict.review import logic, navigation, shutdown
from ddict.review.ui import (
    ai_view,
    analyses_view,
    base_view,
    bulk_view,
    design_view,
    export_view,
    glossary_view,
    groups_view,
    home_view,
    method_view,
    names_view,
    notebook_view,
    plan_view,
    publish_view,
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


def _dashboard(waiting) -> None:
    """What waits for the team, in the recommended order; each line leads to its page."""
    st.caption(_("À faire") if waiting else _("Rien en attente."))
    for index, task in enumerate(waiting):
        st.button(
            task.text.format(n=task.count),
            key=f"task-{index}",
            on_click=c.go_to_task,
            args=(task.mode, task.filter),
            width="stretch",
        )


def _follow(follow: bool) -> None:
    """Follow the open project, or no longer (v0.17, D-131); its file is never touched."""
    path = c.project_path()
    if not (tracked.follow(path) if follow else tracked.unfollow(path)):
        st.session_state.message = ("error", tracked.not_written(), "follow-project")


def _follow_button() -> None:
    if tracked.is_followed(c.project_path()):
        st.button(
            _("Ne plus suivre"),
            key="follow-project",
            on_click=_follow,
            args=(False,),
            icon=":material/bookmark_remove:",
            help=_(
                "Le projet ne figure plus dans « Mes projets », sur l'accueil. Le fichier "
                "projet n'est pas touché."
            ),
        )
    else:
        st.button(
            _("Suivre ce projet"),
            key="follow-project",
            on_click=_follow,
            args=(True,),
            icon=":material/bookmark_add:",
            help=_("Le projet figurera dans « Mes projets », sur l'accueil."),
        )


AI_ALLOWED = "ai-allowed"
AI_ALLOWED_LABEL = N_("Permettre l'envoi des métadonnées de ce projet à l'IA")


def _allow_ai() -> None:
    """The team's decision (v0.18, D-138), saved like any other (D-129, D-130)."""
    project = c.project()
    if st.session_state[AI_ALLOWED]:
        permission.allow(project, date.today().isoformat())
    else:
        permission.forbid(project)
    c.save(AI_ALLOWED, action=_(AI_ALLOWED_LABEL))


def _ai_permission(project) -> None:
    """The box of the sidebar; drawn from the project at each run, so that a refused save
    (changed elsewhere) shows the project as it is."""
    st.session_state[AI_ALLOWED] = permission.is_allowed(project)
    st.checkbox(
        _(AI_ALLOWED_LABEL),
        key=AI_ALLOWED,
        on_change=_allow_ai,
        help=_(
            "Non cochée par défaut. Cochée, les boutons d'IA peuvent envoyer les métadonnées "
            "du projet (questionnaire et codebook), jamais une réponse ni une statistique ; "
            "la case est enregistrée dans le projet, pour que vos collègues la voient."
        ),
    )
    if permission.is_allowed(project):
        st.caption(_("Permis depuis le {day}.").format(day=project.settings.ai.since))


QUITTING = "quitting"
QUIT_ASK = "quit-ask"  # "Quitter" clicked with something typed and not saved (v0.16)


def _quit() -> None:
    """Stop at once, unless something typed is not saved (v0.16, D-124): then ask first."""
    if st.session_state.get(c.DRAFTS) or c.unsaved():
        st.session_state[QUIT_ASK] = True
    else:
        st.session_state[QUITTING] = True


def _quit_button() -> None:
    """At the bottom of the sidebar (v0.7.1, D-055): the way to stop the tool."""
    st.divider()
    if st.session_state.get(QUIT_ASK):
        st.warning(_("Une saisie n'est pas enregistrée : elle sera perdue."))
        with st.container(horizontal=True):
            st.button(
                _("Quitter quand même"),
                key="quit-anyway",
                on_click=lambda: st.session_state.update({QUITTING: True}),
            )
            st.button(
                _("Annuler"), key="quit-cancel", on_click=lambda: st.session_state.pop(QUIT_ASK)
            )
        return
    st.button(
        _("Quitter l'outil"),
        key="quit",
        on_click=_quit,
        icon=":material/power_settings_new:",
        help=_("Arrête l'outil. Vos décisions sont déjà enregistrées dans le fichier projet."),
    )


def _stopped() -> None:
    st.title(_("L'outil est arrêté."))
    st.write(_("Vous pouvez fermer cette fenêtre. Vos décisions sont enregistrées."))
    shutdown.stop_soon()
    st.stop()


def _place(project, mode: str, chosen: str | None) -> c.Place:
    """Where the page drawn now is, for the drafts (v0.16, D-124)."""
    page = _(navigation.PAGES[mode].title)
    if mode == "variables" and chosen is not None:
        return c.Place(mode, chosen, f"{page}, {chosen}", tuple(c.variable_fields(chosen).items()))
    if mode == "groups" and chosen is not None:
        return c.Place(mode, chosen, f"{page}, {chosen}", (("group", chosen),))
    opened = design_view.opened_question() if mode == "design" else None
    if opened is not None:  # v0.20: the question open in the editor
        shown = _("nouvelle question") if opened == design_view.NEW else opened
        return c.Place(mode, opened, f"{page}, {shown}", ((design_view.OPEN, opened),))
    return c.Place(mode, None, page)


def _root_page(current: str, modes: list[str]) -> str:
    return navigation.root(current, modes, st.context.url)


def _navigation(project, waiting):
    """The pages by phase (v0.16, D-122), each with its state. The session's "mode" names the
    page shown at the root address (the first one, or the one a test chooses); a page asked
    for by a button ("goto", set by `c.go_to`) is opened with `st.switch_page`."""
    counts = navigation.waiting(waiting)
    phases = navigation.sections(project)  # v0.20 (D-149): "Concevoir" for a designed one
    shown_pages = [info for infos in phases.values() for info in infos]
    modes = [info.mode for info in shown_pages]
    current = st.session_state.get("mode")
    root = _root_page(current if current in modes else navigation.first(project), modes)
    pages = {
        info.mode: st.Page(
            lambda: None,  # the page is drawn below, with the sidebar it needs
            title=navigation.title(project, info.mode, counts),
            icon=info.icon,
            url_path=info.mode,
            default=info.mode == root,
        )
        for info in shown_pages
    }
    sections = {
        _(section): [pages[info.mode] for info in infos] for section, infos in phases.items()
    }
    shown = st.navigation(sections, position="sidebar", expanded=True)
    mode = next(m for m, page in pages.items() if page.url_path == shown.url_path)
    goto = st.session_state.pop(c.GOTO, None)
    if goto in pages and goto != mode:
        st.switch_page(pages[goto])
    st.session_state.mode = mode
    shown.run()
    return mode


def _home_navigation() -> str:
    """The tabs of the home page in the sidebar (D-160), never the project's pages: the
    session's "home_tab" names the tab at the root address, as "mode" does for a project;
    a button asking for another tab (`home_view.go_to_tab`) opens it with `st.switch_page`."""
    tabs = list(home_view.TABS)
    current = st.session_state.get(home_view.TAB)
    root = _root_page(current if current in tabs else home_view.FIRST_TAB, tabs)
    pages = {
        tab: st.Page(lambda: None, title=_(title), icon=icon, url_path=tab, default=tab == root)
        for tab, (title, icon) in home_view.TABS.items()
    }
    shown = st.navigation(list(pages.values()), position="sidebar")
    tab = next(t for t, page in pages.items() if page.url_path == shown.url_path)
    goto = st.session_state.pop(c.GOTO, None)
    if goto in pages and goto != tab:
        st.switch_page(pages[goto])
    st.session_state[home_view.TAB] = tab
    shown.run()
    return tab


def main() -> None:
    settings.apply()  # read at each run: a change on the home page applies at once
    st.set_page_config(page_title=_("Révision du dictionnaire"), layout="wide")
    if st.session_state.get(QUITTING):
        _stopped()
    if not c.has_project():
        tab = _home_navigation()
        with st.sidebar:
            _quit_button()
        top = _messages_start()
        home_view.page(tab)
        _messages_end(top)
        return
    project = c.project()
    c.watch(project)  # v0.17 (D-130): changed elsewhere since it was read
    waiting = tasks(project, c.project_path(), notebook_view.dashboard_state(project))
    mode = _navigation(project, waiting)
    with st.sidebar:
        st.button(_("Accueil"), key="home", on_click=c.close_project, icon=":material/home:")
        st.title(dataset_title(project))
        _follow_button()
        _ai_permission(project)
        share = logic.codebook_progress(project)  # v0.16: never full on a new project
        st.progress(share, text=_("Codebook documenté à {p} %").format(p=round(100 * share)))
        _dashboard(waiting)
        chosen = None
        if mode == "variables":
            filters = [
                f
                for f in variables_view.FILTERS
                if (f != "unlinked" or project.questionnaire)
                and (f != "aside" or aside.aside(project))
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
    c.changed_notice()
    notice = st.session_state.pop("notice", None)
    if notice:
        st.info(notice)
    here = _place(project, mode, chosen)
    c.set_place(here.mode, here.item, here.title, **dict(here.opens))
    c.keep_drafts(here)  # v0.16 (D-124): what was typed elsewhere, not saved
    c.drafts_notice(here)
    top = _messages_start()
    if navigation.waits_for_base(project, mode):  # v0.20 (D-145): no database yet
        design_view.waiting_for_base(project, mode)
    elif mode == "design":
        design_view.page(project)
    elif mode == "design_review":
        design_view.review_page(project)
    elif mode == "publish":
        publish_view.page(project)
    elif mode == "base":
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
