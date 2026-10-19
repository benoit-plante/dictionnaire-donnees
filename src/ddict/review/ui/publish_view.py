"""The page "Publier" of the phase "Concevoir" (v0.20, step E1): the questionnaire about as a
person answering will see it, and its Word in two versions (D-152). The LimeSurvey file, the
versions marked as sent and the comparison of a re-export follow (E2, E3).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ddict import design, design_word, i18n
from ddict.i18n import _
from ddict.project.model import Project, Question

NAMES = "publish-names"  # "Montrer les noms"


def _label(project: Project, item: design_word.Numbered, names: bool) -> str:
    question = item.question
    text = f"**{item.number}.** {question.text}" + (" \\*" if question.required else "")
    if names:
        text += f" `{design.code(project, question)}`"
    return text


def _option(code: str | None, text: str, names: bool) -> str:
    return f"[{code}] {text}" if names and code else text


def _answer(project: Project, item: design_word.Numbered, names: bool) -> None:
    """A question as the Word shows it: its text, its instruction, then where to answer, the
    fields disabled (their label kept, hidden, for a screen reader)."""
    question: Question = item.question
    key = f"publish-{question.question_id}"
    if question.kind == "display":
        st.markdown(f"*{question.text}*")
        return
    label = _label(project, item, names)
    st.markdown(label)
    if question.instruction:
        st.caption(question.instruction)
    hidden = {"key": key, "disabled": True, "label_visibility": "collapsed"}
    if question.kind == "single":
        options = [_option(o.code, o.text, names) for o in question.options]
        if question.layout == "dropdown":
            st.selectbox(label, options, index=None, placeholder=_("Choisir…"), **hidden)
        else:
            st.radio(label, options, index=None, **hidden)
    elif question.kind == "checkbox":
        for n, option in enumerate(question.options):
            text = _option(option.code, option.text, names)
            st.checkbox(text + (" : …" if option.other else ""), key=f"{key}-{n}", disabled=True)
    elif question.kind == "grid":
        columns = [_option(o.code, o.text, names) for o in question.options]
        rows = [_option(r.code, r.text, names) for r in question.rows]
        st.table(pd.DataFrame([[design_word.ROUND] * len(columns)] * len(rows),
                              index=rows, columns=columns))  # fmt: skip
    elif question.answer == "long":
        st.text_area(label, **hidden)
    elif question.answer == "number":
        st.number_input(label, value=None, **hidden)
    elif question.answer == "date":
        st.date_input(label, value=None, **hidden)
    else:
        st.text_input(label, **hidden)


def _preview(project: Project) -> None:
    st.subheader(_("Aperçu"))
    st.caption(
        _(
            "Le questionnaire à peu près comme le verra une personne qui répond, les champs "
            "désactivés : une approximation. Seul LimeSurvey fait foi."
        )
    )
    names = st.toggle(_("Montrer les noms"), key=NAMES)
    found = design.questionnaire(project)
    if any(q.required for q in found.questions):
        with i18n.using(project.settings.language):  # as the Word says it
            st.caption(_("* Réponse obligatoire.").replace("*", r"\*", 1))
    with st.container(border=True):
        st.markdown(f"### {found.file_name}")
        for section, questions in design_word.numbered(project):
            if section.title:
                st.markdown(f"#### {section.title}")
            if section.instruction:
                st.markdown(f"*{section.instruction}*")
            for item in questions:
                _answer(project, item, names)
                if names and item.question.kind == "display":
                    st.caption(f"`{design.code(project, item.question)}`")


def _word(project: Project) -> None:
    st.subheader(_("Le questionnaire en Word"))
    st.caption(design_word.footer_text(project))
    left, right = st.columns(2)
    texts = {
        "ethics": _("Sans nom, sans code, sans provenance : ce que lira une personne qui répond."),
        "working": _(
            "Avec les codes, la nature et le type LimeSurvey de chaque question, la provenance, "
            "les groupes et les points de relecture."
        ),
    }
    for column, which in zip((left, right), design_word.VERSIONS, strict=True):
        name = _(design_word.VERSION_NAMES[which])
        column.download_button(
            _("Word {version}").format(version=name),
            design_word.render(project, which),
            file_name=design_word.file_name(project, which),
            mime=design_word.MIME,
            key=f"publish-word-{which}",
            icon=":material/description:",
            on_click="ignore",
        )
        column.caption(texts[which])


def page(project: Project) -> None:
    st.header(_("Publier"))
    st.caption(
        _(
            "Le questionnaire pour le comité d'éthique et pour l'équipe, produit par le calcul "
            "depuis le questionnaire de l'outil, jamais par l'IA."
        )
    )
    _word(project)
    st.divider()
    _preview(project)
