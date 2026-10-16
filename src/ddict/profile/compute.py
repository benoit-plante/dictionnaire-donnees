"""Compute the profile of every variable, without any model."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import replace

import numpy as np
import pandas as pd

from ddict.io.model import Code, LoadedData, MissingRange, VariableMetadata
from ddict.io.sav import normalize_code
from ddict.profile.model import Flag, InferredType, ObservedValue, VariableProfile

# Above this many distinct values, observed values are not listed.
MAX_OBSERVED_VALUES = 20

# Usual codes for "no answer" when they are not declared missing.
NEGATIVE_SENTINELS = {-1, -7, -8, -9, -77, -88, -99, -777, -888, -999, -9999}
POSITIVE_SENTINELS = {7, 8, 9, 77, 88, 98, 99, 777, 888, 998, 999, 9998, 9999}
# A positive sentinel must stand clearly above the other values (9 after a 1-5 scale, yes;
# 9 after a 1-8 scale, no).
SENTINEL_GAP = 1.5

# A value label that says the person did not answer (v0.7, D-047): such a code is a suspect
# missing code, whatever its value ("6 = Ne sais pas" after a 1-5 scale).
MISSING_LABEL = re.compile(
    r"(?<!\w)(je )?ne (le )?sai[st] pas(?!\w)|(?<!\w)nsp(?!\w)"
    r"|pr[ée]f[èée]re(rais)? ne pas r[ée]pondre|^refus(?!\w)|(?<!\w)refuse(?!\w)"
    r"|sans objet|ne s'applique pas|non applicable"
    r"|(?<!\w)don'?t know(?!\w)|(?<!\w)do not know(?!\w)|prefer not to (answer|say)"
    r"|(?<!\w)refused(?!\w)|not applicable|^n/?a$",
    re.IGNORECASE,
)

# Labels on only some values (often the ends of a 0-10 scale) do not make the others
# "unlabeled"; codes without a label are reported when most observed values have one.
LABELED_SHARE_FOR_UNLABELED = 0.5

_SPSS_DATETIME_FORMATS = ("DATETIME", "YMDHMS", "MTIME", "DTIME")
_SPSS_DATE_FORMATS = ("DATE", "ADATE", "EDATE", "SDATE", "JDATE", "MOYR", "QYR", "WKYR")
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_ISO_DATETIME = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?")
# 31/12/2024 (Quebec and France) or 12/31/2024 (United States): see _slash_format.
_SLASH_DATE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
# With a time, as survey platforms write it in text: "10/02/2026 09:15:23 AM" (v0.7).
_SLASH_DATETIME = re.compile(r"\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}(:\d{2})?( ?[AaPp][Mm])?")
_SLASH_DATETIME_FORMATS = (
    # A 12-hour clock is American: month first.
    "%m/%d/%Y %I:%M:%S %p",
    "%m/%d/%Y %I:%M %p",
    "%d/%m/%Y %I:%M:%S %p",
    "%d/%m/%Y %I:%M %p",
    # A 24-hour clock: day first, as for dates alone.
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
)
_NUMBER = re.compile(r"[+-]?(\d+([.,]\d*)?|[.,]\d+)([eE][+-]?\d+)?")


def _is_declared(value: object, ranges: tuple[MissingRange, ...]) -> bool:
    for item in ranges:
        if isinstance(value, str) != isinstance(item.low, str):
            continue
        if item.low == item.high:
            if value == item.low:
                return True
        elif item.low <= value <= item.high:
            return True
    return False


def _system_missing(series: pd.Series) -> pd.Series:
    missing = series.isna()
    if not (pd.api.types.is_numeric_dtype(series) or pd.api.types.is_datetime64_any_dtype(series)):
        missing |= series.map(lambda value: isinstance(value, str) and not value.strip())
    return missing


def _spss_kind(variable: VariableMetadata) -> InferredType | None:
    spss_format = (variable.display_format or "").upper()
    if spss_format.startswith(_SPSS_DATETIME_FORMATS):
        return "datetime"
    if spss_format.startswith(_SPSS_DATE_FORMATS):
        return "date"
    return None


def _infer_type(values: pd.Series, variable: VariableMetadata) -> InferredType:
    if values.empty:
        return "empty"
    spss_kind = _spss_kind(variable)
    if spss_kind is not None:
        return spss_kind
    if pd.api.types.is_datetime64_any_dtype(values):
        return "datetime"
    if pd.api.types.is_numeric_dtype(values):
        if not np.all(np.mod(values.to_numpy(dtype=float), 1) == 0):
            return "decimal"
        return "boolean" if set(values.unique()) == {0, 1} else "integer"
    items = list(values)
    if all(isinstance(v, dt.datetime | pd.Timestamp) for v in items):
        return "datetime"
    if all(isinstance(v, dt.date) for v in items):
        return "date"
    texts = [str(v).strip() for v in items]
    if all(_ISO_DATE.fullmatch(t) for t in texts) or _slash_format(texts):
        return "date"
    if all(_ISO_DATETIME.fullmatch(t) for t in texts) or _slash_datetime_format(texts):
        return "datetime"
    numeric = sum(1 for t in texts if _NUMBER.fullmatch(t))
    if numeric < len(texts) and numeric >= len(texts) / 2:
        return "mixed"
    return "text"


def _slash_format(texts: list[str]) -> str | None:
    """The format of dates written with slashes, or None if they are not all such dates.

    Day first, as in Quebec and France, unless a first number above 12 is never seen and a
    second one is (12/31/2024). Dates that fit neither order are not dates.
    """
    parts = [_SLASH_DATE.fullmatch(t) for t in texts]
    if not parts or not all(parts):
        return None
    for fmt in ("%d/%m/%Y", "%m/%d/%Y"):
        try:
            for text in texts:
                dt.datetime.strptime(text, fmt)
        except ValueError:
            continue
        return fmt
    return None


def _slash_datetime_format(texts: list[str]) -> str | None:
    """The format of dates and times written with slashes ("10/02/2026 09:15:23 AM"), or
    None if they are not all such; the first format that reads them all."""
    if not texts or not all(_SLASH_DATETIME.fullmatch(t) for t in texts):
        return None
    for fmt in _SLASH_DATETIME_FORMATS:
        try:
            for text in texts:
                dt.datetime.strptime(text, fmt)
        except ValueError:
            continue
        return fmt
    return None


# The dates and times in text an exclusion rule of duration reads (v0.12): "iso" or a format
# of the slashes, the same in the tool, SPSS and R.
TEXT_DATETIME_FORMATS = ("iso", *_SLASH_DATETIME_FORMATS)


def text_datetime_format(texts: list[str]) -> str | None:
    """ "iso" or the format of dates and times written in text; None if not all such."""
    texts = [str(t).strip() for t in texts]
    if texts and all(_ISO_DATETIME.fullmatch(t) for t in texts):
        return "iso"
    return _slash_datetime_format(texts)


def is_missing_label(label: str) -> bool:
    """A value label saying that the person did not answer: "Ne sais pas", "Refus"..."""
    return bool(MISSING_LABEL.search(label))


def _labelled_missing(valid_codes: list[Code], labels: dict[Code, str]) -> set[Code]:
    return {c for c in set(valid_codes) if c in labels and is_missing_label(str(labels[c]))}


def _as_timestamps(values: pd.Series) -> pd.Series:
    texts = values.map(lambda v: str(v).strip() if isinstance(v, str) else v)
    strings = [t for t in texts if isinstance(t, str)]
    fmt = _slash_format(strings) or _slash_datetime_format(strings)
    return pd.to_datetime(texts, format=fmt) if fmt else pd.to_datetime(texts)


def _number(value: float) -> float:
    return float(value) + 0.0  # turns -0.0 into 0.0


def _numeric_stats(values: pd.Series) -> dict:
    array = values.to_numpy(dtype=float)
    q1, median, q3 = np.quantile(array, [0.25, 0.5, 0.75])
    return {
        "min": _number(array.min()),
        "max": _number(array.max()),
        "mean": _number(array.mean()),
        "sd": _number(array.std(ddof=1)) if len(array) > 1 else None,
        "median": _number(median),
        "q1": _number(q1),
        "q3": _number(q3),
    }


def _code(value: object) -> Code:
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, str):
        return value
    return normalize_code(float(value))


def _sort_key(code: Code) -> tuple:
    return (isinstance(code, str), code)


def _suspect_sentinels(valid_codes: list[Code]) -> tuple[Code, ...]:
    numbers = sorted({c for c in valid_codes if not isinstance(c, str)})
    found = []
    for code in numbers:
        others = [c for c in numbers if c != code]
        if not others:
            continue
        negative = code in NEGATIVE_SENTINELS and min(others) >= 0
        positive = code in POSITIVE_SENTINELS and max(others) > 0
        if negative or (positive and code > SENTINEL_GAP * max(others)):
            found.append(code)
    return tuple(found)


def profile_variable(series: pd.Series, variable: VariableMetadata) -> VariableProfile:
    n_rows = len(series)
    system = _system_missing(series)
    present = series[~system]
    declared = pd.Series(False, index=present.index)
    if variable.declared_missing:
        declared = present.map(lambda v: _is_declared(_code(v), variable.declared_missing))
    valid = present[~declared.astype(bool)]

    inferred = _infer_type(valid, variable)
    stats: dict = {}
    if inferred in ("boolean", "integer", "decimal"):
        stats.update(_numeric_stats(valid))
    elif inferred in ("date", "datetime") and not valid.empty:
        stamps = _as_timestamps(valid)
        fmt = "%Y-%m-%d" if inferred == "date" else "%Y-%m-%dT%H:%M:%S"
        stats["date_min"] = stamps.min().strftime(fmt)
        stats["date_max"] = stamps.max().strftime(fmt)
    elif inferred in ("text", "mixed") and not valid.empty:
        lengths = valid.map(lambda v: len(str(v)))
        stats["length_min"] = int(lengths.min())
        stats["length_max"] = int(lengths.max())
        if inferred == "mixed":
            stats["n_non_numeric"] = int(
                sum(1 for v in valid if not _NUMBER.fullmatch(str(v).strip()))
            )

    is_temporal = inferred in ("date", "datetime")
    valid_codes = [] if is_temporal else [_code(v) for v in valid]
    distinct_valid = set(valid_codes) if not is_temporal else set(valid.map(str))
    n_distinct = len(distinct_valid)

    observed = None
    if not is_temporal:
        counts: dict[Code, list] = {}
        for value, is_declared in zip(present, declared, strict=True):
            code = _code(value)
            entry = counts.setdefault(code, [0, bool(is_declared)])
            entry[0] += 1
        if len(counts) <= MAX_OBSERVED_VALUES:
            observed = tuple(
                ObservedValue(code, count, is_declared)
                for code, (count, is_declared) in sorted(
                    counts.items(), key=lambda item: _sort_key(item[0])
                )
            )
        all_codes = set(counts)
    else:
        all_codes = set()

    labels = variable.value_labels
    unlabeled: tuple[Code, ...] = ()
    unused: tuple[Code, ...] = ()
    if labels and not is_temporal:
        labeled = [c for c in distinct_valid if c in labels]
        if distinct_valid and len(labeled) / len(distinct_valid) >= LABELED_SHARE_FOR_UNLABELED:
            unlabeled = tuple(sorted((c for c in distinct_valid if c not in labels), key=_sort_key))
        unused = tuple(sorted((c for c in labels if c not in all_codes), key=_sort_key))

    flags: list[Flag] = []
    if valid.empty:
        flags.append("all_missing")
    elif n_distinct == 1:
        # One value and empty cells: usually a box ticked (1) or left empty, not a constant.
        flags.append("checkbox" if system.any() else "constant")
    if inferred == "mixed":
        flags.append("mixed_types")

    return VariableProfile(
        name=variable.name,
        inferred_type=inferred,
        n_rows=n_rows,
        n_valid=len(valid),
        n_system_missing=int(system.sum()),
        n_declared_missing=int(declared.sum()),
        n_distinct=n_distinct,
        observed_values=observed,
        unlabeled_codes=unlabeled,
        unused_labels=unused,
        suspect_missing_codes=tuple(
            sorted(
                set(_suspect_sentinels(valid_codes)) | _labelled_missing(valid_codes, labels),
                key=_sort_key,
            )
        ),
        flags=tuple(flags),
        **stats,
    )


def _find_duplicates(data: LoadedData, profiles: list[VariableProfile]) -> dict[str, str]:
    """Map each column identical to an earlier one onto that earlier column."""
    table = data.table
    seen: dict[int, list[str]] = {}
    duplicates: dict[str, str] = {}
    for variable, profile in zip(data.variables, profiles, strict=True):
        if "all_missing" in profile.flags:
            continue
        column = table[variable.name]
        key = int(pd.util.hash_pandas_object(column.astype(str), index=False).sum())
        for earlier in seen.get(key, []):
            if column.equals(table[earlier]):
                duplicates[variable.name] = earlier
                break
        else:
            seen.setdefault(key, []).append(variable.name)
    return duplicates


def profile_database(data: LoadedData) -> tuple[VariableProfile, ...]:
    """Profile every variable, in file order."""
    profiles = [profile_variable(data.table[v.name], v) for v in data.variables]
    duplicates = _find_duplicates(data, profiles)
    return tuple(
        replace(p, duplicate_of=duplicates[p.name], flags=(*p.flags, "duplicate"))
        if p.name in duplicates
        else p
        for p in profiles
    )
