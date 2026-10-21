"""`ddict niveaux` and `ddict codes` (v0.13, step 7): the measure levels and the suspect
missing codes decided on the command line, as on the pages "Base" and "Variables", with the
same functions (`ddict.review.levels`, `ddict.review.logic.decide_sentinel`). The trial on
an open database showed a team could not settle them without the pages.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from ddict.export import wording as w
from ddict.i18n import _
from ddict.project import load_project, save_project
from ddict.project.model import Project, VariableEntry
from ddict.review import levels, logic
from ddict.review.logic import ReviewError

EXIT_ERROR = 2
LEVEL_ACTIONS = {
    "lister": "list",
    "list": "list",
    "accepter": "accept",
    "accept": "accept",
    "rejeter": "reject",
    "reject": "reject",
    "fixer": "set",
    "set": "set",
}
LEVELS = {
    "nominal": "nominal",
    "ordinal": "ordinal",
    "echelle": "scale",
    "échelle": "scale",
    "scale": "scale",
}
CODE_ACTIONS = {
    "lister": "list",
    "list": "list",
    "manquant": "missing",
    "missing": "missing",
    "valeur": "value",
    "value": "value",
    "annuler": "undo",
    "undo": "undo",
}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _entry(project: Project, name: str) -> VariableEntry:
    """A variable by its final name or by its name in the file."""
    for entry in project.variables:
        if name in (w.final_name(entry), entry.name):
            return entry
    raise ReviewError(_("{name} : variable inconnue.").format(name=name))


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return EXIT_ERROR


# --- The measure levels. ---


def level_lines(project: Project, which: str) -> list[str]:
    found = levels.rows(project, which)  # type: ignore[arg-type]
    if not found:
        return [_("Aucun niveau de mesure proposé.")]
    lines = []
    for row in found:
        level = w.MEASURES.get(row.level, _("aucun"))
        state = _("proposé") if row.waiting else row.status
        lines.append(f"{row.name} — {level} ({state}) ; {row.kind}")
    return lines


def cmd_levels(args: argparse.Namespace) -> int:
    path = Path(args.projet)
    project = load_project(path)
    action = LEVEL_ACTIONS[args.action]
    if action == "list":
        for line in level_lines(project, "all" if args.toutes else "proposed"):
            print(line)
        return 0
    try:
        if action == "set":
            entry = _entry(project, args.variable)
            count = levels.apply_table(
                project, {w.final_name(entry): LEVELS[args.niveau]}, {}, now=_now()
            )
        else:
            waiting = [r.name for r in levels.rows(project, "proposed")]
            names = waiting if action == "accept" and args.tout else args.variables
            if not names:
                return _fail(_("Nommez les variables, ou ajoutez --tout."))
            shown = [w.final_name(_entry(project, n)) for n in names]
            count = levels.apply_table(project, {}, {n: action for n in shown}, now=_now())
    except ReviewError as error:
        return _fail(str(error))
    save_project(project, path)
    print(_("Niveaux de mesure décidés : {n}.").format(n=count))
    return 0


# --- The suspect missing codes. ---


def _code(entry: VariableEntry, typed: str):
    """The suspect code of the variable that the team typed ("-1", "999")."""
    for code in entry.suspect_codes:
        if w.code_text(code) == typed.strip():
            return code
        try:
            if not isinstance(code, str) and float(code) == float(typed):
                return code
        except ValueError:
            pass
    raise ReviewError(_("{code} n'est pas un code suspect de cette variable.").format(code=typed))


def code_lines(project: Project) -> list[str]:
    lines = []
    for entry in project.variables:
        decided = {d.code: d.missing for d in entry.sentinel_decisions}
        for code in entry.suspect_codes:
            if code not in decided:
                state = _("à décider")
            elif decided[code]:
                state = _("code manquant")
            else:
                state = _("vraie valeur")
            lines.append(f"{w.final_name(entry)} : {w.code_text(code)} — {state}")
    return lines or [_("Aucun code suspect.")]


def cmd_codes(args: argparse.Namespace) -> int:
    if args.action in ("vides", "blanks"):  # v0.21: the codes of the blanks
        from ddict.cli_conditions import cmd_blank_codes

        return cmd_blank_codes(args)
    path = Path(args.projet)
    project = load_project(path)
    action = CODE_ACTIONS[args.action]
    if action == "list":
        for line in code_lines(project):
            print(line)
        return 0
    missing = {"missing": True, "value": False, "undo": None}[action]
    try:
        for name in args.variables:
            entry = _entry(project, name)
            logic.decide_sentinel(project, entry.name, _code(entry, args.code), missing,
                                  now=_now())  # fmt: skip
    except ReviewError as error:
        return _fail(str(error))
    save_project(project, path)
    print(_("Code {code} décidé pour : {names}.").format(
        code=args.code, names=", ".join(args.variables)))  # fmt: skip
    return 0


def _sub(actions, name: str, alias: str, text: str):
    sub = actions.add_parser(name, aliases=[alias], help=text)
    sub.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    return sub


def add_decisions_parsers(commands) -> None:
    command = commands.add_parser(
        "niveaux",
        aliases=["levels"],
        help=_("Les niveaux de mesure : lister, accepter ou rejeter les propositions, fixer."),
    )
    actions = command.add_subparsers(dest="action", required=True)
    listed = _sub(actions, "lister", "list", _("Les niveaux proposés, ou tous avec --toutes."))
    listed.add_argument("--toutes", "--all", action="store_true", help=_("Toutes les variables."))
    accepted = _sub(actions, "accepter", "accept", _("Accepter des niveaux proposés."))
    accepted.add_argument("variables", nargs="*", help=_("Les variables, par leur nom."))
    accepted.add_argument(
        "--tout", "--all", action="store_true", help=_("Toutes les propositions.")
    )
    rejected = _sub(actions, "rejeter", "reject", _("Rejeter des niveaux proposés."))
    rejected.add_argument("variables", nargs="+", help=_("Les variables, par leur nom."))
    fixed = _sub(actions, "fixer", "set", _("Décider le niveau d'une variable."))
    fixed.add_argument("variable", help=_("La variable, par son nom."))
    fixed.add_argument("niveau", choices=list(LEVELS), help=_("nominal, ordinal ou echelle."))
    command.set_defaults(handler=cmd_levels)

    command = commands.add_parser(
        "codes",
        help=_(
            "Les codes manquants suspects (999, -9…) : lister, dire si c'est un code "
            "manquant ou une vraie valeur, annuler."
        ),
    )
    actions = command.add_subparsers(dest="action", required=True)
    _sub(actions, "lister", "list", _("Les codes suspects et leur décision."))
    for name, alias, text in (
        ("manquant", "missing", _("Ce code est un code manquant.")),
        ("valeur", "value", _("Ce code est une vraie valeur.")),
        ("annuler", "undo", _("Reprendre la décision.")),
    ):
        sub = _sub(actions, name, alias, text)
        sub.add_argument("code", help=_("Le code, p. ex. -1 ou 999."))
        sub.add_argument("variables", nargs="+", help=_("Les variables, par leur nom."))
    from ddict.cli_conditions import add_blank_codes_parser

    add_blank_codes_parser(actions)
    command.set_defaults(handler=cmd_codes)
