"""`ddict conditions` (v0.21, step 8, D-168): a variable's condition on the command line, as on
the page of a variable, with the same functions (`ddict.project.asked`): list (with how many
were asked each variable, when the database is next to the project), set, remove, accept or
reject one read in a LimeSurvey file.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from ddict.analysis.data import DataError, find_database
from ddict.arrival import count_text
from ddict.i18n import _
from ddict.io import read_database
from ddict.project import asked, load_project, save_project, skip
from ddict.project.decisions import is_accepted
from ddict.project.model import Condition, Term

EXIT_ERROR = 2
# The operators as typed; on PowerShell, "<", ">" and their kin go between quotes.
OPERATORS = {
    "=": "eq", "==": "eq", "eq": "eq",
    "!=": "ne", "≠": "ne", "ne": "ne",
    "parmi": "in", "in": "in",
    "pas-parmi": "not_in", "not_in": "not_in",
    "<": "lt", "lt": "lt", "<=": "le", "le": "le",
    ">": "gt", "gt": "gt", ">=": "ge", "ge": "ge",
    "cochee": "checked", "cochée": "checked", "checked": "checked",
    "repondue": "answered", "répondue": "answered", "answered": "answered",
}  # fmt: skip


def _fail(lines: list[str]) -> int:
    for line in lines:
        print(line, file=sys.stderr)
    return EXIT_ERROR


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _term(words: list[str]) -> Term:
    """ "enfants = 1", "enfants parmi 1 2", "age >= 18", "transport_1 cochee"."""
    if len(words) < 2 or words[1] not in OPERATORS:
        raise asked.AskedError(
            [_("Terme illisible : {words}. Exemple : --terme enfants = 1").format(
                words=" ".join(words))]
        )  # fmt: skip
    operator = OPERATORS[words[1]]
    values = words[2:]
    if operator in ("checked", "answered"):
        value = None
    elif operator in ("in", "not_in"):
        value = values
    elif len(values) == 1:
        value = values[0]
    else:
        raise asked.AskedError(
            [_("Le terme « {words} » attend une valeur.").format(words=" ".join(words))]
        )
    return Term(target=words[0], operator=operator, value=value)


def lines(project, path: Path, base: str | None = None) -> list[str]:
    """Each variable with a condition: the condition, who decided it, and its counts."""
    found = [e for e in project.variables if e.asked_if is not None and e.asked_if.value]
    if not found:
        return [_("Aucune condition déclarée.")]
    counts = {}
    try:
        table = read_database(find_database(project, path, Path(base) if base else None)).table
        counts = skip.counts(project, table)
    except DataError:
        pass
    origins = {
        "human": _("tapée par l'équipe"),
        "computed": _("tirée du questionnaire conçu"),
        "questionnaire": _("lue dans LimeSurvey"),
    }
    out = []
    n = project.settings.min_cell_count
    for entry in found:
        state = origins.get(entry.asked_if.origin, entry.asked_if.origin)
        if not is_accepted(entry.asked_if):
            state += ", " + (_("proposée") if entry.asked_if.status == "proposed" else _("rejetée"))
        line = f"{entry.name} — {skip.variable_text(project, entry.asked_if.value)} ({state})"
        if entry.name in counts:
            c = counts[entry.name]
            line += " — " + _(
                "posée à {asked}, non applicable {na}, manquant {missing}, anomalies {anomalies}"
            ).format(
                asked=count_text(c.asked, n), na=count_text(c.not_applicable, n),
                missing=count_text(c.missing, n), anomalies=count_text(c.anomalies, n),
            )  # fmt: skip
        out.append(line)
    return out


def cmd_conditions(args: argparse.Namespace) -> int:
    path = Path(args.projet)
    project = load_project(path)
    if args.action in ("lister", "list"):
        for line in lines(project, path, args.base):
            print(line)
        return 0
    try:
        if args.action in ("poser", "set"):
            terms = [_term(words) for words in args.terme]
            condition = Condition(combine="any" if args.ou else "all", terms=terms)
            asked.set_asked_if(project, args.variable, [condition], now=_now())
            done = _("Condition enregistrée pour : {names}.")
        elif args.action in ("retirer", "remove"):
            asked.set_asked_if(project, args.variable, None, now=_now())
            done = _("Condition retirée pour : {names}.")
        else:
            action = "accept" if args.action in ("accepter", "accept") else "reject"
            for name in args.variable:
                asked.decide(project, name, action, now=_now())
            done = _("Décision enregistrée pour : {names}.")
    except asked.AskedError as refused:
        return _fail(refused.reasons)
    except ValueError as error:  # a condition of more than 10 terms
        return _fail([str(error)])
    save_project(project, path)
    print(done.format(names=", ".join(args.variable)))
    return 0


def add_conditions_parser(commands) -> None:
    command = commands.add_parser(
        "conditions",
        help=_(
            "Quand une variable est posée : lister, poser, retirer, accepter ou rejeter une "
            "condition."
        ),
    )
    actions = command.add_subparsers(dest="action", required=True)
    listed = actions.add_parser("lister", aliases=["list"], help=_("Les conditions du projet."))
    listed.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    listed.add_argument(
        "--base", "--database", help=_("La base, si elle n'est pas à côté du projet.")
    )
    set_ = actions.add_parser("poser", aliases=["set"], help=_("Poser une condition."))
    set_.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    set_.add_argument(
        "--variable", action="append", required=True,
        help=_("Une variable qui reçoit la condition ; à répéter (les énoncés d'une grille)."),
    )  # fmt: skip
    set_.add_argument(
        "--terme", "--term", nargs="+", action="append", required=True,
        metavar="MOT",
        help=_(
            "Un terme : la variable visée, l'opérateur (=, !=, parmi, pas-parmi, <, <=, >, >=, "
            "cochee, repondue), puis la valeur ou les codes ; à répéter. Sous PowerShell, mettez "
            "< et > entre guillemets."
        ),
    )  # fmt: skip
    set_.add_argument(
        "--ou", "--or", action="store_true",
        help=_("Les termes reliés par « ou » (par défaut : « et »)."),
    )  # fmt: skip
    for name, aliases, text in (
        ("retirer", ["remove"], _("Retirer la condition (la variable est toujours posée).")),
        ("accepter", ["accept"], _("Accepter une condition lue dans LimeSurvey.")),
        ("rejeter", ["reject"], _("Rejeter une condition lue dans LimeSurvey.")),
    ):
        sub = actions.add_parser(name, aliases=aliases, help=text)
        sub.add_argument("projet", help=_("Fichier projet (.dd.json)."))
        sub.add_argument(
            "--variable", action="append", required=True, help=_("La variable ; à répéter.")
        )
    command.set_defaults(handler=cmd_conditions)
