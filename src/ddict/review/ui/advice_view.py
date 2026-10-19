"""The AI's advice on the Analyses page (v0.9, step 7, D-073, D-079; through an API key since
v0.18): optional; an objective written by the team, sent with the catalogue and the
variables (metadata only, D-136), and only when the project allows it (D-138); proposals of
analyses of the catalogue, checked against the codebook, which a person takes up or not.
Nothing is computed until "Lancer l'analyse" is clicked.

Proposals stay in memory; the exchange is kept next to the project, like every exchange
with the model.
"""

from __future__ import annotations

import importlib.util
from datetime import datetime

import streamlit as st

from ddict import ai_settings
from ddict.analysis import conditions
from ddict.analysis.catalogue import CATALOGUE, ROLES, TITLES
from ddict.i18n import _
from ddict.llm.advise import (
    ADVICE_API_PROMPT_VERSION,
    ADVICE_PROMPT_VERSION,
    MAX_OBJECTIVE_CHARS,
    AdviceError,
    Proposal,
    build_advice_block,
    method_text,
)
from ddict.project.model import Project
from ddict.review.ui import ai_view
from ddict.review.ui import common as c
from ddict.workflow import advice_error_text, exchange_dir, failure_advice

GOAL = "advice-goal"
START = "advice-start"
SHOWN = "advice-preview"
ADVICE = "advice"  # (objective, proposals) or None
ERROR = "advice-error"


def _version() -> str:
    """The prompt the saved settings send: the whole message to Anthropic (v0.18, B3)."""
    if ai_settings.load().protocol == "anthropic":
        return ADVICE_API_PROMPT_VERSION
    return ADVICE_PROMPT_VERSION


def _start() -> None:
    st.session_state[START] = True


def _toggle_preview() -> None:
    st.session_state[SHOWN] = not st.session_state.get(SHOWN)


def role_key(analysis: str, role: str) -> str:
    return f"analysis-{analysis}-{role}"


def option_key(analysis: str, option: str) -> str:
    return f"analysis-{analysis}-option-{option}"


def take_up(project: Project, proposal: Proposal) -> None:
    """Fill the page's choices with a proposal; only what the codebook allows."""
    from ddict.review.ui.analyses_view import ANALYSIS

    analysis = CATALOGUE[proposal.analysis]
    st.session_state[ANALYSIS] = proposal.analysis
    for role in analysis.roles:
        allowed = conditions.candidates(project, analysis, role.key)
        names = [n for n in proposal.chosen.get(role.key, []) if n in allowed][: role.most]
        st.session_state[role_key(proposal.analysis, role.key)] = (
            (names[0] if names else None) if role.most == 1 else names
        )
    for option, values in analysis.options.items():
        value = proposal.options.get(option, values[0])
        st.session_state[option_key(proposal.analysis, option)] = value


def _ask(project: Project, objective: str) -> None:
    from ddict.llm import connect
    from ddict.llm.advise import advise

    st.session_state.pop(ADVICE, None)
    client = connect.client_for(project)  # ready() said it can
    endpoint, model = client.endpoint, client.model
    with client, st.spinner(_("Le modèle réfléchit…")):
        found = advise(
            project,
            client,
            objective,
            now=datetime.now().isoformat(timespec="seconds"),
            log_dir=exchange_dir(c.project_path()),
        )
    if found.proposals is None:
        detail = found.result.run.detail
        st.session_state[ERROR] = failure_advice(detail, endpoint, model) or _(
            "Le modèle n'a pas donné de réponse valable ({detail}). Réessayez, ou choisissez "
            "l'analyse vous-même."
        ).format(detail=detail)
        return
    st.session_state[ADVICE] = (objective.strip(), found.proposals)


def _show(project: Project, proposals: tuple[Proposal, ...]) -> None:
    if not proposals:
        st.info(_("Le modèle ne propose aucune analyse du catalogue pour cet objectif."))
        return
    st.write(_("Propositions du modèle, à vérifier : rien n'est calculé sans vous."))
    for number, proposal in enumerate(proposals, start=1):
        lines = [f"**{number}. {TITLES[proposal.analysis]}**"]
        for role, names in proposal.chosen.items():
            lines.append(f"- {ROLES[role]} : {', '.join(names)}")
        if proposal.options:
            lines.append("- " + _("Méthode : {method}").format(method=method_text(proposal)))
        lines.append("- " + _("Raison donnée par le modèle : {reason}").format(
            reason=proposal.reason))  # fmt: skip
        st.markdown("\n".join(lines))
        for reason in proposal.check.refusals:
            st.warning(_("Condition non remplie : {reason}").format(reason=reason))
        st.button(
            _("Reprendre cette proposition"),
            key=f"advice-take-{number}",
            on_click=take_up,
            args=(project, proposal),
        )


def panel(project: Project) -> None:
    """The optional box; absent when the AI option is not installed."""
    if importlib.util.find_spec("httpx") is None or importlib.util.find_spec("keyring") is None:
        return
    with st.expander(
        _("Demander une proposition à l'IA (facultatif)"),
        expanded=bool(st.session_state.get(ADVICE) or st.session_state.get(ERROR)),
    ):
        st.text_area(
            _("Objectif de l'analyse"),
            key=GOAL,
            max_chars=MAX_OBJECTIVE_CHARS,
            placeholder=_("Par exemple : comparer le bien-être entre les deux groupes de l'étude."),
        )
        model = ai_settings.load().model or "—"
        st.caption(
            _(
                "Le modèle {model} reçoit cet objectif tel quel, le catalogue et la liste des "
                "variables (nom, libellé, niveau de mesure, groupe) : aucune donnée, aucune "
                "statistique. N'écrivez aucune donnée de participant dans l'objectif. Le "
                "modèle se choisit sur la page « IA »."
            ).format(model=model)
        )
        blocked = ai_view.ready(project)
        if blocked:
            st.info(blocked)
        c.go_button(_("Réglages de l'IA"), "go-ai-advice", "ai")
        objective = str(st.session_state.get(GOAL) or "")
        left, right = st.columns(2)
        left.button(_("Voir ce qui serait envoyé"), key="advice-show", on_click=_toggle_preview)
        right.button(
            _("Demander une proposition"),
            key="advice-ask",
            type="primary",
            disabled=not objective.strip() or blocked is not None,
            on_click=_start,
        )
        if st.session_state.get(SHOWN):
            try:
                block = build_advice_block(project, objective, _version())
            except AdviceError as error:
                st.info(advice_error_text(error))
            else:
                st.code(block.messages[1]["content"], language="json")
        if st.session_state.pop(START, False) and blocked is None:
            st.session_state.pop(ERROR, None)
            try:
                build_advice_block(project, objective, _version())
            except AdviceError as error:
                st.session_state[ERROR] = advice_error_text(error)
            else:
                _ask(project, objective)
        if st.session_state.get(ERROR):
            st.error(st.session_state[ERROR])
        advice = st.session_state.get(ADVICE)
        if advice is not None:
            if advice[0] != objective.strip():
                st.caption(_("Propositions pour l'objectif précédent : {goal}").format(
                    goal=advice[0]))  # fmt: skip
            _show(project, advice[1])
