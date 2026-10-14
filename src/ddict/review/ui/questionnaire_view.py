"""The study's questionnaire: read it, see what was found, replace it (v0.3).

The same as `ddict questionnaire`: no model involved; the acronyms it defines become
proposals for the glossary.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from ddict.i18n import N_, Texts, _
from ddict.io import ReadError
from ddict.project import save_project
from ddict.project.model import Project
from ddict.review.ui import common as c
from ddict.review.ui import dialog
from ddict.workflow import (
    KINDS,
    TO_CHECK,
    QuestionnaireExists,
    acronym_summary,
    add_questionnaire,
    questionnaire_summary,
)

FIELD = "questionnaire-path"
KIND_NAMES = Texts(
    {
        "open": N_("ouverte"),
        "single": N_("choix unique"),
        "checkbox": N_("à cocher"),
        "grid": N_("grille"),
    }
)


def _message(kind: str, text: str, key: str) -> None:
    st.session_state.message = (kind, text, key)


def _browse() -> None:
    path = dialog.choose("questionnaire")
    if path:
        st.session_state[FIELD] = path
    else:
        _message(
            "error",
            _("Aucun fichier choisi. Vous pouvez aussi coller son chemin dans le champ."),
            "questionnaire-browse",
        )


def _read(replace: bool) -> None:
    key = "questionnaire-read"
    text = str(st.session_state.get(FIELD) or "").strip().strip('"')
    path = Path(text) if text else None
    if path is None or not path.is_file():
        _message("error", _("Choisissez d'abord le fichier du questionnaire (.pdf ou .txt)."), key)
        return
    project = c.project()
    try:
        removed = add_questionnaire(project, path, replace=replace)
    except QuestionnaireExists:
        _message("error", _("Le projet a déjà un questionnaire."), key)
        return
    except ReadError as error:
        _message(
            "error", _("Impossible de lire le questionnaire : {detail}").format(detail=error), key
        )
        return
    save_project(project, c.project_path())
    st.session_state[FIELD] = ""
    text = _("Questionnaire lu.")
    if removed:
        text += " " + _(
            "{n} rattachements retirés : ils renvoyaient à l'ancien questionnaire."
        ).format(n=removed)
    _message("success", text, key)


def _chooser(replace: bool) -> None:
    st.button(_("Choisir le questionnaire…"), key="questionnaire-browse", on_click=_browse)
    c.show_message("questionnaire-browse")
    st.text_input(_("ou collez le chemin du fichier"), key=FIELD)
    st.button(
        _("Remplacer le questionnaire") if replace else _("Lire le questionnaire"),
        key="questionnaire-read",
        on_click=_read,
        args=(replace,),
        type="secondary" if replace else "primary",
    )


def page(project: Project) -> None:
    st.header(_("Questionnaire de l'étude"))
    questionnaire = project.questionnaire
    if questionnaire is None:
        st.write(
            _(
                "Le questionnaire dit ce que chaque variable veut dire : le texte exact des "
                "questions, le sens des sigles, les options de réponse. Il est lu sur cet "
                "ordinateur, sans IA : PDF (SurveyMonkey, LimeSurvey, REDCap…) ou texte (.txt "
                "copié depuis Word). Seules les questions rattachées à des variables iront "
                "dans le codebook, jamais la page de consentement."
            )
        )
        _chooser(replace=False)
        c.show_message("questionnaire-read")
        return

    c.show_message("questionnaire-read")
    summary = questionnaire_summary(questionnaire)
    st.write(summary[0])
    st.write(summary[1])
    for line in summary[2:]:
        st.warning(line)
    for line in acronym_summary(project):
        st.info(line)
    if any(q.to_check for q in questionnaire.questions):
        st.caption(
            _(
                "Une question « à vérifier » a été lue, mais sa mise en page est douteuse : "
                "l'outil ne propose pas d'étiquettes de valeurs à partir de ses colonnes. Un "
                ".txt copié depuis Word évite souvent le problème."
            )
        )

    with st.expander(_("Questions trouvées")):
        rows = [
            (
                q.question_id,
                q.page or "",
                KIND_NAMES.get(q.kind, q.kind),
                q.text,
                len(q.rows) if q.kind == "grid" else len(q.options),
                ", ".join(TO_CHECK.get(code, code) for code in q.to_check),
            )
            for q in questionnaire.questions
        ]
        st.dataframe(
            pd.DataFrame(
                rows,
                columns=[
                    _("Question"),
                    _("Page"),
                    _("Type"),
                    _("Texte"),
                    _("Options ou énoncés"),
                    _("À vérifier"),
                ],
            ),
            hide_index=True,
        )
        st.caption(
            ", ".join(
                f"{sum(1 for q in questionnaire.questions if q.kind == kind)} {label}"
                for kind, label in KINDS.items()
            )
        )

    with st.expander(_("Remplacer le questionnaire")):
        st.caption(
            _(
                "Pour une nouvelle version du fichier. Les rattachements qui renvoyaient à "
                "l'ancienne version sont retirés ; les sigles déjà décidés sont gardés."
            )
        )
        _chooser(replace=True)
