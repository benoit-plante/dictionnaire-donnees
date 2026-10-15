"""The "Names" page (v0.7): new names for the variables, decided by a person.

The rules propose (platform variables, the prefix of a group, the base name of a question),
an earlier wave may give its names; a person decides in the table itself (v0.7.1, D-056):
writes a name, or chooses "Accept" or "Reject" on a row. The
original name stays the key; the original file is never changed. The logic is in
`review.names`.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from ddict.i18n import N_, Texts, _
from ddict.project import save_project
from ddict.project.model import Project
from ddict.review import names
from ddict.review.logic import ReviewError
from ddict.review.ui import common as c
from ddict.review.ui import dialog
from ddict.workflow import naming_summary, wave_summary, write_wave_report

FILTER = "names-filter"
WAVE = "names-wave"
POSITION = "names-position"
LENGTH = "names-max-length"
REFERENCE = "names-reference"
TABLE = "names-table"
STEMS = "names-stems"
PREFILL = "names-prefill-filter"  # the filter whose proposed rows show "Accept" already
POSITIONS = Texts({"suffix": N_("À la fin (k6_1_t2)"), "prefix": N_("Au début (t2_k6_1)")})


def _browse() -> None:
    path = dialog.choose("reference")
    if path:
        st.session_state[REFERENCE] = path
    else:
        st.session_state.message = (
            "error",
            _("Aucun fichier choisi. Vous pouvez aussi coller son chemin dans le champ."),
            "names-reference-browse",
        )


def _take_earlier_wave() -> None:
    key = "names-reference-take"
    text = str(st.session_state.get(REFERENCE) or "").strip().strip('"')
    if not text or not Path(text).is_file():
        st.session_state.message = (
            "error",
            _("Choisissez d'abord le fichier de la vague précédente."),
            key,
        )
        return
    project = c.project()
    try:
        report = names.take_earlier_wave(project, Path(text))
    except ReviewError as error:
        st.session_state.message = ("error", str(error), key)
        return
    save_project(project, c.project_path())
    path = write_wave_report(project, report, c.project_path())
    lines = [*wave_summary(report), _("Rapport des écarts : {name}").format(name=path.name)]
    st.session_state.message = ("success", " ".join(lines), key)


def _edited(key: str, rows: list, column: str) -> dict[str, str]:
    """The cells a person changed in a table: first column -> new text."""
    changes = st.session_state.get(key, {}).get("edited_rows", {})
    return {
        rows[int(index)][0]: cells[column] for index, cells in changes.items() if column in cells
    }


def _final(key: str, names_: list[str], shown: list[str], column: str) -> dict[str, str]:
    """A column as the person leaves it: what was shown, with the cells they changed."""
    values = dict(zip(names_, shown, strict=True))
    for index, cells in st.session_state.get(key, {}).get("edited_rows", {}).items():
        if column in cells:
            values[names_[int(index)]] = cells[column] or ""
    return values


def _save_table(rows: list[names.NameRow], shown: list[str], table_key: str) -> None:
    key = "names-table-save"
    labels = {names.DECISIONS[code]: code for code in names.DECISIONS}
    listed = [r.name for r in rows]
    chosen = _final(table_key, listed, shown, "decision")
    decisions = {name: labels[text] for name, text in chosen.items() if text in labels}
    edits = _edited(table_key, [(r.name,) for r in rows], "new_name")
    try:
        n = names.apply_table(c.project(), edits, decisions, now=c.now())
    except ReviewError as error:
        st.session_state.message = ("error", str(error), key)
        return
    save_project(c.project(), c.project_path())
    st.session_state.pop(table_key, None)
    st.session_state.pop(PREFILL, None)
    st.session_state.message = ("success", _("{n} noms enregistrés.").format(n=n), key)


def _prefill(which: str, table_key: str) -> None:
    st.session_state[PREFILL] = which
    st.session_state.pop(table_key, None)  # the table starts again from the filled column


def _save_stems(rows: list[tuple]) -> None:
    key = "names-stems-save"
    try:
        n = names.apply_stems(c.project(), _edited(STEMS, rows, "stem"), now=c.now())
    except ReviewError as error:
        st.session_state.message = ("error", str(error), key)
        return
    save_project(c.project(), c.project_path())
    st.session_state.pop(STEMS, None)
    st.session_state.message = ("success", _("{n} noms de base enregistrés.").format(n=n), key)


def _settings(project: Project) -> None:
    started = any(e.new_name.value for e in project.variables)
    with (
        st.expander(_("Réglages de nommage"), expanded=not started),
        st.form("form-names-settings", border=False),
    ):
        st.text_input(
            _("Marque de vague (vide s'il n'y en a pas)"),
            key=c.field(WAVE, lambda: c.project().settings.naming.wave or ""),
            placeholder="t2",
        )
        st.radio(
            _("Place de la marque"),
            list(POSITIONS),
            key=c.field(POSITION, lambda: c.project().settings.naming.position),
            format_func=POSITIONS.__getitem__,
            horizontal=True,
        )
        st.number_input(
            _("Longueur maximale des noms"),
            min_value=8,
            max_value=64,
            key=c.field(LENGTH, lambda: c.project().settings.naming.max_length),
            help=_("32, la limite de Stata, convient à SPSS, R et Stata."),
        )
        c.button(
            _("Enregistrer et proposer les noms"),
            "names-settings-save",
            names.set_settings,
            c.state(WAVE),
            c.state(POSITION),
            c.state(LENGTH),
            submit=True,
        )


def _earlier_wave() -> None:
    with st.expander(_("Reprendre les noms d'une vague précédente")):
        st.caption(
            _(
                "Son fichier projet (.dd.json, le plus complet), sa copie documentée (.sav) ou "
                "sa table de noms (.csv : nom_origine,nouveau_nom). Chaque variable est "
                "appariée par ses étiquettes, ses étiquettes de valeurs et sa question ; les "
                "noms repris sont des propositions. Un rapport des écarts entre les vagues est "
                "écrit à côté du projet."
            )
        )
        st.text_input(_("Fichier de la vague précédente"), key=REFERENCE)
        left, right = st.columns(2)
        left.button(_("Choisir…"), key="names-reference-browse", on_click=_browse)
        right.button(
            _("Reprendre les noms"),
            key="names-reference-take",
            type="primary",
            on_click=_take_earlier_wave,
        )
        c.show_message("names-reference-browse")
        c.show_message("names-reference-take")


def _table(project: Project) -> None:
    which = st.radio(
        _("Filtre"), list(names.FILTERS), key=FILTER, format_func=names.FILTERS.__getitem__,
        horizontal=True,
    )  # fmt: skip
    rows = names.rows(project, which)
    if not rows:
        st.info(_("Aucune variable dans ce filtre."))
        return
    st.caption(
        _(
            "Décidez dans le tableau : choisissez « Accepter » ou « Rejeter » dans la colonne "
            "« Décision », ou écrivez un autre nom dans « Nouveau nom » (il est alors décidé, "
            "et vérifié). Puis « Enregistrer ». Effacer un nom rend son nom d'origine à la "
            "variable."
        )
    )
    # One table per filter: changes typed under one filter never land on another's rows.
    table_key = f"{TABLE}-{which}"
    accept = names.DECISIONS["accept"]
    shown = [accept if st.session_state.get(PREFILL) == which and r.waiting else "" for r in rows]
    frame = pd.DataFrame(
        [
            (r.name, r.label, r.question, r.new_name, d, r.origin, r.status, r.problem)
            for r, d in zip(rows, shown, strict=True)
        ],
        columns=[
            "name",
            "label",
            "question",
            "new_name",
            "decision",
            "origin",
            "status",
            "problem",
        ],
    )
    st.data_editor(
        frame,
        key=table_key,
        hide_index=True,
        use_container_width=True,
        disabled=["name", "label", "question", "origin", "status", "problem"],
        column_config={
            "name": _("Nom d'origine"),
            "label": _("Étiquette"),
            "question": _("Question"),
            "new_name": _("Nouveau nom"),
            "decision": st.column_config.SelectboxColumn(
                _("Décision"), options=["", *(names.DECISIONS[k] for k in names.DECISIONS)]
            ),
            "origin": _("Origine"),
            "status": _("Statut"),
            "problem": _("Problème"),
        },
    )
    waiting = sum(r.waiting for r in rows)
    left, right = st.columns(2)
    left.button(
        _("Enregistrer"),
        key="names-table-save",
        type="primary",
        on_click=_save_table,
        args=(rows, shown, table_key),
    )
    if waiting:
        right.button(
            _("Choisir « Accepter » pour les {n} noms proposés").format(n=waiting),
            key="names-prefill",
            on_click=_prefill,
            args=(which, table_key),
            help=_(
                "Remplit la colonne « Décision » ; rien n'est enregistré avant que vous ayez "
                "relu le tableau et cliqué « Enregistrer »."
            ),
        )
    c.show_message("names-table-save")


def _stems(project: Project) -> None:
    rows = names.stem_rows(project)
    if not rows:
        return
    with st.expander(_("Noms de base des questions ({n})").format(n=len(rows))):
        st.caption(
            _(
                "Un nom de base par question, partagé par ses variables : « taches » donne "
                "taches_1, taches_2… et taches_autre_txt. Corrigez-le ici, une seule fois."
            )
        )
        frame = pd.DataFrame(rows, columns=["key", "text", "stem", "status"])
        st.data_editor(
            frame,
            key=STEMS,
            hide_index=True,
            use_container_width=True,
            disabled=["key", "text", "status"],
            column_config={
                "key": _("Question"),
                "text": _("Texte"),
                "stem": _("Nom de base"),
                "status": _("Statut"),
            },
        )
        st.button(
            _("Enregistrer les noms de base"),
            key="names-stems-save",
            on_click=_save_stems,
            args=(rows,),
        )
        c.show_message("names-stems-save")


def page(project: Project) -> None:
    st.header(_("Noms des variables"))
    st.caption(
        _(
            "De nouveaux noms, proposés par des règles ou repris d'une vague précédente, "
            "décidés par vous. Le nom d'origine reste celui du fichier, qui n'est jamais "
            "modifié ; les noms acceptés s'appliquent dans le codebook, les fichiers de "
            "commandes et la copie documentée. Le préfixe d'une grille se donne dans la vue "
            "« Groupes »."
        )
    )
    for line in naming_summary(project):
        st.write(line)
    _settings(project)
    _earlier_wave()
    c.button(_("Proposer les noms par les règles"), "names-propose", names.propose)
    _table(project)
    _stems(project)
