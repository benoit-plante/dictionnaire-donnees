"""The phase "Concevoir" (v0.20, D-149): the questionnaire designed in the tool, and what the
pages that show the database say before it arrives (D-145)."""

from __future__ import annotations

import streamlit as st

from ddict import design
from ddict.i18n import _
from ddict.project.model import Project
from ddict.review import navigation
from ddict.review.ui import common as c
from ddict.review.ui.questionnaire_view import KIND_NAMES

EXCERPT = 70  # characters of a question's text on its line


def _excerpt(text: str) -> str:
    return text if len(text) <= EXCERPT else text[: EXCERPT - 1].rstrip() + "…"


def page(project: Project) -> None:
    st.header(_("Questionnaire"))
    st.caption(
        _(
            "Le questionnaire de l'étude, conçu dans l'outil : il est la source du dictionnaire "
            "de données, et chaque question donne ses variables avant la collecte."
        )
    )
    questionnaire = design.questionnaire(project)
    number = 0
    for section in questionnaire.sections:
        st.subheader(section.title or _("Section sans titre"))
        if section.instruction:
            st.write(section.instruction)
        questions = [q for q in questionnaire.questions if q.section == section.section_id]
        if not questions:
            st.caption(_("Aucune question dans cette section."))
        for question in questions:
            number += 1
            names = [e.name for e in project.variables if _of(e) == question.question_id]
            line = f"{number}. {_excerpt(question.text)} — {KIND_NAMES.get(question.kind)}"
            if names:
                line += " — " + ", ".join(f"`{n}`" for n in names[:3])
                if len(names) > 3:
                    line += " " + _("et {n} autres").format(n=len(names) - 3)
            st.markdown(line)


def _of(entry) -> str | None:
    return (entry.question.value or "").partition(".")[0] or None


def waiting_for_base(project: Project, mode: str) -> None:
    """A page that shows the database, before it arrives: it says so, and leads to the step
    that comes first (v0.20, D-145)."""
    st.header(_(navigation.PAGES[mode].title))
    st.info(
        _(
            "En attente de la base : cette page s'ouvrira quand les réponses de la collecte "
            "seront arrivées. D'ici là, le questionnaire est la source du dictionnaire."
        )
    )
    if project.design is not None:
        c.go_button(_("Aller au questionnaire"), key=f"waiting-{mode}", mode="design")
