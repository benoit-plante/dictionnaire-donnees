"""The home page (v0.3): a new project from a database, a project to open, recent projects.

Files are chosen with the system's "Open" window (D-020), or by pasting their path. The
database is read here, on this computer, exactly as `ddict profiler` does: the project
file is written next to it.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st

from ddict import i18n, recents, settings, tracked
from ddict.i18n import _
from ddict.io import ReadError
from ddict.project import ProjectError, load_project, ondisk
from ddict.review import trial
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
    if not tracked.follow(output):  # v0.17 (D-131): a new project is followed
        _message("error", tracked.not_written(), key)


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


def _follow(path: Path, key: str) -> None:
    if tracked.follow(path):
        _message("success", _("Ce projet est maintenant suivi."), key)
    else:
        _message("error", tracked.not_written(), key)


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
    if i18n.language() == "en":  # v0.5: a trial (D-034)
        st.caption(
            "The English interface is a trial version: its translation has not yet been "
            "reviewed by a native speaker. Please report anything unclear."
        )
    st.title(_("Dictionnaire de données"))
    st.caption(
        _(
            "Tout se passe sur cet ordinateur : les fichiers sont lus ici, et rien n'est "
            "envoyé ailleurs."
        )
    )

    _recent()  # v0.16 (finding 16): taking up one's work first
    _trial()
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


def _modified(path: Path) -> str:
    try:
        moment = datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return ""
    return moment.strftime("%Y-%m-%d %H:%M")


def _recent() -> None:
    """The recent projects, latest first: name, folder, last change of the project file."""
    found = recents.load()
    if not found:
        return
    st.header(_("Projets récents"))
    followed = {ondisk.key(p) for p in tracked.load()}
    for index, path in enumerate(found):
        name, where, when, follow = st.columns([2, 4, 1.4, 1.6], vertical_alignment="center")
        with name:
            st.button(
                path.name,
                key=f"home-recent-{index}",
                on_click=_open,
                args=(path, f"home-recent-{index}"),
                icon=":material/folder_open:",
            )
        where.write(str(path.parent))
        when.write(_modified(path))
        if ondisk.key(path) in followed:  # v0.17 (D-131)
            follow.caption(_("Suivi"))
        else:
            follow.button(
                _("Suivre ce projet"),
                key=f"home-follow-{index}",
                on_click=_follow,
                args=(path, f"home-follow-{index}"),
                icon=":material/bookmark_add:",
            )
        c.show_message(f"home-recent-{index}")
        c.show_message(f"home-follow-{index}")
    with st.container(horizontal=True, vertical_alignment="center"):
        st.button(_("Effacer la liste"), key="home-clear", on_click=_clear_recents)
        st.caption(
            _(
                "La liste est gardée sur cet ordinateur ; elle ne contient que les chemins des "
                "fichiers projet."
            )
        )
    c.show_message("home-clear")


def _start_trial(again: bool) -> None:
    key = "home-trial-again" if again else "home-trial"
    try:
        path = trial.start(again=again)
    except (OSError, ReadError, ProjectError) as error:
        _message("error", _("Impossible de préparer l'essai : {detail}").format(detail=error),
                 key)  # fmt: skip
        return
    c.open_project(path)


def _trial() -> None:
    """Try the tool on the fictional database (v0.16, D-125)."""
    st.header(_("Essayer l'outil"))
    where = trial.folder()
    st.write(
        _(
            "Sur une base fictive de 200 personnes et son questionnaire, copiés dans le "
            "dossier {folder}. Rien de réel ; les fichiers de l'essai s'écrivent là."
        ).format(folder=where)
    )
    exists = trial.project_path(where).is_file()
    st.button(
        _("Reprendre l'essai") if exists else _("Essayer avec la base fictive"),
        key="home-trial",
        on_click=_start_trial,
        args=(False,),
        icon=":material/science:",
    )
    c.show_message("home-trial")
    if exists:
        with st.expander(_("Recommencer l'essai")):
            st.checkbox(
                _("Je recommence : les décisions de l'essai seront perdues."),
                key="home-trial-sure",
            )
            st.button(
                _("Recommencer l'essai"),
                key="home-trial-again",
                on_click=_start_trial,
                args=(True,),
                disabled=not st.session_state.get("home-trial-sure"),
            )
            c.show_message("home-trial-again")
