"""What the exports show, shared by the Excel codebook and the Markdown report.

Two kinds of export (CONCEPTION.md, § 8): "final" shows only values from the file, from
computation, or accepted by a person; "work" also shows pending AI proposals, marked.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ddict.i18n import _
from ddict.project.decisions import is_accepted
from ddict.project.model import Code, Profile, TrackedValue, VariableEntry

ExportKind = Literal["final", "work"]

MASKED = _("masqué")

TYPES = {
    "empty": _("vide"),
    "boolean": _("binaire"),
    "integer": _("entier"),
    "decimal": _("décimal"),
    "date": _("date"),
    "datetime": _("date et heure"),
    "text": _("texte"),
    "mixed": _("mixte"),
}
MEASURES = {"nominal": _("nominal"), "ordinal": _("ordinal"), "scale": _("échelle")}
PRIVACY = {
    "ordinary": _("ordinaire"),
    "likely_identifier": _("identifiant probable"),
    "free_text": _("texte libre"),
    "quasi_identifier": _("quasi-identifiant"),
}
REASONS = {
    "identifier_name": _("nom ou étiquette d'identifiant"),
    "email_values": _("valeurs au format courriel"),
    "phone_values": _("valeurs au format téléphone"),
    "unique_text_values": _("textes tous différents"),
    "free_text_name": _("nom de texte libre"),
    "long_text_values": _("textes longs"),
    "birth_date_name": _("nom de date de naissance"),
    "postal_code_name": _("nom de code postal"),
    "postal_code_values": _("valeurs au format code postal"),
    "wide_date_range": _("dates étalées sur de nombreuses années"),
}
ORIGINS = {"file": _("fichier"), "computed": _("calcul"), "ai": _("IA"), "human": _("humain")}
STATUSES = {
    "none": "",
    "proposed": _("proposé par IA"),
    "validated": _("validé"),
    "corrected": _("corrigé"),
    "rejected": _("rejeté"),
}


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


def text(tracked: TrackedValue, kind: ExportKind) -> str:
    value = shown(tracked, kind)
    if value is None:
        return ""
    suffix = f" [{STATUSES['proposed']}]" if value.pending else ""
    return f"{value.value}{suffix}"


def number(value: float | None) -> str:
    """A statistic written the French way: decimal comma (0,363)."""
    if value is None:
        return ""
    return str(int(value)) if float(value).is_integer() else f"{value:g}".replace(".", ",")


def code_text(code: Code) -> str:
    """A code as in the data file (decimal point), since it identifies a value."""
    if isinstance(code, int | float):
        return str(int(code)) if float(code).is_integer() else f"{code:g}"
    return str(code)


def codes(values: list[Code]) -> str:
    return ", ".join(code_text(c) for c in values)


def anomalies(profile: Profile) -> list[str]:
    """Deterministic findings, in plain French."""
    found = []
    for code in profile.unlabeled_codes:
        found.append(_("Code {code} observé sans étiquette").format(code=code_text(code)))
    for code in profile.suspect_missing_codes:
        found.append(
            _("Valeur {code} probablement manquante, non déclarée").format(code=code_text(code))
        )
    for code in profile.unused_labels:
        found.append(_("Étiquette {code} jamais utilisée").format(code=code_text(code)))
    if "all_missing" in profile.flags:
        found.append(_("Variable entièrement vide"))
    if "constant" in profile.flags:
        found.append(_("Variable constante"))
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
    if profile.n_rare_values_hidden:
        found.append(
            _("{n} catégories rares retirées (confidentialité)").format(
                n=profile.n_rare_values_hidden
            )
        )
    return found


def issues(entry: VariableEntry, kind: ExportKind) -> list[str]:
    """Anomalies computed, then accepted (or, in a work export, pending) AI findings."""
    found = anomalies(entry.profile)
    found.extend(t for t in (text(issue, kind) for issue in entry.issues) if t)
    return found


BASIS = {
    "common_prefix": _("préfixe commun"),
    "shared_value_labels": _("mêmes étiquettes de valeurs"),
    "contiguous": _("variables voisines"),
}


def basis_text(basis: list[str]) -> str:
    return ", ".join(BASIS.get(b, b) for b in basis)


def missing_codes(entry: VariableEntry) -> str:
    parts = []
    for item in entry.file.declared_missing:
        if item.low == item.high:
            parts.append(code_text(item.low))
        else:
            parts.append(f"{code_text(item.low)} – {code_text(item.high)}")
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
    labels = {lab.code: lab.label for lab in entry.file.value_labels}
    observed = {o.code: o for o in entry.profile.observed_values or []}
    declared = {m.low for m in entry.file.declared_missing if m.low == m.high}
    rows = []
    for code in sorted(set(labels) | set(observed), key=lambda c: (isinstance(c, str), c)):
        count = ""
        if code in observed:
            count = MASKED if observed[code].count is None else str(observed[code].count)
        elif entry.profile.observed_values is not None:
            count = "0"
        is_missing = code in declared or (code in observed and observed[code].declared_missing)
        rows.append((code_text(code), labels.get(code, ""), count, is_missing))
    return rows
