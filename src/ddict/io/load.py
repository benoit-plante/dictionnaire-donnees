"""Choose the reader from the file extension."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ddict.io.csv_reader import read_csv
from ddict.io.model import LoadedData, ReadError
from ddict.io.sav import read_dta, read_sas7bdat, read_sav
from ddict.io.xlsx_reader import read_xlsx
from ddict.platforms import PLATFORMS, Platform, by_name, recognize

READERS = {
    ".sav": read_sav,
    ".zsav": read_sav,
    ".csv": read_csv,
    ".dta": read_dta,
    ".sas7bdat": read_sas7bdat,
    ".xlsx": read_xlsx,
}


def read_database(path: Path | str) -> LoadedData:
    path = Path(path)
    reader = READERS.get(path.suffix.lower())
    if reader is None:
        supported = ", ".join(sorted(READERS))
        raise ReadError(f"Unsupported file type {path.suffix!r} (supported: {supported})")
    data = _sav_names(reader(path))
    if data.source.platform is None:
        platform = recognize([v.name for v in data.variables])
        if platform is not None:
            data = replace(data, source=replace(data.source, platform=platform.name))
    platform = by_name(data.source.platform)
    if platform is not None and platform.empty_datetime and data.source.format == "sav":
        data = _empty_datetimes(data, platform)
    return data


def _sav_names(data: LoadedData) -> LoadedData:
    """The columns of a CSV or Excel export named as its platform's .sav names them (v0.20):
    "sommeil[SQ001]" becomes "sommeil_SQ001" when the names so written are a LimeSurvey
    export. Every other file is left as it is."""
    for platform in PLATFORMS:
        if not platform.bracket_names:
            continue
        names = [platform.column_name(v.name) for v in data.variables]
        same = names == [v.name for v in data.variables]
        if same or len(set(names)) != len(names) or not platform.recognizes(names):
            continue
        renamed = dict(zip((v.name for v in data.variables), names, strict=True))
        variables = tuple(replace(v, name=renamed[v.name]) for v in data.variables)
        table = data.table.rename(columns=renamed)
        source = replace(data.source, platform=platform.name)
        return replace(data, source=source, variables=variables, table=table)
    return data


def _empty_datetimes(data: LoadedData, platform: Platform) -> LoadedData:
    """A date and time that a platform's .sav file writes for an empty cell (LimeSurvey: the
    submission date of an incomplete response, 1582-10-14, the zero of SPSS's dates) read as
    an empty cell, as its CSV export writes it."""
    import pandas as pd

    zero = pd.Timestamp(platform.empty_datetime)
    table = data.table.copy()
    for column in table.columns:
        if pd.api.types.is_datetime64_any_dtype(table[column]):
            table[column] = table[column].mask(table[column].dt.normalize() == zero)
    return replace(data, table=table)
