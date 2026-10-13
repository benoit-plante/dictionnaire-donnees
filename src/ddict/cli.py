"""Command line: `ddict profiler`, `ddict exporter` and `ddict enrichir`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ddict.export import write_markdown, write_xlsx
from ddict.i18n import _
from ddict.io import ReadError, read_database
from ddict.llm import DEFAULT_BLOCK_SIZE, PROMPT_VERSION, build_blocks
from ddict.privacy import MIN_CELL_COUNT
from ddict.project import (
    PROJECT_SUFFIX,
    ProjectError,
    build_project,
    load_project,
    save_project,
)

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
    flagged = sum(
        1
        for e in project.variables
        if e.profile.unlabeled_codes
        or e.profile.suspect_missing_codes
        or e.profile.unused_labels
        or e.profile.flags
    )
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


def _exchange_dir(project_path: Path) -> Path:
    """Where what is (or would be) sent to the model is kept, next to the project."""
    return project_path.with_name(_strip_project_suffix(project_path) + ".dd-envois")


def cmd_enrich(args: argparse.Namespace) -> int:
    project_path = Path(args.projet)
    project = load_project(project_path)
    if not args.apercu:
        print(
            _("L'envoi au modèle n'est pas encore disponible : utilisez --apercu."),
            file=sys.stderr,
        )
        return EXIT_ERROR
    blocks = build_blocks(project, size=args.taille_bloc)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ddict",
        description=_("Création de dictionnaires de données, en local."),
    )
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
    enrich.set_defaults(handler=cmd_enrich)
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
