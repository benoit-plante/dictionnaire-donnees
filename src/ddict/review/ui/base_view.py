"""The database: what was read and computed, as `ddict profiler` says it (v0.3)."""

from __future__ import annotations

from collections import Counter

import pandas as pd
import streamlit as st

from ddict import i18n
from ddict.export import wording as w
from ddict.i18n import _, field_label, quoted
from ddict.project import save_project
from ddict.project.model import Project
from ddict.review import levels, logic, study
from ddict.review.logic import ReviewError
from ddict.review.ui import common as c
from ddict.workflow import format_note, platform_notes, profile_summary

FORMATS = {
    "sav": "SPSS",
    "csv": "CSV",
    "dta": "Stata",
    "sas7bdat": "SAS",
    "xlsx": "Excel",
}


STUDY_LANGUAGE = "study-language"
DESIGN_KEYS = ("cluster_id", "time", "wave", "cluster", "weight")
LEVEL_FILTER = "levels-filter"
LEVEL_TABLE = "levels-table"
LEVEL_PREFILL = "levels-prefill-filter"  # the filter whose proposals show "Accept" already


def _study_language(project: Project) -> None:
    """The language of the study (v0.5, D-032), guessed from its questionnaire or labels."""
    st.session_state[STUDY_LANGUAGE] = project.settings.language
    st.selectbox(
        _("Langue de l'étude"),
        list(i18n.LANGUAGES),
        placeholder=_("Choisir…"),
        key=STUDY_LANGUAGE,
        format_func=i18n.LANGUAGES.__getitem__,
        on_change=c.act,
        args=(logic.set_project_language, c.state(STUDY_LANGUAGE)),
        kwargs={"key": STUDY_LANGUAGE, "timed": False, "reset": ()},
        help=_(
            "La langue du questionnaire et des libellés : le modèle écrit ses propositions dans "
            "cette langue. Devinée d'après le questionnaire ou les étiquettes du fichier."
        ),
    )
    c.show_message(STUDY_LANGUAGE)


def _dataset(project: Project) -> None:
    """What a row is and how the study is organised (v0.8, D-064): written by the team; only
    the structure may be proposed, from the wave mark or the time suffixes."""
    st.subheader(_("Description de la base"))
    tracked = project.dataset.structure
    if tracked.status == "proposed":
        text = w.STRUCTURES[tracked.value]
        detail = project.dataset.wave or ", ".join(project.dataset.time_suffixes)
        st.info(
            _("Structure proposée : {structure}").format(structure=text)
            + (f" ({detail})" if detail else "")
        )
        left, right = st.columns(2)
        with left:
            c.button(_("Accepter"), "dataset-accept", study.decide_structure, "accept",
                     timed=True, primary=True)  # fmt: skip
        with right:
            c.button(_("Rejeter"), "dataset-reject", study.decide_structure, "reject", timed=True)

    def now_(part: str):
        found = c.project().dataset
        if part == "structure":
            return found.structure.value if found.structure.status != "proposed" else ""
        if part == "suffixes":
            return ", ".join(found.time_suffixes)
        if part.startswith("design_"):
            return getattr(found.design, part.removeprefix("design_")) or ""
        return getattr(found, part) or ""

    keys = {part: f"dataset-{part}" for part in
            ("unit_of_observation", "unit_other", "structure", "wave", "suffixes",
             "description", *(f"design_{k}" for k in DESIGN_KEYS))}  # fmt: skip
    names = [e.name for e in project.variables]
    shown = {e.name: w.final_name(e) for e in project.variables}
    with st.form("form-dataset", border=False):
        left, right = st.columns(2)
        left.selectbox(
            _("Une ligne représente"),
            ["", *w.UNITS],
            placeholder=_("Choisir…"),
            format_func=lambda u: w.UNITS[u] if u else _("(non précisé)"),
            key=c.field(keys["unit_of_observation"], lambda: now_("unit_of_observation")),
        )
        right.text_input(
            _("Autre : laquelle ?"), key=c.field(keys["unit_other"], lambda: now_("unit_other"))
        )
        st.selectbox(
            _("Structure"),
            ["", *w.STRUCTURES],
            placeholder=_("Choisir…"),
            format_func=lambda s: w.STRUCTURES[s] if s else _("(non précisée)"),
            key=c.field(keys["structure"], lambda: now_("structure")),
        )
        left, right = st.columns(2)
        left.text_input(
            _("Vague de ce fichier (une vague par fichier)"),
            key=c.field(keys["wave"], lambda: now_("wave")),
        )
        right.text_input(
            _("Suffixes de temps (format large), séparés par des virgules"),
            key=c.field(keys["suffixes"], lambda: now_("suffixes")),
            placeholder="_t1, _t2",
        )
        columns = st.columns(len(DESIGN_KEYS))
        for column, part in zip(columns, DESIGN_KEYS, strict=True):
            column.selectbox(
                w.DESIGN[part].capitalize(),
                ["", *names],
                placeholder=_("Choisir…"),
                format_func=lambda n: shown.get(n, "—") if n else "—",
                key=c.field(keys[f"design_{part}"], lambda part=part: now_(f"design_{part}")),
            )
        st.text_area(
            _("Description (courte)"),
            key=c.field(keys["description"], lambda: now_("description")),
            height=68,
        )
        c.button(
            _("Enregistrer la description"),
            "dataset-save",
            study.set_dataset,
            c.state(keys["unit_of_observation"]),
            c.state(keys["unit_other"]),
            c.state(keys["structure"]),
            c.state(keys["wave"]),
            c.state(keys["suffixes"]),
            lambda: {part: st.session_state[keys[f"design_{part}"]] for part in DESIGN_KEYS},
            c.state(keys["description"]),
            timed=True,
            reset=tuple(keys.values()),
            submit=True,
        )


def _final(key: str, names: list[str], shown: list[str], column: str) -> dict[str, str]:
    """A column as the person leaves it: what was shown, with the cells they changed."""
    values = dict(zip(names, shown, strict=True))
    for index, cells in st.session_state.get(key, {}).get("edited_rows", {}).items():
        if column in cells:
            values[names[int(index)]] = cells[column] or ""
    return values


def _save_levels(rows: list[levels.LevelRow], levels_shown: list[str], decisions_shown: list[str],
                 table_key: str) -> None:  # fmt: skip
    key = "levels-save"
    names = [r.name for r in rows]
    by_text = {w.MEASURES[code]: code for code in w.MEASURES}
    by_decision = {levels.DECISIONS[code]: code for code in levels.DECISIONS}
    chosen = _final(table_key, names, levels_shown, "level")
    original = dict(zip(names, levels_shown, strict=True))
    new_levels = {
        n: by_text[text] for n, text in chosen.items() if text in by_text and text != original[n]
    }
    decisions = {
        n: by_decision[text]
        for n, text in _final(table_key, names, decisions_shown, "decision").items()
        if text in by_decision
    }
    try:
        n = levels.apply_table(c.project(), new_levels, decisions, now=c.now())
    except ReviewError as error:
        st.session_state.message = ("error", str(error), key)
        return
    save_project(c.project(), c.project_path())
    st.session_state.pop(table_key, None)
    st.session_state.pop(LEVEL_PREFILL, None)
    st.session_state.message = ("success", _("{n} niveaux enregistrés.").format(n=n), key)


def _prefill_levels(which: str, table_key: str) -> None:
    st.session_state[LEVEL_PREFILL] = which
    st.session_state.pop(table_key, None)


def _levels(project: Project) -> None:
    """The measure levels (v0.8, D-063): proposed by rules, decided in the table."""
    st.subheader(_("Niveaux de mesure"))
    st.write(
        _(
            "Proposés par des règles quand le fichier n'en donne pas, ou quand celui du fichier "
            "est douteux. Choisissez « Accepter » ou « Rejeter » dans la colonne « Décision », "
            "ou un autre niveau dans « Niveau » (il est alors décidé), puis « Enregistrer »."
        )
    )
    which = st.radio(
        _("Afficher"), list(levels.FILTERS), key=LEVEL_FILTER,
        format_func=levels.FILTERS.__getitem__, horizontal=True,
    )  # fmt: skip
    rows = levels.rows(project, which)
    if not rows:
        st.info(_("Aucun niveau de mesure proposé."))
        return
    table_key = f"{LEVEL_TABLE}-{which}"
    accept = levels.DECISIONS["accept"]
    prefilled = st.session_state.get(LEVEL_PREFILL) == which
    levels_shown = [w.MEASURES[r.level] if r.level else c.DASH for r in rows]
    decisions_shown = [accept if prefilled and r.waiting else c.DASH for r in rows]
    frame = pd.DataFrame(
        [
            (r.name, c.dash(r.label), c.dash(r.kind), c.dash(r.file_level), lv, d, c.dash(r.status))
            for r, lv, d in zip(rows, levels_shown, decisions_shown, strict=True)
        ],
        columns=["name", "label", "kind", "file_level", "level", "decision", "status"],
    )
    st.data_editor(
        frame,
        key=table_key,
        hide_index=True,
        width="stretch",
        disabled=["name", "label", "kind", "file_level", "status"],
        column_config={
            "name": st.column_config.TextColumn(_("Variable"), width="medium"),
            "label": st.column_config.TextColumn(_("Libellé"), width="large"),
            "kind": st.column_config.TextColumn(_("Type"), width="small"),
            "file_level": st.column_config.TextColumn(_("Dans le fichier"), width="small"),
            "level": st.column_config.SelectboxColumn(
                _("Niveau"),
                options=[c.DASH, *(w.MEASURES[k] for k in w.MEASURES)],
                width="small",
            ),
            "decision": st.column_config.SelectboxColumn(
                _("Décision"),
                options=[c.DASH, *(levels.DECISIONS[k] for k in levels.DECISIONS)],
                width="small",
            ),
            "status": st.column_config.TextColumn(_("Statut"), width="medium"),
        },
    )
    left, right = st.columns(2)
    left.button(
        _("Enregistrer"),
        key="levels-save",
        type="primary",
        on_click=_save_levels,
        args=(rows, levels_shown, decisions_shown, table_key),
    )
    waiting = sum(r.waiting for r in rows)
    if waiting:
        right.button(
            _("Choisir « Accepter » pour les {n} niveaux proposés").format(n=waiting),
            key="levels-prefill",
            on_click=_prefill_levels,
            args=(which, table_key),
            help=_(
                "Remplit la colonne « Décision » ; rien n'est enregistré avant que vous ayez "
                "relu le tableau et cliqué « Enregistrer »."
            ),
        )
    c.show_message("levels-save")


def page(project: Project) -> None:
    source = project.source
    st.header(source.name + (f" — {source.label}" if source.label else ""))
    st.write(profile_summary(project))
    for note in platform_notes(project):
        st.info(note)
    if note := format_note(project):
        st.warning(note)
    _study_language(project)
    _dataset(project)

    sensitive = [e for e in project.variables if logic.is_sensitive(e)]
    flagged = [e for e in project.variables if w.entry_anomalies(e)]
    columns = st.columns(4)
    columns[0].metric(_("Variables"), len(project.variables))
    columns[1].metric(_("Lignes"), source.n_rows)
    columns[2].metric(_("Variables sensibles"), len(sensitive))
    columns[3].metric(_("Avec signalements"), len(flagged))

    facts = [f"{field_label('Format')}{FORMATS.get(source.format, source.format)}"]
    if source.encoding:
        facts.append(f"{field_label('Encodage')}{source.encoding}")
    if source.delimiter:
        facts.append(f"{field_label('Séparateur')}{quoted(source.delimiter)}")
    if source.decimal:
        facts.append(f"{field_label('Marque décimale')}{quoted(source.decimal)}")
    facts.append(_("Groupes de variables repérés : {n}").format(n=len(project.groups)))
    st.markdown("\n".join(f"- {fact}" for fact in facts))
    st.caption(
        _(
            "Le fichier de données n'est jamais modifié ; le projet garde seulement ce que "
            "l'outil a calculé et vos décisions, pas les réponses des participants. "
            "Fichier projet : {path}"
        ).format(path=c.project_path())
    )

    types = Counter(
        w.TYPES.get(e.profile.inferred_type, e.profile.inferred_type) for e in project.variables
    )
    st.subheader(_("Types de variables"))
    st.dataframe(
        pd.DataFrame(sorted(types.items()), columns=[_("Type"), _("Variables")]),
        hide_index=True,
    )
    st.subheader(_("Complétude"))
    st.caption(_("Éléments décidés par l'équipe, sur ceux qui s'appliquent."))
    missing = _("À documenter")
    st.dataframe(
        pd.DataFrame(w.completeness_rows(project), columns=[_("Élément"), _("Décidés"), missing]),
        hide_index=True,
        width="stretch",
        column_config={missing: st.column_config.TextColumn(missing, width="large")},
    )
    _levels(project)
    if sensitive:
        st.subheader(_("Variables sensibles"))
        st.caption(
            _(
                "Seules leurs métadonnées sont utilisées : aucune statistique sur leurs "
                "valeurs, et rien d'elles n'est envoyé au modèle."
            )
        )
        st.dataframe(
            pd.DataFrame(
                [(e.name, w.privacy_text(e)) for e in sensitive],
                columns=[_("Variable"), _("Confidentialité")],
            ),
            hide_index=True,
        )
