"""Choose the reader from the file extension."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ddict.io.csv_reader import read_csv
from ddict.io.model import LoadedData, ReadError
from ddict.io.sav import read_dta, read_sas7bdat, read_sav
from ddict.io.xlsx_reader import read_xlsx
from ddict.platforms import recognize

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
    data = reader(path)
    if data.source.platform is None:
        platform = recognize([v.name for v in data.variables])
        if platform is not None:
            data = replace(data, source=replace(data.source, platform=platform.name))
    return data
