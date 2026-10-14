"""Command line: `ddict profiler`, `exporter`, `questionnaire`, `enrichir`, `reviser`."""

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

from ddict import __version__
from ddict.export import write_markdown, write_xlsx
from ddict.export.wording import anomalies
from ddict.i18n import _
from ddict.io import ReadError, read_database
from ddict.llm import DEFAULT_BLOCK_SIZE, PROMPT_VERSION, build_blocks
from ddict.llm.defaults import DEFAULT_ENDPOINT
from ddict.privacy import MIN_CELL_COUNT
from ddict.project import (
    PROJECT_SUFFIX,
    ProjectError,
    build_project,
    load_project,
    save_project,
)
from ddict.questionnaire import load_questionnaire

EXIT_ERROR = 2


def _default_project_path(database: Path) -> Path:
    return database.with_name(database.stem + PROJECT_SUFFIX)


def _strip_project_suffix(path: Path) -> str:
    name = path.name
    return name[: -len(PROJECT_SUFFIX)] if name.endswith(PROJECT_SUFFIX) else path.stem


def cmd_profile(args: argparse.Namespace) -> int:
    database = Path(args.base)
    output = Path(args.sortie) if args.sortie else _default_project_path(database)
    if output.exists() and not args.remplacer:
        print(
            _("Le projet {path} existe déjà. Utilisez --remplacer pour l'écraser.").format(
                path=output
            ),
            file=sys.stderr,
        )
        return EXIT_ERROR
    data = read_database(database)
    project = build_project(data, min_cell_count=args.seuil)
    save_project(project, output)

    sensitive = sum(
        1 for e in project.variables if (e.privacy.privacy_class.value or "ordinary") != "ordinary"
    )
    # The same count as the "Avec signalements" filter of the review (notes excluded).
    flagged = sum(1 for e in project.variables if anomalies(e.profile))
    print(_("Projet créé : {path}").format(path=output))
    print(
        _(
            "{n} variables, {rows} lignes ; {sensitive} variables sensibles ; "
            "{flagged} avec signalements."
        ).format(
            n=len(project.variables),
            rows=project.source.n_rows,
            sensitive=sensitive,
            flagged=flagged,
        )
    )
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    project_path = Path(args.projet)
    project = load_project(project_path)
    kind = "work" if args.travail else "final"
    stem = _strip_project_suffix(project_path) + ("-travail" if args.travail else "")
    xlsx = Path(args.xlsx) if args.xlsx else project_path.with_name(stem + ".xlsx")
    markdown = Path(args.md) if args.md else project_path.with_name(stem + ".md")
    write_xlsx(project, xlsx, kind=kind)
    write_markdown(project, markdown, kind=kind)
    print(_("Codebook Excel : {path}").format(path=xlsx))
    print(_("Rapport Markdown : {path}").format(path=markdown))
    return 0


TO_CHECK = {
    "grid_header_unclear": _("titres de colonnes collés"),
    "grid_without_header": _("grille sans titres de colonnes"),
    "grid_rows_unnumbered": _("énoncés de grille non numérotés"),
}
KINDS = {
    "open": _("ouvertes"),
    "single": _("à choix unique"),
    "checkbox": _("à cocher"),
    "grid": _("grilles"),
}


def cmd_questionnaire(args: argparse.Namespace) -> int:
    project_path = Path(args.projet)
    project = load_project(project_path)
    if project.questionnaire is not None and not args.remplacer:
        print(
            _(
                "Le projet a déjà un questionnaire ({name}). Utilisez --remplacer pour le "
                "remplacer."
            ).format(name=project.questionnaire.file_name),
            file=sys.stderr,
        )
        return EXIT_ERROR
    try:
        questionnaire = load_questionnaire(args.fichier)
    except ReadError as error:
        print(
            _("Impossible de lire le questionnaire : {detail}").format(detail=error),
            file=sys.stderr,
        )
        return EXIT_ERROR
    project.questionnaire = questionnaire
    save_project(project, project_path)

    questions = questionnaire.questions
    pages = _(" ({n} pages)").format(n=questionnaire.n_pages) if questionnaire.n_pages else ""
    print(_("Questionnaire lu : {name}{pages}").format(name=questionnaire.file_name, pages=pages))
    counts = ", ".join(
        f"{sum(1 for q in questions if q.kind == kind)} {label}"
        for kind, label in KINDS.items()
        if any(q.kind == kind for q in questions)
    )
    rows = sum(len(q.rows) for q in questions)
    grids = _(" ; {n} énoncés de grille").format(n=rows) if rows else ""
    summary = _("{n} questions : {counts}{grids}.")
    print(summary.format(n=len(questions), counts=counts, grids=grids))
    for question in questions:
        if question.to_check:
            reasons = ", ".join(TO_CHECK.get(code, code) for code in question.to_check)
            check = _("À vérifier : {qid} ({reasons}).")
            print(check.format(qid=question.question_id, reasons=reasons))
    print(_("Enregistré dans {path}.").format(path=project_path))
    return 0


def _exchange_dir(project_path: Path) -> Path:
    """Where what is (or would be) sent to the model is kept, next to the project."""
    return project_path.with_name(_strip_project_suffix(project_path) + ".dd-envois")


def cmd_enrich(args: argparse.Namespace) -> int:
    project_path = Path(args.projet)
    project = load_project(project_path)
    if args.apercu:
        return _preview(project, project_path, args.taille_bloc)
    if not args.modele:
        print(_("Indiquez le modèle avec --modele, ou utilisez --apercu."), file=sys.stderr)
        return EXIT_ERROR
    try:
        from ddict.llm.client import EndpointRefused, LocalModelClient
        from ddict.llm.enrich import enrich
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
        events = enrich(
            project,
            client,
            now=lambda: datetime.now().isoformat(timespec="seconds"),
            block_size=args.taille_bloc,
            redo=args.refaire,
            save=lambda p: save_project(p, project_path),
            log_dir=_exchange_dir(project_path),
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
    if last == "connection":
        print(
            _("Le serveur {endpoint} ne répond pas. Ollama est-il lancé ?").format(
                endpoint=client.endpoint
            ),
            file=sys.stderr,
        )
    elif last == "http_404":
        print(
            _(
                "Le modèle « {model} » est introuvable sur le serveur. "
                "Avec Ollama, téléchargez-le d'abord : ollama pull {model}"
            ).format(model=args.modele),
            file=sys.stderr,
        )
    if succeeded:
        print(_("Propositions enregistrées dans {path}, à réviser.").format(path=project_path))
    elif failed:
        print(_("Aucune nouvelle proposition."), file=sys.stderr)
    return EXIT_ERROR if failed else 0


def _preview(project, project_path: Path, block_size: int) -> int:
    blocks = build_blocks(project, size=block_size)
    folder = _exchange_dir(project_path) / "apercu"
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("b-*.json"):
        old.unlink()
    for block in blocks:
        record = {
            "prompt_version": PROMPT_VERSION,
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


def review_command(project_path: Path, port: int) -> tuple[list[str], dict[str, str]]:
    """The Streamlit command and environment: this computer only, no usage statistics."""
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
        "--",
        str(project_path.resolve()),
    ]
    env = {
        **os.environ,
        "STREAMLIT_SERVER_ADDRESS": REVIEW_HOST,
        "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
    }
    return command, env


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
    if importlib.util.find_spec("streamlit") is None:
        print(
            _(
                "L'interface de révision n'est pas installée. Installez-la avec : "
                'uv tool install --reinstall ".[ia,revision]" (voir docs/installation-windows.md).'
            ),
            file=sys.stderr,
        )
        return EXIT_ERROR
    command, env = review_command(project_path, args.port)
    print(
        _(
            "Révision sur http://{host}:{port} (cet ordinateur seulement). Ctrl+C pour arrêter."
        ).format(host=REVIEW_HOST, port=args.port)
    )
    process = subprocess.Popen(command, env=env)
    try:
        if _wait_for_port(REVIEW_HOST, args.port, process):
            webbrowser.open(f"http://{REVIEW_HOST}:{args.port}")
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ddict",
        description=_("Création de dictionnaires de données, en local."),
    )
    parser.add_argument("--version", action="version", version=f"ddict {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    profile = commands.add_parser(
        "profiler",
        help=_("Lire une base (.sav ou .csv) et créer le fichier projet."),
    )
    profile.add_argument("base", help=_("Base de données (.sav, .zsav ou .csv)."))
    profile.add_argument(
        "-o",
        "--sortie",
        help=_("Fichier projet à créer (par défaut : à côté de la base, en .dd.json)."),
    )
    profile.add_argument(
        "--seuil",
        type=int,
        default=MIN_CELL_COUNT,
        help=_("Effectif minimal affiché ; en dessous, il est masqué (défaut : 5)."),
    )
    profile.add_argument("--remplacer", action="store_true", help=_("Écraser un projet existant."))
    profile.set_defaults(handler=cmd_profile)

    export = commands.add_parser(
        "exporter", help=_("Produire le codebook Excel et le rapport Markdown d'un projet.")
    )
    export.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    export.add_argument("--xlsx", help=_("Codebook Excel à écrire."))
    export.add_argument("--md", help=_("Rapport Markdown à écrire."))
    export.add_argument(
        "--travail",
        action="store_true",
        help=_("Inclure les propositions de l'IA en attente, marquées comme telles."),
    )
    export.set_defaults(handler=cmd_export)

    questionnaire = commands.add_parser(
        "questionnaire",
        help=_("Lire le questionnaire de l'étude (.pdf ou .txt) et l'ajouter au projet."),
    )
    questionnaire.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    questionnaire.add_argument("fichier", help=_("Questionnaire (.pdf ou .txt)."))
    questionnaire.add_argument(
        "--remplacer", action="store_true", help=_("Remplacer le questionnaire déjà lu.")
    )
    questionnaire.set_defaults(handler=cmd_questionnaire)

    enrich = commands.add_parser(
        "enrichir",
        help=_("Faire proposer libellés et descriptions par un modèle local (facultatif)."),
    )
    enrich.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    enrich.add_argument(
        "--apercu",
        action="store_true",
        help=_("Écrire les messages qui seraient envoyés, sans rien envoyer."),
    )
    enrich.add_argument(
        "--taille-bloc",
        type=int,
        default=DEFAULT_BLOCK_SIZE,
        help=_("Nombre de variables par message (défaut : 12)."),
    )
    enrich.add_argument(
        "--modele",
        help=_("Nom du modèle dans le serveur local, p. ex. qwen2.5:7b-instruct-q4_K_M."),
    )
    enrich.add_argument(
        "--adresse",
        default=DEFAULT_ENDPOINT,
        help=_("Adresse du serveur local compatible OpenAI (défaut : Ollama, {default}).").format(
            default=DEFAULT_ENDPOINT
        ),
    )
    enrich.add_argument(
        "--refaire",
        action="store_true",
        help=_("Renvoyer aussi les blocs déjà enrichis."),
    )
    enrich.set_defaults(handler=cmd_enrich)

    review = commands.add_parser(
        "reviser",
        help=_("Ouvrir l'interface de révision dans le navigateur (cet ordinateur seulement)."),
    )
    review.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    review.add_argument(
        "--port", type=int, default=8501, help=_("Port local de l'interface (défaut : 8501).")
    )
    review.set_defaults(handler=cmd_review)
    return parser


def main(argv: list[str] | None = None) -> int:
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
