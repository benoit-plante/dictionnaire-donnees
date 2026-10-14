"""The model bench, on the local AI page (v0.4, step 6).

It measures the chosen model on the two fictional bases, never on the project's data; the
report is written next to the project, and can be downloaded.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from ddict.i18n import _
from ddict.review.ui import common as c

START = "bench-start"
REPORT = "bench-report"  # (file name, text) of the last report


def _start() -> None:
    st.session_state[START] = True


def _run(endpoint: str, model: str) -> None:
    from ddict.bench import render_report, run_bench, write_report
    from ddict.llm.client import LocalModelClient

    st.caption(
        _(
            "Environ deux minutes avec un modèle de 7 milliards de paramètres et une carte "
            "graphique ; davantage sans. Changer de page arrête la mesure."
        )
    )
    bar = st.progress(0.0, text=_("Préparation des bases fictives…"))
    steps = 4  # two bases, two tasks each
    done = 0
    results = []
    with LocalModelClient(model, endpoint=endpoint) as client:
        for item in run_bench(client, now=c.now):
            if isinstance(item, str):
                bar.progress(min(done / steps, 1.0), text=item)
                done += 1
            else:
                results.append(item)
    today = date.today().isoformat()
    text = render_report(results, model=model, endpoint=endpoint, date=today)
    try:
        path = write_report(text, c.project_path().resolve().parent, model, today)
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


def section(model: tuple[str, str] | None) -> None:
    st.subheader(_("Banc d'essai des modèles"))
    st.write(
        _(
            "Pour choisir un modèle en connaissance de cause : sur les deux bases fictives de "
            "l'outil, dont on connaît les bonnes réponses, le banc mesure les rattachements "
            "justes, les libellés qui inventent peut-être (citation, seuil, nom d'instrument, "
            "sens d'un sigle, étendue, sens de codes) et la durée. Vos données ne sont pas "
            "utilisées, et aucun modèle n'est téléchargé."
        )
    )
    if st.session_state.get(START) and model is not None:
        st.session_state.pop(START)
        _run(*model)
        return
    st.button(
        _("Mesurer ce modèle"),
        key="bench-run",
        on_click=_start,
        disabled=model is None,
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
