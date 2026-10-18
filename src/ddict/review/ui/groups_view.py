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


def option_text(project: Project, group_id: str) -> str:
    """A group in the list of the sidebar: its number and what it is (v0.16)."""
    return f"{group_id} — {w.group_description(logic.group(project, group_id), 'work')}"


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
    if suspects:  # a proposal, never shown as confirmed (D-126)
        c.offer(
            _("Reprendre les items probables ({items})").format(items=", ".join(suspects)),
            f"offer-{key}",
            key,
            suspects,
        )
    # A form: a change of the list must not reload the page before the click is seen.
    with st.form(f"form-{key}", border=False):
        st.multiselect(
            _("Items inversés confirmés"),
            members,
            placeholder=_("Aucun item inversé"),
            key=c.field(key, lambda: list(logic.group(c.project(), group_id).reverse_items)),
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
    st.write(
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

    def least() -> int | None:
        # Kept as None when every item is required: 0 in the field, once a scoring exists.
        found = logic.group(c.project(), group_id).scoring
        return None if found is None or not found.items else found.min_items_answered or 0

    def rule() -> str | None:
        found = logic.group(c.project(), group_id).scoring
        return found.missing_rule if found is not None and found.items else None

    bounds = scoring.scale_bounds(project.variable(members[0])) if members else None
    found = logic.group(project, group_id).scoring
    known = [*(bounds or ()), *((found.scale_min, found.scale_max) if found else ())]
    # Whole codes (1 to 5): whole numbers in the fields, "1" and not "1.00" (finding 19).
    whole = all(v is None or float(v).is_integer() for v in known)

    def bound(value):
        return int(value) if whole and value is not None else value

    keys = {part: f"scoring-{part}-{group_id}" for part in
            ("items", "how", "min", "max", "least", "rule", "name", "source", "note")}  # fmt: skip
    # Nothing computed or chosen by default is shown as the team's (D-126): buttons take it up.
    offers = st.columns(2)
    if members:
        with offers[0]:
            c.offer(
                _("Prendre les {n} items du groupe").format(n=len(members)),
                f"offer-{keys['items']}",
                keys["items"],
                list(members),
            )
    if bounds:
        with offers[1]:
            low, high = bound(bounds[0]), bound(bounds[1])
            st.button(
                _("Reprendre les bornes des étiquettes ({low} à {high})").format(
                    low=w.number(low), high=w.number(high)
                ),
                key=f"offer-bounds-{group_id}",
                on_click=lambda: st.session_state.update({keys["min"]: low, keys["max"]: high}),
                icon=":material/arrow_downward:",
            )
    number = {"step": 1, "format": "%d"} if whole else {}
    with st.form(f"form-scoring-{group_id}", border=False):
        st.multiselect(
            _("Items du score"),
            members,
            placeholder=_("Choisir les items"),
            key=c.field(keys["items"], lambda: list(current("items", []))),
        )
        st.radio(
            _("Calcul"),
            list(w.AGGREGATIONS),
            format_func=w.AGGREGATIONS.__getitem__,
            horizontal=True,
            key=c.field(keys["how"], lambda: current("aggregation", None)),
        )
        left, middle, right = st.columns(3)
        left.number_input(
            _("Minimum de l'échelle"),
            **number,
            key=c.field(keys["min"], lambda: bound(current("scale_min", None))),
        )
        middle.number_input(
            _("Maximum de l'échelle"),
            **number,
            key=c.field(keys["max"], lambda: bound(current("scale_max", None))),
        )
        right.number_input(
            _("Items répondus, au minimum"),
            min_value=0,
            step=1,
            key=c.field(keys["least"], least),
            help=_("0 : le score exige tous les items."),
        )
        st.radio(
            _("Somme avec des items manquants"),
            list(w.MISSING_RULES),
            format_func=lambda r: w.MISSING_RULES[r].format(n="N"),
            key=c.field(keys["rule"], rule),
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
            study.set_scoring_chosen,
            group_id,
            c.state(keys["items"]),
            c.state(keys["how"]),
            c.state(keys["min"]),
            c.state(keys["max"]),
            c.state(keys["least"]),
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
    st.write(_("Nom de l'instrument : réservé aux personnes, avec une source documentée."))

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
            st.write(
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
