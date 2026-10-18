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
from ddict.analysis import notebook as nb
from ddict.analysis.book import Codebook
from ddict.analysis.catalogue import CATALOGUE, OPTIONS, PURPOSES, ROLES, TITLES, choice
from ddict.analysis.compute import AnalysisRefused, run
from ddict.analysis.data import (
    DataError,
    PreparedData,
    apply_decisions,
    apply_subset,
    find_database,
)
from ddict.analysis.formats import FORMATS, available
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


def prepared_data(project: Project, where: str = "analysis") -> PreparedData | None:
    """The data with the accepted decisions, read once per session and prepared again when
    a decision changes; None, with the reason shown, when the database is not found (the
    Analyses and the Notebook pages share it, `where` names the button)."""
    chosen = st.session_state.get(DATABASE)
    try:
        path = find_database(project, c.project_path(), Path(chosen) if chosen else None)
    except DataError as error:
        st.info(copy_error_text(error, project.source.name))
        st.button(_("Choisir la base…"), key=f"{where}-choose", on_click=_choose_database)
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
            c.go_button(_("Décider les niveaux de mesure (page Base)"),
                        f"go-base-{widget}", "base")  # fmt: skip
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
            format_func=lambda value: choice(key, value),
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
    """A code as the options carry it: "1", "2.5"; a text code as it is."""
    if isinstance(code, str):
        return code
    return str(int(code)) if float(code).is_integer() else str(code)


OPERATORS = {"eq": "=", "ne": "≠", "lt": "<", "le": "≤", "gt": ">", "ge": "≥"}
CODES_LISTED = 30  # more distinct values than this: a number is typed instead


def _operator(code: str) -> str:
    return OPERATORS.get(code) or _("parmi")


def subgroup_widgets(project: Project, prepared, book: Codebook, prefix: str):
    """v0.14 (D-113): an optional subgroup, shared by the pages "Analyses" and "Plan": a
    variable, a condition and its values among those observed; None without one."""
    from ddict.analysis.results import Subset

    levels = conditions.levels(project)
    excluded = conditions._sensitive(project)
    texts = conditions.texts(project)
    names = [n for n, lv in levels.items() if lv and n not in excluded
             and n in prepared.table.columns]  # fmt: skip
    with st.expander(_("Sous-groupe (facultatif)"), key=f"{prefix}-open", on_change="rerun"):
        st.caption(
            _(
                "L'analyse ne porte que sur les personnes qui remplissent cette condition, "
                "après les règles d'exclusion ; la phrase, les tableaux, la Méthode et le "
                "script R le disent."
            )
        )
        name = st.selectbox(
            _("Variable"),
            names,
            index=None,
            key=f"{prefix}-variable",
            format_func=lambda n: n if book.label(n) == n else f"{n} — {book.label(n)}",
            placeholder=_("Aucun : toutes les personnes"),
        )
        if name is None:
            return None
        column = prepared.table[name].dropna()
        ordered = name not in texts and levels.get(name) != "nominal"
        operators = ["eq", "ne", "lt", "le", "gt", "ge", "in"] if ordered else ["eq", "ne", "in"]
        operator = st.radio(
            _("Condition"),
            operators,
            key=f"{prefix}-operator",
            format_func=_operator,
            horizontal=True,
        )
        codes = sorted(set(column))
        if operator == "in":
            values = st.multiselect(
                _("Valeurs"),
                codes,
                key=f"{prefix}-values",
                format_func=lambda code: book.category(name, code),
                placeholder=_("Choisir les valeurs"),
            )
            return Subset(name, "in", list(values)) if values else None
        if len(codes) > CODES_LISTED and name not in texts:
            value = st.number_input(_("Valeur"), value=None, key=f"{prefix}-number")
        else:
            value = st.selectbox(
                _("Valeur"),
                codes,
                index=None,
                key=f"{prefix}-value",
                format_func=lambda code: book.category(name, code),
                placeholder=_("Choisir une valeur"),
            )
        return Subset(name, operator, value) if value is not None else None


def _asked(project: Project, key: str, chosen, options, subset=None) -> tuple:
    return (key, repr(sorted(chosen.items())), repr(sorted(options.items())),
            fingerprint.fingerprint(project), i18n.language(), repr(subset))  # fmt: skip


def _run(project: Project, key: str, chosen, options, subset=None) -> None:
    prepared = st.session_state[PREPARED][1]
    try:
        result = run(project, prepared, key, chosen, options, subset)
    except AnalysisRefused:
        return  # shown before the button already
    st.session_state[RESULT] = (_asked(project, key, chosen, options, subset), result)


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
    files = analysis_files(c.project_path())
    today = date.today().isoformat()
    with st.container(horizontal=True):
        st.button(
            _("Écrire à côté du projet"), key="analysis-write", on_click=_write, args=(project,)
        )
        st.download_button(
            _("Rapport (Markdown)"),
            data=render_report(project, prepared, result, files, today).encode("utf-8"),
            file_name=files.markdown.name,
            mime="text/markdown",
            key="analysis-download-md",
        )
    c.show_message("analysis-write")
    apa_view.panel(project, prepared, result, asked, files, shown_above=("docx",))


def _add(project: Project, prepared: PreparedData, asked: tuple, result) -> None:
    """v0.11: the analysis at the end of the notebook, retained, with the titles and notes
    a person changed above (never their numbers: the notebook numbers by its order)."""
    path = c.project_path()
    try:
        notebook = nb.open_notebook(project, path)
        entry = nb.add(notebook, project, result, edits=apa_view.edits(project, prepared, result,
                                                                      asked))  # fmt: skip
        nb.save_notebook(notebook, nb.notebook_path(path))
    except (OSError, nb.NotebookError) as error:
        text = nb.reason_text(error) if isinstance(error, nb.NotebookError) else str(error)
        st.session_state.message = ("error", text, "analysis-add")
        return
    st.session_state.message = (
        "success",
        _("Ajoutée au carnet : {id}. Le carnet se trouve sur la page Carnet.").format(id=entry.id),
        "analysis-add",
    )


def in_notebook(notebook: nb.Notebook, project: Project, result) -> str | None:
    """The identifier of the same analysis already in the notebook (v0.16): the same
    analysis, variables, options and subgroup, whatever the session that added it."""
    variables = {
        role.key: [nb.reference(project, n) for n in result.chosen[role.key]]
        for role in CATALOGUE[result.analysis].roles
        if result.chosen.get(role.key)
    }
    options = {k: str(v) for k, v in sorted(result.options.items())}
    subgroup = nb.kept_subgroup(project, result.subgroup)
    for entry in notebook.entries:
        same = (entry.analysis, entry.variables, entry.options, entry.subgroup)
        if same == (result.analysis, variables, options, subgroup):
            return entry.id
    return None


def _actions(project: Project, prepared: PreparedData, asked: tuple, result) -> None:
    """Under "Lancer l'analyse" (v0.16, finding 15): what comes next, before the result."""
    path = c.project_path()
    files = analysis_files(path)
    today = date.today().isoformat()
    try:
        found = in_notebook(nb.open_notebook(project, path), project, result)
    except nb.NotebookError:
        found = None  # the notebook cannot be read: adding says why
    document = apa_view.current(project, prepared, result, asked)
    word = FORMATS["docx"] if FORMATS["docx"] in available(document) else None
    with st.container(horizontal=True):
        st.button(
            _("Déjà au carnet : {id}").format(id=found) if found else _("Ajouter au carnet"),
            key="analysis-add",
            icon=":material/bookmark_add:",
            type="primary",
            disabled=found is not None,
            on_click=_add,
            args=(project, prepared, asked, result),
            help=_(
                "Le carnet garde les analyses de l'étude pour l'ébauche d'article, avec les "
                "titres et les notes changés plus bas. Il ne garde que des agrégats."
            ),
        )
        if word is not None:
            st.download_button(
                _("Word"),
                data=apa_view.rendered(project, prepared, result, asked, word),
                file_name=files.markdown.stem + word.suffix,
                mime=word.mime,
                key="analysis-download-docx",
                help=_("Les tableaux et figures APA, avec les titres et notes de la page."),
            )
        st.download_button(
            _("Excel"),
            data=report_xlsx(project, prepared, result, files, today),
            file_name=files.xlsx.name,
            mime=XLSX_TYPE,
            key="analysis-download-xlsx",
            help=_("Les tableaux du résultat."),
        )
        st.download_button(
            _("Script R"),
            data=r_bundle(project, files, project_stem(path), result, today),
            file_name=files.r.with_suffix(".zip").name,
            mime="application/zip",
            key="analysis-download-r",
            help=_(
                "Refait l'analyse hors de l'outil, dans le dossier de la base, avec le fichier "
                "de commandes et le script de préparation joints (.zip)."
            ),
        )
    c.show_message("analysis-add")
    if found:
        c.go_button(_("Ouvrir le carnet"), "go-notebook", "notebook")


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
    prepared = prepared_data(project)
    if prepared is None:
        return
    advice_view.panel(project)
    book = Codebook(project, prepared)
    key = st.selectbox(
        _("Analyse"),
        list(CATALOGUE),
        placeholder=_("Choisir…"),
        key=ANALYSIS,
        format_func=TITLES.__getitem__,
    )
    st.caption(PURPOSES[key])
    chosen = _choose_variables(project, key, book)
    options = _choose_options(key, chosen, prepared, book)
    subset = subgroup_widgets(project, prepared, book, "analysis-subgroup")
    complete = all(len(chosen.get(r.key, [])) >= r.least for r in CATALOGUE[key].roles)
    found = None
    if complete:
        refused = conditions.check_subgroup(project, subset, prepared) if subset else []
        if refused:
            found = conditions.Check(refusals=refused)
        else:
            data = apply_subset(prepared, subset) if subset else prepared
            found = conditions.check(project, key, chosen, options, data)
    last = st.session_state.get(RESULT)
    current = last is not None and last[0] == _asked(project, key, chosen, options, subset)
    if found is not None and not current:
        for reason in found.refusals:
            st.error(reason)
        undecided = [n for names in chosen.values() for n in names if book.levels.get(n) is None]
        if undecided:
            c.go_button(_("Décider les niveaux de mesure (page Base)"), "go-base-levels", "base")
        for warning in found.warnings:
            st.warning(warning)
    st.button(
        _("Lancer l'analyse"),
        key="analysis-run",
        type="primary",
        disabled=found is None or not found.ok,
        on_click=_run,
        args=(project, key, chosen, options, subset),
    )
    if current:
        _actions(project, prepared, last[0], last[1])
        _show(project, prepared, last[0], last[1])
    elif last is not None and last[0][0] == key:
        st.write(_("Les choix ont changé depuis la dernière analyse : relancez-la."))
