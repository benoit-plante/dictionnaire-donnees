"""`ddict ia` (v0.18, plan § 5.3 and § 7): the API key and the connection, from the command
line. `cle` records the key in Windows' credential manager, typed without echo, never as an
argument (PowerShell keeps the history of commands); `oublier` erases it; `tester` asks the
server for its models, which sends nothing of a project and costs nothing.

The address and the protocol come from the AI settings of this computer (`ai_settings`)
unless given. Nothing here ever prints the key: only whether one is recorded (D-137).
"""

from __future__ import annotations

import argparse
import getpass
import sys

from ddict import ai_settings
from ddict.i18n import N_, _
from ddict.llm.defaults import PROTOCOLS, EndpointRefused, check_endpoint

EXIT_ERROR = 2
AI_ACTIONS = {
    "cle": "key",
    "key": "key",
    "oublier": "forget",
    "forget": "forget",
    "tester": "test",
    "test": "test",
}
PROTOCOL_NAMES = {"anthropic": "Anthropic", "openai": N_("serveur compatible OpenAI")}


def not_installed() -> str:
    return _(
        "L'option IA n'est pas installée. Réinstallez l'outil avec ses options : "
        'uv tool install --reinstall ".[ia,revision]" (voir docs/installation-windows.md).'
    )


def _where(args: argparse.Namespace) -> tuple[str, str] | None:
    """The protocol and the checked address: the options, else this computer's settings.
    None (with a message) when the address is missing or refused."""
    settings = ai_settings.load()
    protocol = args.protocole or settings.protocol
    if args.adresse:
        endpoint = args.adresse
    elif protocol == settings.protocol:
        endpoint = settings.endpoint
    else:
        endpoint = ai_settings.default_endpoint(protocol)
    if not endpoint:
        print(_("Indiquez l'adresse du serveur avec --adresse."), file=sys.stderr)
        return None
    try:
        return protocol, check_endpoint(endpoint)
    except EndpointRefused:
        print(
            _(
                "Adresse refusée : {endpoint}. Une adresse en https:// est demandée (http:// "
                "n'est permis que pour cet ordinateur), sans identifiant ni paramètre."
            ).format(endpoint=endpoint),
            file=sys.stderr,
        )
        return None


def _key(protocol: str, endpoint: str) -> int:
    from ddict.llm import keys

    print(
        _(
            "Clé d'API pour {endpoint}. Collez-la puis appuyez sur Entrée : rien ne s'affiche "
            "pendant la saisie, c'est normal."
        ).format(endpoint=endpoint)
    )
    typed = getpass.getpass(_("Clé : "))
    try:
        keys.save(endpoint, typed)
    except ValueError as error:
        if str(error) == "empty":
            print(_("Aucune clé saisie : rien n'est enregistré."), file=sys.stderr)
        else:
            print(
                _("Ce n'est pas une clé (espaces ou plusieurs lignes) : rien n'est enregistré."),
                file=sys.stderr,
            )
        return EXIT_ERROR
    except keys.KeyStoreError:
        print(
            _("Le gestionnaire d'identifiants de Windows n'a pas enregistré la clé."),
            file=sys.stderr,
        )
        return EXIT_ERROR
    print(
        _(
            "Clé enregistrée dans le gestionnaire d'identifiants de Windows. Elle ne "
            "s'affichera jamais ; « ddict ia tester » vérifie que le serveur l'accepte."
        )
    )
    return 0


def _forget(endpoint: str) -> int:
    from ddict.llm import keys

    try:
        erased = keys.forget(endpoint)
    except keys.KeyStoreError:
        print(
            _("Le gestionnaire d'identifiants de Windows n'a pas effacé la clé."), file=sys.stderr
        )
        return EXIT_ERROR
    if erased:
        print(_("Clé effacée pour {endpoint}.").format(endpoint=endpoint))
    else:
        print(_("Aucune clé enregistrée pour {endpoint}.").format(endpoint=endpoint))
    return 0


def test_failure_text(code: str, endpoint: str) -> str:
    """What a failed connection test means, for a person."""
    texts = {
        "auth": _("La clé est refusée (ou absente). Enregistrez-la de nouveau : ddict ia cle."),
        "key_store": _("Le gestionnaire d'identifiants de Windows n'a pas donné la clé."),
        "connection": _("Impossible de joindre {endpoint} : vérifiez la connexion Internet."),
        "timeout": _("{endpoint} n'a pas répondu à temps."),
        "rate_limit": _("Trop de demandes pour cette clé : réessayez dans une minute."),
        "overloaded": _("Le service est surchargé : réessayez plus tard."),
        "http_404": _("Rien à cette adresse : vérifiez-la ({endpoint})."),
    }
    text = texts.get(code, _("Le serveur a répondu par une erreur ({code})."))
    return text.format(endpoint=endpoint, code=code)


def _test(protocol: str, endpoint: str, model: str) -> int:
    from ddict.llm import client as llm
    from ddict.llm import keys

    try:
        recorded = keys.is_recorded(endpoint)
    except keys.KeyStoreError:
        recorded = False
    print(_("Protocole : {name}").format(name=_(PROTOCOL_NAMES[protocol])))
    print(_("Adresse : {endpoint}").format(endpoint=endpoint))
    print(_("Clé : {state}").format(state=_("enregistrée") if recorded else _("absente")))
    if protocol == "anthropic" and not recorded:
        print(_("Enregistrez d'abord la clé : ddict ia cle"), file=sys.stderr)
        return EXIT_ERROR
    key = keys.reader(endpoint) if recorded else None
    try:
        if protocol == "anthropic":
            client = llm.AnthropicClient(model or "", key=key, endpoint=endpoint)
        else:
            client = llm.OpenAICompatibleClient(model or "", key=key, endpoint=endpoint)
        with client:
            models = client.list_models()
    except llm.ModelCallError as error:
        print(test_failure_text(error.code, endpoint), file=sys.stderr)
        return EXIT_ERROR
    print(
        _(
            "Connexion réussie : {n} modèles offerts. Aucun contenu de projet n'a été envoyé."
        ).format(n=len(models))
    )
    if model:
        found = _("offert") if model in models else _("absent de la liste")
        print(_("Modèle choisi : {model} ({found})").format(model=model, found=found))
    return 0


def cmd_ai(args: argparse.Namespace) -> int:
    action = AI_ACTIONS[args.action]
    where = _where(args)
    if where is None:
        return EXIT_ERROR
    protocol, endpoint = where
    try:
        if action == "key":
            return _key(protocol, endpoint)
        if action == "forget":
            return _forget(endpoint)
        return _test(protocol, endpoint, args.modele or ai_settings.load().model)
    except ImportError:
        print(not_installed(), file=sys.stderr)
        return EXIT_ERROR


def _add_where(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--protocole",
        "--protocol",
        choices=PROTOCOLS,
        help=_(
            "anthropic (par défaut) ou openai (un serveur compatible OpenAI, d'une université)."
        ),
    )
    parser.add_argument(
        "--adresse",
        "--address",
        help=_("Adresse du serveur (défaut : celle des réglages de l'IA, sinon Anthropic)."),
    )


def add_ai_parser(commands) -> None:
    command = commands.add_parser(
        "ia",
        aliases=["ai"],
        help=_(
            "La clé d'API et la connexion à l'IA : enregistrer la clé, l'oublier, tester. "
            "La clé ne se donne jamais en argument."
        ),
    )
    actions = command.add_subparsers(dest="action", required=True)
    key = actions.add_parser(
        "cle",
        aliases=["key"],
        help=_(
            "Saisir la clé d'API, sans qu'elle s'affiche ; elle est gardée dans le "
            "gestionnaire d'identifiants de Windows."
        ),
    )
    _add_where(key)
    forget = actions.add_parser(
        "oublier", aliases=["forget"], help=_("Effacer la clé d'API de cet ordinateur.")
    )
    _add_where(forget)
    test = actions.add_parser(
        "tester",
        aliases=["test"],
        help=_(
            "Vérifier la clé et la connexion en demandant la liste des modèles ; aucun "
            "contenu de projet n'est envoyé, rien n'est facturé."
        ),
    )
    _add_where(test)
    test.add_argument("--modele", "--model", help=_("Vérifier aussi que ce modèle est offert."))
    command.set_defaults(handler=cmd_ai)
