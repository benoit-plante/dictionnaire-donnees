"""The page "Plan" (v0.13, step 6, D-101 to D-104, D-109): the general rules, the
hypotheses (add, modify, order, remove) with their conditions checked, freezing, the
amendments and the preregistration; as `ddict plan` does.

Every change is saved at once. After the plan is frozen, a change needs a reason, typed
once at the top of the page, and becomes an amendment (D-102); the notebook then follows
the plan. Removing the whole plan asks a confirmation on the page.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from ddict import i18n
from ddict.analysis import article_text as article
from ddict.analysis import conditions, planning, prereg
from ddict.analysis import notebook as nb
from ddict.analysis import plan_notebook as pn
from ddict.analysis.apa import plain
from ddict.analysis.book import Codebook
from ddict.analysis.catalogue import CATALOGUE, CHOICES, OPTIONS, ROLES, TITLES
from ddict.analysis.data import PreparedData, chosen_levels
from ddict.i18n import N_, Texts, _, field_label
from ddict.project import save_project
from ddict.project.model import Hypothesis, Project
from ddict.review.ui import analyses_view
from ddict.review.ui import common as c

REASON = "plan-reason"
EDITING = "plan-editing"  # the hypothesis the form modifies; none: the form adds one
CLEARING = "plan-clearing"  # the removal of the whole plan, waiting for its confirmation
NEW = "plan-new-"
FORM = "plan-form-open"
OPENED = "plan-form-opened"  # once true, `expanded` never changes back
ANALYSES = [k for k in CATALOGUE if k in planning.EFFECTS]
DIRECTION_LABELS = Texts(
    {
        "": N_("Aucun"),
        "first_higher": N_("Le premier groupe plus élevé"),
        "second_higher": N_("Le second groupe plus élevé"),
        "positive": N_("Positif"),
        "negative": N_("Négatif"),
    }
)
EFFECT_LABELS = Texts({"model": N_("Le modèle entier"), "predictor": N_("Un prédicteur")})
ORIGIN_LABELS = Texts({"primary": N_("Primaires"), "secondary": N_("Secondaires")})


def _today() -> str:
    return date.today().isoformat()


def _reason() -> str | None:
    return (st.session_state.get(REASON) or "").strip() or None


def _prepared() -> PreparedData | None:
    found = st.session_state.get(analyses_view.PREPARED)
    return found[1] if found else None


def _saved(project: Project) -> None:
    """Save the project; a frozen plan's notebook follows it (§ 6 of the sheet)."""
    save_project(project, c.project_path())
    if project.plan.frozen is None:
        return
    notebook = nb.open_notebook(project, c.project_path())
    waiting = pn.sync(notebook, project, _prepared(), _today())
    if notebook.entries:
        nb.save_notebook(notebook, nb.notebook_path(c.project_path()))
    if waiting:
        st.session_state["plan-waiting"] = waiting


def _act(action, *args, key: str, done: str = "", reset: tuple[str, ...] = ()) -> None:
    """Change the plan, save, and keep a message next to the button `key`; on a refusal,
    the fields in `reset` go back to what the project holds."""
    project = c.project()
    try:
        action(project, *args)
    except planning.PlanRefused as error:
        st.session_state.message = ("error", " ".join(error.reasons), key)
        for name in reset:
            st.session_state[name] = st.session_state.fresh[name]()
        return
    _saved(project)
    st.session_state.message = ("success", done or _("Enregistré."), key)


# --- The general rules. ---


def _alpha_text(project: Project) -> str:
    value = project.plan.alpha
    return "" if value is None else i18n.decimal(f"{value:g}")


def _set_rule(project: Project, name: str, key: str) -> None:
    value = st.session_state[key]
    if name == "alpha":
        text = str(value or "").strip().replace(",", ".")
        try:
            value = float(text) if text else None
        except ValueError:
            raise planning.PlanRefused(
                [_("Le seuil α est un nombre strictement entre 0 et 1.")]
            ) from None
    planning.set_rules(project, {name: value}, _reason(), _today())


def _rules(project: Project) -> None:
    st.subheader(_("Règles générales"))
    fields = {
        "alpha": c.field("plan-alpha", lambda: _alpha_text(c.project())),
        "correction": c.field("plan-correction", lambda: c.project().plan.correction),
        "sample_size": c.field("plan-sample", lambda: c.project().plan.sample_size),
        "data_origin": c.field("plan-origin", lambda: c.project().plan.data_origin),
        "data_status": c.field("plan-status", lambda: c.project().plan.data_status),
    }

    def changed(name: str):
        return {
            "on_change": _act,
            "args": (_set_rule, name, fields[name]),
            "kwargs": {"key": "plan-rules", "reset": (fields[name],)},
        }

    left, right = st.columns(2)
    left.text_input(
        _("Seuil α"),
        key=fields["alpha"],
        placeholder=_("p. ex. 0,05"),
        help=_("Tapé par l'équipe : la page n'en enregistre aucun d'office."),
        **changed("alpha"),
    )
    right.selectbox(
        _("Correction pour comparaisons multiples"),
        ["none", "holm", "bonferroni"],
        key=fields["correction"],
        format_func=article.CORRECTIONS.__getitem__,
        **changed("correction"),
    )
    st.text_area(
        _("Justification de la taille d'échantillon"),
        key=fields["sample_size"],
        height=80,
        **changed("sample_size"),
    )
    st.radio(
        _("Origine des données"),
        ["primary", "secondary"],
        key=fields["data_origin"],
        format_func=ORIGIN_LABELS.__getitem__,
        horizontal=True,
        **changed("data_origin"),
    )
    st.radio(
        _("État des données quand le plan a été écrit (déclaré par l'équipe)"),
        list(prereg.STATUSES),
        key=fields["data_status"],
        format_func=prereg.STATUSES.__getitem__,
        **changed("data_status"),
    )
    c.show_message("plan-rules")


# --- The hypotheses. ---


def _summary(project: Project, hypothesis: Hypothesis) -> str:
    for line in prereg._models(project):
        text = plain(line)
        if text.startswith(f"{hypothesis.id}. "):
            return text.split(". ", 1)[1]
    return ""


def _hypothesis(project, rank, hypothesis, prepared, deviations) -> None:
    total = len(project.plan.hypotheses)
    with st.container(border=True):
        kind = prereg.KINDS[hypothesis.kind]
        if hypothesis.family:
            kind = _("{kind}, famille {family}").format(kind=kind, family=hypothesis.family)
        st.markdown(f"**{hypothesis.id}** ({kind}) — {hypothesis.statement}")
        st.caption(_summary(project, hypothesis))
        check = planning.review(project, hypothesis, prepared)
        for reason in check.refusals:
            st.error(reason)
        for warning in check.warnings:
            st.warning(warning)
        if hypothesis.id in deviations:
            st.warning(deviations[hypothesis.id])
        up, down, edit, remove, _space = st.columns([1, 1, 1, 1, 2])
        key = f"plan-h-{hypothesis.id}"
        up.button(
            _("Monter"),
            key=f"{key}-up",
            icon=":material/arrow_upward:",
            disabled=rank == 1,
            on_click=_act,
            args=(planning.move, hypothesis.id, rank - 1),
            kwargs={"key": "plan-hypotheses"},
        )
        down.button(
            _("Descendre"),
            key=f"{key}-down",
            icon=":material/arrow_downward:",
            disabled=rank == total,
            on_click=_act,
            args=(planning.move, hypothesis.id, rank + 1),
            kwargs={"key": "plan-hypotheses"},
        )
        edit.button(
            _("Modifier"),
            key=f"{key}-edit",
            icon=":material/edit:",
            on_click=_edit,
            args=(hypothesis.id,),
        )
        with remove.popover(_("Retirer"), icon=":material/delete:"):
            st.caption(
                _("{id} quitte le plan ; son numéro ne reviendra pas.").format(id=hypothesis.id)
            )
            st.button(
                _("Retirer {id}").format(id=hypothesis.id),
                key=f"{key}-remove",
                on_click=_act,
                args=(_remove, hypothesis.id),
                kwargs={"key": "plan-hypotheses"},
            )


def _remove(project: Project, hypothesis_id: str) -> None:
    planning.remove(project, hypothesis_id, _reason(), _today())


# --- The form: add an hypothesis, or modify one. ---


def _names(project: Project, refs) -> list[str]:
    found = []
    for ref in refs:
        try:
            found.append(nb.resolve(project, ref))
        except nb.NotebookError:
            continue
    return found


def _clear_form() -> None:
    """The form emptied, in the browser too: each field is set again, never only removed
    (the browser keeps its own copy of a field otherwise)."""
    empty = {"statement": "", "analysis": ANALYSES[0], "family": "", "direction": "",
             "kind": "confirmatory",
             "pair": [], "predictor": None}  # fmt: skip
    for key in [k for k in st.session_state if str(k).startswith(NEW)]:
        name = str(key)[len(NEW) :]
        if name in empty:
            st.session_state[key] = empty[name]
        elif name.startswith("role-"):
            st.session_state[key] = [] if isinstance(st.session_state[key], list) else None
        elif name.startswith("levels-") or name == "subgroup-values":
            st.session_state[key] = []
        elif name in ("subgroup-variable", "subgroup-value", "subgroup-number"):
            st.session_state[key] = None
    st.session_state.pop(EDITING, None)


def _edit(hypothesis_id: str) -> None:
    """The form, filled with the hypothesis to modify."""
    project = c.project()
    h = planning.find(project, hypothesis_id)
    _clear_form()
    st.session_state[EDITING] = h.id
    st.session_state[FORM] = True
    st.session_state[NEW + "statement"] = h.statement
    st.session_state[NEW + "analysis"] = h.analysis
    for role, refs in h.roles.items():
        names = _names(project, refs)
        most = next(r.most for r in CATALOGUE[h.analysis].roles if r.key == role)
        st.session_state[f"{NEW}role-{h.analysis}-{role}"] = (
            names[0] if most == 1 and names else names
        )
    for option, value in h.options.items():
        if option in CATALOGUE[h.analysis].options:
            st.session_state[f"{NEW}option-{h.analysis}-{option}"] = value
    group = (_names(project, h.roles.get("group", [])) or [None])[0]
    prepared = _prepared()
    if h.options.get("levels") and group and prepared is not None:
        codes = chosen_levels(h.options["levels"], prepared.table[group])
        st.session_state[f"{NEW}levels-{group}"] = codes
    if h.effect.kind == "predictor":
        st.session_state[NEW + "effect"] = "predictor"
        st.session_state[NEW + "predictor"] = (_names(project, [h.effect.variable]) or [None])[0]
    elif h.effect.kind == "model":
        st.session_state[NEW + "effect"] = "model"
    elif h.effect.kind == "pair":
        pair = _names(project, h.effect.variables)
        if len(pair) == 2:
            st.session_state[NEW + "pair"] = pair
    if h.subgroup is not None:
        try:
            subset = nb.resolved_subgroup(project, h.subgroup)
        except nb.NotebookError:
            subset = None
        if subset is not None:
            st.session_state[NEW + "subgroup-variable"] = subset.name
            st.session_state[NEW + "subgroup-operator"] = subset.operator
            if subset.operator == "in":
                st.session_state[NEW + "subgroup-values"] = list(subset.value)
            else:
                st.session_state[NEW + "subgroup-value"] = subset.value
    st.session_state[NEW + "direction"] = h.direction or ""
    st.session_state[NEW + "kind"] = h.kind
    st.session_state[NEW + "family"] = h.family or ""


def _shown(book: Codebook):
    def shown(name: str) -> str:
        label = book.label(name)
        return label if label.startswith(name) else f"{name} — {label}"

    return shown


def _choose(project: Project, key: str, book: Codebook) -> dict[str, list[str]]:
    chosen: dict[str, list[str]] = {}
    for role in CATALOGUE[key].roles:
        names = conditions.candidates(project, CATALOGUE[key], role.key)
        widget = f"{NEW}role-{key}-{role.key}"
        if not names:
            st.info(
                _(
                    "{role} : aucune variable ne convient. Le niveau de mesure se décide sur la "
                    "page Base."
                ).format(role=ROLES[role.key])
            )
            continue
        if role.most == 1:
            picked = st.selectbox(
                ROLES[role.key],
                names,
                index=None,
                key=widget,
                format_func=_shown(book),
                placeholder=_("Aucune") if role.least == 0 else _("Choisir une variable"),
            )
            chosen[role.key] = [picked] if picked else []
        else:
            chosen[role.key] = st.multiselect(
                ROLES[role.key],
                names,
                key=widget,
                format_func=_shown(book),
                max_selections=role.most,
                placeholder=_("Choisir de {least} à {most} variables").format(
                    least=role.least, most=role.most
                ),
            )
    return {k: v for k, v in chosen.items() if v}


def _compared(key, chosen, options, prepared: PreparedData | None, book: Codebook):
    """The two groups of a t test or the two measures of a paired one, by their names, in
    the order the test takes them (v0.14); None while they are not known."""
    if key == "paired" and chosen.get("first") and chosen.get("second"):
        return book.label(chosen["first"][0]), book.label(chosen["second"][0])
    group = (chosen.get("group") or [None])[0]
    if key != "t_test" or group is None or prepared is None:
        return None
    used = [n for names in chosen.values() for n in names]
    codes = sorted(set(prepared.table[used].dropna()[group]))
    if options.get("levels"):
        codes = [c for c in chosen_levels(options["levels"], prepared.table[group]) if c in codes]
    if len(codes) != 2:
        return None
    return book.category(group, codes[0]), book.category(group, codes[1])


def _levels(key, chosen, options, prepared: PreparedData | None, book: Codebook) -> None:
    """A t test whose group has more than two categories: the two compared, as on the page
    "Analyses" and with `--modalites`."""
    group = (chosen.get("group") or [None])[0]
    if key != "t_test" or group is None or prepared is None:
        return
    used = [n for names in chosen.values() for n in names]
    codes = sorted(set(prepared.table[used].dropna()[group]))
    if len(codes) <= 2:
        return
    picked = st.multiselect(
        OPTIONS["levels"],
        codes,
        key=f"{NEW}levels-{group}",
        max_selections=2,
        format_func=lambda code: book.category(group, code),
        placeholder=_("Choisir les deux groupes à comparer"),
    )
    if len(picked) == 2:
        options["levels"] = ",".join(analyses_view._code_option(code) for code in picked)


def _form_data(project: Project, prepared: PreparedData | None) -> dict | None:
    """The form's widgets, and the fields of the hypothesis they describe."""
    book = Codebook(project, prepared)
    statement = st.text_area(_("Hypothèse"), key=NEW + "statement", height=80)
    key = st.selectbox(_("Analyse"), ANALYSES, key=NEW + "analysis", format_func=TITLES.__getitem__)
    chosen = _choose(project, key, book)
    options = {}
    for option, values in CATALOGUE[key].options.items():
        if option == "alternative":  # set by the expected direction (D-103)
            continue
        options[option] = st.radio(
            OPTIONS[option],
            list(values),
            key=f"{NEW}option-{key}-{option}",
            format_func=CHOICES.__getitem__,
            horizontal=True,
        )
    _levels(key, chosen, options, prepared, book)
    effect: dict = {}
    kinds = planning.EFFECTS[key]
    if key == "regression":
        picked = st.radio(
            _("Effet testé"),
            list(kinds),
            key=NEW + "effect",
            format_func=EFFECT_LABELS.__getitem__,
            horizontal=True,
        )
        if picked == "model":
            effect["model"] = True
        else:
            predictor = st.selectbox(
                _("Prédicteur testé"),
                chosen.get("predictors", []),
                index=None,
                key=NEW + "predictor",
                format_func=_shown(book),
            )
            effect["predictor"] = predictor
    elif key == "correlation" and len(chosen.get("variables", [])) > 2:
        pair = st.multiselect(
            _("Paire testée"),
            chosen["variables"],
            key=NEW + "pair",
            max_selections=2,
            placeholder=_("Choisir les deux variables de la paire"),
            format_func=_shown(book),
        )
        if len(pair) == 2:
            effect["pair"] = pair
    kind_of_effect = (
        "predictor" if effect.get("predictor") else "model" if effect.get("model") else kinds[0]
    )
    allowed = planning.DIRECTIONS.get(kind_of_effect, ())
    direction = ""
    named = _compared(key, chosen, options, prepared, book)

    def shown(code: str) -> str:
        if named and code in ("first_higher", "second_higher"):
            high, low = named if code == "first_higher" else named[::-1]
            return _("{high} plus élevé que {low}").format(high=high, low=low)
        return DIRECTION_LABELS[code]

    if allowed:
        direction = st.radio(
            _("Sens attendu"),
            ["", *allowed],
            key=NEW + "direction",
            format_func=shown,
            horizontal=True,
            help=_(
                "Pour un test t, un sens rend le test unilatéral ; les groupes suivent l'ordre "
                "de leurs codes."
            ),
        )
    subset = None
    if prepared is not None:
        subset = analyses_view.subgroup_widgets(project, prepared, book, NEW + "subgroup")
    left, right = st.columns(2)
    kind = left.radio(
        _("Caractère"),
        ["confirmatory", "exploratory"],
        key=NEW + "kind",
        format_func=prereg.KINDS.__getitem__,
        horizontal=True,
    )
    family = right.text_input(
        _("Famille (correction)"),
        key=NEW + "family",
        disabled=kind == "exploratory",
        placeholder=_("p. ex. F1"),
    )
    return {
        "statement": statement,
        "analysis": key,
        "chosen": chosen,
        "options": options,
        "effect": effect,
        "direction": direction,
        "kind": kind,
        "family": family if kind == "confirmatory" else "",
        "subgroup": subset,
    }


def _submit(project: Project, form: dict) -> None:
    data = planning.data_from_names(
        project,
        form["statement"],
        form["analysis"],
        form["chosen"],
        form["options"],
        pair=form["effect"].get("pair"),
        predictor=form["effect"].get("predictor"),
        model=bool(form["effect"].get("model")),
        direction=form["direction"],
        kind=form["kind"],
        family=form["family"].strip(),
        subgroup=form.get("subgroup"),
    )
    editing = st.session_state.get(EDITING)
    if editing:
        old = planning.find(project, editing)
        changes = {k: v for k, v in data.items() if k != "effect"}
        if "effect" in data:
            changes["effect"] = data["effect"]
        elif old.analysis != data["analysis"] or old.effect.kind in ("pair", "predictor"):
            changes["effect"] = None
        planning.modify(project, editing, changes, _prepared(), _reason(), _today())
    else:
        planning.add(project, data, _prepared(), _reason(), _today())
    _clear_form()


def _form(project: Project, prepared: PreparedData | None) -> None:
    editing = st.session_state.get(EDITING)
    title = _("Modifier {id}").format(id=editing) if editing else _("Ajouter une hypothèse")
    # A key keeps it open or closed from one run to the next, whatever shows above it; once
    # opened by a modification or a message, `expanded` stays true: its change would fold
    # the form at the next keystroke, as on the page "Méthode".
    opened = st.session_state.get(OPENED, False) or bool(editing) or c.message_for("plan-form")
    st.session_state[OPENED] = opened
    with st.expander(
        title,
        expanded=opened,
        key=FORM,
        on_change="rerun",
    ):
        form = _form_data(project, prepared)
        save, cancel, _space = st.columns([1, 1, 3])
        save.button(
            _("Enregistrer {id}").format(id=editing) if editing else _("Ajouter l'hypothèse"),
            key="plan-form-save",
            type="primary",
            on_click=_act,
            args=(_submit, form),
            kwargs={"key": "plan-form"},
        )
        if editing:
            cancel.button(_("Annuler"), key="plan-form-cancel", on_click=_clear_form)
        c.show_message("plan-form")


# --- Freezing, the amendments, removing the whole plan. ---


def _freeze(project: Project) -> None:
    notebook = nb.open_notebook(project, c.project_path())
    pn.freeze(notebook, project, _prepared(), _today())
    nb.save_notebook(notebook, nb.notebook_path(c.project_path()))


def _clear(project: Project) -> None:
    notebook = nb.open_notebook(project, c.project_path())
    pn.clear(notebook, project)
    if nb.notebook_path(c.project_path()).is_file():
        nb.save_notebook(notebook, nb.notebook_path(c.project_path()))
    st.session_state.pop(CLEARING, None)
    for key in ("plan-alpha", "plan-correction", "plan-sample", "plan-origin", "plan-status"):
        st.session_state.pop(key, None)


def _ready(project: Project, prepared: PreparedData | None) -> None:
    """What freezing the plan needs, as a list to tick (v0.16): a plan just begun is not a
    fault, so nothing here is shown in red."""
    plan = project.plan
    computable = [
        f"{h.id} : {reason}"
        for h in plan.hypotheses
        for reason in planning.review(project, h, prepared).refusals
    ]
    lines = [
        (_("Au moins une hypothèse"), bool(plan.hypotheses)),
        (_("Le seuil α du plan"), plan.alpha is not None),
        (
            _("L'origine des données et leur état quand le plan a été écrit"),
            plan.data_origin is not None and plan.data_status is not None,
        ),
        (
            _("La base ouverte : chaque hypothèse devient une analyse du carnet"),
            prepared is not None,
        ),
        (_("Chaque hypothèse calculable sur la base"), bool(plan.hypotheses) and not computable),
    ]
    st.write(field_label("Pour figer le plan"))
    for text, done in lines:  # read-only boxes, in normal text: a disabled box is faded
        box = ":material/check_box:" if done else ":material/check_box_outline_blank:"
        st.markdown(f"{box} {text}")
    for reason in computable:
        st.write(f"- {reason}")


def _frozen(project: Project, prepared: PreparedData | None) -> None:
    st.subheader(_("Figer le plan"))
    plan = project.plan
    if plan.frozen is None:
        st.write(
            _(
                "Le plan figé reçoit sa date et son empreinte ; chaque hypothèse devient une "
                "analyse du carnet. Ensuite, toute modification exige une raison et devient un "
                "amendement, gardé pour toujours."
            )
        )
        refusals = planning.freeze_refusals(project, prepared)
        _ready(project, prepared)
        st.button(
            _("Figer le plan"),
            key="plan-freeze",
            type="primary",
            icon=":material/lock:",
            disabled=bool(refusals) or prepared is None,
            on_click=_act,
            args=(lambda p: _freeze(p),),
            kwargs={"key": "plan-freeze", "done": _("Plan figé.")},
        )
        c.show_message("plan-freeze")
        return
    st.success(
        _("Plan arrêté le {date} ; empreinte : {fingerprint}.").format(
            date=prereg.long_date(plan.frozen.date), fingerprint=plan.frozen.fingerprint[:12]
        )
    )
    if plan.frozen.prior:
        st.caption(
            _("Déjà dans le carnet au gel : {ids}.").format(
                ids=", ".join(f"{p.hypothesis} ({p.entry})" for p in plan.frozen.prior)
            )
        )
    st.subheader(_("Amendements"))
    if plan.amendments:
        for amendment in plan.amendments:
            st.markdown("- " + article.amendment_line(project, amendment))
    else:
        st.caption(_("Aucun amendement."))
    if st.session_state.get(CLEARING):
        st.warning(
            _(
                "Retirer le plan entier efface ses hypothèses, son gel et ses amendements ; les "
                "analyses du carnet restent."
            )
        )
        yes, no, _space = st.columns([1, 1, 3])
        yes.button(
            _("Confirmer le retrait"),
            key="plan-clear-confirm",
            on_click=_act,
            args=(lambda p: _clear(p),),
            kwargs={"key": "plan-clear", "done": _("Plan retiré.")},
        )
        no.button(
            _("Annuler"),
            key="plan-clear-cancel",
            on_click=lambda: st.session_state.pop(CLEARING, None),
        )
    else:
        st.button(
            _("Retirer le plan entier"),
            key="plan-clear",
            icon=":material/delete_forever:",
            on_click=lambda: st.session_state.update({CLEARING: True}),
        )
    c.show_message("plan-clear")


def _write_prereg(project: Project) -> None:
    try:
        written = prereg.write_preregistration(project, c.project_path(), language=i18n.language())
    except OSError as error:
        st.session_state.message = (
            "error",
            _("Impossible d'écrire les fichiers : {detail}.").format(detail=error),
            "plan-prereg",
        )
        return
    st.session_state.message = (
        "success",
        _("Fichiers écrits à côté du projet : {names}.").format(
            names=", ".join(p.name for p in written)
        ),
        "plan-prereg",
    )


def _prereg(project: Project) -> None:
    st.subheader(_("Préenregistrement"))
    template = (
        _("van den Akker et al. (2021), pour des données secondaires")
        if project.plan.data_origin == "secondary"
        else _("OSF Prereg, pour des données primaires")
    )
    st.caption(
        _(
            "Écrit à partir du plan et du codebook seulement, jamais de la base : aucun effectif "
            "ni résultat. Gabarit : {template}. Ce que l'outil ne peut pas savoir reste un trou, "
            "surligné, à compléter dans Word."
        ).format(template=template)
    )
    st.button(
        _("Écrire le préenregistrement à côté du projet"),
        key="plan-prereg",
        icon=":material/description:",
        disabled=not project.plan.hypotheses,
        on_click=_write_prereg,
        args=(project,),
    )
    c.show_message("plan-prereg")


def page(project: Project) -> None:
    st.header(_("Plan"))
    st.caption(
        _(
            "Les hypothèses de l'étude, écrites par l'équipe avant l'analyse, chacune liée à "
            "une analyse du catalogue et à l'effet qui y répond ; les règles générales ; le gel "
            "du plan et ses amendements ; le préenregistrement. Rien n'est envoyé hors de votre "
            "ordinateur."
        )
    )
    prepared = analyses_view.prepared_data(project, "plan")
    if project.plan.frozen is not None:
        st.text_input(
            _("Raison des modifications (le plan est figé : chaque modification est un "
              "amendement)"),
            key=REASON,
        )  # fmt: skip
    waiting = st.session_state.pop("plan-waiting", None)
    for line in waiting or []:
        st.info(line)
    _rules(project)
    st.subheader(_("Hypothèses"))
    deviations = {}
    if project.plan.frozen is not None and prepared is not None:
        notebook = nb.open_notebook(project, c.project_path())
        from ddict.analysis import notebook_check as check

        statuses = check.check_all(notebook, project, prepared, today=_today())
        deviations = {d.hypothesis: d.text for d in pn.deviations(notebook, project, statuses)}
    if not project.plan.hypotheses:
        st.caption(_("Aucune hypothèse pour l'instant."))
    for rank, hypothesis in enumerate(project.plan.hypotheses, start=1):
        _hypothesis(project, rank, hypothesis, prepared, deviations)
    c.show_message("plan-hypotheses")
    _form(project, prepared)
    _frozen(project, prepared)
    _prereg(project)
