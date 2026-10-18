"""`ddict recoder` (v0.15, step 3, D-120): the recodings on the command line, as on the pages
"Variables" and "Groupes", with the same functions (`ddict.project.recodes`,
`ddict.analysis.recode.prepared_rule`): list, regroup categories, cut a number into classes,
remove. A recoding is checked on the database before it is kept: the counts of its new
categories are shown.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ddict.analysis.data import DataError, find_database
from ddict.analysis.recode import prepared_rule
from ddict.i18n import _
from ddict.io import read_database
from ddict.project import load_project, recodes, save_project
from ddict.project.recodes import RecodeRefused

EXIT_ERROR = 2
ACTIONS = {
    "lister": "list",
    "list": "list",
    "regrouper": "groups",
    "group": "groups",
    "decouper": "classes",
    "découper": "classes",
    "cut": "classes",
    "retirer": "remove",
    "remove": "remove",
}
LEVELS = {"nominal": "nominal", "ordinal": "ordinal"}


def _fail(lines: list[str]) -> int:
    for line in lines:
        print(line, file=sys.stderr)
    return EXIT_ERROR


def _value(text: str):
    """A source value as typed: a number where it reads as one, else the text."""
    text = text.strip()
    try:
        number = float(text)
    except ValueError:
        return text
    return int(number) if number.is_integer() else number


def recode_lines(project) -> list[str]:
    from ddict.export import wording as w

    rows = w.recode_rows(project)
    if not rows:
        return [_("Aucun recodage.")]
    return [
        f"{rule_id} — {name} ({level}) : {label}. "
        + _("Tirée de {source} : {parts}. Raison : {reason}").format(
            source=source, parts=parts, reason=reason
        )
        for rule_id, name, label, level, source, parts, reason in rows
    ]


def _fields(project, args: argparse.Namespace, kind: str) -> dict:
    source = recodes.reference(project, args.source)
    fields: dict = {
        "kind": kind,
        "source": source.model_dump(),
        "name": args.nom,
        "label": args.libelle or args.nom,
        "reason": args.raison,
    }
    if kind == "groups":
        fields["level"] = LEVELS[args.niveau]
        fields["groups"] = [
            {"code": i, "label": label, "values": [_value(v) for v in values.split(",")]}
            for i, (values, label) in enumerate(args.groupe or [], start=1)
        ]
        fields["missing_values"] = [_value(v) for v in args.manquant or []]
    else:
        fields["cuts"] = args.seuils
        fields["labels"] = args.etiquettes or recodes.default_labels(args.seuils)
    return fields


def cmd_recode(args: argparse.Namespace) -> int:
    path = Path(args.projet)
    project = load_project(path)
    action = ACTIONS[args.action]
    if action == "list":
        for line in recode_lines(project):
            print(line)
        return 0
    try:
        if action == "remove":
            recodes.remove(project, args.recodage)
            save_project(project, path)
            print(_("Recodage retiré : {id}.").format(id=args.recodage))
            return 0
        table = read_database(find_database(project, path, args.base)).table
        rule, found = prepared_rule(project, table, _fields(project, args, action),
                                    args.remplacer)  # fmt: skip
    except RecodeRefused as refused:
        return _fail(refused.reasons)
    except DataError as error:
        return _fail([_("Base introuvable ou différente du projet : {detail}").format(
            detail=error.detail or error.reason)])  # fmt: skip
    if args.remplacer:
        recodes.replace(project, rule)
    else:
        recodes.add(project, rule)
    save_project(project, path)
    print(_("Recodage enregistré : {id} ({name}).").format(id=rule.id, name=rule.name))
    for label, n in found.counts:
        print(f"  {label} : n = {n}")
    for warning in found.warnings:
        print(_("Avertissement : {text}").format(text=warning))
    return 0


def _common(sub) -> None:
    sub.add_argument("source", help=_("La variable source, par son nom (ou un score)."))
    sub.add_argument("--nom", "--name", required=True, help=_("Le nom de la nouvelle variable."))
    sub.add_argument("--libelle", "--label", help=_("Son libellé (par défaut, son nom)."))
    sub.add_argument("--raison", "--reason", required=True, help=_("La raison, en clair."))
    sub.add_argument(
        "--remplacer",
        "--replace",
        metavar="R1",
        help=_("Changer ce recodage au lieu d'en créer un."),
    )
    sub.add_argument("--base", "--database", help=_("La base, si elle n'est pas à côté du projet."))


def add_recode_parser(commands) -> None:
    command = commands.add_parser(
        "recoder",
        aliases=["recode"],
        help=_(
            "Les recodages : lister, regrouper des modalités, découper un nombre en classes, "
            "retirer."
        ),
    )
    actions = command.add_subparsers(dest="action", required=True)
    listed = actions.add_parser("lister", aliases=["list"], help=_("Les recodages du projet."))
    listed.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    grouped = actions.add_parser(
        "regrouper", aliases=["group"], help=_("Regrouper les modalités d'une variable.")
    )
    grouped.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    _common(grouped)
    grouped.add_argument(
        "--groupe",
        "--group",
        nargs=2,
        action="append",
        metavar=("VALEURS", "ETIQUETTE"),
        help=_(
            "Un groupe : ses valeurs séparées par des virgules, puis son étiquette, p. ex. "
            '--groupe "2,3" "Homme ou autre" ; codes 1, 2… dans l\'ordre.'
        ),
    )
    grouped.add_argument(
        "--manquant", "--missing", nargs="+", help=_("Des valeurs qui deviennent manquantes.")
    )
    grouped.add_argument(
        "--niveau", "--level", choices=list(LEVELS), default="nominal",
        help=_("nominal (par défaut) ou ordinal."),
    )  # fmt: skip
    cut = actions.add_parser(
        "decouper", aliases=["découper", "cut"], help=_("Découper un nombre en classes.")
    )
    cut.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    _common(cut)
    cut.add_argument(
        "--seuils", "--cuts", nargs="+", type=float, required=True,
        help=_("Les seuils, croissants ; une classe va de son seuil inclus au suivant exclu."),
    )  # fmt: skip
    cut.add_argument(
        "--etiquettes", "--labels", nargs="+",
        help=_("Une étiquette par classe (par défaut : « moins de 30 », « 30 à moins de 45 »…)."),
    )  # fmt: skip
    removed = actions.add_parser("retirer", aliases=["remove"], help=_("Retirer un recodage."))
    removed.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    removed.add_argument("recodage", help=_("Son numéro, p. ex. R1."))
    command.set_defaults(handler=cmd_recode)
