"""Grouped decisions, always shown first (v0.4, D-029).

A button opens the exact list of the variables concerned, each with what would be
accepted and a box to uncheck it; a second button accepts the checked ones, one decision
each, with its date. Nothing is accepted without having been shown.
"""

from __future__ import annotations

import streamlit as st

from ddict.export import wording as w
from ddict.i18n import _, colon, semicolon
from ddict.project.model import Project
from ddict.questionnaire import link
from ddict.review import logic
from ddict.review.ui import common as c

OPEN = "bulk-open"  # "links", or "labels-G3": the list being shown


def _box(kind: str, name: str) -> str:
    return f"bulk-{kind}-{name}"


def _open(which: str, kind: str, names: list[str]) -> None:
    st.session_state[OPEN] = which
    for name in names:
        st.session_state[_box(kind, name)] = True  # everything checked at first


def _close() -> None:
    st.session_state[OPEN] = None


def _accept(action, args: tuple, kind: str, names: list[str], key: str, text: str) -> None:
    checked = [n for n in names if st.session_state.get(_box(kind, n))]
    c.act(action, *args, checked, key=key, timed=True, reset=())
    message = st.session_state.get("message")
    if message and message[0] == "success":
        st.session_state.message = ("success", text.format(n=len(checked)), key)
        _close()


def _checked_count(kind: str, names: list[str]) -> int:
    return sum(1 for n in names if st.session_state.get(_box(kind, n)))


def links_panel(project: Project) -> None:
    """On the Variables page: the links where the model and the computation agree."""
    names = logic.agreeing_links(project)
    key = "bulk-links-accept"
    if st.session_state.get(OPEN) != "links":
        if names:
            st.button(
                _("Accepter les rattachements où le modèle et le calcul s'accordent ({n})…").format(
                    n=len(names)
                ),
                key="bulk-links-open",
                on_click=_open,
                args=("links", "link", names),
            )
        c.show_message(key)
        return
    with st.container(border=True):
        st.markdown(f"**{_('Rattachements où le modèle et le calcul s’accordent')}**")
        st.caption(
            _(
                "Lisez chaque ligne : à l'essai sur une vraie base, environ un rattachement sur "
                "cinq de cette liste était faux, surtout pour les scores calculés, les options "
                "de listes à cocher voisines et les variables sans question (identifiant, date "
                "de passation). Décochez ceux qui ne conviennent pas ; chaque rattachement coché "
                "sera accepté comme si vous l'aviez accepté à la main."
            )
        )
        for name in names:
            target = project.variable(name).question.value
            text = link.describe(project.questionnaire, target) or target
            st.checkbox(f"**{name}** → {target}{colon()}{text}", key=_box("link", name))
        count = _checked_count("link", names)
        left, right = st.columns(2)
        left.button(
            _("Accepter ces {n} rattachements").format(n=count),
            key=key,
            type="primary",
            disabled=count == 0,
            on_click=_accept,
            args=(
                logic.accept_links,
                (),
                "link",
                names,
                key,
                _("{n} rattachements acceptés."),
            ),
        )
        right.button(_("Annuler"), key="bulk-links-cancel", on_click=_close)
    st.divider()


def labels_panel(project: Project, group_id: str) -> None:
    """On a group's page: the value labels proposed for its members."""
    names = logic.group_label_proposals(project, group_id)
    which = f"labels-{group_id}"
    key = f"bulk-labels-accept-{group_id}"
    if st.session_state.get(OPEN) != which:
        if names:
            st.button(
                _("Accepter les étiquettes de valeurs de ce groupe ({n})…").format(n=len(names)),
                key=f"bulk-labels-open-{group_id}",
                on_click=_open,
                args=(which, "labels", names),
            )
        c.show_message(key)
        return
    with st.container(border=True):
        st.markdown(f"**{_('Étiquettes de valeurs proposées pour ce groupe')}**")
        st.caption(
            _(
                "Tirées des options de la question de chaque variable, dans l'ordre supposé "
                "des codes. Décochez celles qui ne conviennent pas."
            )
        )
        for name in names:
            labels = project.variable(name).value_labels.value or []
            text = semicolon().join(f"{w.code_text(v.code)} = {v.label}" for v in labels)
            st.checkbox(f"**{name}**{colon()}{text}", key=_box("labels", name))
        count = _checked_count("labels", names)
        left, right = st.columns(2)
        left.button(
            _("Accepter ces {n} étiquetages").format(n=count),
            key=key,
            type="primary",
            disabled=count == 0,
            on_click=_accept,
            args=(
                logic.accept_group_labels,
                (group_id,),
                "labels",
                names,
                key,
                _("Étiquettes de {n} variables acceptées."),
            ),
        )
        right.button(_("Annuler"), key=f"bulk-labels-cancel-{group_id}", on_click=_close)
    st.divider()


def glossary_panel(project: Project, shown: dict[str, str]) -> None:
    """On the Glossary page (v0.16): the acronyms of the questionnaire that wait, each with
    the meaning shown in its field, corrected or not (D-121)."""
    terms = logic.glossary_proposals(project)
    key = "bulk-glossary-accept"
    if st.session_state.get(OPEN) != "glossary":
        if terms:
            st.button(
                _("Tout accepter ({n})…").format(n=len(terms)),
                key="bulk-glossary-open",
                on_click=_open,
                args=("glossary", "glossary", terms),
            )
        c.show_message(key)
        return
    with st.container(border=True):
        st.markdown(f"**{_('Sigles à valider')}**")
        st.write(
            _(
                "Chaque sigle sera accepté avec la définition affichée ici, celle de son champ, "
                "corrigée ou non. Décochez ceux qui ne conviennent pas."
            )
        )
        for term in terms:
            st.checkbox(f"**{term}**{colon()}{shown[term]}", key=_box("glossary", term))
        count = _checked_count("glossary", terms)
        left, right = st.columns(2)
        left.button(
            _("Accepter ces {n} sigles").format(n=count),
            key=key,
            type="primary",
            disabled=count == 0,
            on_click=_accept,
            args=(
                logic.accept_glossary,
                ({t: shown[t] for t in terms},),
                "glossary",
                terms,
                key,
                _("{n} sigles acceptés."),
            ),
        )
        right.button(_("Annuler"), key="bulk-glossary-cancel", on_click=_close)
    st.divider()
