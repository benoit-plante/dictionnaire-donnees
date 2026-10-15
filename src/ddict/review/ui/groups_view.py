"""The groups of items: alphas, reversed items, instrument, copyrighted text."""

from __future__ import annotations

import streamlit as st

from ddict.export import wording as w
from ddict.i18n import _, field_label
from ddict.project import scoring
from ddict.project.model import Project
from ddict.review import logic, names, study
from ddict.review.ui import bulk_view
from ddict.review.ui import common as c


def page(project: Project, group_id: str) -> None:
    group = logic.group(project, group_id)
    st.header(f"{group.group_id} — {w.group_description(group, 'work')}")
    bulk_view.labels_panel(project, group_id)
    members = group.members.value or []
    st.write(f"{field_label('Variables')}" + ", ".join(members))
    st.write(f"{field_label('Indices du regroupement')}{w.basis_text(group.basis)}")
    if group.kind == "scale":
        _prefix(project, group_id)
    if group.kind == "multiple_response":
        # The options of a "tick all that apply" question (v0.7): no scale, no reversed item.
        st.write(_("Question à réponses multiples : une variable par option cochée."))
        if group.attached:
            st.write(f"{field_label('Texte « autre »')}" + ", ".join(group.attached))
        _instrument_and_text(project, group_id)
        return
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
    _scoring(project, group_id)
    _instrument_and_text(project, group_id)


def _scoring(project: Project, group_id: str) -> None:
    """How the score is computed (v0.8, D-060): written by the team, with its source."""
    st.divider()
    st.subheader(_("Cotation"))
    group = logic.group(project, group_id)
    if group.scoring:
        st.success(w.scoring_text(project, group))
    st.caption(
        _(
            "Réservée aux personnes, avec une source documentée (manuel, article) ; jamais "
            "proposée par l'IA. Les items inversés sont ceux confirmés ci-dessus ; l'étendue "
            "du score est calculée. Une cotation qui n'entre pas dans ce cadre s'écrit en note, "
            "sans items."
        )
    )
    members = group.members.value or []

    def current(part: str, default):
        found = logic.group(c.project(), group_id).scoring
        value = getattr(found, part) if found else None
        return default if value is None else value

    bounds = scoring.scale_bounds(project.variable(members[0])) if members else None
    keys = {part: f"scoring-{part}-{group_id}" for part in
            ("items", "how", "min", "max", "least", "rule", "name", "source", "note")}  # fmt: skip
    with st.form(f"form-scoring-{group_id}", border=False):
        st.multiselect(
            _("Items du score"),
            members,
            key=c.field(keys["items"], lambda: current("items", []) or list(members)),
        )
        st.radio(
            _("Calcul"),
            list(w.AGGREGATIONS),
            format_func=w.AGGREGATIONS.__getitem__,
            horizontal=True,
            key=c.field(keys["how"], lambda: current("aggregation", "sum")),
        )
        left, middle, right = st.columns(3)
        left.number_input(
            _("Minimum de l'échelle"),
            key=c.field(keys["min"], lambda: current("scale_min", bounds[0] if bounds else None)),
        )
        middle.number_input(
            _("Maximum de l'échelle"),
            key=c.field(keys["max"], lambda: current("scale_max", bounds[1] if bounds else None)),
        )
        right.number_input(
            _("Items répondus, au minimum"),
            min_value=0,
            step=1,
            key=c.field(keys["least"], lambda: current("min_items_answered", 0)),
            help=_("0 : le score exige tous les items."),
        )
        st.radio(
            _("Somme avec des items manquants"),
            list(w.MISSING_RULES),
            format_func=lambda r: w.MISSING_RULES[r].format(n="N"),
            key=c.field(keys["rule"], lambda: current("missing_rule", "prorate")),
            help=_(
                "Seulement pour une somme qui accepte des items manquants : la règle du "
                "manuel de l'instrument, avec la même source."
            ),
        )
        st.text_input(
            _("Nom du score"), key=c.field(keys["name"], lambda: current("score_name", ""))
        )
        st.text_input(_("Source"), key=c.field(keys["source"], lambda: current("source", "")))
        st.text_area(_("Note"), key=c.field(keys["note"], lambda: current("note", "")), height=68)
        c.button(
            _("Enregistrer la cotation"),
            f"save-scoring-{group_id}",
            study.set_scoring,
            group_id,
            c.state(keys["items"]),
            c.state(keys["how"]),
            c.state(keys["min"]),
            c.state(keys["max"]),
            lambda: int(st.session_state[keys["least"]] or 0) or None,
            c.state(keys["name"]),
            c.state(keys["source"]),
            c.state(keys["note"]),
            c.state(keys["rule"]),
            reset=tuple(keys.values()),
            submit=True,
        )
    if group.scoring:
        c.button(
            _("Retirer la cotation"),
            f"remove-scoring-{group_id}",
            study.remove_scoring,
            group_id,
            reset=tuple(keys.values()),
        )


def _prefix(project: Project, group_id: str) -> None:
    """The prefix of the new names of its items (v0.7): `k6` gives k6_1, k6_2..."""
    key = f"prefix-{group_id}"
    current = logic.group(project, group_id).name_prefix
    if current.status == "proposed":
        st.info(_("Préfixe repris de la vague précédente : {prefix}").format(prefix=current.value))
        c.button(
            _("Accepter ce préfixe"),
            f"accept-{key}",
            names.accept_group_prefix,
            group_id,
            timed=True,
        )
    with st.form(f"form-{key}", border=False):
        st.text_input(
            _("Préfixe des noms de ses items"),
            key=c.field(key, lambda: logic.group(c.project(), group_id).name_prefix.value or ""),
            help=_(
                "Le sigle de l'échelle, en minuscules (k6, stai…) : ses items s'appelleront "
                "k6_1, k6_2… Donné par vous, jamais par l'IA."
            ),
        )
        c.button(
            _("Enregistrer le préfixe"),
            f"save-{key}",
            names.set_group_prefix,
            group_id,
            c.state(key),
            timed=True,
            reset=(key,),
            submit=True,
        )


def _instrument_and_text(project: Project, group_id: str) -> None:
    """The instrument's name, with its source, and the choice not to reproduce its text."""
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
