"""The page "Vérifier" (v0.15, step 5, D-117, D-118): the figures of a Word manuscript
checked against what the tool writes, the values by class, the report and the commented
copy, written next to the manuscript or downloaded. The same functions as `ddict verifier`.
"""

from __future__ import annotations

import io
from pathlib import Path

import streamlit as st

from ddict.analysis import notebook as nb
from ddict.analysis import verify
from ddict.i18n import _
from ddict.project.model import Project
from ddict.review.ui import analyses_view, dialog
from ddict.review.ui import common as c

PATH = "verify-path"
RESULT = "verify-result"
CLASSES = "verify-classes"


def _choose() -> None:
    path = dialog.choose("manuscript")
    if path:
        st.session_state[PATH] = path
        st.session_state.pop(RESULT, None)


def page(project: Project) -> None:
    st.title(_("Vérifier les chiffres"))
    st.caption(
        _(
            "L'outil lit un manuscrit Word, même retouché à la main, y repère les statistiques "
            "écrites au style APA et compare chacune à ce que l'outil écrit lui-même, "
            "recalculé sur la base. Le manuscrit n'est jamais modifié ; rien n'est envoyé hors "
            "de votre ordinateur."
        )
    )
    left, right = st.columns([4, 1])
    left.text_input(_("Manuscrit (.docx)"), key=PATH)
    right.button(_("Choisir le manuscrit…"), key="verify-choose", on_click=_choose)
    manuscript = Path(st.session_state.get(PATH) or "")
    prepared = analyses_view.prepared_data(project, "verify")
    if prepared is None:
        st.caption(_("Sans la base, la comparaison se fait aux valeurs gardées dans le carnet."))
    ready = manuscript.suffix.lower() == ".docx" and manuscript.is_file()
    if st.button(_("Vérifier"), key="verify-run", type="primary", disabled=not ready):
        with st.spinner(_("Lecture et comparaison…")):
            notebook = nb.open_notebook(project, c.project_path())
            st.session_state[RESULT] = (
                str(manuscript),
                verify.verify(project, prepared, notebook, manuscript),
            )
    found = st.session_state.get(RESULT)
    if found is None or found[0] != str(manuscript):
        return
    result = found[1]
    for line in verify.summary_lines(result):
        st.write(line)
    kinds = st.multiselect(
        _("Classes montrées"),
        list(verify.ORDER),
        default=[k for k in verify.ORDER if k != "agrees"],
        key=CLASSES,
        format_func=verify.CLASSES.__getitem__,
    )
    shown = [verify.CLASSES[k] for k in kinds]
    table = [row for row in verify.rows(result) if row[-1] in shown]
    if table:
        header = [_(h) for h in verify.HEADER]
        st.dataframe(
            [dict(zip(header, row, strict=True)) for row in table],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.success(_("Aucune valeur dans ces classes."))
    if st.button(_("Écrire à côté du manuscrit"), key="verify-write"):
        written = verify.write(result, manuscript)
        st.success(
            _("Fichiers écrits à côté du manuscrit : {names}").format(
                names=", ".join(p.name for p in written)
            )
        )
    names = verify.paths(manuscript)
    copy = io.BytesIO()
    verify.commented_copy(manuscript, copy, result)
    one, two, three = st.columns(3)
    one.download_button(_("Rapport (Markdown)"), verify.render_report(result).encode("utf-8"),
                        file_name=names["md"].name, key="verify-md")  # fmt: skip
    two.download_button(_("Rapport (Excel)"), verify.report_xlsx(result),
                        file_name=names["xlsx"].name, key="verify-xlsx")  # fmt: skip
    three.download_button(_("Copie commentée (Word)"), copy.getvalue(),
                          file_name=names["docx"].name, key="verify-docx")  # fmt: skip
