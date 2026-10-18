"""The local model, from the interface (v0.3, D-022, D-023).

- The server is checked on this computer only (the same guards as `ddict enrichir`); the
  tool never downloads nor installs a model: it explains how.
- What would be sent can be read before anything is sent.
- A run goes block by block in this tab, with a progress bar. Any click, "Arrêter" or a
  change of page, stops it after the block in progress; finished blocks are saved, and a
  new run starts where the last one stopped (blocks already done are not sent again).
"""

from __future__ import annotations

import json

import streamlit as st

from ddict.i18n import N_, Texts, _
from ddict.llm.defaults import DEFAULT_ENDPOINT
from ddict.llm.link import DEFAULT_LINK_BLOCK_SIZE, build_link_blocks
from ddict.llm.messages import DEFAULT_BLOCK_SIZE, build_blocks
from ddict.project import save_project
from ddict.project.model import Project
from ddict.questionnaire.link import candidates
from ddict.review.ui import bench_view
from ddict.review.ui import common as c
from ddict.workflow import exchange_dir, failure_advice

ENDPOINT = "ai-endpoint"
MODEL = "ai-model"
START = "ai-start"
RECOMMENDED = "qwen2.5:7b-instruct-q4_K_M"
JOBS = Texts(
    {
        "link": (N_("Rattachement aux questions"), DEFAULT_LINK_BLOCK_SIZE),
        "enrich": (N_("Libellés et descriptions"), DEFAULT_BLOCK_SIZE),
    }
)


def _blocks(project: Project, job: str):
    if job == "link":
        return build_link_blocks(project, size=DEFAULT_LINK_BLOCK_SIZE)
    return build_blocks(project, size=DEFAULT_BLOCK_SIZE)


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


def _install_help() -> None:
    st.markdown(
        _(
            "1. Installez Ollama depuis [ollama.com](https://ollama.com) (bouton « Download "
            "for Windows »), puis lancez-le : son icône apparaît près de l'horloge.\n"
            "2. Téléchargez le modèle recommandé, une seule fois (environ 4,7 Go), dans "
            "PowerShell :"
        )
    )
    st.code(f"ollama pull {RECOMMENDED}", language=None)
    st.caption(
        _(
            "L'outil ne télécharge jamais de modèle lui-même : c'est une étape d'installation, "
            "faite par vous."
        )
    )
    st.button(_("Vérifier de nouveau"), key="ai-check-again")


def _model_section() -> tuple[str, str] | None:
    """The endpoint and model to use, or None when the server cannot be used."""
    try:
        from ddict.llm.client import EndpointRefused, ModelCallError, list_models
    except ImportError:
        st.warning(
            _(
                "L'option IA n'est pas installée. Réinstallez l'outil avec ses options (voir "
                "docs/installation-windows.md)."
            )
        )
        return None
    st.subheader(_("Modèle local"))
    with st.expander(_("Adresse du serveur local")):
        st.text_input(
            _("Adresse (Ollama par défaut)"),
            key=c.field(ENDPOINT, lambda: DEFAULT_ENDPOINT),
        )
        st.caption(_("Seule une adresse de cet ordinateur est acceptée."))
    endpoint = str(st.session_state[ENDPOINT]).strip() or DEFAULT_ENDPOINT
    try:
        models = list_models(endpoint)
    except EndpointRefused:
        st.error(_("Adresse refusée : seul un serveur sur cet ordinateur est permis."))
        return None
    except ModelCallError as error:
        st.warning(
            failure_advice(error.code, endpoint, RECOMMENDED)
            or _("Le serveur local ne répond pas comme prévu.")
        )
        _install_help()
        return None
    if not models:
        st.warning(_("Ollama répond, mais aucun modèle n'est installé."))
        _install_help()
        return None
    if st.session_state.get(MODEL) not in models:
        st.session_state[MODEL] = RECOMMENDED if RECOMMENDED in models else models[0]
    st.selectbox(_("Modèle"), models, placeholder=_("Choisir…"), key=MODEL)
    st.caption(
        _(
            "Le modèle tourne sur cet ordinateur. Il ne reçoit jamais les réponses des "
            "participants : seulement des noms, des étiquettes, des proportions et, pour le "
            "rattachement, quelques questions candidates."
        )
    )
    return endpoint, st.session_state[MODEL]


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


def _run(project: Project, job: str, endpoint: str, model: str) -> None:
    from ddict.llm.client import LocalModelClient
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
    with LocalModelClient(model, endpoint=endpoint) as client:
        run = {"link": propose_links, "enrich": enrich}[job]
        events = run(
            project,
            client,
            now=c.now,
            block_size=size,
            save=lambda p: save_project(p, path),
            log_dir=exchange_dir(path),
        )
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


def _job(
    project: Project,
    job: str,
    model: tuple[str, str] | None,
    intro: str,
    advice: str | None = None,
) -> None:
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
    if st.session_state.get(START) == job and model is not None and blocks:
        st.session_state.pop(START)
        _run(project, job, *model)
        return
    st.button(
        _("Faire proposer : {title}").format(title=title.lower()),
        key=f"ai-{job}",
        on_click=_start,
        args=(job,),
        disabled=model is None or not blocks,
        type="primary",
    )
    c.show_message(f"ai-{job}")


def page(project: Project) -> None:
    st.header(_("IA locale"))
    st.caption(
        _(
            "Facultative. Chaque proposition attend votre décision, et l'IA ne définit jamais "
            "un sigle. Ordre recommandé : glossaire, rattachement, révision des rattachements, "
            "puis libellés et descriptions."
        )
    )
    model = _model_section()

    if project.questionnaire is None:
        st.subheader(JOBS["link"][0])
        st.info(_("Ajoutez d'abord le questionnaire de l'étude (page « Questionnaire »)."))
        c.go_button(_("Ajouter le questionnaire"), "go-questionnaire", "questionnaire")
    else:
        found = candidates(project)
        _job(
            project,
            "link",
            model,
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
        model,
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
    bench_view.section(model)
