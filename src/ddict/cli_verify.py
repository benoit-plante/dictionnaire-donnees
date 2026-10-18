"""`ddict verifier` (v0.15, step 5, D-117, D-118): check the figures of a Word manuscript
against what the tool writes, and write the report and the commented copy next to it.
Without the database, the comparison is with the values the notebook keeps. And `ddict
deposer` (step 6, D-119): the reproduction package, next to the project.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ddict.analysis import notebook as nb
from ddict.analysis import verify
from ddict.analysis.data import DataError, prepare
from ddict.i18n import _
from ddict.project import load_project

EXIT_ERROR = 2


def cmd_verify(args: argparse.Namespace) -> int:
    path = Path(args.projet)
    manuscript = Path(args.manuscrit)
    if manuscript.suffix.lower() != ".docx" or not manuscript.is_file():
        print(_("{name} : un fichier Word (.docx) introuvable.").format(name=manuscript),
              file=sys.stderr)  # fmt: skip
        return EXIT_ERROR
    project = load_project(path)
    try:
        prepared = prepare(project, path, Path(args.base) if args.base else None)
    except DataError:
        prepared = None
    notebook = nb.open_notebook(project, path)
    result = verify.verify(project, prepared, notebook, manuscript)
    for line in verify.summary_lines(result):
        print(line)
    for row in verify.rows(result):
        if row[-1] != verify.CLASSES["agrees"]:
            print("  " + " — ".join(cell for cell in row if cell))
    for written in verify.write(result, manuscript):
        print(_("Fichier écrit : {path}").format(path=written))
    return 0


def add_verify_parser(commands) -> None:
    command = commands.add_parser(
        "verifier",
        aliases=["verify"],
        help=_(
            "Vérifier les chiffres d'un manuscrit Word face à ce que l'outil écrit : un "
            "rapport et une copie commentée, à côté du manuscrit."
        ),
    )
    command.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    command.add_argument("manuscrit", help=_("Le manuscrit, un fichier Word (.docx)."))
    command.add_argument(
        "--base", "--database", help=_("La base, si elle n'est pas à côté du projet.")
    )
    command.set_defaults(handler=cmd_verify)


def cmd_deposit(args: argparse.Namespace) -> int:
    from ddict.analysis import deposit
    from ddict.analysis.notebook_check import waiting_text
    from ddict.analysis.notebook_export import ExportBlocked

    path = Path(args.projet)
    project = load_project(path)
    notebook_file = nb.notebook_path(path)
    if not notebook_file.is_file():
        print(_("Aucune analyse retenue dans le carnet."), file=sys.stderr)
        return EXIT_ERROR
    notebook = nb.load_notebook(notebook_file)
    try:
        prepared = prepare(project, path, Path(args.base) if args.base else None)
    except DataError:
        prepared = None
    try:
        target, files = deposit.write_deposit(project, prepared, notebook, path,
                                              language=args.langue)  # fmt: skip
    except deposit.DepositError as error:
        print(str(error), file=sys.stderr)
        return EXIT_ERROR
    except ExportBlocked as error:
        print(
            _("À confirmer avant de préparer le paquet : {ids} (« ddict carnet confirmer »).")
            .format(ids=waiting_text(error.ids)),
            file=sys.stderr,
        )  # fmt: skip
        return EXIT_ERROR
    print(_("Paquet de reproduction écrit : {path}").format(path=target))
    for name in files:
        print(f"  {name}")
    print(_("La base n'y est pas : déposez-la, ou non, selon votre certificat d'éthique."))
    return 0


def add_deposit_parser(commands) -> None:
    command = commands.add_parser(
        "deposer",
        aliases=["déposer", "deposit"],
        help=_(
            "Préparer le paquet de reproduction (codebook, plan, carnet, scripts, README), "
            "sans la base, à côté du projet."
        ),
    )
    command.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    command.add_argument(
        "--base", "--database", help=_("La base, si elle n'est pas à côté du projet.")
    )
    command.add_argument(
        "--langue", "--language", choices=["fr", "en"], help=_("La langue du paquet.")
    )
    command.set_defaults(handler=cmd_deposit)
