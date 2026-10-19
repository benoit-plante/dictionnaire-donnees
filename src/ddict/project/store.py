"""Save and load project files (*.dd.json), byte for byte reproducibly."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from ddict.io.model import LoadedData
from ddict.project import dataset, measure, ondisk
from ddict.project.model import SCHEMA_VERSION, Project

PROJECT_SUFFIX = ".dd.json"


class ProjectError(Exception):
    """The project file cannot be read."""


class ProjectNewer(ProjectError):
    """Written by a more recent version of the tool: `version` is its format (v0.17, said on
    the home page's table)."""

    def __init__(self, message: str, version: str) -> None:
        super().__init__(message)
        self.version = version


class ProjectChanged(ondisk.FileChanged):
    """The project file changed on the disk since it was read: nothing was written (v0.17,
    D-129)."""


def dumps(project: Project) -> str:
    """Keys in model order, indent 2, UTF-8 characters kept, final newline."""
    data = project.model_dump(mode="json")
    return json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def save_project(project: Project, path: Path | str, *, overwrite: bool = False) -> None:
    """Write through a temporary file, so that an interrupted save never truncates a project.

    Refused (ProjectChanged, nothing written) when the file is no longer what this project
    was read from or last wrote, or, for a project not read from it, when the file exists
    and `overwrite` is not given (v0.17, D-129)."""
    path = Path(path)
    try:
        ondisk.write(project, dumps(project), path, overwrite=overwrite)
    except ondisk.FileChanged as error:
        raise ProjectChanged(error.path, error.reason) from error


def _version(text: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in text.split("."))
    except ValueError:
        return (0,)


def _scoring_as_note(data: dict) -> None:
    """Before 0.3.0 (D-061), a group's scoring was a sourced text: it becomes the note of a
    scoring, with its source."""
    for group in (data.get("variables") and data.get("groups")) or []:
        old = group.get("scoring") if isinstance(group, dict) else None
        if isinstance(old, dict) and "value" in old:
            group["scoring"] = {"source": old.get("source"), "note": old.get("value")}


def load_project(path: Path | str) -> Project:
    path = Path(path)
    try:
        content, disk = ondisk.read(path)
    except OSError as error:
        raise ProjectError(f"Cannot read {path.name}: {error}") from error
    project = _parse(content, path)
    ondisk.remember(project, disk)
    return project


def as_read(project: Project) -> Project | None:
    """The project as its file held it when last read or saved: what a page shows again
    when a save is refused (v0.17). None for a project never read from a file."""
    disk = ondisk.remembered(project)
    if not isinstance(disk, ondisk.DiskState) or not disk.content:
        return None
    found = _parse(disk.content, Path(disk.key))
    ondisk.remember(found, disk)
    return found


def _parse(content: bytes, path: Path) -> Project:
    try:
        data = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ProjectError(f"Cannot read {path.name}: {error}") from error
    version = data.get("schema_version") if isinstance(data, dict) else None
    if not isinstance(version, str) or version.split(".")[0] != SCHEMA_VERSION.split(".")[0]:
        raise ProjectError(f"{path.name}: unsupported schema version {version!r}")
    if _version(version) > _version(SCHEMA_VERSION):
        raise ProjectNewer(
            f"{path.name} was written by a more recent version of the tool "
            f"(format {version}, this version reads up to {SCHEMA_VERSION}): update the tool",
            version,
        )
    _scoring_as_note(data)
    try:
        project = Project.model_validate(data)
    except ValidationError as error:
        raise ProjectError(f"{path.name} is not a valid project file: {error}") from error
    # An older format reads as it is (new fields have defaults) and is saved in this one.
    # Before 0.3.0 (D-061), the rules propose the measure levels it did not have.
    if _version(version) < (0, 3, 0):
        measure.propose(project)
        dataset.propose_structure(project)
    project.schema_version = SCHEMA_VERSION
    return project


def source_differences(project: Project, data: LoadedData) -> list[str]:
    """What changed between the database of the project and the one opened now.

    An empty list means the same file (same SHA-256). Otherwise, short codes:
    "content", "rows", "columns", "variables".
    """
    source = data.source
    if source.sha256 == project.source.sha256:
        return []
    differences = ["content"]
    if source.n_rows != project.source.n_rows:
        differences.append("rows")
    if source.n_columns != project.source.n_columns:
        differences.append("columns")
    if [v.name for v in data.variables] != [e.name for e in project.variables]:
        differences.append("variables")
    return differences
