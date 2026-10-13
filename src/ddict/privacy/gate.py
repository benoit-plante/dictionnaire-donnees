"""The privacy gate: the only way information about a variable leaves the deterministic layer.

Everything sent to the model, written to the project file or exported is built from a
SafeVariable, never from the table nor from the raw profile. A SafeVariable holds file
metadata and aggregates only:

- identifiers, free text and quasi-identifiers keep their name, labels, type and missing
  counts, and nothing computed from their values;
- counts of categories below the threshold (D-006) are masked, with a second count when
  one alone could be recovered by subtraction, and without the mean and sd (D-008);
- counts of declared missing values stay exact (D-007);
- rare text categories, which could be a name or a rare place, are hidden altogether;
- for the model, date ranges are reduced to years.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ddict.io.model import Code, MissingRange, VariableMetadata
from ddict.privacy.classify import PrivacyClass, PrivacyClassification, Reason
from ddict.profile.model import Flag, InferredType, VariableProfile

# Counts of categories below this are masked (D-006).
MIN_CELL_COUNT = 5

Audience = Literal["model", "storage"]


@dataclass(frozen=True)
class SafeCount:
    """A category and its count; count is None when masked (fewer than the threshold)."""

    code: Code
    count: int | None
    declared_missing: bool = False

    @property
    def masked(self) -> bool:
        return self.count is None


@dataclass(frozen=True)
class SafeVariable:
    name: str
    position: int
    label: str | None
    value_labels: dict[Code, str]
    declared_missing: tuple[MissingRange, ...]
    measure_level: str | None
    display_format: str | None
    inferred_type: InferredType
    privacy_class: PrivacyClass
    privacy_reasons: tuple[Reason, ...]
    n_rows: int
    n_valid: int
    n_system_missing: int
    n_declared_missing: int
    n_distinct: int | None = None
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    sd: float | None = None
    median: float | None = None
    q1: float | None = None
    q3: float | None = None
    date_min: str | None = None
    date_max: str | None = None
    n_non_numeric: int | None = None
    observed_values: tuple[SafeCount, ...] | None = None
    n_rare_values_hidden: int = 0
    unlabeled_codes: tuple[Code, ...] = ()
    unused_labels: tuple[Code, ...] = ()
    suspect_missing_codes: tuple[Code, ...] = ()
    flags: tuple[Flag, ...] = ()
    duplicate_of: str | None = None


def _safe_counts(
    profile: VariableProfile, labels: dict[Code, str], threshold: int
) -> tuple[tuple[SafeCount, ...] | None, int, bool]:
    """Return the safe counts, the number of hidden categories, and whether any was masked.

    Counts of declared missing values stay exact (D-007). Among valid values, a single
    small count could be recovered by subtraction from n_valid; the smallest other count is
    then masked too (secondary suppression, D-008).
    """
    if profile.observed_values is None:
        return None, 0, False
    kept: list[SafeCount] = []
    hidden = 0
    for value in profile.observed_values:
        rare = value.count < threshold and not value.declared_missing
        if rare and isinstance(value.code, str) and value.code not in labels:
            hidden += 1
            continue
        kept.append(SafeCount(value.code, None if rare else value.count, value.declared_missing))

    valid = [c for c in kept if not c.declared_missing]
    n_suppressed = hidden + sum(1 for c in valid if c.masked)
    visible = [c for c in valid if not c.masked]
    if n_suppressed == 1 and visible:
        smallest = min(visible, key=lambda c: c.count)
        kept = [SafeCount(c.code, None, False) if c is smallest else c for c in kept]
    return tuple(kept), hidden, n_suppressed > 0


def _numeric_codes(codes: tuple[Code, ...], labels: dict[Code, str]) -> tuple[Code, ...]:
    """Codes are safe when they are numbers or labels from the file, not free strings."""
    return tuple(c for c in codes if not isinstance(c, str) or c in labels)


def safe_variable(
    variable: VariableMetadata,
    profile: VariableProfile,
    classification: PrivacyClassification,
    *,
    audience: Audience,
    threshold: int = MIN_CELL_COUNT,
) -> SafeVariable:
    if not (variable.name == profile.name == classification.name):
        raise ValueError("Metadata, profile and classification of different variables")
    base = dict(
        name=variable.name,
        position=variable.position,
        label=variable.label,
        value_labels=dict(variable.value_labels),
        declared_missing=variable.declared_missing,
        measure_level=variable.measure_level,
        display_format=variable.display_format,
        inferred_type=profile.inferred_type,
        privacy_class=classification.privacy_class,
        privacy_reasons=classification.reasons,
        n_rows=profile.n_rows,
        n_valid=profile.n_valid,
        n_system_missing=profile.n_system_missing,
        n_declared_missing=profile.n_declared_missing,
    )
    if classification.privacy_class != "ordinary":
        return SafeVariable(**base)

    labels = variable.value_labels
    observed, hidden, suppressed = _safe_counts(profile, labels, threshold)
    # With the visible counts, the mean and sd of the codes would reveal the masked ones.
    mean, sd = (None, None) if suppressed else (profile.mean, profile.sd)
    date_min, date_max = profile.date_min, profile.date_max
    if audience == "model" and date_min and date_max:
        date_min, date_max = date_min[:4], date_max[:4]
    return SafeVariable(
        **base,
        n_distinct=profile.n_distinct,
        min=profile.min,
        max=profile.max,
        mean=mean,
        sd=sd,
        median=profile.median,
        q1=profile.q1,
        q3=profile.q3,
        date_min=date_min,
        date_max=date_max,
        n_non_numeric=profile.n_non_numeric,
        observed_values=observed,
        n_rare_values_hidden=hidden,
        unlabeled_codes=_numeric_codes(profile.unlabeled_codes, labels),
        unused_labels=profile.unused_labels,
        suspect_missing_codes=_numeric_codes(profile.suspect_missing_codes, labels),
        flags=profile.flags,
        duplicate_of=profile.duplicate_of,
    )


def safe_database(
    variables: tuple[VariableMetadata, ...],
    profiles: tuple[VariableProfile, ...],
    classifications: tuple[PrivacyClassification, ...],
    *,
    audience: Audience,
    threshold: int = MIN_CELL_COUNT,
) -> tuple[SafeVariable, ...]:
    return tuple(
        safe_variable(v, p, c, audience=audience, threshold=threshold)
        for v, p, c in zip(variables, profiles, classifications, strict=True)
    )
