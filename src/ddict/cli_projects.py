"""`ddict projets` (v0.17, plan-v0.17 § 6.3): the projects followed, from the command line,
as the home page shows them: list them (the table "Mes projets", in text), follow one,
take one off the list, look for those of a folder.

The list is kept on this computer (`tracked`); no project file is ever written here.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ddict import overview, tracked
from ddict.i18n import N_, _
from ddict.project import PROJECT_SUFFIX, ondisk

EXIT_ERROR = 2
PROJECTS_ACTIONS = {
    "lister": "list",
    "list": "list",
    "suivre": "follow",
    "follow": "follow",
    "retirer": "remove",
    "remove": "remove",
    "chercher": "search",
    "search": "search",
}
COLUMNS = (
    (N_("Projet"), lambda r: r.name),
    (N_("Phase"), overview.phase_text),
    (N_("Codebook"), overview.codebook_text),
    (N_("En attente"), overview.waiting_text),
    (N_("Plan"), overview.plan_text),
    (N_("Carnet"), overview.notebook_text),
    (N_("Base"), overview.base_text),
    (N_("Modifié"), overview.modified_text),
    (N_("Dossier"), lambda r: r.folder),
)


def table(rows: list[overview.ProjectRow]) -> list[str]:
    """The home page's table as lines of text, its columns aligned."""
    cells = [[_(title) for title, _text in COLUMNS]]
    cells += [[text(row) for _title, text in COLUMNS] for row in rows]
    widths = [max(len(line[i]) for line in cells) for i in range(len(COLUMNS))]
    return ["  ".join(c.ljust(w) for c, w in zip(line, widths, strict=True)).rstrip()
            for line in cells]  # fmt: skip


def _list() -> int:
    followed = tracked.load()
    if not followed:
        print(_("Aucun projet suivi. Suivez-en un avec « ddict projets suivre <projet> »."))
        return 0
    for line in table(overview.rows(followed)):
        print(line)
    return 0


def _follow(path: Path) -> int:
    if not path.name.casefold().endswith(PROJECT_SUFFIX) or not path.is_file():
        print(
            _("Pas un fichier projet (.dd.json) existant : {path}").format(path=path),
            file=sys.stderr,
        )
        return EXIT_ERROR
    if tracked.is_followed(path):
        print(_("Déjà suivi : {path}").format(path=path.absolute()))
        return 0
    if not tracked.follow(path):
        print(tracked.not_written(), file=sys.stderr)
        return EXIT_ERROR
    print(_("Projet suivi : {path}").format(path=path.absolute()))
    return 0


def _remove(path: Path) -> int:
    if not tracked.is_followed(path):
        print(_("Ce projet n'était pas suivi : {path}").format(path=path.absolute()))
        return 0
    if not tracked.unfollow(path):
        print(tracked.not_written(), file=sys.stderr)
        return EXIT_ERROR
    print(_("Retiré de la liste, son fichier n'est pas touché : {path}").format(
        path=path.absolute()))  # fmt: skip
    return 0


def _search(folder: Path, follow: bool) -> int:
    if not folder.is_dir():
        print(_("Dossier introuvable : {path}").format(path=folder), file=sys.stderr)
        return EXIT_ERROR
    result = tracked.search(folder)
    followed = {ondisk.key(p) for p in tracked.load()}
    for path in result.found:
        mark = _(" (déjà suivi)") if ondisk.key(path) in followed else ""
        print(f"{path}{mark}")
    if result.stopped == "folders":
        print(_("Recherche arrêtée après 20 000 dossiers : choisissez un dossier plus précis."))
    elif result.stopped == "projects":
        print(_("Recherche arrêtée après 500 projets : choisissez un dossier plus précis."))
    new = [p for p in result.found if ondisk.key(p) not in followed]
    if not result.found:
        print(_("Aucun projet dans ce dossier ni dans ses sous-dossiers (4 niveaux)."))
    elif not follow:
        print(
            _(
                "{n} projets trouvés, {k} non suivis. Rien n'est ajouté : relancez avec "
                "--suivre pour les suivre tous, ou suivez-en un avec « ddict projets suivre »."
            ).format(n=len(result.found), k=len(new))
        )
    elif not tracked.follow_all(new):
        print(tracked.not_written(), file=sys.stderr)
        return EXIT_ERROR
    else:
        text = _("1 projet suivi.") if len(new) == 1 else _("{n} projets suivis.")
        print(text.format(n=len(new)))
    return 0


def cmd_projects(args: argparse.Namespace) -> int:
    action = PROJECTS_ACTIONS[args.action]
    if action == "list":
        return _list()
    if action == "follow":
        return _follow(Path(args.fichier))
    if action == "remove":
        return _remove(Path(args.fichier))
    return _search(Path(args.dossier), args.suivre)


def add_projects_parser(commands) -> None:
    command = commands.add_parser(
        "projets",
        aliases=["projects"],
        help=_(
            "Les projets suivis sur cet ordinateur, comme le tableau « Mes projets » de "
            "l'accueil : lister, suivre, retirer, chercher dans un dossier."
        ),
    )
    actions = command.add_subparsers(dest="action", required=True)
    actions.add_parser(
        "lister",
        aliases=["list"],
        help=_("Le tableau des projets suivis : phase, codebook, en attente, plan, carnet…"),
    )
    followed = actions.add_parser(
        "suivre", aliases=["follow"], help=_("Ajouter un fichier projet à la liste.")
    )
    followed.add_argument("fichier", help=_("Fichier projet (.dd.json)."))
    removed = actions.add_parser(
        "retirer",
        aliases=["remove"],
        help=_("Retirer un projet de la liste, trouvé ou non ; son fichier n'est pas touché."),
    )
    removed.add_argument("fichier", help=_("Fichier projet (.dd.json)."))
    searched = actions.add_parser(
        "chercher",
        aliases=["search"],
        help=_(
            "Chercher les fichiers projet d'un dossier et de ses sous-dossiers (4 niveaux), "
            "sans les ouvrir."
        ),
    )
    searched.add_argument("dossier", help=_("Le dossier où chercher."))
    searched.add_argument(
        "--suivre",
        "--follow",
        action="store_true",
        help=_("Suivre tous les projets trouvés ; sans cette option, rien n'est ajouté."),
    )
    command.set_defaults(handler=cmd_projects)
