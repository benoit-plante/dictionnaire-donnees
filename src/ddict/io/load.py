"""Choose the reader from the file extension."""

from __future__ import annotations

from pathlib import Path

from ddict.io.csv_reader import read_csv
from ddict.io.model import LoadedData, ReadError
from ddict.io.sav import read_dta, read_sas7bdat, read_sav
from ddict.io.xlsx_reader import read_xlsx

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
    return reader(path)
