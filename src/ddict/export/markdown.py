"""The Markdown report: an overview, then one section per variable."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from ddict.export import wording as w
from ddict.i18n import _
from ddict.project.model import Project, VariableEntry


def _cell(value: object) -> str:
    """Table cells: pipes escaped, line breaks turned into spaces."""
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _inline(value: object) -> str:
    return str(value).replace("\r", " ").replace("\n", " ")


def _overview(project: Project, kind: w.ExportKind) -> list[str]:
    source = project.source
    types = Counter(w.TYPES.get(e.profile.inferred_type, "") for e in project.variables)
    sensitive = [
        e for e in project.variables if (e.privacy.privacy_class.value or "ordinary") != "ordinary"
    ]
    flagged = [e for e in project.variables if w.issues(e, kind)]
    kind_text = _("finale") if kind == "final" else _("de travail (propositions de l'IA incluses)")
    lines = [
        _("# Dictionnaire de données : {name}").format(name=_inline(source.name)),
        "",
        f"- {_('Fichier')} : `{_inline(source.name)}`"
        + (f" ({_inline(source.label)})" if source.label else ""),
        f"- {_('Empreinte SHA-256')} : `{source.sha256}`",
        f"- {_('Lignes')} : {source.n_rows} ; {_('variables')} : {source.n_columns}",
        f"- {_('Version')} : {kind_text}",
        "- "
        + _("Effectifs inférieurs à {n} masqués (« < {n} »).").format(
            n=project.settings.min_cell_count
        ),
        "",
        _("## Vue d'ensemble"),
        "",
        f"| {_('Type')} | {_('Variables')} |",
        "|---|---|",
    ]
    lines += [f"| {_cell(t)} | {n} |" for t, n in sorted(types.items())]
    lines += [
        "",
        _("- Variables sensibles : {n}").format(n=len(sensitive))
        + (f" ({', '.join(f'`{e.name}`' for e in sensitive)})" if sensitive else ""),
        _("- Variables avec signalements : {n}").format(n=len(flagged)),
        "",
    ]
    return lines


def _variable(entry: VariableEntry, kind: w.ExportKind) -> list[str]:
    p = entry.profile
    label = w.text(entry.label, kind)
    title = f"### `{entry.name}`" + (f" — {_inline(label)}" if label else "")
    lines = [title, ""]
    description = w.text(entry.description, kind)
    if description:
        lines += [_inline(description), ""]

    facts = [
        f"{_('Type')} : {w.TYPES.get(p.inferred_type, p.inferred_type)}",
    ]
    if entry.file.measure_level:
        facts.append(f"{_('Niveau de mesure')} : {w.MEASURES[entry.file.measure_level]}")
    unit = w.text(entry.unit, kind)
    if unit:
        facts.append(f"{_('Unité')} : {_inline(unit)}")
    facts.append(
        _(
            "Valides : {valid} ; cases vides : {empty} ; manquants déclarés : {declared} ({pct} %)"
        ).format(
            valid=p.n_valid,
            empty=p.n_system_missing,
            declared=p.n_declared_missing,
            pct=f"{w.pct_missing(p):g}",
        )
    )
    if entry.file.declared_missing:
        facts.append(f"{_('Codes manquants déclarés')} : {w.missing_codes(entry)}")
    if p.min is not None:
        stats = f"{_('Min')} {w.number(p.min)} ; {_('max')} {w.number(p.max)}"
        if p.mean is not None:
            stats += f" ; {_('moyenne')} {w.number(p.mean)}"
        if p.sd is not None:
            stats += f" ; {_('écart-type')} {w.number(p.sd)}"
        stats += f" ; {_('médiane')} {w.number(p.median)}"
        facts.append(stats)
    if p.date_min:
        facts.append(f"{_('Dates')} : {p.date_min} – {p.date_max}")
    if p.n_distinct is not None:
        facts.append(f"{_('Valeurs distinctes')} : {p.n_distinct}")
    privacy_class = entry.privacy.privacy_class.value or "ordinary"
    facts.append(f"{_('Confidentialité')} : {w.privacy_text(entry)}")
    if privacy_class != "ordinary":
        facts.append(_("Variable sensible : aucune statistique sur ses valeurs."))
    if entry.theoretical_range:
        r = entry.theoretical_range
        facts.append(
            f"{_('Étendue théorique')} : {w.number(r.min)} – {w.number(r.max)} "
            f"({_('source')} : {_inline(r.source)})"
        )
    for t in entry.thresholds:
        facts.append(
            f"{_('Seuil')} {w.number(t.value)} : {_inline(t.meaning)} "
            f"({_('source')} : {_inline(t.source)})"
        )
    for reference in entry.references:
        facts.append(f"{_('Référence')} : {_inline(reference)}")
    lines += [f"- {fact}" for fact in facts] + [""]

    rows = w.value_rows(entry)
    if rows:
        lines += [
            f"| {_('Code')} | {_('Étiquette')} | {_('Effectif')} | {_('Manquant déclaré')} |",
            "|---|---|---|---|",
        ]
        for code, value_label, count, is_missing in rows:
            missing = _("oui") if is_missing else ""
            lines.append(f"| {_cell(code)} | {_cell(value_label)} | {count} | {missing} |")
        lines.append("")

    found = w.issues(entry, kind)
    if found:
        lines += [f"**{_('Signalements')}**", ""] + [f"- {_inline(f)}" for f in found] + [""]
    if entry.notes:
        lines += [f"**{_('Notes')}** : {_inline(entry.notes)}", ""]
    return lines


def render_markdown(project: Project, *, kind: w.ExportKind = "final") -> str:
    lines = _overview(project, kind)
    lines += [_("## Variables"), ""]
    for entry in project.variables:
        lines += _variable(entry, kind)
    return "\n".join(lines).rstrip("\n") + "\n"


def write_markdown(project: Project, path: Path | str, *, kind: w.ExportKind = "final") -> None:
    with Path(path).open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(render_markdown(project, kind=kind))
