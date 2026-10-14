"""Streamlit review interface. Started by `ddict reviser`, which forces a local address
and turns off Streamlit's usage statistics.

Run as: streamlit run app.py -- path/to/project.dd.json
Every decision is saved to the project file at once.

Buttons read the fields they need when clicked (`_state`), never when the page was drawn:
otherwise a value typed just before the click would be lost.

The chosen variable is kept in `current`, not only in the list's own state: Streamlit
resets a list to its first option when its options change, which sent the person back to
the first variable after a decision.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from ddict import glossary
from ddict.export import wording as w
from ddict.i18n import _
from ddict.project import load_project, save_project
from ddict.project.model import Project, TrackedValue, VariableEntry
from ddict.questionnaire import link
from ddict.questionnaire.labels import ASSUMED_ORDER
from ddict.review import logic

FILTERS = {
    "to_review": _("À réviser"),
    "flagged": _("Avec signalements"),
    "sensitive": _("Sensibles"),
    "unlinked": _("Sans question"),
    "all": _("Toutes"),
}
MAX_OPTION_TEXT = 110


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _project_path() -> Path:
    if "project_path" not in st.session_state:
        st.session_state.project_path = sys.argv[1] if len(sys.argv) > 1 else ""
    return Path(st.session_state.project_path)


def _project() -> Project:
    if "project" not in st.session_state:
        st.session_state.project = load_project(_project_path())
    return st.session_state.project


def _state(key: str):
    return lambda: st.session_state[key]


def _act(action, *args, key: str, timed: bool, reset: tuple[str, ...]) -> None:
    """Run a decision with its arguments read now, save, and keep a message to show next to
    the button `key`. On success, the fields in `reset` are drawn again from the project."""
    values = [a() if callable(a) else a for a in args]
    kwargs = {"now": _now()} if timed else {}
    try:
        action(_project(), *values, **kwargs)
    except logic.ReviewError as error:
        st.session_state.message = ("error", str(error), key)
        return
    save_project(_project(), _project_path())
    st.session_state.message = ("success", _("Enregistré."), key)
    for field in reset:
        st.session_state[field] = st.session_state.fresh[field]()


def _field(key: str, fresh) -> str:
    """Key of an input whose starting value `fresh()` comes from the project.

    The value is set through the session state, never with `value=`: after a decision, `_act`
    sets it again, which the browser shows (it keeps its own copy of a field otherwise).
    """
    st.session_state.setdefault("fresh", {})[key] = fresh
    if key not in st.session_state:
        st.session_state[key] = fresh()
    return key


def _show_message(key: str) -> None:
    message = st.session_state.get("shown_message")
    if message and message[2] == key:
        (st.error if message[0] == "error" else st.success)(message[1])
        st.session_state.message_placed = True


def _message_for(prefix: str) -> bool:
    """Whether the message to show answers a button whose key starts with `prefix`."""
    message = st.session_state.get("shown_message")
    return bool(message and message[2].startswith(prefix))


def _button(
    label: str,
    key: str,
    action,
    *args,
    timed: bool = False,
    primary: bool = False,
    reset: tuple[str, ...] = (),
    submit: bool = False,
) -> None:
    """A button that runs a decision; `submit` for the button of a form (st.form), whose
    fields are sent together when it is clicked."""
    widget = st.form_submit_button if submit else st.button
    widget(
        label,
        key=key,
        on_click=_act,
        args=(action, *args),
        kwargs={"key": key, "timed": timed, "reset": reset},
        type="primary" if primary else "secondary",
    )
    _show_message(key)


def _origin(project: Project, tracked: TrackedValue) -> str:
    text = w.ORIGINS[tracked.origin]
    if tracked.status != "none":
        text += f" — {w.STATUSES[tracked.status]}"
    if tracked.ai_run:
        run = next((r for r in project.ai_runs if r.run_id == tracked.ai_run), None)
        if run is not None:
            text += f" ({run.model}, {run.run_id})"
    return text


def _start_text(name: str, field: str) -> str:
    entry = _project().variable(name)
    tracked: TrackedValue = getattr(entry, field)
    # A rejected proposal is not offered again as the starting text.
    kept = tracked.value if tracked.status != "rejected" else None
    return kept or (entry.file.label if field == "label" else "") or ""


def _tracked_field(project: Project, entry: VariableEntry, field: str, title: str) -> None:
    tracked: TrackedValue = getattr(entry, field)
    key = f"{entry.name}-{field}"
    st.markdown(f"**{title}**")
    if tracked.value is not None:
        st.write(tracked.value)
        st.caption(_origin(project, tracked))
        if tracked.proposed_value is not None:
            st.caption(_("Valeur d'origine : {v}").format(v=tracked.proposed_value))
    elif field == "label" and entry.file.label:
        st.write(entry.file.label)
        st.caption(w.ORIGINS["file"])
    else:
        st.caption(_("(vide)"))

    reset = (f"input-{key}",)
    if tracked.status == "proposed":
        left, right = st.columns(2)
        with left:
            _button(
                _("Accepter"),
                f"accept-{key}",
                logic.decide,
                entry.name,
                field,
                "accept",
                timed=True,
                primary=True,
                reset=reset,
            )
        with right:
            _button(
                _("Rejeter"),
                f"reject-{key}",
                logic.decide,
                entry.name,
                field,
                "reject",
                timed=True,
                reset=reset,
            )
    else:
        # The buttons are gone once decided: their message goes under the field.
        _show_message(f"accept-{key}")
        _show_message(f"reject-{key}")
    st.text_input(
        _("Corriger ou saisir"),
        key=_field(f"input-{key}", lambda: _start_text(entry.name, field)),
        label_visibility="collapsed",
    )
    _button(
        _("Enregistrer"),
        f"save-{key}",
        logic.write,
        entry.name,
        field,
        _state(f"input-{key}"),
        timed=True,
        reset=reset,
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

    st.markdown(f"**{_('Question du questionnaire')}**")
    if tracked.value is not None:
        text = link.describe(project.questionnaire, tracked.value)
        if text is None:
            st.warning(
                _("Rattachement introuvable dans le questionnaire : {id}").format(id=tracked.value)
            )
        else:
            st.write(text)
        st.caption(_origin(project, tracked))
        if tracked.proposed_value is not None:
            st.caption(_("Proposé : {v}").format(v=tracked.proposed_value))
    else:
        st.caption(_("(pas encore rattachée)"))

    key = f"question-{name}"
    if tracked.status == "proposed":
        left, right = st.columns(2)
        with left:
            _button(
                _("Accepter"),
                f"accept-{key}",
                logic.decide,
                name,
                "question",
                "accept",
                timed=True,
                primary=True,
                reset=(key,),
            )
        with right:
            _button(
                _("Rejeter"),
                f"reject-{key}",
                logic.decide,
                name,
                "question",
                "reject",
                timed=True,
                reset=(key,),
            )
    else:
        _show_message(f"accept-{key}")
        _show_message(f"reject-{key}")

    found = link.candidates(project).get(name, [])
    choices = [*found, link.NO_QUESTION, *(i for i in by_id if i not in found)]

    def start() -> str:
        current = _project().variable(name).question
        if current.value in choices and current.status != "rejected":
            return current.value
        return found[0] if found else link.NO_QUESTION

    st.selectbox(_("Rattacher à"), choices, format_func=option_text, key=_field(key, start))
    st.caption(_("En tête de liste : les questions candidates calculées, puis « aucune »."))
    _button(
        _("Rattacher"),
        f"save-{key}",
        logic.link_question,
        name,
        _state(key),
        timed=True,
        reset=(key,),
    )
    _value_labels(project, entry)


def _value_labels(project: Project, entry: VariableEntry) -> None:
    """Value labels from the options of the linked question (D-016), to accept or reject."""
    tracked = entry.value_labels
    if tracked.origin != "questionnaire":
        return
    name = entry.name
    st.markdown(f"**{_('Étiquettes de valeurs tirées des options de réponse')}**")
    table = pd.DataFrame(
        [(w.code_text(v.code), v.label) for v in tracked.value or []],
        columns=[_("Code"), _("Étiquette")],
    )
    st.dataframe(table, hide_index=True)
    st.caption(f"{_origin(project, tracked)} — {_(ASSUMED_ORDER)}")
    if tracked.status == "proposed":
        left, right = st.columns(2)
        with left:
            _button(
                _("Accepter les étiquettes"),
                f"accept-labels-{name}",
                logic.decide,
                name,
                "value_labels",
                "accept",
                timed=True,
                primary=True,
            )
        with right:
            _button(
                _("Rejeter les étiquettes"),
                f"reject-labels-{name}",
                logic.decide,
                name,
                "value_labels",
                "reject",
                timed=True,
            )
    else:
        _show_message(f"accept-labels-{name}")
        _show_message(f"reject-labels-{name}")


def _file_and_computed(entry: VariableEntry) -> None:
    p = entry.profile
    left, right = st.columns(2)
    with left:
        st.subheader(_("Dans le fichier"))
        st.write(f"{_('Étiquette')} : {entry.file.label or _('(aucune)')}")
        if entry.file.measure_level:
            st.write(f"{_('Niveau de mesure')} : {w.MEASURES[entry.file.measure_level]}")
        if entry.file.display_format:
            st.write(f"{_('Format')} : {entry.file.display_format}")
        if w.missing_codes(entry):
            st.write(f"{_('Codes manquants déclarés')} : {w.missing_codes(entry)}")
    with right:
        st.subheader(_("Calculé"))
        st.write(f"{_('Type')} : {w.TYPES.get(p.inferred_type, p.inferred_type)}")
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
            st.write(f"{_('Dates')} : {p.date_min} – {p.date_max}")
        if entry.group_id.value:
            group = f"{_('Groupe')} : {entry.group_id.value}"
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
    for text in w.anomalies(p):
        st.warning(text)
    for text in w.notes(p):
        st.info(text)


def _privacy(entry: VariableEntry) -> None:
    tracked = entry.privacy.privacy_class
    st.markdown(f"**{_('Confidentialité')}** : {w.privacy_text(entry)}")
    caption = w.ORIGINS[tracked.origin]
    if tracked.status != "none":
        caption += f" — {w.STATUSES[tracked.status]}"
    st.caption(caption)
    name = entry.name
    key = f"privacy-{name}"
    st.selectbox(
        _("Classe"),
        logic.PRIVACY_CLASSES,
        format_func=lambda c: w.PRIVACY[c],
        key=_field(
            key, lambda: _project().variable(name).privacy.privacy_class.value or "ordinary"
        ),
    )
    _button(
        _("Confirmer la classe"),
        f"save-{key}",
        logic.set_privacy,
        entry.name,
        _state(key),
        timed=True,
        reset=(key,),
    )


def _sourced(entry: VariableEntry) -> None:
    name = entry.name
    title = _("Champs documentés : étendue théorique, seuils, références, notes")
    keys = ("clear-range", "save-range", "remove-threshold", "add-threshold", "save-notes")
    opened = any(_message_for(f"{k}-{name}") for k in keys)
    with st.expander(title, expanded=opened):
        st.caption(_("Réservés aux personnes ; l'étendue et les seuils exigent une source."))
        r = entry.theoretical_range
        if r:
            st.write(
                f"{_('Étendue théorique')} : {w.number(r.min)} – {w.number(r.max)} ({r.source})"
            )
            _button(
                _("Retirer l'étendue"), f"clear-range-{name}", logic.clear_theoretical_range, name
            )
        with st.form(f"form-range-{name}", border=False):
            c1, c2, c3 = st.columns([1, 1, 3])
            c1.number_input(_("Min"), key=_field(f"range-min-{name}", lambda: 0.0))
            c2.number_input(_("Max"), key=_field(f"range-max-{name}", lambda: 1.0))
            c3.text_input(_("Source de l'étendue"), key=_field(f"range-source-{name}", str))
            _button(
                _("Enregistrer l'étendue"),
                f"save-range-{name}",
                logic.set_theoretical_range,
                name,
                _state(f"range-min-{name}"),
                _state(f"range-max-{name}"),
                _state(f"range-source-{name}"),
                reset=(f"range-min-{name}", f"range-max-{name}", f"range-source-{name}"),
                submit=True,
            )

        for index, t in enumerate(entry.thresholds):
            c1, c2 = st.columns([5, 1])
            c1.write(f"{_('Seuil')} {w.number(t.value)} : {t.meaning} ({t.source})")
            with c2:
                _button(
                    _("Retirer"),
                    f"remove-threshold-{name}-{index}",
                    logic.remove_threshold,
                    name,
                    index,
                )
        with st.form(f"form-threshold-{name}", border=False):
            c1, c2, c3 = st.columns([1, 2, 3])
            c1.number_input(_("Seuil"), key=_field(f"threshold-value-{name}", lambda: 0.0))
            c2.text_input(_("Signification"), key=_field(f"threshold-meaning-{name}", str))
            c3.text_input(_("Source du seuil"), key=_field(f"threshold-source-{name}", str))
            _button(
                _("Ajouter le seuil"),
                f"add-threshold-{name}",
                logic.add_threshold,
                name,
                _state(f"threshold-value-{name}"),
                _state(f"threshold-meaning-{name}"),
                _state(f"threshold-source-{name}"),
                reset=(
                    f"threshold-value-{name}",
                    f"threshold-meaning-{name}",
                    f"threshold-source-{name}",
                ),
                submit=True,
            )

        st.text_area(
            _("Références (une par ligne)"),
            key=_field(
                f"references-{name}", lambda: "\n".join(_project().variable(name).references)
            ),
        )
        st.text_area(
            _("Notes de l'équipe"),
            key=_field(f"notes-{name}", lambda: _project().variable(name).notes or ""),
        )
        _button(
            _("Enregistrer références et notes"),
            f"save-notes-{name}",
            logic.set_references_and_notes,
            name,
            _state(f"references-{name}"),
            _state(f"notes-{name}"),
            reset=(f"references-{name}", f"notes-{name}"),
        )


def _variable(project: Project, entry: VariableEntry) -> None:
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
    for index, issue in enumerate(entry.issues):
        st.info(f"{issue.value} — {_origin(project, issue)}")
        if issue.status == "proposed":
            c1, c2 = st.columns(2)
            with c1:
                _button(
                    _("Accepter"),
                    f"accept-issue-{entry.name}-{index}",
                    logic.decide_issue,
                    entry.name,
                    index,
                    "accept",
                    timed=True,
                )
            with c2:
                _button(
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


def _group(project: Project, group_id: str) -> None:
    group = logic.group(project, group_id)
    st.header(f"{group.group_id} — {group.descriptive_label.value or ''}")
    members = group.members.value or []
    st.write(f"{_('Variables')} : " + ", ".join(members))
    st.write(f"{_('Indices du regroupement')} : {w.basis_text(group.basis)}")
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
    st.multiselect(
        _("Items inversés confirmés"),
        members,
        key=_field(key, lambda: logic.group(_project(), group_id).reverse_items or suspects),
    )
    _button(
        _("Enregistrer les items inversés"),
        f"save-{key}",
        logic.set_reverse_items,
        group_id,
        _state(key),
        reset=(key,),
    )
    st.divider()
    st.caption(_("Nom de l'instrument : réservé aux personnes, avec une source documentée."))

    def instrument(part: str) -> str:
        current = logic.group(_project(), group_id).instrument_name
        return getattr(current, part) if current else ""

    with st.form(f"form-instrument-{group_id}", border=False):
        st.text_input(
            _("Instrument"), key=_field(f"instrument-{group_id}", lambda: instrument("value"))
        )
        st.text_input(
            _("Source de l'instrument"),
            key=_field(f"instrument-source-{group_id}", lambda: instrument("source")),
        )
        _button(
            _("Enregistrer l'instrument"),
            f"save-instrument-{group_id}",
            logic.set_instrument,
            group_id,
            _state(f"instrument-{group_id}"),
            _state(f"instrument-source-{group_id}"),
            reset=(f"instrument-{group_id}", f"instrument-source-{group_id}"),
            submit=True,
        )


def _glossary_entry(project: Project, item) -> None:
    term = item.term
    key = f"glossary-{term}"
    st.markdown(f"**{term}** — {item.meaning}")
    caption = w.GLOSSARY_ORIGINS[item.origin]
    if item.status != "none":
        caption += f" — {w.GLOSSARY_STATUSES[item.status]}"
    if item.source:
        caption += f" ({item.source})"
    st.caption(caption)
    if item.proposed_meaning:
        st.caption(_("Dans le questionnaire : {v}").format(v=item.proposed_meaning))
    names = glossary.variables_using(project, term)
    if names:
        st.caption(_("Variables : {names}").format(names=", ".join(names)))
    reset = (f"input-{key}",)
    if item.status == "proposed":
        left, right = st.columns(2)
        with left:
            _button(
                _("Accepter"),
                f"accept-{key}",
                logic.glossary_decide,
                term,
                "accept",
                timed=True,
                primary=True,
                reset=reset,
            )
        with right:
            _button(
                _("Rejeter"),
                f"reject-{key}",
                logic.glossary_decide,
                term,
                "reject",
                timed=True,
                reset=reset,
            )
    else:
        _show_message(f"accept-{key}")
        _show_message(f"reject-{key}")

    def start() -> str:
        current = glossary.entry(_project(), term)
        return "" if current is None or current.status == "rejected" else current.meaning

    st.text_input(
        _("Définition"),
        key=_field(f"input-{key}", start),
        label_visibility="collapsed",
    )
    _button(
        _("Enregistrer"),
        f"save-{key}",
        logic.glossary_write,
        term,
        _state(f"input-{key}"),
        timed=True,
        reset=reset,
    )
    st.divider()


def _glossary(project: Project) -> None:
    st.header(_("Glossaire des sigles"))
    st.caption(
        _(
            "Les définitions viennent du questionnaire ou de l'équipe ; l'IA n'en propose "
            "jamais. Une définition acceptée aide le modèle et figure dans le codebook."
        )
    )
    for item in list(project.glossary):
        _glossary_entry(project, item)
    if not project.glossary:
        st.info(_("Aucun sigle pour l'instant."))

    undefined = glossary.undefined_acronyms(project)
    if undefined:
        st.subheader(_("Sigles probables sans définition"))
        for part, names in undefined.items():
            st.write(f"**{part.upper()}** : {', '.join(names)}")

    st.subheader(_("Ajouter un sigle"))
    with st.form("form-glossary-add", border=False):
        c1, c2 = st.columns([1, 3])
        c1.text_input(_("Sigle"), key=_field("glossary-new-term", str))
        c2.text_input(_("Définition"), key=_field("glossary-new-meaning", str))
        _button(
            _("Ajouter"),
            "glossary-add",
            logic.glossary_write,
            _state("glossary-new-term"),
            _state("glossary-new-meaning"),
            timed=True,
            reset=("glossary-new-term", "glossary-new-meaning"),
            submit=True,
        )


MODES = {"variables": _("Variables"), "groups": _("Groupes"), "glossary": _("Glossaire")}


def _choose_variable(project: Project, names: list[str], which: str) -> None:
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


def _remember_variable() -> None:
    st.session_state.current = st.session_state.variable


def _option_text(project: Project, name: str) -> str:
    # The file label only: a text that changed with each decision would reset the list.
    label = project.variable(name).file.label
    return f"{name} — {label}" if label else name


def main() -> None:
    st.set_page_config(page_title=_("Révision du dictionnaire"), layout="wide")
    project = _project()
    done, total = logic.progress(project)
    with st.sidebar:
        st.title(project.source.name)
        st.progress(
            done / total if total else 1.0,
            text=_("{done} variables sur {total} sans proposition en attente").format(
                done=done, total=total
            ),
        )
        mode = st.radio(_("Afficher"), list(MODES), key="mode", format_func=MODES.__getitem__)
        chosen = None
        if mode == "variables":
            filters = [f for f in FILTERS if f != "unlinked" or project.questionnaire]
            which = st.radio(_("Filtre"), filters, key="filter", format_func=FILTERS.__getitem__)
            names = [e.name for e in logic.select(project, which)]
            _choose_variable(project, names, which)
            if names:
                chosen = st.selectbox(
                    _("Variable"),
                    names,
                    key="variable",
                    format_func=lambda n: _option_text(project, n),
                    on_change=_remember_variable,
                )
            else:
                st.info(_("Aucune variable dans ce filtre."))
        elif mode == "glossary":
            pending = sum(1 for e in project.glossary if e.status == "proposed")
            st.caption(
                _("{n} sigles, dont {p} à valider").format(n=len(project.glossary), p=pending)
            )
        elif project.groups:
            chosen = st.selectbox(_("Groupe"), [g.group_id for g in project.groups], key="group")
        else:
            st.info(_("Aucun groupe trouvé."))
    notice = st.session_state.pop("notice", None)
    if notice:
        st.info(notice)
    # A message goes next to its button; at the top only when that button is not shown.
    st.session_state.shown_message = st.session_state.pop("message", None)
    st.session_state.message_placed = False
    top = st.empty()
    if mode == "glossary":
        _glossary(project)
    elif chosen is not None:
        if mode == "variables":
            _variable(project, project.variable(chosen))
        else:
            _group(project, chosen)
    message = st.session_state.pop("shown_message")
    if message and not st.session_state.message_placed:
        (top.error if message[0] == "error" else top.success)(message[1])


main()
