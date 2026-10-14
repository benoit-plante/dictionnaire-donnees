"""The database: what was read and computed, as `ddict profiler` says it (v0.3)."""

from __future__ import annotations

from collections import Counter

import pandas as pd
import streamlit as st

from ddict.export import wording as w
from ddict.i18n import _
from ddict.project.model import Project
from ddict.review import logic
from ddict.review.ui import common as c
from ddict.workflow import profile_summary

FORMATS = {
    "sav": "SPSS",
    "csv": "CSV",
    "dta": "Stata",
    "sas7bdat": "SAS",
    "xlsx": "Excel",
}


def page(project: Project) -> None:
    source = project.source
    st.header(source.name + (f" — {source.label}" if source.label else ""))
    st.write(profile_summary(project))

    sensitive = [e for e in project.variables if logic.is_sensitive(e)]
    flagged = [e for e in project.variables if w.entry_anomalies(e)]
    columns = st.columns(4)
    columns[0].metric(_("Variables"), len(project.variables))
    columns[1].metric(_("Lignes"), source.n_rows)
    columns[2].metric(_("Variables sensibles"), len(sensitive))
    columns[3].metric(_("Avec signalements"), len(flagged))

    facts = [f"{_('Format')} : {FORMATS.get(source.format, source.format)}"]
    if source.encoding:
        facts.append(f"{_('Encodage')} : {source.encoding}")
    if source.delimiter:
        facts.append(f"{_('Séparateur')} : « {source.delimiter} »")
    if source.decimal:
        facts.append(f"{_('Marque décimale')} : « {source.decimal} »")
    facts.append(_("Groupes de variables repérés : {n}").format(n=len(project.groups)))
    st.markdown("\n".join(f"- {fact}" for fact in facts))
    st.caption(
        _(
            "Le fichier de données n'est jamais modifié ; le projet garde seulement ce que "
            "l'outil a calculé et vos décisions, pas les réponses des participants. "
            "Fichier projet : {path}"
        ).format(path=c.project_path())
    )

    types = Counter(
        w.TYPES.get(e.profile.inferred_type, e.profile.inferred_type) for e in project.variables
    )
    st.subheader(_("Types de variables"))
    st.dataframe(
        pd.DataFrame(sorted(types.items()), columns=[_("Type"), _("Variables")]),
        hide_index=True,
    )
    if sensitive:
        st.subheader(_("Variables sensibles"))
        st.caption(
            _(
                "Seules leurs métadonnées sont utilisées : aucune statistique sur leurs "
                "valeurs, et rien d'elles n'est envoyé au modèle."
            )
        )
        st.dataframe(
            pd.DataFrame(
                [(e.name, w.privacy_text(e)) for e in sensitive],
                columns=[_("Variable"), _("Confidentialité")],
            ),
            hide_index=True,
        )
