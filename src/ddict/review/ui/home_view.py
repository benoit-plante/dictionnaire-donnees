"""The home page (v0.3), in tabs chosen in the sidebar (D-160): the projects followed
(v0.17), a new project from a database, a questionnaire to design (v0.20), a project to open
(a file, the recent projects, the projects of a folder), the settings of this computer.

Files are chosen with the system's "Open" window (D-020), or by pasting their path. The
database is read here, on this computer, exactly as `ddict profiler` does: the project
file is written next to it.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path

import streamlit as st

from ddict import i18n, overview, recents, settings, tracked
from ddict.design import DesignError
from ddict.i18n import N_, _
from ddict.io import ReadError
from ddict.project import ProjectError, load_project, ondisk, title
from ddict.review.ui import common as c
from ddict.review.ui import dialog
from ddict.workflow import (
    ProjectExists,
    create_design,
    default_project_path,
    design_path,
    profile_database,
)

DATABASE = "home-database"
# v0.20 (D-145): a questionnaire to design, in a folder, before its collection.
DESIGN_FOLDER, DESIGN_NAME, DESIGN_LANGUAGE = (
    "home-design-folder",
    "home-design-name",
    "home-design-language",
)
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


def _browse_folder() -> None:
    folder = dialog.choose(dialog.FOLDER)
    if folder:
        st.session_state[DESIGN_FOLDER] = folder
    else:
        _message(
            "error",
            _("Aucun dossier choisi. Vous pouvez aussi coller son chemin dans le champ."),
            "home-design-browse",
        )


def _create_design() -> None:
    """A project to design a questionnaire, before its collection (v0.20, D-145)."""
    key = "home-design-create"
    folder = _path(DESIGN_FOLDER)
    name = str(st.session_state.get(DESIGN_NAME) or "")
    if folder is None or not folder.is_dir():
        _message("error", _("Choisissez d'abord le dossier du projet."), key)
        return
    try:
        path = create_design(
            folder, name, st.session_state.get(DESIGN_LANGUAGE) or "fr", date.today().isoformat()
        )
    except DesignError as error:
        _message("error", " ".join(error.reasons), key)
        return
    except ProjectExists as error:
        _message(
            "error",
            _(
                "Un projet de ce nom existe déjà dans ce dossier : {name}. Ouvrez-le, ou "
                "choisissez un autre nom."
            ).format(name=Path(str(error)).name),
            key,
        )
        return
    c.open_project(path)
    if not tracked.follow(path):  # v0.17 (D-131): a new project is followed
        _message("error", tracked.not_written(), key)


def _design_section() -> None:
    st.write(
        _(
            "Pour une étude qui n'a pas encore de questionnaire : construisez-le dans l'outil, "
            "et le dictionnaire de données existe avant la collecte. Le fichier projet est "
            "créé dans le dossier choisi."
        )
    )
    st.button(_("Choisir un dossier…"), key="home-design-browse", on_click=_browse_folder)
    c.show_message("home-design-browse")
    st.text_input(_("ou collez le chemin du dossier"), key=DESIGN_FOLDER)
    st.text_input(_("Nom du questionnaire"), key=DESIGN_NAME)
    st.segmented_control(
        _("Langue de l'étude"),
        ["fr", "en"],
        key=DESIGN_LANGUAGE,
        default="fr",
        format_func={"fr": _("Français"), "en": _("Anglais")}.__getitem__,
    )
    folder, name = _path(DESIGN_FOLDER), str(st.session_state.get(DESIGN_NAME) or "").strip()
    if folder is not None and name:
        st.caption(_("Fichier projet : {path}").format(path=design_path(folder, name).name))
    st.button(_("Créer le questionnaire"), key="home-design-create", on_click=_create_design)
    c.show_message("home-design-create")


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


TAB = "home_tab"  # the tab shown (D-160): tests choose it, as "mode" chooses a project's page
# The tabs of the home page, in the sidebar (D-160): their address, title and icon.
TABS = {
    "projets": (N_("Mes projets"), ":material/folder_special:"),
    "nouveau": (N_("Nouveau projet"), ":material/add_circle:"),
    "concevoir": (N_("Concevoir un questionnaire"), ":material/edit_note:"),
    "ouvrir": (N_("Ouvrir un projet"), ":material/folder_open:"),
    "reglages": (N_("Réglages"), ":material/settings:"),
}
FIRST_TAB = "projets"


def go_to_tab(tab: str) -> None:
    """Open another tab of the home page, as `c.go_to` opens a project's page."""
    st.session_state[c.GOTO] = tab
    st.session_state[TAB] = tab


def page(tab: str) -> bool:
    """The tab of the home page shown in the window (D-160); whether it put the projects
    followed in the sidebar."""
    if i18n.language() == "en":  # v0.5: a trial (D-034)
        st.caption(
            "The English interface is a trial version: its translation has not yet been "
            "reviewed by a native speaker. Please report anything unclear."
        )
    st.title(_(TABS[tab][0]))
    st.caption(
        _(
            "Tout se passe sur cet ordinateur : les fichiers sont lus ici, et rien n'est "
            "envoyé ailleurs."
        )
    )
    listed = {
        "projets": _projects,
        "nouveau": _new_section,
        "concevoir": _design_section,
        "ouvrir": _open_section,
        "reglages": _settings_section,
    }[tab]()
    return bool(listed)


def _settings_section() -> None:
    st.subheader("Langue · Language")
    _language()
    st.caption(
        _(
            "Pour cet ordinateur. Les textes écrits par l'équipe ne sont jamais traduits : la "
            "langue de l'étude se choisit dans chaque projet."
        )
    )


def _new_section() -> None:
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


def _open_section() -> None:
    """A project file, the recent projects, the projects of a folder (D-160)."""
    st.subheader(_("Un fichier projet"))
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
    _recent()
    st.subheader(_("Chercher les projets d'un dossier"))
    _search_panel()


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
                name=overview.row(path).name  # its title, when it has one
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
    _choose(Path(chosen))  # the detail shows it, where the missing one was
    if project.source is None:  # designed before its collection (v0.20)
        text = _(
            "Projet retrouvé : {name}, un questionnaire conçu dans l'outil, sans base encore. "
            "Si ce n'est pas le bon, retirez-le avec « Ne plus suivre », dans son détail."
        ).format(name=Path(chosen).name)
    else:
        text = _(
            "Projet retrouvé : {name}, fait à partir de la base {base}. Si ce n'est pas le "
            "bon, retirez-le avec « Ne plus suivre », dans son détail."
        ).format(name=Path(chosen).name, base=project.source.name)
    _message("success", text, key)


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


CHOSEN = "home-chosen"  # the project shown in "Mes projets", by its path (D-160)
ICONS = {
    overview.DESIGN: ":material/edit_note:",
    overview.COLLECT: ":material/schedule:",
    overview.DOCUMENT: ":material/description:",
    overview.ANALYSE: ":material/query_stats:",
    overview.WRITE: ":material/article:",
}
SEPARATOR = " \N{SINGLE RIGHT-POINTING ANGLE QUOTATION MARK} "  # between the phases
PROBLEMS = {
    "missing": N_("Introuvable"),
    "unreadable": N_("Illisible"),
    "newer": N_("Version plus récente"),
}


def _choose(path: Path) -> None:
    st.session_state[CHOSEN] = str(path)


def back_home() -> None:
    """Close the project; "Mes projets" shows it, where one left it."""
    path = c.project_path()
    c.close_project()
    _choose(path)


def _chosen(rows: list[overview.ProjectRow]) -> overview.ProjectRow:
    """The project shown: the one chosen, else the latest changed."""
    wanted = st.session_state.get(CHOSEN)
    key = ondisk.key(Path(wanted)) if wanted else None
    return next((r for r in rows if ondisk.key(r.path) == key), rows[0])


def _project_list(rows: list[overview.ProjectRow], shown: overview.ProjectRow) -> None:
    """The projects followed, in the sidebar under the menu (D-160): name and phase, or what
    is wrong; a click shows the project, without opening it."""
    st.caption("**" + _("Projets suivis") + "**")
    for index, row in enumerate(rows):
        state = _(PROBLEMS[row.problem]) if row.problem else overview.phase_text(row)
        st.button(
            f"{row.name}  \n{state}",
            key=f"home-project-{index}",
            on_click=_choose,
            args=(row.path,),
            icon=":material/warning:" if row.problem else ICONS.get(row.phase),
            type="primary" if row.path == shown.path else "secondary",
            width="stretch",
            help=str(row.path),
        )


def _open_folder(folder: Path) -> None:
    """Show the project's folder in Windows' file manager."""
    try:
        os.startfile(folder)  # Windows only (D-081)
    except OSError as error:
        _message(
            "error",
            _("Impossible d'ouvrir le dossier : {detail}").format(detail=error),
            "home-folder",
        )


def _open_task(row: overview.ProjectRow, index: int) -> None:
    """Open the project on the page of one of its tasks."""
    task = row.tasks[index]
    c.open_project(row.path)
    c.go_to_task(task.mode, task.filter)


def _phases(row: overview.ProjectRow) -> str:
    """The phases in order, the project's in bold: where it is, and what comes next; the
    two phases of a design (D-154) for a project designed in the tool."""
    phases = overview.PHASES if row.designed else overview.PHASES[2:]
    return SEPARATOR.join(f"**{_(p)}**" if p == row.phase else _(p) for p in phases)


def _bold(text: str) -> None:
    st.markdown("**" + text + "**")


def _folder_button(row: overview.ProjectRow) -> None:
    st.button(
        _("Ouvrir le dossier"),
        key="home-folder",
        on_click=_open_folder,
        args=(row.path.parent,),
        icon=":material/folder:",
    )


def _unfollow_button(row: overview.ProjectRow) -> None:
    st.button(
        _("Ne plus suivre"),
        key="home-unfollow",
        on_click=_unfollow,
        args=(row.path,),
        icon=":material/bookmark_remove:",
        help=_("Le projet quitte « Mes projets » ; son fichier n'est pas touché."),
    )


def _problem(row: overview.ProjectRow) -> None:
    """A project not found, unreadable or written by a newer tool: what is known of it."""
    st.warning(overview.waiting_text(row))
    st.caption(str(row.path))
    with st.container(horizontal=True):
        if row.problem == "missing":
            st.button(
                _("Le retrouver…"),
                key="home-find",
                on_click=_find_again,
                args=(row.path,),
                icon=":material/search:",
                type="primary",
                help=_("Montrez où est maintenant ce fichier projet."),
            )
        else:
            _folder_button(row)
        _unfollow_button(row)


def _tasks(row: overview.ProjectRow) -> None:
    if not row.tasks:
        _bold(_("Rien en attente."))
        return
    _bold(_("En attente ({n})").format(n=len(row.tasks)))
    with st.container(gap=None):
        for index, task in enumerate(row.tasks):
            st.button(
                task.text.format(n=task.count),
                key=f"home-task-{index}",
                on_click=_open_task,
                args=(row, index),
                icon=":material/arrow_forward:",
                type="tertiary",
            )


TITLE, TITLE_FOR = "home-title", "home-title-for"  # the field, and the project it is of


def _save_title(path: Path, text: str) -> None:
    """Give the project not open its title, or take it off (D-161); no file is renamed."""
    key = "home-title"
    try:
        project = title.rename(path, text)
    except title.TitleError as error:
        _message("error", str(error), key)
        return
    except ProjectError as error:
        _message("error", _("Impossible de lire le projet : {detail}").format(detail=error), key)
        return
    except ondisk.FileChanged:
        _message(
            "error",
            _(
                "Ce projet a été modifié ailleurs pendant l'enregistrement : le titre n'est pas "
                "enregistré. Réessayez."
            ),
            key,
        )
        return
    except ondisk.FileBusy:
        _message(
            "error",
            _(
                "Le fichier est occupé, peut-être par la synchronisation de OneDrive : rien "
                "n'est enregistré. Réessayez dans un instant."
            ),
            key,
        )
        return
    st.session_state[TITLE] = project.title or ""
    if project.title:
        _message("success", _("Titre enregistré. Aucun fichier n'est renommé."), key)
    else:
        _message("success", _("Le projet reprend le nom de son fichier."), key)


def _rename(row: overview.ProjectRow) -> None:
    """ "Renommer": the title, written in the project file; the files keep their names."""
    if st.session_state.get(TITLE_FOR) != str(row.path):  # another project shown
        st.session_state[TITLE] = row.title or ""
        st.session_state[TITLE_FOR] = str(row.path)
    with st.popover(_("Renommer"), icon=":material/edit:"):
        st.text_input(
            _("Titre du projet"),
            key=TITLE,
            max_chars=title.MAX_LENGTH,
            placeholder=row.file_name,
            help=_(
                "Montré à la place du nom du fichier, ici et dans le projet ouvert. Jamais "
                "envoyé à l'IA."
            ),
        )
        st.caption(_("Le fichier garde son nom : {name}.").format(name=row.path.name))
        with st.container(horizontal=True):
            st.button(
                _("Enregistrer le titre"),
                key="home-title-save",
                on_click=lambda: _save_title(row.path, st.session_state[TITLE]),
                type="primary",
            )
            if row.title:
                st.button(
                    _("Revenir au nom du fichier"),
                    key="home-title-clear",
                    on_click=_save_title,
                    args=(row.path, ""),
                )


def _detail(row: overview.ProjectRow) -> None:
    """What the project is, read from its files without its database (plan-accueil, § 7.3)."""
    st.subheader(row.name)
    if row.problem:
        _problem(row)
        return
    st.caption(
        _("{path} · modifié le {date}").format(path=row.path, date=overview.modified_text(row))
    )
    with st.container(horizontal=True):
        st.button(
            _("Ouvrir"),
            key="home-open-chosen",
            on_click=_take_up,
            args=(row,),
            icon=":material/folder_open:",
            type="primary",
            help=_("Le projet s'ouvre là où quelque chose attend."),
        )
        _rename(row)
        _folder_button(row)
        _unfollow_button(row)
    c.show_message("home-title")
    st.markdown(_phases(row))
    share = row.codebook or 0
    st.progress(share, text=_("Codebook documenté à {p} %").format(p=round(100 * share)))
    _tasks(row)
    left, right = st.columns(2)
    with left:
        _bold(_("Plan d'analyse"))
        st.write(overview.plan_text(row))
        _bold(_("Base"))
        st.write(_base_text(row))
    with right:
        _bold(_("Carnet"))
        st.write(_("Pas encore de carnet") if row.notebook is None else overview.notebook_text(row))
        _bold(_("Questionnaire"))
        st.write(_questionnaire_text(row))
    files = overview.produced(row)
    heading = _("Fichiers produits à côté du projet ({n})").format(n=len(files))
    with st.expander(heading, expanded=bool(files)):
        if files:
            st.markdown("\n".join(f"- {name}" for name in files))
        else:
            st.write(_("Aucun pour l'instant."))


def _base_text(row: overview.ProjectRow) -> str:
    if row.source is None:
        return _("Pas encore : le questionnaire est en conception.")
    if row.base:
        return _("{name} — trouvée à côté du projet").format(name=row.source)
    return _("{name} — introuvable à côté du projet").format(name=row.source)


def _questionnaire_text(row: overview.ProjectRow) -> str:
    if row.questionnaire is None:
        return _("Aucun")
    if row.designed:
        return _("Conçu dans l'outil : {name}").format(name=row.questionnaire)
    if row.questionnaire_found:
        return _("{name} — trouvé à côté du projet").format(name=row.questionnaire)
    return _("{name} — introuvable à côté du projet").format(name=row.questionnaire)


def _projects() -> bool:
    """The projects followed (D-160): the list in the sidebar, the latest changed first, and
    the detail of the one chosen in the window; nothing is read but the project and its
    notebook, never its database."""
    followed = tracked.load()
    if not followed:
        st.write(
            _(
                "Aucun projet suivi. Un projet créé ici est suivi d'office ; un projet récent "
                "peut l'être avec « Suivre ce projet », et ceux d'un dossier se cherchent "
                "dans « Ouvrir un projet »."
            )
        )
        st.button(
            _("Chercher les projets dans un dossier…"),
            key="home-go-search",
            on_click=go_to_tab,
            args=("ouvrir",),
            icon=":material/manage_search:",
        )
        c.show_message("home-unfollow")
        return False
    rows = overview.rows(followed)
    shown = _chosen(rows)
    with st.sidebar:
        _project_list(rows, shown)
    for key in ("home-unfollow", "home-find", "home-folder"):
        c.show_message(key)
    with st.container(border=True):
        _detail(shown)
    return True


def _recent() -> None:
    """The recent projects not followed, latest first: name, folder, last change of the
    project file."""
    followed = {ondisk.key(p) for p in tracked.load()}
    found = [p for p in recents.load() if ondisk.key(p) not in followed]  # v0.17: once
    if not found:
        return
    st.subheader(_("Projets récents"))
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
