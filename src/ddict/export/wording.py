"""What the exports show, shared by the Excel codebook and the Markdown report.

Two kinds of export (CONCEPTION.md, § 8): "final" shows only values from the file, from
computation, or accepted by a person; "work" also shows pending AI proposals, marked.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from ddict import glossary
from ddict.i18n import N_, Texts, _, colon, decimal, quoted, semicolon
from ddict.profile.compute import is_missing_label
from ddict.profile.variants import spelling_variants
from ddict.project import completeness, measure, scoring
from ddict.project.build import GROUP_PARTS
from ddict.project.decisions import is_accepted
from ddict.project.model import (
    Code,
    Group,
    Profile,
    Project,
    SentinelDecision,
    TrackedValue,
    VariableEntry,
)
from ddict.questionnaire import link
from ddict.questionnaire.labels import accepted_labels

ExportKind = Literal["final", "work"]

MASKED = N_("masqué")

TYPES = Texts(
    {
        "empty": N_("vide"),
        "boolean": N_("binaire"),
        "integer": N_("entier"),
        "decimal": N_("décimal"),
        "date": N_("date"),
        "datetime": N_("date et heure"),
        "text": N_("texte"),
        "mixed": N_("mixte"),
    }
)
MEASURES = Texts({"nominal": N_("nominal"), "ordinal": N_("ordinal"), "scale": N_("échelle")})
PRIVACY = Texts(
    {
        "ordinary": N_("ordinaire"),
        "likely_identifier": N_("identifiant probable"),
        "free_text": N_("texte libre"),
        "quasi_identifier": N_("quasi-identifiant"),
    }
)
REASONS = Texts(
    {
        "identifier_name": N_("nom ou étiquette d'identifiant"),
        "email_values": N_("valeurs au format courriel"),
        "phone_values": N_("valeurs au format téléphone"),
        "unique_text_values": N_("textes tous différents"),
        "free_text_name": N_("nom de texte libre"),
        "long_text_values": N_("textes longs"),
        "birth_date_name": N_("nom de date de naissance"),
        "birth_place_name": N_("nom de lieu de naissance"),
        "postal_code_name": N_("nom de code postal"),
        "postal_code_values": N_("valeurs au format code postal"),
        "wide_date_range": N_("dates étalées sur de nombreuses années"),
    }
)
ORIGINS = Texts(
    {
        "file": N_("fichier"),
        "computed": N_("calcul"),
        "ai": N_("IA"),
        "questionnaire": N_("questionnaire"),
        "rule": N_("règle"),
        "reference": N_("vague précédente"),
        "human": N_("humain"),
    }
)
GLOSSARY_ORIGINS = Texts({"questionnaire": N_("Questionnaire"), "human": N_("Équipe")})
GLOSSARY_STATUSES = Texts(
    {
        "none": "",
        "proposed": N_("à valider"),
        "validated": N_("validé"),
        "corrected": N_("corrigé"),
        "rejected": N_("rejeté"),
    }
)
STATUSES = Texts(
    {
        "none": "",
        "proposed": N_("proposé par IA"),
        "validated": N_("validé"),
        "corrected": N_("corrigé"),
        "rejected": N_("rejeté"),
    }
)


@dataclass(frozen=True)
class Shown:
    """A value as an export shows it, with a mark when it is a pending AI proposal."""

    value: object
    pending: bool = False


def shown(tracked: TrackedValue, kind: ExportKind) -> Shown | None:
    if is_accepted(tracked):
        return Shown(tracked.value)
    if kind == "work" and tracked.status == "proposed" and tracked.value is not None:
        return Shown(tracked.value, pending=True)
    return None


def status_text(tracked: TrackedValue) -> str:
    """The status of a value; a proposal of the naming rules or of an earlier wave is
    "proposé", not "proposé par IA"."""
    if tracked.status == "proposed" and tracked.origin != "ai":
        return _("proposé")
    return STATUSES[tracked.status]


# --- New names (v0.7, D-048): only accepted ones are applied in a final export. ---


def renamed(project: Project, kind: ExportKind) -> bool:
    """Whether this export shows new names: accepted ones, and proposals in a work export."""
    return any(shown(e.new_name, kind) is not None for e in project.variables)


def name_text(entry: VariableEntry, kind: ExportKind) -> str:
    """The name of a variable in this export: its accepted new name, else its own; in a work
    export, a proposed new name, marked."""
    value = shown(entry.new_name, kind)
    if value is None:
        return entry.name
    return f"{value.value} [{_('proposé')}]" if value.pending else str(value.value)


def final_name(entry: VariableEntry) -> str:
    """The name the data has once the decisions are applied: only an accepted new name."""
    return entry.new_name.value if is_accepted(entry.new_name) else entry.name


def names_of(project: Project) -> dict[str, str]:
    """Original name -> final name, for every variable."""
    return {e.name: final_name(e) for e in project.variables}


def correspondence_rows(project: Project, kind: ExportKind) -> list[tuple[str, str, str, str]]:
    """(original name, new name, status, origin) for each variable this export renames."""
    rows = []
    for entry in project.variables:
        value = shown(entry.new_name, kind)
        if value is None:
            continue
        tracked = entry.new_name
        rows.append((entry.name, str(value.value), status_text(tracked), ORIGINS[tracked.origin]))
    return rows


def text(tracked: TrackedValue, kind: ExportKind) -> str:
    value = shown(tracked, kind)
    if value is None:
        return ""
    suffix = f" [{STATUSES['proposed']}]" if value.pending else ""
    return f"{value.value}{suffix}"


def label_text(entry: VariableEntry, kind: ExportKind) -> str:
    """The label shown; while an AI label is not accepted, the file's label stays."""
    value = text(entry.label, kind)
    if value:
        return value
    return entry.file.label or ""


def number(value: float | None) -> str:
    """A statistic as the language writes it: 0,363 in French, 0.363 in English."""
    if value is None:
        return ""
    return str(int(value)) if float(value).is_integer() else decimal(f"{value:g}")


def code_text(code: Code) -> str:
    """A code as in the data file (decimal point), since it identifies a value."""
    if isinstance(code, int | float):
        return str(int(code)) if float(code).is_integer() else f"{code:g}"
    return str(code)


def codes(values: list[Code]) -> str:
    return ", ".join(code_text(c) for c in values)


def anomalies(
    profile: Profile, decided: frozenset = frozenset(), labels: dict | None = None
) -> list[str]:
    """Deterministic findings, in plain French. `decided`: suspect missing codes the team
    already settled (D-028), no longer anomalies. `labels`: the value labels of the file,
    to say which suspect codes are such by their label (v0.7, D-047)."""
    labels = labels or {}
    found = []
    for code in profile.unlabeled_codes:
        found.append(_("Code {code} observé sans étiquette").format(code=code_text(code)))
    for code in profile.suspect_missing_codes:
        if code in decided:
            continue
        label = labels.get(code)
        if label is not None and is_missing_label(label):
            found.append(
                _("Code {code} ({label}) probablement manquant, non déclaré").format(
                    code=code_text(code), label=quoted(label)
                )
            )
            continue
        found.append(
            _("Valeur {code} probablement manquante, non déclarée").format(code=code_text(code))
        )
    for code in profile.unused_labels:
        found.append(_("Étiquette {code} jamais utilisée").format(code=code_text(code)))
    if "all_missing" in profile.flags:
        found.append(_("Variable entièrement vide"))
    if "constant" in profile.flags:
        found.append(_("Variable constante"))
    if "measure_level_doubtful" in profile.flags:
        found.append(
            _(
                "Niveau de mesure « échelle » douteux : chaque valeur observée a une étiquette "
                "(ordinal probable)"
            )
        )
    if "mixed_types" in profile.flags:
        found.append(
            _("Types mélangés ({n} valeurs non numériques)").format(n=profile.n_non_numeric)
        )
    if profile.reverse_suspect:
        found.append(
            _("Item probablement inversé (corrélation avec le reste de l'échelle : {r})").format(
                r=number(profile.item_rest_r)
            )
        )
    if profile.duplicate_of:
        found.append(_("Identique à {name}").format(name=profile.duplicate_of))
    for group in spelling_variants(profile):
        found.append(
            _("Variantes d'écriture d'une même réponse : {spellings}").format(
                spellings=", ".join(quoted(code) for code in group)
            )
        )
    if profile.n_rare_values_hidden:
        found.append(
            _("{n} catégories rares retirées (confidentialité)").format(
                n=profile.n_rare_values_hidden
            )
        )
    return found


def notes(profile: Profile) -> list[str]:
    """Deterministic findings that describe the variable without being anomalies."""
    if "checkbox" in profile.flags:
        return [
            _(
                "Case à cocher probable : une seule valeur observée, les cases vides "
                "veulent sans doute dire « non coché »"
            )
        ]
    return []


def confirmed_missing(entry: VariableEntry) -> list[Code]:
    """Suspect codes the team confirmed as missing codes (D-028)."""
    return [d.code for d in entry.sentinel_decisions if d.missing]


def entry_anomalies(entry: VariableEntry) -> list[str]:
    """The anomalies of a variable, without the suspect codes the team settled, nor a
    doubtful measure level the team decided (v0.8)."""
    profile = entry.profile
    if entry.measure_level.status != "proposed" and entry.measure_level.value:
        flags = [f for f in profile.flags if f != "measure_level_doubtful"]
        profile = profile.model_copy(update={"flags": flags})
    return anomalies(
        profile,
        frozenset(d.code for d in entry.sentinel_decisions),
        {item.code: item.label for item in entry.file.value_labels},
    )


def level_text(entry: VariableEntry, kind: ExportKind) -> str:
    """The measure level shown: the one in force; in a work export, a proposal, marked."""
    tracked = entry.measure_level
    if kind == "work" and tracked.status == "proposed" and tracked.value:
        return f"{MEASURES[tracked.value]} [{_('proposé')}]"
    found = measure.level(entry)
    return MEASURES[found] if found else ""


def sentinel_notes_for(decision: SentinelDecision) -> str:
    code = code_text(decision.code)
    if decision.missing:
        return _("Code {code} confirmé comme manquant par l'équipe").format(code=code)
    return _("Valeur {code} confirmée comme vraie valeur par l'équipe").format(code=code)


def sentinel_notes(entry: VariableEntry) -> list[str]:
    return [sentinel_notes_for(d) for d in entry.sentinel_decisions]


def issues(entry: VariableEntry, kind: ExportKind) -> list[str]:
    """Anomalies and notes computed, then accepted (or, in a work export, pending) AI
    findings."""
    found = entry_anomalies(entry) + notes(entry.profile) + sentinel_notes(entry)
    found.extend(t for t in (text(issue, kind) for issue in entry.issues) if t)
    return found


BASIS = Texts(
    {
        "common_prefix": N_("préfixe commun"),
        "shared_value_labels": N_("mêmes étiquettes de valeurs"),
        "contiguous": N_("variables voisines"),
        "platform_structure": N_("structure de la plateforme"),
    }
)


def _part_pattern(template: str) -> re.Pattern:
    pattern = re.escape(template)
    for name in ("n", "low", "high", "prefix"):
        pattern = pattern.replace(re.escape("{" + name + "}"), f"(?P<{name}>.+?)")
    return re.compile(pattern + "$")


def group_description(group: Group, kind: ExportKind) -> str:
    """The description of a group; a computed one, stored in French, in the language of the
    moment. Any other text (a person's) is shown as written."""
    stored = text(group.descriptive_label, kind)
    if group.descriptive_label.origin != "computed" or not stored:
        return stored
    parts = []
    for part in stored.split(", "):
        for template in GROUP_PARTS:
            found = _part_pattern(template).match(part)
            if found:
                parts.append(_(template).format(**found.groupdict()))
                break
        else:
            return stored  # not written by this version of the tool: as is
    return ", ".join(parts)


def basis_text(basis: list[str]) -> str:
    return ", ".join(BASIS.get(b, b) for b in basis)


def missing_codes(entry: VariableEntry) -> str:
    parts = []
    for item in entry.file.declared_missing:
        if item.low == item.high:
            parts.append(code_text(item.low))
        else:
            parts.append(f"{code_text(item.low)} – {code_text(item.high)}")
    for code in confirmed_missing(entry):
        parts.append(_("{code} (confirmé par l'équipe)").format(code=code_text(code)))
    for item in entry.file.missing_tokens:
        parts.append(_("« {token} » lu comme vide ({n})").format(token=item.token, n=item.count))
    return ", ".join(parts)


def privacy_text(entry: VariableEntry) -> str:
    privacy_class = entry.privacy.privacy_class.value or "ordinary"
    label = PRIVACY.get(privacy_class, privacy_class)
    if not entry.privacy.reasons:
        return label
    reasons = ", ".join(REASONS.get(r, r) for r in entry.privacy.reasons)
    return f"{label} ({reasons})"


def pct_missing(profile: Profile) -> float:
    missing = profile.n_system_missing + profile.n_declared_missing
    return round(100 * missing / profile.n_rows, 1) if profile.n_rows else 0.0


def value_rows(entry: VariableEntry) -> list[tuple[str, str, str, bool]]:
    """Code, label, count ("masqué" when masked, "" when not observed or not listed), missing."""
    labels = {lab.code: lab.label for lab in accepted_labels(entry)}
    observed = {o.code: o for o in entry.profile.observed_values or []}
    declared = {m.low for m in entry.file.declared_missing if m.low == m.high}
    declared |= set(confirmed_missing(entry))
    rows = []
    for code in sorted(set(labels) | set(observed), key=lambda c: (isinstance(c, str), c)):
        count = ""
        if code in observed:
            count = _(MASKED) if observed[code].count is None else str(observed[code].count)
        elif entry.profile.observed_values is not None:
            count = "0"
        is_missing = code in declared or (code in observed and observed[code].declared_missing)
        rows.append((code_text(code), labels.get(code, ""), count, is_missing))
    return rows


# --- v0.2: what comes from the questionnaire (step 9). ---

OMITTED_TEXT = N_("texte omis : instrument protégé par le droit d'auteur (D-014)")
NO_QUESTION_TEXT = N_("aucune question du questionnaire")
LABELS_FROM_QUESTIONNAIRE = N_(
    "étiquettes tirées des options de la question, ordre vérifié par l'équipe"
)
LABELS_PROPOSED = N_("étiquettes proposées à partir des options, ordre supposé, à vérifier")


def omitted_variables(project: Project, extra_groups: Iterable[str] = ()) -> set[str]:
    """Variables whose question text is not exported: members of the groups the team
    marked (D-014), and of the groups named for this export (`--sans-texte`)."""
    chosen = set(extra_groups)
    names: set[str] = set()
    for group in project.groups:
        if group.omit_question_text or group.group_id in chosen:
            names.update(group.members.value or [])
    return names


def question_reference(project: Project, entry: VariableEntry, kind: ExportKind) -> Shown | None:
    """The link as shown: "Q7.r3, p. 3", or that the variable comes from no question."""
    value = shown(entry.question, kind)
    if value is None:
        return None
    if value.value == link.NO_QUESTION:
        return Shown(_(NO_QUESTION_TEXT), value.pending)
    found = link.target(project.questionnaire, value.value)
    if found is None:
        return None
    page = f", p. {found.question.page}" if found.question.page else ""
    return Shown(f"{value.value}{page}", value.pending)


def question_text(
    project: Project, entry: VariableEntry, kind: ExportKind, omitted: set[str]
) -> str:
    """The exact words of the linked question, read in the questionnaire; never anything
    else of it (paragraphs and the consent page are not exported, D-012)."""
    value = shown(entry.question, kind)
    if value is None or value.value == link.NO_QUESTION:
        return ""
    found = link.target(project.questionnaire, value.value)
    if found is None:
        return ""
    if entry.name in omitted:
        return _(OMITTED_TEXT)
    text = link.target_text(found)
    return f"{text} [{_('rattachement proposé')}]" if value.pending else text


def value_labels_source(entry: VariableEntry, kind: ExportKind) -> str:
    """Where the value labels of a variable come from, when not from the file."""
    if entry.file.value_labels:
        return ""
    if is_accepted(entry.value_labels):
        return _(LABELS_FROM_QUESTIONNAIRE)
    if kind == "work" and entry.value_labels.status == "proposed":
        return _(LABELS_PROPOSED)
    return ""


def glossary_rows(project: Project, kind: ExportKind) -> list[tuple[str, str, str, str, str]]:
    """Term, meaning, origin, status, source: accepted entries, and in a work export the
    ones still waiting for a decision."""
    rows = []
    for item in project.glossary:
        if not glossary.is_accepted(item) and not (kind == "work" and item.status == "proposed"):
            continue
        rows.append(
            (
                item.term,
                item.meaning,
                GLOSSARY_ORIGINS[item.origin],
                GLOSSARY_STATUSES[item.status],
                item.source or "",
            )
        )
    return rows


def questionnaire_facts(project: Project) -> list[tuple[str, str]]:
    """The questionnaire as a documented source: its name, pages and fingerprint."""
    questionnaire = project.questionnaire
    if questionnaire is None:
        return []
    pages = f" ({questionnaire.n_pages} pages)" if questionnaire.n_pages else ""
    linked = sum(1 for e in project.variables if is_accepted(e.question))
    return [
        (_("Questionnaire"), f"{questionnaire.file_name}{pages}"),
        (_("Empreinte SHA-256 du questionnaire"), questionnaire.sha256),
        (_("Variables rattachées à une question"), str(linked)),
    ]


# --- v0.8, step 4: the scoring of a group and the description of the database. ---

AGGREGATIONS = Texts({"sum": N_("somme"), "mean": N_("moyenne")})
MISSING_RULES = Texts(
    {
        "prorate": N_(
            "items manquants : somme proportionnelle (moyenne des items répondus "
            "multipliée par {n})"
        ),
        "sum_answered": N_("items manquants : somme des items répondus"),
    }
)
UNITS = Texts(
    {
        "participant": N_("un participant"),
        "repeated_observation": N_("une observation répétée"),
        "dyad": N_("une dyade"),
        "family": N_("une famille"),
        "other": N_("autre"),
    }
)
STRUCTURES = Texts(
    {
        "cross_sectional": N_("transversale"),
        "one_wave_per_file": N_("longitudinale, une vague par fichier"),
        "wide": N_("longitudinale, format large (une colonne par temps)"),
        "long": N_("longitudinale, format long (une ligne par temps)"),
    }
)
DESIGN = Texts(
    {
        "cluster_id": N_("identifiant de regroupement"),
        "time": N_("variable de temps"),
        "wave": N_("vague"),
        "cluster": N_("grappe"),
        "weight": N_("pondération"),
    }
)


def scoring_text(project: Project, group: Group) -> str:
    """The scoring in one sentence, with its source: "sommeil_total = somme des 8 items,
    après inversion de q3, q6 (6 - x) ; au moins 7 items répondus ; étendue 8 – 40"."""
    found = group.scoring
    if found is None:
        return ""
    names = names_of(project)
    parts = []
    if scoring.structured(found):
        low, high = scoring.score_range(found)
        text = _("{score} = {how} des {n} items").format(
            score=found.score_name, how=AGGREGATIONS[found.aggregation], n=len(found.items)
        )
        reverse = scoring.reversed_items(group, found)
        if reverse:
            text += _(", après inversion de {items} ({total} - x)").format(
                items=", ".join(names.get(r, r) for r in reverse),
                total=number(found.scale_min + found.scale_max),
            )
        parts.append(text)
        if found.min_items_answered:
            parts.append(
                _("au moins {n} items répondus, sinon manquant").format(n=found.min_items_answered)
            )
        if scoring.partial_sum(found):
            parts.append(MISSING_RULES[found.missing_rule].format(n=len(found.items)))
        parts.append(_("étendue {low} – {high}").format(low=number(low), high=number(high)))
    if found.note:
        parts.append(found.note)
    return semicolon().join(parts) + f" ({_('source')}{colon()}{found.source})"


def dataset_facts(project: Project) -> list[tuple[str, str]]:
    """What the team wrote of the database, for the head of the exports."""
    found = project.dataset
    facts = []
    if found.unit_of_observation:
        unit = UNITS[found.unit_of_observation]
        if found.unit_of_observation == "other" and found.unit_other:
            unit = found.unit_other
        facts.append((_("Une ligne représente"), unit))
    if is_accepted(found.structure):
        structure = STRUCTURES[found.structure.value]
        if found.structure.value == "one_wave_per_file" and found.wave:
            structure += f"{semicolon()}{_('vague')} {found.wave}"
        if found.structure.value == "wide" and found.time_suffixes:
            structure += f" ({', '.join(found.time_suffixes)})"
        facts.append((_("Structure"), structure))
    names = names_of(project)
    design = [
        f"{DESIGN[key]}{colon()}{names.get(value, value)}"
        for key in DESIGN
        if (value := getattr(found.design, key))
    ]
    if design:
        facts.append((_("Variables de plan"), semicolon().join(design)))
    if found.description:
        facts.append((_("Description de la base"), found.description))
    return facts


# --- v0.8, step 5: how complete the codebook is. ---

COMPLETENESS = Texts(
    {
        "question": N_("Question rattachée"),
        "label": N_("Libellé"),
        "value_labels": N_("Étiquettes de valeurs (variables codées)"),
        "measure_level": N_("Niveau de mesure"),
        "new_name": N_("Nouveau nom"),
        "scoring": N_("Cotation (groupes d'échelle)"),
    }
)
DATASET_PARTS = Texts({"unit": N_("ce qu'est une ligne"), "structure": N_("la structure")})
SHOWN_MISSING = 10


def missing_text(names: list[str]) -> str:
    """At most ten names, then how many more."""
    text = ", ".join(names[:SHOWN_MISSING])
    if len(names) > SHOWN_MISSING:
        text += " " + _("et {n} autres").format(n=len(names) - SHOWN_MISSING)
    return text


def completeness_rows(project: Project) -> list[tuple[str, str, str]]:
    """(element, "decided / applicable", what is missing), the database last."""
    rows = [
        (COMPLETENESS[p.key], f"{p.done} / {p.applicable}", missing_text(p.missing))
        for p in completeness.parts(project)
    ]
    missing = completeness.dataset_missing(project)
    rows.append(
        (
            _("Description de la base"),
            _("dite") if not missing else _("incomplète"),
            ", ".join(DATASET_PARTS[m] for m in missing),
        )
    )
    return rows
