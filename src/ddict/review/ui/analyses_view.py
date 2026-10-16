"""Analyses (v0.9, step 6): an analysis of the catalogue chosen, with its variables and
options, its conditions checked before the computation, its result, and its report and R
script, as `ddict analyser` writes them.

The database is read in memory for the session, never written in the project (D-070); only
the last analysis run is kept, in memory too (D-078). The local model may propose analyses
(step 7, `advice_view`): a person takes them up or not.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import streamlit as st

from ddict import i18n
from ddict.analysis import conditions
from ddict.analysis.book import Codebook
from ddict.analysis.catalogue import CATALOGUE, CHOICES, OPTIONS, PURPOSES, ROLES, TITLES
from ddict.analysis.compute import AnalysisRefused, run
from ddict.analysis.data import DataError, PreparedData, apply_decisions, find_database
from ddict.analysis.report import (
    _markdown_table,
    excluded_reason,
    r_bundle,
    render_report,
    report_xlsx,
    write_apa,
)
from ddict.analysis.report import write_report as write_files
from ddict.i18n import _
from ddict.io import read_database
from ddict.project import fingerprint
from ddict.project.model import Project
from ddict.review.ui import advice_view, apa_view, dialog
from ddict.review.ui import common as c
from ddict.review.ui.advice_view import option_key, role_key
from ddict.workflow import analysis_files, copy_error_text, project_stem

ANALYSIS = "analysis-key"
DATABASE = "analysis-database"  # the database chosen by hand, when not next to the project
TABLE = "analysis-table"  # (path, table read from the database)
PREPARED = "analysis-prepared"  # (fingerprint, PreparedData)
RESULT = "analysis-result"  # the last analysis run: (what was asked, AnalysisResult)
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _choose_database() -> None:
    path = dialog.choose("database")
    if path:
        st.session_state[DATABASE] = path


def _prepared(project: Project) -> PreparedData | None:
    """The data with the accepted decisions, read once per session and prepared again when
    a decision changes; None, with the reason shown, when the database is not found."""
    chosen = st.session_state.get(DATABASE)
    try:
        path = find_database(project, c.project_path(), Path(chosen) if chosen else None)
    except DataError as error:
        st.info(copy_error_text(error, project.source.name))
        st.button(_("Choisir la base…"), key="analysis-choose", on_click=_choose_database)
        return None
    read = st.session_state.get(TABLE)
    if read is None or read[0] != str(path):
        with st.spinner(_("Lecture de la base…")):
            read = (str(path), read_database(path).table)
        st.session_state[TABLE] = read
        st.session_state.pop(PREPARED, None)
    print_ = fingerprint.fingerprint(project)
    prepared = st.session_state.get(PREPARED)
    if prepared is None or prepared[0] != print_:
        prepared = (print_, apply_decisions(project, read[1]))
        st.session_state[PREPARED] = prepared
    return prepared[1]


def _choose_variables(project: Project, key: str, book: Codebook) -> dict[str, list[str]]:
    analysis = CATALOGUE[key]
    chosen: dict[str, list[str]] = {}

    def shown(name: str) -> str:
        label = book.label(name)
        return label if label.startswith(name) else f"{name} — {label}"

    for role in analysis.roles:
        names = conditions.candidates(project, analysis, role.key)
        widget = role_key(key, role.key)
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
                format_func=shown,
                placeholder=_("Aucune") if role.least == 0 else _("Choisir une variable"),
            )
            chosen[role.key] = [picked] if picked else []
        else:
            chosen[role.key] = st.multiselect(
                ROLES[role.key],
                names,
                key=widget,
                format_func=shown,
                max_selections=role.most,
                placeholder=_("Choisir de {least} à {most} variables").format(
                    least=role.least, most=role.most
                ),
            )
    return {k: v for k, v in chosen.items() if v}


def _choose_options(
    key: str, chosen: dict[str, list[str]], prepared: PreparedData, book: Codebook
) -> dict[str, str]:
    options = {}
    for option, values in CATALOGUE[key].options.items():
        options[option] = st.radio(
            OPTIONS[option],
            list(values),
            key=option_key(key, option),
            format_func=CHOICES.__getitem__,
            horizontal=True,
        )
    group = (chosen.get("group") or [None])[0]
    if key == "t_test" and group is not None:
        used = [n for names in chosen.values() for n in names]
        codes = sorted(set(prepared.table[used].dropna()[group]))
        if len(codes) > 2:
            picked = st.multiselect(
                OPTIONS["levels"],
                codes,
                key=option_key(key, f"levels-{group}"),
                max_selections=2,
                format_func=lambda code: book.category(group, code),
                placeholder=_("Choisir les deux groupes à comparer"),
            )
            if len(picked) == 2:
                options["levels"] = ",".join(_code_option(code) for code in picked)
    return options


def _code_option(code) -> str:
    """A code as the options carry it: "1", "2.5"."""
    return str(int(code)) if float(code).is_integer() else str(code)


def _asked(project: Project, key: str, chosen, options) -> tuple:
    return (key, repr(sorted(chosen.items())), repr(sorted(options.items())),
            fingerprint.fingerprint(project), i18n.language())  # fmt: skip


def _run(project: Project, key: str, chosen, options) -> None:
    prepared = st.session_state[PREPARED][1]
    try:
        result = run(project, prepared, key, chosen, options)
    except AnalysisRefused:
        return  # shown before the button already
    st.session_state[RESULT] = (_asked(project, key, chosen, options), result)


def _write(project: Project) -> None:
    asked, result = st.session_state[RESULT]
    prepared = st.session_state[PREPARED][1]
    path = c.project_path()
    files = analysis_files(path)
    try:
        written = write_files(
            project, prepared, result, files, project_stem(path), date.today().isoformat()
        )
        # v0.10: the APA tables and figures, with the numbers, titles and notes of the page.
        written += write_apa(files, apa_view.current(project, prepared, result, asked))
    except OSError as error:
        st.session_state.message = (
            "error",
            _("Impossible d'écrire les fichiers : {detail}.").format(detail=error),
            "analysis-write",
        )
        return
    st.session_state.message = (
        "success",
        _("Fichiers écrits à côté du projet : {names}.").format(
            names=", ".join(p.name for p in written)
        ),
        "analysis-write",
    )


def _show(project: Project, prepared: PreparedData, asked: tuple, result) -> None:
    st.subheader(_("Résultat"))
    if result.sentence:
        st.markdown(f"> {result.sentence}")
    st.caption(
        _("{used} observations retenues, {excluded} écartées ({why}).").format(
            used=result.n_used, excluded=result.n_excluded, why=excluded_reason(result)
        )
    )
    for warning in result.warnings:
        st.warning(warning)
    for table in result.tables:
        st.markdown(f"**{table.title}**")
        st.markdown("\n".join(_markdown_table(table.columns, table.rows)))
    st.subheader(_("Rapport et script R"))
    st.caption(
        _(
            "Le rapport donne les variables, les options, les résultats, l'empreinte du codebook "
            "et les versions des bibliothèques. Le script R refait l'analyse hors de l'outil ; "
            "il s'exécute dans le dossier de la base, avec le fichier de commandes et le script "
            "de préparation joints. Ces résultats viennent des données de l'étude : rangez-les "
            "avec soin."
        )
    )
    path = c.project_path()
    files = analysis_files(path)
    today = date.today().isoformat()
    stem = project_stem(path)
    first, second, third, fourth = st.columns(4)
    first.button(
        _("Écrire à côté du projet"), key="analysis-write", on_click=_write, args=(project,)
    )
    second.download_button(
        _("Rapport (Markdown)"),
        data=render_report(project, prepared, result, files, today).encode("utf-8"),
        file_name=files.markdown.name,
        mime="text/markdown",
        key="analysis-download-md",
    )
    third.download_button(
        _("Tableaux (Excel)"),
        data=report_xlsx(project, prepared, result, files, today),
        file_name=files.xlsx.name,
        mime=XLSX_TYPE,
        key="analysis-download-xlsx",
    )
    fourth.download_button(
        _("Script R (.zip)"),
        data=r_bundle(project, files, stem, result, today),
        file_name=files.r.with_suffix(".zip").name,
        mime="application/zip",
        key="analysis-download-r",
    )
    c.show_message("analysis-write")
    apa_view.panel(project, prepared, result, asked, files)


def page(project: Project) -> None:
    st.header(_("Analyses"))
    st.caption(
        _(
            "Des analyses écrites et vérifiées d'avance, calculées dans l'outil sur votre base, "
            "avec les décisions acceptées : codes manquants retirés, nouveaux noms, items "
            "inversés, scores. Votre fichier n'est jamais modifié, et rien n'est envoyé hors de "
            "votre ordinateur."
        )
    )
    prepared = _prepared(project)
    if prepared is None:
        return
    advice_view.panel(project)
    book = Codebook(project, prepared)
    key = st.selectbox(_("Analyse"), list(CATALOGUE), key=ANALYSIS, format_func=TITLES.__getitem__)
    st.caption(PURPOSES[key])
    chosen = _choose_variables(project, key, book)
    options = _choose_options(key, chosen, prepared, book)
    complete = all(len(chosen.get(r.key, [])) >= r.least for r in CATALOGUE[key].roles)
    found = conditions.check(project, key, chosen, options, prepared) if complete else None
    last = st.session_state.get(RESULT)
    current = last is not None and last[0] == _asked(project, key, chosen, options)
    if found is not None and not current:
        for reason in found.refusals:
            st.error(reason)
        for warning in found.warnings:
            st.warning(warning)
    st.button(
        _("Lancer l'analyse"),
        key="analysis-run",
        type="primary",
        disabled=found is None or not found.ok,
        on_click=_run,
        args=(project, key, chosen, options),
    )
    if current:
        _show(project, prepared, last[0], last[1])
    elif last is not None and last[0][0] == key:
        st.caption(_("Les choix ont changé depuis la dernière analyse : relancez-la."))
