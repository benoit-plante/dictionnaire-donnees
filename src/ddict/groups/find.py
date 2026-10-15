"""Find probable scales without any model, and compute their item statistics.

In the export of a survey platform (v0.7, D-044), the structure of the names makes the
groups of the variables it covers: a grid (`q0003_0001` ... `q0003_0006`) is a scale, a set
of checkboxes (`q0008_0001` ... with `q0008_other`) a group of multiple responses, without
item statistics, its "other" text attached outside the members.

Elsewhere, two clues make a group:
- a common prefix followed by a number (sommeil_q1 ... sommeil_q8), wherever the items are
  in the file;
- a run of neighbouring variables with the same value labels, when they share no prefix.
The same labels alone are not enough: many scales use the same answer options.

Statistics use the table, so they belong to the deterministic layer; only the aggregates
(correlations, alpha) go further. Declared missing values and suspect missing codes are
left out, and only complete rows are used.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from ddict import platforms
from ddict.io.model import LoadedData, VariableMetadata
from ddict.privacy.classify import PrivacyClassification
from ddict.profile.model import VariableProfile

MIN_ITEMS = 3
# Item statistics need at least this many complete rows.
MIN_COMPLETE_ROWS = 10
DECIMALS = 3

Basis = Literal["common_prefix", "shared_value_labels", "contiguous", "platform_structure"]
GroupKind = Literal["scale", "multiple_response"]
# A set of checkboxes is a group from this many options.
MIN_OPTIONS = 2

# Letters in the stem of a numbered item without a separator (see item_prefix).
MIN_STEM_LETTERS = 3

_NUMBERED = re.compile(r"(.*?[A-Za-z])[_.\-]?(\d+)")


@dataclass(frozen=True)
class ItemStatistics:
    name: str
    item_rest_r: float | None  # correlation of the item with the sum of the others
    reverse_suspect: bool


@dataclass(frozen=True)
class GroupCandidate:
    group_id: str
    members: tuple[str, ...]
    basis: tuple[Basis, ...]
    prefix: str | None
    code_min: float | None
    code_max: float | None
    n_complete_rows: int
    cronbach_alpha: float | None
    cronbach_alpha_reversed: float | None  # with the suspect items reversed
    items: tuple[ItemStatistics, ...]
    kind: GroupKind = "scale"
    attached: tuple[str, ...] = ()  # the "other" text of a set of checkboxes


def item_prefix(name: str) -> str | None:
    """The stem of a numbered item: `sommeil_q` for `sommeil_q3`, `anx` for `anx3`.

    A meaningful stem only (v0.7): two letters or more before a separator (`ab_1`), three
    or more without one (`anx3`). `q1`, `q0001` or `q_2` are numbered questions, not items
    of a scale: their stem says nothing.
    """
    match = _NUMBERED.fullmatch(name)
    if match is None:
        return None
    stem = match.group(1)
    letters = sum(character.isalpha() for character in stem)
    separated = name[len(stem)] in "_.-"
    if letters < 2 or (letters < MIN_STEM_LETTERS and not separated):
        return None
    return stem


def _eligible(profile: VariableProfile, classification: PrivacyClassification) -> bool:
    return (
        classification.privacy_class == "ordinary"
        and profile.inferred_type in ("integer", "boolean")
        and "all_missing" not in profile.flags
        and "constant" not in profile.flags
        and "duplicate" not in profile.flags
    )


def _labels_key(variable: VariableMetadata) -> tuple | None:
    if len(variable.value_labels) < 2:
        return None
    return tuple(sorted(variable.value_labels.items(), key=lambda item: str(item[0])))


def _member_sets(
    variables: list[VariableMetadata], eligible: set[str]
) -> list[tuple[list[str], tuple[Basis, ...], str | None]]:
    """Members of the probable scales, among the eligible variables. A variable left out
    (by its privacy class, or being constant...) with the same value labels as the run it
    sits in does not cut that run in two (v0.7): the run goes on without it."""
    groups = []
    by_prefix: dict[str, list[VariableMetadata]] = {}
    for variable in variables:
        if variable.name not in eligible:
            continue
        prefix = item_prefix(variable.name)
        if prefix:
            by_prefix.setdefault(prefix.lower(), []).append(variable)
    grouped: set[str] = set()
    for members in by_prefix.values():
        if len(members) < MIN_ITEMS:
            continue
        positions = [m.position for m in members]
        basis: list[Basis] = ["common_prefix"]
        keys = {_labels_key(m) for m in members}
        if len(keys) == 1 and None not in keys:
            basis.append("shared_value_labels")
        if positions == list(range(positions[0], positions[0] + len(positions))):
            basis.append("contiguous")
        groups.append(([m.name for m in members], tuple(basis), item_prefix(members[0].name)))
        grouped.update(m.name for m in members)

    run: list[VariableMetadata] = []
    last_position = 0  # of the run's last variable, member or left out

    def close_run() -> None:
        if len(run) >= MIN_ITEMS:
            groups.append(([m.name for m in run], ("shared_value_labels", "contiguous"), None))

    for variable in variables:
        key = _labels_key(variable)
        follows = (
            run
            and key is not None
            and key == _labels_key(run[-1])
            and variable.position == last_position + 1
        )
        if variable.name not in eligible:
            if follows:
                last_position = variable.position
                continue
            close_run()
            run = []
            continue
        last_position = variable.position
        if variable.name in grouped or key is None:
            close_run()
            run = []
        elif follows:
            run.append(variable)
        else:
            close_run()
            run = [variable]
    close_run()
    return groups


def _item_matrix(
    data: LoadedData, members: list[str], profiles: dict[str, VariableProfile]
) -> pd.DataFrame:
    columns = {}
    for name in members:
        variable = data.variable(name)
        excluded = set(profiles[name].suspect_missing_codes)
        for item in variable.declared_missing:
            if item.low == item.high:
                excluded.add(item.low)
        column = pd.to_numeric(data.table[name], errors="coerce").astype(float)
        mask = column.isin([float(c) for c in excluded if not isinstance(c, str)])
        for item in variable.declared_missing:
            if item.low != item.high and not isinstance(item.low, str):
                mask |= column.between(float(item.low), float(item.high))
        columns[name] = column.mask(mask)
    return pd.DataFrame(columns).dropna()


def _round(value: float) -> float:
    return round(float(value), DECIMALS) + 0.0


def _alpha(matrix: pd.DataFrame) -> float | None:
    k = matrix.shape[1]
    total_variance = matrix.sum(axis=1).var(ddof=1)
    if k < 2 or not total_variance > 0:
        return None
    return _round(k / (k - 1) * (1 - matrix.var(ddof=1).sum() / total_variance))


def _statistics(
    matrix: pd.DataFrame,
) -> tuple[float | None, float | None, tuple[ItemStatistics, ...]]:
    """Alpha as observed, alpha with the suspect items reversed, and item statistics."""
    names = list(matrix.columns)
    if len(matrix) < MIN_COMPLETE_ROWS:
        return None, None, tuple(ItemStatistics(n, None, False) for n in names)
    items = []
    total = matrix.sum(axis=1)
    for name in names:
        rest = total - matrix[name]
        if matrix[name].std() == 0 or rest.std() == 0:
            items.append(ItemStatistics(name, None, False))
            continue
        r = float(np.corrcoef(matrix[name], rest)[0, 1])
        items.append(ItemStatistics(name, _round(r), r < 0))

    suspects = [i.name for i in items if i.reverse_suspect]
    reversed_alpha = None
    if suspects:
        # Reversed within the observed codes: min + max - x.
        low, high = matrix.to_numpy().min(), matrix.to_numpy().max()
        recoded = matrix.copy()
        recoded[suspects] = low + high - recoded[suspects]
        reversed_alpha = _alpha(recoded)
    return _alpha(matrix), reversed_alpha, tuple(items)


# In an Excel or CSV export, the answers of a grid are its options as text: a few of them.
MAX_GRID_OPTIONS = 12


def _rated(items, data: LoadedData, profiles: dict[str, VariableProfile]) -> bool:
    """Whether the items of a grid are rated on labelled options, as a scale's are: value
    labels in a .sav file, a few texts in an Excel or CSV export. Not text fields
    (contact information), nor numbers without labels (a ranking, minutes): their grid is
    a question with several fields, not a scale (v0.7, control export)."""
    variables = [data.variable(n) for n in items]
    if all(len(v.value_labels) >= 2 for v in variables):
        return True
    if any(v.value_labels for v in variables):
        return False
    if not all(
        profiles[v.name].inferred_type in ("text", "mixed")
        and (profiles[v.name].n_distinct or 0) <= MAX_GRID_OPTIONS
        for v in variables
    ):
        return False
    # The items of a scale share their options; the columns of a matrix of drop-down menus
    # (a departure time, a mode of transport) do not.
    seen = [{str(o.code) for o in profiles[v.name].observed_values or []} for v in variables]
    for index, mine in enumerate(seen):
        others = set().union(*(s for k, s in enumerate(seen) if k != index))
        if mine and len(mine & others) * 2 < len(mine):
            return False
    return True


def _platform_sets(
    data: LoadedData, profiles: dict[str, VariableProfile]
) -> tuple[list[tuple], set[str]]:
    """The groups given by the structure of a platform's export, and every variable the
    structure covers (questions alone too: they are no items of a scale)."""
    platform = platforms.by_name(data.source.platform)
    if platform is None:
        return [], set()
    ticked = {
        v.name
        for v in data.variables
        if len(v.value_labels) <= 1 and (profiles[v.name].n_distinct or 0) <= 1
    }
    names = [v.name for v in data.variables]
    found: list[tuple] = []
    covered: set[str] = set()
    for question in platforms.survey_questions(platform, names, ticked):
        covered.update(question.variables)
        prefix = platform.item_format.format(question=question.rank, item=0)[:-4]
        if (
            question.kind == "grid"
            and len(question.items) >= MIN_ITEMS
            and _rated(question.items, data, profiles)
        ):
            found.append((list(question.items), ("platform_structure",), prefix, "scale", ()))
        elif question.kind == "checkbox" and len(question.items) >= MIN_OPTIONS:
            attached = (question.other,) if question.other else ()
            found.append(
                (list(question.items), ("platform_structure",), prefix, "multiple_response",
                 attached)
            )  # fmt: skip
    return found, covered


def find_groups(
    data: LoadedData,
    profiles: tuple[VariableProfile, ...],
    classifications: tuple[PrivacyClassification, ...],
) -> tuple[GroupCandidate, ...]:
    """Probable scales and sets of checkboxes, in the order of their first item in the file."""
    by_name = {p.name: p for p in profiles}
    structured, covered = _platform_sets(data, by_name)
    eligible = {
        v.name
        for v, p, c in zip(data.variables, profiles, classifications, strict=True)
        if _eligible(p, c) and v.name not in covered
    }
    found = sorted(
        [(m, b, p, "scale", ()) for m, b, p in _member_sets(list(data.variables), eligible)]
        + structured,
        key=lambda g: data.variable(g[0][0]).position,
    )
    candidates = []
    for number, (members, basis, prefix, kind, attached) in enumerate(found, start=1):
        if kind == "multiple_response":
            candidates.append(
                GroupCandidate(
                    group_id=f"G{number}",
                    members=tuple(members),
                    basis=basis,
                    prefix=prefix,
                    code_min=None,
                    code_max=None,
                    n_complete_rows=0,
                    cronbach_alpha=None,
                    cronbach_alpha_reversed=None,
                    items=tuple(ItemStatistics(m, None, False) for m in members),
                    kind=kind,
                    attached=attached,
                )
            )
            continue
        matrix = _item_matrix(data, members, by_name)
        alpha, reversed_alpha, items = _statistics(matrix)
        codes = matrix.to_numpy().ravel()
        candidates.append(
            GroupCandidate(
                group_id=f"G{number}",
                members=tuple(members),
                basis=basis,
                prefix=prefix,
                code_min=_round(codes.min()) if codes.size else None,
                code_max=_round(codes.max()) if codes.size else None,
                n_complete_rows=len(matrix),
                cronbach_alpha=alpha,
                cronbach_alpha_reversed=reversed_alpha,
                items=items,
            )
        )
    return tuple(candidates)
