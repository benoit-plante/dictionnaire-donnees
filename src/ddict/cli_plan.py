"""`ddict plan` (v0.13, step 6): the analysis plan of a project from the command line, as
the page "Plan" writes it: list, add, modify (or amend), remove, move the hypotheses,
set the general rules, freeze, clear, and write the preregistration.

After the plan is frozen, every change needs `--raison` and becomes an amendment (D-102);
the notebook then follows the plan (`plan_notebook.sync`).
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from ddict.i18n import LANGUAGES, _
from ddict.project import load_project, save_project

EXIT_ERROR = 2
PLAN_ACTIONS = {
    "lister": "list",
    "list": "list",
    "ajouter": "add",
    "add": "add",
    "modifier": "modify",
    "modify": "modify",
    "amender": "modify",
    "amend": "modify",
    "retirer": "remove",
    "remove": "remove",
    "deplacer": "move",
    "move": "move",
    "regles": "rules",
    "rules": "rules",
    "figer": "freeze",
    "freeze": "freeze",
    "effacer": "clear",
    "clear": "clear",
    "preenregistrement": "prereg",
    "preregistration": "prereg",
}
DIRECTIONS = {
    "positif": "positive",
    "positive": "positive",
    "negatif": "negative",
    "negative": "negative",
    "premier": "first_higher",
    "first": "first_higher",
    "second": "second_higher",
    "aucun": "",
    "none": "",
}
ORIGINS = {
    "primaires": "primary",
    "primary": "primary",
    "secondaires": "secondary",
    "secondary": "secondary",
}
STATUSES = {
    "avant-creation": "before_creation",
    "before-creation": "before_creation",
    "avant-observation": "before_observation",
    "before-observation": "before_observation",
    "avant-acces": "before_access",
    "before-access": "before_access",
    "avant-analyse": "before_analysis",
    "before-analysis": "before_analysis",
    "apres-analyse": "after_analysis",
    "after-analysis": "after_analysis",
}
CORRECTIONS = {"aucune": "none", "none": "none", "holm": "holm", "bonferroni": "bonferroni"}


def _today() -> str:
    return datetime.now().date().isoformat()


def _refused(reasons: list[str]) -> int:
    print(_("Plan refusé :"), file=sys.stderr)
    for reason in reasons:
        print(f"- {reason}", file=sys.stderr)
    return EXIT_ERROR


def plan_lines(project, prepared=None, notebook=None, statuses=None) -> list[str]:
    """The plan as `ddict plan lister` prints it: the rules, each hypothesis with its
    analysis, its conditions and its deviation, the freezing and the amendments."""
    from ddict.analysis import article_text as article
    from ddict.analysis import plan_notebook as pn
    from ddict.analysis import planning, prereg
    from ddict.analysis.apa import plain

    plan = project.plan
    alpha = prereg._alpha(plan.alpha) if plan.alpha is not None else _("à taper")
    origin = article.ORIGINS[plan.data_origin] if plan.data_origin else _("à dire")
    status = prereg.STATUSES[plan.data_status] if plan.data_status else _("à dire")
    lines = [
        _("Seuil α : {alpha} ; correction : {correction}.").format(
            alpha=alpha, correction=article.CORRECTIONS[plan.correction]
        ),
        _("Données : {origin}.").format(origin=origin),
        _("État des données quand le plan a été écrit : {status}").format(status=status),
        _("Taille d'échantillon : {text}").format(text=plan.sample_size or _("à écrire")),
    ]
    if plan.frozen is not None:
        lines.append(
            _("Plan arrêté le {date} ; empreinte : {fingerprint}.").format(
                date=prereg.long_date(plan.frozen.date), fingerprint=plan.frozen.fingerprint[:12]
            )
        )
    else:
        lines.append(_("Plan non arrêté."))
    if not plan.hypotheses:
        lines.append(_("Aucune hypothèse : ajoutez-en une avec « ddict plan ajouter »."))
    models = {m[0].text.split(".")[0]: plain(m) for m in prereg._models(project)}
    deviations = {}
    if notebook is not None:
        deviations = {d.hypothesis: d.text for d in pn.deviations(notebook, project, statuses)}
    for h in plan.hypotheses:
        kind = prereg.KINDS[h.kind]
        if h.family:
            kind = _("{kind}, famille {family}").format(kind=kind, family=h.family)
        lines.append(f"{h.id} ({kind}) — {h.statement}")
        lines.append("   " + models.get(h.id, "").split(". ", 1)[-1])
        check = planning.review(project, h, prepared)
        lines += [f"   ✗ {reason}" for reason in check.refusals]
        lines += [f"   ! {warning}" for warning in check.warnings]
        if h.id in deviations:
            lines.append(f"   {deviations[h.id]}")
    if plan.frozen is not None and plan.frozen.prior:
        lines.append(
            _("Déjà dans le carnet au gel : {ids}.").format(
                ids=", ".join(f"{p.hypothesis} ({p.entry})" for p in plan.frozen.prior)
            )
        )
    if plan.amendments:
        lines.append(_("Amendements du plan :"))
        lines += [f"- {article.amendment_line(project, a)}" for a in plan.amendments]
    return lines


def _ref_names(args) -> dict[str, list[str]]:
    from ddict.cli import ROLE_ARGUMENTS

    return {
        role: list(getattr(args, argument))
        for role, argument in ROLE_ARGUMENTS.items()
        if getattr(args, argument, None)
    }


def _options(args) -> dict[str, str]:
    from ddict.cli import OPTION_ARGUMENTS

    return {
        option: getattr(args, argument)
        for option, argument in OPTION_ARGUMENTS.items()
        if getattr(args, argument, None)
    }


def _effect(args) -> dict:
    return {"pair": args.paire, "predictor": args.predicteur, "model": args.modele}


def _changes(args, project, old) -> dict:
    """The fields `modifier` changes: only those given."""
    from ddict.analysis import planning
    from ddict.cli import ANALYSES

    analysis = ANALYSES[args.analyse] if args.analyse else old.analysis
    chosen = _ref_names(args)
    given = _options(args)
    effect = _effect(args)
    data = planning.data_from_names(
        project, args.enonce or old.statement, analysis, chosen, given, **effect
    )
    changes: dict = {}
    if args.enonce:
        changes["statement"] = data["statement"]
    if args.analyse:
        changes["analysis"] = analysis
    if chosen:
        roles = old.model_dump(mode="json")["roles"]
        changes["roles"] = data["roles"] if args.analyse else roles | data["roles"]
    if given:
        changes["options"] = given if analysis != old.analysis else old.options | given
    if "effect" in data:
        changes["effect"] = data["effect"]
    if args.sens is not None:
        changes["direction"] = DIRECTIONS[args.sens] or None
    if args.exploratoire:
        changes["kind"] = "exploratory"
    if args.confirmatoire:
        changes["kind"] = "confirmatory"
    if args.famille is not None:
        changes["family"] = None if args.famille.lower() in ("aucune", "none") else args.famille
    return changes


def _rule_changes(args) -> dict:
    changes: dict = {}
    if args.alpha is not None:
        changes["alpha"] = args.alpha
    if args.correction is not None:
        changes["correction"] = CORRECTIONS[args.correction]
    if args.taille is not None:
        changes["sample_size"] = args.taille
    if args.origine is not None:
        changes["data_origin"] = ORIGINS[args.origine]
    if args.etat is not None:
        changes["data_status"] = STATUSES[args.etat]
    return changes


def _follow(project, project_path, prepared, today) -> None:
    """After a change to a frozen plan, the notebook follows it (§ 6 of the sheet)."""
    from ddict.analysis import notebook as nb
    from ddict.analysis import plan_notebook as pn

    if project.plan.frozen is None:
        return
    notebook = nb.open_notebook(project, project_path)
    for line in pn.sync(notebook, project, prepared, today):
        print(line)
    nb.save_notebook(notebook, nb.notebook_path(project_path))


def cmd_plan(args: argparse.Namespace) -> int:
    from ddict.analysis import notebook as nb
    from ddict.analysis import plan_notebook as pn
    from ddict.analysis import planning, prereg
    from ddict.cli import ANALYSES, _database

    project_path = Path(args.projet)
    project = load_project(project_path)
    action = PLAN_ACTIONS[args.action]
    today = _today()
    if action == "prereg":
        for path in prereg.write_preregistration(project, project_path, language=args.langue):
            print(_("Fichier écrit : {path}").format(path=path))
        return 0
    try:
        notebook = nb.open_notebook(project, project_path)
    except nb.NotebookError as error:
        print(nb.reason_text(error), file=sys.stderr)
        return EXIT_ERROR
    prepared = None
    if action in ("list", "add", "modify", "remove", "rules", "freeze"):
        prepared, reason = _database(project, project_path, getattr(args, "base", None))
        if prepared is None and action == "freeze":
            print(reason, file=sys.stderr)
            return EXIT_ERROR
    if action == "list":
        from ddict.analysis import notebook_check as check

        statuses = []
        if project.plan.frozen is not None and nb.notebook_path(project_path).is_file():
            statuses = check.check_all(notebook, project, prepared, today=today)
        for line in plan_lines(project, prepared, notebook, statuses):
            print(line)
        return 0
    reason = getattr(args, "raison", None)
    try:
        if action == "add":
            data = planning.data_from_names(
                project,
                args.enonce,
                ANALYSES[args.analyse],
                _ref_names(args),
                _options(args),
                **_effect(args),
                direction=DIRECTIONS[args.sens] if args.sens else None,
                kind="exploratory" if args.exploratoire else "confirmatory",
                family=args.famille,
            )
            hypothesis = planning.add(project, data, prepared, reason, today)
            print(_("Hypothèse ajoutée : {id}").format(id=hypothesis.id))
        elif action == "modify":
            old = planning.find(project, args.numero)
            planning.modify(project, old.id, _changes(args, project, old), prepared, reason, today)
            print(_("Hypothèse modifiée : {id}").format(id=old.id))
        elif action == "remove":
            planning.remove(project, args.numero, reason, today)
            print(_("Hypothèse retirée : {id}").format(id=args.numero))
        elif action == "move":
            planning.move(project, args.numero, args.rang)
            rank = [h.id for h in project.plan.hypotheses].index(args.numero) + 1
            print(_("{id} est maintenant au rang {rank}.").format(id=args.numero, rank=rank))
        elif action == "rules":
            planning.set_rules(project, _rule_changes(args), reason, today)
            print(_("Règles du plan enregistrées."))
        elif action == "freeze":
            prior = pn.freeze(notebook, project, prepared, today)
            print(
                _("Plan arrêté le {date} ; empreinte : {fingerprint}.").format(
                    date=prereg.long_date(today), fingerprint=project.plan.frozen.fingerprint[:12]
                )
            )
            if prior:
                print(
                    _("Déjà dans le carnet au gel : {ids}.").format(
                        ids=", ".join(f"{p.hypothesis} ({p.entry})" for p in prior)
                    )
                )
        else:  # clear
            if not args.confirmer:
                print(
                    _(
                        "Retirer le plan entier efface ses hypothèses, son gel et ses "
                        "amendements : ajoutez --confirmer."
                    ),
                    file=sys.stderr,
                )
                return EXIT_ERROR
            pn.clear(notebook, project)
            print(_("Plan retiré."))
    except planning.PlanRefused as error:
        return _refused(error.reasons)
    save_project(project, project_path)
    if action == "freeze" or (action == "clear" and nb.notebook_path(project_path).is_file()):
        nb.save_notebook(notebook, nb.notebook_path(project_path))
    elif action in ("add", "modify", "remove", "rules"):
        _follow(project, project_path, prepared, today)
        if prepared is None and action in ("add", "modify"):
            print(_("Conditions à vérifier quand la base sera ouverte."))
    return 0


def _hypothesis_arguments(command: argparse.ArgumentParser, adding: bool) -> None:
    from ddict.cli import ANALYSES

    if adding:
        command.add_argument(
            "analyse",
            choices=list(ANALYSES),
            help=_(
                "test_t, apparie, anova, khi2, correlation, regression, logistique, partielle "
                "ou moderation."
            ),
        )
        command.add_argument(
            "--enonce",
            "--statement",
            required=True,
            help=_("L'hypothèse, telle que l'équipe l'écrit."),
        )
    else:
        command.add_argument("numero", help=_("Numéro de l'hypothèse, p. ex. H2."))
        command.add_argument(
            "--analyse",
            "--analysis",
            choices=list(ANALYSES),
            help=_("Une autre analyse du catalogue."),
        )
        command.add_argument("--enonce", "--statement", help=_("Le nouvel énoncé."))
    command.add_argument("--variables", nargs="+", help=_("Variables (corrélation)."))
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
        "--premiere",
        "--first",
        nargs=1,
        help=_("Première mesure (test t apparié)."),
    )
    command.add_argument(
        "--seconde",
        "--second",
        nargs=1,
        help=_("Seconde mesure (test t apparié)."),
    )
    command.add_argument(
        "--covariables",
        "--covariates",
        nargs="+",
        help=_("Covariables (corrélation partielle, modération)."),
    )
    command.add_argument("--focal", nargs=1, help=_("Prédicteur (modération)."))
    command.add_argument("--moderateur", "--moderator", nargs=1, help=_("Modérateur (modération)."))
    command.add_argument(
        "--evenement",
        "--event",
        choices=["second", "first"],
        help=_(
            "Régression logistique : la modalité prédite, la seconde (par défaut) ou la "
            "première dans l'ordre des codes."
        ),
    )
    command.add_argument(
        "--centrer",
        "--center",
        choices=["yes", "no"],
        help=_("Modération : centrer le prédicteur et le modérateur (yes, par défaut, ou no)."),
    )
    command.add_argument(
        "--methode",
        "--method",
        help=_(
            "welch, student, mann_whitney ; paired_t, wilcoxon ; anova, kruskal_wallis ; "
            "pearson, fisher, spearman."
        ),
    )
    command.add_argument(
        "--hypothese",
        "--alternative",
        help=_("Test t et test t apparié : two_sided, greater ou less."),
    )
    command.add_argument("--post-hoc", help=_("ANOVA : none ou tukey."))
    command.add_argument(
        "--modalites",
        "--levels",
        help=_("Test t : les deux codes du groupe à comparer, p. ex. 1,3."),
    )
    effect = command.add_mutually_exclusive_group()
    effect.add_argument(
        "--paire", "--pair", nargs=2, metavar=("A", "B"), help=_("Corrélation : la paire testée.")
    )
    effect.add_argument("--predicteur", "--predictor", help=_("Régression : le prédicteur testé."))
    effect.add_argument(
        "--modele",
        "--model",
        action="store_true",
        help=_("Régression : le modèle entier est l'effet testé."),
    )
    command.add_argument(
        "--sens",
        "--direction",
        choices=list(DIRECTIONS),
        help=_(
            "Sens attendu : premier ou second (groupe plus élevé), positif ou "
            "negatif ; aucun pour le retirer."
        ),
    )
    kind = command.add_mutually_exclusive_group()
    kind.add_argument(
        "--exploratoire",
        "--exploratory",
        action="store_true",
        help=_("Une hypothèse exploratoire (confirmatoire par défaut)."),
    )
    if not adding:
        kind.add_argument(
            "--confirmatoire",
            "--confirmatory",
            action="store_true",
            help=_("Une hypothèse confirmatoire."),
        )
    command.add_argument(
        "--famille",
        "--family",
        help=_("Famille de la correction, p. ex. F1 ; aucune pour la retirer."),
    )


def _base(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "--base", "--database", help=_("La base d'origine, si elle n'est pas à côté du projet.")
    )


def _reason(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "--raison", "--reason", help=_("Après le gel : la raison de ce changement (amendement).")
    )


def add_plan_parser(commands) -> None:
    command = commands.add_parser(
        "plan",
        help=_(
            "Le plan d'analyse du projet : hypothèses, règles générales, gel, amendements et "
            "préenregistrement."
        ),
    )
    actions = command.add_subparsers(dest="action", required=True)
    listed = actions.add_parser(
        "lister",
        aliases=["list"],
        help=_("Lister les règles et les hypothèses, avec leurs conditions et leurs écarts."),
    )
    added = actions.add_parser(
        "ajouter", aliases=["add"], help=_("Ajouter une hypothèse à la fin du plan.")
    )
    modified = actions.add_parser(
        "modifier",
        aliases=["modify", "amender", "amend"],
        help=_("Modifier une hypothèse ; après le gel, c'est un amendement, avec sa raison."),
    )
    removed = actions.add_parser("retirer", aliases=["remove"], help=_("Retirer une hypothèse."))
    moved = actions.add_parser(
        "deplacer",
        aliases=["move"],
        help=_("Mettre une hypothèse à un autre rang (l'ordre de l'article)."),
    )
    rules = actions.add_parser(
        "regles",
        aliases=["rules"],
        help=_(
            "Régler α, la correction, la taille d'échantillon, l'origine et l'état des données."
        ),
    )
    frozen = actions.add_parser(
        "figer",
        aliases=["freeze"],
        help=_(
            "Arrêter le plan : sa date et son empreinte ; chaque hypothèse devient une "
            "analyse du carnet."
        ),
    )
    cleared = actions.add_parser(
        "effacer",
        aliases=["clear"],
        help=_("Retirer le plan entier, son gel et ses amendements."),
    )
    prereg = actions.add_parser(
        "preenregistrement",
        aliases=["preregistration"],
        help=_("Écrire le préenregistrement (Word et Markdown) à côté du projet."),
    )
    for sub in (listed, added, modified, removed, moved, rules, frozen, cleared, prereg):
        sub.add_argument("projet", help=_("Fichier projet (.dd.json)."))
    _hypothesis_arguments(added, adding=True)
    _hypothesis_arguments(modified, adding=False)
    removed.add_argument("numero", help=_("Numéro de l'hypothèse, p. ex. H2."))
    moved.add_argument("numero", help=_("Numéro de l'hypothèse, p. ex. H2."))
    moved.add_argument("rang", type=int, help=_("Nouveau rang (1 est le premier)."))
    rules.add_argument("--alpha", type=float, help=_("Le seuil α, p. ex. 0.05."))
    rules.add_argument(
        "--correction", choices=list(CORRECTIONS), help=_("aucune, holm ou bonferroni.")
    )
    rules.add_argument(
        "--taille",
        "--sample-size",
        help=_("La justification de la taille d'échantillon, en texte."),
    )
    rules.add_argument(
        "--origine", "--origin", choices=list(ORIGINS), help=_("primaires ou secondaires.")
    )
    rules.add_argument(
        "--etat",
        "--status",
        choices=list(STATUSES),
        help=_(
            "Quand le plan a été écrit : avant-creation, avant-observation, "
            "avant-acces, avant-analyse ou apres-analyse."
        ),
    )
    for sub in (added, modified, removed, rules):
        _reason(sub)
    for sub in (listed, added, modified, removed, rules, frozen):
        _base(sub)
    cleared.add_argument(
        "--confirmer",
        "--confirm",
        action="store_true",
        help=_("Confirmer le retrait du plan entier."),
    )
    prereg.add_argument(
        "--langue",
        "--language",
        choices=list(LANGUAGES),
        help=_("Langue du document (défaut : celle de l'interface)."),
    )
    command.set_defaults(handler=cmd_plan)
