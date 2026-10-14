"""Export: the Excel codebook and the Markdown report, as `ddict exporter` writes them.

They are written next to the project, or downloaded from the page. A final export holds
only what comes from the file, from computation, or was accepted by a person.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys

import streamlit as st

from ddict.export import render_markdown, write_xlsx
from ddict.export.syntax import render_syntax
from ddict.i18n import _
from ddict.project.model import Project
from ddict.review import logic
from ddict.review.ui import common as c
from ddict.workflow import export_codebook, export_paths, export_syntax, syntax_paths

KIND = "export-kind"
OMIT = "export-omit"
KINDS = {
    "final": _("Finale : seulement ce qui vient du fichier, du calcul ou de vos décisions"),
    "work": _("De travail : avec les propositions en attente, marquées comme telles"),
}
PROGRAMS = {"spss": _("Syntaxe SPSS"), "r": _("Script R"), "stata": _("Fichier Stata")}
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _write() -> None:
    path = c.project_path()
    try:
        xlsx, markdown = export_codebook(
            c.project(),
            path,
            kind=st.session_state[KIND],
            omit_groups=tuple(st.session_state[OMIT]),
        )
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
    st.session_state.message = (
        "success",
        _("Fichiers écrits à côté du projet : {xlsx} et {md}.").format(
            xlsx=xlsx.name, md=markdown.name
        ),
        "export-write",
    )


def _write_syntax() -> None:
    try:
        paths = export_syntax(c.project(), c.project_path())
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


def _open_folder() -> None:
    """Show the project's folder in the file manager of this computer."""
    folder = str(c.project_path().resolve().parent)
    if sys.platform == "win32":
        os.startfile(folder)
    else:
        subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", folder], check=False)


def page(project: Project) -> None:
    st.header(_("Export"))
    st.radio(
        _("Version"),
        list(KINDS),
        key=c.field(KIND, lambda: "final"),
        format_func=KINDS.__getitem__,
    )
    kind = st.session_state[KIND]
    if project.groups and project.questionnaire is not None:
        st.multiselect(
            _("Groupes dont le texte des questions n'est pas reproduit"),
            [g.group_id for g in project.groups],
            placeholder=_("Aucun : tout le texte est reproduit"),
            key=c.field(
                OMIT,
                lambda: [g.group_id for g in c.project().groups if g.omit_question_text],
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
    write_xlsx(project, workbook, kind=kind, omit_groups=omit)
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
        data=render_markdown(project, kind=kind, omit_groups=omit).encode("utf-8"),
        file_name=markdown_path.name,
        mime="text/markdown",
        key="export-download-md",
    )

    st.subheader(_("Fichiers de commandes"))
    st.caption(
        _(
            "Pour appliquer vos décisions à vos données dans SPSS, R ou Stata : libellés, "
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
    for column, (program, title) in zip(st.columns(3), PROGRAMS.items(), strict=True):
        column.download_button(
            title,
            data=render_syntax(project, program).encode("utf-8"),
            file_name=paths[program].name,
            mime="text/plain",
            key=f"export-download-{program}",
        )
