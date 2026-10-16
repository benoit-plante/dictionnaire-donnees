"""Command line: `ddict profiler`, `exporter`, `documenter`, `questionnaire`, `enrichir`,
`rattacher`, `evaluer`, `analyser`, `carnet`, `resultats`, `exclusions`, `conseiller`,
`reviser`."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import socket
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path

from ddict import __version__, settings
from ddict.export.documented import CopyError
from ddict.i18n import LANGUAGES, _
from ddict.io import ReadError
from ddict.llm import DEFAULT_BLOCK_SIZE, build_blocks
from ddict.llm.defaults import DEFAULT_ENDPOINT
from ddict.llm.link import DEFAULT_LINK_BLOCK_SIZE, build_link_blocks
from ddict.llm.stems import DEFAULT_STEM_BLOCK_SIZE, build_stem_blocks
from ddict.naming import NamingError
from ddict.privacy import MIN_CELL_COUNT
from ddict.project import (
    ProjectError,
    load_project,
    save_project,
)
from ddict.questionnaire.labels import propose_value_labels
from ddict.questionnaire.link import candidates
from ddict.waves import ReferenceError
from ddict.workflow import (
    ProjectExists,
    QuestionnaireExists,
    UnknownGroups,
    acronym_summary,
    add_questionnaire,
    advice_error_text,
    analysis_files,
    copy_error_text,
    documented_copy,
    exchange_dir,
    export_codebook,
    export_context,
    export_name_table,
    export_syntax,
    failure_advice,
    format_note,
    naming_summary,
    platform_notes,
    platform_summary,
    profile_database,
    profile_summary,
    project_stem,
    questionnaire_summary,
    rename,
    wave_summary,
    write_wave_report,
)

EXIT_ERROR = 2


def cmd_profile(args: argparse.Namespace) -> int:
    try:
        project, output = profile_database(
            args.base, args.sortie, replace=args.remplacer, min_cell_count=args.seuil
        )
    except ProjectExists as error:
        print(
            _("Le projet {path} existe déjà. Utilisez --remplacer pour l'écraser.").format(
                path=error
            ),
            file=sys.stderr,
        )
        return EXIT_ERROR
    print(_("Projet créé : {path}").format(path=output))
    print(profile_summary(project))
    for note in platform_notes(project):
        print(note)
    if note := format_note(project):
        print(note)
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    project_path = Path(args.projet)
    project = load_project(project_path)
    try:
        xlsx, markdown = export_codebook(
            project,
            project_path,
            kind="work" if args.travail else "final",
            omit_groups=tuple(args.sans_texte or ()),
            xlsx=Path(args.xlsx) if args.xlsx else None,
            markdown=Path(args.md) if args.md else None,
            language=args.langue,
        )
    except UnknownGroups as error:
        print(
            _("Groupe inconnu : {groups}. Groupes du projet : {known}.").format(
                groups=", ".join(error.unknown), known=", ".join(error.known) or _("aucun")
            ),
            file=sys.stderr,
        )
        return EXIT_ERROR
    print(_("Codebook Excel : {path}").format(path=xlsx))
    print(_("Rapport Markdown : {path}").format(path=markdown))
    table = export_name_table(project, project_path)
    if table is not None:
        print(_("Table de correspondance des noms : {path}").format(path=table))
    if args.syntaxe:
        for path in export_syntax(project, project_path, language=args.langue).values():
            print(_("Fichier de commandes : {path}").format(path=path))
    if args.contexte:
        for path in export_context(
            project,
            project_path,
            statistics=args.avec_statistiques,
            omit_groups=tuple(args.sans_texte or ()),
            language=args.langue,
        ):
            print(_("Contexte d'analyse : {path}").format(path=path))
    return 0


def cmd_copy(args: argparse.Namespace) -> int:
    project_path = Path(args.projet)
    project = load_project(project_path)
    try:
        result = documented_copy(
            project,
            project_path,
            database=Path(args.base) if args.base else None,
            target=Path(args.sortie) if args.sortie else None,
            replace=args.remplacer,
        )
    except CopyError as error:
        text = copy_error_text(error, project.source.name)
        if error.reason == "exists":
            text += " " + _("Utilisez --remplacer.")
        print(text, file=sys.stderr)
        return EXIT_ERROR
    print(
        _(
            "Copie documentée : {path} ({rows} lignes, {columns} variables), identique à "
            "l'original case par case."
        ).format(path=result.path, rows=result.n_rows, columns=result.n_columns)
    )
    if result.missing_not_written:
        print(
            _(
                "Codes confirmés par l'équipe non écrits, SPSS n'acceptant que 3 codes "
                "manquants : {names}. Ceux du fichier sont gardés."
            ).format(names=", ".join(result.missing_not_written))
        )
    return 0


# The analyses as the command line names them (v0.9): the catalogue's keys, or in French.
ANALYSES = {
    "table1": "table1",
    "tableau1": "table1",
    "t_test": "t_test",
    "test_t": "t_test",
    "anova": "anova",
    "chi_square": "chi_square",
    "khi2": "chi_square",
    "correlation": "correlation",
    "regression": "regression",
}
ROLE_ARGUMENTS = {
    "variables": "variables",
    "group": "groupe",
    "outcome": "dependante",
    "rows": "lignes",
    "columns": "colonnes",
    "predictors": "predicteurs",
}
# The actions of `ddict carnet`, in French or in English (v0.11).
NOTEBOOK_ACTIONS = {
    "lister": "list",
    "list": "list",
    "ajouter": "add",
    "add": "add",
    "retirer": "remove",
    "remove": "remove",
    "deplacer": "move",
    "move": "move",
    "retenir": "retain",
    "retain": "retain",
    "ecarter": "leave_out",
    "leave-out": "leave_out",
    "confirmer": "confirm",
    "confirm": "confirm",
    "numeros": "numbers",
    "numbers": "numbers",
    "echantillon": "sample",
    "sample": "sample",
}
OPTION_ARGUMENTS = {
    "method": "methode",
    "alternative": "hypothese",
    "post_hoc": "post_hoc",
    "levels": "modalites",
}


def _asked(args: argparse.Namespace) -> tuple[dict[str, list[str]], dict[str, str]]:
    """The variables by role and the options of an analysis, as the command line gives
    them."""
    chosen = {
        role: list(getattr(args, argument))
        for role, argument in ROLE_ARGUMENTS.items()
        if getattr(args, argument)
    }
    options = {
        option: getattr(args, argument)
        for option, argument in OPTION_ARGUMENTS.items()
        if getattr(args, argument)
    }
    return chosen, options


def _print_refusal(error) -> None:
    print(_("Analyse refusée :"), file=sys.stderr)
    for reason in error.check.refusals:
        print(f"- {reason}", file=sys.stderr)


def cmd_analyse(args: argparse.Namespace) -> int:
    # Imported here: SciPy and statsmodels load only for an analysis.
    from ddict.analysis.apa import describe
    from ddict.analysis.compute import AnalysisRefused, run
    from ddict.analysis.data import DataError, prepare
    from ddict.analysis.formats import FORMATS
    from ddict.analysis.report import write_apa, write_report

    # v0.10: the APA tables and figures, in each format asked (all by default, none with
    # --format aucun).
    keys = None if not args.format else [k for k in args.format if k != "aucun"]
    unknown = [k for k in keys or [] if k not in FORMATS]
    if unknown:
        print(
            _("Format inconnu : {formats}. Formats : {known}.").format(
                formats=", ".join(unknown), known=", ".join(FORMATS)
            ),
            file=sys.stderr,
        )
        return EXIT_ERROR
    project_path = Path(args.projet)
    project = load_project(project_path)
    try:
        prepared = prepare(project, project_path, Path(args.base) if args.base else None)
    except DataError as error:
        print(copy_error_text(error, project.source.name), file=sys.stderr)
        return EXIT_ERROR
    try:
        result = run(project, prepared, ANALYSES[args.analyse], *_asked(args))
    except AnalysisRefused as error:
        _print_refusal(error)
        return EXIT_ERROR
    print(result.sentence)
    for warning in result.warnings:
        print(_("Avertissement : {text}").format(text=warning))
    files = analysis_files(project_path)
    today = datetime.now().date().isoformat()
    written = write_report(project, prepared, result, files, project_stem(project_path), today)
    written += write_apa(files, describe(project, prepared, result), keys)
    for path in written:
        print(_("Fichier écrit : {path}").format(path=path))
    return 0


# --- The analysis notebook (v0.11): `ddict carnet` and `ddict resultats`. ---


def _database(project, project_path: Path, base: str | None):
    """The database ready for the analyses, or None and why it cannot be read."""
    from ddict.analysis.data import DataError, prepare

    try:
        return prepare(project, project_path, Path(base) if base else None), ""
    except DataError as error:
        return None, copy_error_text(error, project.source.name)


def notebook_lines(project, notebook, statuses) -> list[str]:
    """The notebook as `ddict carnet lister` prints it: each analysis in its order, retained
    or not, its state, its variables, what changed, and its sentence."""
    from ddict.analysis import notebook as nb
    from ddict.analysis.catalogue import ROLES
    from ddict.analysis.notebook_check import difference_text, state_text
    from ddict.analysis.notebook_export import heading

    if not notebook.entries:
        return [_("Le carnet est vide : ajoutez-y une analyse avec « ddict carnet ajouter ».")]
    by_id = {status.entry_id: status for status in statuses}
    lines = []
    for rank, entry in enumerate(notebook.entries, start=1):
        status = by_id[entry.id]
        kept = _("retenue") if entry.retained else _("écartée")
        lines.append(f"{rank}. {heading(entry)} — {kept}, {state_text(status.state)}")
        try:
            names = nb.resolved(project, entry)
            lines.append(
                "   " + " ; ".join(f"{ROLES[role]} : {', '.join(n)}" for role, n in names.items())
            )
        except nb.NotebookError:
            pass
        if status.reason:
            lines.append(f"   {status.reason}")
        for difference in status.differences:
            lines.append(f"   {difference_text(difference)}")
        if entry.computed.sentence:
            lines.append(f"   {entry.computed.sentence}")
        if entry.pending is not None and entry.pending.sentence:
            lines.append("   " + _("Nouveau : {sentence}").format(sentence=entry.pending.sentence))
    method = by_id.get(nb.METHOD)
    if method is not None:
        lines.append(f"{nb.METHOD}. {_('Méthode')} — {state_text(method.state)}")
        if method.reason:
            lines.append(f"   {method.reason}")
        for difference in method.differences:
            lines.append(f"   {difference_text(difference)}")
    lines.append(numbering_text(notebook))
    return lines


def numbering_text(notebook) -> str:
    return _("Numérotation : premier tableau {table}, première figure {figure}.").format(
        table=notebook.first_table, figure=notebook.first_figure
    )


def _notebook_error(error) -> int:
    from ddict.analysis import notebook as nb

    print(nb.reason_text(error), file=sys.stderr)
    return EXIT_ERROR


def cmd_notebook(args: argparse.Namespace) -> int:
    from ddict.analysis import notebook as nb

    project_path = Path(args.projet)
    project = load_project(project_path)
    path = nb.notebook_path(project_path)
    try:
        notebook = nb.open_notebook(project, project_path)
        code = _notebook_action(NOTEBOOK_ACTIONS[args.action], args, project, project_path,
                                notebook)  # fmt: skip
    except nb.NotebookError as error:
        return _notebook_error(error)
    sample = NOTEBOOK_ACTIONS[args.action] == "sample"
    if code == 0 and (notebook.entries or path.is_file() or sample):
        nb.save_notebook(notebook, path)
    return code


def _notebook_action(action, args, project, project_path, notebook) -> int:
    from ddict.analysis import notebook as nb
    from ddict.analysis import notebook_check as check
    from ddict.analysis.compute import AnalysisRefused, run

    today = datetime.now().date().isoformat()
    if action == "add":
        prepared, reason = _database(project, project_path, args.base)
        if prepared is None:
            print(reason, file=sys.stderr)
            return EXIT_ERROR
        try:
            result = run(project, prepared, ANALYSES[args.analyse], *_asked(args))
        except AnalysisRefused as error:
            _print_refusal(error)
            return EXIT_ERROR
        entry = nb.add(notebook, project, result, today=today)
        print(_("Ajoutée au carnet : {id}").format(id=entry.id))
        if result.sentence:
            print(result.sentence)
    elif action == "remove":
        nb.remove(notebook, args.numero)
        print(_("Retirée du carnet : {id}").format(id=args.numero))
    elif action == "move":
        nb.move(notebook, args.numero, args.rang)
        rank = [e.id for e in notebook.entries].index(args.numero) + 1
        print(_("{id} est maintenant au rang {rank}.").format(id=args.numero, rank=rank))
    elif action in ("retain", "leave_out"):
        for entry_id in args.numeros:
            nb.retain(notebook, entry_id, action == "retain")
        text = _("Retenues : {ids}") if action == "retain" else _("Écartées : {ids}")
        print(text.format(ids=", ".join(args.numeros)))
    elif action == "sample":
        if args.vider:
            nb.describe_sample(notebook, project, [])
        elif args.variables:
            nb.describe_sample(notebook, project, args.variables)
        names = nb.sample_names(notebook, project)
        print(
            _("Variables qui décrivent l'échantillon : {names}").format(
                names=", ".join(names) or _("aucune")
            )
        )
    elif action == "numbers":
        if args.tableau is not None:
            notebook.first_table = max(1, args.tableau)
        if args.figure is not None:
            notebook.first_figure = max(1, args.figure)
        print(numbering_text(notebook))
    else:  # list, confirm: recompute what the decisions changed since
        prepared, reason = _database(project, project_path, args.base)
        statuses = check.check_everything(notebook, project, prepared, today=today, reason=reason)
        if action == "list":
            for line in notebook_lines(project, notebook, statuses):
                print(line)
            return 0
        if prepared is None:
            print(reason, file=sys.stderr)
            return EXIT_ERROR
        ids = [s.entry_id for s in statuses if s.state == "changed"] if args.tout else args.numeros
        if not ids:
            print(_("Aucun changement à confirmer."))
        for entry_id in ids or []:
            check.confirm(notebook, entry_id)
            print(_("Confirmée : {id}").format(id=check.waiting_text([entry_id])))
    return 0


def cmd_results(args: argparse.Namespace) -> int:
    from ddict.analysis import notebook as nb
    from ddict.analysis.notebook_check import waiting_text
    from ddict.analysis.notebook_export import ExportBlocked, write_results

    project_path = Path(args.projet)
    project = load_project(project_path)
    path = nb.notebook_path(project_path)
    try:
        notebook = nb.load_notebook(path) if path.is_file() else None
    except nb.NotebookError as error:
        return _notebook_error(error)
    if notebook is None or not any(e.retained for e in notebook.entries):
        print(_("Aucune analyse retenue dans le carnet."), file=sys.stderr)
        return EXIT_ERROR
    if not nb.belongs(notebook, project):
        print(_("Ce carnet a été fait avec une autre base que celle du projet."), file=sys.stderr)
        return EXIT_ERROR
    prepared, reason = _database(project, project_path, args.base)
    if prepared is None:
        print(reason, file=sys.stderr)
        return EXIT_ERROR
    try:
        written = write_results(project, prepared, notebook, project_path, language=args.langue)
    except ExportBlocked as error:
        nb.save_notebook(notebook, path)  # what changed waits in the notebook
        print(
            _(
                "À confirmer avant de produire le document : {ids}. Voyez les différences "
                "avec « ddict carnet lister », puis confirmez-les avec « ddict carnet "
                "confirmer »."
            ).format(ids=waiting_text(error.ids)),
            file=sys.stderr,
        )
        return EXIT_ERROR
    nb.save_notebook(notebook, path)
    for written_path in written:
        print(_("Fichier écrit : {path}").format(path=written_path))
    return 0


# --- The exclusion rules (v0.12): `ddict exclusions`. ---

EXCLUSION_ACTIONS = {
    "lister": "list",
    "list": "list",
    "ajouter": "add",
    "add": "add",
    "retirer": "remove",
    "remove": "remove",
    "deplacer": "move",
    "move": "move",
    "signaux": "signals",
    "signals": "signals",
}


def exclusion_lines(project, flow) -> list[str]:
    """The rules in their rank, with who each excluded and the counts of the flow, as
    `ddict exclusions lister` prints them."""
    from ddict.project.exclusions import rule_text

    rules = project.exclusions.rules
    if not rules:
        return [_("Aucune règle d'exclusion : toutes les réponses sont analysées.")]
    counts = dict(flow.excluded) if flow is not None else {}
    lines = []
    for rank, rule in enumerate(rules, start=1):
        line = f"{rank}. {rule.id} — {rule.reason} : {rule_text(rule)}"
        if rule.id in counts:
            line += " — " + _("{n} exclues").format(n=counts[rule.id])
        lines.append(line)
        if rule.source:
            lines.append("   " + _("Source : {source}").format(source=rule.source))
    if flow is not None:
        lines.append(
            _(
                "Réponses reçues : {start} ; exclues : {excluded} ; échantillon analysé : "
                "{analysed}."
            ).format(start=flow.start, excluded=flow.start - flow.analysed, analysed=flow.analysed)
        )
    return lines


def _whole_number(text: str) -> int:
    from ddict.project.exclusions import ExclusionRefused

    try:
        return int(text)
    except ValueError:
        raise ExclusionRefused(
            [_("« {value} » n'est pas un nombre entier.").format(value=text)]
        ) from None


def _rule_data(args: argparse.Namespace, project, project_path: Path) -> dict:
    """The fields of the rule the command line describes. Raises ExclusionRefused."""
    from ddict.analysis.quality import duration_rule
    from ddict.project import exclusions as ex

    if args.condition or args.score:
        what, operator, *values = args.condition or args.score
        data = ex.condition_data(project, what, operator, values, score=bool(args.score))
    elif args.completude:
        group, count = args.completude
        data = {"kind": "completeness", "group": group, "min_answered": _whole_number(count)}
    elif args.duree:
        start, end, seconds = args.duree
        prepared, reason = _database(project, project_path, args.base)
        if prepared is None:
            raise ex.ExclusionRefused([reason])
        data = duration_rule(project, prepared, start, end, ex.typed_number(str(seconds)))
    elif args.ligne_droite:
        data = {"kind": "straightlining", "group": args.ligne_droite}
    else:
        names = [ex.original(project, n) for n in args.doublons]
        data = {"kind": "duplicate", "variables": names}
    data["reason"] = args.raison
    if args.source:
        data["source"] = args.source
    return data


def cmd_exclusions(args: argparse.Namespace) -> int:
    from ddict.analysis.quality import proposed_dates, signal_lines
    from ddict.project import exclusions as ex

    project_path = Path(args.projet)
    project = load_project(project_path)
    action = EXCLUSION_ACTIONS[args.action]
    if action in ("list", "signals"):
        prepared, reason = _database(project, project_path, args.base)
        if action == "list":
            for line in exclusion_lines(project, prepared.flow if prepared else None):
                print(line)
            if prepared is None and project.exclusions.rules:
                print(reason, file=sys.stderr)
            return 0
        if prepared is None:
            print(reason, file=sys.stderr)
            return EXIT_ERROR
        dates = proposed_dates(project)
        if args.debut and args.fin:
            dates = (ex.original(project, args.debut), ex.original(project, args.fin))
        duplicate_on = [ex.original(project, n) for n in args.doublons] if args.doublons else None
        try:
            lines = signal_lines(project, prepared, dates, args.duree_min, duplicate_on)
        except KeyError as error:
            print(_("{name} : variable inconnue du projet.").format(name=error.args[0]),
                  file=sys.stderr)  # fmt: skip
            return EXIT_ERROR
        for line in lines:
            print(line)
        return 0
    try:
        if action == "add":
            rule = ex.add(project, _rule_data(args, project, project_path))
            print(_("Règle ajoutée : {id} — {text}").format(id=rule.id, text=ex.rule_text(rule)))
        elif action == "remove":
            ex.remove(project, args.numero)
            print(_("Règle retirée : {id}").format(id=args.numero))
        else:
            ex.move(project, args.numero, args.rang)
            rank = [r.id for r in project.exclusions.rules].index(args.numero) + 1
            print(_("{id} est maintenant au rang {rank}.").format(id=args.numero, rank=rank))
    except ex.ExclusionRefused as error:
        print(_("Règle refusée :"), file=sys.stderr)
        for reason in error.reasons:
            print(f"- {reason}", file=sys.stderr)
        return EXIT_ERROR
    save_project(project, project_path)
    from ddict.analysis import notebook as nb

    if nb.notebook_path(project_path).is_file():
        print(
            _(
                "Les analyses du carnet seront recalculées : voyez ce qui a changé avec "
                "« ddict carnet lister »."
            )
        )
    return 0


def advice_lines(proposals) -> list[str]:
    """The model's proposals as the command line prints them (v0.9, D-079)."""
    from ddict.analysis.catalogue import ROLES, TITLES
    from ddict.llm.advise import method_text

    lines = []
    for number, proposal in enumerate(proposals, start=1):
        lines.append(f"{number}. {TITLES[proposal.analysis]}")
        for role, names in proposal.chosen.items():
            lines.append(f"   {ROLES[role]} : {', '.join(names)}")
        if proposal.options:
            lines.append("   " + _("Méthode : {method}").format(method=method_text(proposal)))
        lines.append("   " + _("Raison : {reason}").format(reason=proposal.reason))
        for reason in proposal.check.refusals:
            lines.append("   " + _("Condition non remplie : {reason}").format(reason=reason))
    return lines


def cmd_advise(args: argparse.Namespace) -> int:
    from ddict.llm.advise import AdviceError, build_advice_block

    project_path = Path(args.projet)
    project = load_project(project_path)
    try:
        block = build_advice_block(project, args.objectif)
    except AdviceError as error:
        print(advice_error_text(error), file=sys.stderr)
        return EXIT_ERROR
    if args.apercu:
        return _preview(project_path, [block])
    if not args.modele:
        print(_("Ajoutez --modele, ou --apercu pour voir le message sans rien envoyer."))
        return EXIT_ERROR
    try:
        from ddict.llm.advise import advise
        from ddict.llm.client import EndpointRefused, LocalModelClient
    except ImportError:
        print(
            _(
                "L'option IA n'est pas installée. Réinstallez l'outil avec ses options : "
                'uv tool install --reinstall ".[ia,revision]" (voir docs/installation-windows.md).'
            ),
            file=sys.stderr,
        )
        return EXIT_ERROR
    try:
        client = LocalModelClient(args.modele, endpoint=args.adresse)
    except EndpointRefused as error:
        print(
            _("Adresse refusée : seul un serveur sur cet ordinateur est permis ({detail}).").format(
                detail=error
            ),
            file=sys.stderr,
        )
        return EXIT_ERROR
    with client:
        found = advise(
            project,
            client,
            args.objectif,
            now=datetime.now().isoformat(timespec="seconds"),
            log_dir=exchange_dir(project_path),
        )
    if found.proposals is None:
        run = found.result.run
        print(_("Aucune proposition ({detail}).").format(detail=run.detail), file=sys.stderr)
        advice = failure_advice(run.detail, client.endpoint, args.modele)
        if advice:
            print(advice, file=sys.stderr)
        return EXIT_ERROR
    if not found.proposals:
        print(_("Le modèle ne propose aucune analyse du catalogue pour cet objectif."))
        return 0
    print(_("Propositions du modèle, à vérifier ; rien n'est calculé :"))
    for line in advice_lines(found.proposals):
        print(line)
    print(
        _("Pour lancer une analyse : ddict analyser {path} <analyse> …").format(path=project_path)
    )
    return 0


def cmd_questionnaire(args: argparse.Namespace) -> int:
    project_path = Path(args.projet)
    project = load_project(project_path)
    try:
        removed = add_questionnaire(project, args.fichier, replace=args.remplacer)
    except QuestionnaireExists as error:
        print(
            _(
                "Le projet a déjà un questionnaire ({name}). Utilisez --remplacer pour le "
                "remplacer."
            ).format(name=error),
            file=sys.stderr,
        )
        return EXIT_ERROR
    except ReadError as error:
        print(
            _("Impossible de lire le questionnaire : {detail}").format(detail=error),
            file=sys.stderr,
        )
        return EXIT_ERROR
    save_project(project, project_path)
    if removed:
        print(
            _(
                "{n} rattachements retirés : ils renvoyaient à l'ancien questionnaire. "
                "Relancez ddict rattacher."
            ).format(n=removed)
        )
    found = questionnaire_summary(project.questionnaire) + platform_summary(project)
    for line in found + acronym_summary(project):
        print(line)
    print(_("Enregistré dans {path}.").format(path=project_path))
    return 0


def cmd_rename(args: argparse.Namespace) -> int:
    project_path = Path(args.projet)
    project = load_project(project_path)
    try:
        report = rename(project, suffix=args.suffixe, prefix=args.prefixe, reference=args.reference)
    except NamingError:
        print(_("Marque de vague invalide : lettres et chiffres seulement."), file=sys.stderr)
        return EXIT_ERROR
    except (ReferenceError, ProjectError, ReadError) as error:
        print(
            _("Impossible de lire la vague précédente : {detail}").format(detail=error),
            file=sys.stderr,
        )
        return EXIT_ERROR
    save_project(project, project_path)
    if report is not None:
        for line in wave_summary(report):
            print(line)
        path = write_wave_report(project, report, project_path)
        print(_("Rapport des écarts entre les vagues : {path}").format(path=path))
    if args.apercu:
        return _preview(project_path, build_stem_blocks(project, size=args.taille_bloc))
    status = 0
    if args.modele:  # optional: the model proposes the stems the rules left open (D-051)
        status = _run_model(args, project, project_path, "rename")
    for line in naming_summary(project):
        print(line)
    print(_("Enregistré dans {path}.").format(path=project_path))
    return status


def cmd_enrich(args: argparse.Namespace) -> int:
    project_path = Path(args.projet)
    project = load_project(project_path)
    if args.apercu:
        return _preview(project_path, build_blocks(project, size=args.taille_bloc))
    if not args.modele:
        print(_("Indiquez le modèle avec --modele, ou utilisez --apercu."), file=sys.stderr)
        return EXIT_ERROR
    return _run_model(args, project, project_path, "enrich")


def cmd_link(args: argparse.Namespace) -> int:
    project_path = Path(args.projet)
    project = load_project(project_path)
    if project.questionnaire is None:
        print(
            _(
                "Le projet n'a pas de questionnaire. Lisez-le d'abord : "
                "ddict questionnaire {path} questionnaire.pdf"
            ).format(path=project_path),
            file=sys.stderr,
        )
        return EXIT_ERROR
    found = candidates(project)
    waiting = propose_value_labels(project)
    if waiting:
        save_project(project, project_path)
        print(
            _(
                "Étiquettes de valeurs tirées des options de réponse, à vérifier dans "
                "l'interface : {names}."
            ).format(names=", ".join(waiting))
        )
    print(
        _("{n} variables sur {total} ont des questions candidates.").format(
            n=sum(1 for ids in found.values() if ids), total=len(found)
        )
    )
    if args.apercu:
        return _preview(project_path, build_link_blocks(project, size=args.taille_bloc))
    if not args.modele:
        print(
            _(
                "Choisissez les rattachements dans l'interface (ddict reviser), ou ajoutez "
                "--modele pour qu'un modèle local propose un choix parmi les candidates."
            )
        )
        return 0
    return _run_model(args, project, project_path, "link")


def _run_model(args: argparse.Namespace, project, project_path: Path, task: str) -> int:
    """Send the blocks of `task` ("enrich", "link" or "rename") to the local model, with
    progress."""
    try:
        from ddict.llm.client import EndpointRefused, LocalModelClient
        from ddict.llm.enrich import enrich
        from ddict.llm.link import propose_links
        from ddict.llm.stems import propose_stems
    except ImportError:
        print(
            _(
                "L'option IA n'est pas installée. Réinstallez l'outil avec ses options : "
                'uv tool install --reinstall ".[ia,revision]" (voir docs/installation-windows.md).'
            ),
            file=sys.stderr,
        )
        return EXIT_ERROR
    try:
        client = LocalModelClient(args.modele, endpoint=args.adresse)
    except EndpointRefused as error:
        print(
            _("Adresse refusée : seul un serveur sur cet ordinateur est permis ({detail}).").format(
                detail=error
            ),
            file=sys.stderr,
        )
        return EXIT_ERROR

    outcomes = {
        "succeeded": _("réussi"),
        "invalid_response": _("réponse invalide"),
        "failed": _("échec"),
        "refused": _("refusé"),
    }
    failed = succeeded = 0
    with client:
        events = {"enrich": enrich, "link": propose_links, "rename": propose_stems}[task](
            project,
            client,
            now=lambda: datetime.now().isoformat(timespec="seconds"),
            block_size=args.taille_bloc,
            redo=args.refaire,
            save=lambda p: save_project(p, project_path),
            log_dir=exchange_dir(project_path),
        )
        try:
            for event in events:
                names = len(event.block.names)
                if event.result is None:
                    print(
                        _("Bloc {block} ({n} variables) : déjà fait.").format(
                            block=event.block.block_id, n=names
                        )
                    )
                    continue
                run = event.result.run
                status = outcomes[run.outcome]
                if run.detail:
                    status += f" ({run.detail})"
                    failed += 1
                else:
                    succeeded += 1
                print(
                    _("Bloc {block} ({n} variables) : {status}.").format(
                        block=event.block.block_id, n=names, status=status
                    ),
                    flush=True,
                )
        except KeyboardInterrupt:
            print(_("Interrompu. Les blocs terminés sont enregistrés ; relancez pour continuer."))
            return EXIT_ERROR
    last = project.ai_runs[-1].detail if failed and project.ai_runs else None
    advice = failure_advice(last, client.endpoint, args.modele)
    if advice:
        print(advice, file=sys.stderr)
    if succeeded:
        print(_("Propositions enregistrées dans {path}, à réviser.").format(path=project_path))
    elif failed:
        print(_("Aucune nouvelle proposition."), file=sys.stderr)
    return EXIT_ERROR if failed else 0


def cmd_bench(args: argparse.Namespace) -> int:
    """Measure an installed model on the fictional bases (v0.4, step 6; English in v0.5)."""
    try:
        from ddict.bench import render_report, run_bench, write_report
        from ddict.llm.client import EndpointRefused, LocalModelClient
    except ImportError:
        print(
            _(
                "L'option IA n'est pas installée. Réinstallez l'outil avec ses options : "
                'uv tool install --reinstall ".[ia,revision]" (voir docs/installation-windows.md).'
            ),
            file=sys.stderr,
        )
        return EXIT_ERROR
    folder = Path(args.dossier)
    if not folder.is_dir():
        print(_("Dossier introuvable : {path}").format(path=folder), file=sys.stderr)
        return EXIT_ERROR
    try:
        client = LocalModelClient(args.modele, endpoint=args.adresse)
    except EndpointRefused as error:
        print(
            _("Adresse refusée : seul un serveur sur cet ordinateur est permis ({detail}).").format(
                detail=error
            ),
            file=sys.stderr,
        )
        return EXIT_ERROR
    results = []
    with client:
        for item in run_bench(client, now=lambda: datetime.now().isoformat(timespec="seconds")):
            if isinstance(item, str):
                print(item, flush=True)
            else:
                results.append(item)
    detail = next((r.failure_detail for r in results if r.failure_detail), None)
    advice = failure_advice(detail, client.endpoint, args.modele)
    if advice:
        print(advice, file=sys.stderr)
    today = datetime.now().date().isoformat()
    text = render_report(results, model=args.modele, endpoint=client.endpoint, date=today)
    path = write_report(text, folder, args.modele, today)
    print(_("Rapport : {path}").format(path=path))
    return 0


def _preview(project_path: Path, blocks) -> int:
    folder = exchange_dir(project_path) / "apercu"
    folder.mkdir(parents=True, exist_ok=True)
    for prefix in {block.block_id.split("-")[0] for block in blocks}:
        for old in folder.glob(f"{prefix}-*.json"):
            old.unlink()
    for block in blocks:
        record = {
            "prompt_version": block.prompt_version,
            "block": block.block_id,
            "variables": list(block.names),
            "message_sha256": block.sha256,
            "messages": list(block.messages),
        }
        path = folder / f"{block.block_id}.json"
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(_("Aperçu : {n} blocs de messages, rien n'a été envoyé.").format(n=len(blocks)))
    print(_("Messages enregistrés dans : {path}").format(path=folder))
    return 0


REVIEW_HOST = "127.0.0.1"


def review_command(project_path: Path | None, port: int) -> tuple[list[str], dict[str, str]]:
    """The Streamlit command and environment: this computer only, no usage statistics.
    Without a project, the interface opens on its home page (v0.3)."""
    app = Path(__file__).resolve().parent / "review" / "app.py"
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app),
        "--server.address",
        REVIEW_HOST,
        "--server.port",
        str(port),
        "--browser.serverAddress",
        REVIEW_HOST,
        "--browser.gatherUsageStats",
        "false",
        "--global.developmentMode",
        "false",
        "--server.fileWatcherType",
        "none",
        # Headless: no first-run prompt asking for an email address in the console, and no
        # browser opened by Streamlit; cmd_review opens it once the page answers.
        "--server.headless",
        "true",
        # No "Deploy" button offering to put the interface online.
        "--client.toolbarMode",
        "minimal",
    ]
    if project_path is not None:
        command += ["--", str(project_path.resolve())]
    env = {
        **os.environ,
        "STREAMLIT_SERVER_ADDRESS": REVIEW_HOST,
        "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
    }
    return command, env


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def _wait_for_port(host: str, port: int, process: subprocess.Popen, timeout: float = 60) -> bool:
    """Wait until the local interface accepts connections (or the process ends)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and process.poll() is None:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def cmd_review(args: argparse.Namespace) -> int:
    project_path = Path(args.projet)
    load_project(project_path)  # a readable project, before starting anything
    return _launch(project_path, args.port)


def cmd_home(args: argparse.Namespace) -> int:
    """`ddict` alone: the interface, on its home page (v0.3)."""
    return _launch(None, args.port)


def _launch(project_path: Path | None, port: int) -> int:
    if importlib.util.find_spec("streamlit") is None:
        print(
            _(
                "L'interface de révision n'est pas installée. Installez-la avec : "
                'uv tool install --reinstall ".[ia,revision]" (voir docs/installation-windows.md).'
            ),
            file=sys.stderr,
        )
        return EXIT_ERROR
    if _port_open(REVIEW_HOST, port):
        if project_path is None:
            # Started again from the icon while it runs: show the open interface.
            print(_("L'outil est déjà ouvert : affichage dans le navigateur."))
            webbrowser.open(f"http://{REVIEW_HOST}:{port}")
            return 0
        print(
            _(
                "Le port {port} est déjà utilisé, peut-être par une autre révision ouverte. "
                "Fermez-la, ou ajoutez --port 8502."
            ).format(port=port),
            file=sys.stderr,
        )
        return EXIT_ERROR
    command, env = review_command(project_path, port)
    print(
        _(
            "Interface sur http://{host}:{port} (cet ordinateur seulement). "
            "Laissez cette fenêtre ouverte ; Ctrl+C ou fermer la fenêtre pour arrêter."
        ).format(host=REVIEW_HOST, port=port)
    )
    process = subprocess.Popen(command, env=env)
    try:
        if _wait_for_port(REVIEW_HOST, port, process):
            webbrowser.open(f"http://{REVIEW_HOST}:{port}")
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ddict",
        description=_(
            "Création de dictionnaires de données, en local. Lancé seul, ddict ouvre "
            "l'interface dans le navigateur."
        ),
    )
    parser.add_argument("--version", action="version", version=f"ddict {__version__}")
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help=_("Port local de l'interface, quand ddict est lancé seul (défaut : 8501)."),
    )
    parser.set_defaults(handler=cmd_home)
    # Without a command, `ddict` opens the interface on its home page (v0.3).
    commands = parser.add_subparsers(dest="command")

    profile = commands.add_parser(
        "profiler",
        aliases=["profile"],
        help=_("Lire une base (.sav, .csv, .dta, .sas7bdat ou .xlsx) et créer le fichier projet."),
    )
    profile.add_argument(
        "base",
        help=_(
            "Base de données : SPSS (.sav, .zsav), CSV, Stata (.dta), SAS (.sas7bdat) "
            "ou Excel (.xlsx, première feuille)."
        ),
    )
    profile.add_argument(
        "-o",
        "--sortie",
        "--output",
        help=_("Fichier projet à créer (par défaut : à côté de la base, en .dd.json)."),
    )
    profile.add_argument(
        "--seuil",
        "--threshold",
        type=int,
        default=MIN_CELL_COUNT,
        help=_("Effectif minimal affiché ; en dessous, il est masqué (défaut : 5)."),
    )
    profile.add_argument(
        "--remplacer", "--replace", action="store_true", help=_("Écraser un projet existant.")
    )
    profile.set_defaults(handler=cmd_profile)

    export = commands.add_parser(
        "exporter",
        aliases=["export"],
        help=_("Produire le codebook Excel et le rapport Markdown d'un projet."),
    )
    export.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    export.add_argument("--xlsx", help=_("Codebook Excel à écrire."))
    export.add_argument("--md", help=_("Rapport Markdown à écrire."))
    export.add_argument(
        "--travail",
        "--work",
        action="store_true",
        help=_("Inclure les propositions de l'IA en attente, marquées comme telles."),
    )
    export.add_argument(
        "--sans-texte",
        "--no-text",
        nargs="+",
        metavar="GROUPE",
        help=_(
            "Ne pas reproduire le texte des questions de ces groupes (p. ex. G3), pour un "
            "instrument protégé par le droit d'auteur (D-014)."
        ),
    )
    export.add_argument(
        "--syntaxe",
        "--syntax",
        action="store_true",
        help=_(
            "Écrire aussi les fichiers de commandes SPSS et R qui appliquent les "
            "décisions acceptées à vos données."
        ),
    )
    export.add_argument(
        "--contexte",
        "--context",
        action="store_true",
        help=_(
            "Écrire aussi le contexte d'analyse (contexte .md et datapackage.json) : le "
            "codebook compact, à donner à un programme ou à un modèle (v0.8)."
        ),
    )
    export.add_argument(
        "--avec-statistiques",
        "--with-statistics",
        action="store_true",
        help=_(
            "Ajouter au contexte d'analyse les statistiques, filtrées par la porte de "
            "confidentialité. Sans cette option, il ne contient que des métadonnées."
        ),
    )
    export.add_argument(
        "--langue",
        "--language",
        choices=list(LANGUAGES),
        help=_("Langue du codebook (défaut : celle de l'interface)."),
    )
    export.set_defaults(handler=cmd_export)

    copy = commands.add_parser(
        "documenter",
        aliases=["document"],
        help=_(
            "Écrire une copie de la base au format SPSS (.sav), avec les décisions acceptées. "
            "L'original n'est jamais modifié."
        ),
    )
    copy.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    copy.add_argument(
        "--base", "--database", help=_("La base d'origine, si elle n'est pas à côté du projet.")
    )
    copy.add_argument(
        "--sortie",
        "--output",
        help=_("Copie à écrire (défaut : à côté de la base, « -documente.sav »)."),
    )
    copy.add_argument(
        "--remplacer", "--replace", action="store_true", help=_("Remplacer une copie déjà écrite.")
    )
    copy.set_defaults(handler=cmd_copy)

    analyse = commands.add_parser(
        "analyser",
        aliases=["analyse"],
        help=_(
            "Lancer une analyse du catalogue sur la base, avec les décisions acceptées, et "
            "écrire son rapport et son script R à côté du projet."
        ),
    )
    analyse.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    _analysis_arguments(analyse)
    analyse.add_argument(
        "--base", "--database", help=_("La base d'origine, si elle n'est pas à côté du projet.")
    )
    analyse.add_argument(
        "--format",
        nargs="+",
        metavar="FORMAT",
        help=_(
            "Tableaux et figures APA : docx (Word), xlsx (graphiques Excel modifiables), ou "
            "aucun ; par défaut, tous ceux qui ont quelque chose à montrer."
        ),
    )
    analyse.set_defaults(handler=cmd_analyse)

    notebook_command = commands.add_parser(
        "carnet",
        aliases=["notebook"],
        help=_(
            "Le carnet d'analyses du projet : lister, ajouter, retirer, déplacer, retenir, "
            "écarter, confirmer, numéroter, décrire l'échantillon."
        ),
    )
    actions = notebook_command.add_subparsers(dest="action", required=True)
    listed = actions.add_parser(
        "lister",
        aliases=["list"],
        help=_("Recalculer et lister les analyses du carnet, avec ce qui a changé."),
    )
    listed.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    added = actions.add_parser(
        "ajouter",
        aliases=["add"],
        help=_("Lancer une analyse et l'ajouter à la fin du carnet, retenue."),
    )
    added.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    _analysis_arguments(added)
    removed = actions.add_parser("retirer", aliases=["remove"], help=_("Retirer une analyse."))
    removed.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    removed.add_argument("numero", help=_("Numéro de l'analyse, p. ex. A3."))
    moved = actions.add_parser(
        "deplacer", aliases=["move"], help=_("Mettre une analyse à un autre rang.")
    )
    moved.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    moved.add_argument("numero", help=_("Numéro de l'analyse, p. ex. A3."))
    moved.add_argument("rang", type=int, help=_("Son nouveau rang, 1 pour la première."))
    for name, alias, text in (
        ("retenir", "retain", _("Retenir des analyses pour le document des résultats.")),
        ("ecarter", "leave-out", _("Écarter des analyses du document, sans les retirer.")),
    ):
        kept = actions.add_parser(name, aliases=[alias], help=text)
        kept.add_argument("projet", help=_("Fichier projet (.dd.json)."))
        kept.add_argument("numeros", nargs="+", help=_("Numéros des analyses, p. ex. A1 A3."))
    confirmed = actions.add_parser(
        "confirmer",
        aliases=["confirm"],
        help=_("Confirmer le nouveau calcul d'analyses qui ont changé."),
    )
    confirmed.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    confirmed.add_argument("numeros", nargs="*", help=_("Numéros des analyses, p. ex. A1 A3."))
    confirmed.add_argument(
        "--tout", "--all", action="store_true", help=_("Confirmer toutes celles qui ont changé.")
    )
    numbers = actions.add_parser(
        "numeros",
        aliases=["numbers"],
        help=_("Numéro du premier tableau et de la première figure du document."),
    )
    numbers.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    numbers.add_argument("--tableau", "--table", type=int, help=_("Premier tableau (défaut : 1)."))
    numbers.add_argument("--figure", type=int, help=_("Première figure (défaut : 1)."))
    sample = actions.add_parser(
        "echantillon",
        aliases=["sample"],
        help=_(
            "Les variables qui décrivent l'échantillon analysé dans la Méthode (p. ex. l'âge "
            "et le genre), dans cet ordre ; sans variable, les montrer."
        ),
    )
    sample.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    sample.add_argument("variables", nargs="*", help=_("Noms des variables."))
    sample.add_argument("--vider", "--clear", action="store_true", help=_("N'en garder aucune."))
    for action in (listed, added, confirmed):
        action.add_argument(
            "--base",
            "--database",
            help=_("La base d'origine, si elle n'est pas à côté du projet."),
        )
    notebook_command.set_defaults(handler=cmd_notebook)

    results = commands.add_parser(
        "resultats",
        aliases=["results"],
        help=_(
            "Produire le document « Méthode et Résultats » : la Méthode, puis les analyses "
            "retenues du carnet, recalculées ; Word, graphiques Excel et script R maître, à "
            "côté du projet."
        ),
    )
    results.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    results.add_argument(
        "--base", "--database", help=_("La base d'origine, si elle n'est pas à côté du projet.")
    )
    results.add_argument(
        "--langue",
        "--language",
        choices=list(LANGUAGES),
        help=_("Langue du document (défaut : celle de l'interface)."),
    )
    results.set_defaults(handler=cmd_results)

    exclusions_command = commands.add_parser(
        "exclusions",
        help=_(
            "Les règles d'exclusion du projet : lister avec leurs effectifs, ajouter, retirer, "
            "déplacer ; voir les signaux de qualité de la passation."
        ),
    )
    rule_actions = exclusions_command.add_subparsers(dest="action", required=True)
    rules_listed = rule_actions.add_parser(
        "lister",
        aliases=["list"],
        help=_("Lister les règles dans leur ordre, avec combien chacune exclut."),
    )
    rules_listed.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    rule_added = rule_actions.add_parser(
        "ajouter",
        aliases=["add"],
        help=_("Ajouter une règle à la fin de la liste, avec sa raison."),
    )
    rule_added.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    kinds = rule_added.add_mutually_exclusive_group(required=True)
    kinds.add_argument(
        "--condition",
        nargs="+",
        metavar="TERME",
        help=_(
            "Une condition sur une variable : VARIABLE OPÉRATEUR [VALEUR…], p. ex. "
            "« age lt 18 », « consentement eq 2 », « groupe manquant ». Opérateurs : eq, ne, "
            "lt, le, gt, ge, parmi (in), manquant (missing)."
        ),
    )
    kinds.add_argument(
        "--score",
        nargs="+",
        metavar="TERME",
        help=_("Une condition sur le score d'un groupe : GROUPE OPÉRATEUR VALEUR."),
    )
    kinds.add_argument(
        "--completude",
        "--completeness",
        nargs=2,
        metavar=("GROUPE", "MIN"),
        help=_("Moins de MIN items du groupe répondus."),
    )
    kinds.add_argument(
        "--duree",
        "--duration",
        nargs=3,
        metavar=("DEBUT", "FIN", "SECONDES"),
        help=_("Une passation plus courte que SECONDES ; exige --source."),
    )
    kinds.add_argument(
        "--ligne-droite",
        "--straightlining",
        metavar="GROUPE",
        help=_("Tous les items du groupe répondus, avec la même valeur."),
    )
    kinds.add_argument(
        "--doublons",
        "--duplicates",
        nargs="+",
        metavar="VARIABLE",
        help=_("Une réponse qui en répète une autre sur ces variables ; la première est gardée."),
    )
    rule_added.add_argument(
        "--raison", "--reason", required=True, help=_("La raison, en clair, telle que publiée.")
    )
    rule_added.add_argument(
        "--source", help=_("D'où vient la règle ou son seuil (p. ex. un procès-verbal).")
    )
    rule_removed = rule_actions.add_parser(
        "retirer", aliases=["remove"], help=_("Retirer une règle.")
    )
    rule_removed.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    rule_removed.add_argument("numero", help=_("Numéro de la règle, p. ex. E2."))
    rule_moved = rule_actions.add_parser(
        "deplacer", aliases=["move"], help=_("Mettre une règle à un autre rang.")
    )
    rule_moved.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    rule_moved.add_argument("numero", help=_("Numéro de la règle, p. ex. E2."))
    rule_moved.add_argument("rang", type=int, help=_("Son nouveau rang, 1 pour la première."))
    signals = rule_actions.add_parser(
        "signaux",
        aliases=["signals"],
        help=_(
            "Les signaux de qualité de la passation, parmi les personnes que les règles "
            "gardent : durées, lignes droites, doublons. Aucun n'est appliqué."
        ),
    )
    signals.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    signals.add_argument("--debut", "--start", help=_("Variable de la date de début."))
    signals.add_argument("--fin", "--end", help=_("Variable de la date de fin."))
    signals.add_argument(
        "--duree-min",
        "--min-duration",
        type=float,
        metavar="SECONDES",
        help=_("Compter les passations plus courtes que ce seuil, choisi par l'équipe."),
    )
    signals.add_argument(
        "--doublons",
        "--duplicates",
        nargs="+",
        metavar="VARIABLE",
        help=_("Les variables des doublons (défaut : celles que la plateforme désigne)."),
    )
    for action in (rules_listed, rule_added, signals):
        action.add_argument(
            "--base",
            "--database",
            help=_("La base d'origine, si elle n'est pas à côté du projet."),
        )
    exclusions_command.set_defaults(handler=cmd_exclusions)

    advise_command = commands.add_parser(
        "conseiller",
        aliases=["advise"],
        help=_(
            "Demander au modèle local des analyses du catalogue pour un objectif : des "
            "propositions à vérifier, jamais de code, rien n'est calculé."
        ),
    )
    advise_command.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    advise_command.add_argument(
        "objectif",
        help=_(
            "L'objectif de l'analyse, en une ou deux phrases, envoyé tel quel au modèle local. "
            "N'y écrivez aucune donnée de participant."
        ),
    )
    advise_command.add_argument(
        "--apercu",
        "--preview",
        action="store_true",
        help=_("Écrire le message qui serait envoyé, sans rien envoyer."),
    )
    advise_command.add_argument(
        "--modele",
        "--model",
        help=_("Nom du modèle dans le serveur local, p. ex. qwen2.5:7b-instruct-q4_K_M."),
    )
    advise_command.add_argument(
        "--adresse",
        "--address",
        default=DEFAULT_ENDPOINT,
        help=_("Adresse du serveur local compatible OpenAI (défaut : Ollama, {default}).").format(
            default=DEFAULT_ENDPOINT
        ),
    )
    advise_command.set_defaults(handler=cmd_advise)

    questionnaire = commands.add_parser(
        "questionnaire",
        help=_(
            "Lire le questionnaire de l'étude (.pdf, .txt, ou export .xlsx d'une plateforme) "
            "et l'ajouter au projet."
        ),
    )
    questionnaire.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    questionnaire.add_argument(
        "fichier", help=_("Questionnaire (.pdf, .txt, ou export .xlsx d'une plateforme).")
    )
    questionnaire.add_argument(
        "--remplacer",
        "--replace",
        action="store_true",
        help=_("Remplacer le questionnaire déjà lu."),
    )
    questionnaire.set_defaults(handler=cmd_questionnaire)

    rename_command = commands.add_parser(
        "renommer",
        aliases=["rename"],
        help=_(
            "Proposer de nouveaux noms aux variables, par les règles de nommage ; le fichier "
            "d'origine n'est jamais modifié."
        ),
    )
    _model_arguments(
        rename_command,
        _("Renvoyer aussi les questions dont le nom de base a déjà été proposé par le modèle."),
        DEFAULT_STEM_BLOCK_SIZE,
    )
    rename_command.add_argument(
        "--reference",
        help=_(
            "La vague précédente : son fichier projet (.dd.json), sa copie documentée (.sav) "
            "ou sa table de noms (.csv : nom_origine,nouveau_nom)."
        ),
    )
    mark = rename_command.add_mutually_exclusive_group()
    mark.add_argument(
        "--suffixe", "--suffix", help=_("Marque de vague à la fin des noms, par exemple _t2.")
    )
    mark.add_argument(
        "--prefixe", "--prefix", help=_("Marque de vague au début des noms, par exemple t2_.")
    )
    rename_command.set_defaults(handler=cmd_rename)

    enrich = commands.add_parser(
        "enrichir",
        aliases=["enrich"],
        help=_("Faire proposer libellés et descriptions par un modèle local (facultatif)."),
    )
    _model_arguments(enrich, _("Renvoyer aussi les blocs déjà enrichis."), DEFAULT_BLOCK_SIZE)
    enrich.set_defaults(handler=cmd_enrich)

    link = commands.add_parser(
        "rattacher",
        aliases=["link"],
        help=_(
            "Rattacher les variables aux questions du questionnaire : questions candidates, "
            "puis choix proposé par un modèle local (facultatif)."
        ),
    )
    _model_arguments(link, _("Renvoyer aussi les blocs déjà traités."), DEFAULT_LINK_BLOCK_SIZE)
    link.set_defaults(handler=cmd_link)

    bench = commands.add_parser(
        "evaluer",
        aliases=["evaluate"],
        help=_(
            "Mesurer un modèle installé sur les bases fictives de l'outil : rattachements justes, "
            "inventions signalées, durée."
        ),
    )
    bench.add_argument(
        "--modele",
        "--model",
        required=True,
        help=_("Nom du modèle dans le serveur local, p. ex. qwen2.5:7b-instruct-q4_K_M."),
    )
    bench.add_argument(
        "--adresse",
        "--address",
        default=DEFAULT_ENDPOINT,
        help=_("Adresse du serveur local compatible OpenAI (défaut : Ollama, {default}).").format(
            default=DEFAULT_ENDPOINT
        ),
    )
    bench.add_argument(
        "--dossier",
        "--folder",
        default=".",
        help=_("Dossier où écrire le rapport (défaut : le dossier courant)."),
    )
    bench.set_defaults(handler=cmd_bench)

    review = commands.add_parser(
        "reviser",
        aliases=["review"],
        help=_("Ouvrir l'interface de révision dans le navigateur (cet ordinateur seulement)."),
    )
    review.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    review.add_argument(
        "--port", type=int, default=8501, help=_("Port local de l'interface (défaut : 8501).")
    )
    review.set_defaults(handler=cmd_review)
    return parser


def _analysis_arguments(command: argparse.ArgumentParser) -> None:
    """The variables and options of an analysis (`analyser`, `carnet ajouter`)."""
    command.add_argument(
        "analyse",
        choices=list(ANALYSES),
        help=_("tableau1, test_t, anova, khi2, correlation ou regression."),
    )
    command.add_argument("--variables", nargs="+", help=_("Variables (Tableau 1, corrélation)."))
    command.add_argument("--groupe", "--group", nargs=1, help=_("Variable de groupe."))
    command.add_argument(
        "--dependante",
        "--outcome",
        nargs=1,
        help=_("Variable dépendante (test t, ANOVA, régression)."),
    )
    command.add_argument("--lignes", "--rows", nargs=1, help=_("Variable en lignes (khi-carré)."))
    command.add_argument(
        "--colonnes", "--columns", nargs=1, help=_("Variable en colonnes (khi-carré).")
    )
    command.add_argument(
        "--predicteurs", "--predictors", nargs="+", help=_("Prédicteurs (régression).")
    )
    command.add_argument(
        "--methode",
        "--method",
        help=_(
            "welch, student, mann_whitney ; anova, kruskal_wallis ; pearson, fisher, spearman "
            "(défaut : la première de chaque analyse)."
        ),
    )
    command.add_argument(
        "--hypothese", "--alternative", help=_("Test t : two_sided, greater ou less.")
    )
    command.add_argument("--post-hoc", help=_("ANOVA : none ou tukey."))
    command.add_argument(
        "--modalites",
        "--levels",
        help=_("Test t : les deux codes du groupe à comparer, p. ex. 1,3."),
    )


def _model_arguments(command: argparse.ArgumentParser, redo_help: str, block_size: int) -> None:
    """Options shared by the commands that call the local model."""
    command.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    command.add_argument(
        "--apercu",
        "--preview",
        action="store_true",
        help=_("Écrire les messages qui seraient envoyés, sans rien envoyer."),
    )
    command.add_argument(
        "--taille-bloc",
        "--block-size",
        type=int,
        default=block_size,
        help=_("Nombre de variables par message (défaut : {n}).").format(n=block_size),
    )
    command.add_argument(
        "--modele",
        "--model",
        help=_("Nom du modèle dans le serveur local, p. ex. qwen2.5:7b-instruct-q4_K_M."),
    )
    command.add_argument(
        "--adresse",
        "--address",
        default=DEFAULT_ENDPOINT,
        help=_("Adresse du serveur local compatible OpenAI (défaut : Ollama, {default}).").format(
            default=DEFAULT_ENDPOINT
        ),
    )
    command.add_argument("--refaire", "--redo", action="store_true", help=redo_help)


def main(argv: list[str] | None = None) -> int:
    settings.apply()  # the language of this computer, or DDICT_LANG (v0.5)
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except ReadError as error:
        print(_("Impossible de lire la base : {detail}").format(detail=error), file=sys.stderr)
    except ProjectError as error:
        print(_("Impossible de lire le projet : {detail}").format(detail=error), file=sys.stderr)
    except OSError as error:
        print(_("Erreur de fichier : {detail}").format(detail=error), file=sys.stderr)
    return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
