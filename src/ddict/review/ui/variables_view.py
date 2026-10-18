"""The variables: what the file says, what was computed, the question, the proposals.

The chosen variable is kept in `current`, not only in the list's own state: Streamlit
resets a list to its first option when its options change, which sent the person back to
the first variable after a decision.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ddict.export import wording as w
from ddict.i18n import N_, Texts, _, field_label
from ddict.project.model import Project, TrackedValue, VariableEntry
from ddict.questionnaire import link
from ddict.questionnaire.labels import ASSUMED_ORDER
from ddict.review import levels, logic, names
from ddict.review.ui import common as c
from ddict.workflow import tasks

FILTERS = Texts(
    {
        "to_review": N_("À réviser"),
        "flagged": N_("Avec signalements"),
        "sensitive": N_("Sensibles"),
        "unlinked": N_("Sans question"),
        "suspects": N_("Codes suspects"),
        "all": N_("Toutes"),
    }
)


MAX_OPTION_TEXT = 110


def _start_text(name: str, field: str) -> str:
    entry = c.project().variable(name)
    tracked: TrackedValue = getattr(entry, field)
    # A rejected proposal is not offered again as the starting text.
    kept = tracked.value if tracked.status != "rejected" else None
    return kept or (entry.file.label if field == "label" else "") or ""


def _tracked_field(project: Project, entry: VariableEntry, field: str, title: str) -> None:
    tracked: TrackedValue = getattr(entry, field)
    key = f"{entry.name}-{field}"
    input_key = f"input-{key}"

    def show() -> None:
        if tracked.value is not None:
            st.write(tracked.value)
        elif field == "label" and entry.file.label:
            st.write(entry.file.label)
            st.caption(w.ORIGINS["file"])
        else:
            st.caption(_("(vide)"))

    def draw() -> None:
        st.text_input(
            _("Corriger ou saisir"),
            key=c.field(input_key, lambda: _start_text(entry.name, field)),
            label_visibility="collapsed",
        )

    shown = str(st.session_state.get(input_key, tracked.value or "")).strip()
    c.decision_card(
        project,
        tracked,
        key=key,
        title=title,
        show=show,
        field=draw,
        input_key=input_key,
        changed=tracked.status == "proposed" and shown != (tracked.value or ""),
        accept=(logic.accept_shown, entry.name, field, c.state(input_key)),
        reject=(logic.decide, entry.name, field, "reject"),
    )  # once decided, the section's one "Enregistrer" (v0.16, D-124)


def _save_texts(entry: VariableEntry) -> None:
    """One "Enregistrer" for the label, the unit and the description (v0.16, D-124); a
    proposal waits for its own "Accepter"."""
    fields = {
        f: f"input-{entry.name}-{f}" for f in logic.TEXTS if getattr(entry, f).status != "proposed"
    }
    if not fields:
        return
    c.button(
        _("Enregistrer"),
        f"save-texts-{entry.name}",
        logic.write_texts,
        entry.name,
        lambda: {f: st.session_state.get(k, "") for f, k in fields.items()},
        timed=True,
        reset=tuple(fields.values()),  # never a correction typed in a proposal
        watch=tuple(fields.values()),
    )


def _question(project: Project, entry: VariableEntry) -> None:
    """The question the variable comes from. Its text is always read in the questionnaire,
    by identifier: neither the model nor this page can write it."""
    tracked = entry.question
    name = entry.name
    by_id = {t.target_id: t for t in link.targets(project.questionnaire)}

    def option_text(target_id: str) -> str:
        if target_id == link.NO_QUESTION:
            return _("Aucune question du questionnaire")
        text = link.target_text(by_id[target_id])
        if len(text) > MAX_OPTION_TEXT:
            text = text[: MAX_OPTION_TEXT - 1] + "…"
        return f"{target_id} — {text}"

    key = f"question-{name}"
    found = link.candidates(project).get(name, [])
    near = not found
    if near:  # questions around its place in the questionnaire (D-040)
        found = link.neighbours(project).get(name, [])
    # "none" may already be first (v0.6, D-039): each choice once.
    choices = list(dict.fromkeys([*found, link.NO_QUESTION, *by_id]))

    def start() -> str | None:
        # The computed candidate is offered by a button, never chosen in advance (D-126).
        current = c.project().variable(name).question
        if current.value in choices and current.status != "rejected":
            return current.value
        return None

    def draw() -> None:
        if found and start() is None:
            first = _("aucune question") if found[0] == link.NO_QUESTION else found[0]
            c.offer(
                _("Reprendre la proposition du calcul : {choice}").format(choice=first),
                f"offer-{key}",
                key,
                found[0],
            )
        st.selectbox(
            _("Rattacher à"),
            choices,
            format_func=option_text,
            placeholder=_("Choisir une question"),
            key=c.field(key, start),
        )
        if found and found[0] == link.NO_QUESTION:
            why = {
                "identifier": N_("un identifiant"),
                "completion_date": N_("une date de passation"),
                "computed_score": N_("un score calculé"),
            }.get(link.no_question_reason(entry) or "identifier")
            st.caption(
                _(
                    "En tête de liste : « aucune », car la variable semble être {why} ; "
                    "puis les questions candidates calculées."
                ).format(why=_(why))
            )
        elif near and found:
            st.caption(
                _(
                    "En tête de liste : les questions voisines, autour de sa place dans le "
                    "questionnaire (aucun mot ne les relie au nom de la variable), puis « aucune »."
                )
            )
        else:
            st.caption(_("En tête de liste : les questions candidates calculées, puis « aucune »."))

    def show() -> None:
        if tracked.value is None:
            st.caption(_("(pas encore rattachée)"))
            return
        text = link.describe(project.questionnaire, tracked.value)
        if text is None:
            st.warning(
                _("Rattachement introuvable dans le questionnaire : {id}").format(id=tracked.value)
            )
        else:
            st.write(text)

    c.decision_card(
        project,
        tracked,
        key=key,
        title=_("Question du questionnaire"),
        show=show,
        field=draw,
        input_key=key,
        changed=tracked.status == "proposed" and st.session_state.get(key) != tracked.value,
        accept=(logic.link_question, name, c.state(key)),
        reject=(logic.decide, name, "question", "reject"),
        save=(logic.link_question, name, c.state(key)),
        save_label=_("Rattacher"),
    )
    _value_labels(project, entry)


def _value_labels(project: Project, entry: VariableEntry) -> None:
    """Value labels from the options of the linked question (D-016), to accept or reject."""
    tracked = entry.value_labels
    if tracked.origin != "questionnaire":
        return
    name = entry.name

    def show() -> None:
        table = pd.DataFrame(
            [(w.code_text(v.code), v.label) for v in tracked.value or []],
            columns=[_("Code"), _("Étiquette")],
        )
        st.dataframe(table, hide_index=True)

    c.decision_card(
        project,
        tracked,
        key=f"labels-{name}",
        title=_("Étiquettes de valeurs tirées des options de réponse"),
        show=show,
        note=_(ASSUMED_ORDER),
        accept=(logic.decide, name, "value_labels", "accept"),
        reject=(logic.decide, name, "value_labels", "reject"),
        labels=(_("Accepter les étiquettes"), _("Rejeter les étiquettes")),
    )


def _file_and_computed(entry: VariableEntry) -> None:
    p = entry.profile
    left, right = st.columns(2)
    with left:
        st.subheader(_("Dans le fichier"))
        st.write(f"{field_label('Étiquette')}{entry.file.label or _('(aucune)')}")
        if entry.file.measure_level:
            st.write(f"{field_label('Niveau de mesure')}{w.MEASURES[entry.file.measure_level]}")
        if entry.measure_level.value:  # v0.8: decided or proposed on the "Base" page
            st.write(
                f"{field_label('Niveau de mesure retenu')}"
                f"{w.MEASURES[entry.measure_level.value]} ({w.status_text(entry.measure_level)})"
            )
        if entry.file.display_format:
            st.write(f"{field_label('Format')}{entry.file.display_format}")
        if w.missing_codes(entry):
            st.write(f"{field_label('Codes manquants déclarés')}{w.missing_codes(entry)}")
    with right:
        st.subheader(_("Calculé"))
        st.write(f"{field_label('Type')}{w.TYPES.get(p.inferred_type, p.inferred_type)}")
        st.write(
            _("Valides : {v} ; cases vides : {e} ; manquants déclarés : {d}").format(
                v=p.n_valid, e=p.n_system_missing, d=p.n_declared_missing
            )
        )
        if p.min is not None:
            stats = f"{_('Min')} {w.number(p.min)} ; {_('max')} {w.number(p.max)}"
            if p.mean is not None:
                stats += f" ; {_('moyenne')} {w.number(p.mean)}"
            st.write(stats)
        if p.date_min:
            st.write(f"{field_label('Dates')}{p.date_min} – {p.date_max}")
        if entry.group_id.value:
            group = f"{field_label('Groupe')}{entry.group_id.value}"
            if p.item_rest_r is not None:
                group += " " + _("(corrélation avec le reste : {r})").format(
                    r=w.number(p.item_rest_r)
                )
            st.write(group)
    rows = w.value_rows(entry)
    if rows:
        table = pd.DataFrame(
            [
                (code, label, count, _("oui") if missing else "")
                for code, label, count, missing in rows
            ],
            columns=[_("Code"), _("Étiquette"), _("Effectif"), _("Manquant déclaré")],
        )
        st.dataframe(table, hide_index=True)
    # Suspect codes are shown apart, each with its decision (D-028).
    for text in w.anomalies(p, frozenset(p.suspect_missing_codes)):
        st.warning(text)
    for code in p.suspect_missing_codes:
        _sentinel(entry, code)
    for text in w.notes(p):
        st.info(text)


def _sentinel(entry: VariableEntry, code) -> None:
    """A suspect missing code: is it a missing code, or a real value? Only the team knows."""
    name, shown = entry.name, w.code_text(code)
    key = f"sentinel-{name}-{shown}"
    decision = next((d for d in entry.sentinel_decisions if d.code == code), None)
    if decision is None:
        st.warning(
            _(
                "Valeur {code} probablement manquante, non déclarée : est-ce un code manquant ?"
            ).format(code=shown)
        )
        left, right = st.columns(2)
        with left:
            c.button(
                _("C'est un code manquant"),
                f"{key}-missing",
                logic.decide_sentinel,
                name,
                code,
                True,
                timed=True,
            )
        with right:
            c.button(
                _("C'est une vraie valeur"),
                f"{key}-real",
                logic.decide_sentinel,
                name,
                code,
                False,
                timed=True,
            )
        return
    st.info(w.sentinel_notes_for(decision))
    c.button(
        _("Revenir sur cette décision"),
        f"{key}-undo",
        logic.decide_sentinel,
        name,
        code,
        None,
        timed=True,
    )
    c.show_message(f"{key}-missing")
    c.show_message(f"{key}-real")


def _privacy(entry: VariableEntry) -> None:
    tracked = entry.privacy.privacy_class
    name = entry.name
    key = f"privacy-{name}"

    def draw() -> None:
        st.selectbox(
            _("Classe"),
            logic.PRIVACY_CLASSES,
            placeholder=_("Choisir…"),
            format_func=lambda c: w.PRIVACY[c],
            key=c.field(
                key, lambda: c.project().variable(name).privacy.privacy_class.value or "ordinary"
            ),
        )

    c.decision_card(
        c.project(),
        tracked,
        key=key,
        title=_("Confidentialité"),
        show=lambda: st.write(w.privacy_text(entry)),
        field=draw,
        input_key=key,
        changed=tracked.status == "proposed" and st.session_state.get(key) != tracked.value,
        accept=(logic.set_privacy, name, c.state(key)),
        save=(logic.set_privacy, name, c.state(key)),
        save_label=_("Confirmer la classe"),
    )


def _level(project: Project, entry: VariableEntry) -> None:
    """A proposed measure level, decided here too (v0.16); the table of the page Base stays."""
    tracked = entry.measure_level
    if tracked.status != "proposed":
        return
    name = entry.name
    key = f"level-{name}"

    def draw() -> None:
        st.selectbox(
            _("Niveau"),
            list(w.MEASURES),
            placeholder=_("Choisir…"),
            format_func=w.MEASURES.__getitem__,
            key=c.field(key, lambda: c.project().variable(name).measure_level.value),
        )

    c.decision_card(
        project,
        tracked,
        key=key,
        title=_("Niveau de mesure"),
        show=lambda: st.write(w.MEASURES[tracked.value]),
        field=draw,
        input_key=key,
        changed=st.session_state.get(key) != tracked.value,
        accept=(levels.accept_shown, name, c.state(key)),
        reject=(levels.apply_table, {}, {w.final_name(entry): "reject"}),
    )


def _new_name(project: Project, entry: VariableEntry) -> None:
    """A proposed new name, decided here too (v0.16); the table of the page Noms stays."""
    tracked = entry.new_name
    if tracked.status != "proposed":
        return
    name = entry.name
    key = f"name-{name}"

    def draw() -> None:
        st.text_input(
            _("Nouveau nom"),
            key=c.field(key, lambda: c.project().variable(name).new_name.value or ""),
            label_visibility="collapsed",
        )

    c.decision_card(
        project,
        tracked,
        key=key,
        title=_("Nouveau nom"),
        show=lambda: st.write(tracked.value),
        field=draw,
        input_key=key,
        changed=str(st.session_state.get(key, tracked.value)).strip() != tracked.value,
        accept=(names.accept_shown, name, c.state(key)),
        reject=(names.reject, name),
    )


def _sourced(entry: VariableEntry) -> None:
    name = entry.name
    title = _("Champs documentés : étendue théorique, seuils, références, notes")
    keys = ("clear-range", "save-range", "remove-threshold", "add-threshold", "save-notes")
    opened = any(c.message_for(f"{k}-{name}") for k in keys)
    with st.expander(title, expanded=opened):
        st.write(_("Réservés aux personnes ; l'étendue et les seuils exigent une source."))
        r = entry.theoretical_range
        if r:
            st.write(
                field_label("Étendue théorique")
                + f"{w.number(r.min)} – {w.number(r.max)} ({r.source})"
            )
            c.button(
                _("Retirer l'étendue"), f"clear-range-{name}", logic.clear_theoretical_range, name
            )
        with st.form(f"form-range-{name}", border=False):
            c1, c2, c3 = st.columns([1, 1, 3])
            c1.number_input(_("Min"), key=c.field(f"range-min-{name}", lambda: None))
            c2.number_input(_("Max"), key=c.field(f"range-max-{name}", lambda: None))
            c3.text_input(_("Source de l'étendue"), key=c.field(f"range-source-{name}", str))
            c.button(
                _("Enregistrer l'étendue"),
                f"save-range-{name}",
                logic.set_theoretical_range,
                name,
                c.state(f"range-min-{name}"),
                c.state(f"range-max-{name}"),
                c.state(f"range-source-{name}"),
                reset=(f"range-min-{name}", f"range-max-{name}", f"range-source-{name}"),
                submit=True,
            )

        for index, t in enumerate(entry.thresholds):
            c1, c2 = st.columns([5, 1])
            c1.write(f"{_('Seuil')} {w.number(t.value)} : {t.meaning} ({t.source})")
            with c2:
                c.button(
                    _("Retirer"),
                    f"remove-threshold-{name}-{index}",
                    logic.remove_threshold,
                    name,
                    index,
                )
        with st.form(f"form-threshold-{name}", border=False):
            c1, c2, c3 = st.columns([1, 2, 3])
            c1.number_input(_("Seuil"), key=c.field(f"threshold-value-{name}", lambda: None))
            c2.text_input(_("Signification"), key=c.field(f"threshold-meaning-{name}", str))
            c3.text_input(_("Source du seuil"), key=c.field(f"threshold-source-{name}", str))
            c.button(
                _("Ajouter le seuil"),
                f"add-threshold-{name}",
                logic.add_threshold,
                name,
                c.state(f"threshold-value-{name}"),
                c.state(f"threshold-meaning-{name}"),
                c.state(f"threshold-source-{name}"),
                reset=(
                    f"threshold-value-{name}",
                    f"threshold-meaning-{name}",
                    f"threshold-source-{name}",
                ),
                submit=True,
            )

        st.text_area(
            _("Références (une par ligne)"),
            key=c.field(
                f"references-{name}", lambda: "\n".join(c.project().variable(name).references)
            ),
        )
        st.text_area(
            _("Notes de l'équipe"),
            key=c.field(f"notes-{name}", lambda: c.project().variable(name).notes or ""),
        )
        c.button(
            _("Enregistrer références et notes"),
            f"save-notes-{name}",
            logic.set_references_and_notes,
            name,
            c.state(f"references-{name}"),
            c.state(f"notes-{name}"),
            reset=(f"references-{name}", f"notes-{name}"),
        )


def page(project: Project, entry: VariableEntry) -> None:
    label = w.label_text(entry, "work")
    st.header(entry.name + (f" — {label}" if label else ""))
    for text in logic.signal_texts(entry):
        st.error(text)
    _file_and_computed(entry)
    if project.questionnaire is not None:
        st.divider()
        _question(project, entry)
    st.divider()
    left, right = st.columns(2)
    with left:
        _tracked_field(project, entry, "label", _("Libellé"))
        _tracked_field(project, entry, "unit", _("Unité"))
    with right:
        _tracked_field(project, entry, "description", _("Description"))
    _save_texts(entry)
    _level(project, entry)
    _new_name(project, entry)
    for index, issue in enumerate(entry.issues):
        st.info(f"{issue.value} — {c.origin(project, issue)}")
        if issue.status == "proposed":
            c1, c2 = st.columns(2)
            with c1:
                c.button(
                    _("Accepter"),
                    f"accept-issue-{entry.name}-{index}",
                    logic.decide_issue,
                    entry.name,
                    index,
                    "accept",
                    timed=True,
                )
            with c2:
                c.button(
                    _("Rejeter"),
                    f"reject-issue-{entry.name}-{index}",
                    logic.decide_issue,
                    entry.name,
                    index,
                    "reject",
                    timed=True,
                )
    st.divider()
    _privacy(entry)
    _sourced(entry)
    from ddict.review.ui import recode_view

    recode_view.panel(project, entry)  # v0.15 (D-120)


def default_filter(project: Project) -> str:
    """The filter the page opens on (v0.16), never an empty list: "to review" as before when
    something waits there; else that of the first task of the dashboard that leads here; else
    "all"."""
    if logic.select(project, "to_review"):
        return "to_review"
    for task in tasks(project):
        if task.mode == "variables" and task.filter in FILTERS:
            return task.filter
    return "all"


def _show_filter(which: str) -> None:
    st.session_state.filter = which


def empty_filter(project: Project, which: str, filters: list[str]) -> None:
    """In the main area, never a blank page (v0.16): the filter is empty, the others not."""
    st.info(_("Aucune variable dans le filtre « {f} ».").format(f=FILTERS[which]))
    others = [(f, len(logic.select(project, f))) for f in filters if f != which]
    others = [(f, n) for f, n in others if n]
    if not others:
        return
    st.write(_("Filtres qui contiennent des variables :"))
    with st.container(horizontal=True):
        for f, n in others:
            st.button(
                f"{FILTERS[f]} ({n})",
                key=f"show-filter-{f}",
                on_click=_show_filter,
                args=(f,),
            )


def choose_variable(project: Project, names: list[str], which: str) -> None:
    """Keep the chosen variable; if a decision took it out of the filter, take the next one
    and say so (not when the person changed the filter)."""
    current = st.session_state.get("current")
    same_filter = st.session_state.get("last_filter", which) == which
    st.session_state.last_filter = which
    if not names or current in names:
        chosen = current if names else None
    else:
        order = [e.name for e in project.variables]
        start = order.index(current) + 1 if current in order else 0
        following = [n for n in order[start:] if n in names]
        chosen = following[0] if following and same_filter else names[0]
        if current is not None and same_filter:
            st.session_state.notice = _(
                "{old} n'est plus dans ce filtre ; voici la variable suivante : {new}."
            ).format(old=current, new=chosen)
    if chosen is not None:
        st.session_state.current = chosen
        st.session_state.variable = chosen  # set before the list is drawn


def _show_variable(name: str) -> None:
    st.session_state.variable = name
    st.session_state.current = name


def neighbours(names: list[str], chosen: str) -> None:
    """ "Précédente" and "Suivante" at the top of the page (v0.16, finding 23), in the order
    of the filter; the list of the sidebar stays."""
    at = names.index(chosen)
    with st.container(horizontal=True, vertical_alignment="center"):
        st.button(
            _("Précédente"),
            key="variable-previous",
            icon=":material/arrow_back:",
            disabled=at == 0,
            on_click=_show_variable,
            args=(names[at - 1] if at else chosen,),
        )
        st.write(_("{n} sur {total}").format(n=at + 1, total=len(names)))
        st.button(
            _("Suivante"),
            key="variable-next",
            icon=":material/arrow_forward:",
            disabled=at == len(names) - 1,
            on_click=_show_variable,
            args=(names[at + 1] if at < len(names) - 1 else chosen,),
        )


def remember_variable() -> None:
    st.session_state.current = st.session_state.variable


def option_text(project: Project, name: str) -> str:
    # The file label only: a text that changed with each decision would reset the list.
    label = project.variable(name).file.label
    return f"{name} — {label}" if label else name
