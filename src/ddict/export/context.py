"""The analysis context (v0.8, step 6, D-058, D-066): the codebook as an analysis contract.

Two files from one source, always final (accepted values only): `<base>-contexte.md`, short
enough to be pasted into a model, and `<base>-datapackage.json`, a Frictionless Data Package
v2 whose properties of the tool are in `_ddict` objects. Format: CONCEPTION.md, § 8.1, and
the examples of `docs/exemples-contexte/`.

What is not in them: proposals, statuses, model calls, detailed provenance, and any observed
value (a spelling variant is said, not quoted). Statistics only on request (D-059), as the
privacy gate let them into the project: counts below the threshold stay masked, and nothing
is given of a sensitive variable.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ddict import __version__
from ddict.export import wording as w
from ddict.i18n import N_, Texts, _, colon, in_language, semicolon
from ddict.profile.variants import spelling_variants
from ddict.project import aside, completeness, fingerprint, measure, scoring
from ddict.project.decisions import is_accepted
from ddict.project.model import Group, NoDatabase, Project, VariableEntry
from ddict.questionnaire import link
from ddict.questionnaire.labels import accepted_labels

SCHEMA = "https://datapackage.org/profiles/2.0/datapackage.json"
TABLE_SCHEMA = "https://datapackage.org/profiles/2.0/tableschema.json"
FIELD_TYPES = {
    "integer": "integer",
    "decimal": "number",
    "text": "string",
    "mixed": "string",
    "date": "date",
    "datetime": "datetime",
    "boolean": "boolean",
    "empty": "any",
}
FORMATS = {"sav": "SPSS", "csv": "CSV", "xlsx": "Excel", "dta": "Stata", "sas7bdat": "SAS"}
MEDIATYPES = {
    "sav": "application/x-spss-sav",
    "csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "dta": "application/x-stata-dta",
    "sas7bdat": "application/x-sas-data",
}
RULES = (
    "missing_values_excluded",
    "reverse_items_before_scores",
    "sensitive_never_in_outputs",
    "undocumented_is_unknown",
)
MULTIPLE_RESPONSE_RULE = "multiple_response_empty_is_unchecked"
RULE_TEXTS = Texts(
    {
        "missing_values_excluded": N_(
            "Les codes de la colonne « Manquants » sont des valeurs manquantes : les exclure "
            "de tout calcul."
        ),
        "reverse_items_before_scores": N_(
            "Inverser les items marqués « inv » avant tout score, selon la cotation de leur groupe."
        ),
        "sensitive_never_in_outputs": N_(
            "Les variables marquées « sensible » ne doivent apparaître dans aucune sortie "
            "(ni valeurs, ni listes)."
        ),
        "undocumented_is_unknown": N_(
            "« Non documenté » veut dire inconnu : ne pas le deviner. Ne citer aucun seuil, "
            "étendue ou instrument absent de ce document."
        ),
        MULTIPLE_RESPONSE_RULE: N_(
            "Question à cocher (groupe « réponses multiples ») : une case vide est une option "
            "non cochée, sauf si toutes les cases de la question sont vides (question sans "
            "réponse)."
        ),
    }
)
SENSITIVE = Texts(
    {
        "likely_identifier": N_("identifiant"),
        "quasi_identifier": N_("quasi-identifiant"),
        "free_text": N_("texte libre"),
    }
)
KINDS = Texts({"scale": N_("échelle"), "multiple_response": N_("réponses multiples")})
COPY_SUFFIX = "-documente.sav"


# --- What both files say. ---


def _sensitive(entry: VariableEntry) -> str | None:
    found = entry.privacy.privacy_class.value or "ordinary"
    return found if found in measure.SENSITIVE else None


def _renamed(project: Project) -> bool:
    return any(w.final_name(e) != e.name for e in aside.kept(project))


def _groups_of(project: Project) -> dict[str, Group]:
    found = {}
    for group in project.groups:
        for name in [*(group.members.value or []), *group.attached]:
            found[name] = group
    return found


def _reversed(project: Project) -> set[str]:
    return {
        name
        for g in project.groups
        if scoring.structured(g.scoring)
        for name in scoring.reversed_items(g, g.scoring)
    }


def _level(entry: VariableEntry) -> str | None:
    """The level in force, where a level means something: not for a date, an empty or
    mixed variable, or a sensitive one."""
    if _sensitive(entry) or entry.data_type in measure.NO_LEVEL_TYPES:
        return None
    return measure.level(entry)


def _missing(entry: VariableEntry) -> list[tuple[object, str]]:
    """Missing codes, declared or confirmed, with their labels: (code or "low–high", label)."""
    labels = {lab.code: lab.label for lab in accepted_labels(entry)}
    found: list[tuple[object, str]] = []
    for item in entry.file.declared_missing:
        if item.low == item.high:
            found.append((item.low, labels.get(item.low, "")))
        else:
            found.append((f"{w.code_text(item.low)}–{w.code_text(item.high)}", ""))
    for code in w.confirmed_missing(entry):
        if all(code != c for c, _label in found):
            found.append((code, labels.get(code, "")))
    return found


def _categories(entry: VariableEntry) -> list:
    missing = {c for c, _label in _missing(entry)}
    return [lab for lab in accepted_labels(entry) if lab.code not in missing]


def _question(entry: VariableEntry) -> str | None:
    """The accepted link: "Q7.r3", "none", or None (not decided)."""
    return entry.question.value if is_accepted(entry.question) else None


def _shared_values(project: Project, group: Group) -> list | None:
    """The value labels of a scale group, when every item has the same."""
    if group.kind != "scale":
        return None
    found = {
        tuple((lab.code, lab.label) for lab in _categories(project.variable(name)))
        for name in group.members.value or []
    }
    if len(found) == 1 and found != {()}:
        return list(next(iter(found)))
    return None


def _findings(entry: VariableEntry, names: dict[str, str]) -> list[str]:
    """What the profile found that matters for an analysis: without the signals already shown
    elsewhere (probable reversed items, doubtful level), the privacy note, and any observed
    value (a spelling variant is said, not quoted)."""
    profile = entry.profile
    if profile is None:
        return []
    settled = {d.code for d in entry.sentinel_decisions}
    plain = profile.model_copy(
        update={
            "unlabeled_codes": [c for c in profile.unlabeled_codes if c not in settled],
            "reverse_suspect": False,
            "n_rare_values_hidden": 0,
            "duplicate_of": None,
            "observed_values": None,
            "flags": [f for f in profile.flags if f != "measure_level_doubtful"],
        }
    )
    texts = w.anomalies(
        plain,
        frozenset(d.code for d in entry.sentinel_decisions),
        {lab.code: lab.label for lab in entry.file.value_labels},
    )
    if spelling_variants(profile):
        texts.append(_("Variantes d'écriture d'une même réponse"))
    if profile.duplicate_of:
        other = names.get(profile.duplicate_of, profile.duplicate_of)
        texts.append(_("Identique à {name}").format(name=other))
    return texts


def _attention(project: Project) -> list[tuple[str, list[str]]]:
    """The findings, grouped: one line per finding, with the variables it concerns."""
    names = w.names_of(project)
    found: dict[str, list[str]] = {}
    for entry in aside.kept(project):
        for text in _findings(entry, names):
            found.setdefault(text[0].lower() + text[1:], []).append(w.final_name(entry))
    return list(found.items())


# --- The Markdown file. ---


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _code(code: object) -> str:
    return code if isinstance(code, str) else w.code_text(code)


def _values_text(labels: list) -> str:
    return semicolon().join(f"{_code(lab.code)} {lab.label}" for lab in labels)


def _base_line(project: Project) -> str:
    source = project.source
    if source is None:  # v0.20 (D-145): designed before its collection
        return _("Base : {planned} ; {n} variables prévues.").format(
            planned=_(w.PLANNED_DICTIONARY), n=len(aside.kept(project))
        )
    return _(
        "Base : `{name}` ({format}), {rows} lignes, {n} variables. Empreinte du fichier : `{sha}`."
    ).format(
        name=source.name,
        format=FORMATS.get(source.format, source.format),
        rows=source.n_rows,
        n=len(project.variables),
        sha=source.sha256[: fingerprint.SHORT],
    )


def _header(project: Project) -> list[str]:
    source = project.source
    lines = [
        _("# Contexte d'analyse : {name}").format(name=w.dataset_title(project)),
        "",
        "- " + _base_line(project),
        "- "
        + _(
            "Codebook : empreinte `{fingerprint}`, dictionnaire-donnees {version}. Seules les "
            "décisions acceptées par l'équipe y figurent."
        ).format(fingerprint=fingerprint.short(project), version=__version__),
    ]
    lines += [f"- {name}{colon()}{value}" for name, value in w.dataset_facts(project)]
    if _renamed(project) and source is not None:
        lines.append(
            "- "
            + _(
                "Noms : les noms ci-dessous sont les nouveaux noms (nom d'origine entre "
                "parenthèses). Travailler sur la copie documentée `{copy}`, ou sur la base "
                "après le fichier de commandes, qui renomme en premier."
            ).format(copy=Path(source.name).stem + COPY_SUFFIX)
        )
    return [*lines, ""]


def _rules(project: Project) -> list[str]:
    codes = list(RULES)
    if any(g.kind == "multiple_response" for g in project.groups):
        codes.append(MULTIPLE_RESPONSE_RULE)
    lines = [_("## Règles"), ""]
    lines += [f"{n}. {RULE_TEXTS[code]}" for n, code in enumerate(codes, start=1)]
    return [*lines, ""]


def _completeness(project: Project) -> list[str]:
    rows = w.completeness_rows(project)
    lines = [_("## Complétude"), ""]
    lines.append(" · ".join(f"{name} {count}" for name, count, _missing in rows) + ".")
    gaps = [f"{name}{colon()}{missing}" for name, _count, missing in rows if missing]
    if gaps:
        lines.append(_("Non documenté : {gaps}.").format(gaps=semicolon().join(gaps)))
    return [*lines, ""]


def _groups(project: Project, omitted: set[str]) -> list[str]:
    if not project.groups:
        return []
    names = w.names_of(project)
    lines = [_("## Groupes"), ""]
    for group in project.groups:
        items = [names[n] for n in group.members.value or []]
        lines.append(
            f"**{group.group_id}** ({KINDS[group.kind]}, "
            + _("{n} variables").format(n=len(items))
            + ") : "
            + ", ".join(f"`{n}`" for n in items)
            + "."
        )
        shared = _shared_values(project, group)
        if shared:
            text = semicolon().join(f"{_code(c)} {label}" for c, label in shared)
            lines.append(_("Valeurs de tous ses items : {values}.").format(values=text))
        if group.kind == "multiple_response":
            first = project.variable(group.members.value[0])
            question = first.file.label or ""
            target = _question(first)
            if target and target != link.NO_QUESTION and project.questionnaire is not None:
                found = link.target(project.questionnaire, target)
                if found is not None:
                    question = found.question.text
            if first.name in omitted:
                question = _(w.OMITTED_TEXT)
            lines.append(
                _(
                    "Question : {question} Chaque option : 1 = cochée, vide = non cochée ; le "
                    "libellé de la ligne est l'option."
                ).format(question=question)
            )
        if group.attached:
            lines.append(
                _("Texte « autre » : {names}.").format(
                    names=", ".join(f"`{names[n]}`" for n in group.attached)
                )
            )
        if group.scoring is not None:
            lines.append(f"{_('Cotation')}{colon()}{w.scoring_text(project, group)}.")
        elif group.kind == "scale":
            lines.append(_("Cotation : non documentée."))
        lines.append("")
    return lines


def _variables(project: Project) -> list[str]:
    groups = _groups_of(project)
    reverse = _reversed(project)
    shared = {g.group_id for g in project.groups if _shared_values(project, g)}
    header = [
        _("Variable"),
        _("Libellé"),
        _("Type"),
        _("Niveau"),
        _("Valeurs"),
        _("Manquants"),
        _("Groupe"),
        _("Question"),
        _("Note"),
    ]
    lines = [_("## Variables"), "", "| " + " | ".join(header) + " |", "|---" * len(header) + "|"]
    for entry in aside.kept(project):
        group = groups.get(entry.name)
        name = w.final_name(entry)
        shown = f"`{name}`" + (f" ({entry.name})" if name != entry.name else "")
        label = w.label_text(entry, "final") or _("non documenté")
        if group is not None and group.kind == "multiple_response" and _categories(entry):
            label = _categories(entry)[0].label
        if group is not None and group.group_id in shared and entry.name not in group.attached:
            values = f"→ {group.group_id}"
        else:
            values = _values_text(_categories(entry))
        missing = ", ".join(_code(c) for c, _label in _missing(entry))
        target = _question(entry)
        question = _("aucune") if target == link.NO_QUESTION else (target or "")
        notes = []
        if _sensitive(entry):
            notes.append(_("sensible ({kind})").format(kind=SENSITIVE[_sensitive(entry)]))
        if entry.name in reverse:
            notes.append("inv")
        if entry.profile is not None and entry.profile.sum_of_group:
            notes.append(_("score de {group}").format(group=entry.profile.sum_of_group))
        level = _level(entry)
        cells = [
            shown,
            label,
            w.TYPES.get(entry.data_type, entry.data_type),
            w.MEASURES[level] if level else "",
            values,
            missing,
            group.group_id if group else "",
            question,
            ", ".join(notes),
        ]
        lines.append("| " + " | ".join(_cell(c) for c in cells) + " |")
    return [*lines, ""]


def _presentation(project: Project) -> list[str]:
    """When a variable was asked and how it was presented (v0.21); nothing for a project
    without conditions, random order or attention checks."""
    if not w.has_presentation(project, "final"):
        return []
    lines = [_("## Questions filtrées et présentation"), ""]
    for entry in aside.kept(project):
        parts = []
        asked = w.asked_if_text(project, entry, "final")
        if asked:
            parts.append(_("posée si {condition}").format(condition=asked))
        presentation = w.presentation_text(project, entry)
        if presentation:
            parts.append(presentation)
        if parts:
            lines.append(f"- `{w.final_name(entry)}`{colon()}{semicolon().join(parts)}")
    return [*lines, ""]


def _attention_lines(project: Project) -> list[str]:
    found = _attention(project)
    if not found:
        return []
    lines = [_("## Points d'attention"), ""]
    lines += [f"- {', '.join(f'`{n}`' for n in names)}{colon()}{text}." for text, names in found]
    return [*lines, ""]


def _statistics(project: Project) -> list[str]:
    lines = [
        _("## Statistiques"),
        "",
        _(
            "Effectifs inférieurs à {n} masqués ; aucune statistique pour une variable sensible."
        ).format(n=project.settings.min_cell_count),
        "",
    ]
    for entry in aside.kept(project):
        if _sensitive(entry):
            continue
        text = _statistics_text(entry)
        if text:
            lines.append(f"- `{w.final_name(entry)}`{colon()}{text}")
    return [*lines, ""]


def _statistics_text(entry: VariableEntry) -> str:
    p = entry.profile
    parts = [_("n = {n}").format(n=p.n_valid)]
    if p.mean is not None and measure.level(entry) == "scale":
        parts.append(_("moyenne {mean}").format(mean=w.number(p.mean)))
        if p.sd is not None:
            parts.append(_("é.-t. {sd}").format(sd=w.number(p.sd)))
        if p.min is not None and p.max is not None:
            parts.append(f"{w.number(p.min)} – {w.number(p.max)}")
        return ", ".join(parts)
    counts = [
        f"{code} {label}: {count}".replace(" :", ":") if label else f"{code}: {count}"
        for code, label, count, _is_missing in w.value_rows(entry)
        if count
    ]
    if not counts:
        return ""
    return ", ".join(parts) + semicolon() + semicolon().join(counts)


def _question_texts(project: Project, omitted: set[str]) -> list[str]:
    if project.questionnaire is None:
        return []
    by_question: dict[str, list] = {}
    order = {q.question_id: n for n, q in enumerate(project.questionnaire.questions)}
    checkboxes = {n for g in project.groups if g.kind == "multiple_response"
                  for n in [*(g.members.value or []), *g.attached]}  # fmt: skip
    for entry in aside.kept(project):
        target = _question(entry)
        if not target or target == link.NO_QUESTION:
            continue
        found = link.target(project.questionnaire, target)
        if found is None:
            continue
        question_id = found.question.question_id
        text = _(w.OMITTED_TEXT) if entry.name in omitted else found.question.text
        lines = by_question.setdefault(question_id, [f"- **{question_id}** {text}"])
        if (
            found.part
            and entry.name not in omitted
            and entry.name not in checkboxes
            and found.part != w.label_text(entry, "final")
        ):
            lines.append(f"  - {target} (`{w.final_name(entry)}`){colon()}{found.part}")
    if not by_question:
        return []
    lines = [_("## Texte des questions"), ""]
    for question_id in sorted(by_question, key=lambda q: order.get(q, len(order))):
        lines += by_question[question_id]
    return [*lines, ""]


def _recodes(project: Project) -> list[str]:
    """v0.15 (D-120): the recoded variables, not in the file: the preparation script makes
    them."""
    if not project.recodes.rules:
        return []
    lines = [
        _("## Variables recodées"),
        "",
        _(
            "Absentes du fichier : le script de préparation les crée, après les scores et avant "
            "les exclusions."
        ),
        "",
    ]
    for _id, name, label, level, source, parts, reason in w.recode_rows(project):
        lines.append(
            f"- `{name}` ({level}) — {label}{colon()}"
            + _("tirée de {source} : {parts}. Raison : {reason}").format(
                source=f"`{source}`", parts=parts, reason=reason
            )
        )
    return [*lines, ""]


@in_language
def render_context(
    project: Project, *, statistics: bool = False, omit_groups: tuple[str, ...] = ()
) -> str:
    """The analysis context in Markdown, to be read by a person or pasted into a model."""
    omitted = w.omitted_variables(project, omit_groups)
    lines = _header(project) + _rules(project) + _completeness(project)
    lines += _groups(project, omitted) + _recodes(project) + _variables(project)
    lines += _presentation(project)
    lines += _attention_lines(project)
    if statistics and project.source is not None:
        lines += _statistics(project)
    lines += _question_texts(project, omitted)
    return "\n".join(lines).rstrip("\n") + "\n"


# --- The Data Package. ---


def _field(project: Project, entry: VariableEntry, groups: dict, statistics: bool) -> dict:
    if entry.set_aside is not None:  # D-158: the column is in the file, nothing said of it
        return {
            "name": entry.name,
            "type": FIELD_TYPES.get(entry.data_type, "any"),
            "_ddict": {"set_aside": entry.set_aside.reason},
        }
    field: dict = {"name": w.final_name(entry)}
    label = w.label_text(entry, "final")
    if label:
        field["title"] = label
    description = w.text(entry.description, "final")
    if description:
        field["description"] = description
    field["type"] = FIELD_TYPES.get(entry.data_type, "any")
    level = _level(entry)
    categories = _categories(entry)
    if categories:
        field["categories"] = [{"value": lab.code, "label": lab.label} for lab in categories]
        field["categoriesOrdered"] = level == "ordinal"
    missing = _missing(entry)
    if missing:
        field["missingValues"] = [
            {"value": _code(code), **({"label": label} if label else {})} for code, label in missing
        ]
    if entry.theoretical_range is not None:
        field["constraints"] = {
            "minimum": entry.theoretical_range.min,
            "maximum": entry.theoretical_range.max,
        }
    extra: dict = {}
    if w.final_name(entry) != entry.name:
        extra["original_name"] = entry.name
    if level:
        extra["measure_level"] = level
    target = _question(entry)
    if target is not None:
        extra["question"] = None if target == link.NO_QUESTION else target
    if entry.name in groups:
        extra["group"] = groups[entry.name].group_id
    unit = w.text(entry.unit, "final")
    if unit:
        extra["unit"] = unit
    if entry.theoretical_range is not None:
        extra["range_source"] = entry.theoretical_range.source
    if entry.thresholds:
        extra["thresholds"] = [t.model_dump(mode="json") for t in entry.thresholds]
    if _sensitive(entry):
        extra["privacy"] = _sensitive(entry)
    elif statistics:
        extra["statistics"] = _field_statistics(entry)
    if extra:
        field["_ddict"] = extra
    return field


def _field_statistics(entry: VariableEntry) -> dict:
    p = entry.profile
    found: dict = {"n_valid": p.n_valid}
    if p.mean is not None and measure.level(entry) == "scale":
        found |= {"mean": p.mean, "sd": p.sd, "min": p.min, "max": p.max}
    elif p.observed_values:
        found["counts"] = [{"value": o.code, "count": o.count} for o in p.observed_values]
    return found


def _group(project: Project, group: Group) -> dict:
    names = w.names_of(project)
    found: dict = {
        "id": group.group_id,
        "kind": group.kind,
        "items": [names[n] for n in group.members.value or []],
    }
    if group.attached:
        found["attached"] = [names[n] for n in group.attached]
    if group.reverse_items:
        found["reverse_items"] = [names[n] for n in group.reverse_items]
    if group.scoring is not None:
        found["scoring"] = _scoring(project, group)
    return found


def _scoring(project: Project, group: Group) -> dict:
    names = w.names_of(project)
    found = group.scoring
    data: dict = {"source": found.source}
    if scoring.structured(found):
        low, high = scoring.score_range(found)
        data |= {
            "items": [names[n] for n in found.items],
            "reverse_items": [names[n] for n in scoring.reversed_items(group, found)],
            "reverse_rule": found.reverse_rule,
            "scale_min": found.scale_min,
            "scale_max": found.scale_max,
            "aggregation": found.aggregation,
            "min_items_answered": found.min_items_answered,
            "missing_rule": found.missing_rule if scoring.partial_sum(found) else None,
            "score_range": {"min": low, "max": high},
            "score_name": found.score_name,
        }
    if found.note:
        data["note"] = found.note
    return data


def _dataset(project: Project) -> dict:
    found = project.dataset
    names = w.names_of(project)
    design = {
        key: names.get(value, value)
        for key in ("cluster_id", "time", "wave", "cluster", "weight")
        if (value := getattr(found.design, key))
    }
    structure = found.structure.value if is_accepted(found.structure) else None
    data: dict = {
        "unit_of_observation": found.unit_of_observation,
        "structure": structure,
    }
    if found.unit_of_observation == "other" and found.unit_other:
        data["unit_other"] = found.unit_other
    if structure == "one_wave_per_file" and found.wave:
        data["wave"] = found.wave
    if structure == "wide" and found.time_suffixes:
        data["time_suffixes"] = found.time_suffixes
    if design:
        data["design_variables"] = design
    if found.description:
        data["description"] = found.description
    return data


@in_language
def context_package(project: Project, *, statistics: bool = False) -> dict:
    """The Frictionless Data Package v2 of the analysis context."""
    source = project.source
    if source is None:
        raise NoDatabase("context")
    stem = Path(source.name).stem
    renamed = _renamed(project)
    groups = _groups_of(project)
    resource: dict = {
        "name": _resource_name(stem),
        "path": stem + COPY_SUFFIX if renamed else source.name,
        "type": "table",
        "format": "sav" if renamed else source.format,
        "mediatype": MEDIATYPES["sav" if renamed else source.format],
    }
    if not renamed:
        resource["hash"] = f"sha256:{source.sha256}"
    resource["schema"] = {
        "$schema": TABLE_SCHEMA,
        "fields": [_field(project, e, groups, statistics) for e in project.variables],
    }
    resource["_ddict"] = {"rows": source.n_rows}
    if renamed:
        resource["_ddict"]["renamed_from"] = {
            "path": source.name,
            "hash": f"sha256:{source.sha256}",
        }
    rules = list(RULES)
    if any(g.kind == "multiple_response" for g in project.groups):
        rules.append(MULTIPLE_RESPONSE_RULE)
    return {
        "$schema": SCHEMA,
        "name": _resource_name(stem),
        "title": source.label or stem,
        "resources": [resource],
        "_ddict": {
            "tool": f"dictionnaire-donnees {__version__}",
            "codebook_fingerprint": fingerprint.fingerprint(project),
            "language": project.settings.language,
            "statistics": statistics,
            "dataset": _dataset(project),
            "rules": rules,
            "completeness": [
                {
                    "element": p.key,
                    "decided": p.done,
                    "applicable": p.applicable,
                    "missing": p.missing,
                }
                for p in completeness.parts(project)
            ],
            "dataset_missing": completeness.dataset_missing(project),
            "groups": [_group(project, g) for g in project.groups],
            **_package_recodes(project),
        },
    }


def _package_recodes(project: Project) -> dict:
    """v0.15 (D-120): the recoded variables, absent from the file, only when there are some
    (the examples without recodings keep their bytes)."""
    from ddict.project.recodes import source_name

    if not project.recodes.rules:
        return {}
    found = []
    for rule in project.recodes.rules:
        data = rule.model_dump(mode="json")
        data["source"] = source_name(project, rule.source)  # by its final name, in place
        found.append(data)
    return {"recodes": found}


def _resource_name(stem: str) -> str:
    """A Frictionless name: lower case, digits, "-", "_", "." only."""
    return re.sub(r"[^a-z0-9._-]+", "-", stem.lower()).strip("-") or "base"


def package_text(package: dict) -> str:
    return json.dumps(package, ensure_ascii=False, indent=2) + "\n"


def write_context(
    project: Project,
    markdown: Path,
    package: Path,
    *,
    statistics: bool = False,
    omit_groups: tuple[str, ...] = (),
    language: str | None = None,
) -> None:
    text = render_context(
        project, statistics=statistics, omit_groups=omit_groups, language=language
    )
    with Path(markdown).open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
    if project.source is None:  # a Data Package describes a file: none yet (v0.20)
        return
    data = context_package(project, statistics=statistics, language=language)
    with Path(package).open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(package_text(data))
