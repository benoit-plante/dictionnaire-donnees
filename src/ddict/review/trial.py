"""Try the tool on the fictional database (v0.16, D-125): `etude-sommeil.sav` and its
questionnaire are copied into a folder of the person's Documents, the project is made there
and opened; when it already exists, it is opened again, decisions kept.

The files are fictional: nothing personal is copied, and nothing leaves this computer.
"""

from __future__ import annotations

import ctypes
import os
import shutil
import uuid
from pathlib import Path

from ddict.bench import data_dir
from ddict.project import save_project
from ddict.workflow import add_questionnaire, default_project_path, profile_database

DATABASE = "etude-sommeil.sav"
QUESTIONNAIRE = "questionnaire-sommeil.pdf"
FOLDER = "Dictionnaire de données - essai"
DOCUMENTS = uuid.UUID("FDD39AD0-238F-46AF-ADB4-6C85480369C7")  # Windows' FOLDERID_Documents


def documents() -> Path:
    """The person's Documents folder, as Windows knows it (it may have been moved, to OneDrive
    for instance); the usual place when Windows does not answer."""
    try:
        guid = (ctypes.c_byte * 16).from_buffer_copy(DOCUMENTS.bytes_le)
        found = ctypes.c_wchar_p()
        shell = ctypes.windll.shell32  # type: ignore[attr-defined]
        if shell.SHGetKnownFolderPath(guid, 0, None, ctypes.byref(found)) == 0:
            path = Path(found.value)
            ctypes.windll.ole32.CoTaskMemFree(found)  # type: ignore[attr-defined]
            return path
    except (AttributeError, OSError):
        pass
    return Path(os.environ.get("USERPROFILE") or Path.home()) / "Documents"


def folder() -> Path:
    """Where the trial is made: `DDICT_TRIAL_DIR` when set (tests), else in Documents."""
    override = os.environ.get("DDICT_TRIAL_DIR")
    return Path(override) if override else documents() / FOLDER


def project_path(where: Path | None = None) -> Path:
    return default_project_path((where or folder()) / DATABASE)


def start(where: Path | None = None, *, again: bool = False) -> Path:
    """The trial's project file: made the first time, opened again afterwards. With `again`,
    the database and questionnaire are copied again and the project is made anew (its
    decisions are lost); the other files of the folder are left as they are."""
    where = where or folder()
    output = project_path(where)
    if output.is_file() and not again:
        return output
    where.mkdir(parents=True, exist_ok=True)
    source = data_dir()
    for name in (DATABASE, QUESTIONNAIRE):
        shutil.copyfile(source / name, where / name)
    project, output = profile_database(where / DATABASE, replace=True)
    add_questionnaire(project, where / QUESTIONNAIRE)
    save_project(project, output)
    return output
