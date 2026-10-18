"""The analysis notebook (v0.11, step 6, D-087 to D-092): the analyses a person added from
the Analyses page, in their order, each with its state since its last confirmed
computation; to reorder, retain or leave out, see what changed and confirm, remove, number,
and write the results document next to the project, as `ddict carnet` and `ddict resultats`
do.

The notebook is read from its file at each display and written at once after each change,
as the project. Recomputing it is kept for the session while neither the decisions nor the
notebook change.
"""

from __future__ import annotations

import hashlib
from datetime import date

import streamlit as st

from ddict import i18n
from ddict.analysis import notebook as nb
from ddict.analysis import notebook_check as check
from ddict.analysis import plan_notebook as pn
from ddict.analysis.catalogue import ROLES
from ddict.analysis.notebook_export import ExportBlocked, heading, write_results
from ddict.i18n import _
from ddict.project import fingerprint
from ddict.project.model import Project
from ddict.review.ui import analyses_view
from ddict.review.ui import common as c

STATUSES = "notebook-statuses"  # (signature, [Status]): the last recomputation
ICONS = {
    "current": ":material/check_circle:",
    "unchanged": ":material/check_circle:",
    "changed": ":material/change_circle:",
    "impossible": ":material/error:",
    "no_database": ":material/help:",
}


def _path():
    return nb.notebook_path(c.project_path())


def _open(project: Project) -> nb.Notebook | None:
    try:
        return nb.open_notebook(project, c.project_path())
    except nb.NotebookError as error:
        st.error(nb.reason_text(error))
        return None


def _save(notebook: nb.Notebook) -> None:
    nb.save_notebook(notebook, _path())


def _change(action, *args) -> None:
    """A change asked by a button: read the notebook, change it, write it at once."""
    project = c.project()
    try:
        notebook = nb.open_notebook(project, c.project_path())
        action(notebook, *args)
    except nb.NotebookError as error:
        st.session_state.message = ("error", nb.reason_text(error), "notebook-top")
        return
    _save(notebook)


def _retain(notebook: nb.Notebook, entry_id: str) -> None:
    nb.retain(notebook, entry_id, st.session_state[f"notebook-retain-{entry_id}"])


def _numbers(notebook: nb.Notebook) -> None:
    notebook.first_table = int(st.session_state["notebook-first-table"])
    notebook.first_figure = int(st.session_state["notebook-first-figure"])


def _signature(project: Project, notebook: nb.Notebook, prepared) -> tuple:
    text = hashlib.sha256(nb.dumps(notebook).encode("utf-8")).hexdigest()
    return (text, fingerprint.fingerprint(project), prepared is None, i18n.language())


def _statuses(project: Project, notebook: nb.Notebook, prepared) -> list[check.Status]:
    """Each entry's state; the notebook is written when the recomputation changed it (a new
    fingerprint, a change waiting)."""
    stored = st.session_state.get(STATUSES)
    if stored is not None and stored[0] == _signature(project, notebook, prepared):
        return stored[1]
    before = nb.dumps(notebook)
    reason = _("La base n'a pas été trouvée.") if prepared is None else ""
    with st.spinner(_("Recalcul du carnet…")):
        statuses = check.check_everything(
            notebook, project, prepared, today=date.today().isoformat(), reason=reason
        )
    if nb.dumps(notebook) != before:
        _save(notebook)
    st.session_state[STATUSES] = (_signature(project, notebook, prepared), statuses)
    return statuses


def _write(project: Project) -> None:
    prepared = st.session_state[analyses_view.PREPARED][1]
    try:
        notebook = nb.open_notebook(project, c.project_path())
        written = write_results(
            project, prepared, notebook, c.project_path(), language=i18n.language()
        )
    except ExportBlocked as error:
        st.session_state.message = (
            "error",
            _(
                "À confirmer avant de produire le document : {ids}. Voyez ce qui a changé "
                "plus haut."
            ).format(ids=check.waiting_text(error.ids)),
            "notebook-write",
        )
        return
    except (OSError, nb.NotebookError) as error:
        st.session_state.message = (
            "error",
            _("Impossible d'écrire les fichiers : {detail}.").format(detail=error),
            "notebook-write",
        )
        return
    _save(notebook)
    st.session_state.message = (
        "success",
        _("Fichiers écrits à côté du projet : {names}.").format(
            names=", ".join(p.name for p in written)
        ),
        "notebook-write",
    )


def _deposit(project: Project) -> None:
    """The reproduction package next to the project (v0.15, D-119)."""
    from ddict.analysis import deposit

    prepared = st.session_state[analyses_view.PREPARED][1]
    try:
        notebook = nb.open_notebook(project, c.project_path())
        target, files = deposit.write_deposit(project, prepared, notebook, c.project_path(),
                                              language=i18n.language())  # fmt: skip
    except ExportBlocked as error:
        text = _("À confirmer avant de préparer le paquet : {ids}.").format(
            ids=check.waiting_text(error.ids)
        )
        st.session_state.message = ("error", text, "notebook-deposit")
        return
    except (OSError, nb.NotebookError, deposit.DepositError) as error:
        st.session_state.message = (
            "error",
            _("Impossible d'écrire les fichiers : {detail}.").format(detail=error),
            "notebook-deposit",
        )
        return
    st.session_state.message = (
        "success",
        _("Paquet écrit à côté du projet : {name} ({files}). La base n'y est pas.").format(
            name=target.name, files=", ".join(files)
        ),
        "notebook-deposit",
    )


def _variables(project: Project, entry: nb.Entry) -> str:
    try:
        names = nb.resolved(project, entry)
        parts = [f"{ROLES[role]} : {', '.join(n)}" for role, n in names.items()]
        if entry.subgroup is not None:  # v0.14 (D-113)
            from ddict.analysis.prereg import subgroup_plain

            parts.append(_("Sous-groupe : {condition}").format(
                condition=subgroup_plain(project, entry.subgroup)))  # fmt: skip
    except nb.NotebookError:
        return ""
    return " ; ".join(parts)


def _entry(project: Project, notebook: nb.Notebook, rank: int, entry, status) -> None:
    count = len(notebook.entries)
    with st.container(border=True):
        title, state = st.columns([3, 1])
        title.markdown(f"**{rank}. {heading(entry)}**")
        state.markdown(f"{ICONS[status.state]} {check.state_text(status.state)}")
        if variables := _variables(project, entry):
            st.caption(variables)
        if planned := pn.state_text(pn.state(notebook, project, entry), entry):
            st.caption(_("Face au plan : {state}").format(state=planned))
        if status.state == "impossible":
            st.warning(status.reason)
        elif status.reason:
            st.caption(status.reason)
        if entry.computed.sentence:
            st.markdown(f"> {entry.computed.sentence}")
        if status.state == "changed":
            _changes(status)
            if entry.pending is not None and entry.pending.sentence:
                st.markdown(_("Nouveau calcul :") + f"\n> {entry.pending.sentence}")
            st.button(
                _("Confirmer le nouveau calcul"),
                key=f"notebook-confirm-{entry.id}",
                type="primary",
                on_click=_change,
                args=(check.confirm, entry.id),
            )
        if entry.edits:
            st.caption(_("Titres ou notes changés : {n}").format(n=len(entry.edits)))
        kept, up, down, remove = st.columns([3, 1, 1, 1])
        kept.toggle(
            _("Retenue pour le document"),
            value=entry.retained,
            key=f"notebook-retain-{entry.id}",
            on_change=_change,
            args=(_retain, entry.id),
        )
        up.button(
            _("Monter"),
            key=f"notebook-up-{entry.id}",
            icon=":material/arrow_upward:",
            disabled=rank == 1,
            on_click=_change,
            args=(nb.move, entry.id, rank - 1),
        )
        down.button(
            _("Descendre"),
            key=f"notebook-down-{entry.id}",
            icon=":material/arrow_downward:",
            disabled=rank == count,
            on_click=_change,
            args=(nb.move, entry.id, rank + 1),
        )
        with remove.popover(_("Retirer"), icon=":material/delete:"):
            st.caption(
                _("{id} quitte le carnet ; son numéro ne reviendra pas.").format(id=entry.id)
            )
            st.button(
                _("Retirer {id}").format(id=entry.id),
                key=f"notebook-remove-{entry.id}",
                on_click=_change,
                args=(nb.remove, entry.id),
            )


def _confirm_all(notebook: nb.Notebook, ids: list[str]) -> None:
    for entry_id in ids:
        check.confirm(notebook, entry_id)


def _changes(status) -> None:
    st.markdown(_("**Ce qui a changé depuis le dernier calcul confirmé :**"))
    st.markdown("\n".join(f"- {check.difference_text(d)}" for d in status.differences))


def _method(status) -> None:
    """The Method's figures (v0.12, D-100), confirmed as an analysis's."""
    with st.container(border=True):
        title, state = st.columns([3, 1])
        title.markdown(f"**{nb.METHOD}. {_('Méthode')}**")
        state.markdown(f"{ICONS[status.state]} {check.state_text(status.state)}")
        st.caption(
            _(
                "Les chiffres de la Méthode : les exclusions, la description de l'échantillon "
                "et la fidélité des scores. Ils se règlent sur la page Méthode."
            )
        )
        if status.reason:
            st.caption(status.reason)
        if status.state == "changed":
            _changes(status)
            st.button(
                _("Confirmer les nouveaux chiffres"),
                key="notebook-confirm-M",
                type="primary",
                on_click=_change,
                args=(check.confirm, nb.METHOD),
            )


def page(project: Project) -> None:
    st.header(_("Carnet"))
    st.caption(
        _(
            "Les analyses ajoutées depuis la page Analyses ou par le gel du plan, dans "
            "l'ordre de l'ébauche d'article. Chacune est recalculée quand une décision change : "
            "ce qui a changé attend votre confirmation. Le carnet est un fichier à côté du "
            "projet ; il ne garde que des agrégats, jamais une ligne de la base."
        )
    )
    top = st.empty()
    notebook = _open(project)
    if notebook is None:
        return
    if not notebook.entries:
        st.info(
            _(
                "Le carnet est vide. Lancez une analyse sur la page Analyses, puis cliquez sur "
                "« Ajouter au carnet »."
            )
        )
        return
    prepared = analyses_view.prepared_data(project, "notebook")
    statuses = _statuses(project, notebook, prepared)
    if not nb.belongs(notebook, project):
        top.warning(_("Ce carnet a été fait avec une autre base que celle du projet."))
    changed = [s.entry_id for s in statuses if s.state == "changed"]
    if changed:
        st.warning(
            _(
                "Une décision a changé des chiffres : {ids}. Voyez ce qui a changé ci-dessous, "
                "puis confirmez un à un ou tout à la fois."
            ).format(ids=check.waiting_text(changed))
        )
        st.button(
            _("Tout confirmer"),
            key="notebook-confirm-all",
            icon=":material/done_all:",
            on_click=_change,
            args=(_confirm_all, changed),
        )
    c.show_message("notebook-top")
    by_id = {s.entry_id: s for s in statuses}
    for rank, entry in enumerate(notebook.entries, start=1):
        _entry(project, notebook, rank, entry, by_id[entry.id])
    if nb.METHOD in by_id:
        _method(by_id[nb.METHOD])
    st.subheader(_("Ébauche d'article"))
    st.caption(
        _(
            "L'Introduction avec les hypothèses du plan, la Méthode, les analyses retenues, "
            "recalculées sur la base avec les décisions en vigueur et numérotées à la suite, la "
            "Discussion et les Références, avec des trous surlignés : un document Word, ses "
            "graphiques Excel et le script R maître, à côté du projet. Ces résultats viennent "
            "des données de l'étude : rangez-les avec soin."
        )
    )
    table, figure = st.columns(2)
    table.number_input(
        _("Premier tableau"),
        min_value=1,
        step=1,
        value=notebook.first_table,
        key="notebook-first-table",
        on_change=_change,
        args=(_numbers,),
    )
    figure.number_input(
        _("Première figure"),
        min_value=1,
        step=1,
        value=notebook.first_figure,
        key="notebook-first-figure",
        on_change=_change,
        args=(_numbers,),
    )
    blocked = check.blocking(notebook, statuses)
    if blocked:
        st.warning(
            _("À confirmer avant de produire le document : {ids}.").format(
                ids=check.waiting_text(blocked)
            )
        )
    retained = any(e.retained for e in notebook.entries)
    st.button(
        _("Produire l'ébauche d'article"),
        key="notebook-write",
        type="primary",
        disabled=prepared is None or bool(blocked) or not retained,
        on_click=_write,
        args=(project,),
    )
    c.show_message("notebook-write")
    st.button(
        _("Préparer le paquet de reproduction"),
        key="notebook-deposit",
        help=_(
            "Un .zip pour un dépôt (OSF, Borealis) : codebook, plan, carnet, scripts et un "
            "README à compléter ; jamais la base."
        ),
        disabled=prepared is None or bool(blocked) or not retained,
        on_click=_deposit,
        args=(project,),
    )
    c.show_message("notebook-deposit")
