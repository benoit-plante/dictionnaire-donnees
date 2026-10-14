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
        + _(
            "Effectifs inférieurs à {n} masqués, ainsi qu'un second effectif quand le "
            "premier pourrait être recalculé par soustraction."
        ).format(n=project.settings.min_cell_count),
    ]
    lines += [f"- {name} : {_inline(value)}" for name, value in w.questionnaire_facts(project)]
    lines += [
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


def _variable(
    project: Project, entry: VariableEntry, kind: w.ExportKind, omitted: set[str]
) -> list[str]:
    p = entry.profile
    label = w.label_text(entry, kind)
    title = f"### `{entry.name}`" + (f" — {_inline(label)}" if label else "")
    lines = [title, ""]
    description = w.text(entry.description, kind)
    if description:
        lines += [_inline(description), ""]
    reference = w.question_reference(project, entry, kind)
    if reference is not None:
        question = f"{_('Question')} ({_inline(reference.value)})"
        text = w.question_text(project, entry, kind, omitted)  # marked when only proposed
        if reference.pending and not text:
            question += f" [{_('rattachement proposé')}]"
        lines += [f"> {question} : {_inline(text)}" if text else f"> {question}", ""]

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
            pct=w.number(w.pct_missing(p)),
        )
    )
    if w.missing_codes(entry):
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
    group = w.text(entry.group_id, kind)
    if group:
        fact = f"{_('Groupe')} : {_inline(group)}"
        if p.item_rest_r is not None:
            fact += " " + _("(corrélation avec le reste du groupe : {r})").format(
                r=w.number(p.item_rest_r)
            )
        facts.append(fact)
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
    source = w.value_labels_source(entry, kind)
    if source == w.LABELS_PROPOSED:
        proposed = "; ".join(
            f"{w.code_text(v.code)} = {_inline(v.label)}" for v in entry.value_labels.value or []
        )
        lines += [f"*{source}* : {proposed}", ""]
    elif source and rows:
        lines += [f"*{_('Étiquettes de valeurs')} : {source}.*", ""]
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


def _groups(project: Project, kind: w.ExportKind) -> list[str]:
    if not project.groups:
        return []
    lines = [_("## Groupes de variables"), ""]
    for group in project.groups:
        description = w.text(group.descriptive_label, kind)
        lines += [f"### {group.group_id}" + (f" — {_inline(description)}" if description else "")]
        lines.append("")
        members = w.shown(group.members, kind)
        facts = []
        if members:
            facts.append(f"{_('Variables')} : " + ", ".join(f"`{m}`" for m in members.value))
        facts.append(f"{_('Indices du regroupement')} : {w.basis_text(group.basis)}")
        hypothesis = w.text(group.ai_hypothesis, kind)
        if hypothesis:
            facts.append(_("Hypothèse de l'IA") + f" : {_inline(hypothesis)}")
        if group.instrument_name:
            facts.append(
                f"{_('Instrument')} : {_inline(group.instrument_name.value)} "
                f"({_('source')} : {_inline(group.instrument_name.source)})"
            )
        suspects = [
            e.name
            for e in project.variables
            if e.profile.reverse_suspect and members and e.name in members.value
        ]
        if suspects:
            facts.append(
                f"{_('Items probablement inversés')} : " + ", ".join(f"`{s}`" for s in suspects)
            )
        if group.reverse_items:
            facts.append(
                f"{_('Items inversés confirmés')} : "
                + ", ".join(f"`{s}`" for s in group.reverse_items)
            )
        if group.cronbach_alpha is not None:
            alpha = _("Alpha de Cronbach observé : {alpha} ({n} lignes complètes)").format(
                alpha=w.number(group.cronbach_alpha), n=group.n_complete_rows
            )
            if group.cronbach_alpha_reversed is not None:
                alpha += " ; " + _("avec les items probables inversés : {alpha}").format(
                    alpha=w.number(group.cronbach_alpha_reversed)
                )
            facts.append(alpha)
        lines += [f"- {fact}" for fact in facts] + [""]
    return lines


def _glossary(project: Project, kind: w.ExportKind) -> list[str]:
    rows = w.glossary_rows(project, kind)
    if not rows:
        return []
    lines = [
        _("## Glossaire des sigles"),
        "",
        f"| {_('Sigle')} | {_('Définition')} | {_('Origine')} | {_('Statut')} | {_('Source')} |",
        "|---|---|---|---|---|",
    ]
    lines += ["| " + " | ".join(_cell(v) for v in row) + " |" for row in rows]
    return [*lines, ""]


def render_markdown(
    project: Project, *, kind: w.ExportKind = "final", omit_groups: tuple[str, ...] = ()
) -> str:
    """`omit_groups`: groups whose question text is left out of this export (D-014)."""
    omitted = w.omitted_variables(project, omit_groups)
    lines = _overview(project, kind)
    lines += _glossary(project, kind)
    lines += _groups(project, kind)
    lines += [_("## Variables"), ""]
    for entry in project.variables:
        lines += _variable(project, entry, kind, omitted)
    return "\n".join(lines).rstrip("\n") + "\n"


def write_markdown(
    project: Project,
    path: Path | str,
    *,
    kind: w.ExportKind = "final",
    omit_groups: tuple[str, ...] = (),
) -> None:
    with Path(path).open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(render_markdown(project, kind=kind, omit_groups=omit_groups))
