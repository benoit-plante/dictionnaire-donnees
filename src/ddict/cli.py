"""Command line: `ddict profiler`, `exporter`, `documenter`, `questionnaire`, `enrichir`,
`rattacher`, `evaluer`, `analyser`, `conseiller`, `reviser`."""

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
OPTION_ARGUMENTS = {
    "method": "methode",
    "alternative": "hypothese",
    "post_hoc": "post_hoc",
    "levels": "modalites",
}


def cmd_analyse(args: argparse.Namespace) -> int:
    # Imported here: SciPy and statsmodels load only for an analysis.
    from ddict.analysis.compute import AnalysisRefused, run
    from ddict.analysis.data import DataError, prepare
    from ddict.analysis.report import write_report

    project_path = Path(args.projet)
    project = load_project(project_path)
    key = ANALYSES[args.analyse]
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
    try:
        prepared = prepare(project, project_path, Path(args.base) if args.base else None)
    except DataError as error:
        print(copy_error_text(error, project.source.name), file=sys.stderr)
        return EXIT_ERROR
    try:
        result = run(project, prepared, key, chosen, options)
    except AnalysisRefused as error:
        print(_("Analyse refusée :"), file=sys.stderr)
        for reason in error.check.refusals:
            print(f"- {reason}", file=sys.stderr)
        return EXIT_ERROR
    print(result.sentence)
    for warning in result.warnings:
        print(_("Avertissement : {text}").format(text=warning))
    files = analysis_files(project_path)
    today = datetime.now().date().isoformat()
    for path in write_report(project, prepared, result, files, project_stem(project_path), today):
        print(_("Fichier écrit : {path}").format(path=path))
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
    analyse.add_argument(
        "analyse",
        choices=list(ANALYSES),
        help=_("tableau1, test_t, anova, khi2, correlation ou regression."),
    )
    analyse.add_argument("--variables", nargs="+", help=_("Variables (Tableau 1, corrélation)."))
    analyse.add_argument("--groupe", "--group", nargs=1, help=_("Variable de groupe."))
    analyse.add_argument(
        "--dependante",
        "--outcome",
        nargs=1,
        help=_("Variable dépendante (test t, ANOVA, régression)."),
    )
    analyse.add_argument("--lignes", "--rows", nargs=1, help=_("Variable en lignes (khi-carré)."))
    analyse.add_argument(
        "--colonnes", "--columns", nargs=1, help=_("Variable en colonnes (khi-carré).")
    )
    analyse.add_argument(
        "--predicteurs", "--predictors", nargs="+", help=_("Prédicteurs (régression).")
    )
    analyse.add_argument(
        "--methode",
        "--method",
        help=_(
            "welch, student, mann_whitney ; anova, kruskal_wallis ; pearson, fisher, spearman "
            "(défaut : la première de chaque analyse)."
        ),
    )
    analyse.add_argument(
        "--hypothese", "--alternative", help=_("Test t : two_sided, greater ou less.")
    )
    analyse.add_argument("--post-hoc", help=_("ANOVA : none ou tukey."))
    analyse.add_argument(
        "--modalites",
        "--levels",
        help=_("Test t : les deux codes du groupe à comparer, p. ex. 1,3."),
    )
    analyse.add_argument(
        "--base", "--database", help=_("La base d'origine, si elle n'est pas à côté du projet.")
    )
    analyse.set_defaults(handler=cmd_analyse)

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
