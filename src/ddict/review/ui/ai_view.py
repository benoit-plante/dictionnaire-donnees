"""The AI page (v0.18, plan § 7; v0.3 to v0.17, a model on this computer, D-022).

- The settings of this computer: the protocol (Anthropic, or a server compatible with
  OpenAI, an institution's), the address, the model, the effort; the API key, typed in a
  masked field and kept in Windows' credential manager, never shown again (D-137). Testing
  the connection asks for the list of models: nothing of a project is sent.
- What leaves, said plainly: metadata only (D-136), to whom, kept how long.
- The project's runs: only when the project allows it (the box of the sidebar, D-138);
  what would be sent can always be read first. A run goes block by block in this tab, with
  a progress bar. Any click, "Arrêter" or a change of page, stops it after the block in
  progress; finished blocks are saved, and a new run starts where the last one stopped.
"""

from __future__ import annotations

import json

import streamlit as st

from ddict import ai_settings
from ddict.i18n import N_, Texts, _
from ddict.llm.defaults import DEFAULT_MODEL, EFFORTS, PROTOCOLS, EndpointRefused, check_endpoint
from ddict.llm.link import API_LINK_BLOCK_SIZE, build_link_blocks
from ddict.llm.messages import API_BLOCK_SIZE, build_blocks
from ddict.project.model import Project
from ddict.project.permission import is_allowed
from ddict.questionnaire.link import candidates
from ddict.review.ui import bench_view
from ddict.review.ui import common as c
from ddict.workflow import exchange_dir, failure_advice

PROTOCOL = "ai-protocol"
ENDPOINT = "ai-endpoint"
MODEL = "ai-model"
EFFORT = "ai-effort"
KEY_INPUT = "ai-key-input"
TESTED = "ai-tested"  # (kind, text) of the last connection test
START = "ai-start"
VERIFIED = "2026-10-19"  # the day the provider's retention was read
RETENTION_URL = (
    "https://privacy.claude.com/en/articles/7996866-how-long-does-anthropic-store-my-"
    "organizations-data"
)
PROTOCOL_NAMES = Texts(
    {"anthropic": N_("Anthropic (par défaut)"), "openai": N_("Serveur compatible OpenAI")}
)
EFFORT_NAMES = Texts(
    {
        "low": N_("faible (le moins coûteux)"),
        "medium": N_("moyen (par défaut)"),
        "high": N_("élevé"),
        "xhigh": N_("très élevé"),
        "max": N_("maximal"),
    }
)
JOBS = Texts(
    {
        "link": (N_("Rattachement aux questions"), API_LINK_BLOCK_SIZE),
        "enrich": (N_("Libellés et descriptions"), API_BLOCK_SIZE),
    }
)


# --- The settings of this computer ----------------------------------------------------------


def _fill_fields() -> None:
    """The fields start from the saved settings, once per session."""
    saved = ai_settings.load()
    st.session_state.setdefault(PROTOCOL, saved.protocol)
    st.session_state.setdefault(ENDPOINT, saved.endpoint)
    st.session_state.setdefault(MODEL, saved.model)
    st.session_state.setdefault(EFFORT, saved.effort)


def _typed() -> ai_settings.AiSettings:
    """The settings as typed on the page, not yet saved."""
    protocol = st.session_state[PROTOCOL]
    endpoint = str(st.session_state[ENDPOINT]).strip() or ai_settings.default_endpoint(protocol)
    return ai_settings.AiSettings(
        protocol=protocol,
        endpoint=endpoint,
        model=str(st.session_state[MODEL]).strip(),
        effort=st.session_state[EFFORT] if protocol == "anthropic" else "low",
    )


def _endpoint_or_none(settings: ai_settings.AiSettings) -> str | None:
    try:
        return check_endpoint(settings.endpoint) if settings.endpoint else None
    except EndpointRefused:
        return None


def _refused_address() -> str:
    return _(
        "Adresse refusée : une adresse en https:// est demandée (http:// n'est permis que pour "
        "cet ordinateur), sans identifiant ni paramètre."
    )


def _protocol_changed() -> None:
    st.session_state[ENDPOINT] = ai_settings.default_endpoint(st.session_state[PROTOCOL])
    st.session_state[MODEL] = ai_settings.default_model(st.session_state[PROTOCOL])


def _save_settings() -> None:
    settings = _typed()
    if _endpoint_or_none(settings) is None:
        st.session_state.message = ("error", _refused_address(), "ai-settings")
        return
    try:
        ai_settings.save(settings)
    except OSError as error:
        text = _("Les réglages n'ont pas pu être enregistrés : {detail}.").format(detail=error)
        st.session_state.message = ("error", text, "ai-settings")
        return
    st.session_state.message = ("success", _("Réglages enregistrés."), "ai-settings")


def _save_key() -> None:
    from ddict.llm import keys

    typed = str(st.session_state.get(KEY_INPUT) or "")
    st.session_state[KEY_INPUT] = ""  # never kept in the session longer than this
    endpoint = _endpoint_or_none(_typed())
    if endpoint is None:
        st.session_state.message = ("error", _refused_address(), "ai-key")
        return
    try:
        keys.save(endpoint, typed)
    except ValueError:
        text = _("Ce n'est pas une clé (vide, avec des espaces ou sur plusieurs lignes).")
        st.session_state.message = ("error", text, "ai-key")
        return
    except keys.KeyStoreError:
        text = _("Le gestionnaire d'identifiants de Windows n'a pas enregistré la clé.")
        st.session_state.message = ("error", text, "ai-key")
        return
    text = _("Clé enregistrée dans le gestionnaire d'identifiants de Windows.")
    st.session_state.message = ("success", text, "ai-key")


def _forget_key() -> None:
    from ddict.llm import keys

    endpoint = _endpoint_or_none(_typed())
    try:
        erased = endpoint is not None and keys.forget(endpoint)
    except keys.KeyStoreError:
        text = _("Le gestionnaire d'identifiants de Windows n'a pas effacé la clé.")
        st.session_state.message = ("error", text, "ai-key")
        return
    text = _("Clé effacée.") if erased else _("Aucune clé enregistrée pour cette adresse.")
    st.session_state.message = ("success", text, "ai-key")


def _test() -> None:
    from ddict.cli_ai import test_failure_text
    from ddict.llm import connect
    from ddict.llm.client import ModelCallError

    settings = _typed()
    try:
        with connect.client_from(settings, need_model=False) as client:
            models = client.list_models()
    except EndpointRefused:
        st.session_state[TESTED] = ("error", _refused_address())
        return
    except ModelCallError as error:
        st.session_state[TESTED] = ("error", test_failure_text(error.code, settings.endpoint))
        return
    text = _("Connexion réussie : {n} modèles offerts. Aucun contenu de projet n'a été envoyé.")
    text = text.format(n=len(models))
    if settings.model and settings.model not in models:
        text += " " + _("Le modèle « {model} » n'est pas dans la liste.").format(
            model=settings.model
        )
    st.session_state[TESTED] = ("success", text)


def _key_recorded(settings: ai_settings.AiSettings) -> bool | None:
    """Whether a key is recorded for the address typed; None when it cannot be said."""
    from ddict.llm import keys

    endpoint = _endpoint_or_none(settings)
    if endpoint is None:
        return None
    try:
        return keys.is_recorded(endpoint)
    except keys.KeyStoreError:
        return None


def _settings_section() -> None:
    st.subheader(_("Réglages de cet ordinateur"))
    _fill_fields()
    st.radio(
        _("Service d'IA"),
        list(PROTOCOLS),
        key=PROTOCOL,
        format_func=PROTOCOL_NAMES.__getitem__,
        horizontal=True,
        on_change=_protocol_changed,
    )
    anthropic = st.session_state[PROTOCOL] == "anthropic"
    st.text_input(
        _("Adresse"),
        key=ENDPOINT,
        help=_(
            "Celle d'Anthropic par défaut. Pour le serveur d'IA d'une université, l'adresse "
            "qu'il donne, souvent terminée par /v1."
        ),
    )
    settings = _typed()
    if _endpoint_or_none(settings) is None:
        st.error(_refused_address())
    st.text_input(
        _("Modèle"),
        key=MODEL,
        help=_(
            "Pour Anthropic : {model} par défaut, choisi d'après le banc (le moins coûteux), ou "
            "claude-sonnet-5-5."
        ).format(model=DEFAULT_MODEL),
    )
    if anthropic:
        st.selectbox(
            _("Réflexion du modèle"),
            list(EFFORTS),
            key=EFFORT,
            placeholder=_("Choisir…"),
            format_func=EFFORT_NAMES.__getitem__,
            help=_("Plus de réflexion coûte plus cher ; le banc dira si elle aide."),
        )
    st.button(_("Enregistrer les réglages"), key="ai-settings", on_click=_save_settings)
    c.show_message("ai-settings")

    recorded = _key_recorded(settings)
    state = {True: _("enregistrée"), False: _("absente"), None: _("inconnue")}[recorded]
    st.write(_("Clé d'API : {state}.").format(state=state))
    st.text_input(
        _("Nouvelle clé d'API"),
        key=KEY_INPUT,
        type="password",
        help=_(
            "Gardée dans le gestionnaire d'identifiants de Windows, jamais dans le projet ni "
            "dans un fichier ; elle ne s'affichera plus."
        ),
    )
    left, right = st.columns(2)
    left.button(_("Enregistrer la clé"), key="ai-key", on_click=_save_key)
    right.button(_("Oublier la clé"), key="ai-forget", on_click=_forget_key, disabled=not recorded)
    c.show_message("ai-key")
    if anthropic:
        st.caption(
            _(
                "Une clé s'obtient dans la console d'Anthropic (console.anthropic.com). Fixez-y "
                "une limite de dépenses : chaque envoi est facturé sur cette clé."
            )
        )

    st.button(_("Tester la connexion"), key="ai-test", on_click=_test)
    tested = st.session_state.get(TESTED)
    if tested:
        (st.success if tested[0] == "success" else st.error)(tested[1])


def _what_leaves_section() -> None:
    st.subheader(_("Ce qui part"))
    st.markdown(
        _(
            "Seulement des métadonnées : ce que disent le questionnaire et le codebook.\n\n"
            "- **Partent** : les noms des variables et de leurs voisines, les étiquettes des "
            "variables et des valeurs, les codes manquants déclarés, le texte des questions "
            "dont le rattachement est accepté, les sigles acceptés du glossaire, le type et le "
            "niveau de mesure, le nombre d'items et le préfixe d'un groupe ; pour la "
            "conseillère, l'objectif que vous écrivez et le catalogue des analyses.\n"
            "- **Ne partent jamais** : une réponse d'un participant, une statistique tirée des "
            "réponses (effectifs, proportions, manquants, minimum, maximum, moyenne, années), "
            "une valeur d'un texte libre ou d'un identifiant, le nom ou le chemin de la base, "
            "les notes de l'équipe.\n"
            "- **Seulement pour un projet qui le permet** : la case de la barre latérale, non "
            "cochée par défaut. L'aperçu de chaque message reste toujours possible."
        )
    )
    if st.session_state.get(PROTOCOL, "anthropic") == "anthropic":
        st.markdown(
            _(
                "**Chez Anthropic**, pour l'interface de programmation (API), les demandes et "
                "les réponses sont supprimées dans les 30 jours, sauf exceptions : une entente "
                "« zéro conservation », le respect de la politique d'usage (un contenu signalé "
                "peut être gardé jusqu'à 2 ans), une obligation légale. Source : "
                "[politique de conservation d'Anthropic]({url}), lue le {day}."
            ).format(url=RETENTION_URL, day=VERIFIED)
        )
    else:
        st.markdown(
            _(
                "**Chez le serveur choisi** : sa durée de conservation est celle de "
                "l'établissement qui l'offre ; demandez-la-lui."
            )
        )


# --- The project's runs -----------------------------------------------------------------------


def _blocks(project: Project, job: str):
    if job == "link":
        return build_link_blocks(project, size=API_LINK_BLOCK_SIZE)
    return build_blocks(project, size=API_BLOCK_SIZE)


def _start(job: str) -> None:
    st.session_state[START] = job


def _stopped(job: str) -> None:
    """The click reloads the page, which stops the run after the block in progress."""
    st.session_state.message = (
        "success",
        _(
            "{title} : arrêté. Les blocs terminés sont enregistrés ; relancez pour continuer "
            "là où le travail s'est arrêté."
        ).format(title=JOBS[job][0]),
        f"ai-{job}",
    )


def _preview(project: Project, job: str) -> None:
    blocks = _blocks(project, job)
    with st.expander(_("Voir exactement ce qui serait envoyé (rien n'est envoyé)")):
        if not blocks:
            st.caption(_("Rien à envoyer."))
            return
        index = st.number_input(
            _("Bloc"), min_value=1, max_value=len(blocks), value=1, key=f"ai-preview-{job}"
        )
        block = blocks[int(index) - 1]
        st.caption(_("Consigne donnée au modèle"))
        st.code(block.messages[0]["content"], language=None, wrap_lines=True)
        st.caption(_("Message du bloc {block}").format(block=block.block_id))
        st.code(
            json.dumps(json.loads(block.messages[1]["content"]), ensure_ascii=False, indent=2),
            language="json",
        )


class _Refused(Exception):
    """A block's save was refused: the project changed elsewhere (v0.17)."""


def _run(project: Project, job: str) -> None:
    from ddict.llm import connect
    from ddict.llm.enrich import enrich
    from ddict.llm.link import propose_links

    title, size = JOBS[job]
    path = c.project_path()
    total = max(len(_blocks(project, job)), 1)
    st.button(_("Arrêter"), key=f"ai-stop-{job}", type="primary", on_click=_stopped, args=(job,))
    st.caption(
        _(
            "Le travail s'arrête après le bloc en cours si vous cliquez sur « Arrêter » ou "
            "changez de page. Les blocs terminés sont gardés ; une relance reprend là où il "
            "s'était arrêté."
        )
    )
    bar = st.progress(0.0, text=_("{title} : envoi du premier bloc…").format(title=title))
    done = succeeded = skipped = failed = 0
    last = None

    def save(_project: Project) -> None:
        # v0.17 (D-130): changed elsewhere, the page says so; no block is sent after.
        if not c.save(f"ai-{job}", action=title):
            raise _Refused

    with connect.client_for(project) as client:
        run = {"link": propose_links, "enrich": enrich}[job]
        events = run(
            project,
            client,
            now=c.now,
            block_size=size,
            save=save,
            log_dir=exchange_dir(path),
        )
        try:
            for event in events:
                done += 1
                if event.result is None:
                    skipped += 1
                elif event.result.run.outcome == "succeeded":
                    succeeded += 1
                else:
                    failed += 1
                    last = event.result.run.detail
                bar.progress(
                    min(done / total, 1.0),
                    text=_("{title} : bloc {done} sur {total}").format(
                        title=title, done=done, total=total
                    ),
                )
        except _Refused:
            st.rerun()
        endpoint, model = client.endpoint, client.model
    text = _("{title} : {ok} blocs réussis, {skipped} déjà faits, {failed} en échec.").format(
        title=title, ok=succeeded, skipped=skipped, failed=failed
    )
    advice = failure_advice(last, endpoint, model)
    if advice:
        text += " " + advice
    if succeeded:
        text += " " + _("Les propositions sont à réviser dans « Variables ».")
    st.session_state.message = ("error" if failed else "success", text, f"ai-{job}")
    st.rerun()


def ready(project: Project) -> str | None:
    """Why the project's messages cannot be sent now; None when they can."""
    if not is_allowed(project):
        return _(
            "L'envoi à l'IA n'est pas permis pour ce projet : cochez « Permettre l'envoi des "
            "métadonnées de ce projet à l'IA » dans la barre latérale. L'aperçu reste possible."
        )
    saved = ai_settings.load()
    if not saved.model or _endpoint_or_none(saved) is None:
        return _("Enregistrez d'abord les réglages de l'IA : adresse et modèle.")
    return None


def _job(project: Project, job: str, blocked: str | None, intro: str, advice=None) -> None:
    title, _size = JOBS[job]
    st.subheader(title)
    st.write(intro)
    if advice:
        st.info(advice)
    blocks = _blocks(project, job)
    names = sum(len(b.names) for b in blocks)
    st.caption(
        _("{n} variables à envoyer, en {b} blocs.").format(n=names, b=len(blocks))
        if blocks
        else _("Aucune variable à envoyer.")
    )
    _preview(project, job)
    if st.session_state.get(START) == job and blocked is None and blocks:
        st.session_state.pop(START)
        _run(project, job)
        return
    st.button(
        _("Faire proposer : {title}").format(title=title.lower()),
        key=f"ai-{job}",
        on_click=_start,
        args=(job,),
        disabled=blocked is not None or not blocks,
        type="primary",
    )
    c.show_message(f"ai-{job}")


def page(project: Project) -> None:
    st.header(_("IA"))
    st.caption(
        _(
            "Facultative. Chaque proposition attend votre décision, et l'IA ne définit jamais "
            "un sigle. Ordre recommandé : glossaire, rattachement, révision des rattachements, "
            "puis libellés et descriptions."
        )
    )
    try:
        import httpx  # noqa: F401
        import keyring  # noqa: F401
    except ImportError:
        st.warning(
            _(
                "L'option IA n'est pas installée. Réinstallez l'outil avec ses options (voir "
                "docs/installation-windows.md)."
            )
        )
        return
    _settings_section()
    _what_leaves_section()
    st.divider()
    blocked = ready(project)
    if blocked:
        st.info(blocked)

    if project.questionnaire is None:
        st.subheader(JOBS["link"][0])
        st.info(_("Ajoutez d'abord le questionnaire de l'étude (page « Questionnaire »)."))
        c.go_button(_("Ajouter le questionnaire"), "go-questionnaire", "questionnaire")
    else:
        found = candidates(project)
        _job(
            project,
            "link",
            blocked,
            _(
                "Le modèle choisit, pour chaque variable, sa question parmi les candidates "
                "calculées ({n} variables en ont), et répond par un identifiant."
            ).format(n=sum(1 for ids in found.values() if ids)),
        )

    first = any(e.status == "proposed" for e in project.glossary) or any(
        e.question.status == "proposed" for e in project.variables
    )
    _job(
        project,
        "enrich",
        blocked,
        _(
            "Le modèle propose un libellé et une description pour chaque variable, à partir "
            "de ses métadonnées, du texte exact de sa question quand le rattachement est "
            "accepté, et du sens des sigles acceptés."
        ),
        advice=_(
            "Conseil : validez d'abord le glossaire et révisez les rattachements proposés ; le "
            "modèle s'en sert pour les libellés."
        )
        if first
        else None,
    )
    st.divider()
    saved = ai_settings.load()
    bench_view.section(saved if saved.model and _endpoint_or_none(saved) else None)
