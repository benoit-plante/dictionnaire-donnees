"""The APA 7 tables and figures on the Analyses page (v0.10, step 5, D-083 to D-086): a
preview of each, its number, title and note to change, and a download for each format of
the list. The numbers inside come from the analysis and never change (D-086).

The page shows what the formats render, from the same description: the table as an HTML
table with the APA rules, the figure as the image the Word file holds.
"""

from __future__ import annotations

import html
import zlib

import streamlit as st

from ddict import i18n
from ddict.analysis.apa import ApaDocument, ApaTable, Edit, Text, describe, edited, plain
from ddict.analysis.formats import available
from ddict.analysis.formats.figures import image
from ddict.i18n import _

FIGURE_WIDTH = 640  # pixels on the page: the image itself is 16 cm at 300 dots per inch
CACHE = "apa-cache"  # (signature, {what: bytes}): images and files, drawn once per state


def _signature(asked: tuple) -> str:
    """A short name for an analysis run, so its fields start again for a new one."""
    return f"{zlib.crc32(repr(asked).encode('utf-8')):08x}"


def _key(signature: str, item: str, field: str) -> str:
    return f"apa-{signature}-{item}-{field}"


def _edits(signature: str, document: ApaDocument) -> dict[str, Edit]:
    """A person's numbers, titles and notes, as the fields hold them now: only what differs
    from the computed document (a note kept as is keeps its italics)."""
    found = {}
    state = st.session_state
    for item in (*document.tables, *document.figures):
        number = state.get(_key(signature, item.key, "number"))
        title = state.get(_key(signature, item.key, "title"))
        note = state.get(_key(signature, item.key, "note"))
        found[item.key] = Edit(
            number=int(number) if number is not None and number != item.number else None,
            title=title if title is not None and title != item.title else None,
            note=note if note is not None and note != plain(item.note) else None,
        )
    return found


def current(project, prepared, result, asked: tuple) -> ApaDocument:
    """The description, in the interface's language, with the fields' values."""
    document = describe(project, prepared, result, language=i18n.language())
    return edited(document, _edits(_signature(asked), document))


def edits(project, prepared, result, asked: tuple) -> dict[str, Edit]:
    """The titles and notes a person changed, for the notebook (v0.11)."""
    document = describe(project, prepared, result, language=i18n.language())
    return _edits(_signature(asked), document)


def rendered(project, prepared, result, asked: tuple, found) -> bytes:
    """A file of the APA tables and figures, with the fields' values, as the panel gives it
    (v0.16: the Word file is in the bar of actions, above the result)."""
    signature = _signature(asked)
    computed = describe(project, prepared, result, language=i18n.language())
    edits = _edits(signature, computed)
    state = repr(sorted((k, e) for k, e in edits.items()))
    document = edited(computed, edits)
    return _cached(signature, ("file", found.key, state), lambda: found.render(document))


def _cached(signature: str, what: tuple, make) -> bytes:
    stored = st.session_state.get(CACHE)
    if stored is None or stored[0] != signature:
        stored = (signature, {})
        st.session_state[CACHE] = stored
    if what not in stored[1]:
        stored[1][what] = make()
    return stored[1][what]


def _html(text: Text) -> str:
    parts = []
    for r in text:
        part = html.escape(r.text)
        part = f"<sub>{part}</sub>" if r.sub else part
        parts.append(f"<i>{part}</i>" if r.italic else part)
    return "".join(parts)


RULE = "border-top:1px solid currentColor;"
LINE = "border-bottom:1px solid currentColor;"


def _table_html(table: ApaTable) -> str:
    """The table as Word shows it: horizontal rules only, the first column left."""
    # "border:none" first: the page's theme draws a line under every row; APA has rules only.
    cell = "border:none;padding:2px 10px;text-align:{align};{border}"
    lines = ["<table style='border:none;border-collapse:collapse;margin:4px 0 8px 0'>"]
    if table.spanners:
        by_first = {s.first: s for s in table.spanners}
        cells, j = [], 0
        while j < len(table.columns):
            spanner = by_first.get(j)
            if spanner is None:
                cells.append(f"<td style='{cell.format(align='center', border=RULE)}'></td>")
                j += 1
                continue
            span = spanner.last - spanner.first + 1
            style = cell.format(align="center", border=RULE) + LINE
            cells.append(f"<td colspan='{span}' style='{style}'>{_html(spanner.label)}</td>")
            j += span
        lines.append("<tr style='border:none'>" + "".join(cells) + "</tr>")
    top = "" if table.spanners else RULE
    lines.append(
        "<tr style='border:none'>"
        + "".join(
            f"<td style='{cell.format(align=c.align, border=top + LINE)}'>{_html(c.header)}</td>"
            for c in table.columns
        )
        + "</tr>"
    )
    for i, row in enumerate(table.rows):
        bottom = LINE if i == len(table.rows) - 1 else ""
        cells = []
        for j, (text, column) in enumerate(zip(row.cells, table.columns, strict=True)):
            indent = f"padding-left:{10 + 18 * row.indent}px;" if j == 0 and row.indent else ""
            style = cell.format(align=column.align, border=bottom) + indent
            cells.append(f"<td style='{style}'>{_html(text)}</td>")
        lines.append("<tr style='border:none'>" + "".join(cells) + "</tr>")
    lines.append("</table>")
    return "".join(lines)


def _fields(signature: str, item, number: int, title: str, note: Text) -> None:
    left, right = st.columns([1, 5])
    left.number_input(
        _("Numéro"), min_value=1, step=1, value=number, key=_key(signature, item, "number")
    )
    right.text_input(_("Titre"), value=title, key=_key(signature, item, "title"))
    st.text_area(_("Note"), value=plain(note), key=_key(signature, item, "note"), height=68)


def _caption(label: str, title: str) -> None:
    st.markdown(f"**{html.escape(label)}**  \n*{html.escape(title)}*", unsafe_allow_html=False)


def panel(project, prepared, result, asked: tuple, files, shown_above: tuple = ()) -> bool:
    """The APA section of the result; the formats of `shown_above` are already in the bar of
    actions. False when the analysis has no APA table nor figure."""
    signature = _signature(asked)
    computed = describe(project, prepared, result, language=i18n.language())
    if not computed.tables and not computed.figures:
        return False
    st.subheader(_("Tableaux et figures APA"))
    st.caption(
        _(
            "Au format APA 7, à télécharger ou à écrire à côté du projet. Le numéro, le titre "
            "et la note se changent ici ; les chiffres viennent du calcul. Dans Word, chaque "
            "tableau reste un vrai tableau ; chaque figure a aussi son graphique Excel natif, "
            "à modifier puis à coller dans Word."
        )
    )
    for table in computed.tables:
        with st.expander(f"{_('Tableau')} {table.number} — {table.title}", expanded=False):
            _fields(signature, table.key, table.number, table.title, table.note)
    for figure in computed.figures:
        with st.expander(f"{_('Figure')} {figure.number} — {figure.title}", expanded=False):
            _fields(signature, figure.key, figure.number, figure.title, figure.note)
    document = edited(computed, _edits(signature, computed))
    for table in document.tables:
        _caption(f"{_('Tableau')} {table.number}", table.title)
        st.markdown(_table_html(table), unsafe_allow_html=True)
        if table.note:
            st.markdown(f"<i>{_('Note.')}</i> {_html(table.note)}", unsafe_allow_html=True)
    for figure in document.figures:
        _caption(f"{_('Figure')} {figure.number}", figure.title)
        st.image(
            _cached(
                signature,
                ("image", figure.key, document.language),
                lambda f=figure: image(f, document.language),
            ),
            width=FIGURE_WIDTH,
        )
        if figure.note:
            st.markdown(f"<i>{_('Note.')}</i> {_html(figure.note)}", unsafe_allow_html=True)
    formats = [f for f in available(document) if f.key not in shown_above]
    columns = st.columns(max(len(formats), 1))
    stem = files.markdown.stem
    for column, found in zip(columns, formats, strict=False):
        state = repr(sorted((k, e) for k, e in _edits(signature, computed).items()))
        column.download_button(
            _(found.label),
            data=_cached(signature, ("file", found.key, state), lambda f=found: f.render(document)),
            file_name=stem + found.suffix,
            mime=found.mime,
            key=f"apa-download-{found.key}",
        )
    return True
