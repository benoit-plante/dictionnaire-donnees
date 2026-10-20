"""The page "Publier" of the phase "Concevoir" (v0.20, steps E1, E2): the questionnaire about
as a person answering will see it, its Word in two versions (D-152), its file for LimeSurvey
and the steps of its import (D-148); the versions marked as sent and the comparison of a
re-export (E3).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from ddict import design, design_compare, design_limesurvey, design_word, i18n
from ddict.i18n import N_, Texts, _
from ddict.io.model import ReadError
from ddict.project.model import Project, Question
from ddict.questionnaire.lss import read_limesurvey
from ddict.review.ui import common as c
from ddict.review.ui import design_view, dialog

NAMES = "publish-names"  # "Montrer les noms"
# Short enough for a column of the window at its smallest (900 pixels).
BUTTONS = Texts({"ethics": N_("Word pour le comité"), "working": N_("Word de travail")})


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
        column.download_button(
            _(BUTTONS[which]),
            design_word.render(project, which),
            file_name=design_word.file_name(project, which),
            mime=design_word.MIME,
            key=f"publish-word-{which}",
            icon=":material/description:",
            on_click="ignore",
        )
        column.caption(texts[which])


def _limesurvey(project: Project) -> None:
    st.subheader(_("Le fichier pour LimeSurvey"))
    st.caption(
        _(
            "La structure en texte à colonnes de LimeSurvey (.txt), vérifiée sur LimeSurvey "
            "Cloud 7.6 ; une autre version n'est pas garantie. Ni branchement, ni ordre "
            "aléatoire, ni quota : ils se règlent dans LimeSurvey."
        )
    )
    found = design_limesurvey.summary(project)
    if found.problems:
        st.error(_("LimeSurvey refuserait ce questionnaire, ou l'importerait autrement :"))
        for problem in found.problems:
            st.markdown(f"- {problem}")
        c.go_button(_("Aller à la relecture"), key="publish-limesurvey-review",
                    mode="design_review")  # fmt: skip
        return
    kinds = ", ".join(
        f"{_(design_limesurvey.TYPE_NAMES[k])} `{k}` ({n})" for k, n in found.kinds.items()
    )
    st.markdown(
        _("Le fichier contient {groups} groupes et {questions} questions : {kinds}.").format(
            groups=found.groups, questions=found.questions, kinds=kinds
        )
    )
    st.markdown(_("Restent dans l'outil, que LimeSurvey n'aura pas :"))
    for line in found.left:
        st.markdown(f"- {line}")
    st.download_button(
        _("Fichier LimeSurvey (.txt)"),
        design_limesurvey.text(project).encode("utf-8"),
        file_name=design_limesurvey.file_name(project),
        mime=design_limesurvey.MIME,
        key="publish-limesurvey",
        icon=":material/upload_file:",
        on_click="ignore",
    )
    with st.expander(_("Importer dans LimeSurvey, pas à pas")):
        for number, step in enumerate(design_limesurvey.import_steps(project), start=1):
            st.markdown(f"{number}. {step}")


# --- Marking as sent, and the loop (E3, D-150). ---

SENT_KIND, SENT_DAY, SENT_NOTE = "publish-sent-kind", "publish-sent-day", "publish-sent-note"
REEXPORT = "publish-reexport"  # the path of a structure re-exported from LimeSurvey
KEPT = "publish-kept"  # the differences kept as the project says, LimeSurvey to correct
MESSAGE = "publish"
COMPARED = "publish-compare"  # the messages of the comparison
ITEM_KINDS = Texts(
    {
        "added": N_("ajouté"),
        "removed": N_("retiré"),
        "recoded": N_("recodé"),
        "reworded": N_("reformulé"),
    }
)
ITEM_WHAT = Texts({"row": N_("Énoncé"), "option": N_("Choix")})


def _mark(project: Project) -> None:
    day = st.session_state.get(SENT_DAY) or date.today()
    design_compare.mark_sent(
        project, st.session_state.get(SENT_KIND) or "limesurvey", day.isoformat(),
        st.session_state.get(SENT_NOTE),
    )  # fmt: skip


def _marked() -> None:
    st.session_state[SENT_NOTE] = ""


def _sent(project: Project) -> None:
    st.subheader(_("Versions envoyées"))
    st.caption(
        _(
            "Marquez le questionnaire comme envoyé au comité d'éthique ou publié dans "
            "LimeSurvey : le projet en garde une copie et son empreinte. Le modifier ensuite "
            "reste permis ; la page dit alors ce qui a changé depuis."
        )
    )
    with st.container(horizontal=True):
        st.selectbox(_("Envoyé où"), list(design_compare.SENT), key=SENT_KIND,
                     placeholder=_("Choisir…"),
                     format_func=lambda k: _(design_compare.SENT[k]))  # fmt: skip
        st.date_input(_("Le"), value=date.today(), key=SENT_DAY, format="YYYY-MM-DD")
    st.text_input(_("Note (facultative)"), key=SENT_NOTE)
    st.button(
        _("Marquer comme envoyé"),
        key="publish-mark",
        icon=":material/send:",
        on_click=design_view.act,
        args=(lambda p: _mark(p),),
        kwargs={"key": MESSAGE, "done": _("Version marquée comme envoyée.")},
    )
    c.show_message(MESSAGE)
    found = project.design.publications
    if not found:
        st.caption(_("Aucune version envoyée."))
    for n, publication in enumerate(reversed(found)):
        changes = design_compare.since(publication, project)
        title = _("{sent} le {date} — empreinte {fingerprint}").format(
            sent=_(design_compare.SENT[publication.kind]),
            date=publication.date,
            fingerprint=publication.fingerprint[:12],
        )
        if publication.note:
            title += f" — {publication.note}"
        with st.expander(title, expanded=n == 0 and bool(changes)):
            if not changes:
                st.write(_("Rien n'a changé depuis cette version."))
            for difference in changes:
                _difference_text(difference)


def _difference_text(difference: design_compare.Difference) -> None:
    """A difference in words, the text changed word by word."""
    question = difference.theirs if difference.mine is None else difference.mine
    head = f"**{difference.title}** — `{difference.code}` : {question.text}"
    if difference.kind == "renamed":
        head = f"**{difference.title}** — `{difference.code}` → `{difference.theirs.code}` : "
        head += question.text
    st.markdown(head)
    if difference.kind != "changed":
        return
    fields = ", ".join(_(design_compare.FIELDS[f]) for f in difference.fields)
    if fields:
        st.markdown(_("Changé : {fields}.").format(fields=fields))
    if "text" in difference.fields:
        words = []
        for tag, text in difference.words():
            words.append({"=": text, "-": f"~~{text}~~", "+": f"**{text}**"}[tag])
        st.markdown(" ".join(words))
    for item in difference.items:
        line = f"{_(ITEM_WHAT[item.what])} {_(ITEM_KINDS[item.kind])} : "
        if item.kind == "recoded":
            line += f"`{item.before}` → `{item.code}` « {item.text} »"
        elif item.kind == "reworded":
            line += f"`{item.code}` « {item.before} » → « {item.text} »"
        else:
            line += f"`{item.code}` « {item.text} »"
        st.markdown(f"- {line}")


def _browse() -> None:
    path = dialog.choose("limesurvey")
    if path:
        st.session_state[REEXPORT] = path


def _take(project: Project, difference) -> None:
    design_compare.take(project, difference, now=c.now())


def _keep(key: str) -> None:
    st.session_state[KEPT] = [*st.session_state.get(KEPT, []), key]


def _review(key: str) -> None:
    """Back on a "Garder le projet": the difference is open again, to take or keep (the
    author's trial, 2026-10-20: it came back only once the tool was closed)."""
    st.session_state[KEPT] = [k for k in st.session_state.get(KEPT, []) if k != key]


def _compare(project: Project) -> None:
    st.subheader(_("Comparer le réexport de LimeSurvey"))
    st.caption(
        _(
            "Après l'importation, réexportez la structure du questionnaire depuis LimeSurvey "
            "(.lss ou .txt) : l'outil la compare au questionnaire du projet, par les codes des "
            "questions. Rien ne change sans votre décision."
        )
    )
    with st.container(horizontal=True, vertical_alignment="bottom"):
        st.text_input(_("Structure réexportée (.lss ou .txt)"), key=REEXPORT)
        st.button(_("Choisir…"), key="publish-reexport-browse", on_click=_browse)
    c.show_message(COMPARED)
    text = str(st.session_state.get(REEXPORT) or "").strip().strip('"')
    if not text:
        return
    path = Path(text)
    try:
        read = read_limesurvey(path, project.settings.language)
    except ReadError as error:
        st.error(_("Impossible de lire la structure : {detail}").format(detail=error))
        return
    differences = design_compare.with_limesurvey(project, read)
    kept = set(st.session_state.get(KEPT, []))
    open_ones = [d for d in differences if f"{d.kind}-{d.code}" not in kept]
    if not differences:
        st.success(_("LimeSurvey dit la même chose que le projet."))
        return
    for difference in open_ones:
        key = f"{difference.kind}-{difference.code}"
        with st.container(border=True):
            _difference_text(difference)
            with st.container(horizontal=True):
                st.button(
                    _("Reprendre dans le projet"),
                    key=f"publish-take-{key}",
                    on_click=design_view.act,
                    args=(_take, difference),
                    kwargs={"key": COMPARED, "done": _("Repris dans le projet.")},
                )
                st.button(_("Garder le projet"), key=f"publish-keep-{key}", on_click=_keep,
                          args=(key,))  # fmt: skip
    kept_ones = [d for d in differences if f"{d.kind}-{d.code}" in kept]
    if kept_ones:
        st.warning(
            _("LimeSurvey est à corriger pour : {codes}.").format(
                codes=", ".join(f"`{d.code}`" for d in kept_ones)
            )
        )
        with st.container(horizontal=True):
            for difference in kept_ones:
                key = f"{difference.kind}-{difference.code}"
                st.button(_("Revoir {code}").format(code=difference.code),
                          key=f"publish-review-{key}", on_click=_review, args=(key,))  # fmt: skip


def page(project: Project) -> None:
    st.header(_("Publier"))
    st.caption(
        _(
            "Le questionnaire pour le comité d'éthique, pour l'équipe et pour LimeSurvey, "
            "produit par le calcul depuis le questionnaire de l'outil, jamais par l'IA."
        )
    )
    for line in design_compare.warnings(project):
        st.warning(line)
    _word(project)
    st.divider()
    _limesurvey(project)
    st.divider()
    _sent(project)
    st.divider()
    _compare(project)
    st.divider()
    _preview(project)
