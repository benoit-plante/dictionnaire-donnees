"""The home page (v0.3): a new project from a database, a project to open, recent projects.

Files are chosen with the system's "Open" window (D-020), or by pasting their path. The
database is read here, on this computer, exactly as `ddict profiler` does: the project
file is written next to it.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from ddict import i18n, recents, settings
from ddict.i18n import _
from ddict.io import ReadError
from ddict.project import ProjectError, load_project
from ddict.review.ui import common as c
from ddict.review.ui import dialog
from ddict.workflow import ProjectExists, default_project_path, profile_database

DATABASE = "home-database"
LANGUAGE = "interface-language"
PROJECT = "home-project"


def _message(kind: str, text: str, key: str) -> None:
    st.session_state.message = (kind, text, key)


def _browse(kind: str, field: str) -> None:
    path = dialog.choose(kind)
    if path:
        st.session_state[field] = path
    else:
        _message(
            "error",
            _("Aucun fichier choisi. Vous pouvez aussi coller son chemin dans le champ."),
            f"browse-{field}",
        )


def _path(field: str) -> Path | None:
    text = str(st.session_state.get(field) or "").strip().strip('"')
    return Path(text) if text else None


def _create(replace: bool) -> None:
    key = "home-create"
    database = _path(DATABASE)
    if database is None or not database.is_file():
        _message("error", _("Choisissez d'abord une base de données existante."), key)
        return
    try:
        _project, output = profile_database(database, replace=replace)
    except ProjectExists as error:
        st.session_state.existing = str(error)
        _message(
            "error",
            _(
                "Un projet existe déjà pour cette base : {name}. Ouvrez-le pour reprendre "
                "votre travail, ou remplacez-le (ses décisions seront perdues)."
            ).format(name=Path(str(error)).name),
            key,
        )
        return
    except ReadError as error:
        _message("error", _("Impossible de lire la base : {detail}").format(detail=error), key)
        return
    c.open_project(output)


def _open(path: Path | None, key: str) -> None:
    if path is None or not path.is_file():
        _message("error", _("Ce fichier projet est introuvable."), key)
        return
    try:
        load_project(path)
    except ProjectError as error:
        _message("error", _("Impossible de lire le projet : {detail}").format(detail=error), key)
        return
    c.open_project(path)


def _clear_recents() -> None:
    recents.clear()
    _message("success", _("Liste effacée."), "home-clear")


def _change_language() -> None:
    chosen = st.session_state[LANGUAGE]
    if chosen is None:  # the chosen language clicked again: nothing changes
        return
    settings.save_interface_language(chosen)
    i18n.set_language(chosen)


def _language() -> None:
    """French or English, for this computer (v0.5, D-032); shown in both languages."""
    st.session_state[LANGUAGE] = i18n.language()
    st.segmented_control(
        "Langue · Language",
        list(i18n.LANGUAGES),
        key=LANGUAGE,
        format_func=i18n.LANGUAGES.__getitem__,
        on_change=_change_language,
        label_visibility="collapsed",
    )


def page() -> None:
    _language()
    st.title(_("Dictionnaire de données"))
    st.caption(
        _(
            "Tout se passe sur cet ordinateur : les fichiers sont lus ici, et rien n'est "
            "envoyé ailleurs."
        )
    )

    st.header(_("Nouveau projet"))
    st.write(
        _(
            "Choisissez la base de données : SPSS (.sav), CSV, Stata (.dta), SAS (.sas7bdat) "
            "ou Excel (.xlsx). Le fichier projet sera créé à côté d'elle ; la base n'est "
            "jamais modifiée."
        )
    )
    st.button(
        _("Choisir une base…"),
        key=f"browse-{DATABASE}",
        on_click=_browse,
        args=("database", DATABASE),
        type="primary",
    )
    c.show_message(f"browse-{DATABASE}")
    st.text_input(_("ou collez le chemin du fichier"), key=DATABASE)
    database = _path(DATABASE)
    if database is not None:
        st.caption(_("Fichier projet : {path}").format(path=default_project_path(database).name))
    st.button(_("Créer le projet"), key="home-create", on_click=_create, args=(False,))
    c.show_message("home-create")
    existing = st.session_state.get("existing")
    if existing and database is not None and default_project_path(database) == Path(existing):
        left, right = st.columns(2)
        left.button(
            _("Ouvrir le projet existant"),
            key="home-open-existing",
            on_click=_open,
            args=(Path(existing), "home-open-existing"),
            type="primary",
        )
        right.button(
            _("Remplacer le projet"),
            key="home-replace",
            on_click=_create,
            args=(True,),
        )

    st.header(_("Ouvrir un projet"))
    st.button(
        _("Choisir un fichier projet…"),
        key=f"browse-{PROJECT}",
        on_click=_browse,
        args=("project", PROJECT),
    )
    c.show_message(f"browse-{PROJECT}")
    st.text_input(_("ou collez le chemin du fichier projet (.dd.json)"), key=PROJECT)
    st.button(
        _("Ouvrir"),
        key="home-open",
        on_click=lambda: _open(_path(PROJECT), "home-open"),
    )
    c.show_message("home-open")

    st.header(_("Projets récents"))
    found = recents.load()
    if not found:
        st.caption(_("Aucun projet récent."))
    for index, path in enumerate(found):
        st.button(
            path.name,
            key=f"home-recent-{index}",
            on_click=_open,
            args=(path, f"home-recent-{index}"),
            help=str(path.parent),
        )
        st.caption(str(path.parent))
        c.show_message(f"home-recent-{index}")
    if found:
        st.button(_("Effacer la liste"), key="home-clear", on_click=_clear_recents)
    c.show_message("home-clear")
    st.caption(
        _(
            "La liste est gardée sur cet ordinateur ; elle ne contient que les chemins des "
            "fichiers projet."
        )
    )
