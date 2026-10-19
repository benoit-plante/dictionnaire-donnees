"""The recodings on the pages (v0.15, step 3, D-120): on the page "Variables", a box
"Recoder cette variable" (regroup its categories or cut it into classes, by its level) with
the counts of the new categories before anything is kept; on the page "Groupes", the list
of the recodings, each with its rule and its reason. The same functions as `ddict
recoder` (`ddict.analysis.recode.prepared_rule`).
"""

from __future__ import annotations

import streamlit as st

from ddict.analysis.book import Codebook
from ddict.analysis.data import PreparedData, decided
from ddict.analysis.recode import prepared_rule
from ddict.export import wording as w
from ddict.i18n import _
from ddict.project import recodes
from ddict.project.model import Project, VariableEntry
from ddict.project.recodes import RecodeRefused
from ddict.review import logic
from ddict.review.ui import analyses_view
from ddict.review.ui import common as c

NEW = "__new__"


def _key(name: str, field: str) -> str:
    return f"recode-{name}-{field}"


def _table(project: Project):
    """The database as read (before any decision); None when it is not found."""
    if analyses_view.prepared_data(project, "recode") is None:
        return None
    return st.session_state[analyses_view.TABLE][1]


def _cuts(text: str) -> list[float]:
    found = []
    for part in text.replace(";", " ").split():
        try:
            found.append(float(part.replace(",", ".")))
        except ValueError:
            raise RecodeRefused([_("Seuil illisible : {text}.").format(text=part)]) from None
    return found


def _groups_fields(name: str, values: list) -> tuple[list[dict], list]:
    """The groups typed beside each observed value, in the order of their first value; the
    values declared missing."""
    groups: dict[str, list] = {}
    missing = []
    for i, value in enumerate(values):
        if st.session_state.get(_key(name, f"missing-{i}")):
            missing.append(value)
            continue
        label = (st.session_state.get(_key(name, f"group-{i}")) or "").strip()
        if label:
            groups.setdefault(label, []).append(value)
    fields = [
        {"code": n, "label": label, "values": listed}
        for n, (label, listed) in enumerate(groups.items(), start=1)
    ]
    return fields, missing


def _fields(project: Project, entry: VariableEntry, kind: str, values: list) -> dict:
    name = entry.name
    fields: dict = {
        "kind": kind,
        "source": {"variable": entry.name},
        "name": (st.session_state.get(_key(name, "name")) or "").strip(),
        "label": (st.session_state.get(_key(name, "label")) or "").strip()
        or (st.session_state.get(_key(name, "name")) or "").strip(),
        "reason": st.session_state.get(_key(name, "reason")) or "",
    }
    if kind == "groups":
        fields["groups"], fields["missing_values"] = _groups_fields(name, values)
        fields["level"] = st.session_state.get(_key(name, "level")) or "nominal"
    else:
        cuts = _cuts(st.session_state.get(_key(name, "cuts")) or "")
        fields["cuts"] = cuts
        typed = [
            line.strip()
            for line in (st.session_state.get(_key(name, "labels")) or "").splitlines()
            if line.strip()
        ]
        fields["labels"] = typed or (recodes.default_labels(cuts) if cuts else [])
    return fields


def _save(project: Project, name: str, table, fields: dict, rule_id: str | None) -> None:
    """Keep the recoding (new, or `rule_id` changed), then show it in the form; refusals as
    a message."""
    try:
        rule, _found = prepared_rule(project, table, fields, rule_id)
    except RecodeRefused as refused:
        raise logic.ReviewError(" ".join(refused.reasons)) from None
    if rule_id is None:
        recodes.add(project, rule)
    else:
        recodes.replace(project, rule)
    _load(name, rule)
    st.session_state[_key(name, "which")] = rule.id


def _remove(project: Project, rule_id: str, name: str | None = None) -> None:
    try:
        recodes.remove(project, rule_id)
    except RecodeRefused as refused:
        raise logic.ReviewError(" ".join(refused.reasons)) from None
    if name is not None:
        _load(name, None)
        st.session_state[_key(name, "which")] = NEW


def _load(name: str, rule) -> None:
    """Fill the form with a recoding to change, or empty it for a new one."""
    for key in [k for k in st.session_state if str(k).startswith(f"recode-{name}-")]:
        if not key.endswith("-which"):
            del st.session_state[key]
    if rule is None:
        return
    st.session_state[_key(name, "name")] = rule.name
    st.session_state[_key(name, "label")] = rule.label
    st.session_state[_key(name, "reason")] = rule.reason
    if rule.kind == "classes":
        st.session_state[_key(name, "cuts")] = " ".join(w.code_text(c) for c in rule.cuts)
        st.session_state[_key(name, "labels")] = "\n".join(rule.labels)
    else:
        st.session_state[_key(name, "level")] = rule.level


def panel(project: Project, entry: VariableEntry) -> None:
    """The box of the page "Variables" for a variable that can be recoded."""
    name = entry.name
    level = recodes.source_level(project, recodes.reference(project, name))
    sensitive = entry.privacy.privacy_class.value in recodes.NAMING or (
        entry.data_type in ("empty", "mixed", "date", "datetime")
    )
    if sensitive or level is None:
        return
    kind = "classes" if level == "scale" else "groups"
    opened = c.message_for(f"recode-{name}") or bool(st.session_state.get(_key(name, "name")))
    title = (
        _("Recoder cette variable : découper en classes")
        if kind == "classes"
        else _("Recoder cette variable : regrouper ses modalités")
    )
    with st.expander(title, expanded=bool(opened)):
        st.caption(
            _(
                "Une nouvelle variable, tirée de celle-ci, calculée en mémoire après les scores "
                "et avant les exclusions ; le projet garde la règle et sa raison, jamais la "
                "colonne. Elle entre dans les analyses, le plan et les scripts."
            )
        )
        own = [r for r in project.recodes.rules if r.source.variable == name]
        options = [NEW, *[r.id for r in own]]
        which = st.selectbox(
            _("Recodage"),
            options,
            placeholder=_("Choisir…"),
            key=_key(name, "which"),
            format_func=lambda o: (
                _("Nouveau recodage")
                if o == NEW
                else next(f"{r.id} — {r.name}" for r in own if r.id == o)
            ),
            on_change=lambda: _load(
                name,
                next((r for r in own if r.id == st.session_state[_key(name, "which")]), None),
            ),
        )
        table = _table(project)
        if table is None:
            return
        before, reversals, scores = decided(project, table)
        final = w.final_name(entry)
        book = Codebook(project, PreparedData(before, scores, {r.new: r.name for r in reversals}))
        values: list = []
        if kind == "groups":
            counts = before[final].value_counts(sort=False).sort_index()
            values = list(counts.index)
            labels = book.value_labels(final)
            rule = next((r for r in own if r.id == which), None)
            st.markdown(_("**Chaque valeur** : le nom de son nouveau groupe, ou « manquante »."))
            for i, (value, n) in enumerate(counts.items()):
                if rule is not None and _key(name, f"group-{i}") not in st.session_state:
                    found = next((g.label for g in rule.groups if _same(g.values, value)), "")
                    st.session_state[_key(name, f"group-{i}")] = found
                    st.session_state[_key(name, f"missing-{i}")] = _same(rule.missing_values, value)
                left, middle, right = st.columns([3, 3, 1])
                shown = w.code_text(value) + (f" — {labels[value]}" if value in labels else "")
                left.write(f"{shown} (n = {int(n)})")
                middle.text_input(
                    _("Nouveau groupe"), key=_key(name, f"group-{i}"),
                    label_visibility="collapsed", placeholder=_("Nouveau groupe"),
                )  # fmt: skip
                right.checkbox(_("manquante"), key=_key(name, f"missing-{i}"))
            st.radio(
                _("Niveau de la nouvelle variable"), ["nominal", "ordinal"],
                key=_key(name, "level"), format_func=w.MEASURES.__getitem__, horizontal=True,
            )  # fmt: skip
        else:
            st.text_input(
                _("Seuils, croissants (une classe va de son seuil inclus au suivant exclu)"),
                key=_key(name, "cuts"), placeholder="30 45",
            )  # fmt: skip
            st.text_area(
                _("Étiquettes, une par classe (vide : « moins de 30 », « 30 à moins de 45 »…)"),
                key=_key(name, "labels"),
            )  # fmt: skip
        left, right = st.columns(2)
        left.text_input(_("Nom de la nouvelle variable"), key=_key(name, "name"))
        right.text_input(_("Libellé"), key=_key(name, "label"))
        st.text_input(_("Raison du recodage"), key=_key(name, "reason"))
        rule_id = None if which == NEW else which
        try:
            fields = _fields(project, entry, kind, values)
            _rule, found = prepared_rule(project, table, fields, rule_id)
        except RecodeRefused as refused:
            if st.session_state.get(_key(name, "name")):
                for reason in refused.reasons:
                    st.warning(reason)
            found = None
        if found is not None:
            st.markdown(_("**Aperçu** (sur toute la base, avant les exclusions) :"))
            st.table({_("Nouvelle modalité"): [lab for lab, _n in found.counts],
                      "n": [n for _lab, n in found.counts]})  # fmt: skip
            for warning in found.warnings:
                st.warning(warning)
        c.button(
            _("Enregistrer le recodage"),
            f"recode-{name}-save",
            _save,
            name,
            table,
            lambda: _fields(project, entry, kind, values),
            rule_id,
            primary=True,
        )
        if rule_id is not None:
            c.button(_("Retirer ce recodage"), f"recode-{name}-remove", _remove, rule_id, name)


def _same(listed: list, value) -> bool:
    try:
        return any(float(v) == float(value) for v in listed)
    except (TypeError, ValueError):
        return value in listed


def listing(project: Project) -> None:
    """The recodings of the project, on the page "Groupes"."""
    st.subheader(_("Recodages"))
    rows = w.recode_rows(project)
    if not rows:
        st.caption(
            _(
                "Aucun recodage. Pour en créer un : page « Variables », la variable source, "
                "encadré « Recoder cette variable »."
            )
        )
        c.go_button(_("Ouvrir la page Variables"), "go-variables-recode", "variables",
                    filter="all")  # fmt: skip
        return
    sources = {rule.id: rule.source.variable for rule in project.recodes.rules}
    for rule_id, name, label, level, source, parts, reason in rows:
        st.markdown(f"**{rule_id} — `{name}`** ({level}) : {label}")
        st.caption(
            _("Tirée de {source} : {parts}. Raison : {reason}").format(
                source=source, parts=parts, reason=reason
            )
        )
        with st.container(horizontal=True):
            if sources[rule_id] is not None:  # a score's recoding has no variable page
                c.go_button(
                    _("Modifier {id}").format(id=rule_id),
                    f"go-recode-{rule_id}",
                    "variables",
                    **c.variable_fields(sources[rule_id]),
                )
            c.button(_("Retirer"), f"recode-list-remove-{rule_id}", _remove, rule_id,
                     message=False)  # fmt: skip
        c.show_message(f"recode-list-remove-{rule_id}")
    st.caption(_("Pour modifier un recodage : page « Variables », sa variable source."))
