"""Streamlit review interface. Started by `ddict reviser`, which forces a local address
and turns off Streamlit's usage statistics.

Run as: streamlit run app.py -- path/to/project.dd.json
Every decision is saved to the project file at once.

Buttons read the fields they need when clicked (`_state`), never when the page was drawn:
otherwise a value typed just before the click would be lost.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from ddict.export import wording as w
from ddict.i18n import _
from ddict.project import load_project, save_project
from ddict.project.model import Project, TrackedValue, VariableEntry
from ddict.review import logic

FILTERS = {
    "to_review": _("À réviser"),
    "flagged": _("Avec signalements"),
    "sensitive": _("Sensibles"),
    "all": _("Toutes"),
}


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


def _act(action, *args, timed: bool = False) -> None:
    """Run a decision with its arguments read now, save, and keep a message to show."""
    values = [a() if callable(a) else a for a in args]
    kwargs = {"now": _now()} if timed else {}
    try:
        action(_project(), *values, **kwargs)
    except logic.ReviewError as error:
        st.session_state.message = ("error", str(error))
        return
    save_project(_project(), _project_path())
    st.session_state.message = ("success", _("Enregistré."))


def _button(label: str, key: str, action, *args, timed: bool = False, primary=False) -> None:
    st.button(
        label,
        key=key,
        on_click=_act,
        args=(action, *args),
        kwargs={"timed": timed},
        type="primary" if primary else "secondary",
    )


def _origin(project: Project, tracked: TrackedValue) -> str:
    text = w.ORIGINS[tracked.origin]
    if tracked.status != "none":
        text += f" — {w.STATUSES[tracked.status]}"
    if tracked.ai_run:
        run = next((r for r in project.ai_runs if r.run_id == tracked.ai_run), None)
        if run is not None:
            text += f" ({run.model}, {run.run_id})"
    return text


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
            )
        with right:
            _button(
                _("Rejeter"), f"reject-{key}", logic.decide, entry.name, field, "reject", timed=True
            )
    current = tracked.value or (entry.file.label if field == "label" else "") or ""
    st.text_input(
        _("Corriger ou saisir"), value=current, key=f"input-{key}", label_visibility="collapsed"
    )
    _button(
        _("Enregistrer"),
        f"save-{key}",
        logic.write,
        entry.name,
        field,
        _state(f"input-{key}"),
        timed=True,
    )


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
        if entry.file.declared_missing:
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


def _privacy(entry: VariableEntry) -> None:
    tracked = entry.privacy.privacy_class
    st.markdown(f"**{_('Confidentialité')}** : {w.privacy_text(entry)}")
    caption = w.ORIGINS[tracked.origin]
    if tracked.status != "none":
        caption += f" — {w.STATUSES[tracked.status]}"
    st.caption(caption)
    key = f"privacy-{entry.name}"
    st.selectbox(
        _("Classe"),
        logic.PRIVACY_CLASSES,
        index=logic.PRIVACY_CLASSES.index(tracked.value or "ordinary"),
        format_func=lambda c: w.PRIVACY[c],
        key=key,
    )
    _button(
        _("Confirmer la classe"),
        f"save-{key}",
        logic.set_privacy,
        entry.name,
        _state(key),
        timed=True,
    )


def _sourced(entry: VariableEntry) -> None:
    name = entry.name
    with st.expander(_("Champs documentés : étendue théorique, seuils, références, notes")):
        st.caption(_("Réservés aux personnes ; l'étendue et les seuils exigent une source."))
        r = entry.theoretical_range
        if r:
            st.write(
                f"{_('Étendue théorique')} : {w.number(r.min)} – {w.number(r.max)} ({r.source})"
            )
            _button(
                _("Retirer l'étendue"), f"clear-range-{name}", logic.clear_theoretical_range, name
            )
        c1, c2, c3 = st.columns([1, 1, 3])
        c1.number_input(_("Min"), key=f"range-min-{name}", value=0.0)
        c2.number_input(_("Max"), key=f"range-max-{name}", value=1.0)
        c3.text_input(_("Source de l'étendue"), key=f"range-source-{name}")
        _button(
            _("Enregistrer l'étendue"),
            f"save-range-{name}",
            logic.set_theoretical_range,
            name,
            _state(f"range-min-{name}"),
            _state(f"range-max-{name}"),
            _state(f"range-source-{name}"),
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
        c1, c2, c3 = st.columns([1, 2, 3])
        c1.number_input(_("Seuil"), key=f"threshold-value-{name}", value=0.0)
        c2.text_input(_("Signification"), key=f"threshold-meaning-{name}")
        c3.text_input(_("Source du seuil"), key=f"threshold-source-{name}")
        _button(
            _("Ajouter le seuil"),
            f"add-threshold-{name}",
            logic.add_threshold,
            name,
            _state(f"threshold-value-{name}"),
            _state(f"threshold-meaning-{name}"),
            _state(f"threshold-source-{name}"),
        )

        st.text_area(
            _("Références (une par ligne)"),
            value="\n".join(entry.references),
            key=f"references-{name}",
        )
        st.text_area(_("Notes de l'équipe"), value=entry.notes or "", key=f"notes-{name}")
        _button(
            _("Enregistrer références et notes"),
            f"save-notes-{name}",
            logic.set_references_and_notes,
            name,
            _state(f"references-{name}"),
            _state(f"notes-{name}"),
        )


def _variable(project: Project, entry: VariableEntry) -> None:
    label = w.label_text(entry, "work")
    st.header(entry.name + (f" — {label}" if label else ""))
    for text in logic.signal_texts(entry):
        st.error(text)
    _file_and_computed(entry)
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
    group = next(g for g in project.groups if g.group_id == group_id)
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
        _("Items inversés confirmés"), members, default=group.reverse_items or suspects, key=key
    )
    _button(
        _("Enregistrer les items inversés"),
        f"save-{key}",
        logic.set_reverse_items,
        group_id,
        _state(key),
    )
    st.divider()
    st.caption(_("Nom de l'instrument : réservé aux personnes, avec une source documentée."))
    current = group.instrument_name
    st.text_input(
        _("Instrument"), value=current.value if current else "", key=f"instrument-{group_id}"
    )
    st.text_input(
        _("Source de l'instrument"),
        value=current.source if current else "",
        key=f"instrument-source-{group_id}",
    )
    _button(
        _("Enregistrer l'instrument"),
        f"save-instrument-{group_id}",
        logic.set_instrument,
        group_id,
        _state(f"instrument-{group_id}"),
        _state(f"instrument-source-{group_id}"),
    )


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
        mode = st.radio(
            _("Afficher"),
            ["variables", "groups"],
            key="mode",
            format_func=lambda m: _("Variables") if m == "variables" else _("Groupes"),
        )
        chosen = None
        if mode == "variables":
            which = st.radio(
                _("Filtre"), list(FILTERS), key="filter", format_func=FILTERS.__getitem__
            )
            names = [e.name for e in logic.select(project, which)]
            if names:
                chosen = st.selectbox(
                    _("Variable"),
                    names,
                    key="variable",
                    format_func=lambda n: f"{n} — {w.label_text(project.variable(n), 'work')}",
                )
            else:
                st.info(_("Aucune variable dans ce filtre."))
        elif project.groups:
            chosen = st.selectbox(_("Groupe"), [g.group_id for g in project.groups], key="group")
        else:
            st.info(_("Aucun groupe trouvé."))
    message = st.session_state.pop("message", None)
    if message:
        (st.error if message[0] == "error" else st.success)(message[1])
    if chosen is None:
        return
    if mode == "variables":
        _variable(project, project.variable(chosen))
    else:
        _group(project, chosen)


main()
