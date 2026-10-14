"""The groups of items: alphas, reversed items, instrument, copyrighted text."""

from __future__ import annotations

import streamlit as st

from ddict.export import wording as w
from ddict.i18n import _, field_label
from ddict.project.model import Project
from ddict.review import logic
from ddict.review.ui import bulk_view
from ddict.review.ui import common as c


def page(project: Project, group_id: str) -> None:
    group = logic.group(project, group_id)
    st.header(f"{group.group_id} — {w.group_description(group, 'work')}")
    bulk_view.labels_panel(project, group_id)
    members = group.members.value or []
    st.write(f"{field_label('Variables')}" + ", ".join(members))
    st.write(f"{field_label('Indices du regroupement')}{w.basis_text(group.basis)}")
    if group.cronbach_alpha is not None:
        st.write(_("Alpha de Cronbach observé : {a}").format(a=w.number(group.cronbach_alpha)))
    if group.cronbach_alpha_reversed is not None:
        st.write(
            _("Avec les items probables inversés : {a}").format(
                a=w.number(group.cronbach_alpha_reversed)
            )
        )
    suspects = [
        e.name for e in project.variables if e.profile.reverse_suspect and e.name in members
    ]
    if suspects:
        st.warning(_("Items probablement inversés : {s}").format(s=", ".join(suspects)))
    key = f"reverse-{group_id}"
    # A form: a change of the list must not reload the page before the click is seen.
    with st.form(f"form-{key}", border=False):
        st.multiselect(
            _("Items inversés confirmés"),
            members,
            placeholder=_("Aucun item inversé"),
            key=c.field(key, lambda: logic.group(c.project(), group_id).reverse_items or suspects),
        )
        c.button(
            _("Enregistrer les items inversés"),
            f"save-{key}",
            logic.set_reverse_items,
            group_id,
            c.state(key),
            reset=(key,),
            submit=True,
        )
    st.divider()
    st.caption(_("Nom de l'instrument : réservé aux personnes, avec une source documentée."))

    def instrument(part: str) -> str:
        current = logic.group(c.project(), group_id).instrument_name
        return getattr(current, part) if current else ""

    with st.form(f"form-instrument-{group_id}", border=False):
        st.text_input(
            _("Instrument"), key=c.field(f"instrument-{group_id}", lambda: instrument("value"))
        )
        st.text_input(
            _("Source de l'instrument"),
            key=c.field(f"instrument-source-{group_id}", lambda: instrument("source")),
        )
        c.button(
            _("Enregistrer l'instrument"),
            f"save-instrument-{group_id}",
            logic.set_instrument,
            group_id,
            c.state(f"instrument-{group_id}"),
            c.state(f"instrument-source-{group_id}"),
            reset=(f"instrument-{group_id}", f"instrument-source-{group_id}"),
            submit=True,
        )

    if project.questionnaire is not None:
        st.divider()
        key = f"omit-text-{group_id}"
        # A form: ticking the box must not reload the page before the click is seen (a
        # quick click on the button saved the old state, found in the browser).
        with st.form(f"form-{key}", border=False):
            st.checkbox(
                _(
                    "Ne pas reproduire le texte des questions de ce groupe dans le codebook "
                    "(instrument protégé par le droit d'auteur)"
                ),
                key=c.field(key, lambda: logic.group(c.project(), group_id).omit_question_text),
            )
            st.caption(
                _(
                    "Reproduire les items d'un instrument protégé relève de l'équipe ; le "
                    "codebook donnera alors la référence de la question (Q12.r3, p. 4) sans "
                    "son texte."
                )
            )
            c.button(
                _("Enregistrer ce choix"),
                f"save-{key}",
                logic.set_omit_question_text,
                group_id,
                c.state(key),
                reset=(key,),
                submit=True,
            )
