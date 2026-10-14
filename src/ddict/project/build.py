"""Build a new project from a database, through the privacy gate."""

from __future__ import annotations

from ddict.groups import GroupCandidate, find_groups
from ddict.i18n import _
from ddict.io.model import LoadedData
from ddict.privacy import MIN_CELL_COUNT, SafeVariable, classify_database, safe_database
from ddict.profile import profile_database
from ddict.profile.compute import MAX_OBSERVED_VALUES
from ddict.project.model import (
    FileMetadata,
    Group,
    MissingRange,
    MissingToken,
    ObservedCount,
    Privacy,
    Profile,
    Project,
    Settings,
    SourceInfo,
    TrackedValue,
    ValueLabel,
    VariableEntry,
)

# Statistics are stored rounded: enough for a codebook, and stable across platforms.
DECIMALS = 4


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, DECIMALS) + 0.0


def _profile(safe: SafeVariable) -> Profile:
    observed = None
    if safe.observed_values is not None:
        observed = [
            ObservedCount(code=c.code, count=c.count, declared_missing=c.declared_missing)
            for c in safe.observed_values
        ]
    return Profile(
        inferred_type=safe.inferred_type,
        n_rows=safe.n_rows,
        n_valid=safe.n_valid,
        n_system_missing=safe.n_system_missing,
        n_declared_missing=safe.n_declared_missing,
        n_distinct=safe.n_distinct,
        min=_round(safe.min),
        max=_round(safe.max),
        mean=_round(safe.mean),
        sd=_round(safe.sd),
        median=_round(safe.median),
        q1=_round(safe.q1),
        q3=_round(safe.q3),
        date_min=safe.date_min,
        date_max=safe.date_max,
        n_non_numeric=safe.n_non_numeric,
        observed_values=observed,
        n_rare_values_hidden=safe.n_rare_values_hidden,
        unlabeled_codes=list(safe.unlabeled_codes),
        unused_labels=list(safe.unused_labels),
        suspect_missing_codes=list(safe.suspect_missing_codes),
        flags=list(safe.flags),
        duplicate_of=safe.duplicate_of,
    )


def _entry(safe: SafeVariable, storage_type: str, storage_width: int | None) -> VariableEntry:
    return VariableEntry(
        name=safe.name,
        position=safe.position,
        file=FileMetadata(
            storage_type=storage_type,
            storage_width=storage_width,
            display_format=safe.display_format,
            measure_level=safe.measure_level,
            label=safe.label,
            value_labels=[ValueLabel(code=c, label=t) for c, t in safe.value_labels.items()],
            declared_missing=[MissingRange(low=m.low, high=m.high) for m in safe.declared_missing],
            missing_tokens=[MissingToken(token=t, count=n) for t, n in safe.missing_tokens.items()],
        ),
        profile=_profile(safe),
        privacy=Privacy(
            privacy_class=TrackedValue[str](value=safe.privacy_class, origin="computed"),
            reasons=list(safe.privacy_reasons),
        ),
        label=TrackedValue[str](value=safe.label, origin="file" if safe.label else "human"),
        description=TrackedValue[str](origin="human"),
        unit=TrackedValue[str](origin="human"),
        group_id=TrackedValue[str](origin="human"),
    )


def descriptive_label(group: GroupCandidate) -> str:
    """A neutral description of what the items have in common, never a guess at a name."""
    parts = [_("{n} items").format(n=len(group.members))]
    if group.code_min is not None:
        parts.append(
            _("codes de {low} à {high}").format(
                low=f"{group.code_min:g}", high=f"{group.code_max:g}"
            )
        )
    if group.prefix:
        parts.append(_("préfixe « {prefix} »").format(prefix=group.prefix))
    else:
        parts.append(_("variables voisines aux mêmes étiquettes"))
    return ", ".join(parts)


def _group(group: GroupCandidate) -> Group:
    return Group(
        group_id=group.group_id,
        members=TrackedValue[list[str]](value=list(group.members), origin="computed"),
        basis=list(group.basis),
        descriptive_label=TrackedValue[str](value=descriptive_label(group), origin="computed"),
        ai_hypothesis=TrackedValue[str](origin="human"),
        n_complete_rows=group.n_complete_rows,
        cronbach_alpha=group.cronbach_alpha,
        cronbach_alpha_reversed=group.cronbach_alpha_reversed,
    )


def _with_group(entry: VariableEntry, groups: tuple[GroupCandidate, ...]) -> VariableEntry:
    for group in groups:
        for item in group.items:
            if item.name == entry.name:
                profile = entry.profile.model_copy(
                    update={
                        "item_rest_r": item.item_rest_r,
                        "reverse_suspect": item.reverse_suspect,
                    }
                )
                return entry.model_copy(
                    update={
                        "profile": profile,
                        "group_id": TrackedValue[str](value=group.group_id, origin="computed"),
                    }
                )
    return entry


def build_project(data: LoadedData, *, min_cell_count: int = MIN_CELL_COUNT) -> Project:
    """Profile, classify and group, then keep only what the privacy gate lets through."""
    profiles = profile_database(data)
    classes = classify_database(data, profiles)
    safe = safe_database(
        data.variables, profiles, classes, audience="storage", threshold=min_cell_count
    )
    groups = find_groups(data, profiles, classes)
    source = data.source
    return Project(
        source=SourceInfo(
            name=source.name,
            format=source.format,
            sha256=source.sha256,
            n_rows=source.n_rows,
            n_columns=source.n_columns,
            label=source.label,
            encoding=source.encoding,
            delimiter=source.delimiter,
            decimal=source.decimal,
        ),
        settings=Settings(min_cell_count=min_cell_count, max_observed_values=MAX_OBSERVED_VALUES),
        variables=[
            _with_group(_entry(s, v.storage_type, v.storage_width), groups)
            for s, v in zip(safe, data.variables, strict=True)
        ],
        groups=[_group(g) for g in groups],
    )
