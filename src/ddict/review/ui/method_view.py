"""The Method (v0.12, step 8, D-093 to D-100): the exclusion rules (add, order, remove)
and who each excluded, the flow diagram, the quality signals of the administration, the
variables that describe the sample, and the three paragraphs of the Method with their
holes, as the article draft will hold them; as `ddict exclusions` and
`ddict carnet echantillon` do.

The rules are decisions of the project, saved at once; the variables of the sample are kept
in the notebook. No signal is ever applied: a signal becomes an exclusion when a person
adds it as a rule, and no threshold is proposed by the tool (D-095).
"""

from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

from ddict import i18n
from ddict.analysis import method as method_facts
from ddict.analysis import method_text, quality
from ddict.analysis import notebook as nb
from ddict.analysis.apa import Text, describe_flow
from ddict.analysis.data import PreparedData
from ddict.analysis.formats.figures import image
from ddict.export import wording as w
from ddict.export.preparation import plan
from ddict.i18n import N_, Texts, _
from ddict.project import aside
from ddict.project import exclusions as ex
from ddict.project.model import Project
from ddict.questionnaire.labels import accepted_labels
from ddict.review.ui import analyses_view, groups_view, notebook_view
from ddict.review.ui import common as c

KINDS = Texts(
    {
        "condition": N_("Condition sur une variable"),
        "score": N_("Condition sur un score"),
        "completeness": N_("Complétude d'un groupe"),
        "duration": N_("Durée de passation"),
        "straightlining": N_("Grille en ligne droite"),
        "duplicate": N_("Doublons"),
    }
)
OPERATORS = Texts(
    {
        "eq": N_("= égal à"),
        "ne": N_("≠ différent de"),
        "lt": N_("< plus petit que"),
        "le": N_("≤ plus petit ou égal à"),
        "gt": N_("> plus grand que"),
        "ge": N_("≥ plus grand ou égal à"),
        "in": N_("parmi (valeurs séparées par des virgules)"),
        "missing": N_("manquant"),
    }
)
FLOW_IMAGE = "method-flow-image"  # (flow, language, PNG bytes): drawn once per state
KIND = "method-kind"
OPEN = "method-form-open"  # the form was opened by the page: keep it open
FIGURE_WIDTH = 560
HOLE = "background:#fff59d;color:#000;padding:0 2px"


# --- Changes, saved at once. ---


def _act(action, *args, key: str) -> None:
    """Change the rules, save the project, and keep a message next to the button `key`."""
    project = c.project()
    before = c.recall()
    try:
        done = action(project, *args)
    except ex.ExclusionRefused as error:
        st.session_state.message = ("error", " ".join(error.reasons), key)
        return
    if not c.save(key, before):
        return
    text = _("Règle ajoutée : {id}.").format(id=done.id) if action is _add else _("Enregistré.")
    st.session_state.message = ("success", text, key)


def _field(key: str):
    return st.session_state.get(f"method-new-{key}")


def _new_rule(project: Project) -> dict:
    """The rule the form describes. Raises ExclusionRefused."""
    kind = st.session_state.get(KIND, "condition")
    if kind in ("condition", "score"):
        operator = _field("operator") or "eq"
        typed = str(_field("value") or "")
        values = [v for v in typed.split(",")] if operator == "in" else [typed]
        values = [v for v in values if v.strip()]
        what = _field("score") if kind == "score" else _field("variable")
        if not what:
            raise ex.ExclusionRefused([_("Choisissez une variable.")])
        data = ex.condition_data(project, what, operator, values, score=kind == "score")
    elif kind == "completeness":
        data = {"kind": kind, "group": _field("group"), "min_answered": _field("min")}
    elif kind == "duration":
        seconds = _field("seconds")
        if not seconds:
            raise ex.ExclusionRefused([_("Donnez le seuil de durée, en secondes.")])
        prepared = st.session_state[analyses_view.PREPARED][1]
        data = quality.duration_rule(project, prepared, _field("start"), _field("end"), seconds)
    elif kind == "straightlining":
        data = {"kind": kind, "group": _field("grid")}
    else:
        data = {"kind": kind, "variables": list(_field("duplicates") or [])}
    data["reason"] = str(_field("reason") or "").strip()
    source = str(_field("source") or "").strip()
    if source:
        data["source"] = source
    return data


def _add(project: Project) -> object:
    rule = ex.add(project, _new_rule(project))
    for name in ("reason", "source", "value"):
        st.session_state[f"method-new-{name}"] = ""  # emptied in the browser too
    return rule


def _prepare(key: str, kind: str, fields: dict) -> None:
    """A signal taken up as a rule: the form, filled and opened; the reason and the source
    are left to the person."""
    st.session_state[KIND] = kind
    for name, value in fields.items():
        st.session_state[f"method-new-{name}"] = value
    st.session_state[OPEN] = True
    text = _(
        "Le formulaire « Ajouter une règle », plus haut, est rempli : donnez la raison, puis "
        "ajoutez la règle."
    )
    st.session_state.message = ("success", text, key)


def _take_up(column, key: str, kind: str, **fields) -> None:
    """The button that makes a signal a rule; its message goes under its line."""
    column.button(_("En faire une règle"), key=key, on_click=_prepare, args=(key, kind, fields))


# --- The rules. ---


def _labelled(project: Project, names: dict[str, str]):
    def shown(original: str) -> str:
        label = w.label_text(project.variable(original), "final")
        final = names.get(original, original)
        return f"{final} — {label}" if label else final

    return shown


def _rule(project: Project, rank: int, rule, counts: dict[str, int]) -> None:
    total = len(project.exclusions.rules)
    with st.container(border=True):
        title, count = st.columns([3, 1])
        title.markdown(f"**{rank}. {rule.id} — {rule.reason}**")
        if rule.id in counts:
            count.markdown(_("{n} exclues").format(n=counts[rule.id]))
        caption = ex.rule_text(rule)
        if rule.source:
            caption += " — " + _("Source : {source}").format(source=rule.source)
        st.caption(caption)
        up, down, remove, _space = st.columns([1, 1, 1, 3])
        key = f"method-rule-{rule.id}"
        up.button(
            _("Monter"),
            key=f"{key}-up",
            icon=":material/arrow_upward:",
            disabled=rank == 1,
            on_click=_act,
            args=(ex.move, rule.id, rank - 1),
            kwargs={"key": "method-rules"},
        )
        down.button(
            _("Descendre"),
            key=f"{key}-down",
            icon=":material/arrow_downward:",
            disabled=rank == total,
            on_click=_act,
            args=(ex.move, rule.id, rank + 1),
            kwargs={"key": "method-rules"},
        )
        with remove.popover(_("Retirer"), icon=":material/delete:"):
            st.caption(
                _("{id} quitte les règles ; son numéro ne reviendra pas.").format(id=rule.id)
            )
            st.button(
                _("Retirer {id}").format(id=rule.id),
                key=f"{key}-remove",
                on_click=_act,
                args=(ex.remove, rule.id),
                kwargs={"key": "method-rules"},
            )


def _value_labels(project: Project, original: str) -> str:
    labels = accepted_labels(project.variable(original))
    return ", ".join(f"{w.code_text(v.code)} = {v.label}" for v in labels)


def _form(project: Project, prepared: PreparedData | None) -> None:
    names = w.names_of(project)
    shown = _labelled(project, names)
    # Once a signal filled it or a rule was added, the form stays open: a change of
    # `expanded` would fold it at the next keystroke.
    opened = st.session_state.setdefault(OPEN, False) or c.message_for("method-add")
    st.session_state[OPEN] = opened
    with st.expander(_("Ajouter une règle"), expanded=opened):
        kind = st.selectbox(
            _("Sorte de règle"),
            list(KINDS),
            placeholder=_("Choisir…"),
            key=KIND,
            format_func=KINDS.get,
        )
        if kind in ("condition", "score"):
            if kind == "condition":
                originals = [e.name for e in aside.kept(project)]
                chosen = st.selectbox(
                    _("Variable"),
                    originals,
                    placeholder=_("Choisir…"),
                    key="method-new-variable",
                    format_func=shown,
                )
                if chosen and (labels := _value_labels(project, chosen)):
                    st.caption(_("Valeurs : {labels}").format(labels=labels))
            else:
                scored = [s.group for s in plan(project)[1]]
                if not scored:
                    st.info(_("Aucun groupe n'a de cotation structurée, donc aucun score."))
                    return
                st.selectbox(
                    _("Score du groupe"), scored, placeholder=_("Choisir…"), key="method-new-score"
                )
            operator = st.selectbox(
                _("Condition"), list(OPERATORS), placeholder=_("Choisir…"),
                key="method-new-operator", format_func=OPERATORS.get,
            )  # fmt: skip
            if operator != "missing":
                st.text_input(_("Valeur"), key="method-new-value")
        elif kind in ("completeness", "straightlining"):
            groups = {g.group_id: ex.members(g) for g in project.groups}
            if kind == "straightlining":
                groups = {g: m for g, m in groups.items() if len(m) >= ex.MIN_GRID}
            groups = {g: m for g, m in groups.items() if m}
            if not groups:
                st.info(_("Aucun groupe n'a d'items acceptés."))
                return
            key = "method-new-group" if kind == "completeness" else "method-new-grid"
            group = st.selectbox(
                _("Groupe"), list(groups), placeholder=_("Choisir…"), key=key,
                format_func=lambda g: _("{group} ({k} items)").format(group=g, k=len(groups[g])),
            )  # fmt: skip
            if kind == "completeness":
                st.number_input(
                    _("Exclure qui a répondu à moins de … items"),
                    min_value=1,
                    max_value=len(groups[group]),
                    step=1,
                    key="method-new-min",
                )
        elif kind == "duration":
            dates = quality.date_variables(project)
            if len(dates) < 2:
                st.info(_("Il faut deux variables de date et d'heure : le début et la fin."))
                return
            proposed = quality.proposed_dates(project) or (dates[0], dates[1])
            st.session_state.setdefault("method-new-start", proposed[0])
            st.session_state.setdefault("method-new-end", proposed[1])
            start, end = st.columns(2)
            start.selectbox(
                _("Début"),
                dates,
                placeholder=_("Choisir…"),
                key="method-new-start",
                format_func=shown,
            )
            end.selectbox(
                _("Fin"), dates, placeholder=_("Choisir…"), key="method-new-end", format_func=shown
            )
            st.number_input(
                _("Exclure les passations de moins de … secondes"),
                min_value=1.0,
                value=None,
                step=10.0,
                key="method-new-seconds",
                help=_("L'outil ne propose aucun seuil : c'est un choix de l'équipe."),
            )
        else:
            st.session_state.setdefault(
                "method-new-duplicates", quality.duplicate_variables(project)[:1]
            )
            st.multiselect(
                _("Variables"),
                [e.name for e in aside.kept(project)],
                key="method-new-duplicates",
                placeholder=_("Choisir les variables"),
                format_func=shown,
                help=_("Une réponse qui répète une réponse antérieure sur toutes ces variables."),
            )
        st.text_input(
            _("Raison, telle que publiée"),
            key="method-new-reason",
            placeholder=_("p. ex. Moins de 18 ans"),
        )
        st.text_input(
            _("Source") + (" *" if kind == "duration" else ""),
            key="method-new-source",
            help=_("D'où vient la règle ou son seuil (p. ex. un procès-verbal)."),
        )
        st.button(
            _("Ajouter la règle"),
            key="method-add",
            type="primary",
            disabled=kind == "duration" and prepared is None,
            on_click=_act,
            args=(_add,),
            kwargs={"key": "method-add"},
        )
        c.show_message("method-add")


def _rules(project: Project, prepared: PreparedData | None) -> None:
    st.subheader(_("Règles d'exclusion"))
    st.caption(
        _(
            "Qui ne fait pas partie de l'échantillon analysé, et pourquoi. Les règles "
            "s'appliquent dans leur ordre : une personne n'est comptée que par la première "
            "qui l'exclut. Elles s'appliquent aussi dans les scripts de préparation SPSS et R, "
            "jamais dans la copie documentée. Une règle décrit une condition, jamais une liste "
            "de personnes."
        )
    )
    flow = prepared.flow if prepared is not None else None
    counts = dict(flow.excluded) if flow is not None else {}
    if not project.exclusions.rules:
        st.info(_("Aucune règle d'exclusion : toutes les réponses sont analysées."))
    for rank, rule in enumerate(project.exclusions.rules, start=1):
        _rule(project, rank, rule, counts)
    c.show_message("method-rules")
    _form(project, prepared)


# --- The flow, the signals, the sample. ---


def _flow(project: Project, prepared: PreparedData) -> None:
    flow = prepared.flow
    if flow is None or not flow.excluded:
        return
    st.subheader(_("Diagramme de flux"))
    received, excluded, analysed = st.columns(3)
    received.metric(_("Réponses reçues"), flow.start)
    excluded.metric(_("Exclues"), flow.start - flow.analysed)
    analysed.metric(_("Échantillon analysé"), flow.analysed)
    language = i18n.language()
    stored = st.session_state.get(FLOW_IMAGE)
    signature = (flow, language, tuple(r.reason for r in project.exclusions.rules))
    if stored is None or stored[0] != signature:
        figure = describe_flow(project, flow, language=language)
        stored = (signature, image(figure, language))
        st.session_state[FLOW_IMAGE] = stored
    st.image(stored[1], width=FIGURE_WIDTH)


def _signals(project: Project, prepared: PreparedData) -> None:
    st.subheader(_("Signaux de qualité de la passation"))
    st.write(
        _(
            "Combien de personnes chaque signal toucherait, parmi les {n} que les règles "
            "gardent. Aucun n'est appliqué : un signal devient une exclusion quand vous "
            "l'ajoutez comme règle. L'outil ne propose aucun seuil."
        ).format(n=len(prepared.table))
    )
    names = w.names_of(project)
    shown = _labelled(project, names)
    dates = quality.date_variables(project)
    if len(dates) >= 2:
        st.markdown(_("**Durée de passation**"))
        proposed = quality.proposed_dates(project) or (dates[0], dates[1])
        st.session_state.setdefault("method-signal-start", proposed[0])
        st.session_state.setdefault("method-signal-end", proposed[1])
        start, end, threshold = st.columns(3)
        first = start.selectbox(
            _("Début"),
            dates,
            placeholder=_("Choisir…"),
            key="method-signal-start",
            format_func=shown,
        )
        last = end.selectbox(
            _("Fin"), dates, placeholder=_("Choisir…"), key="method-signal-end", format_func=shown
        )
        seconds = threshold.number_input(
            _("Seuil, en secondes"), min_value=1.0, value=None, step=10.0,
            key="method-signal-seconds",
        )  # fmt: skip
        try:
            found = quality.durations(project, prepared, first, last) if first != last else None
        except ValueError:
            st.warning(_("Ces variables ne se lisent pas comme des dates."))
            found = None
        if found is not None:
            st.caption(
                _(
                    "{n} durées ({invalid} manquantes ou impossibles) ; médiane {median}, "
                    "5e centile {p5}, 10e centile {p10}."
                ).format(
                    n=found.n,
                    invalid=found.invalid,
                    median=quality.seconds_text(found.median),
                    p5=quality.seconds_text(found.p5),
                    p10=quality.seconds_text(found.p10),
                )
            )
            if seconds:
                count = quality.below(project, prepared, found, seconds)
                text, button = st.columns([3, 1])
                text.markdown(
                    _("Moins de {threshold} : **{count}** personnes.").format(
                        threshold=quality.seconds_text(seconds), count=count
                    )
                )
                _take_up(button, "method-signal-duration", "duration",
                         start=first, end=last, seconds=seconds)  # fmt: skip
                c.show_message("method-signal-duration")
    grids = quality.grids(project, prepared)
    if grids:
        st.markdown(_("**Grilles en ligne droite** (tous les items à la même valeur)"))
        for grid in grids:
            text, button = st.columns([3, 1])
            text.markdown(
                _("{group} ({k} items) : **{count}** personnes.").format(
                    group=grid.group, k=grid.items, count=grid.count
                )
            )
            _take_up(button, f"method-signal-grid-{grid.group}", "straightlining", grid=grid.group)
            c.show_message(f"method-signal-grid-{grid.group}")
    proposed = quality.duplicate_variables(project)
    if proposed:
        st.markdown(_("**Doublons** (une réponse qui en répète une antérieure)"))
        for name in proposed:
            found = quality.duplicates(project, prepared, [name])
            text, button = st.columns([3, 1])
            text.markdown(
                _("{name} : **{count}** réponses.").format(
                    name=names.get(name, name), count=found.count
                )
            )
            _take_up(button, f"method-signal-duplicate-{name}", "duplicate", duplicates=[name])
            c.show_message(f"method-signal-duplicate-{name}")


def _sample_options(project: Project) -> list[str]:
    names = list(w.names_of(project).values())
    return names + [s.name for s in plan(project)[1] if s.name not in names]


def _describe_sample(project: Project) -> None:
    chosen = list(st.session_state["method-sample"])
    try:
        notebook = nb.open_notebook(project, c.project_path())
        nb.describe_sample(notebook, project, chosen)
    except nb.NotebookError as error:
        st.session_state.message = ("error", nb.reason_text(error), "method-sample")
        return
    c.save_notebook(notebook, "method-sample", action=_("Description de l'échantillon"))


def _sample(project: Project, notebook: nb.Notebook) -> None:
    st.subheader(_("Description de l'échantillon"))
    st.caption(
        _(
            "Les variables qui décrivent l'échantillon analysé dans le paragraphe "
            "Participants, dans cet ordre : moyenne et écart-type, ou pourcentages. Elles sont "
            "gardées dans le carnet."
        )
    )
    options = _sample_options(project)
    st.session_state["method-sample"] = [
        n for n in nb.sample_names(notebook, project) if n in options
    ]
    st.multiselect(
        _("Variables"),
        options,
        key="method-sample",
        placeholder=_("Choisir les variables"),
        on_change=_describe_sample,
        args=(project,),
    )
    c.show_message("method-sample")


# --- The paragraphs. ---


def paragraph_html(text: Text) -> str:
    """A paragraph as the document holds it: italics, and the holes highlighted."""
    parts = []
    for run in text:
        part = html.escape(run.text)
        if run.sub:
            part = f"<sub>{part}</sub>"
        if run.italic:
            part = f"<i>{part}</i>"
        if run.hole:
            part = f"<span style='{HOLE}'>{part}</span>"
        parts.append(part)
    return "".join(parts)


def _preview(project: Project, prepared: PreparedData, notebook: nb.Notebook) -> None:
    from ddict.analysis.notebook_export import script_name

    st.subheader(_("Aperçu des paragraphes"))
    st.caption(
        _(
            "Écrits par des gabarits à partir du codebook et du carnet, comme dans l'ébauche "
            "d'article. Ce que le codebook ne dit pas devient un trou, surligné : "
            "à compléter sur la page Groupes, ou dans Word."
        )
    )
    c.go_button(_("Compléter les groupes"), "go-groups", "groups",
                **{groups_view.TAB: groups_view.tab_instrument()})  # fmt: skip
    found = method_facts.facts(project, prepared, notebook)
    flow = prepared.flow
    figure = notebook.first_figure if flow is not None and flow.excluded else None
    script = script_name(Path(c.project_path()))
    sections = [(_("Participants"), [method_text.participants(project, found, figure)])]
    instruments = method_text.instruments(project, prepared, found)
    if instruments:
        sections.append((_("Instruments"), instruments))
    sections.append((_("Analyses"), [method_text.analyses(found, script)]))
    for title, paragraphs in sections:
        st.markdown(f"**{title}**")
        for paragraph in paragraphs:
            st.markdown(paragraph_html(paragraph), unsafe_allow_html=True)


def page(project: Project) -> None:
    st.header(_("Méthode"))
    st.caption(
        _(
            "La section Méthode de l'ébauche d'article : qui a été exclu et "
            "pourquoi, la qualité de la passation, la description de l'échantillon, et les "
            "paragraphes Participants, Instruments et Analyses. Les chiffres viennent de la "
            "base, avec les décisions en vigueur ; rien n'est envoyé hors du poste."
        )
    )
    prepared = analyses_view.prepared_data(project, "method")
    _rules(project, prepared)
    if prepared is None:
        return
    _flow(project, prepared)
    _signals(project, prepared)
    notebook = notebook_view._open(project)
    if notebook is None:
        return
    _sample(project, notebook)
    _preview(project, prepared, notebook)
