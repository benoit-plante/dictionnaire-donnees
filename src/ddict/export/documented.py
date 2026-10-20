"""A documented copy of the database, as an SPSS file (v0.4, D-026).

The only place where the tool writes participant data. The copy holds the same cells as
the original, with the accepted metadata: variable labels, value labels, missing codes
declared or confirmed by the team (D-028), measure levels. The original is only read,
never opened for writing; the copy goes next to it under a new name. Before the copy is
announced it is read back and compared cell by cell with the original; at the first
difference it is deleted. Nothing of the data enters the project nor goes to the model.

The copy has the new names a person accepted (v0.7): its columns are renamed, and the check
compares each column with the original column of the same variable.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import pyreadstat

from ddict.export import wording as w
from ddict.io import ReadError, read_database
from ddict.io.sav import file_sha256
from ddict.project import measure as measure_level
from ddict.project.model import Code, Project, VariableEntry
from ddict.questionnaire.labels import accepted_labels

COPY_SUFFIX = "-documente.sav"
WORKING_SUFFIX = ".en-cours"
SPSS_MAX_DISCRETE = 3
SPSS_MAX_STRING_MISSING = 8  # bytes


class CopyError(Exception):
    """The copy cannot be written; `reason` says why, for a message in French."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(reason, detail)
        self.reason = reason
        self.detail = detail


class CopyExists(CopyError):
    def __init__(self, path: Path) -> None:
        super().__init__("exists", str(path))
        self.path = path


@dataclass(frozen=True)
class CopyResult:
    path: Path
    n_rows: int
    n_columns: int
    # Variables whose confirmed missing codes SPSS cannot hold too: written with the file's
    # declared codes only.
    missing_not_written: list[str] = field(default_factory=list)


def default_copy_path(database: Path) -> Path:
    """ "etude-sommeil-documente.sav", next to "etude-sommeil.csv"."""
    return database.with_name(database.stem + COPY_SUFFIX)


def find_database(project: Project, project_path: Path, given: Path | None = None) -> Path:
    """The database the project was made from: the given file, or the file of the same
    name next to the project. Its fingerprint must be the project's."""
    if project.source is None:
        raise CopyError("no_base")
    path = Path(given) if given else project_path.with_name(project.source.name)
    if not path.is_file():
        raise CopyError("not_found", str(path))
    if file_sha256(path) != project.source.sha256:
        raise CopyError("other_file", str(path))
    return path


def _missing(entry: VariableEntry, confirmed: bool = True) -> list[Code | dict] | None:
    """The missing codes as pyreadstat writes them, or None when SPSS cannot hold them."""
    singles = [m.low for m in entry.file.declared_missing if m.low == m.high]
    ranges = [m for m in entry.file.declared_missing if m.low != m.high]
    if confirmed:
        singles += [c for c in w.confirmed_missing(entry) if c not in singles]
    if not singles and not ranges:
        return []
    string = entry.file.storage_type == "string"
    if string and (
        ranges
        or len(singles) > SPSS_MAX_DISCRETE
        or any(len(str(c).encode("utf-8")) > SPSS_MAX_STRING_MISSING for c in singles)
    ):
        return None
    if len(ranges) > 1 or len(singles) > (1 if ranges else SPSS_MAX_DISCRETE):
        return None
    items: list[Code | dict] = [{"lo": r.low, "hi": r.high} for r in ranges]
    return items + [str(c) if string else c for c in singles]


def _as_in_file(entry, labels: dict, value_labels: dict, missing: dict, measure: dict) -> None:
    """A variable set aside keeps, in the copy, the metadata of the file, under its name."""
    name = entry.name
    labels[name] = entry.file.label or None
    string = entry.file.storage_type == "string"
    found = {(str(lab.code) if string else lab.code): lab.label for lab in entry.file.value_labels}
    if found:
        value_labels[name] = found
    codes = _missing(entry, confirmed=False)
    if codes:
        missing[name] = codes
    if entry.file.measure_level:
        measure[name] = entry.file.measure_level


def _metadata(project: Project, columns: list[str]) -> tuple[dict, list[str]]:
    """The metadata of the copy, by the names of the copy (the accepted new names)."""
    labels, value_labels, missing, measure, refused = {}, {}, {}, {}, []
    for original in columns:
        entry = project.variable(original)
        name = w.final_name(entry)
        if entry.set_aside is not None:  # D-158: what the file said, none of the team's
            _as_in_file(entry, labels, value_labels, missing, measure)
            continue
        labels[name] = w.label_text(entry, "final") or None
        string = entry.file.storage_type == "string"
        accepted = {
            (str(lab.code) if string else lab.code): lab.label for lab in accepted_labels(entry)
        }
        if accepted:
            value_labels[name] = accepted
        codes = _missing(entry)
        if codes is None:
            # The codes the team confirmed do not fit: keep those of the file.
            refused.append(original)
            codes = _missing(entry, confirmed=False)
        if codes:
            missing[name] = codes
        if measure_level.level(entry):
            measure[name] = measure_level.level(entry)
    return {
        "column_labels": labels,
        "variable_value_labels": value_labels,
        "missing_ranges": missing,
        "variable_measure": measure,
    }, refused


def _read(database: Path, file_format: str) -> tuple[pd.DataFrame, dict]:
    """The table of the original, and what of its own file an SPSS copy keeps."""
    if file_format == "sav":
        # Dates stay numbers, with their SPSS formats: no conversion to round off.
        table, meta = pyreadstat.read_sav(
            str(database), user_missing=True, disable_datetime_conversion=True
        )
        return table, {
            "file_label": meta.file_label or "",
            "note": meta.notes or None,
            "variable_format": meta.original_variable_types,
            "variable_display_width": meta.variable_display_width,
        }
    return read_database(database).table, {}


def _read_back(path: Path, file_format: str) -> pd.DataFrame:
    table, _meta = pyreadstat.read_sav(
        str(path), user_missing=True, disable_datetime_conversion=file_format == "sav"
    )
    return table


def differences(original: pd.DataFrame, copy: pd.DataFrame) -> int:
    """Cells that differ; -1 when the columns or the rows themselves differ."""
    if list(original.columns) != list(copy.columns) or len(original) != len(copy):
        return -1
    found = 0
    for name in original.columns:
        a = original[name].reset_index(drop=True)
        b = copy[name].reset_index(drop=True)
        both_empty = a.isna() & b.isna()
        equal = (a == b).fillna(False).astype(bool)
        found += int((~(both_empty | equal)).sum())
    return found


def write_documented_copy(
    project: Project,
    database: Path,
    target: Path | None = None,
    *,
    replace: bool = False,
) -> CopyResult:
    """Write the documented copy, check it cell by cell, and only then put it in place."""
    database = Path(database)
    target = Path(target) if target else default_copy_path(database)
    if target.resolve() == database.resolve():
        raise CopyError("same_file", str(target))
    if target.exists() and not replace:
        raise CopyExists(target)
    try:
        table, kept = _read(database, project.source.format)
    except (ReadError, pyreadstat.ReadstatError, pyreadstat.PyreadstatError) as error:
        raise CopyError("unreadable", str(error)) from error
    columns = list(table.columns)
    if columns != [e.name for e in project.variables] or len(table) != project.source.n_rows:
        raise CopyError("other_file", str(database))
    names = w.names_of(project)
    if len({n.lower() for n in names.values()}) != len(names):
        raise CopyError("name_conflict", "")
    metadata, refused = _metadata(project, columns)
    table = table.rename(columns=names)
    kept = {
        key: ({names.get(k, k): v for k, v in value.items()} if isinstance(value, dict) else value)
        for key, value in kept.items()
    }

    working = target.with_name(target.name + WORKING_SUFFIX)
    try:
        pyreadstat.write_sav(table, str(working), **kept, **metadata)
        found = differences(table, _read_back(working, project.source.format))
    except Exception as error:
        _remove(working)
        raise CopyError("write_failed", str(error)) from error
    if found:
        _remove(working)
        raise CopyError("not_identical", str(found))
    working.replace(target)
    return CopyResult(target, len(table), len(columns), refused)


def _remove(path: Path) -> None:
    with contextlib.suppress(FileNotFoundError):
        path.unlink()
