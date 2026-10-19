"""The home page (v0.3): the projects followed (v0.17), recent projects, a new project from a
database, a project to open.

Files are chosen with the system's "Open" window (D-020), or by pasting their path. The
database is read here, on this computer, exactly as `ddict profiler` does: the project
file is written next to it.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st

from ddict import i18n, overview, recents, settings, tracked
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

    _projects()  # v0.17: taking up one's work first
    _recent()
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


def _take_up(row: overview.ProjectRow) -> None:
    """Open a followed project on its first task, else on the first page of its phase."""
    mode, which = row.first_page()
    c.open_project(row.path)
    c.go_to_task(mode, which)


def _unfollow(path: Path) -> None:
    if tracked.unfollow(path):
        _message(
            "success",
            _("« {name} » n'est plus suivi ; son fichier n'est pas touché.").format(
                name=overview.ProjectRow(path, None).name
            ),
            "home-unfollow",
        )
    else:
        _message("error", tracked.not_written(), "home-unfollow")


def _find_again(old: Path) -> None:
    """A project not found: the person shows where it is now (v0.17, D-131). The old file
    is gone, so the tool cannot check it is the same project: it refuses only a file that
    is not a readable project, and says its database for the person to judge."""
    key = "home-find"
    chosen = dialog.choose("project")
    if not chosen:
        _message("error", _("Aucun fichier choisi : rien n'est changé."), key)
        return
    try:
        project = load_project(chosen)
    except ProjectError:
        _message(
            "error",
            _("Ce fichier n'est pas un projet lisible : rien n'est changé. ({name})").format(
                name=Path(chosen).name
            ),
            key,
        )
        return
    if not tracked.replace(old, chosen):
        _message("error", tracked.not_written(), key)
        return
    _message(
        "success",
        _(
            "Projet retrouvé : {name}, fait à partir de la base {base}. Si ce n'est pas le "
            "bon, retirez-le avec « Ne plus suivre » dans le menu « ⋮ » de sa ligne."
        ).format(name=Path(chosen).name, base=project.source.name),
        key,
    )


SEARCH = "home-search-result"
FOUND = "home-found-"  # the boxes of the projects found, one per project


def _search() -> None:
    """Choose a folder, look for projects in it (v0.17, D-132); nothing is checked."""
    folder = dialog.choose(dialog.FOLDER)
    if not folder:
        _message("error", _("Aucun dossier choisi."), "home-search")
        return
    for key in [k for k in st.session_state if str(k).startswith(FOUND)]:
        del st.session_state[key]
    st.session_state[SEARCH] = (str(Path(folder)), tracked.search(folder))


def _checked() -> list[Path]:
    _folder, result = st.session_state[SEARCH]
    return [p for i, p in enumerate(result.found) if st.session_state.get(f"{FOUND}{i}")]


def _follow_found() -> None:
    chosen = [p for p in _checked() if not tracked.is_followed(p)]
    if not tracked.follow_all(chosen):
        _message("error", tracked.not_written(), "home-follow-found")
        return
    st.session_state.pop(SEARCH)
    text = _("1 projet suivi.") if len(chosen) == 1 else _("{n} projets suivis.")
    _message("success", text.format(n=len(chosen)), "home-search")


def _search_panel() -> None:
    st.button(
        _("Chercher les projets dans un dossier…"),
        key="home-search",
        on_click=_search,
        icon=":material/manage_search:",
        help=_(
            "Le dossier et ses sous-dossiers, sur 4 niveaux. Seuls les noms des fichiers sont "
            "parcourus : aucun fichier n'est ouvert."
        ),
    )
    c.show_message("home-search")
    if SEARCH not in st.session_state:
        return
    folder, result = st.session_state[SEARCH]
    with st.container(border=True):
        st.subheader(_("Projets trouvés dans {folder}").format(folder=folder))
        if result.stopped == "folders":
            st.warning(
                _("Recherche arrêtée après 20 000 dossiers : choisissez un dossier plus précis.")
            )
        elif result.stopped == "projects":
            st.warning(
                _("Recherche arrêtée après 500 projets : choisissez un dossier plus précis.")
            )
        if not result.found:
            st.write(_("Aucun projet dans ce dossier ni dans ses sous-dossiers (4 niveaux)."))
        followed = {ondisk.key(p) for p in tracked.load()}
        for index, path in enumerate(result.found):
            name = overview.ProjectRow(path, None).name
            if ondisk.key(path) in followed:
                st.checkbox(
                    _("{name} — {folder} (déjà suivi)").format(name=name, folder=path.parent),
                    value=True,
                    disabled=True,
                    key=f"home-followed-{index}",
                )
            else:
                st.checkbox(
                    _("{name} — {folder}").format(name=name, folder=path.parent),
                    key=f"{FOUND}{index}",
                )
        chosen = [p for p in _checked() if ondisk.key(p) not in followed]
        with st.container(horizontal=True):
            st.button(
                _("Suivre ce projet") if len(chosen) == 1
                else _("Suivre ces {n} projets").format(n=len(chosen)),
                key="home-follow-found",
                on_click=_follow_found,
                disabled=not chosen,
                type="primary",
            )  # fmt: skip
            st.button(
                _("Fermer"), key="home-search-close", on_click=lambda: st.session_state.pop(SEARCH)
            )
        c.show_message("home-follow-found")


WIDTHS = [1.9, 1.15, 1, 2.3, 1.5, 1.8, 1.15, 1.2, 0.45]
GAP = "xsmall"  # nine columns: a word as long as "Documenter" holds on one line at 1400 px


def short_folder(folder: Path) -> str:
    """The last two folders of a path, the whole path being in the name's help: a long
    path would take ten lines of the table."""
    parts = folder.parts
    return "…\\" + "\\".join(parts[-2:]) if len(parts) > 3 else str(folder)


def _headers() -> None:
    headers = [
        (_("Projet"), _("Un clic sur le nom ouvre le projet là où quelque chose attend.")),
        (
            _("Phase"),
            _(
                "Documenter tant que rien n'est analysé ; Analyser dès qu'une hypothèse est au "
                "plan ou une analyse au carnet ; Rédiger dès que l'ébauche d'article existe."
            ),
        ),
        (_("Codebook"), _("Le même chiffre que la barre de la barre latérale du projet.")),
        (_("En attente"), _("Le nombre de tâches, et la première.")),
        (_("Plan"), None),
        (
            _("Carnet"),
            _(
                "À recalculer : l'empreinte du codebook a changé depuis le dernier calcul de ces "
                "analyses. Leurs chiffres ont peut-être changé, peut-être pas : ouvrez le carnet "
                "pour le savoir. À confirmer : un nouveau calcul attend votre confirmation."
            ),
        ),
        (
            _("Base"),
            _(
                "Trouvée : un fichier de ce nom est à côté du projet. Le tableau ne lit pas la "
                "base ; l'outil vérifie que c'est la bonne à l'ouverture."
            ),
        ),
        (_("Modifié"), _("La dernière modification du projet ou de son carnet.")),
    ]
    for column, (title, help_text) in zip(st.columns(WIDTHS, gap=GAP), headers, strict=False):
        column.caption(f"**{title}**", help=help_text)


def _projects() -> None:
    """The projects followed (v0.17, § 7 of plan-v0.17): where each is, read from its files
    without its database, the latest changed first; a click on its name takes it up."""
    st.header(_("Mes projets"))
    followed = tracked.load()
    if not followed:
        st.write(
            _(
                "Aucun projet suivi. Un projet créé ici est suivi d'office ; un projet récent "
                "peut l'être avec « Suivre ce projet », et ceux d'un dossier se cherchent "
                "ci-dessous."
            )
        )
        _search_panel()
        return
    _headers()
    for index, row in enumerate(overview.rows(followed)):
        cells = st.columns(WIDTHS, gap=GAP, vertical_alignment="center")
        with cells[0]:
            st.button(
                row.name,
                key=f"home-project-{index}",
                on_click=_take_up,
                args=(row,),
                disabled=row.problem is not None,
                icon=":material/folder_open:",
                help=str(row.path),
            )
            st.caption(short_folder(row.path.parent))
        texts = (
            overview.phase_text, overview.codebook_text, overview.waiting_text,
            overview.plan_text, overview.notebook_text, overview.base_text,
            overview.modified_text,
        )  # fmt: skip
        for cell, text in zip(cells[1:8], texts, strict=True):
            cell.write(text(row))
        with cells[8].popover("", icon=":material/more_vert:"):
            st.button(
                _("Ne plus suivre"),
                key=f"home-unfollow-{index}",
                on_click=_unfollow,
                args=(row.path,),
                icon=":material/bookmark_remove:",
                help=_("Le projet quitte ce tableau ; son fichier n'est pas touché."),
            )
            if row.problem == "missing":
                st.button(
                    _("Le retrouver…"),
                    key=f"home-find-{index}",
                    on_click=_find_again,
                    args=(row.path,),
                    icon=":material/search:",
                    help=_("Montrez où est maintenant ce fichier projet."),
                )
    c.show_message("home-unfollow")
    c.show_message("home-find")
    _search_panel()


def _recent() -> None:
    """The recent projects not followed, latest first: name, folder, last change of the
    project file."""
    followed = {ondisk.key(p) for p in tracked.load()}
    found = [p for p in recents.load() if ondisk.key(p) not in followed]  # v0.17: once
    if not found:
        return
    st.header(_("Projets récents"))
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
        follow.button(  # v0.17 (D-131)
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
