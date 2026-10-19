"""Export: the Excel codebook and the Markdown report, as `ddict exporter` writes them.

They are written next to the project, or downloaded from the page. A final export holds
only what comes from the file, from computation, or was accepted by a person.
"""

from __future__ import annotations

import io
import os
from pathlib import Path

import streamlit as st

from ddict import i18n
from ddict.export import render_markdown, write_xlsx
from ddict.export.context import context_package, package_text, render_context
from ddict.export.documented import CopyError, default_copy_path, find_database
from ddict.export.preparation import needed as preparation_needed
from ddict.export.preparation import render_preparation
from ddict.export.syntax import render_syntax
from ddict.i18n import N_, Texts, _
from ddict.project.model import Project
from ddict.review import logic
from ddict.review.ui import common as c
from ddict.review.ui import dialog, names_view
from ddict.workflow import (
    context_paths,
    copy_error_text,
    documented_copy,
    export_codebook,
    export_context,
    export_name_table,
    export_paths,
    export_syntax,
    preparation_paths,
    syntax_paths,
)

KIND = "export-kind"
LANGUAGE = "export-language"
DATABASE = "copy-database"  # the database chosen by hand, when not next to the project
REPLACE = "copy-replace"
CONFLICTS = "copy-conflicts"  # the copy was refused for a conflict of names (v0.16)
OMIT = "export-omit"
STATISTICS = "context-statistics"
KINDS = Texts(
    {
        "final": N_("Finale : seulement ce qui vient du fichier, du calcul ou de vos décisions"),
        "work": N_("De travail : avec les propositions en attente, marquées comme telles"),
    }
)
PROGRAMS = Texts({"spss": N_("Syntaxe SPSS"), "r": N_("Script R")})
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _language() -> str:
    """The language chosen for the codebook; None when the chosen one was clicked again,
    which means the interface's."""
    return st.session_state.get(LANGUAGE) or i18n.language()


def _write() -> None:
    path = c.project_path()
    try:
        xlsx, markdown = export_codebook(
            c.project(),
            path,
            kind=st.session_state[KIND],
            omit_groups=tuple(st.session_state[OMIT]),
            language=_language(),
        )
        table = export_name_table(c.project(), path)  # v0.7: the reference of the next wave
    except OSError as error:
        st.session_state.message = (
            "error",
            _(
                "Impossible d'écrire les fichiers : {detail}. Le codebook est peut-être ouvert "
                "dans Excel : fermez-le, puis recommencez."
            ).format(detail=error),
            "export-write",
        )
        return
    text = _("Fichiers écrits à côté du projet : {xlsx} et {md}.").format(
        xlsx=xlsx.name, md=markdown.name
    )
    if table is not None:
        text += " " + _("Table de correspondance des noms : {path}").format(path=table.name)
    st.session_state.message = ("success", text, "export-write")


def _write_syntax() -> None:
    try:
        paths = export_syntax(c.project(), c.project_path(), language=_language())
    except OSError as error:
        st.session_state.message = (
            "error",
            _("Impossible d'écrire les fichiers : {detail}.").format(detail=error),
            "export-syntax-write",
        )
        return
    st.session_state.message = (
        "success",
        _("Fichiers écrits à côté du projet : {names}.").format(
            names=", ".join(p.name for p in paths.values())
        ),
        "export-syntax-write",
    )


def _choose_database() -> None:
    path = dialog.choose("database")
    if path:
        st.session_state[DATABASE] = path


def _write_copy() -> None:
    project = c.project()
    chosen = st.session_state.get(DATABASE)
    try:
        result = documented_copy(
            project,
            c.project_path(),
            database=Path(chosen) if chosen else None,
            replace=bool(st.session_state.get(REPLACE)),
        )
    except CopyError as error:
        st.session_state.message = (
            "error",
            copy_error_text(error, project),
            "export-copy-write",
        )
        st.session_state[CONFLICTS] = error.reason == "name_conflict"
        return
    st.session_state[REPLACE] = False
    text = _(
        "Copie écrite à côté de la base : {name}. Relue et comparée à l'original : "
        "{rows} lignes et {columns} variables, identiques case par case."
    ).format(name=result.path.name, rows=result.n_rows, columns=result.n_columns)
    if result.missing_not_written:
        text += " " + _(
            "Codes confirmés par l'équipe non écrits, SPSS n'acceptant que 3 codes "
            "manquants : {names}. Ceux du fichier sont gardés."
        ).format(names=", ".join(result.missing_not_written))
    st.session_state.message = ("success", text, "export-copy-write")


def _copy_section(project: Project) -> None:
    st.subheader(_("Copie documentée de la base"))
    st.write(
        _(
            "Une nouvelle copie de votre base au format SPSS (.sav), avec ce que vous avez "
            "accepté. Avant de l'annoncer, l'outil la relit et la compare à l'original case par "
            "case. Votre fichier d'origine n'est jamais modifié. La copie contient les données "
            "des participants : rangez-la comme l'original. Les fichiers de commandes restent "
            "la voie recommandée."
        )
    )
    chosen = st.session_state.get(DATABASE)
    try:
        database = find_database(project, c.project_path(), Path(chosen) if chosen else None)
    except CopyError as error:
        st.info(copy_error_text(error, project))
        st.button(_("Choisir la base…"), key="export-copy-choose", on_click=_choose_database)
        return
    target = default_copy_path(database)
    st.caption(_("Copie : {path}").format(path=target))
    if target.exists():
        st.checkbox(_("{name} existe déjà : la remplacer").format(name=target.name), key=REPLACE)
    st.button(
        _("Écrire la copie documentée"),
        key="export-copy-write",
        on_click=_write_copy,
        disabled=target.exists() and not st.session_state.get(REPLACE),
    )
    c.show_message("export-copy-write")
    if st.session_state.pop(CONFLICTS, False):
        c.go_button(_("Régler les conflits de noms"), "go-names-conflicts", "names",
                    **{names_view.FILTER: "conflicts"})  # fmt: skip


def _open_folder() -> None:
    """Show the project's folder in the file manager of this computer."""
    folder = str(c.project_path().resolve().parent)
    os.startfile(folder)  # Windows only (D-081)


def _write_context(omit: tuple[str, ...], language: str) -> None:
    key = "context-write"
    try:
        paths = export_context(
            c.project(),
            c.project_path(),
            statistics=bool(st.session_state.get(STATISTICS)),
            omit_groups=omit,
            language=language,
        )
    except OSError as error:
        st.session_state.message = (
            "error",
            _("Impossible d'écrire les fichiers : {detail}.").format(detail=error),
            key,
        )
        return
    text = _("Fichiers écrits à côté du projet : {md} et {json}.").format(
        md=paths[0].name, json=paths[1].name
    )
    st.session_state.message = ("success", text, key)


def _context_section(project: Project, omit: tuple[str, ...], language: str) -> None:
    """The analysis context (v0.8, D-058): the codebook compact, for a program or a model."""
    st.subheader(_("Contexte d'analyse"))
    st.caption(
        _(
            "Le codebook en format compact, pour un programme ou pour une IA qui aide à écrire "
            "le code d'analyse : un fichier Markdown à coller dans un modèle, et un "
            "datapackage.json (format Frictionless). Seulement ce qui est accepté. Ce qui peut "
            "sortir de votre ordinateur relève de votre équipe et du certificat d'éthique de "
            "l'étude, pas de l'outil."
        )
    )
    st.checkbox(
        _("Ajouter les statistiques (effectifs de moins de {n} masqués)").format(
            n=project.settings.min_cell_count
        ),
        key=STATISTICS,
        help=_("Sans elles, le contexte ne contient que des métadonnées, aucune donnée."),
    )
    statistics = bool(st.session_state.get(STATISTICS))
    markdown_path, package_path = context_paths(c.project_path())
    left, right, third = st.columns(3)
    left.button(
        _("Écrire le contexte à côté du projet"),
        key="context-write",
        on_click=_write_context,
        args=(omit, language),
    )
    middle_text = render_context(
        project, statistics=statistics, omit_groups=omit, language=language
    )
    right.download_button(
        _("Contexte (Markdown)"),
        data=middle_text.encode("utf-8"),
        file_name=markdown_path.name,
        mime="text/markdown",
        key="context-download-md",
    )
    third.download_button(
        _("datapackage.json"),
        data=package_text(
            context_package(project, statistics=statistics, language=language)
        ).encode("utf-8"),
        file_name=package_path.name,
        mime="application/json",
        key="context-download-json",
    )
    c.show_message("context-write")


def page(project: Project) -> None:
    st.header(_("Export"))
    st.radio(
        _("Version"),
        list(KINDS),
        key=c.field(KIND, lambda: "final", label=_("Version")),
        format_func=KINDS.__getitem__,
    )
    kind = st.session_state[KIND]
    st.segmented_control(
        _("Langue du codebook"),
        list(i18n.LANGUAGES),
        key=c.field(LANGUAGE, i18n.language, label=_("Langue du codebook")),
        format_func=i18n.LANGUAGES.__getitem__,
        help=_(
            "Pour les en-têtes, les notes et les commentaires des fichiers de commandes. Ce que "
            "l'équipe a écrit (libellés, descriptions, questions) n'est jamais traduit."
        ),
    )
    language = _language()
    if project.groups and project.questionnaire is not None:
        st.multiselect(
            _("Groupes dont le texte des questions n'est pas reproduit"),
            [g.group_id for g in project.groups],
            placeholder=_("Aucun : tout le texte est reproduit"),
            key=c.field(
                OMIT,
                lambda: [g.group_id for g in c.project().groups if g.omit_question_text],
                label=_("Groupes dont le texte des questions n'est pas reproduit"),
            ),
            help=_(
                "Pour un instrument protégé par le droit d'auteur : le codebook donne la "
                "référence de chaque question, sans son texte (D-014)."
            ),
        )
    else:
        st.session_state[OMIT] = []
    omit = tuple(st.session_state[OMIT])

    pending = sum(1 for e in project.variables if logic.pending(e))
    if kind == "final" and pending:
        st.info(
            _(
                "{n} variables ont encore des propositions sans décision : elles ne figurent pas "
                "dans la version finale."
            ).format(n=pending)
        )

    xlsx_path, markdown_path = export_paths(c.project_path(), kind)
    st.subheader(_("Écrire à côté du projet"))
    st.caption(
        _("Dans {folder} : {xlsx} et {md}.").format(
            folder=xlsx_path.parent, xlsx=xlsx_path.name, md=markdown_path.name
        )
    )
    left, right = st.columns(2)
    left.button(
        _("Écrire le codebook et le rapport"), key="export-write", on_click=_write, type="primary"
    )
    right.button(_("Ouvrir le dossier"), key="export-folder", on_click=_open_folder)
    c.show_message("export-write")

    st.subheader(_("Télécharger"))
    st.caption(
        _(
            "Le navigateur les enregistre dans votre dossier de téléchargements. Un codebook "
            "se partage souvent avec les données : il ne contient que des métadonnées et des "
            "effectifs d'au moins {n}."
        ).format(n=project.settings.min_cell_count)
    )
    workbook = io.BytesIO()
    write_xlsx(project, workbook, kind=kind, omit_groups=omit, language=language)
    left, right = st.columns(2)
    left.download_button(
        _("Codebook Excel"),
        data=workbook.getvalue(),
        file_name=xlsx_path.name,
        mime=XLSX_TYPE,
        key="export-download-xlsx",
    )
    right.download_button(
        _("Rapport Markdown"),
        data=render_markdown(project, kind=kind, omit_groups=omit, language=language).encode(
            "utf-8"
        ),
        file_name=markdown_path.name,
        mime="text/markdown",
        key="export-download-md",
    )

    st.subheader(_("Fichiers de commandes"))
    st.caption(
        _(
            "Pour appliquer vos décisions à vos données dans SPSS ou R : libellés, "
            "étiquettes de valeurs, codes manquants et niveaux de mesure. Seulement ce qui est "
            "accepté, quelle que soit la version choisie plus haut. Aucune valeur n'est "
            "modifiée ; appliquez-les à une copie de vos données."
        )
    )
    st.button(
        _("Écrire les fichiers de commandes à côté du projet"),
        key="export-syntax-write",
        on_click=_write_syntax,
    )
    c.show_message("export-syntax-write")
    paths = syntax_paths(c.project_path())
    for column, (program, title) in zip(st.columns(len(PROGRAMS)), PROGRAMS.items(), strict=True):
        column.download_button(
            title,
            data=render_syntax(project, program, language=language).encode("utf-8"),
            file_name=paths[program].name,
            mime="text/plain",
            key=f"export-download-{program}",
        )
    if preparation_needed(project):
        # v0.8 (D-062): new variables, reversed items and scores, from the team's decisions.
        st.caption(
            _(
                "Préparation : crée les items inversés et les scores de vos cotations, dans de "
                "nouvelles variables ; à exécuter après le fichier de commandes."
            )
        )
        prepared = preparation_paths(c.project_path())
        columns = st.columns(len(PROGRAMS))
        for column, (program, title) in zip(columns, PROGRAMS.items(), strict=True):
            column.download_button(
                _("{program} : préparation").format(program=title),
                data=render_preparation(project, program, language=language).encode("utf-8"),
                file_name=prepared[program].name,
                mime="text/plain",
                key=f"export-download-preparation-{program}",
            )

    _context_section(project, omit, language)
    _copy_section(project)
