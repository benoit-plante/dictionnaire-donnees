"""The Markdown report: an overview, then one section per variable."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from ddict.export import wording as w
from ddict.i18n import _, colon, field_label, in_language, semicolon
from ddict.project import fingerprint
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
        f"- {field_label('Fichier')}`{_inline(source.name)}`"
        + (f" ({_inline(source.label)})" if source.label else ""),
        f"- {field_label('Empreinte SHA-256')}`{source.sha256}`",
        f"- {field_label('Lignes')}{source.n_rows}{semicolon()}"
        f"{field_label('variables')}{source.n_columns}",
        f"- {field_label('Version')}{kind_text}",
        f"- {field_label('Empreinte du codebook')}`{fingerprint.short(project)}` "
        + _("(décisions acceptées)"),
        "- "
        + _(
            "Effectifs inférieurs à {n} masqués, ainsi qu'un second effectif quand le "
            "premier pourrait être recalculé par soustraction."
        ).format(n=project.settings.min_cell_count),
    ]
    lines += [
        f"- {name}{colon()}{_inline(value)}" for name, value in w.questionnaire_facts(project)
    ]
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
        + (f" ({', '.join(f'`{w.final_name(e)}`' for e in sensitive)})" if sensitive else ""),
        _("- Variables avec signalements : {n}").format(n=len(flagged)),
        "",
    ]
    return lines


def _variable(
    project: Project, entry: VariableEntry, kind: w.ExportKind, omitted: set[str]
) -> list[str]:
    p = entry.profile
    label = w.label_text(entry, kind)
    title = f"### `{w.name_text(entry, kind)}`" + (f" — {_inline(label)}" if label else "")
    lines = [title, ""]
    if w.shown(entry.new_name, kind) is not None:  # v0.7: renamed in this export
        original = field_label("Nom d'origine")
        lines += [f"{original}`{entry.name}`", ""]
    description = w.text(entry.description, kind)
    if description:
        lines += [_inline(description), ""]
    reference = w.question_reference(project, entry, kind)
    if reference is not None:
        question = f"{_('Question')} ({_inline(reference.value)})"
        text = w.question_text(project, entry, kind, omitted)  # marked when only proposed
        if reference.pending and not text:
            question += f" [{_('rattachement proposé')}]"
        lines += [f"> {question}{colon()}{_inline(text)}" if text else f"> {question}", ""]

    facts = [
        f"{field_label('Type')}{w.TYPES.get(p.inferred_type, p.inferred_type)}",
    ]
    if entry.file.measure_level:
        facts.append(f"{field_label('Niveau de mesure')}{w.MEASURES[entry.file.measure_level]}")
    unit = w.text(entry.unit, kind)
    if unit:
        facts.append(f"{field_label('Unité')}{_inline(unit)}")
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
        facts.append(f"{field_label('Codes manquants déclarés')}{w.missing_codes(entry)}")
    if p.min is not None:
        stats = f"{_('Min')} {w.number(p.min)}{semicolon()}{_('max')} {w.number(p.max)}"
        if p.mean is not None:
            stats += f"{semicolon()}{_('moyenne')} {w.number(p.mean)}"
        if p.sd is not None:
            stats += f"{semicolon()}{_('écart-type')} {w.number(p.sd)}"
        stats += f"{semicolon()}{_('médiane')} {w.number(p.median)}"
        facts.append(stats)
    if p.date_min:
        facts.append(f"{field_label('Dates')}{p.date_min} – {p.date_max}")
    if p.n_distinct is not None:
        facts.append(f"{field_label('Valeurs distinctes')}{p.n_distinct}")
    group = w.text(entry.group_id, kind)
    if group:
        fact = f"{field_label('Groupe')}{_inline(group)}"
        if p.item_rest_r is not None:
            fact += " " + _("(corrélation avec le reste du groupe : {r})").format(
                r=w.number(p.item_rest_r)
            )
        facts.append(fact)
    privacy_class = entry.privacy.privacy_class.value or "ordinary"
    facts.append(f"{field_label('Confidentialité')}{w.privacy_text(entry)}")
    if privacy_class != "ordinary":
        facts.append(_("Variable sensible : aucune statistique sur ses valeurs."))
    if entry.theoretical_range:
        r = entry.theoretical_range
        facts.append(
            f"{field_label('Étendue théorique')}{w.number(r.min)} – {w.number(r.max)} "
            f"({field_label('source')}{_inline(r.source)})"
        )
    for t in entry.thresholds:
        facts.append(
            f"{_('Seuil')} {w.number(t.value)}{colon()}{_inline(t.meaning)} "
            f"({field_label('source')}{_inline(t.source)})"
        )
    for reference in entry.references:
        facts.append(f"{field_label('Référence')}{_inline(reference)}")
    lines += [f"- {fact}" for fact in facts] + [""]

    rows = w.value_rows(entry)
    source = w.value_labels_source(entry, kind)
    if source == _(w.LABELS_PROPOSED):
        proposed = "; ".join(
            f"{w.code_text(v.code)} = {_inline(v.label)}" for v in entry.value_labels.value or []
        )
        lines += [f"*{source}*{colon()}{proposed}", ""]
    elif source and rows:
        lines += [f"*{field_label('Étiquettes de valeurs')}{source}.*", ""]
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
        lines += [f"**{_('Notes')}**{colon()}{_inline(entry.notes)}", ""]
    return lines


def _groups(project: Project, kind: w.ExportKind) -> list[str]:
    if not project.groups:
        return []
    lines = [_("## Groupes de variables"), ""]
    for group in project.groups:
        description = w.group_description(group, kind)
        lines += [f"### {group.group_id}" + (f" — {_inline(description)}" if description else "")]
        lines.append("")
        members = w.shown(group.members, kind)
        names = w.names_of(project)
        facts = []
        if members:
            facts.append(
                f"{field_label('Variables')}"
                + ", ".join(f"`{names.get(m, m)}`" for m in members.value)
            )
        facts.append(f"{field_label('Indices du regroupement')}{w.basis_text(group.basis)}")
        hypothesis = w.text(group.ai_hypothesis, kind)
        if hypothesis:
            facts.append(_("Hypothèse de l'IA") + f" : {_inline(hypothesis)}")
        if group.instrument_name:
            facts.append(
                f"{field_label('Instrument')}{_inline(group.instrument_name.value)} "
                f"({field_label('source')}{_inline(group.instrument_name.source)})"
            )
        suspects = [
            e.name
            for e in project.variables
            if e.profile.reverse_suspect and members and e.name in members.value
        ]
        if suspects:
            facts.append(
                f"{field_label('Items probablement inversés')}"
                + ", ".join(f"`{names[s]}`" for s in suspects)
            )
        if group.reverse_items:
            facts.append(
                f"{field_label('Items inversés confirmés')}"
                + ", ".join(f"`{names.get(s, s)}`" for s in group.reverse_items)
            )
        if group.cronbach_alpha is not None:
            alpha = _("Alpha de Cronbach observé : {alpha} ({n} lignes complètes)").format(
                alpha=w.number(group.cronbach_alpha), n=group.n_complete_rows
            )
            if group.cronbach_alpha_reversed is not None:
                alpha += semicolon() + _("avec les items probables inversés : {alpha}").format(
                    alpha=w.number(group.cronbach_alpha_reversed)
                )
            facts.append(alpha)
        lines += [f"- {fact}" for fact in facts] + [""]
    return lines


def _correspondence(project: Project, kind: w.ExportKind) -> list[str]:
    """Original name -> new name (v0.7), when this export renames variables."""
    rows = w.correspondence_rows(project, kind)
    if not rows:
        return []
    lines = [
        _("## Correspondance des noms"),
        "",
        "| " + " | ".join([_("Nom d'origine"), _("Nouveau nom"), _("Statut"), _("Origine")]) + " |",
        "|---|---|---|---|",
    ]
    lines += [f"| `{a}` | `{b}` | {_cell(c)} | {_cell(d)} |" for a, b, c, d in rows]
    return [*lines, ""]


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


@in_language
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
    lines += _correspondence(project, kind)
    return "\n".join(lines).rstrip("\n") + "\n"


@in_language
def write_markdown(
    project: Project,
    path: Path | str,
    *,
    kind: w.ExportKind = "final",
    omit_groups: tuple[str, ...] = (),
) -> None:
    with Path(path).open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(render_markdown(project, kind=kind, omit_groups=omit_groups))
