"""The model bench, on the AI page (v0.4, step 6; through an API key since v0.18).

It measures the chosen model on the fictional bases (two French, one English), never on
the project's data; the report is written next to the project, and can be downloaded.
Through an API key every message is billed: the bench asks first (v0.18).
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from ddict import ai_settings
from ddict.i18n import _
from ddict.review.ui import common as c

ASK = "bench-ask"  # "Mesurer ce modèle" clicked: confirm the cost first
START = "bench-start"
REPORT = "bench-report"  # (file name, text) of the last report


def _ask() -> None:
    st.session_state[ASK] = True


def _confirm() -> None:
    st.session_state.pop(ASK, None)
    st.session_state[START] = True


def _cancel() -> None:
    st.session_state.pop(ASK, None)


def _run(settings: ai_settings.AiSettings) -> None:
    from ddict.bench import load_key, render_report, run_bench, write_report
    from ddict.llm import connect

    st.caption(_("Quelques minutes. Changer de page arrête la mesure."))
    bar = st.progress(0.0, text=_("Préparation des bases fictives…"))
    steps = 2 * len(load_key()["bases"])  # two tasks per base
    done = 0
    results = []
    with connect.client_from(settings) as client:
        for item in run_bench(client, now=c.now):
            if isinstance(item, str):
                bar.progress(min(done / steps, 1.0), text=item)
                done += 1
            else:
                results.append(item)
        endpoint = client.endpoint
    today = date.today().isoformat()
    text = render_report(results, model=settings.model, endpoint=endpoint, date=today)
    try:
        path = write_report(text, c.project_path().resolve().parent, settings.model, today)
    except OSError as error:
        st.session_state.message = (
            "error",
            _("Impossible d'écrire le rapport : {detail}.").format(detail=error),
            "bench-run",
        )
    else:
        st.session_state.message = (
            "success",
            _("Rapport écrit à côté du projet : {name}.").format(name=path.name),
            "bench-run",
        )
        st.session_state[REPORT] = (path.name, text)
    st.rerun()


def section(settings: ai_settings.AiSettings | None) -> None:
    """`settings`: the saved ones, None when they are not usable yet."""
    st.subheader(_("Banc d'essai des modèles"))
    st.write(
        _(
            "Pour choisir un modèle en connaissance de cause : sur les bases fictives de "
            "l'outil, dont on connaît les bonnes réponses, le banc mesure les rattachements "
            "justes, les libellés qui inventent peut-être (citation, seuil, nom d'instrument, "
            "sens d'un sigle, étendue, sens de codes) et la durée. Vos données ne sont pas "
            "utilisées."
        )
    )
    if st.session_state.get(START) and settings is not None:
        st.session_state.pop(START)
        _run(settings)
        return
    if st.session_state.get(ASK) and settings is not None:
        st.warning(
            _(
                "Le banc envoie plusieurs dizaines de messages au service, tirés des bases "
                "fictives seulement. Chacun est facturé sur votre clé : de l'ordre de quelques "
                "cents avec {model}, davantage avec un modèle plus grand. Lancer la mesure ?"
            ).format(model=settings.model)
        )
        left, right = st.columns(2)
        left.button(_("Lancer la mesure"), key="bench-confirm", on_click=_confirm, type="primary")
        right.button(_("Annuler"), key="bench-cancel", on_click=_cancel)
        return
    st.button(
        _("Mesurer ce modèle"),
        key="bench-run",
        on_click=_ask,
        disabled=settings is None,
    )
    c.show_message("bench-run")
    report = st.session_state.get(REPORT)
    if report:
        name, text = report
        with st.expander(_("Dernier rapport : {name}").format(name=name), expanded=True):
            st.markdown(text)
        st.download_button(
            _("Télécharger le rapport"),
            data=text.encode("utf-8"),
            file_name=name,
            mime="text/markdown",
            key="bench-download",
        )
