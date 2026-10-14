"""The Excel codebook: one sheet per kind of information."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from ddict.export import wording as w
from ddict.i18n import _
from ddict.project.model import Project, TrackedValue

MAX_WIDTH = 60


def _cell_value(value: object) -> object:
    return "" if value is None else value


def _sheet(book: Workbook, title: str, header: list[str], rows: list[list]) -> Worksheet:
    sheet = book.create_sheet(title)
    sheet.append(header)
    for row in rows:
        sheet.append([_cell_value(v) for v in row])
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            # A label starting with "=" must stay text, never become a formula.
            if cell.data_type == "f":
                cell.data_type = "s"
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    sheet.freeze_panes = "B2"
    if rows:
        sheet.auto_filter.ref = sheet.dimensions
    for index, title_text in enumerate(header, start=1):
        values = [str(title_text)] + [str(_cell_value(r[index - 1])) for r in rows]
        width = max(len(line) for v in values for line in v.split("\n"))
        sheet.column_dimensions[get_column_letter(index)].width = min(width + 2, MAX_WIDTH)
    return sheet


def _about(project: Project, kind: w.ExportKind, omit_groups: tuple[str, ...]) -> list[list]:
    source = project.source
    kind_text = (
        _("finale (valeurs acceptées seulement)")
        if kind == "final"
        else _("de travail (propositions de l'IA en attente incluses)")
    )
    return [
        [_("Fichier de données"), source.name],
        [_("Empreinte SHA-256"), source.sha256],
        [_("Lignes"), source.n_rows],
        [_("Variables"), source.n_columns],
        [_("Étiquette du fichier"), source.label],
        [_("Version"), kind_text],
        [
            _("Confidentialité"),
            _(
                "Effectifs inférieurs à {n} masqués, ainsi qu'un second effectif quand le "
                "premier pourrait être recalculé par soustraction ; variables sensibles "
                "décrites sans statistiques."
            ).format(n=project.settings.min_cell_count),
        ],
        [_("Format du projet"), project.schema_version],
        *_questionnaire_rows(project, omit_groups),
    ]


def _questionnaire_rows(project: Project, omit_groups: tuple[str, ...]) -> list[list]:
    rows = [[name, value] for name, value in w.questionnaire_facts(project)]
    if not rows:
        return []
    omitted = sorted(
        {g.group_id for g in project.groups if g.omit_question_text} | set(omit_groups)
    )
    rows.append(
        [
            _("Texte des questions"),
            _("omis pour les groupes {groups} (instrument protégé, D-014)").format(
                groups=", ".join(omitted)
            )
            if omitted
            else _("exporté pour toutes les variables rattachées"),
        ]
    )
    return rows


def _variables(project: Project, kind: w.ExportKind, omitted: set[str]) -> list[list]:
    rows = []
    for e in project.variables:
        reference = w.question_reference(project, e, kind)
        p = e.profile
        sourced_range = ""
        if e.theoretical_range:
            r = e.theoretical_range
            sourced_range = f"{w.number(r.min)} – {w.number(r.max)} ({r.source})"
        thresholds = "\n".join(
            f"{w.number(t.value)} : {t.meaning} ({t.source})" for t in e.thresholds
        )
        rows.append(
            [
                e.position,
                e.name,
                w.label_text(e, kind),
                w.text(e.description, kind),
                ""
                if reference is None
                else reference.value + (f" [{_('proposé')}]" if reference.pending else ""),
                w.question_text(project, e, kind, omitted),
                w.TYPES.get(p.inferred_type, p.inferred_type),
                w.MEASURES.get(e.file.measure_level or "", ""),
                e.file.display_format,
                w.text(e.unit, kind),
                p.n_valid,
                p.n_system_missing,
                p.n_declared_missing,
                w.pct_missing(p),
                p.n_distinct,
                p.min,
                p.max,
                p.mean,
                p.sd,
                p.median,
                p.date_min,
                p.date_max,
                w.missing_codes(e),
                w.privacy_text(e),
                w.text(e.group_id, kind),
                p.item_rest_r,
                sourced_range,
                thresholds,
                "\n".join(e.references),
                "\n".join(w.issues(e, kind)),
                e.notes,
            ]
        )
    return rows


VARIABLE_HEADER = [
    _("Position"),
    _("Nom"),
    _("Libellé"),
    _("Description"),
    _("Question"),
    _("Texte de la question"),
    _("Type"),
    _("Niveau de mesure"),
    _("Format"),
    _("Unité"),
    _("Valides"),
    _("Cases vides"),
    _("Manquants déclarés"),
    _("% manquants"),
    _("Valeurs distinctes"),
    _("Min"),
    _("Max"),
    _("Moyenne"),
    _("Écart-type"),
    _("Médiane"),
    _("Date min"),
    _("Date max"),
    _("Codes manquants déclarés"),
    _("Confidentialité"),
    _("Groupe"),
    _("Corrélation avec le reste du groupe"),
    _("Étendue théorique (source)"),
    _("Seuils (source)"),
    _("Références"),
    _("Signalements"),
    _("Notes"),
]


def _values(project: Project, kind: w.ExportKind) -> list[list]:
    rows = []
    for e in project.variables:
        source = w.value_labels_source(e, kind)
        for code, label, count, is_missing in w.value_rows(e):
            rows.append(
                [
                    e.name,
                    code,
                    label,
                    count,
                    _("oui") if is_missing else "",
                    source if label else "",
                ]
            )
        if source == w.LABELS_PROPOSED:  # proposals are not mixed with the counts
            for item in e.value_labels.value or []:
                rows.append([e.name, w.code_text(item.code), item.label, "", "", source])
    return rows


def _groups(project: Project, kind: w.ExportKind) -> list[list]:
    rows = []
    for g in project.groups:
        members = w.shown(g.members, kind)
        suspects = [
            e.name
            for e in project.variables
            if e.profile.reverse_suspect and members and e.name in members.value
        ]
        rows.append(
            [
                g.group_id,
                w.text(g.descriptive_label, kind),
                ", ".join(members.value) if members else "",
                w.basis_text(g.basis),
                ", ".join(suspects),
                ", ".join(g.reverse_items),
                w.text(g.ai_hypothesis, kind),
                f"{g.instrument_name.value} ({g.instrument_name.source})"
                if g.instrument_name
                else "",
                f"{g.scoring.value} ({g.scoring.source})" if g.scoring else "",
                g.n_complete_rows,
                g.cronbach_alpha,
                g.cronbach_alpha_reversed,
            ]
        )
    return rows


GROUP_HEADER = [
    _("Groupe"),
    _("Description"),
    _("Variables"),
    _("Indices du regroupement"),
    _("Items inversés probables"),
    _("Items inversés confirmés"),
    _("Hypothèse de l'IA"),
    _("Instrument (source)"),
    _("Cotation (source)"),
    _("Lignes complètes"),
    _("Alpha de Cronbach observé"),
    _("Alpha, items probables inversés"),
]


def _provenance(project: Project, kind: w.ExportKind) -> list[list]:
    rows = []

    def as_text(value: object) -> str:
        if value is None:
            return ""
        return ", ".join(value) if isinstance(value, list) else str(value)

    def add(name: str, field: str, tracked: TrackedValue) -> None:
        value = w.shown(tracked, kind)
        if value is None:
            return
        rows.append(
            [
                name,
                field,
                as_text(value.value),
                w.ORIGINS[tracked.origin],
                w.STATUSES[tracked.status],
                as_text(tracked.proposed_value),
                tracked.ai_run,
            ]
        )

    for e in project.variables:
        add(e.name, _("Question"), e.question)
        if e.value_labels.value is not None:
            value = w.shown(e.value_labels, kind)
            if value is not None:
                rows.append(
                    [
                        e.name,
                        _("Étiquettes de valeurs"),
                        "; ".join(f"{w.code_text(v.code)} = {v.label}" for v in value.value),
                        w.ORIGINS[e.value_labels.origin],
                        w.STATUSES[e.value_labels.status],
                        "",
                        None,
                    ]
                )
        add(e.name, _("Libellé"), e.label)
        add(e.name, _("Description"), e.description)
        add(e.name, _("Unité"), e.unit)
        add(e.name, _("Groupe"), e.group_id)
        add(e.name, _("Confidentialité"), e.privacy.privacy_class)
        for issue in e.issues:
            add(e.name, _("Signalement"), issue)
    for g in project.groups:
        add(g.group_id, _("Variables"), g.members)
        add(g.group_id, _("Description"), g.descriptive_label)
        add(g.group_id, _("Hypothèse de l'IA"), g.ai_hypothesis)
    return rows


def write_xlsx(
    project: Project,
    path: Path | str,
    *,
    kind: w.ExportKind = "final",
    omit_groups: tuple[str, ...] = (),
) -> None:
    """`omit_groups`: groups whose question text is left out of this export (D-014)."""
    omitted = w.omitted_variables(project, omit_groups)
    book = Workbook()
    book.remove(book.active)
    _sheet(book, _("Informations"), [_("Élément"), _("Valeur")], _about(project, kind, omit_groups))
    _sheet(book, _("Variables"), VARIABLE_HEADER, _variables(project, kind, omitted))
    _sheet(
        book,
        _("Valeurs"),
        [
            _("Variable"),
            _("Code"),
            _("Étiquette"),
            _("Effectif"),
            _("Manquant déclaré"),
            _("Source de l'étiquette"),
        ],
        _values(project, kind),
    )
    _sheet(book, _("Groupes"), GROUP_HEADER, _groups(project, kind))
    if project.glossary:
        _sheet(
            book,
            _("Glossaire"),
            [_("Sigle"), _("Définition"), _("Origine"), _("Statut"), _("Source")],
            [list(row) for row in w.glossary_rows(project, kind)],
        )
    _sheet(
        book,
        _("Provenance"),
        [
            _("Variable"),
            _("Champ"),
            _("Valeur"),
            _("Origine"),
            _("Statut"),
            _("Valeur d'origine"),
            _("Appel IA"),
        ],
        _provenance(project, kind),
    )
    book.save(Path(path))
